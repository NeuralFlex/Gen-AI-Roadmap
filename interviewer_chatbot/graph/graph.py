from langgraph.graph import StateGraph, END
from graph.state import InterviewState
from graph.nodes import (
    setup_node,
    get_answer_node,
    evaluate_question_node,
    generate_question_node,
    final_evaluation_node,
    display_results_node,
    retrieval_decision_node,
    retrieval_node,
    tavily_search_node,
)
from utils.logger import setup_logger

logger = setup_logger(__name__)

SETUP_NODE = "setup"
GET_ANSWER_NODE = "get_answer"
RETRIEVAL_DECISION_NODE = "retrieval_decision"
RETRIEVAL_NODE = "retrieval"
TAVILY_SEARCH_NODE = "tavily_search"
GENERATE_QUESTION_NODE = "generate_question"
EVALUATE_QUESTION_NODE = "evaluate_question"
FINAL_EVALUATION_NODE = "final_evaluation"
DISPLAY_RESULTS_NODE = "display_results"


def should_retrieve(state: InterviewState) -> str:
    """Decide whether to run RAG retrieval or Tavily search."""
    return RETRIEVAL_NODE if state["needs_retrieval"] else TAVILY_SEARCH_NODE


def should_continue(state: InterviewState) -> str:
    """Decide whether to continue the interview or move to final evaluation."""
    return (
        GET_ANSWER_NODE
        if state["step"] < state["max_questions"]
        else FINAL_EVALUATION_NODE
    )


def should_generate_question(state: InterviewState) -> str:
    """Determine whether to generate another question or proceed to final evaluation."""
    return (
        GENERATE_QUESTION_NODE
        if state["step"] < state["max_questions"]
        else FINAL_EVALUATION_NODE
    )


def create_interview_graph() -> StateGraph:
    """Build and compile the full interview flow graph with RAG and Tavily nodes."""
    logger.info("Initializing interview graph with RAG + Tavily search flow...")

    builder = StateGraph(InterviewState)

    builder.add_node(SETUP_NODE, setup_node)
    builder.add_node(GET_ANSWER_NODE, get_answer_node)
    builder.add_node(RETRIEVAL_DECISION_NODE, retrieval_decision_node)
    builder.add_node(RETRIEVAL_NODE, retrieval_node)
    builder.add_node(TAVILY_SEARCH_NODE, tavily_search_node)
    builder.add_node(GENERATE_QUESTION_NODE, generate_question_node)
    builder.add_node(EVALUATE_QUESTION_NODE, evaluate_question_node)
    builder.add_node(FINAL_EVALUATION_NODE, final_evaluation_node)
    builder.add_node(DISPLAY_RESULTS_NODE, display_results_node)

    builder.set_entry_point(SETUP_NODE)
    builder.add_edge(SETUP_NODE, GET_ANSWER_NODE)
    builder.add_edge(GET_ANSWER_NODE, RETRIEVAL_DECISION_NODE)

    builder.add_conditional_edges(
        RETRIEVAL_DECISION_NODE,
        should_retrieve,
        {
            RETRIEVAL_NODE: RETRIEVAL_NODE,
            TAVILY_SEARCH_NODE: TAVILY_SEARCH_NODE,
        },
    )

    builder.add_conditional_edges(
        RETRIEVAL_NODE,
        should_generate_question,
        {
            GENERATE_QUESTION_NODE: GENERATE_QUESTION_NODE,
            FINAL_EVALUATION_NODE: FINAL_EVALUATION_NODE,
        },
    )

    builder.add_conditional_edges(
        TAVILY_SEARCH_NODE,
        should_generate_question,
        {
            GENERATE_QUESTION_NODE: GENERATE_QUESTION_NODE,
            FINAL_EVALUATION_NODE: FINAL_EVALUATION_NODE,
        },
    )

    builder.add_edge(GENERATE_QUESTION_NODE, EVALUATE_QUESTION_NODE)

    builder.add_conditional_edges(
        EVALUATE_QUESTION_NODE,
        should_continue,
        {
            GET_ANSWER_NODE: GET_ANSWER_NODE,
            FINAL_EVALUATION_NODE: FINAL_EVALUATION_NODE,
        },
    )

    builder.add_edge(FINAL_EVALUATION_NODE, DISPLAY_RESULTS_NODE)
    builder.add_edge(DISPLAY_RESULTS_NODE, END)

    logger.info("Interview graph successfully compiled with RAG ↔ Tavily logic.")
    return builder.compile()
