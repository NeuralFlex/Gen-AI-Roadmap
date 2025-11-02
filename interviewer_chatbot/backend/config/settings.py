import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
DB_URI = os.getenv(
    "DATABASE_URL",
    "postgresql://interview_user:postgres@localhost:5432/interview_db",
)

gemini_model = os.getenv("GEMINI_MODEL")
gemini_embedding_model = os.getenv(
    "GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"
)

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables!")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found in environment variables!")


class Settings:
    def __init__(self):
        self.gemini_api_key = GEMINI_API_KEY
        self.tavily_api_key = TAVILY_API_KEY
        self.gemini_model = gemini_model
        self.gemini_embedding_model = gemini_embedding_model
        self.database_url = DB_URI


settings = Settings()
