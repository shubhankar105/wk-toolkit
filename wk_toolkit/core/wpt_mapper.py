"""Map WebCore source changes to Web Platform Tests coverage."""

from __future__ import annotations

import os
from typing import Dict, List, Sequence

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# WPT root inside the WebKit repo
# ---------------------------------------------------------------------------

WPT_ROOT = "LayoutTests/imported/w3c/web-platform-tests/"

# ---------------------------------------------------------------------------
# Source pattern → WPT spec directory mapping (~40 entries)
#
# Keys are *relative* sub-paths inside Source/WebCore/ (without the
# "Source/WebCore/" prefix).  Values are the WPT spec directory name
# that lives under WPT_ROOT.
# ---------------------------------------------------------------------------

SOURCE_TO_WPT_SPEC: Dict[str, str] = {
    # CSS
    "css/CSSSelector": "css/selectors",
    "css/CSSGrid": "css/css-grid",
    "css/CSSFlexibleBox": "css/css-flexbox",
    "css/CSSContainerRule": "css/css-contain",
    "css/CSSColor": "css/css-color",
    "css/CSSAnimation": "css/css-animations",
    "css/CSSTransition": "css/css-transitions",
    "css/CSSTransform": "css/css-transforms",
    "css/CSSTypedOM": "css/css-typed-om",
    "css/CSSCustomProperty": "css/css-variables",
    "css/CSSCounterStyles": "css/css-counter-styles",
    "css/CSSFont": "css/css-fonts",
    "css/CSSText": "css/css-text",
    "css/CSSWritingMode": "css/css-writing-modes",
    "css/MediaQuery": "css/mediaqueries",
    "css/CSSScroll": "css/scroll-animations",
    "css/CSSOverflow": "css/css-overflow",
    "css/CSSPosition": "css/css-position",
    # DOM
    "dom/MutationObserver": "dom/mutations",
    "dom/Element": "dom/nodes",
    "dom/Document": "dom/nodes",
    "dom/CustomElement": "custom-elements",
    "dom/ShadowRoot": "shadow-dom",
    "dom/Range": "dom/ranges",
    "dom/Event": "dom/events",
    "dom/AbortController": "dom/abort",
    # HTML
    "html/HTMLFormElement": "html/semantics/forms",
    "html/HTMLMediaElement": "media-source",
    "html/HTMLCanvasElement": "html/canvas",
    "html/HTMLInputElement": "html/semantics/forms",
    "html/HTMLDialogElement": "html/semantics/interactive-elements/the-dialog-element",
    # Modules
    "Modules/fetch": "fetch",
    "Modules/webgpu": "webgpu",
    "Modules/indexeddb": "IndexedDB",
    "Modules/websockets": "websockets",
    "Modules/streams": "streams",
    "Modules/webaudio": "webaudio",
    "Modules/webxr": "webxr",
    "Modules/service-worker": "service-workers",
    # Platform / other
    "platform/network": "fetch",
    "svg/": "svg",
    "accessibility/": "wai-aria",
    "workers/": "workers",
}

