"""API module for AlTi RAG Service."""

from .routes import router
from .feedback import router as feedback_router

__all__ = ["router", "feedback_router"]
