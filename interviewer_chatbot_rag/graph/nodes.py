import json
import textwrap
from typing import List
from pydantic import BaseModel, Field
from graph.state import InterviewState
from services.gemini_client import gemini_client, QuestionFeedback, AnswerFeedback
from config.prompts import *

# -----------------------------
# Helpers
# -----------------------------
def build_transcript(questions: List[str], answers: List[str], feedback_list: List[dict]) -> str:
    transcript = ""
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        f = feedback_list[i-1] if i-1 < len(feedback_list) else {}
        transcript += (
            f"Q{i}: {q}\nA{i}: {a}\n"
            f"Question Feedback: {f.get('question_feedback', {}).get('feedback', '')}\n"
            f"Answer Feedback: {f.get('answer_feedback', {}).get('feedback', '')}\n\n"
        )
    return transcript.strip()

def safe_prompt(fstring: str) -> str:
    """Dedent and strip multi-line f-string prompts"""
    return textwrap.dedent(fstring).strip()

# -----------------------------
# Setup Node
# -----------------------------
def setup_node(state: InterviewState) -> InterviewState:
    topic = state.get("topic", "").strip()
    question_type = state.get("question_type", "broad_followup").strip()
    cv_content = state.get("cv_content", "").strip()

    valid_types = {"broad_followup", "narrow_followup", "broad_nonfollowup", "narrow_nonfollowup"}
    if question_type not in valid_types:
        print(f"⚠️ Invalid question_type '{question_type}', defaulting to 'broad_followup'.")
        question_type = "broad_followup"

    content_list = [cv_content] if cv_content else ["No content"]

    try:
        prompt_question = safe_prompt(get_setup_prompt(cv_content, topic, question_type))
        first_question = gemini_client.generate_content(prompt_question) or \
                         "Tell me about your experience related to this topic."
    except Exception as e:
        print(f"⚠️ Error generating first question: {e}")
        first_question = "Tell me about your experience related to this topic."

    return {
        **state,
        "topic": topic,
        "question_type": question_type,
        "cv_content": cv_content,
        "content": content_list,
        "messages": [{"role": "user", "content": f"Interview topic: {topic}"}],
        "step": 0,
        "questions": [],
        "answers": [],
        "feedback": [],
        "current_question": first_question,
        "max_questions": state.get("max_questions", 5),
    }

