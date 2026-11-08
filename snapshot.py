"""Build a committed static Pioneer snapshot for GitLab Pages or other static hosts."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from server import ROOT, fetch_card_profiles, fetch_pioneer_sources_live


DEFAULT_OUTPUT = ROOT / "ui" / "data" / "pioneer-snapshot.json"


def snapshot_card_names(payload: dict) -> list[str]:
    """Return every card name represented by a published mainboard or sideboard."""
    names: set[str] = set()
    events = payload.get("events")
    if not isinstance(events, list):
        return []
    for event in events:
        if not isinstance(event, dict):
            continue
        for deck in event.get("decks", []):
            if not isinstance(deck, dict):
                continue
            for field in ("deck_text", "sideboard_text"):
                for line in str(deck.get(field) or "").splitlines():
                    match = re.match(r"^\s*\d+\s+(.+?)\s*$", line)
                    if match:
                        names.add(match.group(1).strip())
    return sorted(names)


def snapshot_profiles(payload: dict) -> tuple[dict[str, dict], list[str]]:
    """Embed public Scryfall card facts so static rendering needs no local API."""
    profiles: dict[str, dict] = {}
    warnings: list[str] = []
    names = snapshot_card_names(payload)
    for index in range(0, len(names), 75):
        try:
            profiles.update(fetch_card_profiles(names[index:index + 75]))
        except RuntimeError as error:
            warnings.append(f"Card profiles: {error}")
    return profiles, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=90, help="Recency window to include (1–90 days).")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Static JSON path to write.")
    arguments = parser.parse_args()
    days = max(1, min(arguments.days, 90))
    payload = fetch_pioneer_sources_live(days)
    profiles, profile_warnings = snapshot_profiles(payload)
    payload["card_profiles"] = profiles
    if profile_warnings:
        payload.setdefault("warnings", []).extend(profile_warnings)
    payload["snapshot_generated_at"] = datetime.now(timezone.utc).isoformat()
    payload["snapshot_mode"] = True
    output = arguments.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    source_counts = payload.get("source_counts", {})
    total = len(payload["events"][0]["decks"])
    print(f"Static snapshot: wrote {total} tournament lists to {output.relative_to(ROOT)}")
    print(f"Sources: {source_counts}")
    print(f"Card profiles: {len(profiles)}")


if __name__ == "__main__":
    main()
