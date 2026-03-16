"""Configuration and WebKit component constants."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Application configuration."""

    github_token: Optional[str] = None
    github_repo: str = "WebKit/WebKit"
    bugzilla_url: str = "https://bugs.webkit.org"
    buildbot_url: str = "https://build.webkit.org"
    ews_url: str = "https://ews-build.webkit.org"
    data_dir: Path = field(default_factory=lambda: Path.home() / ".wk-toolkit")


# ---------------------------------------------------------------------------
# WebKit component constants
# ---------------------------------------------------------------------------

class Components:
    """WebKit component name constants."""

    # JavaScriptCore
    JSC = "JavaScriptCore"
    JSC_DFG = "JavaScriptCore/DFG"
    JSC_FTL = "JavaScriptCore/FTL"
    JSC_B3 = "JavaScriptCore/B3"
    JSC_WASM = "JavaScriptCore/Wasm"
    JSC_PARSER = "JavaScriptCore/Parser"
    JSC_RUNTIME = "JavaScriptCore/Runtime"
    JSC_BYTECODE = "JavaScriptCore/Bytecode"
    JSC_HEAP = "JavaScriptCore/Heap"
    JSC_JIT = "JavaScriptCore/JIT"
    JSC_LLINT = "JavaScriptCore/LLInt"

    # WebCore
    WEBCORE = "WebCore"
    WEBCORE_CSS = "WebCore/CSS"
    WEBCORE_DOM = "WebCore/DOM"
    WEBCORE_HTML = "WebCore/HTML"
    WEBCORE_LAYOUT = "WebCore/Layout"
    WEBCORE_RENDERING = "WebCore/Rendering"
    WEBCORE_NETWORK = "WebCore/Network"
    WEBCORE_GRAPHICS = "WebCore/Graphics"
    WEBCORE_SVG = "WebCore/SVG"
    WEBCORE_ACCESSIBILITY = "WebCore/Accessibility"
    WEBCORE_BINDINGS = "WebCore/Bindings"
    WEBCORE_PAGE = "WebCore/Page"
    WEBCORE_EDITING = "WebCore/Editing"
    WEBCORE_WEBGPU = "WebCore/WebGPU"
    WEBCORE_FETCH = "WebCore/Fetch"
    WEBCORE_INDEXEDDB = "WebCore/IndexedDB"
    WEBCORE_WORKERS = "WebCore/Workers"

    # WebCore platform-specific
    WEBCORE_PLATFORM_COCOA = "WebCore/Platform/Cocoa"
    WEBCORE_PLATFORM_GLIB = "WebCore/Platform/GLib"
    WEBCORE_PLATFORM_WIN = "WebCore/Platform/Win"

    # WebKit (multi-process)
    WEBKIT = "WebKit"
    WEBKIT_UIPROCESS = "WebKit/UIProcess"
    WEBKIT_WEBPROCESS = "WebKit/WebProcess"
    WEBKIT_NETWORKPROCESS = "WebKit/NetworkProcess"
    WEBKIT_GPUPROCESS = "WebKit/GPUProcess"

    # Other source modules
    WTF = "WTF"
    WEBGPU = "WebGPU"
    WEBINSPECTORUI = "WebInspectorUI"
    WEBDRIVER = "WebDriver"
    BMALLOC = "bmalloc"

    # Tools
    TOOLS_SCRIPTS = "Tools/Scripts"
    TOOLS_CISUPPORT = "Tools/CISupport"
    TOOLS_TESTWEBKITAPI = "Tools/TestWebKitAPI"
    TOOLS_BUILDBOT = "Tools/buildbot"

    # Tests
    LAYOUT_TESTS = "LayoutTests"
    LAYOUT_TESTS_CSS = "LayoutTests/CSS"
    LAYOUT_TESTS_DOM = "LayoutTests/DOM"
    LAYOUT_TESTS_HTML = "LayoutTests/HTML"
    LAYOUT_TESTS_HTTP = "LayoutTests/HTTP"
    LAYOUT_TESTS_WPT = "LayoutTests/WPT"
    JSTESTS = "JSTests"
    PERFORMANCE_TESTS = "PerformanceTests"

    # Other
    WEBSITES = "Websites"
    OTHER = "Other"
