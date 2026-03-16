"""Tests for BuildDetector."""

import pytest

from wk_toolkit.core.build_detector import BuildDetector, BuildWarning


@pytest.fixture
def detector() -> BuildDetector:
    return BuildDetector()


# ------------------------------------------------------------------
# Individual detection rules
# ------------------------------------------------------------------

class TestCMakeChanges:
    def test_cmake_triggers_info(self, detector: BuildDetector) -> None:
        w = detector.detect(["Source/WebCore/CMakeLists.txt"])
        cmake_w = [x for x in w if x.category == "cmake_changes"]
        assert len(cmake_w) == 1
        assert cmake_w[0].severity == "info"
        assert "CMake" in cmake_w[0].message


class TestNewSourceFiles:
    def test_new_cpp_triggers_warning(self, detector: BuildDetector) -> None:
        w = detector.detect(["Source/WebCore/css/NewFeature.cpp"])
        src_w = [x for x in w if x.category == "new_source_files"]
        assert len(src_w) == 1
        assert "Sources.txt" in src_w[0].message

    def test_new_mm_triggers_warning(self, detector: BuildDetector) -> None:
        w = detector.detect(["Source/WebCore/platform/cocoa/Foo.mm"])
        src_w = [x for x in w if x.category == "new_source_files"]
        assert len(src_w) == 1

    def test_test_html_does_not_trigger(self, detector: BuildDetector) -> None:
        w = detector.detect(["LayoutTests/fast/css/test.html"])
        src_w = [x for x in w if x.category == "new_source_files"]
        assert len(src_w) == 0

    def test_test_cpp_does_not_trigger(self, detector: BuildDetector) -> None:
        w = detector.detect(["Tools/TestWebKitAPI/Tests/WebCore/TestFoo.cpp"])
        src_w = [x for x in w if x.category == "new_source_files"]
        assert len(src_w) == 0


class TestXcodeChanges:
    def test_xcodeproj_triggers_warning(self, detector: BuildDetector) -> None:
        w = detector.detect(["Source/WebCore/WebCore.xcodeproj/project.pbxproj"])
        xc_w = [x for x in w if x.category == "xcodeproj_changes"]
        assert len(xc_w) == 1

    def test_xcworkspace_triggers_warning(self, detector: BuildDetector) -> None:
        w = detector.detect(["WebKit.xcworkspace/contents.xcworkspacedata"])
        xc_w = [x for x in w if x.category == "xcodeproj_changes"]
        assert len(xc_w) == 1


class TestFeatureFlags:
    def test_platform_enable_triggers(self, detector: BuildDetector) -> None:
        w = detector.detect(["Source/WTF/wtf/PlatformEnableCocoa.h"])
        ff = [x for x in w if x.category == "feature_flag_changes"]
        assert len(ff) == 1
        assert "Feature flags" in ff[0].message

    def test_feature_defines_triggers(self, detector: BuildDetector) -> None:
        w = detector.detect(["Source/WTF/wtf/FeatureDefines.h"])
        ff = [x for x in w if x.category == "feature_flag_changes"]
        assert len(ff) == 1


class TestPublicHeaders:
    def test_public_headers_dir(self, detector: BuildDetector) -> None:
        w = detector.detect(["Source/WebKit/PublicHeaders/WebKit/WKWebView.h"])
        ph = [x for x in w if x.category == "public_header_changes"]
        assert len(ph) == 1

    def test_api_dir(self, detector: BuildDetector) -> None:
        w = detector.detect(["Source/WebKit/UIProcess/API/Cocoa/WKWebView.h"])
        ph = [x for x in w if x.category == "public_header_changes"]
        assert len(ph) == 1


class TestSourcesTxt:
    def test_sources_txt_triggers_info(self, detector: BuildDetector) -> None:
        w = detector.detect(["Source/WebCore/Sources.txt"])
        st = [x for x in w if x.category == "sources_txt_changes"]
        assert len(st) == 1
        assert st[0].severity == "info"


class TestDerivedSources:
    def test_derived_sources_triggers(self, detector: BuildDetector) -> None:
        w = detector.detect(["Source/WebCore/DerivedSources.make"])
        ds = [x for x in w if x.category == "derived_sources"]
        assert len(ds) == 1

    def test_generator_script_triggers(self, detector: BuildDetector) -> None:
        w = detector.detect(["Source/WebCore/bindings/scripts/CodeGenerator.pm"])
        ds = [x for x in w if x.category == "derived_sources"]
        assert len(ds) == 1


# ------------------------------------------------------------------
# has_build_impact
# ------------------------------------------------------------------

class TestHasBuildImpact:
    def test_true_for_cmake(self, detector: BuildDetector) -> None:
        assert detector.has_build_impact(["Source/WebCore/CMakeLists.txt"]) is True

    def test_true_for_source_file(self, detector: BuildDetector) -> None:
        assert detector.has_build_impact(["Source/WebCore/css/New.cpp"]) is True

    def test_false_for_header_only(self, detector: BuildDetector) -> None:
        assert detector.has_build_impact(["Source/WebCore/css/CSSParser.h"]) is False

    def test_false_for_empty(self, detector: BuildDetector) -> None:
        assert detector.has_build_impact([]) is False

    def test_false_for_test_html(self, detector: BuildDetector) -> None:
        assert detector.has_build_impact(["LayoutTests/fast/css/test.html"]) is False


# ------------------------------------------------------------------
# Edge cases
# ------------------------------------------------------------------

class TestEdgeCases:
    def test_no_changes_no_warnings(self, detector: BuildDetector) -> None:
        assert detector.detect([]) == []

    def test_multiple_categories_at_once(self, detector: BuildDetector) -> None:
        files = [
            "Source/WebCore/CMakeLists.txt",
            "Source/WebCore/css/New.cpp",
            "Source/WebCore/WebCore.xcodeproj/project.pbxproj",
        ]
        w = detector.detect(files)
        cats = {x.category for x in w}
        assert "cmake_changes" in cats
        assert "new_source_files" in cats
        assert "xcodeproj_changes" in cats

    def test_affected_files_populated(self, detector: BuildDetector) -> None:
        w = detector.detect(["Source/WebCore/CMakeLists.txt"])
        cmake_w = [x for x in w if x.category == "cmake_changes"][0]
        assert "Source/WebCore/CMakeLists.txt" in cmake_w.affected_files
