import os
import json
import time
import textwrap
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping

import requests

from utils.interview_results import render_interview_results
from utils.logger import setup_logger
from utils.generation import build_prompt, safe_parse_json, safe_text, _safe_generate
from utils.prompt_template import safe_prompt

from services.tavily_client import tavily_service
from services.gemini_client import gemini_client

from langchain_community.vectorstores import FAISS

from graph.state import InterviewState
from models.embedding_model import embeddings
from models.final_evaluation import FinalEvaluation
from config.prompts import (
    get_setup_prompt,
    get_evaluation_prompt,
    get_question_generation_prompt,
    get_final_evaluation_prompt,
)

logger = setup_logger(__name__)


def decide_retrieval(query: str, user_id: str = "default_user"):
    """Decides whether retrieval is needed based on similarity scores."""
    try:
        index_dir = os.path.join(os.getcwd(), f"faiss_index_{user_id}")
        if not os.path.exists(index_dir):
            logger.warning("No FAISS index found, skipping retrieval.")
            return False, 1.0

        vectorstore = FAISS.load_local(
            index_dir, embeddings, allow_dangerous_deserialization=True
        )
        top_chunks = vectorstore.similarity_search_with_score(query, k=3)
        if not top_chunks:
            return False, 1.0

        min_distance = min(score for _, score in top_chunks)
        needs_retrieval = min_distance < 0.55
        return needs_retrieval, min_distance

    except Exception as e:
        logger.error(f"Retrieval decision error: {e}")
        return False, 1.0


def setup_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """Initializes interview state and retrieves context for topic."""
    state = vars(state) if not isinstance(state, dict) else state

    topic = state.get("topic", "").strip()
    question_type = state.get("question_type", "broad_followup").strip()
    user_id = state.get("user_id", "default_user")

    retrieved_context = ""
    try:
        index_dir = os.path.join(os.getcwd(), f"faiss_index_{user_id}")
        if os.path.exists(index_dir):
            vectorstore = FAISS.load_local(
                index_dir, embeddings, allow_dangerous_deserialization=True
            )
            docs = vectorstore.similarity_search(topic, k=3)
            retrieved_context = "\n\n".join([doc.page_content for doc in docs])
            logger.info("Retrieved setup context for topic: %s", topic)
    except Exception as e:
        logger.error("Setup retrieval failed: %s", e)
    # topic: str, question_type: str, context: str, tool_used: str
    prompt = safe_prompt(
        get_setup_prompt(topic, question_type, retrieved_context, "RAG")
    )
    first_question = _safe_generate(
        prompt, "Tell me about your experience with this technology."
    )

    return {
        **state,
        "topic": topic,
        "question_type": question_type,
        "content": [retrieved_context or "No content"],
        "messages": [{"role": "user", "content": f"Interview topic: {topic}"}],
        "step": 0,
        "questions": [],
        "answers": [],
        "feedback": [],
        "current_question": first_question,
        "max_questions": state.get("max_questions", 3),
        "needs_retrieval": False,
        "retrieved_context": retrieved_context,
        "similarity_score": 0.0,
    }


def get_answer_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    state = vars(state) if not isinstance(state, dict) else state

    current_q = state.get("current_question")
    if not current_q:
        raise ValueError("No current_question found in state.")

    answer = input(
        f"\n❓ Question {state.get('step', 0) + 1}: {current_q}\n💭 Your answer: "
    ).strip()

    new_messages = list(state.get("messages", [])) + [
        {"role": "interviewer", "content": current_q},
        {"role": "candidate", "content": answer},
    ]
    content_list = list(state.get("content", [])) + [f"Q: {current_q}\nA: {answer}"]

    return {
        **state,
        "current_answer": answer,
        "messages": new_messages,
        "questions": state.get("questions", []) + [current_q],
        "answers": state.get("answers", []) + [answer],
        "content": content_list,
    }


def retrieval_decision_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    state = vars(state) if not isinstance(state, dict) else state

    current_answer = state.get("current_answer", "")
    user_id = state.get("user_id", "default_user")

    needs_retrieval, similarity_score = decide_retrieval(current_answer, user_id)
    logger.info(
        "Retrieval decision: %s (similarity: %.2f)", needs_retrieval, similarity_score
    )

    return {
        **state,
        "needs_retrieval": needs_retrieval,
        "similarity_score": similarity_score,
    }


def retrieval_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    state = vars(state) if not isinstance(state, dict) else state

    if not state.get("needs_retrieval", False):
        logger.info("Retrieval not needed, skipping retrieval_node.")
        return {**state, "retrieved_context": None}

    user_id = state.get("user_id", "default_user")
    query = state.get("current_answer", state.get("topic", ""))
    try:
        index_dir = os.path.join(os.getcwd(), f"faiss_index_{user_id}")
        vectorstore = FAISS.load_local(
            index_dir, embeddings, allow_dangerous_deserialization=True
        )
        docs = vectorstore.similarity_search(query, k=3)
        retrieved_context = "\n\n".join([doc.page_content for doc in docs])
        logger.info("Retrieved additional context for: %s", query[:50])
        return {**state, "retrieved_context": retrieved_context}
    except Exception as e:
        logger.error("Retrieval failed: %s", e)
        return {**state, "retrieved_context": None}


