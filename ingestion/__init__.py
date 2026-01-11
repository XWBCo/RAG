"""Document ingestion module for AlTi RAG Service."""

from .pipeline import IngestionPipeline
from .loaders import (
    load_portfolio_csv,
    load_cma_excel,
    load_pdf_documents,
    load_qualtrics_json,
)

__all__ = [
    "IngestionPipeline",
    "load_portfolio_csv",
    "load_cma_excel",
    "load_pdf_documents",
    "load_qualtrics_json",
]
