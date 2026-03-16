"""Tests for RiskScorer."""

import pytest

from wk_toolkit.core.risk_scorer import RiskScorer, RiskResult


@pytest.fixture
def scorer() -> RiskScorer:
    return RiskScorer()


# ------------------------------------------------------------------
# Helpers to build common inputs
# ------------------------------------------------------------------

def _low_risk_kwargs() -> dict:
    """Single component, small diff, good coverage."""
    return dict(
        components=["WebCore/CSS"],
        diff_stats={"Source/WebCore/css/CSSParser.cpp": (10, 5)},
        file_hotness={"Source/WebCore/css/CSSParser.cpp": 3},
        platform_specific_files=[],
        test_coverage_ratio=1.0,
        wpt_coverage_score=1.0,
        codeowner_count=1,
    )


def _high_risk_kwargs() -> dict:
    """4 components, large diff, low coverage."""
    return dict(
        components=["WebCore/CSS", "WebCore/DOM", "JavaScriptCore", "WTF"],
        diff_stats={
            "a.cpp": (400, 200),
            "b.cpp": (300, 150),
            "c.cpp": (100, 50),
        },
        file_hotness={"a.cpp": 25, "b.cpp": 22, "c.cpp": 18},
        platform_specific_files=["a.cpp", "b.cpp"],
        test_coverage_ratio=0.1,
        wpt_coverage_score=0.0,
        codeowner_count=5,
    )


# ------------------------------------------------------------------
# Overall score & level
# ------------------------------------------------------------------

class TestOverallScore:
    def test_low_risk_scenario(self, scorer: RiskScorer) -> None:
        result = scorer.score(**_low_risk_kwargs())
        assert result.level == "LOW"
        assert result.total_score <= 25

    def test_high_risk_scenario(self, scorer: RiskScorer) -> None:
        result = scorer.score(**_high_risk_kwargs())
        assert result.level in ("HIGH", "CRITICAL")
        assert result.total_score >= 51

    def test_score_never_exceeds_100(self, scorer: RiskScorer) -> None:
        kwargs = _high_risk_kwargs()
        # Push every factor to max.
        kwargs["diff_stats"] = {f"f{i}.cpp": (500, 500) for i in range(20)}
        kwargs["file_hotness"] = {f"f{i}.cpp": 100 for i in range(20)}
        kwargs["platform_specific_files"] = [f"f{i}.cpp" for i in range(20)]
        kwargs["test_coverage_ratio"] = 0.0
        kwargs["wpt_coverage_score"] = 0.0
        kwargs["codeowner_count"] = 10
        result = scorer.score(**kwargs)
        assert result.total_score <= 100

    def test_score_never_below_0(self, scorer: RiskScorer) -> None:
        result = scorer.score(**_low_risk_kwargs())
        assert result.total_score >= 0


# ------------------------------------------------------------------
# Level thresholds
# ------------------------------------------------------------------

class TestLevelThresholds:
    def test_low_threshold(self, scorer: RiskScorer) -> None:
        result = scorer.score(**_low_risk_kwargs())
        assert result.level == "LOW"

    def test_moderate_threshold(self, scorer: RiskScorer) -> None:
        kwargs = _low_risk_kwargs()
        kwargs["components"] = ["WebCore/CSS", "WebCore/DOM"]
        kwargs["diff_stats"] = {"a.cpp": (100, 80)}
        kwargs["file_hotness"] = {"a.cpp": 12}
        kwargs["test_coverage_ratio"] = 0.5
        kwargs["wpt_coverage_score"] = 0.5
        kwargs["codeowner_count"] = 2
        result = scorer.score(**kwargs)
        assert result.level in ("MODERATE", "HIGH")
        assert result.total_score >= 26

    def test_critical_threshold(self, scorer: RiskScorer) -> None:
        kwargs = _high_risk_kwargs()
        kwargs["components"] = ["A", "B", "C", "D", "E"]
        kwargs["codeowner_count"] = 6
        result = scorer.score(**kwargs)
        assert result.total_score >= 51  # at least HIGH


# ------------------------------------------------------------------
# Individual factor effects
# ------------------------------------------------------------------

