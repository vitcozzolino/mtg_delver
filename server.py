"""Local-only server for Delver's live Pioneer sources.

Run with TOPDECK_API_KEY set in your shell. The key is never returned to the
browser and is only sent to TopDeck's API in the Authorization request.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).parent
TOPDECK_URL = "https://topdeck.gg/api/v2/tournaments"


def load_local_env() -> None:
    """Load the project's local .env without adding a third-party dependency."""
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for raw_line in env_file.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip("'\"")
        if key.strip() and value:
            os.environ.setdefault(key.strip(), value)


load_local_env()


def to_deck_text(deck: object) -> str:
    if isinstance(deck, str):
        return deck
    if not isinstance(deck, dict):
        return ""
    mainboard = deck.get("Mainboard") or deck.get("mainboard") or deck.get("main") or {}
    if not isinstance(mainboard, dict):
        return ""
    return "\n".join(f"{quantity} {name}" for name, quantity in mainboard.items())


def iso_date(unix_seconds: object) -> str:
    try:
        return datetime.fromtimestamp(float(unix_seconds), tz=timezone.utc).date().isoformat()
    except (TypeError, ValueError, OSError):
        return datetime.now(timezone.utc).date().isoformat()


def fetch_topdeck(days: int) -> dict:
    api_key = os.environ.get("TOPDECK_API_KEY")
    if not api_key:
        raise RuntimeError("TOPDECK_API_KEY is not set on the local server")

    payload = json.dumps({
        "game": "Magic: The Gathering",
        "format": "Pioneer",
        "last": days,
        "columns": ["name", "decklist", "wins", "draws", "losses"],
    }).encode()
    request = Request(
        TOPDECK_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            # Cloudflare rejects urllib's default `Python-urllib/x.y` identifier.
            "User-Agent": "mtg-delver/0.1 (+https://github.com/vitcozzolino/mtg_delver)",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            tournaments = json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"TopDeck returned HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach TopDeck: {error.reason}") from error

    events = []
    for tournament in tournaments:
        event_date = iso_date(tournament.get("startDate"))
        decks = []
        for standing in tournament.get("standings", []):
            deck_text = to_deck_text(standing.get("decklist") or standing.get("deckObj"))
            if not deck_text:
                continue
            wins, draws, losses = (standing.get(key, 0) or 0 for key in ("wins", "draws", "losses"))
            decks.append({
                "number": standing.get("id", ""),
                "date": event_date,
                "event": tournament.get("tournamentName", "TopDeck tournament"),
                "result": f"#{standing.get('standing', '—')} · {wins}-{losses}" + (f"-{draws}" if draws else ""),
                "player": standing.get("name", "Unknown player"),
                "archetype": standing.get("archetype") or standing.get("archetypeInput") or "Unknown",
                "source": "topdeck",
                "format": "pioneer",
                "deck_text": deck_text,
            })
        events.append({
            "id": tournament.get("TID", ""),
            "url": "https://topdeck.gg",
            "title": tournament.get("tournamentName", "TopDeck tournament"),
            "publish_date": event_date,
            "event_type": "tournament",
            "decks_total": len(decks),
            "decks_cached": len(decks),
            "decks": decks,
        })
    published_deck_count = sum(len(event["decks"]) for event in events)
    if not published_deck_count:
        raise RuntimeError(
            f"TopDeck returned {len(events)} Pioneer events but no publicly available decklists "
            f"in the selected {days}-day window"
        )
    return {
        "schema_version": "1",
        "kind": "topdeck_pioneer_decklists",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "format": "pioneer",
        "source": "topdeck-api",
        "days": days,
        "events": events,
    }


class DelverHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/pioneer":
            return super().do_GET()
        days = int(parse_qs(parsed.query).get("days", [30])[0])
        days = max(1, min(days, 90))
        try:
            payload = fetch_topdeck(days)
            self._send_json(200, payload)
        except (RuntimeError, ValueError) as error:
            self._send_json(502, {"error": str(error)})

    def _send_json(self, status: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    print("Delver is available at http://127.0.0.1:8080")
    ThreadingHTTPServer(("127.0.0.1", 8080), DelverHandler).serve_forever()


if __name__ == "__main__":
    main()
