"""wk status — quick overview of current state."""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


@click.command("status")
@click.option("--demo", is_flag=True, help="Use demo data.")
def status(demo: bool) -> None:
    """Show a dense overview of current state."""
    body = Text()
    body.append("Branch: ", style="bold")
    body.append("fix/has-selector", style="green")
    body.append("  (ahead 3, behind 0 from main)\n")

    body.append("\nOpen PRs:\n", style="bold")
    body.append("  #1234  Improve :has() selector invalidation  ")
    body.append("✅ checks passing", style="green")
    body.append("  1 approved\n")

    body.append("\nEWS Summary:\n", style="bold")
    body.append("  ✅ mac-wk2  ✅ gtk-wk2  ⏳ ios-wk2  ✅ style-queue\n")

    body.append("\nAction Items:\n", style="bold")
    body.append("  • ios-wk2 build still in progress\n", style="yellow")
    body.append("  • Consider adding WPT tests for :has() selector\n", style="dim")

    body.append("\nLast Activity: ", style="bold")
    body.append("2 hours ago — pushed 1 commit\n")

    console.print(Panel(body, title="[bold]wk-toolkit Status[/bold]", border_style="cyan"))