class TestIndividualFactors:
    def test_hot_files_increase_score(self, scorer: RiskScorer) -> None:
        low = _low_risk_kwargs()
        hot = dict(low)
        hot["file_hotness"] = {"Source/WebCore/css/CSSParser.cpp": 30}
        r_low = scorer.score(**low)
        r_hot = scorer.score(**hot)
        assert r_hot.total_score > r_low.total_score

    def test_platform_specific_increases_score(self, scorer: RiskScorer) -> None:
        base = _low_risk_kwargs()
        plat = dict(base)
        plat["platform_specific_files"] = ["Source/WebCore/css/CSSParser.cpp"]
        r_base = scorer.score(**base)
        r_plat = scorer.score(**plat)
        assert r_plat.total_score >= r_base.total_score

    def test_good_test_coverage_decreases_score(self, scorer: RiskScorer) -> None:
        bad = _low_risk_kwargs()
        bad["test_coverage_ratio"] = 0.0
        good = _low_risk_kwargs()
        good["test_coverage_ratio"] = 1.0
        r_bad = scorer.score(**bad)
        r_good = scorer.score(**good)
        assert r_good.total_score < r_bad.total_score

    def test_good_wpt_coverage_decreases_score(self, scorer: RiskScorer) -> None:
        no_wpt = _low_risk_kwargs()
        no_wpt["wpt_coverage_score"] = 0.0
        full_wpt = _low_risk_kwargs()
        full_wpt["wpt_coverage_score"] = 1.0
        r_no = scorer.score(**no_wpt)
        r_full = scorer.score(**full_wpt)
        assert r_full.total_score < r_no.total_score

    def test_missing_wpt_increases_score(self, scorer: RiskScorer) -> None:
        base = _low_risk_kwargs()
        base["wpt_coverage_score"] = 1.0
        missing = dict(base)
        missing["wpt_coverage_score"] = 0.0
        r_base = scorer.score(**base)
        r_miss = scorer.score(**missing)
        assert r_miss.total_score > r_base.total_score


# ------------------------------------------------------------------
# Recommendations
# ------------------------------------------------------------------

class TestRecommendations:
    def test_cross_component_recommendation(self, scorer: RiskScorer) -> None:
        kwargs = _high_risk_kwargs()
        result = scorer.score(**kwargs)
        assert any("splitting" in r.lower() for r in result.recommendations)

    def test_low_test_coverage_recommendation(self, scorer: RiskScorer) -> None:
        kwargs = _low_risk_kwargs()
        kwargs["test_coverage_ratio"] = 0.1
        result = scorer.score(**kwargs)
        assert any("test coverage" in r.lower() for r in result.recommendations)

    def test_missing_wpt_recommendation(self, scorer: RiskScorer) -> None:
        kwargs = _low_risk_kwargs()
        kwargs["wpt_coverage_score"] = 0.0
        result = scorer.score(**kwargs)
        assert any("wpt" in r.lower() for r in result.recommendations)

    def test_large_diff_recommendation(self, scorer: RiskScorer) -> None:
        kwargs = _low_risk_kwargs()
        kwargs["diff_stats"] = {"a.cpp": (800, 400)}
        result = scorer.score(**kwargs)
        assert any("large diff" in r.lower() for r in result.recommendations)

    def test_platform_specific_recommendation(self, scorer: RiskScorer) -> None:
        kwargs = _low_risk_kwargs()
        kwargs["platform_specific_files"] = ["a.cpp"]
        result = scorer.score(**kwargs)
        assert any("platform" in r.lower() for r in result.recommendations)

    def test_no_recommendations_for_low_risk(self, scorer: RiskScorer) -> None:
        result = scorer.score(**_low_risk_kwargs())
        assert len(result.recommendations) == 0


# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------

class TestSummary:
    def test_summary_contains_score(self, scorer: RiskScorer) -> None:
        result = scorer.score(**_low_risk_kwargs())
        assert f"{result.total_score}/100" in result.summary

    def test_summary_contains_component_count(self, scorer: RiskScorer) -> None:
        result = scorer.score(**_low_risk_kwargs())
        assert "1 component" in result.summary

    def test_summary_good_coverage_note(self, scorer: RiskScorer) -> None:
        result = scorer.score(**_low_risk_kwargs())
        assert "good test coverage" in result.summary

    def test_summary_low_coverage_note(self, scorer: RiskScorer) -> None:
        kwargs = _low_risk_kwargs()
        kwargs["test_coverage_ratio"] = 0.1
        result = scorer.score(**kwargs)
        assert "low test coverage" in result.summary


# ------------------------------------------------------------------
# Factor math
# ------------------------------------------------------------------

class TestFactorMath:
    def test_contributions_sum_correctly(self, scorer: RiskScorer) -> None:
        result = scorer.score(**_low_risk_kwargs())
        expected = sum(f.contribution for f in result.factors)
        assert result.total_score == min(100, max(0, round(expected * 100)))

    def test_all_seven_factors_present(self, scorer: RiskScorer) -> None:
        result = scorer.score(**_low_risk_kwargs())
        assert len(result.factors) == 7
        names = {f.name for f in result.factors}
        assert names == {
            "cross_component",
            "diff_size",
            "file_hotness",
            "platform_specificity",
            "test_coverage",
            "wpt_coverage",
            "review_complexity",
        }

    def test_contribution_equals_norm_times_weight(self, scorer: RiskScorer) -> None:
        result = scorer.score(**_high_risk_kwargs())
        for f in result.factors:
            assert f.contribution == pytest.approx(
                f.normalized * f.weight, abs=1e-3
            )

    def test_weights_sum_to_1(self, scorer: RiskScorer) -> None:
        result = scorer.score(**_low_risk_kwargs())
        total_weight = sum(f.weight for f in result.factors)
        assert total_weight == pytest.approx(1.0)
