#!/usr/bin/env python3
"""Normalize a Magic4Ever Pioneer text export into Delver's local source format."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output" / "magic4ever"
RAW_PATH = OUTPUT_DIR / "pioneer_decklists.txt"
JSON_PATH = OUTPUT_DIR / "decklists.json"
ZIP_PATH = OUTPUT_DIR / "decklists.zip"
SOURCE_URL = "https://www.magic4ever.com/decklists/pioneer.txt"
PIONEER_URL = "https://www.magic4ever.com/pioneer/"

EVENT_RE = re.compile(r"^EVENT\s*=\s*(?P<event>.+)$", re.IGNORECASE | re.MULTILINE)
PLAYER_RE = re.compile(r"^(?P<pilot>.+?)\s+\((?P<place>\d+)(?:st|nd|rd|th) Place\)\s*$", re.IGNORECASE)
CARD_RE = re.compile(r"^(?P<quantity>\d+)\s+(?P<name>.+?)\s*$")
TOTAL_RE = re.compile(r"^\d+\s+Cards?$", re.IGNORECASE)
SIDE_RE = re.compile(r"^Sideboard\s*\(\d+\)$", re.IGNORECASE)
CATEGORY_RE = re.compile(r"^[A-Za-z][A-Za-z /-]*\s*\(\d+\)$")


def request_export() -> str:
    """Download only Magic4Ever's published text export; never bypass a challenge."""
    response = requests.get(
        SOURCE_URL,
        headers={"User-Agent": "mtg-delver/0.1 (+https://github.com/vitcozzolino/mtg_delver)"},
        timeout=60,
    )
    response.raise_for_status()
    if "please wait while your request is being verified" in response.text.lower():
        raise RuntimeError("Magic4Ever served an access verification page; use the scraper's saved export instead.")
    return response.text


def event_date(event_label: str) -> tuple[str, str]:
    date_text, separator, name = event_label.partition(",")
    if separator:
        try:
            # The export uses day/month/year, while its rendered page may use US order.
            return datetime.strptime(date_text.strip(), "%d/%m/%Y").date().isoformat(), name.strip()
        except ValueError:
            pass
    return datetime.now(timezone.utc).date().isoformat(), event_label.strip()


def parse_cards(lines: list[str]) -> list[tuple[int, str]]:
    cards: list[tuple[int, str]] = []
    for raw_line in lines:
        line = html.unescape(raw_line.strip())
        if CATEGORY_RE.fullmatch(line):
            continue
        match = CARD_RE.fullmatch(line)
        if match:
            cards.append((int(match.group("quantity")), match.group("name")))
    return cards


def deck_text(cards: list[tuple[int, str]]) -> str:
    return "\n".join(f"{quantity} {name}" for quantity, name in cards if quantity > 0 and name)


def parse_deck(block: str) -> dict | None:
    lines = [html.unescape(line).strip() for line in block.splitlines()]
    if not lines:
        return None
    player_match = PLAYER_RE.fullmatch(lines[0])
    if not player_match:
        return None
    try:
        overview = lines.index("Overview") + 1
        mainboard_end = next(index for index in range(overview, len(lines)) if TOTAL_RE.fullmatch(lines[index]))
    except (ValueError, StopIteration):
        return None
    sideboard_start = next(
        (index for index in range(mainboard_end + 1, len(lines)) if SIDE_RE.fullmatch(lines[index])),
        None,
    )
    mainboard = parse_cards(lines[overview:mainboard_end])
    sideboard: list[tuple[int, str]] = []
    if sideboard_start is not None:
        for line in lines[sideboard_start + 1 :]:
            if not CARD_RE.fullmatch(line):
                break
            sideboard.extend(parse_cards([line]))
    if sum(quantity for quantity, _ in mainboard) < 40:
        return None
    return {
        "player": player_match.group("pilot"),
        "place": int(player_match.group("place")),
        "deck_text": deck_text(mainboard),
        "sideboard_text": deck_text(sideboard),
        "cards": {name.casefold() for _, name in mainboard},
    }


