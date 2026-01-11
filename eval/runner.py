"""Query runner for RAG evaluation."""

import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import httpx
import yaml

from .models import Endpoint, QueryResult, SourceResult, TestQuery
from .scoring import score_result, ScoredResult


def load_queries(yaml_path: Path) -> List[TestQuery]:
    """Load test queries from YAML file."""
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    queries = []
    for item in data.get("queries", []):
        queries.append(TestQuery(
            id=item["id"],
            query=item["query"],
            domain=item.get("domain", "app_education"),
            expected_topics=item.get("expected_topics", []),
            tags=item.get("tags", []),
            notes=item.get("notes", ""),
        ))
    return queries


class EvalRunner:
    """
    Runs evaluation queries against RAG service endpoints.

    Usage:
        runner = EvalRunner(base_url="http://localhost:8000")
        results = runner.run_queries(queries, endpoint=Endpoint.V1)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def check_health(self) -> bool:
        """Check if RAG service is healthy."""
        try:
            response = self.client.get(f"{self.base_url}/api/v1/health")
            return response.status_code == 200
        except Exception:
            return False

    def run_single_query(
        self,
        test_query: TestQuery,
        endpoint: Endpoint = Endpoint.V1,
    ) -> QueryResult:
        """
        Run a single query against the specified endpoint.

        Returns QueryResult with timing and retrieval metrics.
        """
        # Build request payload
        if endpoint == Endpoint.V1:
            url = f"{self.base_url}/api/v1/query/custom"
            payload = {
                "query": test_query.query,
                "domain": test_query.domain,
                "prompt_name": "standard_qa",
                "top_k": 5,
                "min_similarity": 0.3,
            }
        else:  # V2
            url = f"{self.base_url}/api/v1/v2/query"
            payload = {
                "query": test_query.query,
                "domain": test_query.domain,
            }

        # Execute with timing
        start = time.perf_counter()
        response = self.client.post(url, json=payload)
        latency_ms = (time.perf_counter() - start) * 1000

        response.raise_for_status()
        data = response.json()

        # Parse sources - handle both v1 and v2 response formats
        # v1 uses: relevance_score, chunk_text
        # v2 uses: relevance (no chunk_text)
        sources = []
        raw_sources = data.get("sources", [])
        for src in raw_sources:
            # Handle both v1 (relevance_score) and v2 (relevance) formats
            score = src.get("relevance_score") or src.get("relevance") or 0.0
            sources.append(SourceResult(
                file_name=src.get("file_name", "Unknown"),
                document_type=src.get("document_type", "Unknown"),
                relevance_score=float(score),
                chunk_text=src.get("chunk_text", "")[:200] if src.get("chunk_text") else "",
                priority=src.get("priority"),
            ))

        # Calculate retrieval metrics
        scores = [s.relevance_score for s in sources]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        top_score = max(scores) if scores else 0.0

        result = QueryResult(
            query_id=test_query.id,
            query_text=test_query.query,
            endpoint=endpoint,
            answer=data.get("answer", ""),
            sources=sources,
            latency_ms=latency_ms,
            avg_retrieval_score=avg_score,
            top_retrieval_score=top_score,
            timestamp=datetime.now(),
        )

        # Add v2-specific fields
        if endpoint == Endpoint.V2:
            result.intent = data.get("intent")
            result.retrieval_quality = data.get("retrieval_quality")

        return result

    def run_queries(
        self,
        queries: List[TestQuery],
        endpoint: Endpoint = Endpoint.V1,
        tags: Optional[List[str]] = None,
        verbose: bool = False,
    ) -> List[ScoredResult]:
        """
        Run multiple queries and return scored results.

        Args:
            queries: List of test queries to run
            endpoint: Which endpoint to use (v1 or v2)
            tags: Optional filter to only run queries with these tags
            verbose: Print progress to stdout

        Returns:
            List of ScoredResult objects with metrics
        """
        # Filter by tags if specified
        if tags:
            queries = [q for q in queries if any(t in q.tags for t in tags)]

        results = []
        total = len(queries)

        for i, query in enumerate(queries, 1):
            if verbose:
                print(f"[{i}/{total}] {query.id}...", end=" ", flush=True)

            try:
                result = self.run_single_query(query, endpoint)
                scored = score_result(result, query.expected_topics)
                results.append(scored)

                if verbose:
                    grade_emoji = {"good": "🟢", "fair": "🟡", "poor": "🔴"}
                    emoji = grade_emoji.get(scored.retrieval_grade, "⚪")
                    print(f"{emoji} {scored.query_result.avg_retrieval_score:.1%}")

            except Exception as e:
                if verbose:
                    print(f"❌ Error: {e}")
                # Continue with other queries

        return results

    def compare_endpoints(
        self,
        queries: List[TestQuery],
        verbose: bool = False,
    ) -> dict:
        """
        Run same queries against both v1 and v2, return comparison.

        Returns dict with both result sets and comparison metrics.
        """
        if verbose:
            print("Running v1 queries...")
        v1_results = self.run_queries(queries, Endpoint.V1, verbose=verbose)

        if verbose:
            print("\nRunning v2 queries...")
        v2_results = self.run_queries(queries, Endpoint.V2, verbose=verbose)

        # Build comparison
        from .scoring import calculate_metrics

        v1_metrics = calculate_metrics(v1_results)
        v2_metrics = calculate_metrics(v2_results)

        return {
            "v1": {
                "results": v1_results,
                "metrics": v1_metrics,
            },
            "v2": {
                "results": v2_results,
                "metrics": v2_metrics,
            },
            "comparison": {
                "retrieval_diff": v2_metrics["avg_retrieval_score"] - v1_metrics["avg_retrieval_score"],
                "latency_diff_ms": v2_metrics["avg_latency_ms"] - v1_metrics["avg_latency_ms"],
                "topic_coverage_diff": v2_metrics["avg_topic_coverage"] - v1_metrics["avg_topic_coverage"],
            },
        }
