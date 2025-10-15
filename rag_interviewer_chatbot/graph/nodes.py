import json
import textwrap
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from graph.state import InterviewState
from services.gemini_client import gemini_client, QuestionFeedback, AnswerFeedback
from config.prompts import *
from utils.logger import setup_logger

logger = setup_logger("interview_bot.nodes")


def safe_prompt(fstring: str) -> str:
    """Safely format and clean up a prompt string."""
    return textwrap.dedent(fstring).strip()


def build_transcript(
    questions: List[str], answers: List[str], feedback_list: List[Dict[str, Any]]
) -> str:
    """Build a readable transcript of all interview questions, answers, and feedback."""
    transcript_lines = []
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        f = feedback_list[i - 1] if i - 1 < len(feedback_list) else {}
        transcript_lines.append(
            f"Q{i}: {q}\nA{i}: {a}\n"
            f"Question Feedback: {f.get('question_feedback', {}).get('feedback', '')}\n"
            f"Answer Feedback: {f.get('answer_feedback', {}).get('feedback', '')}\n"
        )
    return "\n".join(transcript_lines).strip()


def _safe_generate(prompt: str, fallback: str) -> str:
    """Safely call Gemini with fallback handling."""
    try:
        return gemini_client.generate_content(prompt) or fallback
    except Exception as e:
        logger.error("Gemini generation failed: %s", e)
        return fallback


def setup_node(state: InterviewState) -> InterviewState:
    """Initializes the interview setup node and generates the first question."""
    topic = state.get("topic", "").strip()
    question_type = state.get("question_type", "broad_followup").strip()
    cv_content = state.get("cv_content", "").strip()

    valid_types = {
        "broad_followup",
        "narrow_followup",
        "broad_nonfollowup",
        "narrow_nonfollowup",
    }
    if question_type not in valid_types:
        logger.warning(
            "Invalid question_type '%s', defaulting to 'broad_followup'.", question_type
        )
        question_type = "broad_followup"

    prompt = safe_prompt(get_setup_prompt(cv_content, topic, question_type))
    first_question = _safe_generate(
        prompt, "Tell me about your experience related to this topic."
    )

    return {
        **state,
        "topic": topic,
        "question_type": question_type,
        "cv_content": cv_content,
        "content": [cv_content or "No content"],
        "messages": [{"role": "user", "content": f"Interview topic: {topic}"}],
        "step": 0,
        "questions": [],
        "answers": [],
        "feedback": [],
        "current_question": first_question,
        "max_questions": state.get("max_questions", 5),
    }


def get_answer_node(state: InterviewState) -> InterviewState:
    """Captures the candidate's answer for the current question."""
    current_q = state.get("current_question")
    if not current_q:
        raise ValueError("No current_question found in state.")

    answer = (
        state.get("user_input")
        or input(
            f"\n❓ Question {state.get('step', 0) + 1}: {current_q}\n💭 Your answer: "
        ).strip()
    )

    new_messages = state.get("messages", []) + [
        {"role": "interviewer", "content": current_q},
        {"role": "candidate", "content": answer},
    ]

    content_list = state.get("content", [])
    content_list.append(f"Q: {current_q}\nA: {answer}")

    return {
        **state,
        "current_answer": answer,
        "messages": new_messages,
        "questions": state.get("questions", []) + [current_q],
        "answers": state.get("answers", []) + [answer],
        "content": content_list,
    }


def evaluate_question_node(state: InterviewState) -> InterviewState:
    """Evaluates the most recent question and answer using Gemini feedback."""
    questions, answers = state.get("questions", []), state.get("answers", [])
    feedback_list = state.get("feedback", [])

    if not questions or not answers:
        logger.warning("No questions/answers to evaluate.")
        return state

    last_q, last_a = questions[-1], answers[-1]
    transcript = build_transcript(questions[:-1], answers[:-1], feedback_list)
    full_messages = json.dumps(state.get("messages", []))
    full_content = "\n".join(state.get("content", []))

    def _get_feedback(kind: str, model):
        prompt = safe_prompt(
            get_evaluation_prompt(
                kind, full_messages, full_content, transcript, last_q, last_a
            )
        )
        text = _safe_generate(prompt, '{"rating":0,"feedback":"Evaluation failed."}')
        return gemini_client.safe_parse_json(text, model=model)

    try:
        q_feedback = _get_feedback("question", QuestionFeedback)
        a_feedback = _get_feedback("answer", AnswerFeedback)
        feedback = {"question_feedback": q_feedback, "answer_feedback": a_feedback}
    except Exception as e:
        logger.error("Error evaluating question/answer: %s", e)
        feedback = {
            "question_feedback": {"rating": 0, "feedback": "Evaluation failed."},
            "answer_feedback": {"rating": 0, "feedback": "Evaluation failed."},
        }

    logger.info("Question %d evaluated.", state.get("step", 0) + 1)
    return {
        **state,
        "feedback": feedback_list + [feedback],
        "step": state.get("step", 0) + 1,
    }


