"""Real-time monitoring dashboard for autonomous development."""

import time
from pathlib import Path
from typing import Optional

from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config import Config
from .state import RunStatus, State, TaskStatus


class DevelopmentMonitor:
    """Real-time monitoring dashboard for autonomous development."""

    def __init__(self, config: Config):
        """Initialize the monitor.

        Args:
            config: Configuration object
        """
        self.config = config
        self.console = Console()
        self.last_state: Optional[State] = None

    def read_state(self) -> State:
        """Read current state from state file.

        Returns:
            Current state or a waiting state if file doesn't exist
        """
        state = State.load(self.config.state_file)
        if state:
            return state

        # Return waiting state if no state file exists
        return State.create_waiting(self.config.max_iterations)

    def create_header_panel(self, state: State) -> Panel:
        """Create header panel with title and status.

        Args:
            state: Current state

        Returns:
            Header panel
        """
        status_color = {
            RunStatus.RUNNING: "green",
            RunStatus.WAITING: "yellow",
            RunStatus.ERROR: "red",
            RunStatus.STOPPED: "blue",
        }.get(state.status, "white")

        title = Text("Steer-Driven Runner Monitor", style="bold cyan")
        status_text = Text(f"Status: {state.status.value.upper()}", style=f"bold {status_color}")

        content = Text.assemble(title, "\n", status_text)
        return Panel(content, box=box.DOUBLE, border_style="cyan")

    def create_iteration_panel(self, state: State) -> Panel:
        """Create iteration progress panel.

        Args:
            state: Current state

        Returns:
            Iteration panel
        """
        iteration = state.iteration
        current = iteration.current
        specified = iteration.specified

        if specified > 0:
            progress_pct = (current / specified) * 100
            progress_bar = self._create_progress_bar(progress_pct, width=30)
            content = f"Iteration: {current}/{specified}\n{progress_bar}\nProgress: {progress_pct:.1f}%"
        else:
            content = f"Iteration: {current}/∞\nContinuous mode (no limit)"

        return Panel(content, title="Iteration Progress", border_style="green")

    def create_code_metrics_panel(self, state: State) -> Panel:
        """Create code metrics panel.

        Args:
            state: Current state

        Returns:
            Code metrics panel
        """
        metrics = state.code_metrics

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Total Lines", f"{metrics.total_lines:,}")
        table.add_row("File Count", str(metrics.file_count))

        return Panel(table, title="Code Metrics", border_style="blue")

    def create_current_task_panel(self, state: State) -> Panel:
        """Create current task panel.

        Args:
            state: Current state

        Returns:
            Current task panel
        """
        task = state.current_task
        description = task.description
        task_status = task.status

        status_color = {
            TaskStatus.PENDING: "yellow",
            TaskStatus.IN_PROGRESS: "green",
            TaskStatus.COMPLETED: "blue",
            TaskStatus.ERROR: "red",
        }.get(task_status, "white")

        content = Text()
        content.append("Status: ", style="bold")
        content.append(task_status.value, style=f"bold {status_color}")
        content.append("\n\nTask:\n", style="bold")
        content.append(description, style="white")

        return Panel(content, title="Current Task", border_style="magenta")

    def create_output_panel(self, state: State) -> Panel:
        """Create output panel showing recent output.

        Args:
            state: Current state

        Returns:
            Output panel
        """
        output = state.last_output

        if not output:
            output = "[dim]No output yet...[/dim]"

        # Truncate to last 10 lines
        lines = output.split("\n")
        if len(lines) > 10:
            lines = lines[-10:]
            output = "\n".join(lines)

        return Panel(output, title="Recent Output", border_style="yellow")

    def create_timestamp_panel(self, state: State) -> Panel:
        """Create timestamp panel.

        Args:
            state: Current state

        Returns:
            Timestamp panel
        """
        from datetime import datetime

        timestamp = state.timestamp
        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        elapsed = (datetime.now() - timestamp).total_seconds()
        elapsed_str = f"({elapsed:.0f}s ago)"

        content = f"Last Update: {time_str} {elapsed_str}"
        return Panel(content, border_style="dim")

    def _create_progress_bar(self, percentage: float, width: int = 30) -> str:
        """Create a text-based progress bar.

        Args:
            percentage: Progress percentage (0-100)
            width: Width of the progress bar

        Returns:
            Progress bar string
        """
        filled = int((percentage / 100) * width)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"

    def create_layout(self, state: State) -> Layout:
        """Create the overall layout.

        Args:
            state: Current state

        Returns:
            Layout object
        """
        layout = Layout()

        # Split into header, body, and footer
        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )

        # Split body into left and right
        layout["body"].split_row(Layout(name="left"), Layout(name="right"))

        # Split left into iteration, metrics, and task
        layout["left"].split_column(
            Layout(name="iteration", size=8),
            Layout(name="metrics", size=8),
            Layout(name="task"),
        )

        # Right side is output
        layout["right"].update(self.create_output_panel(state))

        # Fill panels
        layout["header"].update(self.create_header_panel(state))
        layout["iteration"].update(self.create_iteration_panel(state))
        layout["metrics"].update(self.create_code_metrics_panel(state))
        layout["task"].update(self.create_current_task_panel(state))
        layout["footer"].update(self.create_timestamp_panel(state))

        return layout

    def run(self) -> None:
        """Run the monitoring dashboard."""
        try:
            with Live(
                self.create_layout(self.read_state()),
                refresh_per_second=1 / self.config.monitor_refresh_rate,
                console=self.console,
            ) as live:
                while True:
                    state = self.read_state()
                    self.last_state = state
                    live.update(self.create_layout(state))
                    time.sleep(self.config.monitor_refresh_rate)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Monitor stopped by user.[/yellow]")
