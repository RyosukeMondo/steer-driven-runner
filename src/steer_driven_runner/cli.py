"""Command-line interface for steer-driven-runner."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from . import __version__
from .config import Config
from .feedback import FeedbackManager, FeedbackPriority, FeedbackType
from .monitor import DevelopmentMonitor
from .runner import AutonomousRunner


console = Console()


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """Steer-Driven Runner - Autonomous AI development driven by steering documents."""
    pass


@cli.command(name="run")
@click.option(
    "-i",
    "--iterations",
    type=int,
    help="Maximum iterations (default: 50)",
)
@click.option(
    "-c",
    "--checkpoint",
    type=int,
    help="Checkpoint interval (default: 10)",
)
@click.option(
    "-s",
    "--spec",
    type=str,
    help="Specification name to run",
)
@click.option(
    "-m",
    "--model",
    type=str,
    help="Codex model (default: gpt-5.1-codex)",
)
@click.option(
    "-p",
    "--project-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Project root directory (default: current directory)",
)
def run(
    iterations: Optional[int],
    checkpoint: Optional[int],
    spec: Optional[str],
    model: Optional[str],
    project_root: Optional[Path],
) -> None:
    """Run autonomous development iterations."""
    # Build config from CLI args and env
    config_kwargs = {}

    if iterations is not None:
        config_kwargs["max_iterations"] = iterations
    if checkpoint is not None:
        config_kwargs["checkpoint_interval"] = checkpoint
    if spec is not None:
        config_kwargs["spec_name"] = spec
    if model is not None:
        config_kwargs["codex_model"] = model
    if project_root is not None:
        config_kwargs["project_root"] = project_root

    config = Config(**config_kwargs)

    runner = AutonomousRunner(config)
    exit_code = runner.run()
    raise SystemExit(exit_code)


@cli.command(name="monitor")
@click.option(
    "-p",
    "--project-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Project root directory (default: current directory)",
)
@click.option(
    "-r",
    "--refresh-rate",
    type=float,
    default=2.0,
    help="Refresh rate in seconds (default: 2.0)",
)
def monitor(project_root: Optional[Path], refresh_rate: float) -> None:
    """Monitor autonomous development progress in real-time."""
    config_kwargs = {"monitor_refresh_rate": refresh_rate}

    if project_root is not None:
        config_kwargs["project_root"] = project_root

    config = Config(**config_kwargs)

    console.print("Starting Steer-Driven Runner Monitor...")
    console.print(f"Project: {config.project_root.name}")
    console.print(f"State file: {config.state_file}")
    console.print("\nPress Ctrl+C to stop\n")

    import time

    time.sleep(1)

    dev_monitor = DevelopmentMonitor(config)
    dev_monitor.run()


@cli.command(name="feedback")
@click.argument("message")
@click.option(
    "-p",
    "--priority",
    type=click.Choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"], case_sensitive=False),
    default="MEDIUM",
    help="Priority level (default: MEDIUM)",
)
@click.option(
    "-t",
    "--type",
    "feedback_type",
    type=click.Choice(["FEEDBACK", "BUG", "FEATURE", "IMPROVEMENT", "VISUAL"], case_sensitive=False),
    default="FEEDBACK",
    help="Feedback type (default: FEEDBACK)",
)
@click.option(
    "--project-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Project root directory (default: current directory)",
)
def feedback(
    message: str,
    priority: str,
    feedback_type: str,
    project_root: Optional[Path],
) -> None:
    """Post async feedback for the AI agent to process.

    MESSAGE: The feedback message to post
    """
    config_kwargs = {}
    if project_root is not None:
        config_kwargs["project_root"] = project_root

    config = Config(**config_kwargs)
    manager = FeedbackManager(config.project_root)

    # Convert string to enum
    priority_enum = FeedbackPriority[priority.upper()]
    type_enum = FeedbackType[feedback_type.upper()]

    pending_file = manager.post_feedback(message, priority_enum, type_enum)

    console.print("✓ Feedback posted successfully!", style="green")
    console.print()
    console.print(f"[blue]Feedback location:[/blue] {pending_file}")
    console.print(f"[blue]Priority:[/blue] {priority}")
    console.print(f"[blue]Type:[/blue] {feedback_type}")
    console.print()
    console.print("[yellow]Note:[/yellow] AI agent will read this feedback on the next iteration.")
    console.print("It will consider your feedback when determining what to implement next.")
    console.print()
    console.print("[blue]To view pending feedback:[/blue]")
    console.print(f"  cat {pending_file}")


@cli.command(name="init")
@click.option(
    "-p",
    "--project-root",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path.cwd(),
    help="Project root directory (default: current directory)",
)
def init(project_root: Path) -> None:
    """Initialize a new project for steer-driven development."""
    console.print(f"Initializing steer-driven development in: {project_root}")
    console.print()

    # Create directory structure
    spec_workflow = project_root / ".spec-workflow"
    steering_dir = spec_workflow / "steering"
    feedback_dir = spec_workflow / "feedback"
    monitor_dir = spec_workflow / "monitor"

    for directory in [steering_dir, feedback_dir, monitor_dir]:
        directory.mkdir(parents=True, exist_ok=True)
        console.print(f"✓ Created: {directory.relative_to(project_root)}")

    # Create template steering documents
    product_md = steering_dir / "product.md"
    if not product_md.exists():
        product_md.write_text("""# Product Specification

## Vision
[Describe the product vision]

## Features
- Feature 1
- Feature 2

## User Stories
- As a user, I want to...
""")
        console.print(f"✓ Created: {product_md.relative_to(project_root)}")

    design_md = steering_dir / "design.md"
    if not design_md.exists():
        design_md.write_text("""# Design Specification

## Architecture
[Describe the architecture]

## UI/UX
[Describe UI/UX design]
""")
        console.print(f"✓ Created: {design_md.relative_to(project_root)}")

    tech_md = steering_dir / "tech.md"
    if not tech_md.exists():
        tech_md.write_text("""# Technical Specification

## Tech Stack
- Language: [e.g., Python, TypeScript]
- Framework: [e.g., React, FastAPI]

## Code Quality
- Test coverage: ≥80%
- Linting: Enabled
""")
        console.print(f"✓ Created: {tech_md.relative_to(project_root)}")

    # Create README
    readme = spec_workflow / "README.md"
    if not readme.exists():
        readme.write_text("""# Spec Workflow

This directory contains steering documents and workflow artifacts for autonomous AI development.

## Structure
- `steering/` - Steering documents (product.md, design.md, tech.md)
- `feedback/` - Async feedback system
- `monitor/` - Runtime monitoring state

## Usage
```bash
# Run autonomous development
steer-run -i 100

# Monitor progress
steer-monitor

# Post feedback
steer-feedback "Add user authentication"
```
""")
        console.print(f"✓ Created: {readme.relative_to(project_root)}")

    console.print()
    console.print("[green]✓ Initialization complete![/green]")
    console.print()
    console.print("[blue]Next steps:[/blue]")
    console.print("1. Edit steering documents in .spec-workflow/steering/")
    console.print("2. Run: steer-run")
    console.print("3. Monitor: steer-monitor (in a separate terminal)")


# Convenience function for running via python -m
def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
