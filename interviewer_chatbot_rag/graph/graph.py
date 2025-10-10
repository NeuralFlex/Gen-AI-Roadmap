# graph.py
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

# Node constants...
SETUP_NODE = "setup"
GET_ANSWER_NODE = "get_answer"
EVALUATE_QUESTION_NODE = "evaluate_question"
GENERATE_QUESTION_NODE = "generate_question"
FINAL_EVALUATION_NODE = "final_evaluation"
DISPLAY_RESULTS_NODE = "display_results"

def should_continue(state: InterviewState) -> str:
    step = state.get("step", 0)
    max_questions = state.get("max_questions", 5)
    if not isinstance(step, int) or not isinstance(max_questions, int):
        print("⚠️ Warning: Invalid state values detected. Ending interview.")
        return FINAL_EVALUATION_NODE
    return GENERATE_QUESTION_NODE if step < max_questions else FINAL_EVALUATION_NODE

def create_interview_graph():
    builder = StateGraph(InterviewState)
    builder.add_node(SETUP_NODE, setup_node)
    builder.add_node(GET_ANSWER_NODE, get_answer_node)
    builder.add_node(EVALUATE_QUESTION_NODE, evaluate_question_node)
    builder.add_node(GENERATE_QUESTION_NODE, generate_question_node)
    builder.add_node(FINAL_EVALUATION_NODE, final_evaluation_node)
    builder.add_node(DISPLAY_RESULTS_NODE, display_results_node)

    builder.set_entry_point(SETUP_NODE)
    builder.add_edge(SETUP_NODE, GET_ANSWER_NODE)
    builder.add_edge(GET_ANSWER_NODE, EVALUATE_QUESTION_NODE)
    builder.add_conditional_edges(
        EVALUATE_QUESTION_NODE,
        should_continue,
        {GENERATE_QUESTION_NODE: GENERATE_QUESTION_NODE,
         FINAL_EVALUATION_NODE: FINAL_EVALUATION_NODE}
    )
    builder.add_edge(GENERATE_QUESTION_NODE, GET_ANSWER_NODE)
    builder.add_edge(FINAL_EVALUATION_NODE, DISPLAY_RESULTS_NODE)
    builder.add_edge(DISPLAY_RESULTS_NODE, END)

    return builder.compile()
