"""API routes for AlTi RAG Service."""

import logging
import time
import uuid
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config import settings
from ingestion import IngestionPipeline
from retrieval import RetrievalEngine
from retrieval.engine import QueryMode, QueryResult, Source
from utils.logging import QueryMetrics, get_metrics_logger

logger = logging.getLogger(__name__)
metrics_logger = get_metrics_logger()

router = APIRouter()


# =============================================================================
# Context Building Utilities
# =============================================================================

def format_currency(value: float, symbol: str = "$") -> str:
    """Format a number as currency with commas."""
    if value is None:
        return "N/A"
    return f"{symbol}{value:,.0f}"


def build_contextual_query(query: str, app_context: dict) -> str:
    """
    Build an enhanced query with the user's actual computed results.

    This transforms a generic question like "explain my results" into a
    specific prompt that includes the user's actual numbers for interpretation.
    """
    if not app_context:
        return query

    page = app_context.get("page", "unknown")

    if page == "monte_carlo":
        # Monte Carlo simulation results
        initial = app_context.get("initial_portfolio", 0)
        currency = app_context.get("currency", "USD")
        symbol = {"USD": "$", "GBP": "£", "EUR": "€"}.get(currency, "$")
        sims = app_context.get("simulations", {})

        results_text = f"""
USER'S CURRENT MONTE CARLO SIMULATION RESULTS:
===============================================
Initial Portfolio: {format_currency(initial, symbol)}
Number of Simulations: {app_context.get('num_simulations', 1000):,}
Inflation Rate: {app_context.get('inflation_rate_pct', 0):.1f}%
"""
        for sim_key, sim_data in sims.items():
            if sim_data:
                name = sim_data.get("name", sim_key)
                duration = sim_data.get("duration_years", 0)
                p5 = sim_data.get("percentile_5th", 0)
                p50 = sim_data.get("percentile_50th", 0)
                p95 = sim_data.get("percentile_95th", 0)
                prob_out = sim_data.get("prob_outperform_inflation", 0)
                prob_loss = sim_data.get("prob_loss_50pct", 0)
                ret = sim_data.get("annual_return_pct", 0)
                risk = sim_data.get("annual_risk_pct", 0)

                results_text += f"""
{name.upper()} ({duration:.0f} years, {ret}% return, {risk}% risk):
  - 5th Percentile (pessimistic): {format_currency(p5, symbol)}
  - 50th Percentile (median): {format_currency(p50, symbol)}
  - 95th Percentile (optimistic): {format_currency(p95, symbol)}
  - Probability of outperforming inflation: {prob_out:.1f}%
  - Probability of >50% loss: {prob_loss:.1f}%
"""
        results_text += f"\nUSER QUESTION: {query}"
        return results_text

    elif page == "risk_analytics":
        # Risk analytics results
        results_text = f"""
USER'S CURRENT RISK ANALYTICS RESULTS:
======================================
Portfolio: {app_context.get('portfolio_name', 'N/A')}
Benchmark: {app_context.get('benchmark_name', 'N/A')}

KEY METRICS:
- Portfolio Volatility: {app_context.get('portfolio_volatility_pct', 0):.2f}%
- Benchmark Volatility: {app_context.get('benchmark_volatility_pct', 0):.2f}%
- Tracking Error: {app_context.get('tracking_error_pct', 0):.2f}%
- Factor Explained: {app_context.get('factor_explained_pct', 0):.1f}%
- Idiosyncratic Risk: {app_context.get('idiosyncratic_pct', 0):.1f}%

PERFORMANCE:
- Portfolio CAGR: {app_context.get('portfolio_cagr_pct', 0):.2f}%
- Benchmark CAGR: {app_context.get('benchmark_cagr_pct', 0):.2f}%
- Portfolio Sharpe Ratio: {app_context.get('portfolio_sharpe', 0):.2f}
- Benchmark Sharpe Ratio: {app_context.get('benchmark_sharpe', 0):.2f}
- Portfolio Max Drawdown: {app_context.get('portfolio_max_dd_pct', 0):.2f}%

BETA ANALYSIS:
- Total Beta: {app_context.get('total_beta', 0):.3f}
- Growth Beta: {app_context.get('growth_beta', 0):.3f}
- Defensive Beta: {app_context.get('defensive_beta', 0):.3f}

DIVERSIFICATION:
- Average Correlation: {app_context.get('avg_correlation', 0):.2f}
- Effective N (diversification): {app_context.get('effective_n', 0):.1f}
- Top 5 Concentration: {app_context.get('concentration_ratio', 0):.1f}%
"""
        # Add top risk contributors
        contributors = app_context.get('top_risk_contributors', [])
        if contributors:
            results_text += "\nTOP RISK CONTRIBUTORS:\n"
            for i, contrib in enumerate(contributors[:5], 1):
                results_text += f"  {i}. {contrib.get('security', 'N/A')}: {contrib.get('contribution_pct', 0):.2f}%\n"

        results_text += f"\nUSER QUESTION: {query}"
        return results_text

    elif page == "portfolio_evaluation":
        # Portfolio optimization/evaluation results
        frontier_summaries = app_context.get("frontier_summaries", {})
        optimal_alloc = app_context.get("optimal_allocation", {})
        benchmark = app_context.get("benchmark", {})
        caps_template = app_context.get("caps_template", "standard")

        results_text = f"""
USER'S CURRENT PORTFOLIO OPTIMIZATION RESULTS:
===============================================
Constraints Template: {caps_template.upper()}
"""
        # Add frontier summaries
        for key, summary in frontier_summaries.items():
            if summary:
                name = summary.get("name", key)
                results_text += f"""
{name.upper()} FRONTIER:
  - Risk Range: {summary.get('min_risk_pct', 0):.2f}% to {summary.get('max_risk_pct', 0):.2f}%
  - Return Range: {summary.get('min_return_pct', 0):.2f}% to {summary.get('max_return_pct', 0):.2f}%
  - Optimal Sharpe Ratio: {summary.get('optimal_sharpe', 0):.3f}
  - Optimal Point: {summary.get('optimal_return_pct', 0):.2f}% return at {summary.get('optimal_risk_pct', 0):.2f}% risk
"""

        # Add optimal allocation
        if optimal_alloc:
            results_text += "\nOPTIMAL ALLOCATION (Core + Private Frontier):\n"
            sorted_allocs = sorted(optimal_alloc.items(), key=lambda x: x[1], reverse=True)
            for asset, weight in sorted_allocs:
                if weight > 0.1:  # Only show allocations > 0.1%
                    results_text += f"  - {asset}: {weight:.1f}%\n"

        # Add benchmark comparison if available
        if benchmark and 'return' in benchmark and 'risk' in benchmark:
            results_text += f"""
BENCHMARK COMPARISON:
  - Benchmark Return: {benchmark.get('return', 0)*100:.2f}%
  - Benchmark Risk: {benchmark.get('risk', 0)*100:.2f}%
"""

        results_text += f"\nUSER QUESTION: {query}"
        return results_text

    # Unknown page type - return original query
    return query


