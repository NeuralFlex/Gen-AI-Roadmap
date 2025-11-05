import chromadb
from chromadb.api.models.Collection import Collection
from langchain_core.documents import Document
from models.embedding_model import embeddings
import logging
import os

logger = logging.getLogger(__name__)
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
CHROMA_TENANT = os.getenv("CHROMA_TENANT")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE")

client = chromadb.CloudClient(
    api_key=CHROMA_API_KEY,
    tenant=CHROMA_TENANT,
    database=CHROMA_DATABASE,
)


def create_vectorstore(
    documents: list[Document], user_id: str = "default_user"
) -> Collection | None:
    """
    Create or update a Chroma Cloud collection for a user.

    Args:
        documents (list[Document]): List of LangChain Documents.
        user_id (str): Identifier for the user (used for collection name).

    Returns:
        Chroma Collection object or None.
    """
    try:
        if not documents:
            logger.warning("No documents provided to create vectorstore.")
            return None

        collection_name = f"interviewer-chatbot-{user_id}"
        collection = client.get_or_create_collection(collection_name)

        doc_texts = [doc.page_content for doc in documents]
        doc_embeddings = [embeddings.embed_query(text) for text in doc_texts]
        doc_ids = [f"{user_id}_{i}" for i in range(len(documents))]

        collection.add(documents=doc_texts, embeddings=doc_embeddings, ids=doc_ids)

        logger.info("Chroma Cloud collection created/updated: %s", collection_name)
        return collection

    except Exception as e:
        logger.error("Failed to create vectorstore: %s", e, exc_info=True)
        return None


def load_vectorstore(user_id: str = "default_user") -> Collection | None:
    """
    Load a Chroma Cloud collection for a user.

    Args:
        user_id (str): Identifier for the user.

    Returns:
        Chroma Collection object or None.
    """
    try:
        collection_name = f"interviewer-chatbot-{user_id}"
        collection = client.get_or_create_collection(collection_name)
        logger.info("Loaded Chroma Cloud collection: %s", collection_name)
        return collection
    except Exception as e:
        logger.error("Failed to load vectorstore: %s", e, exc_info=True)
        return None


def delete_vectorstore(user_id: str = "default_user") -> bool:
    """
    Delete a user's Chroma Cloud collection.

    Args:
        user_id (str): Identifier for the user.

    Returns:
        bool: True if deleted successfully, False otherwise.
    """
    try:
        collection_name = f"interviewer-chatbot-{user_id}"
        client.delete_collection(collection_name)
        logger.info("Deleted Chroma Cloud collection: %s", collection_name)
        return True
    except Exception as e:
        logger.error("Failed to delete vectorstore: %s", e, exc_info=True)
        return False
