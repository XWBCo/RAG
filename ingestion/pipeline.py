"""Document ingestion pipeline for AlTi RAG Service."""

import logging
from pathlib import Path
from typing import List, Optional

import chromadb
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore

from .loaders import (
    load_cma_excel,
    load_fund_holdings_csv,
    load_markdown_documents,
    load_model_archetypes,
    load_pdf_documents,
    load_portfolio_csv,
    load_powerpoint,
    load_qualtrics_json,
    load_returns_csv,
)

logger = logging.getLogger(__name__)


def get_embed_model(provider: str, **kwargs):
    """Get embedding model based on provider."""
    if provider == "ollama":
        from llama_index.embeddings.ollama import OllamaEmbedding
        return OllamaEmbedding(
            model_name=kwargs.get("model", "nomic-embed-text"),
            base_url=kwargs.get("base_url", "http://localhost:11434"),
        )
    else:  # openai
        from llama_index.embeddings.openai import OpenAIEmbedding
        return OpenAIEmbedding(model=kwargs.get("model", "text-embedding-3-small"))


class IngestionPipeline:
    """Pipeline for ingesting financial documents into vector store."""

    def __init__(
        self,
        chroma_persist_dir: str = "./chroma_db",
        collection_name: str = "alti_investments",
        provider: str = "ollama",
        embedding_model: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
        chunk_size: int = 512,
        chunk_overlap: int = 128,
    ):
        self.chroma_persist_dir = Path(chroma_persist_dir)
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize embedding model based on provider
        Settings.embed_model = get_embed_model(
            provider, model=embedding_model, base_url=base_url
        )

        # Initialize text splitter
        self.text_splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        # Initialize Chroma
        self._init_chroma()

    def _init_chroma(self):
        """Initialize Chroma vector store."""
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)

        self.chroma_client = chromadb.PersistentClient(
            path=str(self.chroma_persist_dir)
        )

        self.chroma_collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "AlTi investment documents"}
        )

        self.vector_store = ChromaVectorStore(
            chroma_collection=self.chroma_collection
        )

        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )

    def load_documents_from_path(
        self, path: Path, priority: str = "normal"
    ) -> List[Document]:
        """Load documents based on file type.

        Args:
            path: Path to the document file
            priority: Document priority level (critical, high, normal, low)
        """
        documents = []
        suffix = path.suffix.lower()
        name_lower = path.stem.lower()

        try:
            if suffix == ".csv":
                # Determine CSV type based on filename
                if "return" in name_lower:
                    documents = load_returns_csv(path)
                elif any(x in name_lower for x in ["sma", "intl", "lp", "holdings"]):
                    documents = load_fund_holdings_csv(path)
                elif "portfolio" in name_lower or "universe" in name_lower:
                    documents = load_portfolio_csv(path)
                else:
                    documents = load_portfolio_csv(path)  # Default to portfolio

            elif suffix in [".xlsx", ".xls", ".xlsm"]:
                # Special handling for Model Archetypes
                if "model" in name_lower and "archetype" in name_lower:
                    documents = load_model_archetypes(path)
                    logger.info(f"Loaded PRIORITY document: Model Archetypes")
                else:
                    documents = load_cma_excel(path)

            elif suffix == ".pptx":
                # PowerPoint files (investment profiles)
                documents = load_powerpoint(path, priority=priority)

            elif suffix == ".pdf":
                documents = load_pdf_documents(path)

            elif suffix == ".json":
                documents = load_qualtrics_json(path)

            elif suffix == ".md":
                documents = load_markdown_documents(path)

            else:
                logger.warning(f"Unsupported file type: {suffix} for {path}")

        except Exception as e:
            logger.error(f"Error loading {path}: {e}")

        return documents

    def ingest_directory(
        self,
        directory: Path,
        recursive: bool = True,
        extensions: Optional[List[str]] = None,
    ) -> dict:
        """
        Ingest all supported documents from a directory.

        Args:
            directory: Path to directory containing documents
            recursive: Whether to search subdirectories
            extensions: File extensions to include (default: all supported)

        Returns:
            Summary of ingestion results
        """
        if extensions is None:
            extensions = [".csv", ".xlsx", ".xls", ".xlsm", ".pdf", ".json", ".pptx", ".md"]

        directory = Path(directory)
        if not directory.exists():
            raise ValueError(f"Directory not found: {directory}")

        all_documents = []
        files_processed = 0
        errors = []

        # Find all matching files
        pattern = "**/*" if recursive else "*"
        for ext in extensions:
            for file_path in directory.glob(f"{pattern}{ext}"):
                try:
                    docs = self.load_documents_from_path(file_path)
                    all_documents.extend(docs)
                    files_processed += 1
                    logger.info(f"Loaded {len(docs)} documents from {file_path.name}")
                except Exception as e:
                    errors.append({"file": str(file_path), "error": str(e)})
                    logger.error(f"Failed to process {file_path}: {e}")

        # Index documents
        if all_documents:
            index = VectorStoreIndex.from_documents(
                all_documents,
                storage_context=self.storage_context,
                transformations=[self.text_splitter],
                show_progress=True,
            )
            logger.info(f"Indexed {len(all_documents)} documents")

        return {
            "files_processed": files_processed,
            "documents_created": len(all_documents),
            "errors": errors,
            "collection_count": self.chroma_collection.count(),
        }

    def ingest_file(self, file_path: Path, priority: str = "normal") -> dict:
        """Ingest a single file with optional priority level."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        documents = self.load_documents_from_path(file_path, priority=priority)

        if documents:
            VectorStoreIndex.from_documents(
                documents,
                storage_context=self.storage_context,
                transformations=[self.text_splitter],
            )

        return {
            "file": str(file_path),
            "documents_created": len(documents),
            "collection_count": self.chroma_collection.count(),
            "priority": priority,
        }

    def ingest_priority_documents(self, file_paths: List[Path]) -> dict:
        """
        Ingest documents marked as priority/must-know.

        These documents get:
        - Critical priority metadata (priority_score: 1.0)
        - Enhanced retrieval boosting
        - Detailed document breakdowns for better semantic matching
        """
        all_documents = []
        results = []

        for file_path in file_paths:
            file_path = Path(file_path)

            if not file_path.exists():
                results.append({"file": str(file_path), "status": "not_found"})
                continue

            try:
                # Determine priority level based on filename
                name_lower = file_path.stem.lower()
                if "model" in name_lower and "archetype" in name_lower:
                    # Model Archetypes - absolute top priority
                    priority = "critical"
                else:
                    # Other priority documents
                    priority = "high"

                documents = self.load_documents_from_path(file_path, priority=priority)
                all_documents.extend(documents)

                results.append({
                    "file": str(file_path),
                    "status": "loaded",
                    "documents_created": len(documents),
                    "priority": priority,
                })

                logger.info(
                    f"Loaded {len(documents)} documents from {file_path.name} "
                    f"(priority: {priority})"
                )

            except Exception as e:
                results.append({
                    "file": str(file_path),
                    "status": "error",
                    "error": str(e),
                })
                logger.error(f"Failed to process priority document {file_path}: {e}")

        # Index all priority documents together
        if all_documents:
            VectorStoreIndex.from_documents(
                all_documents,
                storage_context=self.storage_context,
                transformations=[self.text_splitter],
                show_progress=True,
            )
            logger.info(f"Indexed {len(all_documents)} priority documents")

        return {
            "total_documents": len(all_documents),
            "files": results,
            "collection_count": self.chroma_collection.count(),
        }

    def clear_collection(self) -> dict:
        """Clear all documents from the collection."""
        # Delete and recreate collection
        self.chroma_client.delete_collection(self.collection_name)
        self._init_chroma()

        return {"status": "cleared", "collection_count": 0}

    def get_stats(self) -> dict:
        """Get collection statistics."""
        return {
            "collection_name": self.collection_name,
            "document_count": self.chroma_collection.count(),
            "persist_directory": str(self.chroma_persist_dir),
        }