# Request/Response Models
class QueryRequest(BaseModel):
    """Query request body."""

    query: str = Field(..., min_length=1, description="Natural language query")
    domain: str = Field(default="investments", description="Domain: investments, estate_planning, etc.")
    mode: QueryMode = Field(default=QueryMode.COMPACT, description="Response synthesis mode")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    min_similarity: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum similarity threshold")


class SearchRequest(BaseModel):
    """Search request body."""

    query: str = Field(..., min_length=1, description="Search query")
    domain: str = Field(default="investments", description="Domain: investments, estate_planning, etc.")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results")


class IngestRequest(BaseModel):
    """Ingestion request body."""

    directory: str = Field(..., description="Directory path to ingest")
    domain: str = Field(default="investments", description="Domain: investments, estate_planning, etc.")
    recursive: bool = Field(default=True, description="Search subdirectories")
    extensions: Optional[List[str]] = Field(
        default=None,
        description="File extensions to include"
    )


class IngestFileRequest(BaseModel):
    """Single file ingestion request."""

    file_path: str = Field(..., description="Path to file")
    domain: str = Field(default="investments", description="Domain: investments, estate_planning, etc.")


class CustomQueryRequest(BaseModel):
    """Custom query with prompt selection."""

    query: str = Field(..., min_length=1, description="Natural language query")
    domain: str = Field(default="investments", description="Domain: investments, estate_planning, etc.")
    prompt_name: str = Field(default="standard_qa", description="Name of prompt template")
    custom_prompt: Optional[str] = Field(default=None, description="Custom prompt (overrides prompt_name)")
    mode: QueryMode = Field(default=QueryMode.COMPACT, description="Response synthesis mode")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    min_similarity: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum similarity threshold")
    app_context: Optional[dict] = Field(
        default=None,
        description="Application context with user's computed results for contextual interpretation"
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    collection_count: int
    document_types: List[str]


class IngestResponse(BaseModel):
    """Ingestion response."""

    files_processed: int
    documents_created: int
    collection_count: int
    errors: List[dict]


# =============================================================================
# Domain Resolution & Engine Management
# =============================================================================

def get_collection_for_domain(domain: str) -> str:
    """
    Get the collection name for a given domain.

    Args:
        domain: Domain identifier (e.g., 'investments', 'estate_planning')

    Returns:
        Collection name from settings.domain_collections

    Raises:
        HTTPException: If domain is not configured
    """
    collection = settings.domain_collections.get(domain)
    if not collection:
        available = list(settings.domain_collections.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unknown domain: '{domain}'. Available domains: {available}"
        )
    return collection


# Domain-keyed engine caches (one engine per domain)
_retrieval_engines: dict[str, RetrievalEngine] = {}
_ingestion_pipelines: dict[str, IngestionPipeline] = {}


def get_retrieval_engine(domain: str = "investments") -> RetrievalEngine:
    """
    Get or create retrieval engine for a domain.

    Each domain gets its own engine pointing to its collection.
    """
    global _retrieval_engines

    collection_name = get_collection_for_domain(domain)

    if domain not in _retrieval_engines:
        # Determine model names based on provider
        if settings.llm_provider == "ollama":
            embed_model = settings.ollama_embedding_model
            llm_model = settings.ollama_llm_model
            base_url = settings.ollama_base_url
        else:
            embed_model = settings.openai_embedding_model
            llm_model = settings.openai_llm_model
            base_url = ""

        _retrieval_engines[domain] = RetrievalEngine(
            chroma_persist_dir=settings.chroma_persist_dir,
            collection_name=collection_name,
            provider=settings.llm_provider,
            embedding_model=embed_model,
            llm_model=llm_model,
            base_url=base_url,
            similarity_top_k=settings.similarity_top_k,
        )
        logger.info(f"Created retrieval engine for domain '{domain}' → collection '{collection_name}'")

    return _retrieval_engines[domain]


def get_ingestion_pipeline(domain: str = "investments") -> IngestionPipeline:
    """
    Get or create ingestion pipeline for a domain.

    Each domain gets its own pipeline pointing to its collection.
    """
    global _ingestion_pipelines

    collection_name = get_collection_for_domain(domain)

    if domain not in _ingestion_pipelines:
        # Determine model name based on provider
        if settings.llm_provider == "ollama":
            embed_model = settings.ollama_embedding_model
            base_url = settings.ollama_base_url
        else:
            embed_model = settings.openai_embedding_model
            base_url = ""

        _ingestion_pipelines[domain] = IngestionPipeline(
            chroma_persist_dir=settings.chroma_persist_dir,
            collection_name=collection_name,
            provider=settings.llm_provider,
            embedding_model=embed_model,
            base_url=base_url,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        logger.info(f"Created ingestion pipeline for domain '{domain}' → collection '{collection_name}'")

    return _ingestion_pipelines[domain]


# Routes
@router.get("/domains")
async def list_domains():
    """List all available domains and their collections."""
    return {
        "domains": list(settings.domain_collections.keys()),
        "default": settings.default_domain,
        "collections": settings.domain_collections,
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health and get basic stats for default domain."""
    try:
        engine = get_retrieval_engine(domain=settings.default_domain)
        stats = engine.get_stats()
        return HealthResponse(
            status="healthy",
            collection_count=stats["document_count"],
            document_types=stats["document_types"],
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            collection_count=0,
            document_types=[],
        )


@router.post("/query", response_model=QueryResult)
async def query_documents(request: QueryRequest):
    """
    Query the knowledge base for a specific domain.

    Uses RAG to retrieve relevant documents and synthesize an answer.
    Domain determines which collection to search.
    """
    try:
        engine = get_retrieval_engine(domain=request.domain)
        result = engine.query(
            query_text=request.query,
            mode=request.mode,
            top_k=request.top_k,
            min_similarity=request.min_similarity,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=List[Source])
async def search_documents(request: SearchRequest):
    """
    Semantic search without LLM synthesis.

    Returns raw document chunks matching the query.
    Domain determines which collection to search.
    """
    try:
        engine = get_retrieval_engine(domain=request.domain)
        sources = engine.search(
            query_text=request.query,
            top_k=request.top_k,
        )
        return sources
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/custom", response_model=QueryResult)
async def custom_query(request: CustomQueryRequest):
    """
    Query with a custom or pre-defined prompt template.

    Available prompts: standard_qa, investment_advisor, model_comparison,
    beginner_friendly, citation_qa, allocation_breakdown, esg_analysis, risk_assessment,
    results_interpreter_contextual (for interpreting user's actual results)

    Domain determines which collection to search.
    When app_context is provided, the query is enhanced with the user's actual
    computed results for specific interpretation rather than generic education.
    """
    # Initialize metrics
    metrics = QueryMetrics(
        query_id=str(uuid.uuid4())[:8],
        query_text=request.query[:200],
        domain=request.domain,
        endpoint="v1",
        min_similarity=request.min_similarity,
    )
    start_time = time.perf_counter()

    try:
        engine = get_retrieval_engine(domain=request.domain)

        # If app_context is provided, enhance the query with user's results
        query_text = request.query
        if request.app_context:
            query_text = build_contextual_query(request.query, request.app_context)

        result = engine.query_with_prompt(
            query_text=query_text,
            prompt_name=request.prompt_name,
            custom_prompt=request.custom_prompt,
            mode=request.mode,
            top_k=request.top_k,
            min_similarity=request.min_similarity,
        )

        # Collect metrics
        metrics.total_time_ms = (time.perf_counter() - start_time) * 1000
        metrics.documents_retrieved = len(result.sources)
        if result.sources:
            scores = [s.relevance_score for s in result.sources]
            metrics.top_score = max(scores)
            metrics.avg_score = sum(scores) / len(scores)
            metrics.top_sources = [
                {"file": s.file_name, "score": round(s.relevance_score, 3)}
                for s in result.sources[:3]
            ]
        metrics.answer_length = len(result.answer)
        metrics.log()

        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        metrics.total_time_ms = (time.perf_counter() - start_time) * 1000
        metrics.error = str(e)
        metrics.log(logging.ERROR)
        logger.error(f"Custom query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts")
async def list_available_prompts():
    """List all available prompt templates."""
    try:
        engine = get_retrieval_engine()
        return {"prompts": engine.get_available_prompts()}
    except Exception as e:
        logger.error(f"Failed to list prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/directory", response_model=IngestResponse)
async def ingest_directory(request: IngestRequest):
    """
    Ingest all documents from a directory into a domain's collection.

    Processes CSV, Excel, PDF, and JSON files.
    Domain determines which collection to ingest into.
    """
    try:
        pipeline = get_ingestion_pipeline(domain=request.domain)
        result = pipeline.ingest_directory(
            directory=Path(request.directory),
            recursive=request.recursive,
            extensions=request.extensions,
        )
        return IngestResponse(**result)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/file")
async def ingest_file(request: IngestFileRequest):
    """Ingest a single file into a domain's collection."""
    try:
        pipeline = get_ingestion_pipeline(domain=request.domain)
        result = pipeline.ingest_file(Path(request.file_path))
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"File ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/legacy")
async def ingest_legacy_data():
    """
    Ingest data from the legacy alti-risk-portfolio-app.

    Processes the /data directory from the Dash application.
    """
    try:
        pipeline = get_ingestion_pipeline()

        legacy_path = Path(settings.legacy_data_dir)
        if not legacy_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Legacy data directory not found: {legacy_path}"
            )

        result = pipeline.ingest_directory(
            directory=legacy_path,
            recursive=True,
            extensions=[".csv", ".xlsx", ".xls", ".pdf"],
        )
        return IngestResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Legacy ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collection")
async def clear_collection():
    """Clear all documents from the collection."""
    try:
        pipeline = get_ingestion_pipeline()
        result = pipeline.clear_collection()

        # Reset retrieval engine to pick up cleared collection
        global _retrieval_engine
        _retrieval_engine = None

        return result
    except Exception as e:
        logger.error(f"Clear collection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """Get detailed collection statistics."""
    try:
        engine = get_retrieval_engine()
        return engine.get_stats()
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LangGraph Agentic RAG Endpoints (v2)
# ============================================================================

class PrismQueryRequest(BaseModel):
    """Request for Prism agentic RAG query."""

    query: str = Field(..., min_length=1, description="Natural language query")
    domain: str = Field(default="investments", description="Domain: investments, estate_planning, etc.")
    thread_id: Optional[str] = Field(default=None, description="Conversation thread ID for memory")
    archetype: Optional[str] = Field(default=None, description="Pre-selected archetype from Qualtrics")
    region: Literal["US", "INT"] = Field(default="US", description="Region focus")
    # V1 context-aware features (for dashboard compatibility)
    prompt_name: Optional[str] = Field(default=None, description="Custom prompt template (e.g., monte_carlo_interpreter_cited)")
    app_context: Optional[dict] = Field(default=None, description="User's computed results for interpretation")


class PrismQueryResponse(BaseModel):
    """Response from Prism agentic RAG."""

    answer: str
    sources: List[dict]
    intent: str
    retrieval_quality: str
    turn_count: int
    thread_id: str
    query_id: str = Field(description="Unique ID for linking feedback to this query")


class PrismStreamEvent(BaseModel):
    """Streaming event from Prism workflow."""

    type: Literal["token", "complete", "error"]
    content: Optional[str] = None
    answer: Optional[str] = None
    sources: Optional[List[dict]] = None
    intent: Optional[str] = None


# LangGraph app singleton
_prism_app = None


def get_prism_app():
    """Get or create Prism LangGraph app singleton."""
    global _prism_app
    if _prism_app is None:
        try:
            from graph.workflow import get_app
            _prism_app = get_app()
            logger.info("Prism LangGraph app initialized")
        except ImportError as e:
            logger.warning(f"LangGraph not available: {e}. Using fallback.")
            _prism_app = None
        except Exception as e:
            logger.error(f"Failed to initialize Prism app: {e}")
            _prism_app = None
    return _prism_app


@router.post("/v2/query", response_model=PrismQueryResponse)
async def prism_query(request: PrismQueryRequest):
    """
    Query using the new LangGraph agentic RAG workflow.

    Features:
    - Intent routing (archetype, pipeline, clarity, general)
    - Hybrid retrieval (BM25 + semantic)
    - CRAG document grading
    - Self-RAG hallucination checking
    - Conversation memory (via thread_id)
    """
    try:
        prism_app = get_prism_app()

        if prism_app is None:
            # Fallback to legacy engine
            logger.info("Using legacy retrieval (LangGraph not available)")
            engine = get_retrieval_engine()
            result = engine.query(
                query_text=request.query,
                mode=QueryMode.COMPACT,
                top_k=5,
                min_similarity=0.3,
            )
            fallback_thread_id = request.thread_id or str(uuid.uuid4())
            return PrismQueryResponse(
                answer=result.answer,
                sources=[s.model_dump() for s in result.sources],
                intent="general",
                retrieval_quality="unknown",
                turn_count=1,
                thread_id=fallback_thread_id,
                query_id=fallback_thread_id[:8],
            )

        # Use LangGraph workflow
        from graph.workflow import invoke_prism_sync

        thread_id = request.thread_id or str(uuid.uuid4())

        # Enhance query with app_context if provided (v1 compatibility)
        query = request.query
        if request.app_context:
            query = build_contextual_query(request.query, request.app_context)
            # DEBUG: Log the enhanced query to trace MCS results
            logger.info(f"[RAG DEBUG] app_context page: {request.app_context.get('page', 'unknown')}")
            logger.info(f"[RAG DEBUG] Enhanced query preview (first 500 chars):\n{query[:500]}")

        start_time = time.time()
        result = invoke_prism_sync(
            query=query,
            thread_id=thread_id,
            archetype=request.archetype,
            region=request.region,
            domain=request.domain,
            prompt_name=request.prompt_name,
            app_context=request.app_context,
        )
        elapsed_ms = (time.time() - start_time) * 1000

        # Log v2 query metrics for feedback loop
        metrics = QueryMetrics(
            query_id=thread_id[:8],
            query_text=request.query[:200],
            domain=request.domain,
            endpoint="v2",
            total_time_ms=elapsed_ms,
            documents_retrieved=len(result.get("sources", [])),
            intent=result.get("intent"),
            retrieval_quality=result.get("retrieval_quality"),
            answer_length=len(result.get("answer", "")),
            top_sources=[
                {"file": s.get("file_name", "unknown")}
                for s in result.get("sources", [])[:3]
            ],
        )
        metrics.log()

        # Use thread_id prefix as query_id (matches metrics.jsonl for correlation)
        query_id = thread_id[:8]

        return PrismQueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            intent=result["intent"],
            retrieval_quality=result["retrieval_quality"],
            turn_count=result["turn_count"],
            thread_id=thread_id,
            query_id=query_id,
        )

    except Exception as e:
        logger.error(f"Prism query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/query/stream")
async def prism_query_stream(request: PrismQueryRequest):
    """
    Stream responses from Prism RAG workflow.

    Returns Server-Sent Events (SSE) with tokens as they're generated.
    """
    import json

    async def event_generator():
        try:
            prism_app = get_prism_app()

            if prism_app is None:
                # Fallback: return complete response as single event
                engine = get_retrieval_engine()
                result = engine.query(
                    query_text=request.query,
                    mode=QueryMode.COMPACT,
                    top_k=5,
                    min_similarity=0.3,
                )
                event = PrismStreamEvent(
                    type="complete",
                    answer=result.answer,
                    sources=[s.model_dump() for s in result.sources],
                    intent="general",
                )
                yield f"data: {json.dumps(event.model_dump())}\n\n"
                return

            # Stream from LangGraph
            from graph.workflow import stream_prism

            thread_id = request.thread_id or str(uuid.uuid4())

            async for event in stream_prism(
                query=request.query,
                thread_id=thread_id,
                archetype=request.archetype,
                region=request.region,
            ):
                yield f"data: {json.dumps(event)}\n\n"

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            error_event = PrismStreamEvent(type="error", content=str(e))
            yield f"data: {json.dumps(error_event.model_dump())}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/v2/health")
async def prism_health():
    """Check health of the LangGraph Prism workflow."""
    prism_app = get_prism_app()

    if prism_app is None:
        return {
            "status": "fallback",
            "message": "LangGraph not available, using legacy retrieval",
            "features": {
                "hybrid_retrieval": False,
                "crag_grading": False,
                "self_rag": False,
                "memory": False,
            },
        }

    return {
        "status": "healthy",
        "message": "Prism LangGraph workflow active",
        "features": {
            "hybrid_retrieval": True,
            "crag_grading": True,
            "self_rag": True,
            "memory": True,
        },
    }
