from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from graph.graph import compiled_graph

router = APIRouter(tags=["Interview"])


class ContinueRequest(BaseModel):
    """Request model for continuing an existing interview session."""

    user_response: str
    thread_id: str


@router.post("/continue_interview")
async def continue_interview(req: ContinueRequest):
    """
    Continue an existing interview session by providing a user's response.

    Args:
        req (ContinueRequest): The user's response and associated thread ID.

    Returns:
        dict: The next interview question or final evaluation.

    Raises:
        HTTPException: If continuation or state retrieval fails.
    """
    config = {"configurable": {"thread_id": req.thread_id}}

    try:
        existing_state = compiled_graph.get_state(config)
        if not existing_state:
            raise HTTPException(
                status_code=400, detail="No ongoing interview for this thread."
            )

        if hasattr(existing_state, "values"):
            state_dict = dict(existing_state.values)
        else:
            state_dict = dict(existing_state)

        state_dict["user_response"] = req.user_response
        state_dict["waiting_for_user"] = False

        final_state = compiled_graph.invoke(state_dict, config=config)
        messages = final_state.get("messages", [])

        if messages and messages[-1].get("role") == "system":
            return {
                "thread_id": req.thread_id,
                "status": "completed",
                "message": messages[-1]["content"],
                "current_step": final_state.get("step", 1),
                "max_steps": final_state.get("max_steps", 3),
            }

        if final_state.get("feedback"):
            return {
                "thread_id": req.thread_id,
                "status": "completed",
                "message": final_state["feedback"],
                "current_step": final_state.get("step", 1),
                "feedback_list": final_state["feedback"],
                "final_evaluation": final_state["final_evaluation"],
                "max_steps": final_state.get("max_steps", 3),
            }

        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                return {
                    "thread_id": req.thread_id,
                    "status": "question",
                    "message": msg["content"],
                    "current_step": final_state.get("step", 1),
                    "max_steps": final_state.get("max_steps", 3),
                }

        if messages:
            return {
                "thread_id": req.thread_id,
                "status": "unknown",
                "message": messages[-1]["content"],
                "current_step": final_state.get("step", 1),
                "max_steps": final_state.get("max_steps", 3),
            }

        raise HTTPException(
            status_code=500, detail="No response generated from the graph."
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to continue interview: {e}"
        )
