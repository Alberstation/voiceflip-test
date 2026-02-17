"""
Qdrant vector store. Collection and connection from config (.env).
"""
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from app.config import settings
from app.embeddings import get_embeddings


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def get_vector_store() -> QdrantVectorStore:
    ensure_collection()
    client = get_qdrant_client()
    embeddings = get_embeddings()
    return QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection_name,
        embedding=embeddings,
    )


def ensure_collection():
    """Create collection with correct vector size if it does not exist."""
    client = get_qdrant_client()
    collections = client.get_collections().collections
    names = [c.name for c in collections]
    if settings.qdrant_collection_name not in names:
        client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config=qdrant_models.VectorParams(
                size=settings.embedding_dim,
                distance=qdrant_models.Distance.COSINE,
            ),
        )


def chunks_to_langchain_docs(chunks: list[tuple[str, dict]]) -> list[Document]:
    """Convert (text, metadata) chunks to LangChain Document objects."""
    return [Document(page_content=text, metadata=meta) for text, meta in chunks]
