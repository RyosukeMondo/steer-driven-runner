"""Async feedback system for human-AI collaboration."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class FeedbackPriority(str, Enum):
    """Priority levels for feedback."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FeedbackType(str, Enum):
    """Types of feedback."""

    FEEDBACK = "FEEDBACK"
    BUG = "BUG"
    FEATURE = "FEATURE"
    IMPROVEMENT = "IMPROVEMENT"
    VISUAL = "VISUAL"


class FeedbackManager:
    """Manager for async feedback system."""

    def __init__(self, project_root: Path):
        """Initialize feedback manager.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.feedback_dir = project_root / ".spec-workflow" / "feedback"
        self.pending_file = self.feedback_dir / "pending.md"
        self.archive_dir = self.feedback_dir / "archive"

    def post_feedback(
        self,
        message: str,
        priority: FeedbackPriority = FeedbackPriority.MEDIUM,
        feedback_type: FeedbackType = FeedbackType.FEEDBACK,
    ) -> Path:
        """Post feedback for the AI agent to process.

        Args:
            message: Feedback message
            priority: Priority level
            feedback_type: Type of feedback

        Returns:
            Path to the pending feedback file
        """
        self.feedback_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check if pending.md already exists
        separator = ""
        if self.pending_file.exists():
            separator = "\n\n---\n\n"

        # Append feedback
        with open(self.pending_file, "a") as f:
            f.write(separator)
            f.write(f"## {message}\n")
            f.write(f"**Date:** {timestamp}\n")
            f.write(f"**Priority:** {priority.value}\n")
            f.write(f"**Type:** {feedback_type.value}\n")
            f.write("\n")
            f.write("**Description:**\n")
            f.write(f"{message}\n")
            f.write("\n")
            f.write("**Status:** PENDING (awaiting AI agent processing)\n")
            f.write("\n")
            f.write("**Posted by:** Human (async feedback)\n")

        return self.pending_file

    def has_pending_feedback(self) -> bool:
        """Check if there is pending feedback.

        Returns:
            True if pending feedback exists
        """
        return self.pending_file.exists()

    def read_pending_feedback(self) -> Optional[str]:
        """Read pending feedback content.

        Returns:
            Feedback content or None if no pending feedback
        """
        if not self.has_pending_feedback():
            return None

        with open(self.pending_file, "r") as f:
            return f.read()

    def archive_feedback(self) -> Optional[Path]:
        """Archive processed feedback.

        Returns:
            Path to archived file or None if no pending feedback
        """
        if not self.has_pending_feedback():
            return None

        self.archive_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        archive_file = self.archive_dir / f"{timestamp}.md"

        self.pending_file.rename(archive_file)
        return archive_file

    def clear_feedback(self) -> bool:
        """Clear pending feedback without archiving.

        Returns:
            True if feedback was cleared
        """
        if self.has_pending_feedback():
            self.pending_file.unlink()
            return True
        return False
