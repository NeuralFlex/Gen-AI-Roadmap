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
from langgraph.checkpoint.memory import MemorySaver
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

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
    return RETRIEVAL_NODE if state["needs_retrieval"] else TAVILY_SEARCH_NODE


def should_continue(state: InterviewState) -> str:
    if state.get("waiting_for_user", False):
        return END
    if state.get("step", 0) >= state.get("max_steps", 10):
        return FINAL_EVALUATION_NODE
    return GET_ANSWER_NODE


def should_generate_question(state: InterviewState) -> str:
    return (
        GENERATE_QUESTION_NODE
        if state["step"] < state["max_steps"]
        else FINAL_EVALUATION_NODE
    )


def should_start_or_wait(state: InterviewState) -> str:
    return END if state.get("waiting_for_user", False) else GET_ANSWER_NODE


def create_interview_graph() -> StateGraph:
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

    builder.add_conditional_edges(
        SETUP_NODE,
        should_start_or_wait,
        {GET_ANSWER_NODE: GET_ANSWER_NODE, END: END},
    )

    builder.add_edge(GET_ANSWER_NODE, RETRIEVAL_DECISION_NODE)

    builder.add_conditional_edges(
        RETRIEVAL_DECISION_NODE,
        should_retrieve,
        {RETRIEVAL_NODE: RETRIEVAL_NODE, TAVILY_SEARCH_NODE: TAVILY_SEARCH_NODE},
    )

    builder.add_edge(RETRIEVAL_NODE, GENERATE_QUESTION_NODE)
    builder.add_edge(TAVILY_SEARCH_NODE, GENERATE_QUESTION_NODE)

    builder.add_conditional_edges(
        GENERATE_QUESTION_NODE,
        should_continue,
        {
            GET_ANSWER_NODE: GET_ANSWER_NODE,
            EVALUATE_QUESTION_NODE: EVALUATE_QUESTION_NODE,
            FINAL_EVALUATION_NODE: FINAL_EVALUATION_NODE,
            END: END,
        },
    )

    builder.add_edge(EVALUATE_QUESTION_NODE, FINAL_EVALUATION_NODE)
    builder.add_edge(FINAL_EVALUATION_NODE, DISPLAY_RESULTS_NODE)
    builder.add_edge(DISPLAY_RESULTS_NODE, END)

    logger.info("✅ Interview graph successfully compiled with RAG ↔ Tavily logic.")

    try:
        conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
        memory = SqliteSaver(conn)
        logger.info("✅ Using SQLite checkpoint saver.")
    except Exception as e:
        logger.warning("⚠️ SQLite saver failed, using in-memory checkpoint: %s", e)
        memory = MemorySaver()

    return builder.compile(checkpointer=memory)


compiled_graph = create_interview_graph()
