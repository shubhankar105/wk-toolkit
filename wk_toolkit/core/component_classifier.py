"""Classify WebKit file paths into components using longest-prefix matching."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Sequence

from wk_toolkit.config import Components


# Directories that indicate platform-specific code.
_PLATFORM_DIRS = ("cocoa/", "glib/", "win/", "gtk/", "wpe/")

# Top-level directories that contain tests.
_TEST_ROOTS = (
    "LayoutTests/",
    "JSTests/",
    "Tools/TestWebKitAPI/",
    "PerformanceTests/",
)


class ComponentClassifier:
    """Map WebKit repository paths to their owning component.

    Uses a hierarchical prefix dictionary.  On lookup the *longest*
    matching prefix wins, so ``Source/JavaScriptCore/dfg/foo.cpp``
    resolves to ``JavaScriptCore/DFG`` rather than the broader
    ``JavaScriptCore``.
    """

    def __init__(self) -> None:
        # Build the prefix → component mapping.
        # Order doesn't matter – we always pick the longest match.
        self._prefixes: Dict[str, str] = {}
        self._build_prefix_map()

        # Pre-sort prefixes longest-first for efficient matching.
        self._sorted_prefixes: List[str] = sorted(
            self._prefixes, key=len, reverse=True
        )

    # ------------------------------------------------------------------
    # Prefix map construction
    # ------------------------------------------------------------------

    def _build_prefix_map(self) -> None:
        p = self._prefixes

        # --- JavaScriptCore sub-components ---
        p["Source/JavaScriptCore/dfg/"] = Components.JSC_DFG
        p["Source/JavaScriptCore/ftl/"] = Components.JSC_FTL
        p["Source/JavaScriptCore/b3/"] = Components.JSC_B3
        p["Source/JavaScriptCore/wasm/"] = Components.JSC_WASM
        p["Source/JavaScriptCore/parser/"] = Components.JSC_PARSER
        p["Source/JavaScriptCore/runtime/"] = Components.JSC_RUNTIME
        p["Source/JavaScriptCore/bytecode/"] = Components.JSC_BYTECODE
        p["Source/JavaScriptCore/heap/"] = Components.JSC_HEAP
        p["Source/JavaScriptCore/jit/"] = Components.JSC_JIT
        p["Source/JavaScriptCore/llint/"] = Components.JSC_LLINT
        p["Source/JavaScriptCore/"] = Components.JSC

        # --- WebCore sub-components ---
        p["Source/WebCore/css/"] = Components.WEBCORE_CSS
        p["Source/WebCore/dom/"] = Components.WEBCORE_DOM
        p["Source/WebCore/html/"] = Components.WEBCORE_HTML
        p["Source/WebCore/layout/"] = Components.WEBCORE_LAYOUT
        p["Source/WebCore/rendering/"] = Components.WEBCORE_RENDERING
        p["Source/WebCore/platform/network/"] = Components.WEBCORE_NETWORK
        p["Source/WebCore/platform/graphics/"] = Components.WEBCORE_GRAPHICS
        p["Source/WebCore/svg/"] = Components.WEBCORE_SVG
        p["Source/WebCore/accessibility/"] = Components.WEBCORE_ACCESSIBILITY
        p["Source/WebCore/bindings/"] = Components.WEBCORE_BINDINGS
        p["Source/WebCore/page/"] = Components.WEBCORE_PAGE
        p["Source/WebCore/editing/"] = Components.WEBCORE_EDITING
        p["Source/WebCore/Modules/webgpu/"] = Components.WEBCORE_WEBGPU
        p["Source/WebCore/Modules/fetch/"] = Components.WEBCORE_FETCH
        p["Source/WebCore/Modules/indexeddb/"] = Components.WEBCORE_INDEXEDDB
        p["Source/WebCore/workers/"] = Components.WEBCORE_WORKERS

        # WebCore platform-specific
        p["Source/WebCore/platform/cocoa/"] = Components.WEBCORE_PLATFORM_COCOA
        p["Source/WebCore/platform/glib/"] = Components.WEBCORE_PLATFORM_GLIB
        p["Source/WebCore/platform/win/"] = Components.WEBCORE_PLATFORM_WIN

        # WebCore catch-all
        p["Source/WebCore/"] = Components.WEBCORE

        # --- WebKit (multi-process) ---
        p["Source/WebKit/UIProcess/"] = Components.WEBKIT_UIPROCESS
        p["Source/WebKit/WebProcess/"] = Components.WEBKIT_WEBPROCESS
        p["Source/WebKit/NetworkProcess/"] = Components.WEBKIT_NETWORKPROCESS
        p["Source/WebKit/GPUProcess/"] = Components.WEBKIT_GPUPROCESS
        p["Source/WebKit/"] = Components.WEBKIT

        # --- Other source modules ---
        p["Source/WTF/"] = Components.WTF
        p["Source/WebGPU/"] = Components.WEBGPU
        p["Source/WebInspectorUI/"] = Components.WEBINSPECTORUI
        p["Source/WebDriver/"] = Components.WEBDRIVER
        p["Source/bmalloc/"] = Components.BMALLOC

        # --- Tools ---
        p["Tools/Scripts/"] = Components.TOOLS_SCRIPTS
        p["Tools/CISupport/"] = Components.TOOLS_CISUPPORT
        p["Tools/TestWebKitAPI/"] = Components.TOOLS_TESTWEBKITAPI
        p["Tools/buildbot/"] = Components.TOOLS_BUILDBOT

        # --- LayoutTests sub-components ---
        p["LayoutTests/fast/css/"] = Components.LAYOUT_TESTS_CSS
        p["LayoutTests/fast/dom/"] = Components.LAYOUT_TESTS_DOM
        p["LayoutTests/fast/html/"] = Components.LAYOUT_TESTS_HTML
        p["LayoutTests/http/"] = Components.LAYOUT_TESTS_HTTP
        p["LayoutTests/imported/w3c/web-platform-tests/"] = Components.LAYOUT_TESTS_WPT
        p["LayoutTests/"] = Components.LAYOUT_TESTS

        # --- Other test / top-level dirs ---
        p["JSTests/"] = Components.JSTESTS
        p["PerformanceTests/"] = Components.PERFORMANCE_TESTS
        p["Websites/"] = Components.WEBSITES

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(self, path: str) -> str:
        """Return the component name for *path*.

        Matches the longest prefix first. Returns ``Components.OTHER``
        when no prefix matches.
        """
        # Normalise backslashes (Windows paths) to forward slashes.
        path = path.replace("\\", "/")

        for prefix in self._sorted_prefixes:
            if path.startswith(prefix):
                return self._prefixes[prefix]

        return Components.OTHER

    def classify_many(self, paths: Sequence[str]) -> Dict[str, List[str]]:
        """Classify *paths* and group them by component.

        Returns a dict mapping component name → list of file paths.
        """
        groups: Dict[str, List[str]] = defaultdict(list)
        for path in paths:
            component = self.classify(path)
            groups[component].append(path)
        return dict(groups)

    @staticmethod
    def is_platform_specific(path: str) -> bool:
        """Return ``True`` if *path* lives under a platform-specific directory."""
        path = path.replace("\\", "/")
        return any(d in path.split("/") for d in ("cocoa", "glib", "win", "gtk", "wpe"))

    @staticmethod
    def is_test_file(path: str) -> bool:
        """Return ``True`` if *path* is inside a recognised test directory."""
        path = path.replace("\\", "/")
        return any(path.startswith(root) for root in _TEST_ROOTS)