def generate_question_node(state: InterviewState) -> InterviewState:
    """Generates the next interview question based on the user's previous answer."""
    step = state.get("step", 0)
    max_questions = state.get("max_questions", 5)
    if step >= max_questions:
        logger.warning("Max questions reached, skipping question generation.")
        return state

    question_type = state.get("question_type", "broad_followup")
    content_list = state.get("content", ["No content"])
    prev_answer = state.get("answers", [""])[-1]
    is_followup = "followup" in question_type
    is_broad = question_type.startswith("broad")

    instruction = safe_prompt(
        get_question_instruction(is_followup, is_broad, prev_answer)
    )
    prompt = safe_prompt(
        get_question_generation_prompt(
            "\n".join(content_list), instruction, state.get("topic", ""), step
        )
    )

    question = _safe_generate(prompt, f"Tell me more about {state.get('topic', '')}.")
    return {**state, "current_question": question, "content": content_list}


class FinalEvaluation(BaseModel):
    overall_quality: int = Field(0, ge=0, le=10)
    strengths: List[str] = []
    areas_for_improvement: List[str] = []
    recommendation: str = "revise"
    final_feedback: str = "No feedback available."


def final_evaluation_node(state: InterviewState) -> InterviewState:
    """Generates the final evaluation report based on the interview transcript."""
    transcript = build_transcript(
        state.get("questions", []),
        state.get("answers", []),
        state.get("feedback", []),
    )

    try:
        prompt = safe_prompt(get_final_evaluation_prompt(transcript))
        result_text = _safe_generate(prompt, "{}")
        logger.debug("Raw Gemini output: %s", result_text)
        evaluation = gemini_client.safe_parse_json(result_text, model=FinalEvaluation)
    except Exception as e:
        logger.error("Final evaluation failed: %s", e)
        evaluation = FinalEvaluation().dict()

    return {**state, "final_evaluation": evaluation}


def display_results_node(state: InterviewState) -> InterviewState:
    """Logs and saves the final interview report to a JSON file."""
    logger.info("INTERVIEW COMPLETE - FINAL REPORT")
    logger.info("Topic: %s", state.get("topic", "N/A"))

    for i, (q, a) in enumerate(
        zip(state.get("questions", []), state.get("answers", [])), 1
    ):
        logger.info("Q%d: %s", i, q)
        logger.info("A%d: %s", i, a)

    for i, fb in enumerate(state.get("feedback", []), 1):
        qfb, afb = fb.get("question_feedback", {}), fb.get("answer_feedback", {})
        logger.info(
            "Question %d: Rating %d/10 - %s",
            i,
            qfb.get("rating", 0),
            qfb.get("feedback", "N/A"),
        )
        logger.info(
            "Answer %d: Rating %d/10 - %s",
            i,
            afb.get("rating", 0),
            afb.get("feedback", "N/A"),
        )

    eval_data = state.get("final_evaluation", {})
    logger.info("Overall Quality: %s/10", eval_data.get("overall_quality", "N/A"))
    logger.info("Strengths: %s", ", ".join(eval_data.get("strengths", [])))
    logger.info(
        "Areas for Improvement: %s",
        ", ".join(eval_data.get("areas_for_improvement", [])),
    )
    logger.info("Recommendation: %s", eval_data.get("recommendation", "N/A"))
    logger.info("Feedback: %s", eval_data.get("final_feedback", "N/A"))

    try:
        with open("interview_results.json", "w") as f:
            json.dump(state, f, indent=2)
        logger.info("Results saved to 'interview_results.json'")
    except Exception as e:
        logger.error("Failed to save results: %s", e)

    return state
