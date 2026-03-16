"""Tests for CommitFormatter."""

import pytest

from wk_toolkit.core.commit_formatter import CommitFormatter


@pytest.fixture
def fmt() -> CommitFormatter:
    return CommitFormatter()


# ------------------------------------------------------------------
# Basic formatting
# ------------------------------------------------------------------

class TestBasicFormat:
    def test_basic_format_with_title_and_files(self, fmt: CommitFormatter) -> None:
        msg = fmt.format(
            title="Fix selector specificity",
            changed_files=["Source/WebCore/css/CSSSelector.cpp"],
        )
        assert msg.startswith("[")
        assert "Fix selector specificity" in msg
        assert "* Source/WebCore/css/CSSSelector.cpp:" in msg

    def test_component_auto_detected(self, fmt: CommitFormatter) -> None:
        msg = fmt.format(
            title="Fix parser",
            changed_files=[
                "Source/JavaScriptCore/parser/Parser.cpp",
                "Source/JavaScriptCore/parser/Parser.h",
            ],
        )
        assert msg.startswith("[JavaScriptCore]")

    def test_most_common_component_wins(self, fmt: CommitFormatter) -> None:
        msg = fmt.format(
            title="Update",
            changed_files=[
                "Source/WebCore/css/A.cpp",
                "Source/WebCore/css/B.cpp",
                "Source/JavaScriptCore/jit/C.cpp",
            ],
        )
        assert msg.startswith("[WebCore]")


# ------------------------------------------------------------------
# Bug ID and reviewer
# ------------------------------------------------------------------

class TestBugAndReviewer:
    def test_bug_id_included(self, fmt: CommitFormatter) -> None:
        msg = fmt.format(
            title="Fix",
            changed_files=["Source/WebCore/css/X.cpp"],
            bug_id=12345,
        )
        assert "bugs.webkit.org/show_bug.cgi?id=12345" in msg

    def test_no_bug_id_when_none(self, fmt: CommitFormatter) -> None:
        msg = fmt.format(
            title="Fix",
            changed_files=["Source/WebCore/css/X.cpp"],
        )
        assert "Bug:" not in msg

    def test_reviewer_included(self, fmt: CommitFormatter) -> None:
        msg = fmt.format(
            title="Fix",
            changed_files=["Source/WebCore/css/X.cpp"],
            reviewer="Darin Adler",
        )
        assert "Reviewed by: Darin Adler." in msg

    def test_no_reviewer_when_none(self, fmt: CommitFormatter) -> None:
        msg = fmt.format(
            title="Fix",
            changed_files=["Source/WebCore/css/X.cpp"],
        )
        assert "Reviewed by" not in msg


# ------------------------------------------------------------------
# File list
# ------------------------------------------------------------------

class TestFileList:
    def test_files_sorted_source_first(self, fmt: CommitFormatter) -> None:
        msg = fmt.format(
            title="Fix",
            changed_files=[
                "LayoutTests/fast/css/test.html",
                "Source/WebCore/css/X.cpp",
            ],
        )
        lines = msg.splitlines()
        file_lines = [l for l in lines if l.startswith("* ")]
        assert "Source/" in file_lines[0]
        assert "LayoutTests/" in file_lines[1]

    def test_new_files_marked_added(self, fmt: CommitFormatter) -> None:
        msg = fmt.format(
            title="Add test",
            changed_files=["LayoutTests/fast/css/new-test.html"],
            new_files={"LayoutTests/fast/css/new-test.html"},
        )
        assert "Added." in msg

    def test_deleted_files_marked_removed(self, fmt: CommitFormatter) -> None:
        msg = fmt.format(
            title="Remove old",
            changed_files=["Source/WebCore/css/Old.cpp"],
            deleted_files={"Source/WebCore/css/Old.cpp"},
        )
        assert "Removed." in msg

    def test_long_file_lists_truncated(self, fmt: CommitFormatter) -> None:
        files = [f"Source/WebCore/css/File{i}.cpp" for i in range(20)]
        msg = fmt.format(title="Big change", changed_files=files)
        assert "... and 5 more files" in msg


# ------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------

class TestValidation:
    def test_valid_message_no_issues(self, fmt: CommitFormatter) -> None:
        msg = fmt.format(
            title="Fix bug",
            changed_files=["Source/WebCore/css/X.cpp"],
            bug_id=123,
        )
        issues = CommitFormatter.validate(msg)
        assert len(issues) == 0

    def test_missing_component_prefix(self) -> None:
        issues = CommitFormatter.validate(
            "Fix bug\n\n* Source/WebCore/css/X.cpp:"
        )
        assert any("Component" in i for i in issues)

    def test_missing_file_list(self) -> None:
        issues = CommitFormatter.validate("[WebCore] Fix bug\n\nSome text.")
        assert any("file list" in i.lower() for i in issues)

    def test_long_line_detected(self) -> None:
        long_title = "[WebCore] " + "x" * 70
        msg = f"{long_title}\n\n* Source/WebCore/css/X.cpp:"
        issues = CommitFormatter.validate(msg)
        assert any("72" in i for i in issues)

    def test_bad_bug_url_detected(self) -> None:
        msg = "[WebCore] Fix\n\nBug: https://example.com/123\n\n* Source/WebCore/css/X.cpp:"
        issues = CommitFormatter.validate(msg)
        assert any("Bug URL" in i for i in issues)
