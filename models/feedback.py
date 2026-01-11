"""Feedback models for RAG service user feedback collection."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FeedbackRating(str, Enum):
    """User feedback rating options."""
    POSITIVE = "positive"
    NEGATIVE = "negative"


class FeedbackSubmission(BaseModel):
    """Model for submitting user feedback on RAG responses."""

    query_id: str = Field(
        ...,
        description="Unique identifier linking to the original query in metrics.jsonl"
    )
    rating: FeedbackRating = Field(
        ...,
        description="User's rating of the response (positive/negative)"
    )
    comment: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional user comment explaining their feedback"
    )
    page_context: Optional[str] = Field(
        None,
        description="Dashboard page where feedback was submitted (e.g., /mcs, /risk)"
    )
    user_email: Optional[str] = Field(
        None,
        description="Email of user submitting feedback (from SAML session)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "abc12345",
                "rating": "positive",
                "comment": "Very helpful explanation of Monte Carlo results",
                "page_context": "/mcs",
                "user_email": "xavier.court@alti-global.com"
            }
        }


class FeedbackRecord(BaseModel):
    """Internal model for stored feedback with metadata."""

    feedback_id: str = Field(..., description="Unique identifier for this feedback")
    query_id: str = Field(..., description="Links to original query")
    rating: FeedbackRating
    comment: Optional[str] = None
    page_context: Optional[str] = None
    user_email: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FeedbackResponse(BaseModel):
    """Response after feedback submission."""

    success: bool
    feedback_id: str
    message: str


class FeedbackStats(BaseModel):
    """Aggregated feedback statistics."""

    total: int = Field(0, description="Total feedback submissions")
    positive: int = Field(0, description="Positive ratings count")
    negative: int = Field(0, description="Negative ratings count")
    positive_rate: float = Field(0.0, description="Percentage of positive feedback")
    by_context: dict = Field(
        default_factory=dict,
        description="Breakdown by page context"
    )
    by_user: dict = Field(
        default_factory=dict,
        description="Breakdown by user (for dev testing analysis)"
    )
    recent_comments: list = Field(
        default_factory=list,
        description="Most recent feedback comments"
    )
