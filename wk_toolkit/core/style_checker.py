"""Check WebKit coding conventions on diff content."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class StyleViolation(BaseModel):
    """A single style violation."""

    line_number: int
    column: Optional[int] = None
    rule: str
    message: str
    severity: str  # "error" | "warning"


# ---------------------------------------------------------------------------
# StyleChecker
# ---------------------------------------------------------------------------

# File extensions where tabs are banned (WebKit uses 4-space indentation).
_TAB_BAN_EXTS = (".cpp", ".h", ".mm", ".js")

# Regex for "Type *var" or "Type &ref" (space before * or &).
_POINTER_RE = re.compile(r"[A-Za-z0-9_>]\s+[*&][A-Za-z_]")


class StyleChecker:
    """Check WebKit coding conventions on unified-diff content."""

    # ------------------------------------------------------------------
    # Single-file check
    # ------------------------------------------------------------------

    def check(
        self, diff_lines: List[str], file_path: str
    ) -> List[StyleViolation]:
        """Check added lines (starting with ``+``) in *diff_lines*.

        Returns a list of :class:`StyleViolation` instances.
        """
        violations: List[StyleViolation] = []
        ext = _ext(file_path)

        # Track logical line number within the added content.
        line_no = 0
        first_include_seen = False

        for raw in diff_lines:
            if not raw.startswith("+"):
                continue
            # Strip the leading "+" to get the actual source line.
            line = raw[1:]
            line_no += 1

            # 1. trailing_whitespace
            if line.rstrip("\n\r") != line.rstrip("\n\r").rstrip(" \t"):
                violations.append(
                    StyleViolation(
                        line_number=line_no,
                        rule="trailing_whitespace",
                        message="Trailing whitespace",
                        severity="error",
                    )
                )

            # 2. tab_indentation (only for relevant extensions)
            if ext in _TAB_BAN_EXTS and line.startswith("\t"):
                violations.append(
                    StyleViolation(
                        line_number=line_no,
                        rule="tab_indentation",
                        message="Tab indentation — WebKit uses 4 spaces",
                        severity="error",
                    )
                )

            # 3. line_length
            length = len(line.rstrip("\n\r"))
            if length > 200:
                violations.append(
                    StyleViolation(
                        line_number=line_no,
                        column=201,
                        rule="line_length",
                        message=f"Line too long ({length} chars, max 200)",
                        severity="error",
                    )
                )
            elif length > 120:
                violations.append(
                    StyleViolation(
                        line_number=line_no,
                        column=121,
                        rule="line_length",
                        message=f"Line too long ({length} chars, preferred max 120)",
                        severity="warning",
                    )
                )

            # 4. include_order — first #include in .cpp must be "config.h"
            if ext == ".cpp" and not first_include_seen:
                stripped = line.strip()
                if stripped.startswith("#include"):
                    first_include_seen = True
                    if '"config.h"' not in stripped.lower():
                        violations.append(
                            StyleViolation(
                                line_number=line_no,
                                rule="include_order",
                                message='First #include should be "config.h"',
                                severity="warning",
                            )
                        )

            # 5. pointer_style — "Type *var" / "Type &ref"
            if ext in (".cpp", ".h", ".mm"):
                if _POINTER_RE.search(line):
                    col = _POINTER_RE.search(line)
                    violations.append(
                        StyleViolation(
                            line_number=line_no,
                            column=col.start() + 1 if col else None,
                            rule="pointer_style",
                            message="Pointer/reference should bind to type (use Type* / Type&)",
                            severity="warning",
                        )
                    )

            # 6. copyright_header — current year check
            if "copyright" in line.lower():
                current_year = str(datetime.now().year)
                if current_year not in line:
                    violations.append(
                        StyleViolation(
                            line_number=line_no,
                            rule="copyright_header",
                            message=f"Copyright header missing current year ({current_year})",
                            severity="warning",
                        )
                    )

            # 7. no_inline_namespaces — "using namespace" in headers
            if ext == ".h" and "using namespace" in line:
                violations.append(
                    StyleViolation(
                        line_number=line_no,
                        rule="no_inline_namespaces",
                        message='"using namespace" in header file — avoid polluting namespace',
                        severity="warning",
                    )
                )

        return violations

    # ------------------------------------------------------------------
    # Multi-file check
    # ------------------------------------------------------------------

    def check_all(
        self, diff_content: str, file_paths: List[str]
    ) -> Dict[str, List[StyleViolation]]:
        """Run :meth:`check` on each file section in *diff_content*.

        Simple heuristic: splits *diff_content* by ``--- a/`` markers and
        maps each section to the corresponding file path.  If that proves
        unreliable, callers can split externally and call :meth:`check`
        directly.
        """
        results: Dict[str, List[StyleViolation]] = {}

        # Fast path: one file → whole diff applies.
        if len(file_paths) == 1:
            lines = diff_content.splitlines()
            results[file_paths[0]] = self.check(lines, file_paths[0])
            return results

        # Multi-file: split on "diff --git" or "--- a/" markers.
        sections = re.split(r"(?=^diff --git )", diff_content, flags=re.M)
        for fp in file_paths:
            matched_lines: List[str] = []
            for section in sections:
                if fp in section:
                    matched_lines = section.splitlines()
                    break
            results[fp] = self.check(matched_lines, fp)

        return results

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    @staticmethod
    def summary(
        violations: List[StyleViolation],
    ) -> Dict[str, object]:
        """Return a summary dict with counts and triggered rules."""
        errors = sum(1 for v in violations if v.severity == "error")
        warnings = sum(1 for v in violations if v.severity == "warning")
        rules = {v.rule for v in violations}
        return {
            "error_count": errors,
            "warning_count": warnings,
            "rules_triggered": rules,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ext(path: str) -> str:
    """Return the lowercased file extension, e.g. '.cpp'."""
    idx = path.rfind(".")
    if idx == -1:
        return ""
    return path[idx:].lower()