# -----------------------------
# Get Answer Node
# -----------------------------
def get_answer_node(state: InterviewState) -> InterviewState:
    current_q = state.get("current_question")
    if not current_q:
        raise ValueError("No current_question found in state.")

    answer = state.get("user_input") or input(f"\n❓ Question {state.get('step', 0) + 1}: {current_q}\n💭 Your answer: ").strip()

    new_messages = state.get("messages", []) + [
        {"role": "interviewer", "content": current_q},
        {"role": "candidate", "content": answer}
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

# -----------------------------
# Evaluate Question Node
# -----------------------------
def evaluate_question_node(state: InterviewState) -> InterviewState:
    questions = state.get("questions", [])
    answers = state.get("answers", [])
    feedback_list = state.get("feedback", [])

    if not questions or not answers:
        print("⚠️ No questions/answers to evaluate.")
        return state

    last_q, last_a = questions[-1], answers[-1]
    transcript = build_transcript(questions[:-1], answers[:-1], feedback_list)

    full_messages = json.dumps(state.get("messages", []))
    full_content = "\n".join(state.get("content", []))

    try:
        q_prompt = safe_prompt(get_evaluation_prompt("question", full_messages, full_content, transcript, last_q, last_a))
        q_feedback_text = gemini_client.generate_content(q_prompt)
        q_feedback = gemini_client.safe_parse_json(q_feedback_text, model=QuestionFeedback)

        a_prompt = safe_prompt(get_evaluation_prompt("answer", full_messages, full_content, transcript, last_q, last_a))
        a_feedback_text = gemini_client.generate_content(a_prompt)
        a_feedback = gemini_client.safe_parse_json(a_feedback_text, model=AnswerFeedback)

        feedback = {"question_feedback": q_feedback, "answer_feedback": a_feedback}
    except Exception as e:
        print(f"⚠️ Error evaluating question/answer: {e}")
        feedback = {
            "question_feedback": {"rating": 0, "feedback": "Evaluation failed."},
            "answer_feedback": {"rating": 0, "feedback": "Evaluation failed."}
        }

    print(f"✅ Question {state.get('step', 0) + 1} evaluated.")
    return {**state, "feedback": feedback_list + [feedback], "step": state.get("step", 0) + 1}

# -----------------------------
# Generate Next Question Node
# -----------------------------
def generate_question_node(state: InterviewState) -> InterviewState:
    content_list = state.get("content", ["No content"])
    question_type = state.get("question_type", "broad_followup")
    step = state.get("step", 0)
    max_questions = state.get("max_questions", 5)

    if step >= max_questions:
        print("⚠️ Max questions reached, skipping question generation.")
        return state

    try:
        is_followup = "followup" in question_type
        is_broad = question_type.startswith("broad")
        prev_answer = state.get("answers", [""])[-1]

        prompt_instruction = safe_prompt(get_question_instruction(is_followup, is_broad, prev_answer))
        prompt_question = safe_prompt(get_question_generation_prompt("\n".join(content_list), prompt_instruction, state.get("topic", ""), step))

        question = gemini_client.generate_content(prompt_question) or f"Tell me more about {state.get('topic', '')}."
    except Exception as e:
        print(f"⚠️ Error generating question: {e}")
        question = f"Tell me more about {state.get('topic', '')}."

    return {**state, "current_question": question, "content": content_list}

# -----------------------------
# Final Evaluation Node
# -----------------------------
class FinalEvaluation(BaseModel):
    overall_quality: int = Field(0, ge=0, le=10)
    strengths: List[str] = []
    areas_for_improvement: List[str] = []
    recommendation: str = "revise"
    final_feedback: str = "No feedback available."

def final_evaluation_node(state: InterviewState) -> InterviewState:
    questions = state.get("questions", [])
    answers = state.get("answers", [])
    feedback_list = state.get("feedback", [])

    transcript = build_transcript(questions, answers, feedback_list)

    try:
        prompt = safe_prompt(get_final_evaluation_prompt(transcript))
        result_text = gemini_client.generate_content(prompt)
        print("\n🔍 Raw Gemini output:\n", result_text)
        evaluation = gemini_client.safe_parse_json(result_text, model=FinalEvaluation)
    except Exception as e:
        print(f"⚠️ Final evaluation failed: {e}")
        evaluation = FinalEvaluation().dict()

    return {**state, "final_evaluation": evaluation}

# -----------------------------
# Display Results Node
# -----------------------------
def display_results_node(state: InterviewState) -> InterviewState:
    print("\n" + "=" * 60)
    print(" INTERVIEW COMPLETE - FINAL REPORT")
    print("=" * 60)
    print(f"\n Topic: {state.get('topic', 'N/A')}\n")

    print("📝 INTERVIEW TRANSCRIPT:")
    print("-" * 40)
    for i, (q, a) in enumerate(zip(state.get("questions", []), state.get("answers", [])), 1):
        print(f"\nQ{i}: {q}")
        print(f"A{i}: {a}")

    print("\n📊 FEEDBACK SUMMARY:")
    print("-" * 40)
    for i, fb in enumerate(state.get("feedback", []), 1):
        qfb = fb.get("question_feedback", {})
        afb = fb.get("answer_feedback", {})
        print(f"\nQuestion {i}: Rating {qfb.get('rating', 0)}/10 - {qfb.get('feedback', 'N/A')}")
        print(f"Answer {i}: Rating {afb.get('rating', 0)}/10 - {afb.get('feedback', 'N/A')}")

    print("\n🏁 FINAL EVALUATION:")
    eval_data = state.get("final_evaluation", {})
    print(f"Overall Quality: {eval_data.get('overall_quality', 'N/A')}/10")
    print("Strengths:")
    for s in eval_data.get("strengths", []):
        print(f"  • {s}")
    print("Areas for Improvement:")
    for s in eval_data.get("areas_for_improvement", []):
        print(f"  • {s}")
    print(f"Recommendation: {eval_data.get('recommendation', 'N/A')}")
    print(f"Feedback: {eval_data.get('final_feedback', 'N/A')}")

    try:
        with open("interview_results.json", "w") as f:
            json.dump(state, f, indent=2)
        print("\n💾 Results saved to 'interview_results.json'")
    except Exception as e:
        print(f"⚠️ Failed to save results: {e}")

    return state

