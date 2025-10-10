import time
import json
import re
from typing import Type
from pydantic import BaseModel, Field, ValidationError
from models.gemini_model import GeminiModel
from utils.logger import setup_logger 
logger = setup_logger(__name__)  

class QuestionFeedback(BaseModel):
    rating: int = Field(0, ge=0, le=10)
    feedback: str = "No feedback"

class AnswerFeedback(BaseModel):
    rating: int = Field(0, ge=0, le=10)
    feedback: str = "No feedback"

class GeminiClient:
    """Wrapper for Gemini LLM API with retry and Pydantic validation for JSON outputs."""

    def __init__(self):
        self.model = GeminiModel

    def generate_content(self, prompt: str, retries: int = 3, delay: int = 5) -> str:
        for attempt in range(retries):
            try:
                response = self.model.generate_content(prompt)
                logger.info(f"Generated content for prompt (length {len(prompt)} chars)")
                return response.text.strip() if response.text else ""
            except Exception as e:
                logger.exception(f"Gemini API error (attempt {attempt+1}/{retries})")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    logger.error("Gemini API failed after maximum retries")
                    return ""

    def safe_parse_json(self, response_text: str, model: Type[BaseModel] = QuestionFeedback) -> dict:
        if not response_text or not response_text.strip():
            logger.warning("Empty response received; returning default model")
            return model().dict()

        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                validated = model(**data)
                return validated.dict()
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"Failed to parse/validate JSON: {e}")
                return model().dict()
        logger.warning("No JSON found in response; returning default model")
        return model().dict()


# Shared client instance
gemini_client = GeminiClient()
