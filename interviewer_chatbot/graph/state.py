from typing import List, Dict, Optional
from typing_extensions import TypedDict


class InterviewState(TypedDict):
    topic: str
    content: List[str]
    cv_content: str
    questions: List[str]
    answers: List[str]
    feedback: List[Dict]
    current_question: Optional[str]
    current_answer: Optional[str]
    step: int
    max_questions: int
    final_evaluation: Optional[Dict]
    messages: List[Dict]
    question_type: str
    needs_retrieval: bool
    retrieved_context: Optional[str]
    similarity_score: Optional[float]
    user_id: str
