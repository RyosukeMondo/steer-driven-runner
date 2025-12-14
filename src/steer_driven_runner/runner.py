"""Main autonomous development runner."""

import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from rich.console import Console
from rich.logging import RichHandler

from .config import Config
from .feedback import FeedbackManager
from .state import RunStatus, State, TaskInfo, TaskStatus, collect_code_metrics, IterationState


class AutonomousRunner:
    """Autonomous development runner driven by steering documents."""

    def __init__(self, config: Config):
        """Initialize the runner.

        Args:
            config: Configuration object
        """
        self.config = config
        self.console = Console()
        self.feedback_manager = FeedbackManager(config.project_root)
        self.logger = self._setup_logging()

        # Circuit breaker state
        self.consecutive_failures = 0
        self.no_progress_count = 0

    def _setup_logging(self) -> logging.Logger:
        """Set up logging with rich handler.

        Returns:
            Configured logger
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[
                RichHandler(console=self.console, rich_tracebacks=True),
                logging.FileHandler(self.config.log_file),
            ],
        )
        return logging.getLogger(__name__)

    def _print_banner(self) -> None:
        """Print startup banner."""
        self.console.print()
        self.console.print("╔════════════════════════════════════════════════════════════╗", style="blue")
        self.console.print("║          🤖 Steer-Driven Autonomous Runner                ║", style="blue")
        self.console.print("║          AI-Driven Development                             ║", style="blue")
        self.console.print("╚════════════════════════════════════════════════════════════╝", style="blue")
        self.console.print()

        self.console.print("📊 Configuration:", style="blue")
        self.console.print(f"  Max iterations: {self.config.max_iterations}")
        self.console.print(f"  Checkpoint interval: {self.config.checkpoint_interval}")
        if self.config.spec_name:
            self.console.print(f"  Spec: {self.config.spec_name}")
        else:
            self.console.print("  Mode: Steering-driven (no spec)", style="green")
        self.console.print(f"  Project root: {self.config.project_root}")
        self.console.print(f"  Log file: {self.config.log_file}")
        self.console.print()

    def _validate_environment(self) -> None:
        """Validate the environment before starting.

        Raises:
            RuntimeError: If validation fails
        """
        product_md = self.config.steering_dir / "product.md"
        if not product_md.exists():
            raise RuntimeError(
                f"Steering documents not found at {self.config.steering_dir}\n"
                "Please ensure product.md, design.md, and tech.md exist."
            )

        # Determine mode
        if self.config.is_steering_driven:
            self.logger.info("✓ Running in steering-driven mode")
            self.logger.info("Will work directly from steering documents")
        else:
            self.logger.info(f"✓ Running in task-driven mode with spec: {self.config.spec_name}")

    def _check_stop_file(self) -> bool:
        """Check if stop file exists.

        Returns:
            True if should stop
        """
        stop_file = self.config.project_root / "stop.txt"
        if stop_file.exists():
            self.console.print()
            self.console.print("╔════════════════════════════════════════════════════════╗", style="yellow")
            self.console.print("║  🛑 STOP FILE DETECTED                                ║", style="yellow")
            self.console.print("║  Graceful shutdown after current iteration           ║", style="yellow")
            self.console.print("╚════════════════════════════════════════════════════════╝", style="yellow")
            self.console.print()
            self.logger.info(f"Found: {stop_file}")
            self.logger.info("Removing stop.txt for next run...")
            stop_file.unlink()
            return True
        return False

    def _get_task_counts(self) -> Tuple[int, int, int]:
        """Get task counts from tasks.md if available.

        Returns:
            Tuple of (pending, in_progress, completed) counts
        """
        if self.config.is_steering_driven or not self.config.tasks_file:
            return 0, 0, 0

        if not self.config.tasks_file.exists():
            return 0, 0, 0

        try:
            content = self.config.tasks_file.read_text()
            pending = content.count("\n- [ ]")
            in_progress = content.count("\n- [-]")
            completed = content.count("\n- [x]")
            return pending, in_progress, completed
        except IOError:
            return 0, 0, 0

    def _get_current_task_description(self) -> str:
        """Get the current task description from tasks.md.

        Returns:
            Current task description or default message
        """
        if self.config.is_steering_driven:
            return "Working from steering documents"

        if not self.config.tasks_file or not self.config.tasks_file.exists():
            return "No tasks.md found"

        try:
            content = self.config.tasks_file.read_text()
            for line in content.split("\n"):
                if line.strip().startswith("- [-]"):
                    # Extract task description
                    desc = line.replace("- [-]", "").strip()
                    return desc if desc else "In progress task (no description)"
            return "Waiting for next task"
        except IOError:
            return "Error reading tasks.md"

    def _write_state(
        self,
        status: RunStatus,
        iteration: int,
        current_task_desc: str,
        task_status: TaskStatus,
        last_output: str,
    ) -> None:
        """Write current state to state file.

        Args:
            status: Overall run status
            iteration: Current iteration number
            current_task_desc: Description of current task
            task_status: Status of current task
            last_output: Recent output message
        """
        state = State(
            status=status,
            iteration=IterationState(
                current=iteration,
                specified=self.config.max_iterations,
            ),
            code_metrics=collect_code_metrics(self.config.project_root),
            current_task=TaskInfo(
                description=current_task_desc,
                status=task_status,
            ),
            last_output=last_output,
            timestamp=datetime.now(),
        )
        state.save(self.config.state_file)

    def _get_current_commit(self) -> Optional[str]:
        """Get current git commit SHA.

        Returns:
            Commit SHA or None if not in git repo
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.config.project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            pass
        return None

    def _count_commits_between(self, commit1: str, commit2: str) -> int:
        """Count commits between two SHAs.

        Args:
            commit1: First commit SHA
            commit2: Second commit SHA

        Returns:
            Number of commits
        """
        try:
            result = subprocess.run(
                ["git", "rev-list", f"{commit1}..{commit2}", "--count"],
                cwd=self.config.project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
        except (FileNotFoundError, ValueError):
            pass
        return 1

    def _build_prompt(self, iteration: int, feedback_content: Optional[str]) -> str:
        """Build the prompt for Codex.

        Args:
            iteration: Current iteration number
            feedback_content: Optional feedback content

        Returns:
            Formatted prompt
        """
        # This would load the full prompt template
        # For now, returning a simplified version
        mode_status = (
            "Steering-driven (working from product.md directly)"
            if self.config.is_steering_driven
            else f"Task-driven (spec: {self.config.spec_name})"
        )

        feedback_section = ""
        if feedback_content:
            feedback_section = f"""
### ⚠️ IMPORTANT: Human Feedback Available

The human has posted async feedback for you to consider:

```
{feedback_content}
```

**Instructions:**
- CONSIDER this feedback when deciding what to implement
- If you address the feedback, mention it in your commit message
- After processing, this feedback will be archived
- Feedback is advisory - you can continue with planned work if more urgent
"""

        prompt = f"""# Autonomous Development Task - Iteration {iteration}

## Current Status
- **Iteration**: {iteration} of {self.config.max_iterations}
- **Mode**: {mode_status}

{feedback_section}

## Instructions
Read steering documents → Find next task → Implement → Test → Commit → Exit

**BEGIN IMPLEMENTATION NOW**
"""
        return prompt

    def _run_codex(self, prompt: str) -> int:
        """Run Codex with the given prompt.

        Args:
            prompt: Prompt to send to Codex

        Returns:
            Exit code from Codex
        """
        cmd = [
            self.config.codex_cmd,
            "e",
            *self.config.codex_flags.split(),
            "--model",
            self.config.codex_model,
            "-c",
            f"max_tokens={self.config.max_tokens}",
            "-c",
            f"temperature={self.config.temperature}",
            prompt,
        ]

        self.logger.info(f"🤖 Invoking Codex (model: {self.config.codex_model})...")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.config.project_root,
                check=False,
            )
            return result.returncode
        except FileNotFoundError:
            self.logger.error(f"❌ Codex command not found: {self.config.codex_cmd}")
            return 1

    def _handle_exit_code(
        self, exit_code: int, iteration: int, commit_before: Optional[str], commit_after: Optional[str]
    ) -> bool:
        """Handle Codex exit code.

        Args:
            exit_code: Exit code from Codex
            iteration: Current iteration
            commit_before: Commit SHA before iteration
            commit_after: Commit SHA after iteration

        Returns:
            True if should continue, False if should stop
        """
        if exit_code == 0:
            self.logger.info(f"✅ Iteration {iteration} completed successfully")
            self.consecutive_failures = 0

            # Archive feedback if it was processed and commits were made
            if commit_before != commit_after and self.feedback_manager.has_pending_feedback():
                archived = self.feedback_manager.archive_feedback()
                if archived:
                    self.logger.info(f"📦 Feedback archived to: {archived.name}")

            return True

        elif exit_code == 99:
            self.console.print()
            self.console.print("╔════════════════════════════════════════════════════════╗", style="green")
            self.console.print("║  🎉 PROJECT COMPLETE!                                 ║", style="green")
            self.console.print("║  All tasks done. Ready for review.                    ║", style="green")
            self.console.print("╚════════════════════════════════════════════════════════╝", style="green")
            return False

        elif exit_code == 1:
            self.consecutive_failures += 1
            self.logger.error(f"❌ Error encountered (failure {self.consecutive_failures} of {self.config.max_consecutive_failures})")

            if self.consecutive_failures >= self.config.max_consecutive_failures:
                self.console.print()
                self.console.print("╔════════════════════════════════════════════════════════╗", style="red")
                self.console.print("║  ⚠️  ESCALATION REQUIRED                              ║", style="red")
                self.console.print(f"║  {self.config.max_consecutive_failures} consecutive failures. Human intervention needed.   ║", style="red")
                self.console.print("╚════════════════════════════════════════════════════════╝", style="red")
                return False

            self.logger.warning("Retrying with next iteration...")
            return True

        else:
            self.logger.error(f"❓ Unknown exit code: {exit_code}")
            return False

    def run(self) -> int:
        """Run the autonomous development loop.

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        self._print_banner()

        try:
            self._validate_environment()
        except RuntimeError as e:
            self.logger.error(str(e))
            return 1

        iteration = 0

        while iteration < self.config.max_iterations:
            iteration += 1
            next_checkpoint = ((iteration // self.config.checkpoint_interval) + 1) * self.config.checkpoint_interval

            self.console.print()
            self.console.print("═══════════════════════════════════════════════════════════", style="blue")
            self.console.print(f"  Iteration {iteration} of {self.config.max_iterations}", style="blue")
            self.console.print("═══════════════════════════════════════════════════════════", style="blue")
            self.console.print()

            # Get task counts
            pending, in_progress, completed = self._get_task_counts()

            if not self.config.is_steering_driven:
                self.logger.info("📋 Task Status:")
                self.logger.info(f"  Pending: {pending}")
                self.logger.info(f"  In Progress: {in_progress}")
                self.logger.info(f"  Completed: {completed}")
                self.console.print()

            # Get current task description
            current_task_desc = self._get_current_task_description()

            # Write state for monitoring
            self._write_state(
                RunStatus.RUNNING,
                iteration,
                current_task_desc,
                TaskStatus.IN_PROGRESS,
                f"Iteration {iteration} starting...",
            )

            # Check for stop file
            if self._check_stop_file():
                self.logger.info("Exiting gracefully...")
                return 0

            # Check for feedback
            feedback_content = self.feedback_manager.read_pending_feedback()
            if feedback_content:
                self.logger.info("📬 Human feedback detected!")

            # Get commit before
            commit_before = self._get_current_commit()
            if commit_before:
                self.logger.info(f"📍 Current commit: {commit_before[:7]}")

            # Build prompt
            prompt = self._build_prompt(iteration, feedback_content)

            # Run Codex
            exit_code = self._run_codex(prompt)
            self.logger.info(f"Codex exited with code: {exit_code}")

            # Get commit after
            commit_after = self._get_current_commit()

            # Circuit breaker: Check if progress was made
            if commit_before == commit_after:
                self.no_progress_count += 1
                self.logger.warning(
                    f"⚠️  No git commit detected - no progress made ({self.no_progress_count}/{self.config.max_no_progress})"
                )

                if self.no_progress_count >= self.config.max_no_progress:
                    self.console.print()
                    self.console.print("╔════════════════════════════════════════════════════════╗", style="red")
                    self.console.print("║  🛑 CIRCUIT BREAKER TRIGGERED                         ║", style="red")
                    self.console.print(f"║  No commits for {self.config.max_no_progress} iterations.                     ║", style="red")
                    self.console.print("║  AI is not making progress. Human intervention needed.║", style="red")
                    self.console.print("╚════════════════════════════════════════════════════════╝", style="red")
                    return 1
            else:
                # Progress made - reset counter
                new_commits = self._count_commits_between(commit_before, commit_after) if commit_before and commit_after else 1
                self.logger.info(f"✅ Progress detected: {new_commits} new commit(s) - {commit_after[:7] if commit_after else 'unknown'}")
                self.no_progress_count = 0

            # Handle exit code
            if not self._handle_exit_code(exit_code, iteration, commit_before, commit_after):
                # Update final state
                self._write_state(
                    RunStatus.STOPPED,
                    iteration,
                    current_task_desc,
                    TaskStatus.COMPLETED,
                    "Run completed",
                )
                return 0 if exit_code in [0, 99] else exit_code

            # Checkpoint check
            if iteration % self.config.checkpoint_interval == 0:
                self.console.print()
                self.console.print("╔════════════════════════════════════════════════════════╗", style="yellow")
                self.console.print(f"║  📊 CHECKPOINT {iteration // self.config.checkpoint_interval} REACHED                               ║", style="yellow")
                self.console.print("╚════════════════════════════════════════════════════════╝", style="yellow")
                self.console.print()
                self.logger.info("Progress Summary:")
                self.logger.info(f"  Iterations completed: {iteration}")
                self.logger.info(f"  Tasks completed: {completed}")
                self.logger.info(f"  Tasks pending: {pending}")
                self.console.print()
                self.logger.info("⏸️  Pausing for human review...")
                self.logger.info("Run 'steer-run' again to continue.")

                self._write_state(
                    RunStatus.STOPPED,
                    iteration,
                    current_task_desc,
                    TaskStatus.PENDING,
                    f"Checkpoint {iteration // self.config.checkpoint_interval} - paused for review",
                )
                return 2

            # Brief pause between iterations
            time.sleep(2)

        # Max iterations reached
        self.console.print()
        self.console.print("╔════════════════════════════════════════════════════════╗", style="yellow")
        self.console.print("║  ⚠️  MAX ITERATIONS REACHED                           ║", style="yellow")
        self.console.print("║  Human review required before continuing.             ║", style="yellow")
        self.console.print("╚════════════════════════════════════════════════════════╝", style="yellow")
        self.console.print()
        self.logger.info("📊 Statistics:")
        self.logger.info(f"  Iterations completed: {self.config.max_iterations}")
        pending, _, completed = self._get_task_counts()
        self.logger.info(f"  Tasks completed: {completed}")
        self.logger.info(f"  Tasks pending: {pending}")
        self.console.print()

        self._write_state(
            RunStatus.STOPPED,
            self.config.max_iterations,
            "Max iterations reached",
            TaskStatus.PENDING,
            "Maximum iterations reached - human review required",
        )
        return 2
