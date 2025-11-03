import os
from typing import List
from langchain_core.documents import Document

from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


def create_vectorstore(documents: List[Document], user_id: str = "default_user"):
    """Create ChromaDB vectorstore from documents."""
    persist_directory = os.path.join(os.getcwd(), f"chroma_db_{user_id}")
    os.makedirs(persist_directory, exist_ok=True)
    vectorstore = Chroma.from_documents(
        documents=documents, embedding=embeddings, persist_directory=persist_directory
    )

    return vectorstore


def load_vectorstore(user_id: str = "default_user"):
    """Load existing ChromaDB vectorstore."""
    persist_directory = os.path.join(os.getcwd(), f"chroma_db_{user_id}")

    if not os.path.exists(persist_directory):
        return None

    vectorstore = Chroma(
        persist_directory=persist_directory, embedding_function=embeddings
    )
    return vectorstore
