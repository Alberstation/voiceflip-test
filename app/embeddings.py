"""
Embeddings via Hugging Face Inference API (remote).
Model and batch/timeout/retry from config (.env).
"""
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.config import settings


def get_embeddings() -> HuggingFaceEndpointEmbeddings:
    """Embeddings via Hugging Face Inference API. Model and dim from config (.env)."""
    kwargs = {"model": settings.embedding_model, "task": "feature-extraction"}
    if settings.huggingfacehub_api_token:
        kwargs["huggingfacehub_api_token"] = settings.huggingfacehub_api_token
    return HuggingFaceEndpointEmbeddings(**kwargs)