def tavily_search_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    state = vars(state) if not isinstance(state, dict) else state

    query = state.get("current_answer", state.get("topic", ""))
    if not query:
        logger.warning("No query available for Tavily search.")
        return state

    try:
        snippets = tavily_service.search(query, top_k=5)
        if snippets:
            enriched_context = (
                (state.get("retrieved_context") or "") + "\n\n" + "\n\n".join(snippets)
            )
            logger.info("Tavily search added %d snippets to context", len(snippets))
            return {
                **state,
                "retrieved_context": enriched_context,
                "tavily_snippets": snippets,
            }
        return state
    except Exception as e:
        logger.error("Tavily search failed: %s", e)
        return state


def generate_question_node(state: InterviewState) -> InterviewState:
    """Generates the next interview question using RAG or Tavily context."""
    step = state["step"]
    max_questions = state["max_questions"]
    if step >= max_questions:
        logger.warning("Max questions reached. Skipping question generation.")
        return state

    topic = state["topic"]
    content_list = state.get("content", [])
    current_answer = state.get("current_answer", "")
    context_text = []

    if state.get("needs_retrieval", False) and state.get("retrieved_context"):
        context_text.append(state["retrieved_context"])
        context_sources = ["RAG"]
    elif state.get("tavily_snippets"):
        context_text.extend(state["tavily_snippets"])
        context_sources = ["Tavily"]
    else:
        context_sources = ["None"]

    logger.info(
        "Using %s context for question generation.", " + ".join(context_sources)
    )

    # content_text: str, topic: str, step: int, tool_used: str, context: str
    full_content = "\n".join(content_list + context_text)
    context_str = "\n".join(context_text)

    prompt = get_question_generation_prompt(
        content_text=full_content,
        topic=topic,
        step=step,
        tool_used=context_sources[0],
        context=context_str,
    )

    question = _safe_generate(
        prompt, f"Tell me more about your experience with {topic}."
    )

    state["current_question"] = question
    return state


def evaluate_question_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    state = vars(state) if not isinstance(state, dict) else state

    questions, answers = state.get("questions", []), state.get("answers", [])
    if not questions or not answers:
        logger.warning("No Q/A to evaluate.")
        return state

    current_q, current_a = questions[-1], answers[-1]
    full_content = "\n".join(state.get("content", []))
    transcript = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(questions, answers)])
    messages_text = "\n".join([m.get("content", "") for m in state.get("messages", [])])

    try:
        q_raw = gemini_client.generate_content(
            get_evaluation_prompt(
                kind="question",
                full_messages=messages_text,
                full_content=full_content,
                transcript=transcript,
                last_question=current_q,
                last_answer=current_a,
            )
        )
        q_parsed = safe_parse_json(q_raw)

        a_raw = gemini_client.generate_content(
            get_evaluation_prompt(
                kind="answer",
                full_messages=messages_text,
                full_content=full_content,
                transcript=transcript,
                last_question=current_q,
                last_answer=current_a,
            )
        )
        a_parsed = safe_parse_json(a_raw)

    except Exception as e:
        logger.error("Evaluation failed: %s", e)
        q_parsed = {"rating": 6, "feedback": "Good effort."}
        a_parsed = {"rating": 6, "feedback": "Good effort."}

    feedback_list = list(state.get("feedback", []))
    feedback_list.append({"question_feedback": q_parsed, "answer_feedback": a_parsed})

    return {**state, "feedback": feedback_list, "step": state.get("step", 0) + 1}


def final_evaluation_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    state = vars(state) if not isinstance(state, dict) else state

    questions, answers, feedback = (
        state.get("questions", []),
        state.get("answers", []),
        state.get("feedback", []),
    )
    if not questions or not answers:
        logger.warning("No data for final evaluation.")
        return state

    transcript = ""
    for i in range(len(questions)):
        fb = feedback[i] if i < len(feedback) else {}
        transcript += (
            f"Q{i+1}: {questions[i]}\nA{i+1}: {answers[i]}\n"
            f"Feedback: {fb.get('answer_feedback', {}).get('feedback', '')}\n\n"
        )

    final_prompt = get_final_evaluation_prompt(transcript)
    try:
        raw_final = gemini_client.generate_content(final_prompt)
        parsed_final = safe_parse_json(raw_final)
    except Exception as e:
        logger.error("Final eval parse failed: %s", e)
        parsed_final = {}

    final_eval = FinalEvaluation(
        overall_quality=int(parsed_final.get("overall_quality", 7)),
        strengths=parsed_final.get("strengths", ["Good technical depth"]),
        areas_for_improvement=parsed_final.get(
            "areas_for_improvement", ["Elaborate examples"]
        ),
        recommendation=parsed_final.get(
            "recommendation", "Recommended with reservations."
        ),
        final_feedback=parsed_final.get("final_feedback", "Solid overall performance."),
    )

    return {**state, "final_evaluation": final_eval.model_dump()}


def display_results_node(state: InterviewState) -> InterviewState:
    """
    Display interview results and send them to Slack.
    Uses the shared `render_interview_results` utility.
    """
    render_interview_results(state)
    return state
