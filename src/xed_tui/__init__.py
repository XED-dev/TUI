"""XED /TUI — Terminal browser and session manager for Claude Code.

Zero external dependencies. Requires Python 3.11+ and a Unix terminal.
"""

try:
    from importlib.metadata import version as _pkg_version
    __version__ = _pkg_version("xed-tui")
except Exception:
    # Development fallback: read VERSION from the script directly
    try:
        from xed_tui.xed_tui_v1 import VERSION as _V
        __version__ = _V.lstrip("v")
    except Exception:
        __version__ = "0.0.0"

VERSION = f"v{__version__}"
__all__ = ["VERSION", "__version__"]
