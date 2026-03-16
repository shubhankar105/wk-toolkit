"""Thin wrapper around subprocess git calls for WebKit repositories."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class GitClient:
    """Execute common git operations via subprocess.

    All methods handle errors gracefully — they return empty or
    default results on failure and never raise.
    """

    def __init__(self, cwd: Optional[str] = None) -> None:
        self.cwd = cwd or str(Path.cwd())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _run(
        self,
        args: List[str],
        *,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        """Run a git command and return the CompletedProcess."""
        return subprocess.run(
            ["git"] + args,
            cwd=self.cwd,
            capture_output=True,
            text=True,
            check=check,
        )

    def _run_lines(self, args: List[str]) -> List[str]:
        """Run a git command and return non-empty stdout lines."""
        result = self._run(args)
        if result.returncode != 0:
            return []
        return [l for l in result.stdout.splitlines() if l.strip()]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def current_branch(self) -> str:
        """Return the name of the currently checked-out branch."""
        try:
            result = self._run(["rev-parse", "--abbrev-ref", "HEAD"])
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return ""

    def list_branches(self) -> List[Dict[str, object]]:
        """Return a list of local branches with tracking info.

        Each entry is a dict with keys:
        ``name``, ``upstream``, ``is_current``, ``ahead``, ``behind``.
        """
        try:
            lines = self._run_lines(
                [
                    "for-each-ref",
                    "--format=%(HEAD)|%(refname:short)|%(upstream:short)|%(upstream:track)",
                    "refs/heads/",
                ]
            )
        except Exception:
            return []

        branches: List[Dict[str, object]] = []
        for line in lines:
            parts = line.split("|", 3)
            if len(parts) < 4:
                continue
            head_marker, name, upstream, track = parts

            ahead = behind = 0
            if track:
                m_ahead = re.search(r"ahead (\d+)", track)
                m_behind = re.search(r"behind (\d+)", track)
                if m_ahead:
                    ahead = int(m_ahead.group(1))
                if m_behind:
                    behind = int(m_behind.group(1))

            branches.append(
                {
                    "name": name,
                    "upstream": upstream or None,
                    "is_current": head_marker.strip() == "*",
                    "ahead": ahead,
                    "behind": behind,
                }
            )
        return branches

    def changed_files(self, base: str = "main") -> List[str]:
        """Return file paths changed between *base* and HEAD."""
        try:
            lines = self._run_lines(["diff", "--name-only", f"{base}...HEAD"])
            return lines
        except Exception:
            return []

    def log_blame(
        self, file_path: str, n: int = 50
    ) -> List[Tuple[str, str, str]]:
        """Return the last *n* blame entries for *file_path*.

        Each entry is ``(author, email, date)``.
        """
        try:
            lines = self._run_lines(
                [
                    "log",
                    f"-{n}",
                    "--format=%an|%ae|%ai",
                    "--",
                    file_path,
                ]
            )
            results: List[Tuple[str, str, str]] = []
            for line in lines:
                parts = line.split("|", 2)
                if len(parts) == 3:
                    results.append((parts[0], parts[1], parts[2]))
            return results
        except Exception:
            return []

    def log_follow(
        self, file_path: str, n: int = 30
    ) -> List[Dict[str, str]]:
        """Return commit history for *file_path*, following renames.

        Each entry has keys: ``hash``, ``author``, ``date``, ``subject``.
        """
        try:
            lines = self._run_lines(
                [
                    "log",
                    f"-{n}",
                    "--follow",
                    "--format=%H|%an|%ai|%s",
                    "--",
                    file_path,
                ]
            )
            results: List[Dict[str, str]] = []
            for line in lines:
                parts = line.split("|", 3)
                if len(parts) == 4:
                    results.append(
                        {
                            "hash": parts[0],
                            "author": parts[1],
                            "date": parts[2],
                            "subject": parts[3],
                        }
                    )
            return results
        except Exception:
            return []

    def diff_stat(self, base: str = "main") -> Dict[str, Tuple[int, int]]:
        """Return ``{file: (additions, deletions)}`` vs *base*."""
        try:
            lines = self._run_lines(["diff", "--numstat", f"{base}...HEAD"])
            stats: Dict[str, Tuple[int, int]] = {}
            for line in lines:
                parts = line.split("\t", 2)
                if len(parts) == 3:
                    add_str, del_str, name = parts
                    additions = int(add_str) if add_str != "-" else 0
                    deletions = int(del_str) if del_str != "-" else 0
                    stats[name] = (additions, deletions)
            return stats
        except Exception:
            return {}

    def has_conflicts(self, base: str = "main") -> bool:
        """Return ``True`` if merging *base* into HEAD would conflict."""
        try:
            # Dry-run merge to check for conflicts.
            result = self._run(["merge-tree", "--write-tree", base, "HEAD"])
            return result.returncode != 0
        except Exception:
            return False

    def is_webkit_repo(self) -> bool:
        """Return ``True`` if the cwd looks like a WebKit checkout."""
        try:
            cwd = Path(self.cwd)
            markers = [
                cwd / "Source" / "WebCore",
                cwd / "Source" / "JavaScriptCore",
                cwd / "Source" / "WebKit",
                cwd / "Tools" / "Scripts",
            ]
            return any(m.exists() for m in markers)
        except Exception:
            return False
