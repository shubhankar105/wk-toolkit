"""Shared Rich formatting helpers for CLI output."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


console = Console()


# ------------------------------------------------------------------
# Colour helpers
# ------------------------------------------------------------------

def risk_color(score: int) -> str:
    """Return a Rich colour name for a risk *score* (0-100)."""
    if score <= 25:
        return "green"
    if score <= 50:
        return "yellow"
    if score <= 75:
        return "dark_orange"
    return "red"


def _bar(score: int, width: int = 30) -> Text:
    filled = max(0, min(width, round(score / 100 * width)))
    colour = risk_color(score)
    bar = Text()
    bar.append("█" * filled, style=colour)
    bar.append("░" * (width - filled), style="dim")
    bar.append(f" {score}/100", style=f"bold {colour}")
    return bar


# ------------------------------------------------------------------
# Risk
# ------------------------------------------------------------------

def format_risk_panel(result: Any) -> Panel:
    """Build a Rich Panel for a :class:`RiskResult`."""
    body = Text()
    body.append_text(_bar(result.total_score))
    body.append(f"\n{result.level}", style=f"bold {risk_color(result.total_score)}")
    body.append(f"  —  {result.summary}\n")
    if result.recommendations:
        body.append("\nRecommendations:\n", style="bold")
        for rec in result.recommendations:
            body.append(f"  • {rec}\n")
    return Panel(body, title="[bold]RISK ASSESSMENT[/bold]", border_style=risk_color(result.total_score))


# ------------------------------------------------------------------
# EWS checks
# ------------------------------------------------------------------

def format_ews_table(checks: Sequence[Dict[str, Any]]) -> Table:
    table = Table(title="EWS / CI Checks", show_lines=False)
    table.add_column("Status", width=3)
    table.add_column("Name")
    table.add_column("Conclusion")
    for c in checks:
        status = c.get("status", "")
        conclusion = c.get("conclusion", "")
        icon = "⏳" if status == "in_progress" else ("✅" if conclusion == "success" else "❌")
        table.add_row(icon, c.get("name", ""), conclusion or status)
    return table


# ------------------------------------------------------------------
# Reviewers
# ------------------------------------------------------------------

def format_reviewer_table(suggestions: Sequence[Any]) -> Table:
    table = Table(title="SUGGESTED REVIEWERS", show_lines=False)
    table.add_column("#", width=3)
    table.add_column("Name")
    table.add_column("Score", justify="right")
    table.add_column("Commits", justify="right")
    table.add_column("Expertise")
    table.add_column("CODEOWNER", width=10)
    for i, s in enumerate(suggestions, 1):
        badge = "✅" if s.is_codeowner else ""
        table.add_row(
            str(i),
            s.author,
            f"{s.score:.3f}",
            str(s.commits_to_changed_files),
            ", ".join(s.expertise_areas[:3]),
            badge,
        )
    return table


# ------------------------------------------------------------------
# Test predictions
# ------------------------------------------------------------------

def format_test_table(predictions: Sequence[Any]) -> Table:
    table = Table(title="PREDICTED TESTS", show_lines=False)
    table.add_column("Type", width=20)
    table.add_column("Test Path")
    table.add_column("Relevance", justify="right")
    _type_labels = {
        "direct_match": "Layout Tests",
        "api_test": "API Tests",
        "wpt": "WPT Tests",
        "component_fallback": "Component Fallback",
    }
    for p in predictions:
        label = _type_labels.get(p.reason, p.reason)
        colour = {
            "direct_match": "green",
            "api_test": "cyan",
            "wpt": "blue",
            "component_fallback": "dim",
        }.get(p.reason, "white")
        table.add_row(
            Text(label, style=colour),
            p.test_path,
            f"{p.relevance_score:.2f}",
        )
    return table


# ------------------------------------------------------------------
# WPT coverage
# ------------------------------------------------------------------

def format_wpt_panel(coverage: Any) -> Panel:
    body = Text()
    pct = round(coverage.coverage_score * 100)
    colour = "green" if pct >= 75 else ("yellow" if pct >= 50 else "red")
    body.append(f"Coverage score: {pct}%\n", style=f"bold {colour}")
    body.append(f"WPT specs found: {coverage.total_wpt_specs_found}\n")
    if coverage.covered_specs:
        body.append("\nCovered specs:\n", style="bold")
        for spec in coverage.covered_specs:
            body.append(f"  ✅ {spec.spec_dir} ({spec.wpt_test_pattern})\n", style="green")
    if coverage.missing_coverage:
        body.append("\nMissing coverage:\n", style="bold")
        for m in coverage.missing_coverage:
            body.append(f"  ⚠️  {m.source_file} — {m.reason}\n", style="yellow")
    if coverage.recommendations:
        body.append("\nRecommendations:\n", style="bold")
        for rec in coverage.recommendations:
            body.append(f"  • {rec}\n")
    return Panel(body, title="[bold]WPT COVERAGE[/bold]", border_style=colour)


# ------------------------------------------------------------------
# Style violations
# ------------------------------------------------------------------

def format_style_table(violations: Sequence[Any]) -> Table | Text:
    if not violations:
        return Text("  ✅ No style violations found", style="green")
    table = Table(title="STYLE CHECK", show_lines=False)
    table.add_column("Line", justify="right", width=5)
    table.add_column("Rule")
    table.add_column("Message")
    table.add_column("Severity", width=8)
    for v in violations:
        sev_style = "red" if v.severity == "error" else "yellow"
        table.add_row(str(v.line_number), v.rule, v.message, Text(v.severity, style=sev_style))
    return table


# ------------------------------------------------------------------
# Build warnings
# ------------------------------------------------------------------

def format_build_warnings(warnings: Sequence[Any]) -> Text:
    if not warnings:
        return Text("  ✅ No build system impact", style="green")
    body = Text()
    for w in warnings:
        icon = {"info": "ℹ️ ", "warning": "⚠️ ", "critical": "🔴"}.get(w.severity, "•")
        body.append(f"  {icon} [{w.category}] {w.message}\n")
        for f in w.affected_files[:3]:
            body.append(f"      {f}\n", style="dim")
    return body


# ------------------------------------------------------------------
# Commit message
# ------------------------------------------------------------------

def format_commit_panel(message: str) -> Panel:
    return Panel(message, title="[bold]COMMIT MESSAGE[/bold]", border_style="cyan")


# ------------------------------------------------------------------
# Component table
# ------------------------------------------------------------------

def format_component_table(
    components: Dict[str, List[str]],
    platform_files: Sequence[str] | None = None,
) -> Table:
    platform_files = set(platform_files or [])
    table = Table(title="COMPONENT IMPACT", show_lines=False)
    table.add_column("Component")
    table.add_column("Files", justify="right")
    table.add_column("Platform-specific")
    for comp, files in sorted(components.items()):
        plat = any(f in platform_files for f in files)
        table.add_row(comp, str(len(files)), "⚠️  yes" if plat else "")
    return table
