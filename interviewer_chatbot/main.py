# import os
# from utils.cv_tools import load_cv_from_path
# from graph.graph import create_interview_graph
# from utils.logger import setup_logger

# logger = setup_logger("interview_bot.main")


# def prompt_question_type() -> str:
#     """Prompt user to choose the style of interview questions."""
#     print("\nChoose question style:")
#     print("1. Broad, follow-up questions (general, builds on previous answers)")
#     print(
#         "2. Narrow, follow-up questions (specific, probes details from previous answers)"
#     )
#     print("3. Broad, non-follow-up questions (general, new topic aspects)")
#     print("4. Narrow, non-follow-up questions (specific, new topic aspects)")

#     question_type_map = {
#         "1": "broad_followup",
#         "2": "narrow_followup",
#         "3": "broad_nonfollowup",
#         "4": "narrow_nonfollowup",
#     }

#     while True:
#         choice = input("Enter choice (1-4): ").strip()
#         if choice in question_type_map:
#             return question_type_map[choice]
#         print("⚠️ Invalid choice! Please enter 1, 2, 3, or 4.")


# def main() -> None:
#     """Main entry point for running the AI Interviewer."""
#     logger.info("Initializing Interview Bot...")

#     cv_path = input("Enter path to the user's CV: ").strip()
#     if not os.path.isfile(cv_path):
#         logger.error("CV file not found at path: %s", cv_path)
#         return

#     try:
#         cv_data = load_cv_from_path(cv_path)
#         logger.info("CV successfully loaded from: %s", cv_path)
#     except Exception as e:
#         logger.exception("Failed to load CV: %s", e)
#         return

#     topic = cv_data.get("topic", "").strip()
#     if not topic:
#         logger.warning("No topic found in CV. Defaulting to 'General Experience'.")
#         topic = "General Experience"

#     question_type = prompt_question_type()
#     logger.info("Selected question type: %s", question_type)

#     try:
#         interview_graph = create_interview_graph()
#         logger.info("Interview graph successfully initialized.")
#     except Exception as e:
#         logger.exception("Failed to create interview graph: %s", e)
#         return

#     # Initialize interview state
#     initial_state = {
#         "topic": topic,
#         "cv_content": cv_data.get("cv_content", ""),
#         "content": [cv_data.get("cv_content", "")],
#         "questions": [],
#         "answers": [],
#         "feedback": [],
#         "current_question": None,
#         "current_answer": None,
#         "step": 0,
#         "max_questions": 3,
#         "final_evaluation": None,
#         "messages": [],
#         "question_type": question_type,
#     }

#     try:
#         final_state = interview_graph.invoke(initial_state)
#         logger.info("Interview process completed successfully.")
#     except Exception as e:
#         logger.exception("Interview execution failed: %s", e)
#         return

#     print("\n✅ Interview completed successfully!")
#     logger.info("Final state keys: %s", list(final_state.keys()))


# if __name__ == "__main__":
#     main()


import os
from utils.cv_tools import load_cv_from_path
from graph.graph import create_interview_graph
from utils.logger import setup_logger

logger = setup_logger("interview_bot.main")

MAX_QUESTIONS = 3


def prompt_question_type() -> str:
    """Prompt user to choose the style of interview questions."""
    question_type_map = {
        "1": "broad_followup",
        "2": "narrow_followup",
        "3": "broad_nonfollowup",
        "4": "narrow_nonfollowup",
    }

    prompt_text = (
        "\nChoose question style:\n"
        "1. Broad, follow-up questions (general, builds on previous answers)\n"
        "2. Narrow, follow-up questions (specific, probes details from previous answers)\n"
        "3. Broad, non-follow-up questions (general, new topic aspects)\n"
        "4. Narrow, non-follow-up questions (specific, new topic aspects)\n"
    )

    while True:
        choice = input(prompt_text + "Enter choice (1-4): ").strip()
        if choice in question_type_map:
            logger.info("User selected question type: %s", question_type_map[choice])
            return question_type_map[choice]
        logger.warning("Invalid choice entered: %s. Prompting again.", choice)


def main() -> None:
    """Main entry point for running the AI Interviewer."""
    logger.info("Initializing Interview Bot...")

    cv_path = input("Enter path to the user's CV: ").strip()
    if not os.path.isfile(cv_path):
        logger.error("CV file not found at path: %s", cv_path)
        return

    try:
        cv_data = load_cv_from_path(cv_path)
        logger.info("CV successfully loaded from: %s", cv_path)
    except Exception as e:
        logger.exception("Failed to load CV: %s", e)
        return

    topic = cv_data.get("topic") or "General Experience"
    if not cv_data.get("topic"):
        logger.warning("No topic found in CV. Defaulting to '%s'.", topic)

    question_type = prompt_question_type()

    try:
        interview_graph = create_interview_graph()
        logger.info("Interview graph successfully initialized.")
    except Exception as e:
        logger.exception("Failed to create interview graph: %s", e)
        return

    initial_state = {
        "topic": topic,
        "cv_content": cv_data.get("cv_content", ""),
        "content": [cv_data.get("cv_content", "")],
        "questions": [],
        "answers": [],
        "feedback": [],
        "current_question": None,
        "current_answer": None,
        "step": 0,
        "max_questions": MAX_QUESTIONS,
        "final_evaluation": None,
        "messages": [],
        "question_type": question_type,
    }

    try:
        final_state = interview_graph.invoke(initial_state)
        logger.info("Interview process completed successfully.")
    except Exception as e:
        logger.exception("Interview execution failed: %s", e)
        return

    logger.info("Interview completed. Final state keys: %s", list(final_state.keys()))
    print("\n✅ Interview completed successfully!")


if __name__ == "__main__":
    main()
