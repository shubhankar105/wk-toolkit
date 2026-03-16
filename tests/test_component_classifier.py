"""Tests for ComponentClassifier."""

import pytest

from wk_toolkit.config import Components
from wk_toolkit.core.component_classifier import ComponentClassifier


@pytest.fixture
def clf() -> ComponentClassifier:
    return ComponentClassifier()


# ------------------------------------------------------------------
# JSC paths
# ------------------------------------------------------------------

class TestJSCClassification:
    def test_jsc_root(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/JavaScriptCore/CMakeLists.txt") == Components.JSC

    def test_jsc_dfg(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/JavaScriptCore/dfg/DFGGraph.cpp") == Components.JSC_DFG

    def test_jsc_wasm(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/JavaScriptCore/wasm/WasmModule.h") == Components.JSC_WASM

    def test_jsc_ftl(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/JavaScriptCore/ftl/FTLLowerDFGToB3.cpp") == Components.JSC_FTL

    def test_jsc_b3(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/JavaScriptCore/b3/B3Value.cpp") == Components.JSC_B3

    def test_jsc_parser(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/JavaScriptCore/parser/Parser.cpp") == Components.JSC_PARSER

    def test_jsc_runtime(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/JavaScriptCore/runtime/JSObject.h") == Components.JSC_RUNTIME

    def test_jsc_bytecode(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/JavaScriptCore/bytecode/Opcode.h") == Components.JSC_BYTECODE

    def test_jsc_heap(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/JavaScriptCore/heap/Heap.cpp") == Components.JSC_HEAP

    def test_jsc_jit(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/JavaScriptCore/jit/JIT.cpp") == Components.JSC_JIT

    def test_jsc_llint(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/JavaScriptCore/llint/LowLevelInterpreter.asm") == Components.JSC_LLINT


# ------------------------------------------------------------------
# WebCore paths
# ------------------------------------------------------------------

class TestWebCoreClassification:
    def test_webcore_root(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/WebCore.xcodeproj/project.pbxproj") == Components.WEBCORE

    def test_webcore_css(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/css/CSSParser.cpp") == Components.WEBCORE_CSS

    def test_webcore_dom(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/dom/Element.cpp") == Components.WEBCORE_DOM

    def test_webcore_html(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/html/HTMLElement.h") == Components.WEBCORE_HTML

    def test_webcore_layout(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/layout/LayoutBox.cpp") == Components.WEBCORE_LAYOUT

    def test_webcore_rendering(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/rendering/RenderBlock.cpp") == Components.WEBCORE_RENDERING

    def test_webcore_network(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/platform/network/ResourceHandle.cpp") == Components.WEBCORE_NETWORK

    def test_webcore_graphics(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/platform/graphics/GraphicsContext.cpp") == Components.WEBCORE_GRAPHICS

    def test_webcore_svg(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/svg/SVGElement.h") == Components.WEBCORE_SVG

    def test_webcore_accessibility(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/accessibility/AXObject.cpp") == Components.WEBCORE_ACCESSIBILITY

    def test_webcore_bindings(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/bindings/js/JSDOMBinding.cpp") == Components.WEBCORE_BINDINGS

    def test_webcore_page(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/page/Page.cpp") == Components.WEBCORE_PAGE

    def test_webcore_editing(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/editing/Editor.cpp") == Components.WEBCORE_EDITING

    def test_webcore_webgpu_module(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/Modules/webgpu/GPUDevice.cpp") == Components.WEBCORE_WEBGPU

    def test_webcore_fetch_module(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/Modules/fetch/FetchRequest.cpp") == Components.WEBCORE_FETCH

    def test_webcore_indexeddb_module(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/Modules/indexeddb/IDBDatabase.cpp") == Components.WEBCORE_INDEXEDDB

    def test_webcore_workers(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/workers/Worker.cpp") == Components.WEBCORE_WORKERS


# ------------------------------------------------------------------
# Platform-specific WebCore
# ------------------------------------------------------------------

class TestPlatformSpecificClassification:
    def test_platform_cocoa(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/platform/cocoa/NetworkLoader.mm") == Components.WEBCORE_PLATFORM_COCOA

    def test_platform_glib(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/platform/glib/EventLoop.cpp") == Components.WEBCORE_PLATFORM_GLIB

    def test_platform_win(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebCore/platform/win/ClipboardWin.cpp") == Components.WEBCORE_PLATFORM_WIN


# ------------------------------------------------------------------
# WebKit process paths
# ------------------------------------------------------------------

class TestWebKitProcessClassification:
    def test_uiprocess(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebKit/UIProcess/WebPageProxy.cpp") == Components.WEBKIT_UIPROCESS

    def test_webprocess(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebKit/WebProcess/WebPage.cpp") == Components.WEBKIT_WEBPROCESS

    def test_networkprocess(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebKit/NetworkProcess/NetworkLoad.cpp") == Components.WEBKIT_NETWORKPROCESS

    def test_gpuprocess(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebKit/GPUProcess/GPUConnectionToWebProcess.cpp") == Components.WEBKIT_GPUPROCESS

    def test_webkit_root(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebKit/Shared/SharedMemory.cpp") == Components.WEBKIT


# ------------------------------------------------------------------
# Tools
# ------------------------------------------------------------------

class TestToolsClassification:
    def test_tools_scripts(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Tools/Scripts/run-webkit-tests") == Components.TOOLS_SCRIPTS

    def test_tools_cisupport(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Tools/CISupport/ews-build/steps.py") == Components.TOOLS_CISUPPORT

    def test_tools_testwebkitapi(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Tools/TestWebKitAPI/Tests/WebCore/FloatRect.cpp") == Components.TOOLS_TESTWEBKITAPI

    def test_tools_buildbot(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Tools/buildbot/config.json") == Components.TOOLS_BUILDBOT


# ------------------------------------------------------------------
# Test directories
# ------------------------------------------------------------------

class TestLayoutTestsClassification:
    def test_layout_tests_css(self, clf: ComponentClassifier) -> None:
        assert clf.classify("LayoutTests/fast/css/color.html") == Components.LAYOUT_TESTS_CSS

    def test_layout_tests_dom(self, clf: ComponentClassifier) -> None:
        assert clf.classify("LayoutTests/fast/dom/element-api.html") == Components.LAYOUT_TESTS_DOM

    def test_layout_tests_html(self, clf: ComponentClassifier) -> None:
        assert clf.classify("LayoutTests/fast/html/form-submit.html") == Components.LAYOUT_TESTS_HTML

    def test_layout_tests_http(self, clf: ComponentClassifier) -> None:
        assert clf.classify("LayoutTests/http/tests/security/xss.html") == Components.LAYOUT_TESTS_HTTP

    def test_layout_tests_wpt(self, clf: ComponentClassifier) -> None:
        assert clf.classify(
            "LayoutTests/imported/w3c/web-platform-tests/css/css-grid/grid-template.html"
        ) == Components.LAYOUT_TESTS_WPT

    def test_layout_tests_generic(self, clf: ComponentClassifier) -> None:
        assert clf.classify("LayoutTests/animations/keyframes.html") == Components.LAYOUT_TESTS

    def test_jstests(self, clf: ComponentClassifier) -> None:
        assert clf.classify("JSTests/stress/array-push.js") == Components.JSTESTS

    def test_performance_tests(self, clf: ComponentClassifier) -> None:
        assert clf.classify("PerformanceTests/Speedometer/index.html") == Components.PERFORMANCE_TESTS


# ------------------------------------------------------------------
# Other source modules
# ------------------------------------------------------------------

class TestOtherModulesClassification:
    def test_wtf(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WTF/wtf/Vector.h") == Components.WTF

    def test_webgpu(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebGPU/WGSL/Parser.cpp") == Components.WEBGPU

    def test_webinspectorui(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebInspectorUI/UserInterface/Views/Main.js") == Components.WEBINSPECTORUI

    def test_webdriver(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/WebDriver/Session.cpp") == Components.WEBDRIVER

    def test_bmalloc(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source/bmalloc/bmalloc/Heap.cpp") == Components.BMALLOC

    def test_websites(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Websites/webkit.org/index.html") == Components.WEBSITES


# ------------------------------------------------------------------
# Edge cases
# ------------------------------------------------------------------

class TestEdgeCases:
    def test_unknown_path_returns_other(self, clf: ComponentClassifier) -> None:
        assert clf.classify("README.md") == Components.OTHER

    def test_completely_unknown_path(self, clf: ComponentClassifier) -> None:
        assert clf.classify("some/random/path.txt") == Components.OTHER

    def test_empty_string(self, clf: ComponentClassifier) -> None:
        assert clf.classify("") == Components.OTHER

    def test_longest_prefix_wins(self, clf: ComponentClassifier) -> None:
        """Deeper prefix should beat the shallower one."""
        # Source/JavaScriptCore/dfg/foo.cpp should be JSC_DFG, not JSC
        assert clf.classify("Source/JavaScriptCore/dfg/DFGNode.cpp") == Components.JSC_DFG

    def test_longest_prefix_webcore(self, clf: ComponentClassifier) -> None:
        """WebCore/css/ should beat WebCore/."""
        assert clf.classify("Source/WebCore/css/SomeFile.cpp") == Components.WEBCORE_CSS

    def test_longest_prefix_platform_network(self, clf: ComponentClassifier) -> None:
        """platform/network/ should beat WebCore/ root."""
        assert clf.classify("Source/WebCore/platform/network/curl/CurlHandle.cpp") == Components.WEBCORE_NETWORK

    def test_backslash_normalisation(self, clf: ComponentClassifier) -> None:
        assert clf.classify("Source\\JavaScriptCore\\dfg\\DFGGraph.cpp") == Components.JSC_DFG


# ------------------------------------------------------------------
# classify_many
# ------------------------------------------------------------------

class TestClassifyMany:
    def test_classify_many_groups_correctly(self, clf: ComponentClassifier) -> None:
        paths = [
            "Source/JavaScriptCore/dfg/DFGNode.cpp",
            "Source/JavaScriptCore/wasm/WasmModule.h",
            "Source/WebCore/css/CSSParser.cpp",
            "Source/WebCore/dom/Element.cpp",
            "README.md",
        ]
        result = clf.classify_many(paths)

        assert result[Components.JSC_DFG] == ["Source/JavaScriptCore/dfg/DFGNode.cpp"]
        assert result[Components.JSC_WASM] == ["Source/JavaScriptCore/wasm/WasmModule.h"]
        assert result[Components.WEBCORE_CSS] == ["Source/WebCore/css/CSSParser.cpp"]
        assert result[Components.WEBCORE_DOM] == ["Source/WebCore/dom/Element.cpp"]
        assert result[Components.OTHER] == ["README.md"]

    def test_classify_many_empty(self, clf: ComponentClassifier) -> None:
        assert clf.classify_many([]) == {}

    def test_classify_many_same_component(self, clf: ComponentClassifier) -> None:
        paths = [
            "Source/JavaScriptCore/dfg/DFGNode.cpp",
            "Source/JavaScriptCore/dfg/DFGGraph.h",
        ]
        result = clf.classify_many(paths)
        assert len(result[Components.JSC_DFG]) == 2


# ------------------------------------------------------------------
# is_platform_specific
# ------------------------------------------------------------------

class TestIsPlatformSpecific:
    def test_cocoa_is_platform_specific(self, clf: ComponentClassifier) -> None:
        assert clf.is_platform_specific("Source/WebCore/platform/cocoa/Foo.mm") is True

    def test_glib_is_platform_specific(self, clf: ComponentClassifier) -> None:
        assert clf.is_platform_specific("Source/WebCore/platform/glib/Bar.cpp") is True

    def test_win_is_platform_specific(self, clf: ComponentClassifier) -> None:
        assert clf.is_platform_specific("Source/WebCore/platform/win/Baz.cpp") is True

    def test_gtk_is_platform_specific(self, clf: ComponentClassifier) -> None:
        assert clf.is_platform_specific("Source/WebKit/UIProcess/gtk/WebPage.cpp") is True

    def test_wpe_is_platform_specific(self, clf: ComponentClassifier) -> None:
        assert clf.is_platform_specific("Source/WebKit/UIProcess/wpe/Display.cpp") is True

    def test_generic_is_not_platform_specific(self, clf: ComponentClassifier) -> None:
        assert clf.is_platform_specific("Source/WebCore/dom/Element.cpp") is False


# ------------------------------------------------------------------
# is_test_file
# ------------------------------------------------------------------

class TestIsTestFile:
    def test_layout_test(self, clf: ComponentClassifier) -> None:
        assert clf.is_test_file("LayoutTests/fast/css/color.html") is True

    def test_jstest(self, clf: ComponentClassifier) -> None:
        assert clf.is_test_file("JSTests/stress/array-push.js") is True

    def test_testwebkitapi(self, clf: ComponentClassifier) -> None:
        assert clf.is_test_file("Tools/TestWebKitAPI/Tests/WebCore/FloatRect.cpp") is True

    def test_performance_test(self, clf: ComponentClassifier) -> None:
        assert clf.is_test_file("PerformanceTests/Speedometer/index.html") is True

    def test_source_is_not_test(self, clf: ComponentClassifier) -> None:
        assert clf.is_test_file("Source/WebCore/dom/Element.cpp") is False

    def test_tools_scripts_is_not_test(self, clf: ComponentClassifier) -> None:
        assert clf.is_test_file("Tools/Scripts/run-webkit-tests") is False
