"""Development runner that restarts Delver when project source changes."""

from __future__ import annotations

from pathlib import Path

from watchfiles import DefaultFilter, run_process

import server


ROOT = Path(__file__).parent
WATCHED_SUFFIXES = {".py", ".js", ".css", ".html", ".toml"}


class DelverWatchFilter(DefaultFilter):
    """Watch source only; caches, deck archives, and the venv must not loop."""

    ignore_dirs = (*DefaultFilter.ignore_dirs, ".git", ".venv", "__pycache__", "output")

    def __call__(self, change, path: str) -> bool:
        return Path(path).suffix in WATCHED_SUFFIXES and super().__call__(change, path)


def main() -> None:
    print("Watching Delver source for changes — http://127.0.0.1:8080")
    run_process(str(ROOT), target=server.main, watch_filter=DelverWatchFilter())


if __name__ == "__main__":
    main()
