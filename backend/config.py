"""Configuration management for the VASP Wiki RAG Agent."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Gemini API Configuration
    gemini_api_key: Optional[str] = None
    embedding_model: str = "embedding-001"
    llm_model: str = "gemini-2.5-flash"
    use_gemini_embeddings: bool = False  # Default to False (free sentence-transformers). Set True to use Gemini embeddings.
    
    # Vector Store Configuration
    faiss_index_path: str = "embeddings/faiss_index"
    
    # Wiki Configuration
    wiki_base_url: str = "https://vasp.at/wiki"
    wiki_api_url: str = "https://vasp.at/wiki/api.php"
    
    # RAG Configuration
    top_k: int = 5
    chunk_size: int = 512
    chunk_overlap: int = 50
    min_chunk_size: int = 100
    
    # Server Configuration
    backend_host: str = "localhost"
    backend_port: int = 8000
    
    # Data paths
    data_raw_path: str = "data/raw"
    data_processed_path: str = "data/processed"
    data_chunks_path: str = "data/chunks"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure data directories exist
Path(settings.data_raw_path).mkdir(parents=True, exist_ok=True)
Path(settings.data_processed_path).mkdir(parents=True, exist_ok=True)
Path(settings.data_chunks_path).mkdir(parents=True, exist_ok=True)
Path(settings.faiss_index_path).mkdir(parents=True, exist_ok=True)
