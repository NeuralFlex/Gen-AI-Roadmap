from langgraph.graph import StateGraph, END
from graph.state import InterviewState
from graph.nodes import (
    setup_node, 
    get_answer_node, 
    evaluate_question_node,
    generate_question_node,
    final_evaluation_node,
    display_results_node
)

def should_continue(state: InterviewState) -> str:
    return "generate_question" if state['step'] < state['max_questions'] else "final_evaluation"

def create_interview_graph():
    builder = StateGraph(InterviewState)
    
    # Add nodes
    builder.add_node("setup", setup_node)
    builder.add_node("get_answer", get_answer_node)
    builder.add_node("evaluate_question", evaluate_question_node)
    builder.add_node("generate_question", generate_question_node)
    builder.add_node("final_evaluation", final_evaluation_node)
    builder.add_node("display_results", display_results_node)
    
    # Build graph
    builder.set_entry_point("setup")
    builder.add_edge("setup", "get_answer")
    builder.add_edge("get_answer", "evaluate_question")
    builder.add_conditional_edges(
        "evaluate_question",
        should_continue,
        {"generate_question": "generate_question", "final_evaluation": "final_evaluation"}
    )
    builder.add_edge("generate_question", "get_answer")
    builder.add_edge("final_evaluation", "display_results")
    builder.add_edge("display_results", END)
    
    return builder.compile()

# Create graph instance
interview_graph = create_interview_graph()