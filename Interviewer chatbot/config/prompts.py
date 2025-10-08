"""
Interview System Prompts
Centralized prompt templates for the AI Interviewer system
"""

# Setup and Initial Question Prompts
def get_setup_prompt(content_list: str, topic: str, question_type: str) -> str:
    """Prompt for generating the first question"""
    question_style = "Ask a broad, general question." if question_type.startswith('broad') else "Ask a specific, detailed question."
    
    return f"""
    You are an expert interviewer. Using the following reference content:
    {content_list}

    Generate question #1 for the topic: {topic}.
    {question_style}
    Return ONLY the question text.
    """

# Question Generation Prompts
def get_question_generation_prompt(updated_content: str, prompt_instruction: str, topic: str, step: int) -> str:
    """Prompt for generating follow-up questions"""
    return f"""
    You are an expert interviewer. Using the following reference content:
    {updated_content}

    {prompt_instruction}
    Topic: {topic}
    Question number: {step + 1}
    Return ONLY the question text.
    """

def get_question_instruction(question_type: str, is_followup: bool, is_broad: bool, previous_answer: str = "") -> str:
    """Generate the instruction part for question generation"""
    if is_followup:
        return f"Generate a {'broad, general' if is_broad else 'specific, detailed'} follow-up question that directly probes details from the previous answer: {previous_answer}."
    else:
        return f"Generate a {'broad, general' if is_broad else 'specific, detailed'} question that explores a new aspect of the topic, independent of the previous answer."

# Evaluation Prompts
def get_question_evaluation_prompt(full_messages: str, full_content: str, transcript: str, last_q: str, last_a: str) -> str:
    """Prompt for evaluating question quality"""
    return f"""
    You are an expert interviewer. Evaluate the following question for its clarity, relevance, and ability to probe understanding, considering the ENTIRE interview history, accumulated context, all previous messages, questions, answers, and feedback.

    Full Interview History (Messages): {full_messages}
    Accumulated Context (Search Snippets): {full_content}
    Previous Q&A Transcript: {transcript}
    Current Question: {last_q}
    Current Candidate Answer: {last_a}

    Provide a rating (1-10) for question quality and 2-3 sentence feedback. Consider how well this question builds on prior answers, avoids repetition, incorporates context, and advances the topic.
    Return in JSON format:
    {{
        "rating": 0,
        "feedback": "..."
    }}
    """

def get_answer_evaluation_prompt(full_messages: str, full_content: str, transcript: str, last_q: str, last_a: str) -> str:
    """Prompt for evaluating answer quality"""
    return f"""
    You are an expert interviewer. Evaluate the following candidate answer for its clarity, relevance, depth, and alignment with the question, considering the ENTIRE interview history and context.

    Full Interview History (Messages): {full_messages}
    Accumulated Context (Search Snippets): {full_content}
    Previous Q&A Transcript: {transcript}
    Current Question: {last_q}
    Current Candidate Answer: {last_a}

    Provide a rating (1-10) for answer quality and 2-3 sentence feedback. Highlight strengths and areas for improvement.
    Return in JSON format:
    {{
        "rating": 0,
        "feedback": "..."
    }}
    """

# Final Evaluation Prompt
def get_final_evaluation_prompt(transcript: str) -> str:
    """Prompt for final evaluation of all questions"""
    return f"""
    Based on this transcript, produce a JSON summary evaluation of the questions:
    {transcript}

    JSON format ONLY:
    {{
        "overall_quality": 0-10,
        "strengths": ["..."],
        "areas_for_improvement": ["..."],
        "recommendation": "keep/revise/remove",
        "final_feedback": "..."
    }}
    """