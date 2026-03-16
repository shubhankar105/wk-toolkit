"""wk test — test prediction and execution commands."""

from __future__ import annotations

import click
from rich.console import Console

from wk_toolkit.core.test_predictor import TestPredictor
from wk_toolkit.core.wpt_mapper import WPTMapper
from wk_toolkit.formatters.rich_output import format_test_table, format_wpt_panel

console = Console()

_DEMO_SOURCE_FILES = [
    "Source/WebCore/css/CSSSelector.cpp",
    "Source/WebCore/css/CSSSelector.h",
    "Source/WebCore/style/StyleResolver.cpp",
]


@click.group("test")
def test() -> None:
    """Test prediction and execution commands."""


@test.command("predict")
@click.option("--demo", is_flag=True, help="Use demo data.")
def test_predict(demo: bool) -> None:
    """Predict which tests to run for current changes."""
    predictor = TestPredictor()
    predictions = predictor.predict(_DEMO_SOURCE_FILES)
    summary = predictor.predict_summary(_DEMO_SOURCE_FILES)

    console.print(format_test_table(predictions))
    console.print()
    console.print(
        f"[bold]Total:[/bold] {summary['total_predicted']} test targets  "
        f"[bold]Est. runtime:[/bold] {summary['estimated_runtime_minutes']} min"
    )


@test.command("wpt-check")
@click.option("--demo", is_flag=True, help="Use demo data.")
def test_wpt_check(demo: bool) -> None:
    """Check WPT coverage for current changes."""
    mapper = WPTMapper()
    coverage = mapper.map_files(_DEMO_SOURCE_FILES)
    console.print(format_wpt_panel(coverage))


@test.command("run")
@click.option("--demo", is_flag=True, help="Use demo data.")
def test_run(demo: bool) -> None:
    """Show what tests would be run (placeholder)."""
    predictor = TestPredictor()
    predictions = predictor.predict(_DEMO_SOURCE_FILES)
    paths = [p.test_path for p in predictions if p.reason == "direct_match"]
    if paths:
        console.print("[bold]Would run:[/bold]")
        console.print(f"  Tools/Scripts/run-webkit-tests {' '.join(paths)}")
    else:
        console.print("[dim]No specific tests predicted.[/dim]")
