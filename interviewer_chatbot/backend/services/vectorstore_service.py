from chromadb.api.models.Collection import Collection
import chromadb
from models.embedding_model import embeddings
import logging
from typing import Optional
from langchain_core.documents import Document
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
) -> Optional[Collection]:
    if not documents:
        logger.warning("No documents provided")
        return None

    collection_name = f"interviewer-chatbot-{user_id}"
    collection = client.get_or_create_collection(collection_name)

    doc_texts = [doc.page_content for doc in documents]
    doc_embeddings = [embeddings.embed_query(text) for text in doc_texts]
    doc_ids = [f"{user_id}_{i}" for i in range(len(documents))]

    collection.add(ids=doc_ids, documents=doc_texts, embeddings=doc_embeddings)
    return collection


def load_vectorstore(user_id: str = "default_user") -> Optional[Collection]:
    collection_name = f"interviewer-chatbot-{user_id}"
    return client.get_or_create_collection(collection_name)
