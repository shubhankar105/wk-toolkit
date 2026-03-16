"""Predict which tests to run based on changed source files."""

from __future__ import annotations

import os
from typing import Dict, List, Literal, Sequence

from pydantic import BaseModel, Field

from wk_toolkit.core.component_classifier import ComponentClassifier
from wk_toolkit.core.wpt_mapper import WPTMapper, WPT_ROOT


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class PredictedTest(BaseModel):
    """A single predicted test to run."""

    test_path: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    reason: Literal["direct_match", "api_test", "wpt", "component_fallback"]
    source_file: str


# ---------------------------------------------------------------------------
# Source → test directory mapping (~30 entries)
#
# Keys are prefixes inside ``Source/WebCore/``.  Values are lists of
# LayoutTests directories that exercise that source code.
# ---------------------------------------------------------------------------

SOURCE_TO_TEST_DIRS: Dict[str, List[str]] = {
    # CSS
    "css/CSSSelector": ["LayoutTests/fast/css/"],
    "css/CSSGrid": ["LayoutTests/fast/css/grid-layout/"],
    "css/CSSFlexibleBox": ["LayoutTests/fast/css/flexbox/", "LayoutTests/fast/flexbox/"],
    "css/CSSAnimation": ["LayoutTests/fast/css/animations/"],
    "css/CSSTransition": ["LayoutTests/fast/css/transitions/"],
    "css/CSSTransform": ["LayoutTests/fast/css/transforms/"],
    "css/CSSFont": ["LayoutTests/fast/css/font-face/"],
    "css/CSSColor": ["LayoutTests/fast/css/color/"],
    "css/": ["LayoutTests/fast/css/"],
    # DOM
    "dom/MutationObserver": ["LayoutTests/fast/dom/MutationObserver/"],
    "dom/Element": ["LayoutTests/fast/dom/"],
    "dom/Document": ["LayoutTests/fast/dom/"],
    "dom/Event": ["LayoutTests/fast/dom/"],
    "dom/Range": ["LayoutTests/fast/dom/Range/"],
    "dom/ShadowRoot": ["LayoutTests/fast/dom/shadow/"],
    "dom/": ["LayoutTests/fast/dom/"],
    # HTML
    "html/HTMLFormElement": ["LayoutTests/fast/forms/"],
    "html/HTMLInputElement": ["LayoutTests/fast/forms/"],
    "html/HTMLMediaElement": ["LayoutTests/media/"],
    "html/HTMLCanvasElement": ["LayoutTests/fast/canvas/"],
    "html/HTMLDialogElement": ["LayoutTests/fast/html/dialog/"],
    "html/": ["LayoutTests/fast/html/"],
    # Rendering
    "rendering/RenderFlexibleBox": ["LayoutTests/fast/css/flexbox/", "LayoutTests/fast/flexbox/"],
    "rendering/": ["LayoutTests/fast/rendering/"],
    # Layout
    "layout/": ["LayoutTests/fast/layout/"],
    # SVG
    "svg/": ["LayoutTests/svg/"],
    # Accessibility
    "accessibility/": ["LayoutTests/accessibility/"],
    # Modules
    "Modules/webgpu/": ["LayoutTests/webgpu/"],
    "Modules/fetch/": ["LayoutTests/http/"],
    "Modules/indexeddb/": ["LayoutTests/storage/indexeddb/"],
    # Platform / other
    "platform/network/": ["LayoutTests/http/"],
    "workers/": ["LayoutTests/workers/"],
    "editing/": ["LayoutTests/editing/"],
    "page/": ["LayoutTests/fast/dom/"],
}

# Component-level fallback test directories.
_COMPONENT_FALLBACK_DIRS: Dict[str, List[str]] = {
    "Source/WebCore/css/": ["LayoutTests/fast/css/"],
    "Source/WebCore/dom/": ["LayoutTests/fast/dom/"],
    "Source/WebCore/html/": ["LayoutTests/fast/html/"],
    "Source/WebCore/rendering/": ["LayoutTests/fast/rendering/"],
    "Source/WebCore/layout/": ["LayoutTests/fast/layout/"],
    "Source/WebCore/svg/": ["LayoutTests/svg/"],
    "Source/WebCore/accessibility/": ["LayoutTests/accessibility/"],
    "Source/WebCore/Modules/webgpu/": ["LayoutTests/webgpu/"],
    "Source/WebCore/Modules/fetch/": ["LayoutTests/http/"],
    "Source/WebCore/Modules/indexeddb/": ["LayoutTests/storage/indexeddb/"],
    "Source/WebCore/platform/network/": ["LayoutTests/http/"],
    "Source/WebCore/workers/": ["LayoutTests/workers/"],
    "Source/WebCore/editing/": ["LayoutTests/editing/"],
    "Source/WebCore/page/": ["LayoutTests/fast/dom/"],
    "Source/WebCore/bindings/": ["LayoutTests/fast/dom/"],
    "Source/WebCore/platform/graphics/": ["LayoutTests/fast/canvas/"],
    "Source/JavaScriptCore/": ["JSTests/"],
    "Source/WTF/": [],
}

# Map top-level source directories to their TestWebKitAPI sub-directory.
_API_TEST_COMPONENTS: Dict[str, str] = {
    "Source/WebCore/": "Tools/TestWebKitAPI/Tests/WebCore/",
    "Source/JavaScriptCore/": "Tools/TestWebKitAPI/Tests/JavaScriptCore/",
    "Source/WTF/": "Tools/TestWebKitAPI/Tests/WTF/",
    "Source/WebKit/": "Tools/TestWebKitAPI/Tests/WebKit/",
}


