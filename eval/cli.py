#!/usr/bin/env python3
"""
RAG Evaluation Harness CLI

Usage:
    python -m eval.cli run --endpoint v1
    python -m eval.cli run --endpoint v2 --tags monte_carlo
    python -m eval.cli compare
    python -m eval.cli list-tags
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from .models import Endpoint
from .runner import EvalRunner, load_queries
from .scoring import calculate_metrics


# Paths
EVAL_DIR = Path(__file__).parent
QUERIES_FILE = EVAL_DIR / "queries.yaml"
REPORTS_DIR = EVAL_DIR / "reports"


def ensure_reports_dir():
    """Create reports directory if it doesn't exist."""
    REPORTS_DIR.mkdir(exist_ok=True)


def format_duration(seconds: float) -> str:
    """Format duration as human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.1f}s"


def print_summary(metrics: dict, endpoint: str, duration: float):
    """Print evaluation summary to console."""
    click.echo()
    click.secho("=" * 60, fg="cyan")
    click.secho(f"Evaluation Results", fg="cyan", bold=True)
    click.secho("=" * 60, fg="cyan")
    click.echo()

    click.echo(f"Endpoint: {endpoint.upper()}")
    click.echo(f"Queries:  {metrics['total']}")
    click.echo(f"Duration: {format_duration(duration)}")
    click.echo()

    # Score distribution
    click.secho("Score Distribution:", bold=True)
    good_bar = "█" * int(metrics["good_pct"] / 5) if metrics["total"] else ""
    fair_bar = "█" * int(metrics["fair_pct"] / 5) if metrics["total"] else ""
    poor_bar = "█" * int(metrics["poor_pct"] / 5) if metrics["total"] else ""

    click.echo(f"  🟢 60%+ (good):  {metrics['good_count']:3d} ({metrics['good_pct']:5.1f}%) {good_bar}")
    click.echo(f"  🟡 40-60% (fair): {metrics['fair_count']:3d} ({metrics['fair_pct']:5.1f}%) {fair_bar}")
    click.echo(f"  🔴 <40% (poor):  {metrics['poor_count']:3d} ({metrics['poor_pct']:5.1f}%) {poor_bar}")
    click.echo()

    # Averages
    click.secho("Averages:", bold=True)
    click.echo(f"  Retrieval Score:  {metrics['avg_retrieval_score']:.1%} (top source: {metrics.get('avg_top_retrieval_score', 0):.1%})")
    click.echo(f"  Topic Coverage:   {metrics['avg_topic_coverage']:.1%}")
    click.echo(f"  Latency:          {metrics['avg_latency_ms']:.0f}ms")
    click.echo()

    # Worst performers
    if metrics["worst_queries"]:
        click.secho("Worst Performing:", bold=True)
        for i, (query_id, score) in enumerate(metrics["worst_queries"], 1):
            click.echo(f"  {i}. {query_id}: {score:.1%}")
    click.echo()


def print_comparison(comparison: dict):
    """Print v1 vs v2 comparison results."""
    v1 = comparison["v1"]["metrics"]
    v2 = comparison["v2"]["metrics"]
    diff = comparison["comparison"]

    click.echo()
    click.secho("=" * 60, fg="cyan")
    click.secho("v1 vs v2 Comparison", fg="cyan", bold=True)
    click.secho("=" * 60, fg="cyan")
    click.echo()

    # Side by side comparison
    click.secho(f"{'Metric':<25} {'v1':>12} {'v2':>12} {'Diff':>12}", bold=True)
    click.secho("-" * 60, fg="cyan")

    # Retrieval score
    retrieval_diff = diff["retrieval_diff"]
    diff_color = "green" if retrieval_diff > 0 else "red" if retrieval_diff < 0 else "white"
    diff_str = f"+{retrieval_diff:.1%}" if retrieval_diff > 0 else f"{retrieval_diff:.1%}"
    click.echo(f"{'Avg Retrieval Score':<25} {v1['avg_retrieval_score']:>11.1%} {v2['avg_retrieval_score']:>11.1%} ", nl=False)
    click.secho(f"{diff_str:>12}", fg=diff_color)

    # Topic coverage
    topic_diff = diff["topic_coverage_diff"]
    diff_color = "green" if topic_diff > 0 else "red" if topic_diff < 0 else "white"
    diff_str = f"+{topic_diff:.1%}" if topic_diff > 0 else f"{topic_diff:.1%}"
    click.echo(f"{'Avg Topic Coverage':<25} {v1['avg_topic_coverage']:>11.1%} {v2['avg_topic_coverage']:>11.1%} ", nl=False)
    click.secho(f"{diff_str:>12}", fg=diff_color)

    # Latency (lower is better)
    latency_diff = diff["latency_diff_ms"]
    diff_color = "red" if latency_diff > 0 else "green" if latency_diff < 0 else "white"
    diff_str = f"+{latency_diff:.0f}ms" if latency_diff > 0 else f"{latency_diff:.0f}ms"
    click.echo(f"{'Avg Latency':<25} {v1['avg_latency_ms']:>10.0f}ms {v2['avg_latency_ms']:>10.0f}ms ", nl=False)
    click.secho(f"{diff_str:>12}", fg=diff_color)

    click.echo()

    # Grade distribution
    click.secho("Grade Distribution:", bold=True)
    click.echo(f"  v1: 🟢 {v1['good_count']} / 🟡 {v1['fair_count']} / 🔴 {v1['poor_count']}")
    click.echo(f"  v2: 🟢 {v2['good_count']} / 🟡 {v2['fair_count']} / 🔴 {v2['poor_count']}")
    click.echo()

    # Winner
    if retrieval_diff > 0.02:
        click.secho("Winner: v2 (LangGraph)", fg="green", bold=True)
    elif retrieval_diff < -0.02:
        click.secho("Winner: v1 (Basic)", fg="green", bold=True)
    else:
        click.secho("Result: No significant difference", fg="yellow", bold=True)
    click.echo()


def save_report(results: list, metrics: dict, endpoint: str, tags: Optional[list] = None) -> Path:
    """Save evaluation results to JSON file."""
    ensure_reports_dir()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"{timestamp}_{endpoint}"
    if tags:
        filename += f"_{'_'.join(tags)}"
    filename += ".json"

    report_path = REPORTS_DIR / filename

    # Build report data
    report = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "tags_filter": tags,
            "total_queries": metrics["total"],
        },
        "summary": metrics,
        "results": [
            {
                "query_id": r.query_result.query_id,
                "query": r.query_result.query_text,
                "retrieval_score": r.query_result.avg_retrieval_score,
                "retrieval_grade": r.retrieval_grade,
                "topic_coverage": r.topic_coverage,
                "topic_matches": [
                    {"topic": m.topic, "found": m.found}
                    for m in r.topic_matches
                ],
                "latency_ms": r.query_result.latency_ms,
                "answer_preview": r.query_result.answer[:500] + "..." if len(r.query_result.answer) > 500 else r.query_result.answer,
                "sources": [
                    {
                        "file": s.file_name,
                        "type": s.document_type,
                        "score": s.relevance_score,
                    }
                    for s in r.query_result.sources
                ],
            }
            for r in results
        ],
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report_path


@click.group()
def cli():
    """RAG Evaluation Harness - Test and compare RAG endpoints."""
    pass


@cli.command()
@click.option(
    "--endpoint", "-e",
    type=click.Choice(["v1", "v2"]),
    default="v1",
    help="Endpoint to test (v1=basic, v2=LangGraph)"
)
@click.option(
    "--tags", "-t",
    multiple=True,
    help="Filter queries by tag (can specify multiple)"
)
@click.option(
    "--base-url", "-u",
    default="http://localhost:8000",
    help="RAG service base URL"
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Suppress per-query output"
)
@click.option(
    "--no-save",
    is_flag=True,
    help="Don't save results to file"
)
def run(endpoint: str, tags: tuple, base_url: str, quiet: bool, no_save: bool):
    """Run evaluation queries against an endpoint."""
    # Load queries
    if not QUERIES_FILE.exists():
        click.secho(f"Error: Queries file not found: {QUERIES_FILE}", fg="red")
        sys.exit(1)

    queries = load_queries(QUERIES_FILE)
    click.echo(f"Loaded {len(queries)} queries from {QUERIES_FILE.name}")

    # Filter by tags
    tags_list = list(tags) if tags else None
    if tags_list:
        original_count = len(queries)
        queries = [q for q in queries if any(t in q.tags for t in tags_list)]
        click.echo(f"Filtered to {len(queries)} queries (tags: {', '.join(tags_list)})")

    if not queries:
        click.secho("No queries match the specified tags", fg="yellow")
        sys.exit(0)

    # Check service health
    endpoint_enum = Endpoint.V1 if endpoint == "v1" else Endpoint.V2

    with EvalRunner(base_url=base_url) as runner:
        if not runner.check_health():
            click.secho(f"Error: RAG service not reachable at {base_url}", fg="red")
            click.echo("Start the service with: python main.py")
            sys.exit(1)

        click.echo(f"Service healthy at {base_url}")
        click.echo()

        # Run evaluation
        import time
        start = time.perf_counter()
        results = runner.run_queries(queries, endpoint_enum, verbose=not quiet)
        duration = time.perf_counter() - start

    # Calculate metrics
    metrics = calculate_metrics(results)

    # Print summary
    print_summary(metrics, endpoint, duration)

    # Save report
    if not no_save:
        report_path = save_report(results, metrics, endpoint, tags_list)
        click.echo(f"Full report: {report_path}")


@cli.command()
@click.option(
    "--base-url", "-u",
    default="http://localhost:8000",
    help="RAG service base URL"
)
@click.option(
    "--tags", "-t",
    multiple=True,
    help="Filter queries by tag"
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Suppress per-query output"
)
def compare(base_url: str, tags: tuple, quiet: bool):
    """Compare v1 and v2 endpoints side by side."""
    # Load queries
    if not QUERIES_FILE.exists():
        click.secho(f"Error: Queries file not found: {QUERIES_FILE}", fg="red")
        sys.exit(1)

    queries = load_queries(QUERIES_FILE)

    # Filter by tags
    tags_list = list(tags) if tags else None
    if tags_list:
        queries = [q for q in queries if any(t in q.tags for t in tags_list)]

    if not queries:
        click.secho("No queries match the specified tags", fg="yellow")
        sys.exit(0)

    click.echo(f"Comparing {len(queries)} queries...")
    click.echo()

    with EvalRunner(base_url=base_url) as runner:
        if not runner.check_health():
            click.secho(f"Error: RAG service not reachable at {base_url}", fg="red")
            sys.exit(1)

        comparison = runner.compare_endpoints(queries, verbose=not quiet)

    print_comparison(comparison)

    # Save comparison report
    ensure_reports_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_path = REPORTS_DIR / f"{timestamp}_comparison.json"

    report = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_queries": len(queries),
            "tags_filter": tags_list,
        },
        "v1_summary": comparison["v1"]["metrics"],
        "v2_summary": comparison["v2"]["metrics"],
        "comparison": comparison["comparison"],
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    click.echo(f"Comparison report: {report_path}")


@cli.command("list-tags")
def list_tags():
    """List all available tags in the query suite."""
    if not QUERIES_FILE.exists():
        click.secho(f"Error: Queries file not found: {QUERIES_FILE}", fg="red")
        sys.exit(1)

    queries = load_queries(QUERIES_FILE)

    # Collect all tags with counts
    tag_counts = {}
    for q in queries:
        for tag in q.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    click.secho("Available Tags:", bold=True)
    click.echo()
    for tag, count in sorted(tag_counts.items()):
        click.echo(f"  {tag:<20} ({count} queries)")


@cli.command("list-queries")
@click.option("--tags", "-t", multiple=True, help="Filter by tags")
def list_queries(tags: tuple):
    """List all queries in the test suite."""
    if not QUERIES_FILE.exists():
        click.secho(f"Error: Queries file not found: {QUERIES_FILE}", fg="red")
        sys.exit(1)

    queries = load_queries(QUERIES_FILE)

    if tags:
        queries = [q for q in queries if any(t in q.tags for t in tags)]

    click.secho(f"Test Queries ({len(queries)}):", bold=True)
    click.echo()
    for q in queries:
        click.echo(f"  {q.id}")
        click.echo(f"    {q.query[:60]}...")
        click.echo(f"    Tags: {', '.join(q.tags)}")
        click.echo()


@cli.command()
def health():
    """Check RAG service health."""
    with EvalRunner() as runner:
        if runner.check_health():
            click.secho("✓ RAG service is healthy", fg="green")
        else:
            click.secho("✗ RAG service not reachable", fg="red")
            sys.exit(1)


if __name__ == "__main__":
    cli()
