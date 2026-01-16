"""AlTi RAG Service - FastAPI Application."""

# SSL trust for corporate environments (Windows prod with SSL inspection)
# Only load on Windows or when USE_TRUSTSTORE=1 is set
import os
import platform
if platform.system() == "Windows" or os.getenv("USE_TRUSTSTORE", "0") == "1":
    try:
        import truststore
        truststore.inject_into_ssl()
    except ImportError:
        pass  # truststore not installed, skip

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from api import router, feedback_router
from config import settings, get_log_dir, get_chroma_dir, validate_environment, configure_langsmith
from utils.logging import setup_structured_logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Set up structured metrics logging
logs_dir = get_log_dir()
logs_dir.mkdir(parents=True, exist_ok=True)
setup_structured_logging(log_file=str(logs_dir / "metrics.jsonl"))


async def warmup_service():
    """Pre-initialize expensive components to avoid cold start latency."""
    import time
    start = time.time()
    logger.info("Warming up service components...")

    try:
        # 1. Initialize ChromaDB and retrieval engine
        logger.info("  [1/3] Initializing ChromaDB retrieval engine...")
        from api.routes import get_retrieval_engine
        engine = get_retrieval_engine("app_education")
        logger.info(f"        Retrieval engine ready")

        # 2. Compile LangGraph workflow
        logger.info("  [2/3] Compiling LangGraph workflow...")
        from graph.workflow import compile_app
        prism_app = compile_app()
        logger.info(f"        LangGraph workflow compiled")

        # 3. Run a minimal warmup query to initialize OpenAI connection
        logger.info("  [3/3] Warming up OpenAI connection...")
        from graph.workflow import invoke_prism_sync
        result = invoke_prism_sync(
            query="warmup",
            domain="app_education",
            thread_id="warmup_thread"
        )
        logger.info(f"        OpenAI connection ready")

        elapsed = time.time() - start
        logger.info(f"Warmup complete in {elapsed:.1f}s - service ready for queries!")

    except Exception as e:
        logger.warning(f"Warmup failed (service will still start): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"Chroma persist dir: {get_chroma_dir()}")
    logger.info(f"Log dir: {get_log_dir()}")
    logger.info(f"Legacy data dir: {settings.legacy_data_dir}")

    # Configure LangSmith tracing (if API key is set)
    langsmith_enabled = configure_langsmith()
    logger.info(f"LangSmith tracing: {'enabled' if langsmith_enabled else 'disabled'}")

    # Warmup to avoid cold start latency on first real query
    await warmup_service()

    yield
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="""
    RAG-powered investment research service for AlTi wealth management.

    ## Features
    - **Query**: Natural language Q&A over investment documents
    - **Search**: Semantic search across portfolios, CMA, holdings
    - **Ingest**: Process CSV, Excel, PDF, and JSON documents

    ## Document Types
    - Portfolio holdings and allocations
    - Capital Market Assumptions (CMA)
    - Historical returns and risk data
    - Qualtrics survey responses
    - Research PDFs and reports
    """,
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
# Note: v1 endpoints at /api/v1/*, v2 endpoints also included here at /api/v1/v2/*
# TODO: Consider separate router mounting for cleaner /api/v2/* paths
app.include_router(router, prefix="/api/v1", tags=["RAG"])

# Include feedback routes at /api/v1/feedback/*
app.include_router(feedback_router, prefix="/api/v1", tags=["Feedback"])

# Mount static files for playground
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/playground")
async def playground():
    """Redirect to RAG playground UI."""
    return RedirectResponse(url="/static/playground.html")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "playground": "/playground",
    }


def run_server():
    """Run the server with validation and error handling."""
    import uvicorn

    # Validate environment before starting
    logger.info("=" * 60)
    logger.info(f"AlTi RAG Service - Starting...")
    logger.info(f"Environment: {settings.environment}")
    logger.info("=" * 60)

    errors = validate_environment()
    if errors:
        logger.error("Environment validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.error("Please fix the above issues and restart.")
        sys.exit(1)

    logger.info("Environment validation passed")
    logger.info(f"Starting server on {settings.host}:{settings.port}")

    try:
        uvicorn.run(
            "main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug if settings.environment == "development" else False,
        )
    except OSError as e:
        if "Address already in use" in str(e) or "10048" in str(e):  # 10048 is Windows error
            logger.error(f"Port {settings.port} is already in use.")
            logger.error("Either stop the other process or set a different PORT in .env")
            sys.exit(1)
        raise


if __name__ == "__main__":
    run_server()
