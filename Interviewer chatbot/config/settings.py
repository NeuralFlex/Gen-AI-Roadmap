import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables!")
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY not found in environment variables!")

settings = Settings()