def classify(cards: set[str]) -> str:
    """Conservative inferred labels because the export has no deck-archetype field."""
    has = lambda name: name.casefold() in cards
    both = lambda first, second: has(first) and has(second)
    if has("Arclight Phoenix"):
        return "Izzet Phoenix"
    if both("Greasefang, Okiba Boss", "Parhelion II"):
        return "Abzan Greasefang"
    if has("Indomitable Creativity"):
        return "Temur Indomitable Creativity"
    if both("Eddymurk Crab", "Sunderflock"):
        return "Izzet Prowess"
    if both("Vivi Ornitier", "Proft's Eidetic Memory"):
        return "Izzet Midrange"
    if both("Nykthos, Shrine to Nyx", "Kiora, Behemoth Beckoner"):
        return "Nykthos Ramp"
    if both("Badgermole Cub", "Unholy Annex // Ritual Chamber"):
        return "Golgari Midrange"
    if both("Gleeful Demolition", "Venerated Loxodon"):
        return "Boros Convoke"
    if both("Monastery Swiftspear", "Heartfire Hero"):
        return "Mono-Red Prowess"
    if both("Thalia's Lieutenant", "Coppercoat Vanguard"):
        return "Mono-White Humans"
    if both("Teferi, Hero of Dominaria", "Supreme Verdict"):
        return "Azorius Control"
    return "Unknown"


def parse_export(raw_text: str) -> list[dict]:
    event_matches = list(EVENT_RE.finditer(raw_text))
    decks: list[dict] = []
    seen: set[str] = set()
    for event_index, event_match in enumerate(event_matches):
        event_end = event_matches[event_index + 1].start() if event_index + 1 < len(event_matches) else len(raw_text)
        event_block = raw_text[event_match.end() : event_end]
        date, event_name = event_date(event_match.group("event"))
        player_matches = list(re.finditer(r"^.+?\s+\(\d+(?:st|nd|rd|th) Place\)\s*$", event_block, re.IGNORECASE | re.MULTILINE))
        for player_index, player_match in enumerate(player_matches):
            deck_end = player_matches[player_index + 1].start() if player_index + 1 < len(player_matches) else len(event_block)
            parsed = parse_deck(event_block[player_match.start() : deck_end])
            if not parsed:
                continue
            archetype = classify(parsed.pop("cards"))
            fingerprint = hashlib.sha256(f"{date}|{event_name}|{parsed['player']}|{parsed['deck_text']}".encode()).hexdigest()[:16]
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            decks.append({
                "id": f"magic4ever-{fingerprint}",
                "date": date,
                "event": event_name,
                "result": f"{parsed.pop('place')}th Place",
                "player": parsed.pop("player"),
                "archetype": archetype,
                "source": "magic4ever-local",
                "format": "pioneer",
                "source_url": PIONEER_URL,
                **parsed,
            })
    return sorted(decks, key=lambda deck: (deck["date"], deck["event"], deck["player"]), reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Refresh the local raw export from Magic4Ever's published text URL.")
    parser.add_argument("--input", type=Path, default=RAW_PATH, help="Path to the scraper's raw Pioneer export.")
    arguments = parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if arguments.refresh:
        RAW_PATH.write_text(request_export(), encoding="utf-8")
        input_path = RAW_PATH
    else:
        input_path = arguments.input
    if not input_path.is_file():
        raise SystemExit(f"No Magic4Ever export at {input_path}. Put the scraper output there or run with --refresh.")

    decks = parse_export(input_path.read_text(encoding="utf-8", errors="replace"))
    if not decks:
        raise SystemExit("No valid Magic4Ever Pioneer decklists were found in the export.")
    payload = {
        "schema_version": "1",
        "kind": "magic4ever_pioneer_archive",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_url": PIONEER_URL,
        "decks": decks,
    }
    JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("decklists.json", json.dumps(payload, ensure_ascii=False, indent=2))
    archetypes = {deck["archetype"] for deck in decks}
    print(f"Magic4Ever: normalized {len(decks)} Pioneer decklists across {len(archetypes)} inferred archetypes.")
    print(f"Wrote {JSON_PATH.relative_to(PROJECT_ROOT)} and {ZIP_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
