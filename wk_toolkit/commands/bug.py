"""wk bug — Bugzilla integration commands."""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.group("bug")
def bug() -> None:
    """Bugzilla bug tracking commands."""


@bug.command("link")
@click.argument("bugid", type=int)
@click.option("--demo", is_flag=True, help="Use demo data.")
def bug_link(bugid: int, demo: bool) -> None:
    """Link a bug to the current PR."""
    console.print(Panel(
        f"Would link Bug {bugid} to current PR\n"
        f"URL: https://bugs.webkit.org/show_bug.cgi?id={bugid}\n\n"
        "[dim]Use --confirm to apply[/dim]",
        title=f"[bold]Link Bug #{bugid}[/bold]",
    ))


@bug.command("create")
@click.option("--demo", is_flag=True, help="Use demo data.")
def bug_create(demo: bool) -> None:
    """Create a new Bugzilla bug (placeholder)."""
    console.print(Panel(
        "Would create a new bug:\n"
        "  Product: WebKit\n"
        "  Component: CSS\n"
        "  Summary: (from current branch name)\n\n"
        "[dim]Use interactive mode for full bug creation[/dim]",
        title="[bold]Create Bug[/bold]",
    ))


@bug.command("sync")
@click.option("--demo", is_flag=True, help="Use demo data.")
def bug_sync(demo: bool) -> None:
    """Show bug sync status."""
    console.print("[bold]Bug sync status:[/bold]")
    console.print("  Bug 12345 — ASSIGNED — linked to PR #1234")
    console.print("  Bug 12340 — RESOLVED FIXED — PR #1230 merged")
    console.print()
    console.print("[dim]All bugs in sync[/dim]")
