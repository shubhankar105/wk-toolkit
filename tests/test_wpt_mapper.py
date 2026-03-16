"""Tests for WPTMapper."""

import pytest

from wk_toolkit.core.wpt_mapper import WPTMapper, WPT_ROOT, WPTCoverage


@pytest.fixture
def mapper() -> WPTMapper:
    return WPTMapper()


# ------------------------------------------------------------------
# Individual source → WPT spec mappings
# ------------------------------------------------------------------

class TestWPTSpecMappings:
    def test_css_selector_maps_to_css_selectors(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/WebCore/css/CSSSelector.cpp"])
        assert len(cov.covered_specs) == 1
        assert cov.covered_specs[0].spec_dir == "css/selectors"

    def test_css_grid_maps_to_css_grid(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/WebCore/css/CSSGrid.cpp"])
        assert len(cov.covered_specs) == 1
        assert cov.covered_specs[0].spec_dir == "css/css-grid"

    def test_dom_mutation_observer_maps_to_dom_mutations(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/WebCore/dom/MutationObserver.cpp"])
        assert len(cov.covered_specs) == 1
        assert cov.covered_specs[0].spec_dir == "dom/mutations"

    def test_fetch_module_maps_to_fetch(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/WebCore/Modules/fetch/FetchRequest.cpp"])
        assert len(cov.covered_specs) == 1
        assert cov.covered_specs[0].spec_dir == "fetch"

    def test_webgpu_maps_to_webgpu(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/WebCore/Modules/webgpu/GPUDevice.cpp"])
        assert len(cov.covered_specs) == 1
        assert cov.covered_specs[0].spec_dir == "webgpu"

    def test_svg_maps_to_svg(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/WebCore/svg/SVGElement.cpp"])
        assert len(cov.covered_specs) == 1
        assert cov.covered_specs[0].spec_dir == "svg"

    def test_workers_maps_to_workers(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/WebCore/workers/Worker.cpp"])
        assert len(cov.covered_specs) == 1
        assert cov.covered_specs[0].spec_dir == "workers"

    def test_dom_element_maps_to_dom_nodes(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/WebCore/dom/Element.cpp"])
        assert cov.covered_specs[0].spec_dir == "dom/nodes"

    def test_shadow_root_maps_to_shadow_dom(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/WebCore/dom/ShadowRoot.cpp"])
        assert cov.covered_specs[0].spec_dir == "shadow-dom"

    def test_css_animation_maps_to_css_animations(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/WebCore/css/CSSAnimation.cpp"])
        assert cov.covered_specs[0].spec_dir == "css/css-animations"


# ------------------------------------------------------------------
# Multiple files
# ------------------------------------------------------------------

class TestMultipleFiles:
    def test_multiple_files_across_specs(self, mapper: WPTMapper) -> None:
        files = [
            "Source/WebCore/css/CSSSelector.cpp",
            "Source/WebCore/dom/MutationObserver.cpp",
            "Source/WebCore/Modules/fetch/FetchRequest.cpp",
        ]
        cov = mapper.map_files(files)
        spec_dirs = {s.spec_dir for s in cov.covered_specs}
        assert "css/selectors" in spec_dirs
        assert "dom/mutations" in spec_dirs
        assert "fetch" in spec_dirs
        assert cov.total_wpt_specs_found == 3

    def test_two_files_same_spec_merged(self, mapper: WPTMapper) -> None:
        files = [
            "Source/WebCore/dom/Element.cpp",
            "Source/WebCore/dom/Document.cpp",
        ]
        cov = mapper.map_files(files)
        # Both map to dom/nodes, so only one spec entry.
        assert cov.total_wpt_specs_found == 1
        assert len(cov.covered_specs[0].matched_source_files) == 2


# ------------------------------------------------------------------
# Non-WebCore files — should NOT be flagged as missing
# ------------------------------------------------------------------

class TestNonWebCoreFiles:
    def test_jsc_not_flagged(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/JavaScriptCore/dfg/DFGGraph.cpp"])
        assert len(cov.covered_specs) == 0
        assert len(cov.missing_coverage) == 0

    def test_tools_not_flagged(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Tools/Scripts/run-webkit-tests"])
        assert len(cov.covered_specs) == 0
        assert len(cov.missing_coverage) == 0


# ------------------------------------------------------------------
# Missing coverage detection
# ------------------------------------------------------------------

class TestMissingCoverage:
    def test_unmapped_css_file_flagged(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/WebCore/css/CSSUnknownThing.cpp"])
        # No mapping exists for CSSUnknownThing, but it's in css/
        # so it should appear in missing_coverage.
        assert len(cov.missing_coverage) == 1
        assert cov.missing_coverage[0].source_file == "Source/WebCore/css/CSSUnknownThing.cpp"

    def test_unmapped_dom_file_flagged(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/WebCore/dom/SomeNewFeature.cpp"])
        assert len(cov.missing_coverage) == 1

    def test_bindings_not_flagged_as_missing(self, mapper: WPTMapper) -> None:
        """bindings/ is not in the WPT-expected list, so not flagged."""
        cov = mapper.map_files(["Source/WebCore/bindings/js/JSDOMBinding.cpp"])
        assert len(cov.missing_coverage) == 0


# ------------------------------------------------------------------
# Coverage score
# ------------------------------------------------------------------

class TestCoverageScore:
    def test_all_covered_score_1(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files([
            "Source/WebCore/css/CSSSelector.cpp",
            "Source/WebCore/dom/MutationObserver.cpp",
        ])
        assert cov.coverage_score == 1.0

    def test_none_covered_score_0(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files([
            "Source/WebCore/css/CSSUnknownThing.cpp",
        ])
        assert cov.coverage_score == 0.0

    def test_partial_coverage_score(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files([
            "Source/WebCore/css/CSSSelector.cpp",       # covered
            "Source/WebCore/css/CSSUnknownThing.cpp",   # not covered
        ])
        assert cov.coverage_score == pytest.approx(0.5)

    def test_empty_files_score_0(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files([])
        assert cov.coverage_score == 0.0


# ------------------------------------------------------------------
# Recommendations
# ------------------------------------------------------------------

class TestRecommendations:
    def test_recommendations_for_missing(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/WebCore/css/CSSUnknownThing.cpp"])
        assert len(cov.recommendations) == 1
        assert "CSSUnknownThing" in cov.recommendations[0]

    def test_no_recommendations_when_all_covered(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/WebCore/css/CSSSelector.cpp"])
        assert len(cov.recommendations) == 0


# ------------------------------------------------------------------
# get_wpt_test_paths
# ------------------------------------------------------------------

class TestGetWPTTestPaths:
    def test_returns_flat_list(self, mapper: WPTMapper) -> None:
        paths = mapper.get_wpt_test_paths([
            "Source/WebCore/css/CSSSelector.cpp",
            "Source/WebCore/dom/MutationObserver.cpp",
        ])
        assert isinstance(paths, list)
        assert len(paths) == 2
        assert all(p.startswith(WPT_ROOT) for p in paths)

    def test_empty_for_non_webcore(self, mapper: WPTMapper) -> None:
        paths = mapper.get_wpt_test_paths(["Source/JavaScriptCore/jit/JIT.cpp"])
        assert paths == []

    def test_wpt_test_pattern_populated(self, mapper: WPTMapper) -> None:
        cov = mapper.map_files(["Source/WebCore/css/CSSGrid.cpp"])
        assert cov.covered_specs[0].wpt_test_pattern == "css/css-grid/*.html"
