"""Structured logging utilities for RAG service debugging."""

import json
import logging
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional

# Configure structured logger
logger = logging.getLogger("rag.metrics")


@dataclass
class QueryMetrics:
    """Metrics collected during a RAG query."""

    query_id: str
    query_text: str
    domain: str
    endpoint: str  # v1 or v2
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Timing (ms)
    total_time_ms: float = 0.0
    retrieval_time_ms: float = 0.0
    llm_time_ms: float = 0.0

    # Retrieval metrics
    documents_retrieved: int = 0
    documents_after_filter: int = 0
    top_score: float = 0.0
    avg_score: float = 0.0
    min_similarity: float = 0.0

    # Sources
    top_sources: list = field(default_factory=list)

    # Response
    answer_length: int = 0
    intent: Optional[str] = None
    retrieval_quality: Optional[str] = None

    # Errors
    error: Optional[str] = None

    def to_json(self) -> str:
        """Serialize metrics to JSON."""
        return json.dumps(asdict(self), indent=2)

    def log(self, level: int = logging.INFO):
        """Log metrics in structured format."""
        data = asdict(self)
        logger.log(level, json.dumps(data))


class QueryTimer:
    """Context manager for timing query phases."""

    def __init__(self, metrics: QueryMetrics):
        self.metrics = metrics
        self._phase_start: Optional[float] = None
        self._total_start: Optional[float] = None

    def __enter__(self):
        self._total_start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._total_start:
            self.metrics.total_time_ms = (time.perf_counter() - self._total_start) * 1000
        if exc_val:
            self.metrics.error = str(exc_val)

    @contextmanager
    def phase(self, name: str):
        """Time a specific phase (retrieval, llm, etc.)."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            if name == "retrieval":
                self.metrics.retrieval_time_ms = elapsed_ms
            elif name == "llm":
                self.metrics.llm_time_ms = elapsed_ms


def log_query(func: Callable) -> Callable:
    """
    Decorator to log query metrics.

    Usage:
        @log_query
        def query(self, query_text: str, **kwargs) -> QueryResult:
            ...
    """
    @wraps(func)
    def wrapper(self, query_text: str, *args, **kwargs):
        metrics = QueryMetrics(
            query_id=str(hash(query_text + str(time.time())))[:8],
            query_text=query_text[:200],
            domain=kwargs.get("domain", "unknown"),
            endpoint="v1",
        )

        start = time.perf_counter()
        try:
            result = func(self, query_text, *args, **kwargs)

            # Extract metrics from result
            metrics.total_time_ms = (time.perf_counter() - start) * 1000

            if hasattr(result, "sources"):
                sources = result.sources
                metrics.documents_retrieved = len(sources)
                scores = [s.relevance_score for s in sources if hasattr(s, "relevance_score")]
                if scores:
                    metrics.top_score = max(scores)
                    metrics.avg_score = sum(scores) / len(scores)
                metrics.top_sources = [
                    {"file": s.file_name, "score": s.relevance_score}
                    for s in sources[:3]
                    if hasattr(s, "file_name")
                ]

            if hasattr(result, "answer"):
                metrics.answer_length = len(result.answer)

            metrics.log()
            return result

        except Exception as e:
            metrics.total_time_ms = (time.perf_counter() - start) * 1000
            metrics.error = str(e)
            metrics.log(logging.ERROR)
            raise

    return wrapper


def setup_structured_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    json_format: bool = True,
):
    """
    Configure structured logging for the RAG service.

    Args:
        log_file: Optional file path for metrics log
        level: Logging level
        json_format: Use JSON format for logs
    """
    metrics_logger = logging.getLogger("rag.metrics")
    metrics_logger.setLevel(level)

    # Create formatter
    if json_format:
        formatter = logging.Formatter("%(message)s")
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    metrics_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        metrics_logger.addHandler(file_handler)

    return metrics_logger


# Pre-configured structured logger
def get_metrics_logger():
    """Get the metrics logger instance."""
    return logging.getLogger("rag.metrics")
