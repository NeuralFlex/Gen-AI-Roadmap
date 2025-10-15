import google.generativeai as genai
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Configure Gemini with API key
try:
    genai.configure(api_key=settings.gemini_api_key)
    GeminiModel = genai.GenerativeModel(settings.gemini_model)
    logger.info(f"Gemini model '{settings.gemini_model}' initialized successfully.")
except Exception as e:
    logger.exception(f"Failed to initialize Gemini model: {e}")
    GeminiModel = None
