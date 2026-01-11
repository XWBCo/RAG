"""Feedback API endpoints for collecting user feedback on RAG responses."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from models.feedback import FeedbackResponse, FeedbackStats, FeedbackSubmission
from storage.feedback import FeedbackStorage

logger = logging.getLogger(__name__)

# Create router for feedback endpoints
router = APIRouter(prefix="/feedback", tags=["Feedback"])

# Initialize storage (singleton pattern)
_storage: Optional[FeedbackStorage] = None


def get_storage() -> FeedbackStorage:
    """Get or create feedback storage instance."""
    global _storage
    if _storage is None:
        _storage = FeedbackStorage()
    return _storage


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(submission: FeedbackSubmission) -> FeedbackResponse:
    """
    Submit user feedback on a RAG response.

    This endpoint allows users to provide thumbs up/down feedback
    along with optional comments on RAG-generated answers.

    The feedback is stored in logs/feedback.jsonl and linked to
    the original query via query_id for correlation analysis.
    """
    try:
        storage = get_storage()
        record = storage.save(submission)

        logger.info(
            f"Feedback submitted: {record.feedback_id} | "
            f"query={submission.query_id} | "
            f"rating={submission.rating.value} | "
            f"user={submission.user_email or 'anonymous'}"
        )

        return FeedbackResponse(
            success=True,
            feedback_id=record.feedback_id,
            message=f"Thank you for your feedback!"
        )

    except Exception as e:
        logger.error(f"Failed to save feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save feedback: {str(e)}"
        )


@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats() -> FeedbackStats:
    """
    Get aggregated feedback statistics.

    Returns overall counts, positive rate, and breakdowns by:
    - Page context (which dashboard page)
    - User (for dev testing analysis)
    - Recent comments

    Useful for monitoring RAG quality during developer testing.
    """
    try:
        storage = get_storage()
        stats = storage.get_stats()

        logger.info(
            f"Feedback stats requested: "
            f"total={stats.total} | "
            f"positive_rate={stats.positive_rate}%"
        )

        return stats

    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve stats: {str(e)}"
        )


@router.get("/by-query/{query_id}")
async def get_feedback_by_query(query_id: str):
    """
    Get all feedback for a specific query.

    Useful for correlating user feedback with query metrics
    stored in metrics.jsonl.
    """
    try:
        storage = get_storage()
        records = storage.get_by_query_id(query_id)

        return {
            "query_id": query_id,
            "feedback_count": len(records),
            "feedback": [
                {
                    "feedback_id": r.feedback_id,
                    "rating": r.rating.value,
                    "comment": r.comment,
                    "page_context": r.page_context,
                    "user_email": r.user_email,
                    "timestamp": r.timestamp.isoformat() if hasattr(r.timestamp, 'isoformat') else r.timestamp
                }
                for r in records
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get feedback for query {query_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve feedback: {str(e)}"
        )


@router.get("/by-user")
async def get_feedback_by_user(
    email: str = Query(..., description="User email address")
):
    """
    Get all feedback from a specific user.

    Useful for analyzing feedback patterns during dev testing
    from authorized testers (Xavier, Alex, Joao).
    """
    try:
        storage = get_storage()
        records = storage.get_by_user(email)

        positive = sum(1 for r in records if r.rating.value == "positive")
        negative = len(records) - positive

        return {
            "user_email": email,
            "total_feedback": len(records),
            "positive": positive,
            "negative": negative,
            "feedback": [
                {
                    "feedback_id": r.feedback_id,
                    "query_id": r.query_id,
                    "rating": r.rating.value,
                    "comment": r.comment,
                    "page_context": r.page_context,
                    "timestamp": r.timestamp.isoformat() if hasattr(r.timestamp, 'isoformat') else r.timestamp
                }
                for r in sorted(records, key=lambda x: x.timestamp, reverse=True)
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get feedback for user {email}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve feedback: {str(e)}"
        )
