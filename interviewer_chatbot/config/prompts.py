"""
Interview System Prompts
Centralized prompt templates for the AI Interviewer system (CV-only version).
Handles structured prompt construction for Gemini-based question generation and evaluation.
"""

import textwrap
from typing import Literal


#
def safe_text(text: str, max_len: int = 2000) -> str:
    """
    Safely sanitize and truncate input text to prevent prompt overflow or malformed context.

    Args:
        text (str): Text to sanitize.
        max_len (int): Max character length (default 2000).

    Returns:
        str: Cleaned and truncated text.
    """
    if not text:
        return ""
    sanitized = str(text).replace("\r", "").replace("\t", "    ")
    return sanitized[:max_len]


def build_prompt(role_desc: str, content: str, body: str) -> str:
    """
    Unified prompt builder ensuring consistent structure and role context.

    Args:
        role_desc (str): Role or persona (e.g., "expert interviewer").
        content (str): Background or context (e.g., CV or transcript).
        body (str): Main task or instruction.

    Returns:
        str: Formatted prompt string.
    """
    return textwrap.dedent(
        f"""
        You are {role_desc}.
        Use the following reference content to guide your response:
        {safe_text(content)}

        {body}
    """
    ).strip()


def get_setup_prompt(cv_content: str, topic: str, question_type: str) -> str:
    """
    Generate the first interview question prompt based on CV and topic.

    Args:
        cv_content (str): Extracted text from candidate CV.
        topic (str): Topic or skill area for the interview.
        question_type (str): Either "broad" or "specific".

    Returns:
        str: Formatted prompt for Gemini.
    """
    question_style = (
        "Ask a broad, general question about the candidate’s experience."
        if question_type.startswith("broad")
        else "Ask a specific, detailed question about their listed skills or experience."
    )

    body = f"Generate question #1 for the topic: {topic}.\n{question_style}\nReturn ONLY the question text."

    return build_prompt("an expert technical interviewer", cv_content, body)


def get_question_instruction(
    is_followup: bool, is_broad: bool, previous_answer: str = ""
) -> str:
    """
    Construct an instruction for generating the next interview question.

    Args:
        is_followup (bool): If the next question should follow up on the previous answer.
        is_broad (bool): If the question should be conceptual (True) or detailed (False).
        previous_answer (str): Candidate’s last answer, if any.

    Returns:
        str: Instructional text for Gemini.
    """
    style = "broad, conceptual" if is_broad else "specific, detailed"

    if is_followup and previous_answer.strip():
        return f"Generate a {style} follow-up question based on this answer: {previous_answer}"
    elif is_followup:
        return f"Generate a {style} follow-up question that builds naturally on the previous discussion."
    else:
        return f"Generate a {style} question exploring a new aspect of the candidate’s CV or the topic."


def get_question_generation_prompt(
    content_text: str, prompt_instruction: str, topic: str, step: int
) -> str:
    """
    Build a prompt for generating the next interview question.

    Args:
        content_text (str): Combined CV and Q&A history.
        prompt_instruction (str): Instruction text from get_question_instruction().
        topic (str): Current interview topic.
        step (int): Current question number (0-indexed).

    Returns:
        str: Formatted Gemini question generation prompt.
    """
    body = (
        f"{prompt_instruction}\n"
        f"Topic: {topic}\n"
        f"Question number: {step + 1}\n"
        f"Return ONLY the question text."
    )
    return build_prompt("an expert technical interviewer", content_text, body)


def get_evaluation_prompt(
    kind: Literal["question", "answer"],
    full_messages: str,
    full_content: str,
    transcript: str,
    last_question: str = "",
    last_answer: str = "",
) -> str:
    """
    Build a structured evaluation prompt for questions or answers.

    Args:
        kind (Literal["question", "answer"]): Type of evaluation.
        full_messages (str): JSON-like dump of conversation messages.
        full_content (str): Combined CV + conversation context.
        transcript (str): Transcript of all prior Q&A.
        last_question (str): Most recent question asked.
        last_answer (str): Most recent answer given.

    Returns:
        str: Evaluation prompt for Gemini.
    """
    kind_desc = "question" if kind == "question" else "candidate answer"

    body = textwrap.dedent(
        f"""
        Evaluate the following {kind_desc} for clarity, relevance, and quality,
        considering the entire interview context and candidate background.

        Interview Messages: {safe_text(full_messages)}
        CV + Q&A Context: {safe_text(full_content)}
        Transcript: {safe_text(transcript)}
        Current Question: {safe_text(last_question)}
        Current Answer: {safe_text(last_answer)}

        Provide a rating (1–10) and 2–3 sentences of feedback.
        Return strictly in JSON format:
        {{
            "rating": 0,
            "feedback": "..."
        }}
    """
    ).strip()

    return build_prompt("an expert technical interviewer", "", body)


# ===============================================================
# 🏁 Final Evaluation Prompt
# ===============================================================


def get_final_evaluation_prompt(transcript: str) -> str:
    """
    Generate the final evaluation prompt summarizing overall candidate performance.

    Args:
        transcript (str): Complete interview transcript with Q&A and feedback.

    Returns:
        str: Final evaluation prompt returning JSON.
    """
    body = textwrap.dedent(
        f"""
        Review the full interview transcript below and summarize the candidate’s overall performance.

        Transcript:
        {safe_text(transcript)}

        Return JSON ONLY:
        {{
            "overall_quality": 0,                # integer (1–10)
            "strengths": ["..."],                # list of strings
            "areas_for_improvement": ["..."],    # list of strings
            "recommendation": "keep/revise/remove", # recommendation decision
            "final_feedback": "..."              # short overall summary
        }}
    """
    ).strip()

    return build_prompt("an expert technical interviewer", "", body)
