"""Scoring logic for RAG evaluation."""

import re
from typing import List

from .models import QueryResult, ScoredResult, TopicMatch


def score_retrieval(avg_score: float) -> str:
    """
    Grade retrieval quality based on average score.

    Thresholds based on empirical testing:
    - 60%+: Good - reliable retrieval
    - 40-60%: Fair - may miss some context
    - <40%: Poor - likely irrelevant results
    """
    if avg_score >= 0.60:
        return "good"
    elif avg_score >= 0.40:
        return "fair"
    else:
        return "poor"


def check_topic_in_text(topic: str, text: str) -> bool:
    """
    Check if a topic/concept appears in text.

    Uses fuzzy matching to handle variations:
    - Case insensitive
    - Handles plurals (scenario/scenarios)
    - Handles common synonyms
    """
    text_lower = text.lower()
    topic_lower = topic.lower()

    # Direct match
    if topic_lower in text_lower:
        return True

    # Handle plurals
    if topic_lower.endswith('s'):
        singular = topic_lower[:-1]
        if singular in text_lower:
            return True
    else:
        plural = topic_lower + 's'
        if plural in text_lower:
            return True

    # Common synonyms and related terms
    synonyms = {
        "pessimistic": ["worst-case", "downside", "bad", "conservative"],
        "optimistic": ["best-case", "upside", "good"],
        "probability": ["likelihood", "chance", "odds"],
        "scenario": ["outcome", "case", "situation"],
        "worst-case": ["pessimistic", "5th percentile", "downside"],
        "planning": ["preparation", "strategy"],
        "volatility": ["risk", "variance", "fluctuation"],
        "correlation": ["relationship", "co-movement"],
        "diversification": ["spread", "variety", "allocation"],
    }

    # Check synonyms
    for key, syn_list in synonyms.items():
        if topic_lower == key or topic_lower in syn_list:
            # Check if topic or any synonym is in text
            if key in text_lower:
                return True
            for syn in syn_list:
                if syn in text_lower:
                    return True

    return False


def match_topics(expected_topics: List[str], answer: str) -> List[TopicMatch]:
    """Check which expected topics appear in the answer."""
    matches = []
    for topic in expected_topics:
        found = check_topic_in_text(topic, answer)
        matches.append(TopicMatch(topic=topic, found=found))
    return matches


def calculate_topic_coverage(matches: List[TopicMatch]) -> float:
    """Calculate what percentage of expected topics were found."""
    if not matches:
        return 1.0  # No expectations = full coverage

    found_count = sum(1 for m in matches if m.found)
    return found_count / len(matches)


def score_result(result: QueryResult, expected_topics: List[str]) -> ScoredResult:
    """
    Score a query result against expected topics.

    Returns a ScoredResult with:
    - Topic matches (which topics were/weren't found)
    - Topic coverage (0-1)
    - Retrieval grade (good/fair/poor)
    """
    topic_matches = match_topics(expected_topics, result.answer)
    topic_coverage = calculate_topic_coverage(topic_matches)
    retrieval_grade = score_retrieval(result.avg_retrieval_score)

    return ScoredResult(
        query_result=result,
        topic_matches=topic_matches,
        topic_coverage=topic_coverage,
        retrieval_grade=retrieval_grade,
    )


def calculate_metrics(scored_results: List[ScoredResult]) -> dict:
    """
    Calculate aggregate metrics from scored results.

    Returns dict with:
    - Distribution (good/fair/poor counts)
    - Averages (retrieval score, topic coverage, latency)
    - Top scores (best single source per query)
    - Worst performers
    """
    if not scored_results:
        return {
            "total": 0,
            "good_count": 0,
            "fair_count": 0,
            "poor_count": 0,
            "avg_retrieval_score": 0.0,
            "avg_top_retrieval_score": 0.0,
            "avg_topic_coverage": 0.0,
            "avg_latency_ms": 0.0,
            "worst_queries": [],
        }

    good = sum(1 for r in scored_results if r.retrieval_grade == "good")
    fair = sum(1 for r in scored_results if r.retrieval_grade == "fair")
    poor = sum(1 for r in scored_results if r.retrieval_grade == "poor")

    avg_retrieval = sum(r.query_result.avg_retrieval_score for r in scored_results) / len(scored_results)
    avg_top_retrieval = sum(r.query_result.top_retrieval_score for r in scored_results) / len(scored_results)
    avg_topic = sum(r.topic_coverage for r in scored_results) / len(scored_results)
    avg_latency = sum(r.query_result.latency_ms for r in scored_results) / len(scored_results)

    # Find worst performers by retrieval score
    sorted_by_score = sorted(scored_results, key=lambda r: r.query_result.avg_retrieval_score)
    worst = [(r.query_result.query_id, r.query_result.avg_retrieval_score) for r in sorted_by_score[:5]]

    return {
        "total": len(scored_results),
        "good_count": good,
        "fair_count": fair,
        "poor_count": poor,
        "good_pct": good / len(scored_results) * 100,
        "fair_pct": fair / len(scored_results) * 100,
        "poor_pct": poor / len(scored_results) * 100,
        "avg_retrieval_score": avg_retrieval,
        "avg_top_retrieval_score": avg_top_retrieval,
        "avg_topic_coverage": avg_topic,
        "avg_latency_ms": avg_latency,
        "worst_queries": worst,
    }
