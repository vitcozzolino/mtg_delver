"""Console entry points for the standalone loader scripts."""

from pathlib import Path
from runpy import run_path


def _run(script_name: str) -> None:
    run_path(str(Path(__file__).with_name(script_name)), run_name="__main__")


def mtgdecks() -> None:
    """Run the MTGDecks loader through ``uv run load-mtgdecks``."""
    _run("mtgdecks.py")


def aetherhub() -> None:
    """Run the interactive AetherHub loader through ``uv run load-aetherhub``."""
    _run("aetherhub.py")
