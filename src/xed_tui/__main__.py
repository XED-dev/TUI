"""Entry point for `python -m xed_tui` and the `xed-tui` console script."""
import importlib.util
import sys
from pathlib import Path


def main() -> None:
    spec = importlib.util.spec_from_file_location(
        "xed_tui_v1",
        Path(__file__).parent / "xed-tui_v1.py",
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules["xed_tui_v1"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    mod.run()


if __name__ == "__main__":
    main()
