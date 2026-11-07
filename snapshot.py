"""Build a committed static Pioneer snapshot for GitLab Pages or other static hosts."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from server import ROOT, fetch_pioneer_sources_live


DEFAULT_OUTPUT = ROOT / "ui" / "data" / "pioneer-snapshot.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=90, help="Recency window to include (1–90 days).")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Static JSON path to write.")
    arguments = parser.parse_args()
    days = max(1, min(arguments.days, 90))
    payload = fetch_pioneer_sources_live(days)
    payload["snapshot_generated_at"] = datetime.now(timezone.utc).isoformat()
    payload["snapshot_mode"] = True
    output = arguments.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    source_counts = payload.get("source_counts", {})
    total = len(payload["events"][0]["decks"])
    print(f"Static snapshot: wrote {total} tournament lists to {output.relative_to(ROOT)}")
    print(f"Sources: {source_counts}")


if __name__ == "__main__":
    main()
