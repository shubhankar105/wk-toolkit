"""Generate WebKit-standard commit messages."""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List, Optional, Sequence, Set

from wk_toolkit.core.component_classifier import ComponentClassifier


# ---------------------------------------------------------------------------
# CommitFormatter
# ---------------------------------------------------------------------------

class CommitFormatter:
    """Format commit messages following WebKit conventions."""

    def __init__(self) -> None:
        self._classifier = ComponentClassifier()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _primary_component(self, files: Sequence[str]) -> str:
        """Return the most common component across *files*."""
        counts: Counter[str] = Counter()
        for f in files:
            comp = self._classifier.classify(f)
            # Use the top-level component name (before '/').
            top = comp.split("/")[0]
            counts[top] += 1
        if not counts:
            return "WebKit"
        return counts.most_common(1)[0][0]

    @staticmethod
    def _sort_files(
        files: Sequence[str],
    ) -> List[str]:
        """Sort files: source files first, then test files."""
        source: List[str] = []
        tests: List[str] = []
        for f in files:
            if (
                f.startswith("LayoutTests/")
                or f.startswith("JSTests/")
                or f.startswith("PerformanceTests/")
                or f.startswith("Tools/TestWebKitAPI/")
            ):
                tests.append(f)
            else:
                source.append(f)
        return sorted(source) + sorted(tests)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def format(
        self,
        title: str,
        changed_files: Sequence[str],
        description: str = "",
        bug_id: Optional[int] = None,
        reviewer: Optional[str] = None,
        new_files: Optional[Set[str]] = None,
        deleted_files: Optional[Set[str]] = None,
    ) -> str:
        """Build a WebKit-style commit message.

        Parameters
        ----------
        title:
            Short summary line.
        changed_files:
            All files touched by the commit.
        description:
            Longer explanation (can be multi-line).
        bug_id:
            Bugzilla bug number.  Omitted from output if ``None``.
        reviewer:
            Reviewer name.  Omitted from output if ``None``.
        new_files:
            Set of file paths that are newly added.
        deleted_files:
            Set of file paths that are being removed.
        """
        new_files = new_files or set()
        deleted_files = deleted_files or set()

        component = self._primary_component(changed_files)
        parts: List[str] = []

        # Title line.
        parts.append(f"[{component}] {title}")
        parts.append("")

        # Description.
        if description:
            parts.append(description)
            parts.append("")

        # Bug URL.
        if bug_id is not None:
            parts.append(
                f"Bug: https://bugs.webkit.org/show_bug.cgi?id={bug_id}"
            )
            parts.append("")

        # Reviewed by.
        if reviewer is not None:
            parts.append(f"Reviewed by: {reviewer}.")
            parts.append("")

        # File list.
        sorted_files = self._sort_files(changed_files)
        truncated = False
        display_files = sorted_files
        if len(sorted_files) > 15:
            display_files = sorted_files[:15]
            truncated = True

        for f in display_files:
            suffix = ""
            if f in new_files:
                suffix = " Added."
            elif f in deleted_files:
                suffix = " Removed."
            parts.append(f"* {f}:{suffix}")

        if truncated:
            remaining = len(sorted_files) - 15
            parts.append(f"... and {remaining} more files")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate(message: str) -> List[str]:
        """Validate a commit message against WebKit conventions.

        Returns a list of human-readable warnings (empty = valid).
        """
        issues: List[str] = []
        lines = message.splitlines()

        if not lines:
            issues.append("Commit message is empty")
            return issues

        # 1. [Component] prefix on first line.
        if not re.match(r"^\[.+\]", lines[0]):
            issues.append("Missing [Component] prefix on the first line")

        # 2. File list with * prefix.
        has_file_list = any(l.strip().startswith("* ") for l in lines)
        if not has_file_list:
            issues.append("Missing file list (lines starting with '* ')")

        # 3. Bug URL format.
        for line in lines:
            if line.strip().startswith("Bug:"):
                if "bugs.webkit.org/show_bug.cgi?id=" not in line:
                    issues.append("Bug URL format incorrect — expected bugs.webkit.org/show_bug.cgi?id=XXXXX")

        # 4. Line length.
        for idx, line in enumerate(lines):
            # Skip file list lines (paths can be long).
            if line.strip().startswith("* ") or line.strip().startswith("..."):
                continue
            if len(line) > 72:
                issues.append(
                    f"Line {idx + 1} exceeds 72 characters ({len(line)} chars)"
                )

        return issues
