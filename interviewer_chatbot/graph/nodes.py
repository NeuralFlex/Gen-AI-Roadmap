import json
from typing import Dict, List
from graph.state import InterviewState
from services.gemini_client import gemini_client, QuestionFeedback, AnswerFeedback
from services.tavily_client import tavily_service
from config.prompts import *
from utils.logger import setup_logger

logger = setup_logger(__name__)

# -----------------------------
# Setup Node
# -----------------------------
def setup_node(state: InterviewState) -> InterviewState:
    """Initializes the interview: topic, question_type, content, first question."""
    topic = state.get("topic", "").strip()
    question_type = state.get("question_type", "broad_followup").strip()
    valid_types = {"broad_followup", "narrow_followup", "broad_nonfollowup", "narrow_nonfollowup"}
    if question_type not in valid_types:
        logger.warning(f"Invalid question_type '{question_type}', defaulting to 'broad_followup'.")
        question_type = "broad_followup"

    # Fetch initial content safely
    try:
        content_list = tavily_service.search(f"key areas for interview on: {topic}")
        if not isinstance(content_list, list):
            logger.warning("Tavily returned invalid content, using empty list.")
            content_list = []
    except Exception as e:
        logger.error(f"Error fetching content from Tavily: {e}")
        content_list = []

    initial_messages = [{"role": "user", "content": f"Interview topic: {topic}"}]
    try:
        prompt_question = get_setup_prompt("\n".join(content_list), topic, question_type)
        first_question = gemini_client.generate_content(prompt_question) or "Tell me about your interest in this topic."
    except Exception as e:
        logger.error(f"Error generating first question: {e}")
        first_question = "Tell me about your interest in this topic."

    logger.info(f"Setup complete for topic '{topic}' with question type '{question_type}'.")
    return {
        **state,
        "topic": topic,
        "question_type": question_type,
        "content": content_list,
        "messages": initial_messages,
        "step": 0,
        "questions": [],
        "answers": [],
        "feedback": [],
        "current_question": first_question,
        "max_questions": state.get("max_questions", 5)
    }

# -----------------------------
# Get Answer Node
# -----------------------------
def get_answer_node(state: InterviewState) -> InterviewState:
    """Captures candidate's answer for current question."""
    current_q = state.get("current_question")
    if not current_q:
        raise ValueError("No current_question found in state.")

    answer = state.get("user_input")
    if answer is None:
        answer = input(f"\n❓ Question {state.get('step',0)+1}: {current_q}\n💭 Your answer: ").strip()

    logger.info(f"Captured answer for question {state.get('step',0)+1}")
    new_messages = state.get("messages", []) + [
        {"role": "interviewer", "content": current_q},
        {"role": "candidate", "content": answer}
    ]

    return {
        **state,
        "current_answer": answer,
        "messages": new_messages,
        "questions": state.get("questions", []) + [current_q],
        "answers": state.get("answers", []) + [answer]
    }

# -----------------------------
# Evaluate Question Node
# -----------------------------
def evaluate_question_node(state: InterviewState) -> InterviewState:
    """Generates feedback for last question and answer using GeminiClient."""
    questions = state.get("questions", [])
    answers = state.get("answers", [])
    feedback_list = state.get("feedback", [])

    if not questions or not answers:
        logger.warning("No questions/answers to evaluate.")
        return state

    last_q = questions[-1]
    last_a = answers[-1]

    transcript = ""
    for i in range(len(feedback_list)):
        f = feedback_list[i]
        q = questions[i]
        a = answers[i]
        transcript += (
            f"Previous Q{i+1}: {q}\n"
            f"Previous A{i+1}: {a}\n"
            f"Previous Feedback: {f.get('question_feedback', {}).get('feedback', '')}\n\n"
        )

    full_messages = json.dumps(state.get("messages", []))
    full_content = "\n".join(state.get("content", []))

    try:
        # Generic evaluation for question
        q_feedback_text = gemini_client.generate_content(get_evaluation_prompt(
            kind="question",
            full_messages=full_messages,
            full_content=full_content,
            transcript=transcript,
            last_question=last_q,
            last_answer=last_a
        ))
        q_feedback = gemini_client.safe_parse_json(q_feedback_text, model=QuestionFeedback)

        # Generic evaluation for answer
        a_feedback_text = gemini_client.generate_content(get_evaluation_prompt(
            kind="answer",
            full_messages=full_messages,
            full_content=full_content,
            transcript=transcript,
            last_question=last_q,
            last_answer=last_a
        ))
        a_feedback = gemini_client.safe_parse_json(a_feedback_text, model=AnswerFeedback)

        feedback = {"question_feedback": q_feedback, "answer_feedback": a_feedback}
        logger.info(f"Question {state.get('step',0)+1} evaluated successfully.")
    except Exception as e:
        logger.error(f"Error evaluating question/answer: {e}")
        feedback = {
            "question_feedback": {"rating": 0, "feedback": "Evaluation failed."},
            "answer_feedback": {"rating": 0, "feedback": "Evaluation failed."}
        }

    return {
        **state,
        "feedback": feedback_list + [feedback],
        "step": state.get("step", 0) + 1
    }