# Directories inside Source/WebCore/ where WPT coverage is *expected*.
# Used to flag missing coverage.
_WEBCORE_WPT_EXPECTED_DIRS = (
    "css/",
    "dom/",
    "html/",
    "svg/",
    "accessibility/",
    "workers/",
    "Modules/",
    "platform/network/",
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class WPTSpecMatch(BaseModel):
    """A match between source files and a WPT spec directory."""

    spec_dir: str
    matched_source_files: List[str]
    wpt_test_pattern: str = ""


class MissingWPTCoverage(BaseModel):
    """A source file that should have WPT coverage but lacks a mapping."""

    source_file: str
    expected_spec_dir: str = ""
    reason: str = ""


class WPTCoverage(BaseModel):
    """Full WPT coverage report for a set of changed files."""

    covered_specs: List[WPTSpecMatch] = Field(default_factory=list)
    missing_coverage: List[MissingWPTCoverage] = Field(default_factory=list)
    coverage_score: float = 0.0
    total_wpt_specs_found: int = 0
    recommendations: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# WPTMapper
# ---------------------------------------------------------------------------

class WPTMapper:
    """Map WebCore source changes to Web Platform Tests coverage."""

    def _extract_source_pattern(self, path: str) -> str | None:
        """Extract the relevant sub-path inside Source/WebCore/.

        Returns ``None`` if *path* is not under ``Source/WebCore/``.
        """
        prefix = "Source/WebCore/"
        if not path.startswith(prefix):
            return None

        rel = path[len(prefix):]  # e.g. "css/CSSSelector.cpp"
        # Strip the file extension to get the stem.
        stem, _ = os.path.splitext(rel)
        return stem  # e.g. "css/CSSSelector"

    def _match_spec(self, pattern: str) -> str | None:
        """Return the WPT spec dir for *pattern*, or ``None``.

        Tries an exact match first, then checks whether *pattern*
        starts with any of the mapping keys (for directory-level keys
        like ``"svg/"``).
        """
        if pattern in SOURCE_TO_WPT_SPEC:
            return SOURCE_TO_WPT_SPEC[pattern]

        # Check prefix-style keys (e.g. "svg/", "accessibility/",
        # "Modules/fetch").
        for key, spec in SOURCE_TO_WPT_SPEC.items():
            if pattern.startswith(key):
                return spec

        return None

    def _is_wpt_expected(self, rel_path: str) -> bool:
        """Return True if *rel_path* (under Source/WebCore/) is in a
        directory where WPT coverage is expected."""
        return any(rel_path.startswith(d) for d in _WEBCORE_WPT_EXPECTED_DIRS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def map_files(self, changed_files: Sequence[str]) -> WPTCoverage:
        """Analyse *changed_files* and build a WPT coverage report."""
        # Accumulate spec_dir → list of source files.
        spec_to_files: Dict[str, List[str]] = {}
        missing: List[MissingWPTCoverage] = []
        webcore_count = 0
        covered_count = 0

        for path in changed_files:
            path = path.replace("\\", "/")
            pattern = self._extract_source_pattern(path)
            if pattern is None:
                # Not a WebCore file — skip entirely (not flagged).
                continue

            webcore_count += 1
            spec = self._match_spec(pattern)

            if spec is not None:
                covered_count += 1
                spec_to_files.setdefault(spec, []).append(path)
            elif self._is_wpt_expected(pattern):
                # WebCore file in a directory where we *expect* WPT
                # coverage, but no mapping exists.
                filename = os.path.basename(path)
                stem, _ = os.path.splitext(filename)
                missing.append(
                    MissingWPTCoverage(
                        source_file=path,
                        expected_spec_dir=pattern.split("/")[0],
                        reason=f"No WPT spec mapping for {stem} — consider adding tests",
                    )
                )

        # Build covered_specs list.
        covered_specs: List[WPTSpecMatch] = []
        for spec_dir, files in sorted(spec_to_files.items()):
            covered_specs.append(
                WPTSpecMatch(
                    spec_dir=spec_dir,
                    matched_source_files=files,
                    wpt_test_pattern=f"{spec_dir}/*.html",
                )
            )

        # Coverage score.
        coverage_score = (covered_count / webcore_count) if webcore_count > 0 else 0.0

        # Recommendations.
        recommendations: List[str] = []
        for m in missing:
            stem = os.path.splitext(os.path.basename(m.source_file))[0]
            recommendations.append(
                f"Add WPT tests for {stem} in {m.expected_spec_dir}/"
            )

        return WPTCoverage(
            covered_specs=covered_specs,
            missing_coverage=missing,
            coverage_score=coverage_score,
            total_wpt_specs_found=len(covered_specs),
            recommendations=recommendations,
        )

    def get_wpt_test_paths(self, changed_files: Sequence[str]) -> List[str]:
        """Return a flat list of WPT test directory paths to run."""
        coverage = self.map_files(changed_files)
        return [
            f"{WPT_ROOT}{spec.spec_dir}/"
            for spec in coverage.covered_specs
        ]
