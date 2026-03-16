"""wk pr — pull request commands."""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

_DEMO_PRS = [
    {"number": 1234, "title": "Improve :has() selector invalidation", "author": "AWebKitDev", "state": "open", "checks": "✅ passing", "reviews": "1 approved"},
    {"number": 1230, "title": "Fix flexbox layout with min-height", "author": "ALayoutExpert", "state": "open", "checks": "⏳ pending", "reviews": "awaiting"},
    {"number": 1228, "title": "Add WebGPU compute shader support", "author": "AGPUDev", "state": "open", "checks": "❌ failing", "reviews": "changes requested"},
    {"number": 1225, "title": "Update WPT test expectations for css-grid", "author": "ATestWriter", "state": "merged", "checks": "✅ passing", "reviews": "2 approved"},
    {"number": 1220, "title": "Refactor NetworkProcess connection handling", "author": "ANetworkDev", "state": "closed", "checks": "✅ passing", "reviews": "1 approved"},
]


@click.group("pr")
def pr() -> None:
    """Pull request commands."""


@pr.command("list")
@click.option("--demo", is_flag=True, help="Use demo data.")
def pr_list(demo: bool) -> None:
    """List recent pull requests."""
    table = Table(title="Pull Requests", show_lines=False)
    table.add_column("#", width=6, justify="right")
    table.add_column("Title")
    table.add_column("Author")
    table.add_column("State", width=8)
    table.add_column("Checks")
    table.add_column("Reviews")
    for p in _DEMO_PRS:
        state_style = {"open": "green", "merged": "magenta", "closed": "red"}.get(p["state"], "white")
        table.add_row(
            str(p["number"]),
            p["title"],
            p["author"],
            f"[{state_style}]{p['state']}[/{state_style}]",
            p["checks"],
            p["reviews"],
        )
    console.print(table)


@pr.command("status")
@click.argument("number", type=int)
@click.option("--demo", is_flag=True, help="Use demo data.")
def pr_status(number: int, demo: bool) -> None:
    """Show detailed PR status."""
    console.print(Panel(
        f"PR #{number}: Improve :has() selector invalidation\n"
        f"Author: AWebKitDev  |  State: open  |  Base: main\n"
        f"Files: 5 changed (+162 -34)\n\n"
        f"  ✅ style-queue — passed\n"
        f"  ✅ mac-wk2 — passed\n"
        f"  ⏳ ios-wk2 — in progress\n"
        f"  ✅ gtk-wk2 — passed\n\n"
        f"Reviews: 1 approved (Darin Adler)",
        title=f"[bold]PR #{number}[/bold]",
    ))


@pr.command("create")
@click.option("--demo", is_flag=True, help="Use demo data.")
def pr_create(demo: bool) -> None:
    """Preview what PR would be created from current branch."""
    console.print(Panel(
        "Would create PR:\n"
        "  Title: [WebCore] Improve :has() selector matching\n"
        "  Base: main\n"
        "  Head: fix/has-selector\n"
        "  Files: 5 changed\n\n"
        "[dim]Use --confirm to actually create the PR[/dim]",
        title="[bold]PR Preview[/bold]",
    ))


@pr.command("land")
@click.argument("number", type=int)
@click.option("--demo", is_flag=True, help="Use demo data.")
def pr_land(number: int, demo: bool) -> None:
    """Preview commit message for landing a PR."""
    console.print(Panel(
        f"[WebCore] Improve :has() selector matching\n\n"
        f"Bug: https://bugs.webkit.org/show_bug.cgi?id=12345\n"
        f"Reviewed by: Darin Adler.\n\n"
        f"* Source/WebCore/css/CSSSelector.cpp:\n"
        f"* Source/WebCore/css/CSSSelector.h:\n"
        f"* Source/WebCore/style/StyleResolver.cpp:\n"
        f"* LayoutTests/fast/css/has-selector-invalidation.html: Added.\n",
        title=f"[bold]Landing PR #{number}[/bold]",
    ))
