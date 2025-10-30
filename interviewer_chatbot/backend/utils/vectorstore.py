import os
from typing import List
from langchain_core.documents import Document

# New correct import
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Initialize embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


def create_vectorstore(documents: List[Document], user_id: str = "default_user"):
    """Create FAISS vectorstore from documents."""
    index_dir = os.path.join(os.getcwd(), f"faiss_index_{user_id}")
    os.makedirs(index_dir, exist_ok=True)  # Ensure directory exists

    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(index_dir)

    return vectorstore
