from langgraph.graph import StateGraph, END
from graph.state import InterviewState
from graph.nodes import (
    setup_node,
    get_answer_node,
    evaluate_question_node,
    generate_question_node,
    final_evaluation_node,
    display_results_node,
)
from utils.logger import setup_logger

logger = setup_logger("interview_bot.graph")


SETUP_NODE = "setup"
GET_ANSWER_NODE = "get_answer"
EVALUATE_QUESTION_NODE = "evaluate_question"
GENERATE_QUESTION_NODE = "generate_question"
FINAL_EVALUATION_NODE = "final_evaluation"
DISPLAY_RESULTS_NODE = "display_results"


def should_continue(state: InterviewState) -> str:
    """
    Determine whether the interview should continue or end.

    Args:
        state (InterviewState): The current interview state, which includes
            the current step count and maximum question limit.

    Returns:
        str: The next node name to transition to. Either:
            - GENERATE_QUESTION_NODE → Continue interview with new question
            - FINAL_EVALUATION_NODE → End interview and perform final evaluation
    """
    step = state.get("step", 0)
    max_questions = state.get("max_questions", 5)

    if not isinstance(step, int) or not isinstance(max_questions, int):
        logger.warning(
            "Invalid state values detected (step: %s, max_questions: %s). Ending interview.",
            step,
            max_questions,
        )
        return FINAL_EVALUATION_NODE

    next_node = (
        GENERATE_QUESTION_NODE if step < max_questions else FINAL_EVALUATION_NODE
    )
    logger.debug(
        "should_continue → step=%d / max=%d → next_node=%s",
        step,
        max_questions,
        next_node,
    )
    return next_node


def create_interview_graph() -> StateGraph:
    """
    Build and compile the interview workflow graph.

    This function creates a LangGraph `StateGraph` and registers
    all the key nodes involved in the AI interview lifecycle.
    The edges define the flow of execution between these nodes.

    Flow:
        setup → get_answer → evaluate_question → (conditional) →
        generate_question or final_evaluation → display_results → END

    Returns:
        StateGraph: A compiled interview graph ready for execution.
    """
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
        {
            GENERATE_QUESTION_NODE: GENERATE_QUESTION_NODE,
            FINAL_EVALUATION_NODE: FINAL_EVALUATION_NODE,
        },
    )
    builder.add_edge(GENERATE_QUESTION_NODE, GET_ANSWER_NODE)
    builder.add_edge(FINAL_EVALUATION_NODE, DISPLAY_RESULTS_NODE)
    builder.add_edge(DISPLAY_RESULTS_NODE, END)

    logger.info("Interview graph successfully created and compiled.")
    return builder.compile()
