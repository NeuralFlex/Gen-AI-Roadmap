import json
import os
from typing import Any, Dict, Mapping, List

from langchain_community.vectorstores import FAISS
from utils.logger import setup_logger
from utils.generation import _safe_generate
from services.tavily_client import tavily_service
from services.gemini_client import gemini_client
from models.embedding_model import embeddings
from models.final_evaluation import FinalEvaluation
from config.prompts import (
    get_setup_prompt,
    get_question_generation_prompt,
    get_evaluation_prompt,
    get_final_evaluation_prompt,
)
from utils.sanitizer import sanitize_state

logger = setup_logger(__name__)


def decide_retrieval(query: str, user_id: str = "default_user") -> (bool, float):
    """
    Decide if retrieval is needed based on similarity score from FAISS.

    Args:
        query (str): User query or current answer.
        user_id (str): User identifier for personalized FAISS index.

    Returns:
        Tuple[bool, float]: Tuple of (needs_retrieval, min_distance)
    """
    try:
        index_dir = os.path.join(os.getcwd(), f"faiss_index_{user_id}")
        if not os.path.exists(index_dir):
            logger.warning(
                "No FAISS index found for user '%s', skipping retrieval.", user_id
            )
            return False, 1.0

        vectorstore = FAISS.load_local(
            index_dir, embeddings, allow_dangerous_deserialization=True
        )
        top_chunks = vectorstore.similarity_search_with_score(query, k=3)
        if not top_chunks:
            return False, 1.0

        min_distance = min(score for _, score in top_chunks)
        needs_retrieval = min_distance < 0.55
        return bool(needs_retrieval), float(min_distance)

    except Exception as e:
        logger.error("Retrieval decision error for user '%s': %s", user_id, e)
        return False, 1.0


def setup_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Initialize the interview node. If step > 0, sanitize existing state.

    Args:
        state (Mapping[str, Any]): Current state.

    Returns:
        Dict[str, Any]: Updated sanitized state.
    """
    state = dict(state)
    if state.get("step", 0) > 0:
        return sanitize_state(state)

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
        logger.error("Setup retrieval failed for user '%s': %s", user_id, e)

    prompt = get_setup_prompt(topic, question_type, retrieved_context, "RAG")
    first_question = _safe_generate(
        prompt, "Tell me about your experience with this technology."
    )

    new_state = {
        **state,
        "topic": topic,
        "question_type": question_type,
        "content": [retrieved_context or "No content"],
        "messages": [
            {"role": "user", "content": f"Interview topic: {topic}"},
            {"role": "assistant", "content": first_question},
        ],
        "step": 1,
        "questions": [],
        "answers": [],
        "feedback": [],
        "current_question": first_question,
        "max_steps": state.get("max_steps", 3),
        "waiting_for_user": True,
        "needs_retrieval": False,
        "retrieved_context": retrieved_context,
        "similarity_score": 0.0,
        "tavily_snippets": [],
    }

    return sanitize_state(new_state)


def get_answer_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Update state with the user's answer to the current question.

    Args:
        state (Mapping[str, Any]): Current state.

    Returns:
        Dict[str, Any]: Updated state including new messages and content.
    """
    state = dict(state)
    current_q = state.get("current_question")
    if not current_q:
        raise ValueError("No current_question found in state.")

    answer = state.get("user_response", "")
    new_messages = list(state.get("messages", [])) + [
        {"role": "interviewer", "content": current_q},
        {"role": "candidate", "content": answer},
    ]
    content_list = list(state.get("content", [])) + [f"Q: {current_q}\nA: {answer}"]

    new_state = {
        **state,
        "current_answer": answer,
        "messages": new_messages,
        "questions": state.get("questions", []) + [current_q],
        "answers": state.get("answers", []) + [answer],
        "content": content_list,
    }
    return sanitize_state(new_state)


def retrieval_decision_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Decide if retrieval is needed based on the current answer.

    Args:
        state (Mapping[str, Any]): Current state.

    Returns:
        Dict[str, Any]: State updated with retrieval decision and similarity score.
    """
    state = dict(state)
    current_answer = state.get("current_answer", "")
    user_id = state.get("user_id", "default_user")

    try:
        needs_retrieval, similarity_score = decide_retrieval(current_answer, user_id)
    except Exception as e:
        logger.error("Retrieval decision node failed: %s", e)
        needs_retrieval, similarity_score = False, 1.0

    new_state = {
        **state,
        "needs_retrieval": needs_retrieval,
        "similarity_score": similarity_score,
    }
    return sanitize_state(new_state)


def retrieval_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Perform FAISS retrieval if needed and update the state with retrieved context.

    Args:
        state (Mapping[str, Any]): Current state.

    Returns:
        Dict[str, Any]: State updated with retrieved context or None.
    """
    state = dict(state)
    if not state.get("needs_retrieval", False):
        return sanitize_state({**state, "retrieved_context": None})

    user_id = state.get("user_id", "default_user")
    query = state.get("current_answer", state.get("topic", ""))

    try:
        index_dir = os.path.join(os.getcwd(), f"faiss_index_{user_id}")
        vectorstore = FAISS.load_local(
            index_dir, embeddings, allow_dangerous_deserialization=True
        )
        docs = vectorstore.similarity_search(query, k=3)
        retrieved_context = "\n\n".join([doc.page_content for doc in docs])
        return sanitize_state({**state, "retrieved_context": retrieved_context})
    except Exception as e:
        logger.error("Retrieval failed for user '%s': %s", user_id, e)
        return sanitize_state({**state, "retrieved_context": None})


