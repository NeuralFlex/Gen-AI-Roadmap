import json
from typing import Dict, List
from graph.state import InterviewState
from services.gemini_client import gemini_client, QuestionFeedback, AnswerFeedback
from services.tavily_client import tavily_service
from config.prompts import *
from utils.logger import setup_logger
from utils.vectorstore import embeddings
from langchain_community.vectorstores import FAISS
from config.prompts import (
    get_setup_prompt,
    get_evaluation_prompt,
    get_question_generation_prompt,
    get_question_instruction,
    get_final_evaluation_prompt,
)

logger = setup_logger(__name__)


import os
import json
import time
import textwrap
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

# -------------------------
# Logger (reuse your setup)
# -------------------------
logger = setup_logger(__name__)


def safe_prompt(fstring: str) -> str:
    return textwrap.dedent(fstring).strip()


def _safe_generate(prompt: str, fallback: str) -> str:
    try:
        return gemini_client.generate_content(prompt) or fallback
    except Exception as e:
        logger.error("Generation failed: %s", e)
        return fallback


# -------------------------
# Helper utilities
# -------------------------
def safe_parse_json(response: Any) -> Dict[str, Any]:
    """
    Robustly parse possible model responses into a Python dict.
    Handles:
      - dict-like responses
      - objects with `.text` attribute
      - strings that contain JSON (extract first {...} substring)
    Falls back to a minimal safe structure if parsing fails.
    """
    fallback = {"rating": 6, "feedback": "Good effort. Could elaborate more."}

    if not response:
        return fallback

    # If it's already a dict-like object, return as-is
    if isinstance(response, dict):
        return response

    # If it's an object with .text or .content, try to pull its string
    text = None
    if hasattr(response, "text"):
        try:
            text = response.text
        except Exception:
            text = None
    if text is None and hasattr(response, "content"):
        try:
            text = response.content
        except Exception:
            text = None
    if text is None and isinstance(response, str):
        text = response

    if not text:
        return fallback

    # Try full JSON parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try to extract substring that looks like JSON object
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end]
            return json.loads(json_str)
    except Exception:
        pass

    # As a last attempt, return fallback but include the raw text for debugging
    return {
        "rating": 6,
        "feedback": "Good effort. Could elaborate more.",
        "raw_text": text[:1000],
    }


@dataclass
class FinalEvaluation:
    """
    Structured final evaluation object used to store overall summary.
    """

    overall_quality: int
    strengths: List[str]
    areas_for_improvement: List[str]
    recommendation: str
    final_feedback: str

    def model_dump(self) -> Dict[str, Any]:
        return {
            "overall_quality": int(self.overall_quality),
            "strengths": list(self.strengths or []),
            "areas_for_improvement": list(self.areas_for_improvement or []),
            "recommendation": str(self.recommendation),
            "final_feedback": str(self.final_feedback),
        }


# -------------------------
# Nodes
# -------------------------


# ===== RETRIEVAL DECISION =====


def decide_retrieval(question: str, user_id: str = "default_user"):
    """Decides whether to retrieve context based on the question."""
    try:
        index_dir = os.path.join(os.getcwd(), f"faiss_index_{user_id}")
        if not os.path.exists(index_dir):
            logger.warning("No FAISS index found, skipping retrieval.")
            return False, 1.0

        vectorstore = FAISS.load_local(
            index_dir, embeddings, allow_dangerous_deserialization=True
        )

        top_chunks = vectorstore.similarity_search_with_score(question, k=3)
        if not top_chunks:
            return False, 1.0

        min_distance = min(score for _, score in top_chunks)
        # Larger distance => less similar => need retrieval
        needs_retrieval = min_distance < 0.55

        return needs_retrieval, min_distance

    except Exception as e:
        logger.error(f"Retrieval decision error: {e}")
        return False, 1.0


# ===== STATE =====
# ---------- SETUP NODE ----------
def setup_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Initialize interview state, optionally run RAG retrieval for topic.
    """
    topic = state.get("topic", "").strip()
    question_type = state.get("question_type", "broad_followup").strip()
    user_id = state.get("user_id", "default_user")

    needs_retrieval = True
    retrieved_context = ""
    similarity_score = 0.0

    if needs_retrieval:
        try:
            index_dir = os.path.join(os.getcwd(), f"faiss_index_{user_id}")
            vectorstore = FAISS.load_local(
                index_dir, embeddings, allow_dangerous_deserialization=True
            )
            docs = vectorstore.similarity_search(topic, k=3)
            retrieved_context = "\n\n".join([doc.page_content for doc in docs])
            logger.info("Retrieved context for setup based on topic: %s", topic)
        except Exception as e:
            logger.error("Setup retrieval failed: %s", e)

    # prompt builder expects (content_text, topic, question_type)
    if retrieved_context:
        prompt = safe_prompt(get_setup_prompt(retrieved_context, topic, question_type))
    else:
        prompt = safe_prompt(get_setup_prompt("", topic, question_type))

    first_question = _safe_generate(
        prompt, "Tell me about your experience with this technology."
    )

    new_state = {
        **dict(state),
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
        "needs_retrieval": needs_retrieval,
        "retrieved_context": retrieved_context,
        "similarity_score": similarity_score,
    }
    return new_state


# ---------- GET ANSWER NODE ----------
def get_answer_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Collect user's answer (CLI) and update messages/transcript.
    Replace blocking input() if using a web frontend.
    """
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

    content_list = list(state.get("content", []))
    content_list.append(f"Q: {current_q}\nA: {answer}")

    return {
        **dict(state),
        "current_answer": answer,
        "messages": new_messages,
        "questions": list(state.get("questions", [])) + [current_q],
        "answers": list(state.get("answers", [])) + [answer],
        "content": content_list,
    }