# -----------------------------
# Generate Next Question Node
# -----------------------------
def generate_question_node(state: InterviewState) -> InterviewState:
    """Generates the next question."""
    content_list = state.get("content", [])
    question_type = state.get("question_type", "broad_followup")
    step = state.get("step", 0)
    max_questions = state.get("max_questions", 5)

    if step >= max_questions:
        logger.info("Max questions reached, skipping question generation.")
        return state

    # Add context from last Q&A
    if step > 0 and state.get("questions") and state.get("answers"):
        last_q = state["questions"][-1]
        last_a = state["answers"][-1]
        try:
            tavily_results = tavily_service.search(f"{state.get('topic')} interview context: Q: {last_q} A: {last_a}")
            if isinstance(tavily_results, list):
                content_list += tavily_results
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")

    try:
        last_answer_text = state["answers"][-1] if state.get("answers") else ""
        prompt_instruction = get_question_instruction(
            is_followup="followup" in question_type,
            is_broad="broad" in question_type,
            previous_answer=last_answer_text
        )
        prompt_question = get_question_generation_prompt(
            "\n".join(content_list),
            prompt_instruction,
            state.get("topic", ""),
            step
        )
        question = gemini_client.generate_content(prompt_question) or f"Tell me more about {state.get('topic','')}."
        logger.info(f"Generated next question for step {step+1}")
    except Exception as e:
        logger.error(f"Error generating question: {e}")
        question = f"Tell me more about {state.get('topic','')}."

    return {
        **state,
        "current_question": question,
        "content": content_list
    }

# -----------------------------
# Final Evaluation Node
# -----------------------------
from pydantic import BaseModel, Field

class FinalEvaluation(BaseModel):
    overall_quality: int = Field(0, ge=0, le=10)
    strengths: List[str] = []
    areas_for_improvement: List[str] = []
    recommendation: str = "revise"
    final_feedback: str = "Failed to generate evaluation."

def final_evaluation_node(state: InterviewState) -> InterviewState:
    """Generates final evaluation of the interview."""
    questions = state.get("questions", [])
    answers = state.get("answers", [])
    feedback_list = state.get("feedback", [])

    transcript = ""
    for i in range(min(len(questions), len(answers), len(feedback_list))):
        q = questions[i]
        a = answers[i]
        f = feedback_list[i]
        transcript += (
            f"Q{i+1}: {q}\nA{i+1}: {a}\n"
            f"Question Feedback: {f.get('question_feedback', {}).get('feedback','')}"
            f" (Rating: {f.get('question_feedback', {}).get('rating',0)})\n"
            f"Answer Feedback: {f.get('answer_feedback', {}).get('feedback','')}"
            f" (Rating: {f.get('answer_feedback', {}).get('rating',0)})\n\n"
        )

    try:
        prompt = get_final_evaluation_prompt(transcript)
        response_text = gemini_client.generate_content(prompt)
        evaluation = gemini_client.safe_parse_json(response_text, model=FinalEvaluation)
        logger.info("Final evaluation generated successfully.")
    except Exception as e:
        logger.error(f"Final evaluation failed: {e}")
        evaluation = FinalEvaluation().dict()

    return {**state, "final_evaluation": evaluation}

# -----------------------------
# Display Results Node
# -----------------------------
def display_results_node(state: InterviewState) -> InterviewState:
    """Displays interview results and saves JSON file."""
    logger.info("Displaying final interview results.")
    print("\n" + "=" * 60)
    print(" INTERVIEW COMPLETE - FINAL REPORT")
    print("=" * 60)
    print(f"\n Topic: {state.get('topic','N/A')}")

    print("\n📝 INTERVIEW TRANSCRIPT:")
    print("-"*40)
    for i, (q, a) in enumerate(zip(state.get("questions", []), state.get("answers", [])), 1):
        print(f"\nQ{i}: {q}")
        print(f"A{i}: {a}")

    print("\n\n📊 DETAILED FEEDBACK:")
    print("-"*40)
    for i, (q, a, f) in enumerate(zip(state.get("questions", []), state.get("answers", []), state.get("feedback", [])), 1):
        q_fb = f.get("question_feedback", {})
        a_fb = f.get("answer_feedback", {})
        print(f"\n{'='*50}")
        print(f"QUESTION {i} ANALYSIS:")
        print(f"{'='*50}")
        print(f"Question: {q}")
        print(f"Answer: {a}")
        print(f"\nQuestion Feedback: {q_fb.get('feedback','N/A')}")
        print(f"Question Rating: {q_fb.get('rating',0)}/10")
        print(f"\nAnswer Feedback: {a_fb.get('feedback','N/A')}")
        print(f"Answer Rating: {a_fb.get('rating',0)}/10")

    print("\n\n🏁 FINAL EVALUATION:")
    print("-"*40)
    eval_data = state.get("final_evaluation", {})
    print(f"Overall Quality: {eval_data.get('overall_quality','N/A')}/10")
    print("\nStrengths:")
    for s in eval_data.get("strengths", []):
        print(f"  • {s}")
    print("\nAreas for Improvement:")
    for a in eval_data.get("areas_for_improvement", []):
        print(f"  • {a}")
    print(f"\nRecommendation: {eval_data.get('recommendation','N/A')}")
    print(f"\nFinal Feedback: {eval_data.get('final_feedback','N/A')}")

    try:
        with open("interview_results.json","w") as f:
            json.dump(state,f,indent=2)
        logger.info("Results saved to 'interview_results.json'.")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")

    return state
