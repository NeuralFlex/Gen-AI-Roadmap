import google.generativeai as genai
import time
import json
import re
from typing import Dict, Optional
from pydantic import BaseModel, Field, ValidationError
from config.settings import settings

genai.configure(api_key=settings.gemini_api_key)

class QuestionFeedback(BaseModel):
    rating: int = Field(0, ge=0, le=10)
    feedback: str = "No feedback"

class AnswerFeedback(BaseModel):
    rating: int = Field(0, ge=0, le=10)
    feedback: str = "No feedback"

class GeminiClient:
    """
    Wrapper for Gemini LLM API with retry and Pydantic validation for JSON outputs.
    """

    def __init__(self):
        """Initialize the Gemini client with the configured model."""
        self.model = genai.GenerativeModel(settings.gemini_model)

    def generate_content(self, prompt: str, retries: int = 3, delay: int = 5) -> str:
        """
        Generate text content from the Gemini model with retry logic.
        """
        for attempt in range(retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text.strip() if response.text else ""
            except Exception as e:
                print(f"Gemini API error (attempt {attempt+1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    return ""

    def safe_parse_json(self, response_text: str, model: BaseModel = QuestionFeedback) -> dict:
        """
        Safely parse JSON using Pydantic validation.

        Args:
            response_text (str): Raw text from Gemini API.
            model (BaseModel): Pydantic model to validate against.

        Returns:
            dict: Validated data as dictionary. Returns defaults if parsing fails.
        """
        if not response_text or not response_text.strip():
            return model().dict()

        # Extract JSON portion
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                validated = model(**data)
                return validated.dict()
            except (json.JSONDecodeError, ValidationError):
                return model().dict()
        return model().dict()
gemini_client = GeminiClient()