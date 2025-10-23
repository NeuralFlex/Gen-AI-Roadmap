import os
import logging
from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from models.embedding_model import embeddings

logger = logging.getLogger(__name__)


def create_vectorstore(documents: List[Document], user_id: str = "default_user"):
    """
    Create a FAISS vectorstore from documents and save it locally.

    Args:
        documents (List[Document]): List of LangChain Document objects.
        user_id (str): Identifier for the user (used for index folder).

    Returns:
        FAISS: The created vectorstore instance, or None if failed.
    """
    index_dir = os.path.join(os.getcwd(), f"faiss_index_{user_id}")
    try:
        os.makedirs(index_dir, exist_ok=True)  # Ensure directory exists
        if not documents:
            logger.warning("No documents provided to create vectorstore.")
            return None

        vectorstore = FAISS.from_documents(documents, embeddings)
        vectorstore.save_local(index_dir)
        logger.info("FAISS vectorstore created and saved at: %s", index_dir)
        return vectorstore

    except Exception as e:
        logger.error("Failed to create FAISS vectorstore: %s", e, exc_info=True)
        return None
