"""State management for monitoring and persistence."""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    """Status of the autonomous runner."""

    WAITING = "waiting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class TaskStatus(str, Enum):
    """Status of the current task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"


class IterationState(BaseModel):
    """Iteration progress information."""

    current: int = Field(description="Current iteration number")
    specified: int = Field(description="Specified maximum iterations")


class CodeMetrics(BaseModel):
    """Code metrics collected during development."""

    total_lines: int = Field(default=0, description="Total lines of code")
    file_count: int = Field(default=0, description="Number of source files")


class TaskInfo(BaseModel):
    """Information about the current task."""

    description: str = Field(description="Task description")
    status: TaskStatus = Field(description="Current status of the task")


class State(BaseModel):
    """Complete state of the autonomous runner."""

    status: RunStatus = Field(description="Overall runner status")
    iteration: IterationState = Field(description="Iteration progress")
    code_metrics: CodeMetrics = Field(default_factory=CodeMetrics, description="Code metrics")
    current_task: TaskInfo = Field(description="Current task information")
    last_output: str = Field(default="", description="Recent output from the runner")
    timestamp: datetime = Field(default_factory=datetime.now, description="State timestamp")

    def save(self, path: Path) -> None:
        """Save state to JSON file.

        Args:
            path: Path to save the state file
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2, default=str)

    @classmethod
    def load(cls, path: Path) -> Optional["State"]:
        """Load state from JSON file.

        Args:
            path: Path to load the state file from

        Returns:
            State object or None if file doesn't exist or is invalid
        """
        if not path.exists():
            return None

        try:
            with open(path, "r") as f:
                data = json.load(f)
            return cls(**data)
        except (json.JSONDecodeError, ValueError):
            return None

    @classmethod
    def create_waiting(cls, max_iterations: int) -> "State":
        """Create a waiting state.

        Args:
            max_iterations: Maximum number of iterations

        Returns:
            State object in waiting status
        """
        return cls(
            status=RunStatus.WAITING,
            iteration=IterationState(current=0, specified=max_iterations),
            current_task=TaskInfo(
                description="Waiting for autonomous runner to start...",
                status=TaskStatus.PENDING,
            ),
            last_output="",
        )


def collect_code_metrics(project_root: Path) -> CodeMetrics:
    """Collect code metrics from the project.

    Args:
        project_root: Root directory of the project

    Returns:
        CodeMetrics with collected data
    """
    src_dir = project_root / "src"
    if not src_dir.exists():
        return CodeMetrics(total_lines=0, file_count=0)

    total_lines = 0
    file_count = 0

    for ext in ["*.ts", "*.tsx", "*.js", "*.py"]:
        files = list(src_dir.rglob(ext))
        file_count += len(files)

        for file in files:
            try:
                with open(file, "r") as f:
                    total_lines += sum(1 for _ in f)
            except (IOError, UnicodeDecodeError):
                continue

    return CodeMetrics(total_lines=total_lines, file_count=file_count)
