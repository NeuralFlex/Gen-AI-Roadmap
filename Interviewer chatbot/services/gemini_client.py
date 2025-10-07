

import google.generativeai as genai
import time
import json
import re
from typing import Dict
from config.settings import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiClient:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash")
    
    def generate_content(self, prompt: str, retries: int = 3, delay: int = 5) -> str:
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
    
    def safe_parse_json(self, response_text: str, fallback: Dict = None) -> Dict:
        """Safely parse JSON - optimized version (matches notebook behavior)"""
        if not response_text or not response_text.strip():
            return fallback or {"rating": 0, "feedback": "Empty response from API"}
        
        # Try to extract JSON using regex first (this is what's actually working)
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                # Only show error if regex extraction also fails
                pass
        
        return fallback or {"rating": 0, "feedback": "Failed to parse JSON response"}

gemini_client = GeminiClient()