


# main.py
from utils.cv_tools import load_cv_from_path
from graph.graph import create_interview_graph
import os
def main():
    # Instantiate the graph at runtime
    # topic = input("What topic do you want interview to be of: ")
    cv_path = input("Enter a path to user's cv: ").strip()
    if not os.path.isfile(cv_path):
        print(f"❌ CV file not found at {cv_path}")
        return
    try:
        cv_data = load_cv_from_path(cv_path)
    except Exception as e: 
        print(f"failed to load cv {e}")
    topic = cv_data["topic"]

    print("\nChoose question style:")
    print("1. Broad, follow-up questions (general, builds on previous answers)")
    print("2. Narrow, follow-up questions (specific, probes details from previous answers)")
    print("3. Broad, non-follow-up questions (general, new topic aspects)")
    print("4. Narrow, non-follow-up questions (specific, new topic aspects)")
    question_type_map = {
        "1": "broad_followup",
        "2": "narrow_followup",
        "3": "broad_nonfollowup",
        "4": "narrow_nonfollowup"
    }
    while True:
        choice = input("Enter choice (1-4): ").strip()
        if choice in question_type_map:
            question_type = question_type_map[choice]
            break
        print("⚠️ Invalid choice! Please enter 1, 2, 3, or 4.")

    interview_graph = create_interview_graph()
    
    # Initial state
    initial_state = {
        "topic": topic,
        "content": [cv_data['cv_content']],
        "cv_content": cv_data['cv_content'],

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
    }
    try:
        final_state = interview_graph.invoke(initial_state)
    except Exception as e:
        print(f"❌ Interview failed due to error: {e}")
        return

    print("\n✅ Interview completed successfully!")

if __name__ == "__main__":
    main()

