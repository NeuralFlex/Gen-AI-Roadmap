from graph.graph import create_interview_graph
from utils.logger import setup_logger
from utils.cv_tools import extract_text_from_pdf, chunk_cv_text
from services.vectorstore_service import create_vectorstore

logger = setup_logger(__name__)


def main():
    cv_path = input("Enter CV path: ").strip()
    cv_text = extract_text_from_pdf(cv_path)
    documents = chunk_cv_text(cv_text, user_id="user123")
    vectorstore = create_vectorstore(documents, user_id="user123")
    print(f"✅ CV processed: {len(documents)} chunks created and indexed.")

    topic = input("Enter interview topic/job title: ").strip()
    print("\nChoose question style:")
    print("1. Broad, follow-up questions (general, builds on previous answers)")
    print(
        "2. Narrow, follow-up questions (specific, probes details from previous answers)"
    )
    print("3. Broad, non-follow-up questions (general, new topic aspects)")
    print("4. Narrow, non-follow-up questions (specific, new topic aspects)")

    question_type_map = {
        "1": "broad_followup",
        "2": "narrow_followup",
        "3": "broad_nonfollowup",
        "4": "narrow_nonfollowup",
    }

    while True:
        choice = input("Enter choice (1-4): ").strip()
        if choice in question_type_map:
            question_type = question_type_map[choice]
            break
        print("⚠️ Invalid choice! Please enter 1, 2, 3, or 4.")

    interview_graph = create_interview_graph()

    initial_state = {
        "topic": topic,
        "content": [],
        "cv_content": cv_text[:1000],
        "questions": [],
        "answers": [],
        "feedback": [],
        "current_question": None,
        "current_answer": None,
        "step": 0,
        "max_questions": 3,
        "final_evaluation": None,
        "messages": [],
        "question_type": question_type,
        "needs_retrieval": False,
        "retrieved_context": None,
        "similarity_score": None,
        "user_id": "user123",
    }

    try:
        final_state = interview_graph.invoke(initial_state)
        logger.info("Interview completed successfully")
        print("\n✅ Interview completed successfully!")
    except Exception as e:
        logger.exception(f"Interview failed due to error: {e}")
        print(f"❌ Interview failed due to error: {e}")


if __name__ == "__main__":
    main()
