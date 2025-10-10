import io
import PyPDF2
from docx import Document
from services.gemini_client import GeminiClient
from utils.logger import setup_logger

logger = setup_logger("interview_bot.cv_tools")

# Initialize Gemini client once per module
gemini_client = GeminiClient()


def extract_text_from_cv(filename: str, content: bytes) -> str:
    """
    Extract raw text from a CV file, based on its file type.

    Args:
        filename (str): The name or path of the uploaded CV file.
        content (bytes): Raw file content in bytes.

    Returns:
        str: Extracted text content from the file. Returns an empty string on error.
    """
    try:
        filename_lower = filename.lower()

        if filename_lower.endswith(".pdf"):
            logger.debug("Extracting text from PDF file: %s", filename)
            return extract_text_from_pdf(content)

        elif filename_lower.endswith(".txt"):
            logger.debug("Extracting text from TXT file: %s", filename)
            return content.decode("utf-8")

        elif filename_lower.endswith((".doc", ".docx")):
            logger.debug("Extracting text from DOC/DOCX file: %s", filename)
            return extract_text_from_doc(content, filename)

        else:
            logger.warning(
                "Unsupported file type for: %s. Attempting generic decode.", filename
            )
            return content.decode("utf-8", errors="ignore")

    except Exception as e:
        logger.exception("Error extracting text from CV: %s", e)
        return ""


def extract_text_from_pdf(content: bytes) -> str:
    """
    Extract text content from a PDF file.

    Args:
        content (bytes): Raw PDF content.

    Returns:
        str: Extracted text from all PDF pages.
    """
    text = ""
    try:
        pdf_file = io.BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        for page_number, page in enumerate(pdf_reader.pages, start=1):
            page_text = page.extract_text() or ""
            text += page_text + "\n"
            logger.debug("Extracted text from PDF page %d.", page_number)

    except Exception as e:
        logger.error("Failed to extract text from PDF: %s", e)

    return text.strip()


def extract_text_from_doc(content: bytes, filename: str) -> str:
    """
    Extract text content from a DOCX file. DOC files are not supported.

    Args:
        content (bytes): Raw DOCX content.
        filename (str): The name of the uploaded file (used for format validation).

    Returns:
        str: Extracted text from the document, or a warning message for unsupported formats.
    """
    try:
        if filename.lower().endswith(".docx"):
            doc_file = io.BytesIO(content)
            doc = Document(doc_file)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            logger.debug("Extracted %d paragraphs from DOCX file.", len(paragraphs))
            return "\n".join(paragraphs)
        else:
            logger.warning("Legacy .doc files not supported for extraction.")
            return "Word document extraction only supports .docx"
    except Exception as e:
        logger.error("Error reading DOCX file: %s", e)
        return ""


def analyze_cv_for_topic(cv_text: str) -> str:
    """
    Analyze CV content to determine the most appropriate interview topic.

    Uses Gemini AI to analyze CV text and infer the main technical topic focus,
    such as 'Machine Learning', 'Backend Development', or 'Cloud Engineering'.

    Args:
        cv_text (str): Extracted text from a CV/resume.

    Returns:
        str: A short topic phrase (e.g. "Machine Learning") inferred from the CV.
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
        logger.info("Extracted interview topic: %s", topic)
        return topic

    except Exception as e:
        logger.exception("Error analyzing CV for topic: %s", e)
        return "Software Development"
