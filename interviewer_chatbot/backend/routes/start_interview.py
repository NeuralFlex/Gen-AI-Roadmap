from fastapi import APIRouter, Form, File, UploadFile, HTTPException
import uuid
from typing import Optional

from utils.cv_tools import extract_text_from_pdf_bytes, chunk_cv_text
from services.vectorstore_service import create_vectorstore
from graph.graph import compiled_graph

router = APIRouter(tags=["Interview"])


@router.post("/start_interview")
async def start_interview(
    job_title: str = Form(...),
    question_type: str = Form(...),
    cv: Optional[UploadFile] = File(None),
):
    """
    Start a new interview session.

    Args:
        job_title (str): The title or role for which the interview is being conducted.
        question_type (str): The type of questions (e.g., technical, behavioral).
        cv (Optional[UploadFile]): Optional CV file to extract contextual data from.

    Returns:
        dict: The initial interview question and session details.

    Raises:
        HTTPException: If interview initialization fails.
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    user_id = "user123"
    cv_text = ""

    try:
        if cv:
            cv_bytes = await cv.read()
            cv_text = extract_text_from_pdf_bytes(cv_bytes)
            document = chunk_cv_text(cv_text, user_id=user_id)
            create_vectorstore(document, user_id=user_id)

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
            "max_steps": 2,
            "final_evaluation": None,
            "messages": [],
            "question_type": question_type,
            "needs_retrieval": False,
            "retrieved_context": None,
            "similarity_score": None,
            "user_id": user_id,
        }

        final_state = compiled_graph.invoke(initial_state, config=config)

        return {
            "thread_id": thread_id,
            "status": "question",
            "message": final_state["messages"][-1]["content"],
            "current_step": final_state["step"],
            "max_steps": final_state["max_steps"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {e}")
