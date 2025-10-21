import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
gemini_model = os.getenv("GEMINI_MODEL")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables!")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found in environment variables!")


class Settings:
    def __init__(self):
        self.gemini_api_key = GEMINI_API_KEY
        self.tavily_api_key = TAVILY_API_KEY
        self.gemini_model = gemini_model


settings = Settings()