# ---------------------------------------------------------------------------
# TestPredictor
# ---------------------------------------------------------------------------

class TestPredictor:
    """Predict which tests should be run for a set of changed source files."""

    def __init__(self) -> None:
        self._classifier = ComponentClassifier()
        self._wpt_mapper = WPTMapper()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _webcore_relative(self, path: str) -> str | None:
        """Return the path relative to Source/WebCore/, or None."""
        prefix = "Source/WebCore/"
        if path.startswith(prefix):
            return path[len(prefix):]
        return None

    def _filename_stem(self, path: str) -> str:
        return os.path.splitext(os.path.basename(path))[0]

    def _direct_match(self, path: str) -> List[PredictedTest]:
        """Rule (a): direct path correspondence."""
        rel = self._webcore_relative(path)
        if rel is None:
            return []

        stem, _ = os.path.splitext(rel)  # e.g. "css/CSSSelector"

        # Try exact match on stem first, then prefix matches.
        matched_dirs: List[str] = []
        for key, dirs in SOURCE_TO_TEST_DIRS.items():
            if stem == key or stem.startswith(key):
                matched_dirs = dirs
                # Prefer exact match — break if it's exact.
                if stem == key:
                    break

        # If no exact / prefix hit, try matching the filename stem
        # against the keys more loosely.
        if not matched_dirs:
            # Try longest-prefix on the stem.
            best_key = ""
            for key in SOURCE_TO_TEST_DIRS:
                if stem.startswith(key) and len(key) > len(best_key):
                    best_key = key
            if best_key:
                matched_dirs = SOURCE_TO_TEST_DIRS[best_key]

        results: List[PredictedTest] = []
        for test_dir in matched_dirs:
            results.append(
                PredictedTest(
                    test_path=test_dir,
                    relevance_score=0.95,
                    reason="direct_match",
                    source_file=path,
                )
            )
        return results

    def _api_test_match(self, path: str) -> List[PredictedTest]:
        """Rule (b): API test naming match."""
        for src_prefix, test_prefix in _API_TEST_COMPONENTS.items():
            if path.startswith(src_prefix):
                stem = self._filename_stem(path)
                return [
                    PredictedTest(
                        test_path=f"{test_prefix}{stem}",
                        relevance_score=0.8,
                        reason="api_test",
                        source_file=path,
                    )
                ]
        return []

    def _wpt_match(self, path: str) -> List[PredictedTest]:
        """Rule (c): WPT spec mapping."""
        wpt_paths = self._wpt_mapper.get_wpt_test_paths([path])
        return [
            PredictedTest(
                test_path=wpt_path,
                relevance_score=0.7,
                reason="wpt",
                source_file=path,
            )
            for wpt_path in wpt_paths
        ]

    def _component_fallback(self, path: str) -> List[PredictedTest]:
        """Rule (d): component-level fallback."""
        for src_prefix, test_dirs in _COMPONENT_FALLBACK_DIRS.items():
            if path.startswith(src_prefix):
                return [
                    PredictedTest(
                        test_path=td,
                        relevance_score=0.4,
                        reason="component_fallback",
                        source_file=path,
                    )
                    for td in test_dirs
                ]
        return []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, changed_files: Sequence[str]) -> List[PredictedTest]:
        """Predict tests for *changed_files*.

        Applies rules in priority order, deduplicates (keeping highest
        relevance), and sorts by relevance descending.
        """
        all_predictions: List[PredictedTest] = []

        for path in changed_files:
            path = path.replace("\\", "/")
            file_preds: List[PredictedTest] = []

            # (a) direct match
            file_preds.extend(self._direct_match(path))

            # (b) API test match
            file_preds.extend(self._api_test_match(path))

            # (c) WPT match
            file_preds.extend(self._wpt_match(path))

            # (d) component fallback — only if no higher-priority matches
            if not file_preds:
                file_preds.extend(self._component_fallback(path))

            all_predictions.extend(file_preds)

        # Deduplicate by test_path, keeping highest relevance.
        best: Dict[str, PredictedTest] = {}
        for pred in all_predictions:
            existing = best.get(pred.test_path)
            if existing is None or pred.relevance_score > existing.relevance_score:
                best[pred.test_path] = pred

        results = sorted(best.values(), key=lambda p: p.relevance_score, reverse=True)
        return results

    def predict_summary(self, changed_files: Sequence[str]) -> Dict:
        """Return a summary dict for the predictions."""
        predictions = self.predict(changed_files)

        by_type: Dict[str, int] = {
            "direct_match": 0,
            "api_test": 0,
            "wpt": 0,
            "component_fallback": 0,
        }
        layout_dirs = 0
        api_suites = 0
        wpt_dirs = 0

        for p in predictions:
            by_type[p.reason] += 1
            if p.reason == "direct_match" or p.reason == "component_fallback":
                layout_dirs += 1
            elif p.reason == "api_test":
                api_suites += 1
            elif p.reason == "wpt":
                wpt_dirs += 1

        estimated_runtime = (
            layout_dirs * 0.5
            + api_suites * 2.0
            + wpt_dirs * 1.0
        )

        return {
            "total_predicted": len(predictions),
            "by_type": by_type,
            "estimated_runtime_minutes": round(estimated_runtime, 1),
        }
