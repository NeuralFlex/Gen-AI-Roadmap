import time
import json
import re
from typing import Type
from pydantic import BaseModel, Field, ValidationError
from models.gemini_model import GeminiModel
from utils.logger import setup_logger

logger = setup_logger(__name__)


class QuestionFeedback(BaseModel):
    """Evaluation feedback for a generated question."""

    rating: int = Field(0, ge=0, le=10)
    feedback: str = "No feedback"


class AnswerFeedback(BaseModel):
    """Evaluation feedback for a candidate's answer."""

    rating: int = Field(0, ge=0, le=10)
    feedback: str = "No feedback"


class GeminiClient:
    """
    Wrapper around the Gemini LLM API.
    Includes retry logic and Pydantic-based JSON validation.
    """

    def __init__(self):
        if not GeminiModel:
            raise RuntimeError("GeminiModel not initialized.")
        self.model = GeminiModel

    def generate_content(self, prompt: str, retries: int = 3, delay: int = 5) -> str:
        """
        Generate text content from the Gemini model with retries.

        Args:
            prompt (str): Input prompt.
            retries (int): Retry attempts.
            delay (int): Delay between retries (in seconds).

        Returns:
            str: Generated text content or an empty string if all retries fail.
        """
        for attempt in range(retries):
            try:
                response = self.model.generate_content(prompt)
                text = response.text.strip() if response.text else ""
                logger.debug(
                    f"Generated response (len={len(text)}) on attempt {attempt+1}"
                )
                return text
            except Exception as e:
                logger.warning(f"Gemini API error (attempt {attempt+1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    logger.error("Gemini API failed after maximum retries.")
                    return ""

    def safe_parse_json(
        self, response_text: str, model: Type[BaseModel] = QuestionFeedback
    ) -> dict:
        """
        Safely parse a Gemini response as JSON and validate it with a Pydantic model.

        Args:
            response_text (str): Raw text response from Gemini.
            model (Type[BaseModel]): Pydantic model to validate against.

        Returns:
            dict: Validated JSON as dictionary or default model values.
        """
        if not response_text or not response_text.strip():
            logger.warning("Empty response received; returning default model.")
            return model().dict()

        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if not match:
            logger.warning("No JSON structure detected; returning default model.")
            return model().dict()

        try:
            data = json.loads(match.group(0))
            validated = model(**data)
            return validated.dict()
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to parse or validate JSON: {e}")
            return model().dict()


gemini_client = GeminiClient()
