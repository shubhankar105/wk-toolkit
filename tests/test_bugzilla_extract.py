"""Tests for BugzillaClient.extract_bug_refs()."""

import pytest

from wk_toolkit.clients.bugzilla_client import BugzillaClient


class TestExtractBugRefs:
    def test_bug_uppercase(self) -> None:
        assert BugzillaClient.extract_bug_refs("Bug 12345") == [12345]

    def test_bug_lowercase(self) -> None:
        assert BugzillaClient.extract_bug_refs("bug 12345") == [12345]

    def test_multiple_bugs(self) -> None:
        text = "Fixed bug 12345 and bug 67890"
        result = BugzillaClient.extract_bug_refs(text)
        assert result == [12345, 67890]

    def test_full_url(self) -> None:
        text = "https://bugs.webkit.org/show_bug.cgi?id=12345"
        assert BugzillaClient.extract_bug_refs(text) == [12345]

    def test_short_url(self) -> None:
        text = "See webkit.org/b/12345 for details"
        assert BugzillaClient.extract_bug_refs(text) == [12345]

    def test_no_bugs(self) -> None:
        assert BugzillaClient.extract_bug_refs("No bugs here.") == []

    def test_empty_string(self) -> None:
        assert BugzillaClient.extract_bug_refs("") == []

    def test_deduplication(self) -> None:
        text = "Bug 12345 and https://bugs.webkit.org/show_bug.cgi?id=12345"
        assert BugzillaClient.extract_bug_refs(text) == [12345]

    def test_mixed_patterns(self) -> None:
        text = (
            "Bug 11111, see webkit.org/b/22222 and "
            "https://bugs.webkit.org/show_bug.cgi?id=33333"
        )
        result = BugzillaClient.extract_bug_refs(text)
        assert result == [11111, 22222, 33333]

    def test_bug_in_commit_message(self) -> None:
        text = "[WebCore] Fix selector specificity\n\nBug 54321\nReviewed by Darin."
        assert BugzillaClient.extract_bug_refs(text) == [54321]
