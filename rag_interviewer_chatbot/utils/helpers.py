import io
import os
import PyPDF2
from docx import Document
from services.gemini_client import GeminiClient
from utils.logger import setup_logger

logger = setup_logger("interview_bot.cv_tools")

# Initialize Gemini client once per module
gemini_client = GeminiClient()


def extract_text_from_cv(filename: str, content: bytes) -> str:
    """
    Extracts raw text from a CV file based on its type.

    Supports PDF, DOCX, and TXT formats. Falls back to a generic UTF-8 decode
    for unsupported file extensions.

    Args:
        filename (str): The name of the CV file.
        content (bytes): Raw file content in bytes.

    Returns:
        str: Extracted text content. Returns an empty string if extraction fails.
    """
    try:
        filename_lower = filename.lower()

        if filename_lower.endswith(".pdf"):
            logger.debug("Extracting text from PDF: %s", filename)
            return extract_text_from_pdf(content)

        if filename_lower.endswith(".txt"):
            logger.debug("Extracting text from TXT: %s", filename)
            return content.decode("utf-8", errors="ignore")

        if filename_lower.endswith((".doc", ".docx")):
            logger.debug("Extracting text from DOC/DOCX: %s", filename)
            return extract_text_from_doc(content, filename)

        logger.warning(
            "Unsupported file type: %s. Attempting generic decode.", filename
        )
        return content.decode("utf-8", errors="ignore")

    except Exception as e:
        logger.exception("Error extracting text from CV '%s': %s", filename, e)
        return ""


def extract_text_from_pdf(content: bytes) -> str:
    """
    Extracts text content from a PDF file.

    Args:
        content (bytes): Raw PDF content.

    Returns:
        str: Combined text extracted from all PDF pages.
    """
    text = []
    try:
        pdf_file = io.BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        for page_number, page in enumerate(pdf_reader.pages, start=1):
            page_text = page.extract_text() or ""
            text.append(page_text)
            logger.debug("Extracted text from PDF page %d", page_number)

        return "\n".join(text).strip()

    except Exception as e:
        logger.error("Failed to extract text from PDF: %s", e)
        return ""


def extract_text_from_doc(content: bytes, filename: str) -> str:
    """
    Extracts text content from a DOCX file.

    Note:
        Legacy `.doc` files are not supported.

    Args:
        content (bytes): Raw DOCX content.
        filename (str): Name of the uploaded file (used for validation).

    Returns:
        str: Extracted text content. Returns a warning message if unsupported.
    """
    try:
        if filename.lower().endswith(".docx"):
            doc_file = io.BytesIO(content)
            doc = Document(doc_file)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            logger.debug("Extracted %d paragraphs from DOCX file.", len(paragraphs))
            return "\n".join(paragraphs)

        logger.warning("Legacy .doc files not supported for extraction.")
        return "Word document extraction only supports .docx"

    except Exception as e:
        logger.error("Error reading DOCX file '%s': %s", filename, e)
        return ""


def analyze_cv_for_topic(cv_text: str) -> str:
    """
    Analyzes a CV’s text content to determine the best-fitting interview topic.

    Uses Gemini AI to infer the main technical focus (e.g. "Machine Learning",
    "Backend Development", "Cloud Engineering").

    Args:
        cv_text (str): Extracted text from the CV.

    Returns:
        str: Short inferred topic phrase.
    """
    prompt = f"""
    Analyze this CV/resume and determine the most appropriate technical interview topic focus.
    Consider the candidate’s skills, experience, and technologies mentioned.

    CV Content:
    {cv_text[:3000]}

    Return ONLY the main interview topic as a short phrase.
    """

    try:
        topic = gemini_client.generate_content(prompt)

        if not topic:
            logger.warning(
                "Gemini returned no topic — defaulting to Software Development."
            )
            topic = "Software Development"

        topic = topic.strip()
        logger.info("Inferred interview topic: %s", topic)
        return topic

    except Exception as e:
        logger.exception("Error analyzing CV for topic: %s", e)
        return "Software Development"
