"""Tests for ReviewerFinder."""

import pytest
from datetime import datetime, timezone, timedelta

from wk_toolkit.core.reviewer_finder import (
    BlameEntry,
    ReviewerFinder,
    ReviewerSuggestion,
)


def _date_str(days_ago: int = 0) -> str:
    """Return a git-style date string *days_ago* days in the past."""
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.strftime("%Y-%m-%d %H:%M:%S +0000")


@pytest.fixture
def finder() -> ReviewerFinder:
    return ReviewerFinder()


# ------------------------------------------------------------------
# Basic suggestions
# ------------------------------------------------------------------

class TestBasicSuggestions:
    def test_single_author_suggested(self, finder: ReviewerFinder) -> None:
        blame = [
            BlameEntry(
                author="Alice",
                email="alice@webkit.org",
                date=_date_str(1),
                file_path="Source/WebCore/css/CSSParser.cpp",
            ),
        ]
        result = finder.find_reviewers(blame, ["Source/WebCore/css/CSSParser.cpp"])
        assert len(result) == 1
        assert result[0].author == "Alice"
        assert result[0].commits_to_changed_files == 1

    def test_multiple_authors_ranked_by_recency(self, finder: ReviewerFinder) -> None:
        blame = [
            BlameEntry(
                author="Alice",
                email="alice@webkit.org",
                date=_date_str(100),
                file_path="Source/WebCore/css/CSSParser.cpp",
            ),
            BlameEntry(
                author="Bob",
                email="bob@webkit.org",
                date=_date_str(1),
                file_path="Source/WebCore/css/CSSParser.cpp",
            ),
        ]
        result = finder.find_reviewers(blame, ["Source/WebCore/css/CSSParser.cpp"])
        assert result[0].author == "Bob"
        assert result[0].score > result[1].score

    def test_author_with_more_commits_ranks_higher(self, finder: ReviewerFinder) -> None:
        blame = [
            BlameEntry(author="Alice", email="a@w.org", date=_date_str(5), file_path="a.cpp"),
            BlameEntry(author="Alice", email="a@w.org", date=_date_str(6), file_path="a.cpp"),
            BlameEntry(author="Alice", email="a@w.org", date=_date_str(7), file_path="a.cpp"),
            BlameEntry(author="Bob", email="b@w.org", date=_date_str(5), file_path="a.cpp"),
        ]
        result = finder.find_reviewers(blame, ["a.cpp"])
        assert result[0].author == "Alice"

    def test_returns_max_5(self, finder: ReviewerFinder) -> None:
        blame = [
            BlameEntry(author=f"Dev{i}", email=f"d{i}@w.org", date=_date_str(i), file_path="a.cpp")
            for i in range(10)
        ]
        result = finder.find_reviewers(blame, ["a.cpp"])
        assert len(result) <= 5


# ------------------------------------------------------------------
# PR author filtering
# ------------------------------------------------------------------

class TestPRAuthorFiltering:
    def test_pr_author_filtered_out(self, finder: ReviewerFinder) -> None:
        blame = [
            BlameEntry(author="Alice", email="a@w.org", date=_date_str(1), file_path="a.cpp"),
            BlameEntry(author="Bob", email="b@w.org", date=_date_str(2), file_path="a.cpp"),
        ]
        result = finder.find_reviewers(blame, ["a.cpp"], pr_author="Alice")
        assert all(s.author != "Alice" for s in result)
        assert len(result) == 1
        assert result[0].author == "Bob"


# ------------------------------------------------------------------
# CODEOWNERS
# ------------------------------------------------------------------

class TestCodeowners:
    def test_codeowner_boost(self) -> None:
        codeowners = {"Source/WebCore/css/": ["Alice"]}
        finder = ReviewerFinder(codeowners=codeowners)
        blame = [
            BlameEntry(author="Alice", email="a@w.org", date=_date_str(10), file_path="Source/WebCore/css/CSSParser.cpp"),
            BlameEntry(author="Bob", email="b@w.org", date=_date_str(1), file_path="Source/WebCore/css/CSSParser.cpp"),
        ]
        result = finder.find_reviewers(blame, ["Source/WebCore/css/CSSParser.cpp"])
        alice = next(s for s in result if s.author == "Alice")
        assert alice.is_codeowner is True

    def test_codeowner_marked_correctly(self) -> None:
        codeowners = {"Source/WebCore/css/": ["Bob"]}
        finder = ReviewerFinder(codeowners=codeowners)
        blame = [
            BlameEntry(author="Alice", email="a@w.org", date=_date_str(1), file_path="Source/WebCore/css/X.cpp"),
            BlameEntry(author="Bob", email="b@w.org", date=_date_str(2), file_path="Source/WebCore/css/X.cpp"),
        ]
        result = finder.find_reviewers(blame, ["Source/WebCore/css/X.cpp"])
        bob = next(s for s in result if s.author == "Bob")
        alice = next(s for s in result if s.author == "Alice")
        assert bob.is_codeowner is True
        assert alice.is_codeowner is False


# ------------------------------------------------------------------
# parse_codeowners
# ------------------------------------------------------------------

class TestParseCodeowners:
    def test_basic_parsing(self) -> None:
        content = (
            "# Comment line\n"
            "Source/WebCore/css/ @AWebKitReviewer @AnotherDev\n"
            "Source/JavaScriptCore/ @AJSCExpert\n"
            "\n"
            "# Another comment\n"
        )
        result = ReviewerFinder.parse_codeowners(content)
        assert result == {
            "Source/WebCore/css/": ["AWebKitReviewer", "AnotherDev"],
            "Source/JavaScriptCore/": ["AJSCExpert"],
        }

    def test_empty_content(self) -> None:
        assert ReviewerFinder.parse_codeowners("") == {}

    def test_comments_only(self) -> None:
        assert ReviewerFinder.parse_codeowners("# just comments\n# more") == {}


# ------------------------------------------------------------------
# Edge cases
# ------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_blame_returns_empty(self, finder: ReviewerFinder) -> None:
        assert finder.find_reviewers([], ["a.cpp"]) == []

    def test_expertise_areas_populated(self, finder: ReviewerFinder) -> None:
        blame = [
            BlameEntry(author="Alice", email="a@w.org", date=_date_str(1), file_path="Source/WebCore/css/CSSParser.cpp"),
            BlameEntry(author="Alice", email="a@w.org", date=_date_str(2), file_path="Source/JavaScriptCore/jit/JIT.cpp"),
        ]
        result = finder.find_reviewers(blame, ["Source/WebCore/css/CSSParser.cpp"])
        alice = result[0]
        assert len(alice.expertise_areas) >= 2

    def test_multiple_files_combined_scoring(self, finder: ReviewerFinder) -> None:
        blame = [
            BlameEntry(author="Alice", email="a@w.org", date=_date_str(1), file_path="a.cpp"),
            BlameEntry(author="Alice", email="a@w.org", date=_date_str(2), file_path="b.cpp"),
        ]
        result = finder.find_reviewers(blame, ["a.cpp", "b.cpp"])
        assert result[0].author == "Alice"
        assert result[0].commits_to_changed_files == 2
