"""Data models for evaluation harness."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Endpoint(str, Enum):
    """Available RAG endpoints."""
    V1 = "v1"
    V2 = "v2"


@dataclass
class TestQuery:
    """A single test query with expected behavior."""
    id: str
    query: str
    domain: str = "app_education"
    expected_topics: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class SourceResult:
    """A source document from retrieval."""
    file_name: str
    document_type: str
    relevance_score: float
    chunk_text: str
    priority: Optional[str] = None


@dataclass
class QueryResult:
    """Result from running a single query."""
    query_id: str
    query_text: str
    endpoint: Endpoint
    answer: str
    sources: list[SourceResult]
    latency_ms: float
    avg_retrieval_score: float
    top_retrieval_score: float
    timestamp: datetime = field(default_factory=datetime.now)

    # v2-specific fields
    intent: Optional[str] = None
    retrieval_quality: Optional[str] = None


@dataclass
class TopicMatch:
    """Result of matching expected topics in answer."""
    topic: str
    found: bool


@dataclass
class ScoredResult:
    """Query result with computed scores."""
    query_result: QueryResult
    topic_matches: list[TopicMatch]
    topic_coverage: float  # 0-1, what % of expected topics found
    retrieval_grade: str  # good/fair/poor based on avg score


@dataclass
class EvalSummary:
    """Summary of evaluation run."""
    endpoint: Endpoint
    total_queries: int
    duration_seconds: float
    timestamp: datetime

    # Score distribution
    good_count: int  # 60%+
    fair_count: int  # 40-60%
    poor_count: int  # <40%

    # Averages
    avg_retrieval_score: float
    avg_topic_coverage: float
    avg_latency_ms: float

    # Worst performers
    worst_queries: list[tuple[str, float]]  # (query_id, score)
