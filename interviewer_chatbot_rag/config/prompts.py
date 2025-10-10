"""
Interview System Prompts
Centralized prompt templates for the AI Interviewer system (CV-only version).
This module builds consistent, structured prompts for Gemini-based evaluation and question generation.
"""

import textwrap


# ===============================================================
# 🔧 Constants
# ===============================================================
ROLE_DESC = "an expert technical interviewer"


# ===============================================================
# 🧹 Utility Functions
# ===============================================================
def safe_text(text: str, max_len: int = 2000) -> str:
    """
    Clean and truncate text safely to prevent model overload or malformed prompts.

    Args:
        text (str): Input text.
        max_len (int): Maximum allowed characters (default 2000).

    Returns:
        str: Sanitized and truncated text.
    """
    if not text:
        return ""
    sanitized = str(text).replace("\r", "").replace("\t", "    ")
    return sanitized[:max_len]


def build_prompt(role_desc: str, content: str, body: str) -> str:
    """
    Build a unified, well-formatted prompt with consistent role context.

    Args:
        role_desc (str): Role or persona for the model (e.g., "expert interviewer").
        content (str): Background or CV context.
        body (str): Main instruction or task.

    Returns:
        str: Fully constructed prompt ready for Gemini.
    """
    return textwrap.dedent(f"""
        You are {role_desc}.
        Use the following CV and conversation context to guide your response:
        {safe_text(content)}

        {body}
    """).strip()


# ===============================================================
# 🏁 Setup and Initial Question Prompts
# ===============================================================
def get_setup_prompt(cv_content: str, topic: str, question_type: str) -> str:
    """
    Generate the first interview question based on the CV content and topic.

    Args:
        cv_content (str): Extracted text from the candidate's CV.
        topic (str): Interview topic.
        question_type (str): Type of question (e.g., broad_followup).

    Returns:
        str: A prompt instructing Gemini to generate the first question.
    """
    question_style = (
        "Ask a broad, general question related to their experience."
        if question_type.startswith("broad")
        else "Ask a specific, detailed question about their listed skills or experience."
    )

    body = (
        f"Generate question #1 for the topic: {topic}.\n"
        f"{question_style}\n"
        f"Return ONLY the question text."
    )

    return build_prompt(ROLE_DESC, cv_content, body)


# ===============================================================
# 💬 Question Generation Prompts
# ===============================================================
def get_question_instruction(is_followup: bool, is_broad: bool, previous_answer: str = "") -> str:
    """
    Build a guiding instruction for the next interview question.

    Args:
        is_followup (bool): Whether the question should be a follow-up.
        is_broad (bool): Whether the question should be conceptual or detailed.
        previous_answer (str): Candidate’s last answer, used for context.

    Returns:
        str: Instructional text for question generation.
    """
    style = "broad, conceptual" if is_broad else "specific, detailed"

    if is_followup:
        if previous_answer.strip():
            return f"Generate a {style} follow-up question based on this answer: {previous_answer}"
        return f"Generate a {style} follow-up question that builds naturally on the previous discussion."

    return f"Generate a {style} question exploring a new aspect of the topic or CV."


def get_question_generation_prompt(content_text: str, prompt_instruction: str, topic: str, step: int) -> str:
    """
    Generate the next interview question prompt based on prior content and topic.

    Args:
        content_text (str): Accumulated CV + Q&A context.
        prompt_instruction (str): Instruction text from get_question_instruction().
        topic (str): Interview topic.
        step (int): Current question step (0-indexed).

    Returns:
        str: A formatted prompt for Gemini question generation.
    """
    body = (
        f"{prompt_instruction}\n"
        f"Topic: {topic}\n"
        f"Question number: {step + 1}\n"
        f"Return ONLY the question text."
    )

    return build_prompt(ROLE_DESC, content_text, body)


# ===============================================================
# 🧠 Evaluation Prompts
# ===============================================================
def get_evaluation_prompt(
    kind: str,
    full_messages: str,
    full_content: str,
    transcript: str,
    last_question: str = "",
    last_answer: str = ""
) -> str:
    """
    Build an evaluation prompt for assessing the quality of a question or answer.

    Args:
        kind (str): Either "question" or "answer".
        full_messages (str): JSON dump of the interview messages.
        full_content (str): Combined CV and Q&A content.
        transcript (str): Previous Q&A transcript.
        last_question (str): Last asked question.
        last_answer (str): Candidate’s last answer.

    Returns:
        str: A prompt instructing Gemini to return structured JSON feedback.
    """
    kind_desc = "question" if kind == "question" else "candidate answer"

    body = textwrap.dedent(f"""
        Evaluate the following {kind_desc} for clarity, relevance, and quality,
        considering the entire interview history, context, and CV content.

        Interview Messages: {safe_text(full_messages)}
        CV + Q&A Context: {safe_text(full_content)}
        Transcript: {safe_text(transcript)}
        Current Question: {safe_text(last_question)}
        Current Answer: {safe_text(last_answer)}

        Provide a rating (1-10) and 2-3 sentences of feedback.
        Return in JSON format:
        {{
            "rating": 0,
            "feedback": "..."
        }}
    """).strip()

    return build_prompt(ROLE_DESC, "", body)


# ===============================================================
# 🏆 Final Evaluation Prompt
# ===============================================================
def get_final_evaluation_prompt(transcript: str) -> str:
    """
    Build a final evaluation prompt summarizing the candidate’s overall performance.

    Args:
        transcript (str): Complete interview transcript including feedback.

    Returns:
        str: A prompt instructing Gemini to produce structured JSON output.
    """
    body = textwrap.dedent(f"""
        Review the full interview transcript and produce a JSON summary
        of the candidate’s overall performance.

        Transcript:
        {safe_text(transcript)}

        Return JSON only:
        {{
            "overall_quality": 0-10,
            "strengths": ["..."],
            "areas_for_improvement": ["..."],
            "recommendation": "keep/revise/remove",
            "final_feedback": "..."
        }}
    """).strip()

    return build_prompt(ROLE_DESC, "", body)

