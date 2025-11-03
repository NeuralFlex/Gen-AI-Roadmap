import os
import logging
from typing import List, Optional
from langchain_core.documents import Document
from langchain_chroma import Chroma
from models.embedding_model import embeddings

logger = logging.getLogger(__name__)


def create_vectorstore(
    documents: List[Document], user_id: str = "default_user"
) -> Optional[Chroma]:
    """
    Create a ChromaDB vectorstore from documents and save it locally.

    Args:
        documents (List[Document]): List of LangChain Document objects.
        user_id (str): Identifier for the user (used for database folder).

    Returns:
        Chroma: The created vectorstore instance, or None if failed.
    """
    persist_directory = os.path.join(os.getcwd(), f"chroma_db_{user_id}")
    try:
        os.makedirs(persist_directory, exist_ok=True)  # Ensure directory exists
        if not documents:
            logger.warning("No documents provided to create vectorstore.")
            return None

        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=persist_directory,
        )

        logger.info("ChromaDB vectorstore created and saved at: %s", persist_directory)
        return vectorstore

    except Exception as e:
        logger.error("Failed to create ChromaDB vectorstore: %s", e, exc_info=True)
        return None


def load_vectorstore(user_id: str = "default_user") -> Optional[Chroma]:
    """
    Load existing ChromaDB vectorstore.

    Args:
        user_id (str): Identifier for the user (used for database folder).

    Returns:
        Chroma: The loaded vectorstore instance, or None if not found.
    """
    persist_directory = os.path.join(os.getcwd(), f"chroma_db_{user_id}")
    try:
        if not os.path.exists(persist_directory):
            logger.warning("Vectorstore directory not found: %s", persist_directory)
            return None

        vectorstore = Chroma(
            persist_directory=persist_directory, embedding_function=embeddings
        )

        logger.info("ChromaDB vectorstore loaded from: %s", persist_directory)
        return vectorstore

    except Exception as e:
        logger.error("Failed to load ChromaDB vectorstore: %s", e, exc_info=True)
        return None


def delete_vectorstore(user_id: str = "default_user") -> bool:
    """
    Delete ChromaDB vectorstore for a user.

    Args:
        user_id (str): Identifier for the user.

    Returns:
        bool: True if successful, False otherwise.
    """
    persist_directory = os.path.join(os.getcwd(), f"chroma_db_{user_id}")
    try:
        import shutil

        if os.path.exists(persist_directory):
            shutil.rmtree(persist_directory)
            logger.info("ChromaDB vectorstore deleted: %s", persist_directory)
            return True
        else:
            logger.warning(
                "Vectorstore directory not found for deletion: %s", persist_directory
            )
            return False
    except Exception as e:
        logger.error("Failed to delete ChromaDB vectorstore: %s", e, exc_info=True)
        return False
