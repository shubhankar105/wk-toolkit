"""wk branch — branch management commands."""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

console = Console()

_DEMO_BRANCHES = [
    {"name": "main", "upstream": "origin/main", "is_current": False, "ahead": 0, "behind": 0},
    {"name": "fix/has-selector", "upstream": "origin/fix/has-selector", "is_current": True, "ahead": 3, "behind": 0},
    {"name": "feature/webgpu-compute", "upstream": "origin/feature/webgpu-compute", "is_current": False, "ahead": 12, "behind": 5},
    {"name": "fix/flexbox-minheight", "upstream": "origin/fix/flexbox-minheight", "is_current": False, "ahead": 1, "behind": 20},
    {"name": "experiment/jsc-opt", "upstream": None, "is_current": False, "ahead": 0, "behind": 0},
    {"name": "cleanup/old-tests", "upstream": "origin/cleanup/old-tests", "is_current": False, "ahead": 0, "behind": 45},
]


@click.group("branch")
def branch() -> None:
    """Branch management commands."""


@branch.command("list")
@click.option("--demo", is_flag=True, help="Use demo data.")
def branch_list(demo: bool) -> None:
    """List local branches with tracking info."""
    table = Table(title="Local Branches", show_lines=False)
    table.add_column("", width=2)
    table.add_column("Branch")
    table.add_column("Upstream")
    table.add_column("Ahead", justify="right")
    table.add_column("Behind", justify="right")
    for b in _DEMO_BRANCHES:
        marker = "→" if b["is_current"] else " "
        name_style = "bold green" if b["is_current"] else ""
        ahead_style = "green" if b["ahead"] > 0 else "dim"
        behind_style = "red" if b["behind"] > 5 else "dim"
        table.add_row(
            marker,
            f"[{name_style}]{b['name']}[/{name_style}]" if name_style else b["name"],
            b["upstream"] or "[dim]none[/dim]",
            f"[{ahead_style}]+{b['ahead']}[/{ahead_style}]",
            f"[{behind_style}]-{b['behind']}[/{behind_style}]",
        )
    console.print(table)


@branch.command("clean")
@click.option("--demo", is_flag=True, help="Use demo data.")
def branch_clean(demo: bool) -> None:
    """Show merged branches that could be deleted."""
    console.print("[bold]Branches merged and safe to delete:[/bold]")
    console.print("  • cleanup/old-tests (behind by 45, fully merged)")
    console.print()
    console.print("[dim]Run with --confirm to delete these branches[/dim]")


@branch.command("rebase")
@click.option("--demo", is_flag=True, help="Use demo data.")
def branch_rebase(demo: bool) -> None:
    """Rebase the current branch onto main."""
    console.print("[bold]Rebasing fix/has-selector onto main...[/bold]")
    console.print()
    console.print("  Current branch: [green]fix/has-selector[/green]")
    console.print("  Base branch:    main")
    console.print("  Commits to rebase: 3")
    console.print()
    console.print("[dim]Use --confirm to perform the rebase[/dim]")
