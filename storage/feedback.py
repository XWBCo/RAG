"""JSON file-based storage for user feedback."""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from models.feedback import FeedbackRecord, FeedbackRating, FeedbackStats, FeedbackSubmission

logger = logging.getLogger(__name__)


class FeedbackStorage:
    """
    JSON Lines file storage for feedback data.

    Stores feedback in logs/feedback.jsonl alongside metrics.jsonl
    for easy correlation and analysis.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize feedback storage.

        Args:
            storage_path: Path to feedback.jsonl file.
                         Defaults to logs/feedback.jsonl relative to project root.
        """
        if storage_path is None:
            # Default to logs directory
            self.storage_path = Path(__file__).parent.parent / "logs" / "feedback.jsonl"
        else:
            self.storage_path = Path(storage_path)

        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Create file if it doesn't exist
        if not self.storage_path.exists():
            self.storage_path.touch()
            logger.info(f"Created feedback storage file: {self.storage_path}")

    def save(self, submission: FeedbackSubmission) -> FeedbackRecord:
        """
        Save a feedback submission.

        Args:
            submission: User feedback submission

        Returns:
            FeedbackRecord with generated ID and timestamp
        """
        # Generate unique feedback ID
        feedback_id = f"fb_{uuid.uuid4().hex[:12]}"

        # Create record with metadata
        record = FeedbackRecord(
            feedback_id=feedback_id,
            query_id=submission.query_id,
            rating=submission.rating,
            comment=submission.comment,
            page_context=submission.page_context,
            user_email=submission.user_email,
            timestamp=datetime.now()
        )

        # Append to JSON Lines file
        record_dict = record.model_dump()
        record_dict["timestamp"] = record.timestamp.isoformat()

        with open(self.storage_path, "a") as f:
            f.write(json.dumps(record_dict) + "\n")

        logger.info(f"Saved feedback {feedback_id} for query {submission.query_id}")
        return record

    def get_by_query_id(self, query_id: str) -> List[FeedbackRecord]:
        """Get all feedback for a specific query."""
        return [r for r in self._read_all() if r.query_id == query_id]

    def get_by_user(self, user_email: str) -> List[FeedbackRecord]:
        """Get all feedback from a specific user."""
        return [
            r for r in self._read_all()
            if r.user_email and r.user_email.lower() == user_email.lower()
        ]

    def get_stats(self) -> FeedbackStats:
        """Calculate aggregated feedback statistics."""
        records = self._read_all()

        if not records:
            return FeedbackStats()

        total = len(records)
        positive = sum(1 for r in records if r.rating == FeedbackRating.POSITIVE)
        negative = total - positive

        # Group by context
        by_context = {}
        for r in records:
            ctx = r.page_context or "unknown"
            if ctx not in by_context:
                by_context[ctx] = {"positive": 0, "negative": 0}
            if r.rating == FeedbackRating.POSITIVE:
                by_context[ctx]["positive"] += 1
            else:
                by_context[ctx]["negative"] += 1

        # Group by user
        by_user = {}
        for r in records:
            user = r.user_email or "anonymous"
            if user not in by_user:
                by_user[user] = {"positive": 0, "negative": 0}
            if r.rating == FeedbackRating.POSITIVE:
                by_user[user]["positive"] += 1
            else:
                by_user[user]["negative"] += 1

        # Recent comments (last 10 with comments)
        recent_comments = [
            {
                "feedback_id": r.feedback_id,
                "rating": r.rating.value,
                "comment": r.comment,
                "page_context": r.page_context,
                "timestamp": r.timestamp.isoformat() if isinstance(r.timestamp, datetime) else r.timestamp
            }
            for r in sorted(records, key=lambda x: x.timestamp, reverse=True)
            if r.comment
        ][:10]

        return FeedbackStats(
            total=total,
            positive=positive,
            negative=negative,
            positive_rate=round(positive / total * 100, 1) if total > 0 else 0.0,
            by_context=by_context,
            by_user=by_user,
            recent_comments=recent_comments
        )

    def _read_all(self) -> List[FeedbackRecord]:
        """Read all feedback records from storage."""
        records = []

        if not self.storage_path.exists():
            return records

        with open(self.storage_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    # Parse timestamp back to datetime
                    if "timestamp" in data and isinstance(data["timestamp"], str):
                        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                    records.append(FeedbackRecord(**data))
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(f"Failed to parse feedback record: {e}")
                    continue

        return records

    def count(self) -> int:
        """Return total number of feedback records."""
        return len(self._read_all())
