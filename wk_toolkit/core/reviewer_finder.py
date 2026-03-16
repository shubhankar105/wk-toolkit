"""Suggest reviewers based on git blame analysis and CODEOWNERS."""

from __future__ import annotations

import fnmatch
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence

from pydantic import BaseModel, Field

from wk_toolkit.core.component_classifier import ComponentClassifier


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class BlameEntry(BaseModel):
    """A single blame record from git log."""

    author: str
    email: str
    date: str  # ISO-ish format, e.g. "2025-01-15 10:30:00 +0000"
    file_path: str


class ReviewerSuggestion(BaseModel):
    """A suggested reviewer with scoring details."""

    author: str
    email: str
    score: float
    commits_to_changed_files: int
    most_recent_date: str
    is_codeowner: bool = False
    expertise_areas: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# ReviewerFinder
# ---------------------------------------------------------------------------

class ReviewerFinder:
    """Suggest reviewers for a set of changed files."""

    def __init__(
        self, codeowners: Optional[Dict[str, List[str]]] = None
    ) -> None:
        self._codeowners = codeowners or {}
        self._classifier = ComponentClassifier()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _days_since(date_str: str) -> float:
        """Return fractional days between *date_str* and now (UTC)."""
        try:
            # Try parsing "YYYY-MM-DD HH:MM:SS +ZZZZ" (git log --format=%ai)
            dt = datetime.strptime(
                date_str.strip()[:19], "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)
        except (ValueError, IndexError):
            try:
                dt = datetime.fromisoformat(date_str.strip())
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except ValueError:
                return 365.0  # fallback — treat unparseable as old
        now = datetime.now(timezone.utc)
        delta = now - dt
        return max(delta.total_seconds() / 86400.0, 0.0)

    def _codeowner_usernames(self, changed_files: Sequence[str]) -> set[str]:
        """Return the set of codeowner usernames that match *changed_files*."""
        owners: set[str] = set()
        for pattern, usernames in self._codeowners.items():
            for f in changed_files:
                if f.startswith(pattern) or fnmatch.fnmatch(f, pattern):
                    owners.update(usernames)
        return owners

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_reviewers(
        self,
        blame_data: Sequence[BlameEntry],
        changed_files: Sequence[str],
        pr_author: str = "",
    ) -> List[ReviewerSuggestion]:
        """Return up to 5 suggested reviewers, sorted by score descending."""

        if not blame_data:
            return []

        # 1. Accumulate per-author stats.
        author_scores: Dict[str, float] = defaultdict(float)
        author_commits: Dict[str, int] = defaultdict(int)
        author_email: Dict[str, str] = {}
        author_dates: Dict[str, str] = {}
        author_files: Dict[str, set[str]] = defaultdict(set)

        for entry in blame_data:
            days = self._days_since(entry.date)
            recency = 1.0 / (days + 1)
            author_scores[entry.author] += recency
            author_commits[entry.author] += 1
            author_email[entry.author] = entry.email
            author_files[entry.author].add(entry.file_path)

            # Track most recent date per author.
            prev = author_dates.get(entry.author)
            if prev is None or entry.date > prev:
                author_dates[entry.author] = entry.date

        # 2. Filter out PR author.
        if pr_author:
            author_scores.pop(pr_author, None)

        # 3. CODEOWNERS boost.
        co_users = self._codeowner_usernames(changed_files)
        for author in list(author_scores):
            email = author_email.get(author, "")
            username = email.split("@")[0] if email else ""
            if author in co_users or username in co_users:
                author_scores[author] *= 2.0

        # 4. Expertise areas via ComponentClassifier.
        author_expertise: Dict[str, List[str]] = {}
        for author in author_scores:
            components: set[str] = set()
            for fp in author_files.get(author, set()):
                components.add(self._classifier.classify(fp))
            author_expertise[author] = sorted(components)

        # 5. Build suggestions, sort, return top 5.
        suggestions: List[ReviewerSuggestion] = []
        for author, score in author_scores.items():
            email = author_email.get(author, "")
            username = email.split("@")[0] if email else ""
            is_co = author in co_users or username in co_users
            suggestions.append(
                ReviewerSuggestion(
                    author=author,
                    email=author_email.get(author, ""),
                    score=round(score, 6),
                    commits_to_changed_files=author_commits.get(author, 0),
                    most_recent_date=author_dates.get(author, ""),
                    is_codeowner=is_co,
                    expertise_areas=author_expertise.get(author, []),
                )
            )

        suggestions.sort(key=lambda s: s.score, reverse=True)
        return suggestions[:5]

    # ------------------------------------------------------------------
    # CODEOWNERS parser
    # ------------------------------------------------------------------

    @staticmethod
    def parse_codeowners(content: str) -> Dict[str, List[str]]:
        """Parse GitHub CODEOWNERS format into ``{pattern: [usernames]}``."""
        result: Dict[str, List[str]] = {}
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            pattern = parts[0]
            owners = [p.lstrip("@") for p in parts[1:] if p.startswith("@")]
            if owners:
                result[pattern] = owners
        return result
