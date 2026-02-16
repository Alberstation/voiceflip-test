"""
LLM via Hugging Face Inference API (remote).
Model and generation params from config (.env).
"""
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from app.config import settings


def get_llm() -> ChatHuggingFace:
    endpoint = HuggingFaceEndpoint(
        repo_id=settings.llm_model,
        task="text-generation",
        huggingfacehub_api_token=settings.huggingfacehub_api_token or None,
        model_kwargs={
            "max_new_tokens": settings.llm_max_new_tokens,
            "temperature": settings.llm_temperature,
            "top_p": settings.llm_top_p,
        },
    )
    return ChatHuggingFace(llm=endpoint)
