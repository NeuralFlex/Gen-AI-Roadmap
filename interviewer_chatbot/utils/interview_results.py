from utils.logger import setup_logger

logger = setup_logger(__name__)


def render_interview_results(state: dict):
    """
    Print interview results to the console.
    """
    user_id = state.get("user_id", "unknown_user")
    topic = state.get("topic", "unknown_topic")

    questions = state.get("questions", [])
    answers = state.get("answers", [])
    feedback_list = state.get("feedback", [])
    final_eval = state.get("final_evaluation", {})

    qna_section = ""
    for i, (q, a) in enumerate(zip(questions, answers)):
        fb = feedback_list[i] if i < len(feedback_list) else {}
        q_fb = fb.get("question_feedback", {}).get("feedback", "No feedback")
        a_fb = fb.get("answer_feedback", {}).get("feedback", "No feedback")
        qna_section += (
            f"Q{i+1}: {q}\n"
            f"A{i+1}: {a}\n"
            f"Question Feedback: {q_fb}\n"
            f"Answer Feedback: {a_fb}\n\n"
        )

    final_section = ""
    if final_eval:
        final_section += (
            f"Overall Quality: {final_eval.get('overall_quality', 'N/A')}\n"
            f"Recommendation: {final_eval.get('recommendation', 'N/A')}\n"
            "Strengths:\n"
            + "\n".join([f" - {s}" for s in final_eval.get("strengths", [])])
            + "\nAreas for Improvement:\n"
            + "\n".join(
                [f" - {a}" for a in final_eval.get("areas_for_improvement", [])]
            )
            + f"\nFinal Feedback: {final_eval.get('final_feedback', '')}\n"
        )

    print(f"\n📋 Interview Results for {user_id} on {topic}:\n")
    print("-" * 70)
    print(qna_section)
    print(final_section)
    print("=" * 70)
