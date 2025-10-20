# For PDF reading
import fitz  # PyMuPDF

# For LangChain documents
from langchain_core.documents import Document

# For text splitting
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_core.documents import Document


def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text


def chunk_cv_text(cv_text: str, user_id: str = "default_user") -> list:
    """Splits CV text into chunks for embedding and retrieval."""
    chunk_size = 800
    chunk_overlap = 200
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    cv_text = cv_text.strip().replace("\n", " ")
    documents = []

    for i, chunk in enumerate(splitter.split_text(cv_text)):
        chunk_text = chunk.strip()
        if len(chunk_text) < 20:
            continue
        documents.append(
            Document(
                page_content=chunk_text, metadata={"user_id": user_id, "chunk_index": i}
            )
        )
    return documents
