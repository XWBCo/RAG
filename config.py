"""Configuration for AlTi RAG Service."""

import os
import sys
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment: "development" or "production"
    environment: str = "development"

    # API Settings
    app_name: str = "AlTi RAG Service"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8080  # Changed from 8000 to match actual usage

    # LLM Provider: "ollama" or "openai"
    llm_provider: str = "ollama"

    # Ollama (local, free)
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_llm_model: str = "llama3.2:3b"

    # OpenAI (cloud, paid) - set OPENAI_API_KEY in .env to use
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_llm_model: str = "gpt-4o-mini"

    # Chroma Vector Store
    chroma_persist_dir: str = "./chroma_db"
    collection_name: str = "alti_investments"  # Default collection

    # Domain Configuration - maps domain names to collection names
    # Add new domains here as needed
    domain_collections: dict[str, str] = {
        "investments": "alti_investments",
        "estate_planning": "estate_documents",
        "app_education": "app_education_docs",
        # Future domains:
        # "client_portal": "client_documents",
    }

    # Default domain when none specified
    default_domain: str = "investments"

    # Document Processing
    # Larger chunks preserve more context; higher overlap prevents mid-thought cuts
    chunk_size: int = 768  # Increased from 512 for educational content
    chunk_overlap: int = 200  # Increased from 128 for better context continuity

    # Data Sources
    data_dir: str = "./data"
    legacy_data_dir: str = "../alti-risk-portfolio-app/data"

    # Retrieval Settings
    similarity_top_k: int = 5

    # CORS - Allow dashboard and dev servers
    allowed_origins: list[str] = [
        "http://localhost:3000",      # Next.js dev
        "http://127.0.0.1:3000",
        "http://localhost:8050",      # Dash dev (default port)
        "http://127.0.0.1:8050",
        "http://localhost:8051",      # Dash dev (alternate)
        "http://127.0.0.1:8051",
        "https://plotly.alti-global.com",  # Production dashboard
    ]

    # Windows Production Paths (used when ENVIRONMENT=production)
    windows_chroma_dir: str = r"D:\App\rag-service\chroma_db"
    windows_log_dir: str = r"D:\App\rag-service\logs"
    windows_data_dir: str = r"D:\App\rag-service\data"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance
settings = Settings()


def get_base_dir() -> Path:
    """Get base directory, handling frozen executables."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def get_chroma_dir() -> Path:
    """Get ChromaDB directory based on environment."""
    if settings.environment == "production":
        return Path(settings.windows_chroma_dir)
    return get_base_dir() / settings.chroma_persist_dir


def get_log_dir() -> Path:
    """Get log directory based on environment."""
    if settings.environment == "production":
        return Path(settings.windows_log_dir)
    return get_base_dir() / "logs"


def get_data_dir() -> Path:
    """Get data directory based on environment."""
    if settings.environment == "production":
        return Path(settings.windows_data_dir)
    return get_base_dir() / settings.data_dir


def validate_environment() -> list[str]:
    """
    Validate required environment variables and configuration.
    Returns list of error messages (empty if all valid).
    """
    errors = []

    # Check OpenAI API key if using OpenAI provider
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            errors.append(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai. "
                "Set it in .env or environment variables."
            )

    # Check ChromaDB directory is writable
    chroma_dir = get_chroma_dir()
    try:
        chroma_dir.mkdir(parents=True, exist_ok=True)
        test_file = chroma_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
    except (PermissionError, OSError) as e:
        errors.append(f"Cannot write to ChromaDB directory {chroma_dir}: {e}")

    # Check log directory is writable
    log_dir = get_log_dir()
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as e:
        errors.append(f"Cannot create log directory {log_dir}: {e}")

    return errors


# Paths (legacy compatibility)
BASE_DIR = get_base_dir()
CHROMA_DIR = get_chroma_dir()
DATA_DIR = get_data_dir()
