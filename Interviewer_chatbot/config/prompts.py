"""
Interview System Prompts
Centralized prompt templates for the AI Interviewer system
"""

import textwrap

# -------------------------------
# Utility functions
# -------------------------------

def safe_text(text: str, max_len: int = 2000) -> str:
    """
    Sanitize and truncate user-provided or large text to avoid context overflow
    and unwanted characters.
    """
    if not text:
        return ""
    # Replace problematic characters if needed
    sanitized = str(text).replace("\r", "").replace("\t", "    ")
    # Truncate if too long
    return sanitized[:max_len]

def build_prompt(role_desc: str, content: str, body: str) -> str:
    """
    Standard prompt builder to avoid duplication.
    Applies safe_text to content and strips extra whitespace.
    """
    return textwrap.dedent(f"""
        You are {role_desc}.
        Using the following reference content:
        {safe_text(content)}

        {body}
    """).strip()


# -------------------------------
# Setup and Initial Question Prompts
# -------------------------------

def get_setup_prompt(content_text: str, topic: str, question_type: str) -> str:
    """Prompt for generating the first question"""
    question_style = "Ask a broad, general question." if question_type.startswith('broad') else "Ask a specific, detailed question."
    body = f"Generate question #1 for the topic: {topic}.\n{question_style}\nReturn ONLY the question text."
    return build_prompt("an expert interviewer", content_text, body)


# -------------------------------
# Question Generation Prompts
# -------------------------------

def get_question_generation_prompt(content_text: str, prompt_instruction: str, topic: str, step: int) -> str:
    """Prompt for generating follow-up questions"""
    body = f"{prompt_instruction}\nTopic: {topic}\nQuestion number: {step + 1}\nReturn ONLY the question text."
    return build_prompt("an expert interviewer", content_text, body)

def get_question_instruction(is_followup: bool, is_broad: bool, previous_answer: str = "") -> str:
    """
    Generate the instruction part for question generation.
    
    Avoids awkward references when previous_answer is empty.
    """
    style = "broad, general" if is_broad else "specific, detailed"
    
    if is_followup:
        if previous_answer.strip():
            # Only reference previous_answer if non-empty
            return f"Generate a {style} follow-up question that directly probes details from the previous answer: {previous_answer}"
        else:
            # Generic follow-up if previous_answer is empty
            return f"Generate a {style} follow-up question that builds on the previous discussion."
    else:
        return f"Generate a {style} question that explores a new aspect of the topic, independent of the previous answer."


# -------------------------------
# Evaluation Prompts
# -------------------------------

def get_evaluation_prompt(kind: str, full_messages: str, full_content: str, transcript: str, last_question: str = "", last_answer: str = "") -> str:
    """
    Generic evaluation prompt for 'question' or 'answer'.
    Uses safe_text to prevent context overflow.
    """
    kind_desc = "question" if kind == "question" else "candidate answer"
    body = textwrap.dedent(f"""
        Evaluate the following {kind_desc} for its clarity, relevance, and ability to probe understanding,
        considering the ENTIRE interview history, accumulated context, all previous messages, questions, answers, and feedback.

        Full Interview History (Messages): {safe_text(full_messages)}
        Accumulated Context (Search Snippets): {safe_text(full_content)}
        Previous Q&A Transcript: {safe_text(transcript)}
        Current Question: {safe_text(last_question)}
        Current Candidate Answer: {safe_text(last_answer)}

        Provide a rating (1-10) for {kind_desc} quality and 2-3 sentence feedback.
        Return in JSON format:
        {{
            "rating": 0,
            "feedback": "..."
        }}
    """).strip()
    return build_prompt("an expert interviewer", "", body)


# -------------------------------
# Final Evaluation Prompt
# -------------------------------

def get_final_evaluation_prompt(transcript: str) -> str:
    """Prompt for final evaluation of all questions"""
    body = textwrap.dedent(f"""
        Based on this transcript, produce a JSON summary evaluation of the questions:
        {safe_text(transcript)}

        JSON format ONLY, with explicit types:
        {{
            "overall_quality": 0,             # integer 1-10
            "strengths": ["..."],             # list of strings
            "areas_for_improvement": ["..."], # list of strings
            "recommendation": "...",          # string: keep/revise/remove
            "final_feedback": "..."           # string
        }}
    """).strip()
    return build_prompt("an expert interviewer", "", body)
