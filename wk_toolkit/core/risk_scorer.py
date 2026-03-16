"""Compute a change risk score (0-100) with a detailed breakdown."""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class RiskFactor(BaseModel):
    """One dimension of the risk assessment."""

    name: str
    description: str
    raw_value: float
    normalized: float = Field(ge=0.0, le=1.0)
    weight: float
    contribution: float  # normalized * weight


class RiskResult(BaseModel):
    """Full risk assessment output."""

    total_score: int = Field(ge=0, le=100)
    level: str  # LOW | MODERATE | HIGH | CRITICAL
    factors: List[RiskFactor]
    summary: str
    recommendations: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _level_for(score: int) -> str:
    if score <= 25:
        return "LOW"
    if score <= 50:
        return "MODERATE"
    if score <= 75:
        return "HIGH"
    return "CRITICAL"


# ---------------------------------------------------------------------------
# RiskScorer
# ---------------------------------------------------------------------------

class RiskScorer:
    """Score the risk of a change-set on a 0-100 scale."""

    # ------------------------------------------------------------------
    # Normalisation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _norm_cross_component(n: int) -> float:
        if n <= 1:
            return 0.0
        if n == 2:
            return 0.3
        if n == 3:
            return 0.6
        return 1.0  # 4+

    @staticmethod
    def _norm_diff_size(total_lines: int) -> float:
        if total_lines < 50:
            return 0.1
        if total_lines < 200:
            return 0.3
        if total_lines < 500:
            return 0.6
        if total_lines < 1000:
            return 0.8
        return 1.0

    @staticmethod
    def _norm_file_hotness(avg_commits: float) -> float:
        if avg_commits > 20:
            return 1.0
        if avg_commits >= 10:
            return 0.6
        if avg_commits >= 5:
            return 0.3
        return 0.1

    @staticmethod
    def _norm_platform_specificity(
        platform_count: int, total_files: int
    ) -> float:
        if total_files == 0 or platform_count == 0:
            return 0.0
        ratio = platform_count / total_files
        if ratio > 0.5:
            return 0.8
        if ratio >= 0.2:
            return 0.5
        return 0.2

    @staticmethod
    def _norm_test_coverage(ratio: float) -> float:
        """Inverted – high coverage → low risk."""
        return _clamp(1.0 - ratio)

    @staticmethod
    def _norm_wpt_coverage(score: float) -> float:
        """Inverted – high WPT coverage → low risk."""
        return _clamp(1.0 - score)

    @staticmethod
    def _norm_review_complexity(owners: int) -> float:
        if owners <= 1:
            return 0.0
        if owners == 2:
            return 0.3
        if owners == 3:
            return 0.6
        return 1.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(
        self,
        components: Sequence[str],
        diff_stats: Dict[str, Tuple[int, int]],
        file_hotness: Dict[str, int],
        platform_specific_files: Sequence[str],
        test_coverage_ratio: float,
        wpt_coverage_score: float,
        codeowner_count: int,
    ) -> RiskResult:
        n_components = len(set(components))
        total_lines = sum(a + d for a, d in diff_stats.values())
        total_files = len(diff_stats) if diff_stats else 1

        avg_hotness = (
            sum(file_hotness.values()) / len(file_hotness)
            if file_hotness
            else 0.0
        )

        # --- build factors ---
        factors: List[RiskFactor] = []

        def _add(
            name: str, desc: str, raw: float, norm: float, weight: float
        ) -> None:
            factors.append(
                RiskFactor(
                    name=name,
                    description=desc,
                    raw_value=raw,
                    normalized=round(norm, 4),
                    weight=weight,
                    contribution=round(norm * weight, 4),
                )
            )

        _add(
            "cross_component",
            "Number of distinct components touched",
            float(n_components),
            self._norm_cross_component(n_components),
            0.20,
        )
        _add(
            "diff_size",
            "Total lines changed (additions + deletions)",
            float(total_lines),
            self._norm_diff_size(total_lines),
            0.15,
        )
        _add(
            "file_hotness",
            "Average recent commit frequency of changed files",
            avg_hotness,
            self._norm_file_hotness(avg_hotness),
            0.20,
        )
        _add(
            "platform_specificity",
            "Percentage of changed files that are platform-specific",
            float(len(platform_specific_files)),
            self._norm_platform_specificity(
                len(platform_specific_files), total_files
            ),
            0.15,
        )
        _add(
            "test_coverage",
            "Test coverage ratio for changed source files",
            test_coverage_ratio,
            self._norm_test_coverage(test_coverage_ratio),
            0.15,
        )
        _add(
            "wpt_coverage",
            "WPT coverage for spec-related changes",
            wpt_coverage_score,
            self._norm_wpt_coverage(wpt_coverage_score),
            0.10,
        )
        _add(
            "review_complexity",
            "Number of distinct code owners across changed files",
            float(codeowner_count),
            self._norm_review_complexity(codeowner_count),
            0.05,
        )

        raw = sum(f.contribution for f in factors)
        total_score = min(100, max(0, round(raw * 100)))
        level = _level_for(total_score)

        # --- summary ---
        summary = (
            f"{level} risk ({total_score}/100): "
            f"{n_components} component{'s' if n_components != 1 else ''}, "
            f"{total_lines} lines changed"
        )
        if test_coverage_ratio >= 0.75:
            summary += ", good test coverage"
        elif test_coverage_ratio < 0.25:
            summary += ", low test coverage"

        # --- recommendations ---
        recs: List[str] = []

        cc_factor = factors[0]  # cross_component
        if cc_factor.normalized > 0.5:
            recs.append(
                f"Consider splitting this PR — it touches {n_components} components"
            )

        ds_factor = factors[1]  # diff_size
        if ds_factor.normalized > 0.6:
            recs.append(
                f"Large diff ({total_lines} lines) — consider breaking into smaller PRs"
            )

        fh_factor = factors[2]  # file_hotness
        if fh_factor.normalized > 0.6:
            if file_hotness:
                hottest = max(file_hotness, key=file_hotness.get)  # type: ignore[arg-type]
                recs.append(
                    f"{hottest} is a hot file ({file_hotness[hottest]} commits/month) "
                    f"— extra review recommended"
                )

        ps_factor = factors[3]  # platform_specificity
        if ps_factor.normalized > 0.5:
            recs.append(
                "Platform-specific changes may not be validated on all CI bots"
            )

        tc_factor = factors[4]  # test_coverage
        if tc_factor.normalized > 0.5:
            pct = round(test_coverage_ratio * 100)
            recs.append(
                f"Test coverage is low ({pct}%) — consider adding tests"
            )

        wpt_factor = factors[5]  # wpt_coverage
        if wpt_factor.normalized > 0.5:
            recs.append(
                "No WPT coverage for spec-related changes — "
                "consider adding tests to web-platform-tests/"
            )

        return RiskResult(
            total_score=total_score,
            level=level,
            factors=factors,
            summary=summary,
            recommendations=recs,
        )
