"""
All RAG parameters loaded from environment (.env).
Documented in .env.example; override any value via .env or docker-compose environment.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Hugging Face
    huggingfacehub_api_token: str = ""

    # Qdrant
    qdrant_host: str = "vectordb"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "real_estate_rag"

    # Paths (inside container)
    docs_dir: str = "/app/docs"
    docs_metadata_xlsx: str = "/app/Real_Estate_RAG_Documents.xlsx"

    # Embeddings
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    embedding_batch_size: int = 16
    embedding_timeout_sec: int = 30
    embedding_retries: int = 1

    # Retrieval — Similarity Top-k
    retrieval_top_k: int = 5
    retrieval_similarity_threshold: float = 0.25

    # Retrieval — MMR
    retrieval_mmr_fetch_k: int = 20
    retrieval_mmr_k: int = 6
    retrieval_mmr_lambda: float = 0.7

    # LLM
    llm_model: str = "Qwen/Qwen2.5-1.5B-Instruct"
    llm_max_new_tokens: int = 350
    llm_temperature: float = 0.2
    llm_top_p: float = 0.9
    llm_timeout_sec: int = 60
    llm_retries: int = 1

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 64

    # Cleaning
    clean_max_consecutive_newlines: int = 2

    # Optional
    log_level: str = "INFO"

    def docs_path(self) -> Path:
        return Path(self.docs_dir)

    def metadata_xlsx_path(self) -> Path:
        return Path(self.docs_metadata_xlsx)


settings = Settings()