def tavily_search_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Perform Tavily search to enrich context with relevant snippets.

    Args:
        state (Mapping[str, Any]): Current state.

    Returns:
        Dict[str, Any]: Updated state including Tavily snippets and enriched context.
    """
    state = dict(state)
    query = state.get("current_answer", state.get("topic", ""))
    if not query:
        return sanitize_state(state)

    try:
        snippets = tavily_service.search(query, top_k=5)
        if snippets:
            enriched_context = (
                (state.get("retrieved_context") or "") + "\n\n" + "\n\n".join(snippets)
            )
            return sanitize_state(
                {
                    **state,
                    "retrieved_context": enriched_context,
                    "tavily_snippets": snippets,
                }
            )
        return sanitize_state(state)
    except Exception as e:
        logger.error("Tavily search failed: %s", e)
        return sanitize_state(state)


def generate_question_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Generate the next interview question based on current state and context.

    Args:
        state (Mapping[str, Any]): Current state.

    Returns:
        Dict[str, Any]: Updated state with new question.
    """
    state = dict(state)
    step = state.get("step", 0)
    max_questions = state.get("max_steps", 3)
    if step >= max_questions:
        return sanitize_state(state)

    topic = state.get("topic", "")
    content_list = state.get("content", [])
    context_text = []

    if state.get("needs_retrieval") and state.get("retrieved_context"):
        context_text.append(state["retrieved_context"])
        context_sources = ["RAG"]
    elif state.get("tavily_snippets"):
        context_text.extend(state["tavily_snippets"])
        context_sources = ["Tavily"]
    else:
        context_sources = ["None"]

    full_content = "\n".join(content_list + context_text)
    context_str = "\n".join(context_text)

    prompt = get_question_generation_prompt(
        content_text=full_content,
        topic=topic,
        step=step,
        tool_used=context_sources[0],
        context=context_str,
    )
    try:
        question = _safe_generate(
            prompt, f"Tell me more about your experience with {topic}."
        )
    except Exception as e:
        logger.error("Question generation failed: %s", e)
        question = f"Please elaborate more on {topic}."

    messages = list(state.get("messages", [])) + [
        {"role": "assistant", "content": question}
    ]

    new_state = {
        **state,
        "current_question": question,
        "messages": messages,
        "waiting_for_user": True,
        "step": step + 1,
    }

    return sanitize_state(new_state)


def evaluate_question_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Evaluate the last question and answer using Gemini and update feedback.

    Args:
        state (Mapping[str, Any]): Current state.

    Returns:
        Dict[str, Any]: Updated state including feedback.
    """
    state = dict(state)
    questions, answers = state.get("questions", []), state.get("answers", [])
    if not questions or not answers:
        return sanitize_state(state)

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
        q_parsed = json.loads(q_raw)
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
        a_parsed = json.loads(a_raw)
    except Exception as e:
        logger.error("Evaluation failed: %s", e)
        q_parsed = {"rating": 6, "feedback": "Good effort."}
        a_parsed = {"rating": 6, "feedback": "Good effort."}

    feedback_list = list(state.get("feedback", []))
    feedback_list.append({"question_feedback": q_parsed, "answer_feedback": a_parsed})

    new_state = {
        **state,
        "feedback": feedback_list,
        "step": state.get("step", 0) + 1,
    }
    return sanitize_state(new_state)


def final_evaluation_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Perform a final evaluation of the interview including overall quality, strengths, and recommendations.

    Args:
        state (Mapping[str, Any]): Current state.

    Returns:
        Dict[str, Any]: State updated with final evaluation.
    """
    state = dict(state)
    questions, answers, feedback = (
        state.get("questions", []),
        state.get("answers", []),
        state.get("feedback", []),
    )
    if not questions or not answers:
        return sanitize_state(state)

    transcript = ""
    for i in range(len(questions)):
        fb = feedback[i] if i < len(feedback) else {}
        transcript += f"Q{i+1}: {questions[i]}\nA{i+1}: {answers[i]}\nFeedback: {fb.get('answer_feedback', {}).get('feedback', '')}\n\n"

    final_prompt = get_final_evaluation_prompt(transcript)
    try:
        raw_final = gemini_client.generate_content(final_prompt)
        parsed_final = json.loads(raw_final)
    except Exception as e:
        logger.error("Final evaluation parse failed: %s", e)
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

    return sanitize_state({**state, "final_evaluation": final_eval.model_dump()})


def display_results_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Display interview results using shared rendering utility.

    Args:
        state (Mapping[str, Any]): Current state.

    Returns:
        Dict[str, Any]: Sanitized state.
    """
    try:
        from utils.interview_results import render_interview_results

        render_interview_results(state)
    except Exception as e:
        logger.error("Display results failed: %s", e)
    return sanitize_state(state)
