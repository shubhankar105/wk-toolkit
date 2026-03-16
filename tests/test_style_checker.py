"""Tests for StyleChecker."""

import pytest
from datetime import datetime

from wk_toolkit.core.style_checker import StyleChecker, StyleViolation


@pytest.fixture
def checker() -> StyleChecker:
    return StyleChecker()


# ------------------------------------------------------------------
# Individual rules
# ------------------------------------------------------------------

class TestTrailingWhitespace:
    def test_trailing_spaces_detected(self, checker: StyleChecker) -> None:
        lines = ["+int x = 0;   "]
        v = checker.check(lines, "foo.cpp")
        assert any(vi.rule == "trailing_whitespace" for vi in v)

    def test_trailing_tab_detected(self, checker: StyleChecker) -> None:
        lines = ["+int x = 0;\t"]
        v = checker.check(lines, "foo.cpp")
        assert any(vi.rule == "trailing_whitespace" for vi in v)


class TestTabIndentation:
    def test_tabs_detected_in_cpp(self, checker: StyleChecker) -> None:
        lines = ["+\tint x = 0;"]
        v = checker.check(lines, "foo.cpp")
        assert any(vi.rule == "tab_indentation" for vi in v)

    def test_tabs_detected_in_js(self, checker: StyleChecker) -> None:
        lines = ["+\tvar x = 0;"]
        v = checker.check(lines, "script.js")
        assert any(vi.rule == "tab_indentation" for vi in v)

    def test_tabs_not_flagged_in_py(self, checker: StyleChecker) -> None:
        lines = ["+\tx = 0"]
        v = checker.check(lines, "script.py")
        assert not any(vi.rule == "tab_indentation" for vi in v)


class TestLineLength:
    def test_warning_at_121_chars(self, checker: StyleChecker) -> None:
        long_line = "+" + "x" * 121
        v = checker.check([long_line], "foo.cpp")
        length_warnings = [vi for vi in v if vi.rule == "line_length"]
        assert len(length_warnings) == 1
        assert length_warnings[0].severity == "warning"

    def test_error_at_201_chars(self, checker: StyleChecker) -> None:
        long_line = "+" + "x" * 201
        v = checker.check([long_line], "foo.cpp")
        length_errors = [vi for vi in v if vi.rule == "line_length" and vi.severity == "error"]
        assert len(length_errors) == 1

    def test_120_chars_ok(self, checker: StyleChecker) -> None:
        ok_line = "+" + "x" * 120
        v = checker.check([ok_line], "foo.cpp")
        assert not any(vi.rule == "line_length" for vi in v)


class TestIncludeOrder:
    def test_wrong_first_include(self, checker: StyleChecker) -> None:
        lines = ['+#include "WebCore.h"']
        v = checker.check(lines, "foo.cpp")
        assert any(vi.rule == "include_order" for vi in v)

    def test_correct_first_include(self, checker: StyleChecker) -> None:
        lines = ['+#include "config.h"']
        v = checker.check(lines, "foo.cpp")
        assert not any(vi.rule == "include_order" for vi in v)

    def test_include_order_only_cpp(self, checker: StyleChecker) -> None:
        lines = ['+#include "WebCore.h"']
        v = checker.check(lines, "foo.h")
        assert not any(vi.rule == "include_order" for vi in v)


class TestPointerStyle:
    def test_space_before_pointer_detected(self, checker: StyleChecker) -> None:
        lines = ["+void foo(Type *ptr);"]
        v = checker.check(lines, "foo.cpp")
        assert any(vi.rule == "pointer_style" for vi in v)

    def test_space_before_reference_detected(self, checker: StyleChecker) -> None:
        lines = ["+void foo(Type &ref);"]
        v = checker.check(lines, "foo.cpp")
        assert any(vi.rule == "pointer_style" for vi in v)

    def test_correct_pointer_style_ok(self, checker: StyleChecker) -> None:
        lines = ["+void foo(Type* ptr);"]
        v = checker.check(lines, "foo.cpp")
        assert not any(vi.rule == "pointer_style" for vi in v)


class TestCopyrightHeader:
    def test_missing_year_in_copyright(self, checker: StyleChecker) -> None:
        lines = ["+// Copyright (C) 2020 Apple Inc."]
        v = checker.check(lines, "foo.cpp")
        current_year = str(datetime.now().year)
        if "2020" != current_year:
            assert any(vi.rule == "copyright_header" for vi in v)

    def test_current_year_copyright_ok(self, checker: StyleChecker) -> None:
        year = datetime.now().year
        lines = [f"+// Copyright (C) {year} Apple Inc."]
        v = checker.check(lines, "foo.cpp")
        assert not any(vi.rule == "copyright_header" for vi in v)


class TestNoInlineNamespaces:
    def test_using_namespace_in_header(self, checker: StyleChecker) -> None:
        lines = ["+using namespace WebCore;"]
        v = checker.check(lines, "foo.h")
        assert any(vi.rule == "no_inline_namespaces" for vi in v)

    def test_using_namespace_ok_in_cpp(self, checker: StyleChecker) -> None:
        lines = ["+using namespace WebCore;"]
        v = checker.check(lines, "foo.cpp")
        assert not any(vi.rule == "no_inline_namespaces" for vi in v)


# ------------------------------------------------------------------
# Only diff "+" lines
# ------------------------------------------------------------------

class TestDiffParsing:
    def test_only_plus_lines_checked(self, checker: StyleChecker) -> None:
        lines = [
            " int clean = 0;   ",       # context — not checked
            "-int old = 0;   ",          # removed — not checked
            "+int added = 0;   ",        # added — SHOULD be checked
        ]
        v = checker.check(lines, "foo.cpp")
        assert len(v) == 1
        assert v[0].rule == "trailing_whitespace"

    def test_no_violations_on_clean_code(self, checker: StyleChecker) -> None:
        lines = [
            '+#include "config.h"',
            "+",
            "+void foo(Type* ptr)",
            "+{",
            "+    return;",
            "+}",
        ]
        v = checker.check(lines, "foo.cpp")
        assert len(v) == 0


# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------

class TestSummary:
    def test_summary_counts(self, checker: StyleChecker) -> None:
        violations = [
            StyleViolation(line_number=1, rule="trailing_whitespace", message="x", severity="error"),
            StyleViolation(line_number=2, rule="tab_indentation", message="x", severity="error"),
            StyleViolation(line_number=3, rule="line_length", message="x", severity="warning"),
        ]
        s = StyleChecker.summary(violations)
        assert s["error_count"] == 2
        assert s["warning_count"] == 1
        assert s["rules_triggered"] == {"trailing_whitespace", "tab_indentation", "line_length"}

    def test_empty_violations_summary(self, checker: StyleChecker) -> None:
        s = StyleChecker.summary([])
        assert s["error_count"] == 0
        assert s["warning_count"] == 0
        assert s["rules_triggered"] == set()
