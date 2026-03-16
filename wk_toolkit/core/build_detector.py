"""Detect when changes affect the build system."""

from __future__ import annotations

import os
from typing import List, Sequence

from pydantic import BaseModel, Field

from wk_toolkit.core.component_classifier import ComponentClassifier


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class BuildWarning(BaseModel):
    """A single build-system warning."""

    category: str
    message: str
    severity: str  # "info" | "warning" | "critical"
    affected_files: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SOURCE_EXTS = (".cpp", ".mm", ".c")

# Test directories — files here do NOT trigger "new source file" warnings.
_TEST_ROOTS = (
    "LayoutTests/",
    "JSTests/",
    "PerformanceTests/",
    "Tools/TestWebKitAPI/",
)


# ---------------------------------------------------------------------------
# BuildDetector
# ---------------------------------------------------------------------------

class BuildDetector:
    """Detect build-system impacts from a set of changed files."""

    def __init__(self) -> None:
        self._classifier = ComponentClassifier()

    # ------------------------------------------------------------------
    # Detection helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_test_path(path: str) -> bool:
        return any(path.startswith(r) for r in _TEST_ROOTS)

    @staticmethod
    def _ext(path: str) -> str:
        _, ext = os.path.splitext(path)
        return ext.lower()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, changed_files: Sequence[str]) -> List[BuildWarning]:
        """Return build warnings for *changed_files*."""
        warnings: List[BuildWarning] = []

        new_source: List[str] = []
        cmake: List[str] = []
        xcode: List[str] = []
        feature_flag: List[str] = []
        public_header: List[str] = []
        sources_txt: List[str] = []
        derived: List[str] = []

        for path in changed_files:
            basename = os.path.basename(path)

            # 1. new_source_files
            if (
                self._ext(path) in _SOURCE_EXTS
                and not self._is_test_path(path)
            ):
                new_source.append(path)

            # 2. cmake_changes
            if basename == "CMakeLists.txt":
                cmake.append(path)

            # 3. xcodeproj_changes
            if ".xcodeproj" in path or ".xcworkspace" in path:
                xcode.append(path)

            # 4. feature_flag_changes
            if basename.startswith("PlatformEnable") or basename.startswith(
                "FeatureDefines"
            ):
                feature_flag.append(path)

            # 5. public_header_changes
            if "/PublicHeaders/" in path or path.startswith(
                "Source/WebKit/UIProcess/API/"
            ):
                public_header.append(path)

            # 6. sources_txt_changes
            if basename == "Sources.txt":
                sources_txt.append(path)

            # 7. derived_sources
            if "DerivedSources" in basename or "Generator" in basename:
                derived.append(path)

        # --- Emit warnings ---

        if new_source:
            warnings.append(
                BuildWarning(
                    category="new_source_files",
                    message="New source file may need Sources.txt entry for unified builds",
                    severity="warning",
                    affected_files=new_source,
                )
            )

        if cmake:
            warnings.append(
                BuildWarning(
                    category="cmake_changes",
                    message="CMake configuration changed — full reconfigure required",
                    severity="info",
                    affected_files=cmake,
                )
            )

        if xcode:
            warnings.append(
                BuildWarning(
                    category="xcodeproj_changes",
                    message="Xcode project changed",
                    severity="warning",
                    affected_files=xcode,
                )
            )

        if feature_flag:
            warnings.append(
                BuildWarning(
                    category="feature_flag_changes",
                    message="Feature flags changed — may affect conditional compilation",
                    severity="warning",
                    affected_files=feature_flag,
                )
            )

        if public_header:
            warnings.append(
                BuildWarning(
                    category="public_header_changes",
                    message="Public API header changed — may break framework clients",
                    severity="warning",
                    affected_files=public_header,
                )
            )

        if sources_txt:
            warnings.append(
                BuildWarning(
                    category="sources_txt_changes",
                    message="Unified source list modified — clean build recommended",
                    severity="info",
                    affected_files=sources_txt,
                )
            )

        if derived:
            warnings.append(
                BuildWarning(
                    category="derived_sources",
                    message="Code generation scripts changed — derived sources will regenerate",
                    severity="warning",
                    affected_files=derived,
                )
            )

        return warnings

    def has_build_impact(self, changed_files: Sequence[str]) -> bool:
        """Return ``True`` if any build warnings are generated."""
        return len(self.detect(changed_files)) > 0
