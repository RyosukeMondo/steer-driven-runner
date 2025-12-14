"""Configuration management for steer-driven-runner."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Configuration for autonomous development runner."""

    # Runner settings
    max_iterations: int = Field(default=50, description="Maximum number of iterations")
    checkpoint_interval: int = Field(
        default=10, description="Checkpoint interval for human review"
    )
    spec_name: Optional[str] = Field(default=None, description="Specification name to run")

    # Codex/AI settings
    codex_cmd: str = Field(default="codex", description="Codex command")
    codex_model: str = Field(
        default="gpt-5.1-codex",
        description="Codex model (gpt-5.1-codex-max, gpt-5.1-codex, gpt-5.1-codex-mini, gpt-5-codex)",
    )
    codex_flags: str = Field(
        default="--dangerously-bypass-approvals-and-sandbox",
        description="Codex flags for automation",
    )
    max_tokens: int = Field(default=4000, description="Max tokens for Codex")
    temperature: float = Field(default=0.7, description="Temperature for Codex")

    # Project paths
    project_root: Path = Field(default=Path.cwd(), description="Project root directory")

    # Circuit breaker settings
    max_no_progress: int = Field(
        default=3, description="Max iterations without progress before stopping"
    )
    max_consecutive_failures: int = Field(
        default=3, description="Max consecutive failures before escalation"
    )

    # Monitoring
    monitor_refresh_rate: float = Field(
        default=2.0, description="Monitor refresh rate in seconds"
    )

    # Derived paths
    @property
    def spec_dir(self) -> Optional[Path]:
        """Get specification directory."""
        if self.spec_name:
            return self.project_root / ".spec-workflow" / "specs" / self.spec_name
        return None

    @property
    def tasks_file(self) -> Optional[Path]:
        """Get tasks file path."""
        if self.spec_dir:
            return self.spec_dir / "tasks.md"
        return None

    @property
    def steering_dir(self) -> Path:
        """Get steering documents directory."""
        return self.project_root / ".spec-workflow" / "steering"

    @property
    def feedback_file(self) -> Path:
        """Get pending feedback file path."""
        return self.project_root / ".spec-workflow" / "feedback" / "pending.md"

    @property
    def monitor_dir(self) -> Path:
        """Get monitor state directory."""
        return self.project_root / ".spec-workflow" / "monitor"

    @property
    def state_file(self) -> Path:
        """Get state file path."""
        return self.monitor_dir / "state.json"

    @property
    def log_file(self) -> Path:
        """Get log file path."""
        return self.project_root / "autonomous-dev.log"

    @property
    def is_steering_driven(self) -> bool:
        """Check if running in steering-driven mode (no spec name or tasks.md missing)."""
        if not self.spec_name:
            return True
        if self.tasks_file and self.tasks_file.exists():
            return False
        return True

    class Config:
        """Pydantic config."""

        env_prefix = "STEER_"
        env_file = ".env"
        case_sensitive = False
