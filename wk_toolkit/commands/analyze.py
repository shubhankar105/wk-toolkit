"""wk analyze — run all analysis engines and output a Rich report."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

import click
from rich.console import Console

from wk_toolkit.core.component_classifier import ComponentClassifier
from wk_toolkit.core.test_predictor import TestPredictor
from wk_toolkit.core.wpt_mapper import WPTMapper
from wk_toolkit.core.risk_scorer import RiskScorer
from wk_toolkit.core.reviewer_finder import ReviewerFinder, BlameEntry
from wk_toolkit.core.style_checker import StyleChecker
from wk_toolkit.core.build_detector import BuildDetector
from wk_toolkit.core.commit_formatter import CommitFormatter
from wk_toolkit.formatters.rich_output import (
    format_risk_panel,
    format_component_table,
    format_test_table,
    format_wpt_panel,
    format_reviewer_table,
    format_style_table,
    format_build_warnings,
    format_commit_panel,
)

console = Console()


# ------------------------------------------------------------------
# Demo data
# ------------------------------------------------------------------

def _demo_date(days_ago: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.strftime("%Y-%m-%d %H:%M:%S +0000")


_DEMO_FILES = [
    "Source/WebCore/css/CSSSelector.cpp",
    "Source/WebCore/css/CSSSelector.h",
    "Source/WebCore/style/StyleResolver.cpp",
    "LayoutTests/fast/css/has-selector-invalidation.html",
    "LayoutTests/imported/w3c/web-platform-tests/css/selectors/has/has-basic.html",
]

_DEMO_DIFF_STATS: Dict[str, Tuple[int, int]] = {
    "Source/WebCore/css/CSSSelector.cpp": (80, 25),
    "Source/WebCore/css/CSSSelector.h": (12, 4),
    "Source/WebCore/style/StyleResolver.cpp": (15, 5),
    "LayoutTests/fast/css/has-selector-invalidation.html": (30, 0),
    "LayoutTests/imported/w3c/web-platform-tests/css/selectors/has/has-basic.html": (20, 0),
}

_DEMO_BLAME: List[BlameEntry] = [
    BlameEntry(author="Antti Koivisto", email="antti@webkit.org", date=_demo_date(3), file_path="Source/WebCore/css/CSSSelector.cpp"),
    BlameEntry(author="Antti Koivisto", email="antti@webkit.org", date=_demo_date(10), file_path="Source/WebCore/css/CSSSelector.h"),
    BlameEntry(author="Darin Adler", email="darin@webkit.org", date=_demo_date(7), file_path="Source/WebCore/css/CSSSelector.cpp"),
    BlameEntry(author="Sam Weinig", email="sam@webkit.org", date=_demo_date(14), file_path="Source/WebCore/style/StyleResolver.cpp"),
    BlameEntry(author="Darin Adler", email="darin@webkit.org", date=_demo_date(20), file_path="Source/WebCore/style/StyleResolver.cpp"),
    BlameEntry(author="Antoine Quint", email="graouts@webkit.org", date=_demo_date(5), file_path="Source/WebCore/css/CSSSelector.cpp"),
    BlameEntry(author="Antti Koivisto", email="antti@webkit.org", date=_demo_date(1), file_path="Source/WebCore/css/CSSSelector.cpp"),
]

_DEMO_DIFF_LINES = [
    "+#include \"config.h\"",
    "+#include \"CSSSelector.h\"",
    "+",
    "+bool CSSSelector::matchesHas(const Element& element) const",
    "+{",
    "+    // New :has() selector matching logic",
    "+    return true;",
    "+}",
]

_DEMO_CODEOWNERS = {
    "Source/WebCore/css/": ["AWebKitReviewer", "antti"],
}


# ------------------------------------------------------------------
# Full analysis runner
# ------------------------------------------------------------------

def _run_full_analysis(
    changed_files: List[str],
    diff_stats: Dict[str, Tuple[int, int]],
    blame_data: List[BlameEntry],
    diff_lines: List[str],
    codeowners: Dict[str, List[str]] | None = None,
) -> None:
    """Execute all analysis engines and print the Rich report."""
    classifier = ComponentClassifier()
    predictor = TestPredictor()
    wpt_mapper = WPTMapper()
    risk_scorer = RiskScorer()
    reviewer_finder = ReviewerFinder(codeowners=codeowners)
    style_checker = StyleChecker()
    build_detector = BuildDetector()
    commit_formatter = CommitFormatter()

    # Component classification
    components = classifier.classify_many(changed_files)
    component_list = [classifier.classify(f) for f in changed_files]
    platform_files = [f for f in changed_files if classifier.is_platform_specific(f)]

    # Test prediction
    source_files = [f for f in changed_files if not classifier.is_test_file(f)]
    predictions = predictor.predict(source_files)

    # WPT coverage
    wpt_coverage = wpt_mapper.map_files(source_files)

    # File hotness (simulated from blame)
    file_hotness: Dict[str, int] = {}
    for entry in blame_data:
        file_hotness[entry.file_path] = file_hotness.get(entry.file_path, 0) + 1

    # Test coverage ratio
    test_files_count = sum(1 for f in changed_files if classifier.is_test_file(f))
    total = len(changed_files) or 1
    test_coverage_ratio = test_files_count / total

    # Risk scoring
    risk_result = risk_scorer.score(
        components=component_list,
        diff_stats=diff_stats,
        file_hotness=file_hotness,
        platform_specific_files=platform_files,
        test_coverage_ratio=test_coverage_ratio,
        wpt_coverage_score=wpt_coverage.coverage_score,
        codeowner_count=len(set(e.author for e in blame_data)),
    )

    # Reviewer suggestions
    reviewers = reviewer_finder.find_reviewers(blame_data, changed_files)

    # Style check
    violations = style_checker.check(diff_lines, "Source/WebCore/css/CSSSelector.cpp")

    # Build detection
    build_warnings = build_detector.detect(changed_files)

    # Commit message
    commit_msg = commit_formatter.format(
        title="Improve :has() selector matching",
        changed_files=changed_files,
        bug_id=None,
        reviewer=reviewers[0].author if reviewers else None,
    )

    # ---- Print report ----
    console.print()
    console.rule("[bold]wk-toolkit Analysis Report[/bold]")
    console.print()

    # Section 1: Risk
    console.print(format_risk_panel(risk_result))
    console.print()

    # Section 2: Component impact
    console.print(format_component_table(components, platform_files))
    console.print()

    # Section 3: Predicted tests
    console.print(format_test_table(predictions))
    console.print()

    # Section 4: WPT coverage
    console.print(format_wpt_panel(wpt_coverage))
    console.print()

    # Section 5: Reviewers
    console.print(format_reviewer_table(reviewers))
    console.print()

    # Section 6: Style check
    console.print(format_style_table(violations))
    console.print()

    # Section 7: Build impact
    console.print(format_build_warnings(build_warnings))
    console.print()

    # Section 8: Commit message
    console.print(format_commit_panel(commit_msg))
    console.print()


# ------------------------------------------------------------------
# CLI commands
# ------------------------------------------------------------------

@click.group("analyze")
def analyze() -> None:
    """Run analysis engines on your changes."""


@analyze.command("full")
@click.option("--pr", "pr_number", type=int, default=None, help="PR number to analyze.")
@click.option("--demo", is_flag=True, help="Use demo data (no git/API needed).")
def analyze_full(pr_number: int | None, demo: bool) -> None:
    """Run ALL analysis engines and output a comprehensive report."""
    if demo or pr_number is None:
        _run_full_analysis(
            changed_files=_DEMO_FILES,
            diff_stats=_DEMO_DIFF_STATS,
            blame_data=_DEMO_BLAME,
            diff_lines=_DEMO_DIFF_LINES,
            codeowners=_DEMO_CODEOWNERS,
        )
    else:
        console.print(f"[dim]Would fetch PR #{pr_number} from GitHub (requires token)[/dim]")
        console.print("[dim]Using demo data instead...[/dim]")
        _run_full_analysis(
            changed_files=_DEMO_FILES,
            diff_stats=_DEMO_DIFF_STATS,
            blame_data=_DEMO_BLAME,
            diff_lines=_DEMO_DIFF_LINES,
            codeowners=_DEMO_CODEOWNERS,
        )


@analyze.command("risk")
@click.option("--demo", is_flag=True, help="Use demo data.")
def analyze_risk(demo: bool) -> None:
    """Compute risk score for current changes."""
    classifier = ComponentClassifier()
    files = _DEMO_FILES
    component_list = [classifier.classify(f) for f in files]
    platform_files = [f for f in files if classifier.is_platform_specific(f)]
    test_files_count = sum(1 for f in files if classifier.is_test_file(f))

    result = RiskScorer().score(
        components=component_list,
        diff_stats=_DEMO_DIFF_STATS,
        file_hotness={"Source/WebCore/css/CSSSelector.cpp": 4},
        platform_specific_files=platform_files,
        test_coverage_ratio=test_files_count / len(files),
        wpt_coverage_score=0.5,
        codeowner_count=3,
    )
    console.print(format_risk_panel(result))


@analyze.command("reviewers")
@click.option("--demo", is_flag=True, help="Use demo data.")
def analyze_reviewers(demo: bool) -> None:
    """Suggest reviewers for current changes."""
    finder = ReviewerFinder(codeowners=_DEMO_CODEOWNERS)
    reviewers = finder.find_reviewers(_DEMO_BLAME, _DEMO_FILES)
    console.print(format_reviewer_table(reviewers))


@analyze.command("style")
@click.option("--demo", is_flag=True, help="Use demo data.")
def analyze_style(demo: bool) -> None:
    """Check WebKit style conventions on current diff."""
    violations = StyleChecker().check(_DEMO_DIFF_LINES, "Source/WebCore/css/CSSSelector.cpp")
    console.print(format_style_table(violations))


@analyze.command("wpt")
@click.option("--demo", is_flag=True, help="Use demo data.")
def analyze_wpt(demo: bool) -> None:
    """Check WPT coverage for current changes."""
    source = [f for f in _DEMO_FILES if f.startswith("Source/")]
    coverage = WPTMapper().map_files(source)
    console.print(format_wpt_panel(coverage))