# ---------- RETRIEVAL DECISION NODE ----------
def retrieval_decision_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Decide whether to retrieve additional context based on the current answer.
    Uses `decide_retrieval(answer, user_id)` - implement that heuristic as needed.
    """
    current_answer = state.get("current_answer", "")
    user_id = state.get("user_id", "default_user")

    if not current_answer:
        return {
            **dict(state),
            "needs_retrieval": False,
            "retrieved_context": None,
            "similarity_score": 0,
        }

    needs_retrieval, similarity_score = decide_retrieval(current_answer, user_id)
    retrieved_context = None

    if needs_retrieval:
        try:
            index_dir = os.path.join(os.getcwd(), f"faiss_index_{user_id}")
            vectorstore = FAISS.load_local(
                index_dir, embeddings, allow_dangerous_deserialization=True
            )
            docs = vectorstore.similarity_search(current_answer, k=3)
            retrieved_context = "\n\n".join([doc.page_content for doc in docs])
            logger.info(
                "Retrieved context based on answer similarity: %.2f", similarity_score
            )
        except Exception as e:
            logger.error("Answer retrieval failed: %s", e)

    return {
        **dict(state),
        "needs_retrieval": needs_retrieval,
        "retrieved_context": retrieved_context,
        "similarity_score": similarity_score,
    }


# ---------- EVALUATE QUESTION NODE ----------
def evaluate_question_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Use the LLM to evaluate both the question quality and the candidate's answer.
    Stores structured feedback in state['feedback'].
    """
    questions = list(state.get("questions", []))
    answers = list(state.get("answers", []))
    if not questions or not answers:
        logger.warning("No questions/answers to evaluate.")
        return dict(state)

    current_q = questions[-1]
    current_a = answers[-1]
    full_content = "\n".join(state.get("content", []))
    transcript = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(questions, answers)])
    messages_text = "\n".join([m.get("content", "") for m in state.get("messages", [])])

    try:
        # Ask for a question-quality evaluation
        q_prompt = get_evaluation_prompt(
            kind="question",
            full_messages=messages_text,
            full_content=full_content,
            transcript=transcript,
            last_question=current_q,
            last_answer=current_a,
        )
        q_raw = gemini_client.generate_content(q_prompt)
        q_parsed = safe_parse_json(q_raw)

        # Ask for an answer evaluation
        a_prompt = get_evaluation_prompt(
            kind="answer",
            full_messages=messages_text,
            full_content=full_content,
            transcript=transcript,
            last_question=current_q,
            last_answer=current_a,
        )
        a_raw = gemini_client.generate_content(a_prompt)
        a_parsed = safe_parse_json(a_raw)

    except Exception as e:
        logger.warning("Gemini feedback parsing failed: %s", e)
        q_parsed = {"rating": 6, "feedback": "Good effort. Could elaborate more."}
        a_parsed = {"rating": 6, "feedback": "Good effort. Could elaborate more."}

    # Normalise field names to your earlier schema if necessary
    # e.g., ensure 'rating' or 'score' consistently present
    def _norm(parsed: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(parsed)
        if "score" in parsed and "rating" not in parsed:
            out["rating"] = parsed["score"]
        if "rating" in parsed and isinstance(parsed["rating"], (float, str)):
            try:
                out["rating"] = int(parsed["rating"])
            except Exception:
                pass
        return out

    q_final = _norm(q_parsed)
    a_final = _norm(a_parsed)

    # Append to feedback list
    feedback_list = list(state.get("feedback", []))
    feedback_list.append({"question_feedback": q_final, "answer_feedback": a_final})

    logger.info(
        "Question %d evaluated: %s",
        state.get("step", 0) + 1,
        a_final.get("feedback", ""),
    )

    return {**dict(state), "feedback": feedback_list, "step": state.get("step", 0) + 1}


# ---------- GENERATE QUESTION NODE ----------
def generate_question_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Generate the next question. Uses RAG prompt if retrieved_context present.
    Adapts behavior according to `state['question_type']`.
    """
    step = state.get("step", 0)
    max_questions = state.get("max_questions", 3)
    if step >= max_questions:
        logger.warning("Max questions reached, skipping question generation.")
        return dict(state)

    topic = state.get("topic", "")
    content_list = list(state.get("content", ["No content"]))
    prompt_instruction = get_question_instruction(
        is_followup=True if "followup" in state.get("question_type", "") else False,
        is_broad=True if "broad" in state.get("question_type", "") else False,
        previous_answer=state.get("current_answer", ""),
    )

    retrieved_context = state.get("retrieved_context")
    if retrieved_context and state.get("needs_retrieval", False):
        prompt = safe_prompt(
            get_rag_question_generation_prompt(
                "\n".join(content_list), topic, step, retrieved_context
            )
        )
        logger.info("Using RAG context for question generation")
    else:
        prompt = safe_prompt(
            get_question_generation_prompt(
                "\n".join(content_list), prompt_instruction, topic, step
            )
        )
        logger.info("Using standard question generation")

    question = _safe_generate(
        prompt, f"Tell me more about your experience with {topic}."
    )
    return {**dict(state), "current_question": question}


# ---------- FINAL EVALUATION NODE ----------
def final_evaluation_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Summarize all feedback and produce a final structured evaluation.
    """
    questions = list(state.get("questions", []))
    answers = list(state.get("answers", []))
    feedback = list(state.get("feedback", []))

    if not questions or not answers:
        logger.warning("No data available for final evaluation.")
        return dict(state)

    # Compose transcript for final prompt
    transcript = ""
    for i in range(len(questions)):
        q = questions[i]
        a = answers[i] if i < len(answers) else ""
        fb = feedback[i] if i < len(feedback) else {}
        transcript += f"Q{i+1}: {q}\nA{i+1}: {a}\nFeedback: {fb.get('answer_feedback', {}).get('feedback', '')}\n\n"

    final_prompt = get_final_evaluation_prompt(transcript)
    try:
        raw_final = gemini_client.generate_content(final_prompt)
        parsed_final = safe_parse_json(raw_final)
    except Exception as e:
        logger.error("Final evaluation parsing failed: %s", e)
        parsed_final = {}

    final_eval = FinalEvaluation(
        overall_quality=int(parsed_final.get("overall_quality", 7)),
        strengths=parsed_final.get("strengths", ["Good technical depth"]),
        areas_for_improvement=parsed_final.get(
            "areas_for_improvement", ["Could elaborate on examples"]
        ),
        recommendation=parsed_final.get(
            "recommendation", "Recommended with reservations."
        ),
        final_feedback=parsed_final.get(
            "final_feedback", "Solid overall performance with scope for improvement."
        ),
    )

    logger.info("Final evaluation completed successfully.")
    return {**dict(state), "final_evaluation": final_eval.model_dump()}


# ---------- DISPLAY RESULTS NODE ----------
def display_results_node(state: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Pretty-print full interview report to console and save structured JSON to disk.
    """
    topic = state.get("topic", "N/A")
    user_id = state.get("user_id", "user")
    questions = list(state.get("questions", []))
    answers = list(state.get("answers", []))
    feedback = list(state.get("feedback", []))
    final_eval = state.get("final_evaluation", {})

    # Pretty terminal output
    sep = "=" * 70
    print("\n" + sep)
    print(f"INTERVIEW REPORT — Topic: {topic}")
    print(sep + "\n")

    for i, q in enumerate(questions, start=1):
        a = answers[i - 1] if i - 1 < len(answers) else ""
        fb = feedback[i - 1].get("answer_feedback", {}) if i - 1 < len(feedback) else {}
        q_fb = (
            feedback[i - 1].get("question_feedback", {})
            if i - 1 < len(feedback)
            else {}
        )
        print(f"Q{i}: {q}")
        print(f"A{i}: {a}\n")
        print("Question Feedback:")
        print(f"  {q_fb.get('feedback', q_fb.get('comment', 'No feedback'))}")
        print(f"  (Rating: {q_fb.get('rating', q_fb.get('score', '-'))})\n")
        print("Answer Feedback:")
        print(f"  {fb.get('feedback', 'No feedback')}")
        # if suggestions exist, show them
        suggestions = fb.get("suggestions") or fb.get("recommendations") or []
        if suggestions:
            print("  Suggestions:")
            for s in suggestions:
                print(f"   - {s}")
        print(f"  (Rating: {fb.get('rating', fb.get('score', '-'))})")
        print("-" * 70)

    # Final evaluation summary
    print("\nFINAL EVALUATION")
    print("-" * 70)
    print(f"Overall Quality: {final_eval.get('overall_quality', 'N/A')}/10")
    print("Strengths:")
    for s in final_eval.get("strengths", []):
        print(f" - {s}")
    print("Areas for improvement:")
    for a in final_eval.get("areas_for_improvement", []):
        print(f" - {a}")
    print(f"Recommendation: {final_eval.get('recommendation', 'N/A')}")
    print(f"\nFinal Feedback: {final_eval.get('final_feedback', '')}")
    print(sep + "\n")

    # Save JSON result
    try:
        os.makedirs("results", exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"results/{user_id}_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(dict(state), f, indent=2, ensure_ascii=False)
        logger.info("Results saved to %s", filename)
        print(f"Results saved to {filename}")
    except Exception as e:
        logger.error("Failed to save results: %s", e)
        print("Failed to save results:", e)

    return dict(state)
