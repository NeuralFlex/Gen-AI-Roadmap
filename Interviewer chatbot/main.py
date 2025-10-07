from graph.graph import interview_graph

def main():
    initial_state = {
        "topic": "",
        "content": [],
        "questions": [],
        "answers": [],
        "feedback": [],
        "current_question": None,
        "current_answer": None,
        "step": 0,
        "max_questions": 3,
        "final_evaluation": None,
        "messages": [],
        "question_type": "broad_followup"
    }
    
    print("🚀 Starting AI Interview System...")
    final_state = interview_graph.invoke(initial_state)
    print("\n✅ Interview completed successfully!")

if __name__ == "__main__":
    main()