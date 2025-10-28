from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from pydantic import BaseModel
import uuid
from typing import Optional

from utils.cv_tools import extract_text_from_pdf_bytes, chunk_cv_text
from services.vectorstore_service import create_vectorstore
from graph.graph import compiled_graph

app = FastAPI()


class ContinueRequest(BaseModel):
    user_response: str
    thread_id: str


@app.post("/start_interview")
async def start_interview(
    job_title: str = Form(...),
    question_type: str = Form(...),
    cv: Optional[UploadFile] = File(None),
):
    """
    Start a new interview session.

    Args:
        job_title (str): Topic for the interview.
        question_type (str): Type of questions to ask.
        cv (UploadFile, optional): Candidate's CV file.

    Returns:
        dict: JSON containing thread_id, current question, and step info.
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    user_id = "user123"
    cv_text = ""

    try:
        # Process CV if provided
        if cv:
            cv_bytes = await cv.read()
            cv_text = extract_text_from_pdf_bytes(cv_bytes)
            document = chunk_cv_text(cv_text, user_id=user_id)
            create_vectorstore(document, user_id=user_id)

        # Initialize interview state
        initial_state = {
            "topic": job_title,
            "content": [],
            "cv_content": cv_text[:1000] if cv_text else "",
            "questions": [],
            "answers": [],
            "user_response": None,
            "feedback": [],
            "current_question": None,
            "current_answer": None,
            "step": 0,
            "max_steps": 3,
            "final_evaluation": None,
            "messages": [],
            "question_type": question_type,
            "needs_retrieval": False,
            "retrieved_context": None,
            "similarity_score": None,
            "user_id": user_id,
        }

        final_state = compiled_graph.invoke(initial_state, config=config)

        # Return first question
        return {
            "thread_id": thread_id,
            "status": "question",
            "message": final_state["messages"][-1]["content"],
            "current_step": final_state["step"],
            "max_steps": final_state["max_steps"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {e}")


@app.post("/continue_interview")
async def continue_interview(req: ContinueRequest):
    """
    Continue an ongoing interview with the candidate's response.

    Args:
        req (ContinueRequest): Contains thread_id and user_response.

    Returns:
        dict: JSON containing next question or final feedback.
    """
    config = {"configurable": {"thread_id": req.thread_id}}

    try:
        # Fetch existing state
        existing_state = compiled_graph.get_state(config)
        if not existing_state:
            raise HTTPException(
                status_code=400, detail="No ongoing interview for this thread."
            )

        # Convert GraphState to dict if needed
        if hasattr(existing_state, "values"):
            state_dict = dict(existing_state.values)
        else:
            state_dict = dict(existing_state)

        # Merge user input
        state_dict["user_response"] = req.user_response
        state_dict["waiting_for_user"] = False

        # Invoke graph
        final_state = compiled_graph.invoke(state_dict, config=config)
        messages = final_state.get("messages", [])

        # Check if interview is completed
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
                "max_steps": final_state.get("max_steps", 3),
            }

        # Return next assistant message
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                return {
                    "thread_id": req.thread_id,
                    "status": "question",
                    "message": msg["content"],
                    "current_step": final_state.get("step", 1),
                    "max_steps": final_state.get("max_steps", 3),
                }

        # Fallback if no assistant message found
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

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to continue interview: {e}"
        )


@app.get("/debug/{thread_id}")
async def debug_interview(thread_id: str):
    """
    Debug endpoint to inspect the current state of an interview.

    Args:
        thread_id (str): Thread ID of the interview.

    Returns:
        dict: Current state values or error.
    """
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = compiled_graph.get_state(config)
        if not state:
            return {"error": "No state found for this thread."}

        return {
            "thread_id": thread_id,
            "values": getattr(state, "values", state),
            "next_node": getattr(state, "next", None),
            "config": getattr(state, "config", None),
        }
    except Exception as e:
        return {"error": str(e)}
