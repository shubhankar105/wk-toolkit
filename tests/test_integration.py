"""Integration tests for the wk CLI (using Click's CliRunner)."""

import pytest
from click.testing import CliRunner

from wk_toolkit.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ------------------------------------------------------------------
# Help screens (exit 0)
# ------------------------------------------------------------------

class TestHelpScreens:
    def test_wk_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "wk-toolkit" in result.output

    def test_wk_version(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_analyze_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "analyze" in result.output.lower()

    def test_pr_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["pr", "--help"])
        assert result.exit_code == 0

    def test_test_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["test", "--help"])
        assert result.exit_code == 0

    def test_branch_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["branch", "--help"])
        assert result.exit_code == 0

    def test_bug_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["bug", "--help"])
        assert result.exit_code == 0

    def test_status_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0


# ------------------------------------------------------------------
# Demo mode — each command runs without error and produces output
# ------------------------------------------------------------------

class TestDemoMode:
    def test_analyze_full_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["analyze", "full", "--demo"])
        assert result.exit_code == 0
        assert "RISK ASSESSMENT" in result.output

    def test_analyze_risk_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["analyze", "risk", "--demo"])
        assert result.exit_code == 0
        assert "RISK ASSESSMENT" in result.output

    def test_analyze_reviewers_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["analyze", "reviewers", "--demo"])
        assert result.exit_code == 0
        assert "SUGGESTED REVIEWERS" in result.output

    def test_analyze_style_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["analyze", "style", "--demo"])
        assert result.exit_code == 0
        # May show "No style violations" or table
        assert len(result.output) > 0

    def test_analyze_wpt_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["analyze", "wpt", "--demo"])
        assert result.exit_code == 0
        assert "WPT COVERAGE" in result.output

    def test_pr_list_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["pr", "list", "--demo"])
        assert result.exit_code == 0
        assert "Pull Requests" in result.output

    def test_pr_status_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["pr", "status", "1234", "--demo"])
        assert result.exit_code == 0
        assert "1234" in result.output

    def test_branch_list_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["branch", "list", "--demo"])
        assert result.exit_code == 0
        assert "Local Branches" in result.output

    def test_branch_clean_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["branch", "clean", "--demo"])
        assert result.exit_code == 0

    def test_branch_rebase_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["branch", "rebase", "--demo"])
        assert result.exit_code == 0
        assert "Rebasing" in result.output

    def test_test_predict_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["test", "predict", "--demo"])
        assert result.exit_code == 0
        assert "PREDICTED TESTS" in result.output

    def test_test_wpt_check_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["test", "wpt-check", "--demo"])
        assert result.exit_code == 0
        assert "WPT COVERAGE" in result.output

    def test_test_run_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["test", "run", "--demo"])
        assert result.exit_code == 0

    def test_bug_link_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["bug", "link", "12345", "--demo"])
        assert result.exit_code == 0
        assert "12345" in result.output

    def test_bug_create_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["bug", "create", "--demo"])
        assert result.exit_code == 0

    def test_bug_sync_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["bug", "sync", "--demo"])
        assert result.exit_code == 0

    def test_status_demo(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["status", "--demo"])
        assert result.exit_code == 0
        assert "Status" in result.output


# ------------------------------------------------------------------
# Analyze full produces all report sections
# ------------------------------------------------------------------

class TestAnalyzeFullSections:
    def test_full_report_has_all_sections(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["analyze", "full", "--demo"])
        assert result.exit_code == 0
        assert "RISK ASSESSMENT" in result.output
        assert "COMPONENT IMPACT" in result.output
        assert "PREDICTED TESTS" in result.output
        assert "WPT COVERAGE" in result.output
        assert "SUGGESTED REVIEWERS" in result.output
        assert "COMMIT MESSAGE" in result.output
