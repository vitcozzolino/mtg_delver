"""Local-only server for Delver's live Pioneer sources.

Run with TOPDECK_API_KEY set in your shell. The key is never returned to the
browser and is only sent to TopDeck's API in the Authorization request.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from errno import EADDRINUSE
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html import unescape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).parent
TOPDECK_URL = "https://topdeck.gg/api/v2/tournaments"
VIDERE_DECKS_URL = "https://api.videreproject.com/decks"
SPICERACK_URL = "https://api.spicerack.gg/api/export-decklists/"
MTG_DECKLISTS_URL = "https://mtgdecklists.com"
MOXFIELD_API_URL = "https://api2.moxfield.com"
MAX_VIDERE_DECKS = 1_000
CACHE_DB = ROOT / "delver-cache.sqlite3"
SOURCE_CACHE_TTL_SECONDS = 30 * 60
ARCHETYPE_CACHE_TTL_SECONDS = 6 * 60 * 60
MAX_ARCHETYPE_DECKS = 20


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


def initialize_cache() -> None:
    """Create a small, local cache that survives server restarts."""
    with sqlite3.connect(CACHE_DB) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cached_payloads (
                cache_key TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                fetched_at REAL NOT NULL
            )
            """
        )


def read_cached_payload(cache_key: str) -> tuple[dict | None, float | None]:
    with sqlite3.connect(CACHE_DB, timeout=5) as connection:
        row = connection.execute(
            "SELECT payload, fetched_at FROM cached_payloads WHERE cache_key = ?", (cache_key,)
        ).fetchone()
    if not row:
        return None, None
    try:
        payload = json.loads(row[0])
    except (TypeError, json.JSONDecodeError):
        return None, None
    return (payload if isinstance(payload, dict) else None), float(row[1])


def write_cached_payload(cache_key: str, payload: dict) -> float:
    fetched_at = time.time()
    with sqlite3.connect(CACHE_DB, timeout=5) as connection:
        connection.execute(
            """
            INSERT INTO cached_payloads (cache_key, payload, fetched_at)
            VALUES (?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET payload = excluded.payload, fetched_at = excluded.fetched_at
            """,
            (cache_key, json.dumps(payload), fetched_at),
        )
    return fetched_at


def annotate_cache(payload: dict, status: str, fetched_at: float, detail: str | None = None) -> dict:
    """Return a copy so cache metadata never contaminates the stored payload."""
    response = json.loads(json.dumps(payload))
    response["cache"] = {
        "status": status,
        "fetched_at": datetime.fromtimestamp(fetched_at, tz=timezone.utc).isoformat(),
    }
    if detail:
        response["cache"]["detail"] = detail
    return response


def cached_fetch(cache_key: str, ttl_seconds: int, loader, *, force_refresh: bool = False) -> dict:
    """Read-through SQLite cache, with stale data as a safe source-outage fallback."""
    cached, fetched_at = read_cached_payload(cache_key)
    if cached is not None and fetched_at is not None and not force_refresh:
        if time.time() - fetched_at < ttl_seconds:
            return annotate_cache(cached, "hit", fetched_at)
    try:
        payload = loader()
    except RuntimeError as error:
        if cached is not None and fetched_at is not None:
            return annotate_cache(cached, "stale", fetched_at, f"Live refresh failed: {error}")
        raise
    fetched_at = write_cached_payload(cache_key, payload)
    return annotate_cache(payload, "refreshed", fetched_at)


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


def fetch_json(url: str, timeout: int = 20, headers: dict[str, str] | None = None) -> object:
    request_headers = {
        "Accept": "application/json",
        "User-Agent": "mtg-delver/0.1 (+https://github.com/vitcozzolino/mtg_delver)",
    }
    if headers:
        request_headers.update(headers)
    request = Request(url, headers=request_headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:200]
        raise RuntimeError(f"Source returned HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach source: {error.reason}") from error


def fetch_html(url: str, timeout: int = 20) -> str:
    request = Request(url, headers={
        "Accept": "text/html,application/xhtml+xml",
        "User-Agent": "mtg-delver/0.1 (+https://github.com/vitcozzolino/mtg_delver)",
    })
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except HTTPError as error:
        raise RuntimeError(f"Source returned HTTP {error.code}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach source: {error.reason}") from error


def html_text(value: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", value)).strip()


def archetype_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def fetch_mtgdecklists_archetype(
    archetype: str,
    days: int,
    limit: int = MAX_ARCHETYPE_DECKS,
    *,
    force_refresh: bool = False,
) -> dict:
    """Fetch a small, cached public sample for one requested Pioneer archetype.

    MTG Decklists permits crawling in robots.txt. This deliberately loads at
    most 20 recent pages and persists results locally for six hours.
    """
    limit = max(1, min(limit, MAX_ARCHETYPE_DECKS))
    cache_key = f"archetype:{archetype_slug(archetype)}:{days}:{limit}"
    return cached_fetch(
        cache_key,
        ARCHETYPE_CACHE_TTL_SECONDS,
        lambda: fetch_mtgdecklists_archetype_live(archetype, days, limit),
        force_refresh=force_refresh,
    )


def fetch_mtgdecklists_archetype_live(archetype: str, days: int, limit: int) -> dict:

    list_url = f"{MTG_DECKLISTS_URL}/archetypes/pioneer-{archetype_slug(archetype)}.html"
    listing = fetch_html(list_url)
    entries = []
    pattern = re.compile(
        r'<a class="recent-item" href="(?P<href>[^"]+)"[^>]*>.*?'
        r'<div class="meta muted">(?P<meta>.*?)</div>.*?'
        r'<div class="when">(?P<date>[^<]+)</div>\s*</a>',
        re.DOTALL,
    )
    cutoff = datetime.now(timezone.utc).date().fromordinal(datetime.now(timezone.utc).date().toordinal() - days)
    for match in pattern.finditer(listing):
        try:
            deck_date = datetime.fromisoformat(match.group("date").strip()).date()
        except ValueError:
            continue
        if deck_date < cutoff:
            continue
        parts = [part.strip() for part in html_text(match.group("meta")).split(" · ")]
        if len(parts) < 3:
            continue
        entries.append({
            "url": f"{MTG_DECKLISTS_URL}{match.group('href')}",
            "date": deck_date.isoformat(),
            "player": parts[0],
            "result": parts[1],
            "event": " · ".join(parts[2:]),
        })
        if len(entries) >= limit:
            break

    def load_deck(entry: dict) -> dict | None:
        page = fetch_html(entry["url"])
        main_match = re.search(
            r'<div class="section-title"[^>]*><h2>Main deck</h2></div>(?P<main>.*?)'
            r'<div class="section-title"[^>]*><h2>Sideboard</h2></div>',
            page,
            re.DOTALL,
        )
        if not main_match:
            return None
        cards = re.findall(
            r'<figcaption><span class="qty">(\d+)</span>(.*?)</figcaption>',
            main_match.group("main"),
            re.DOTALL,
        )
        deck_text = "\n".join(f"{quantity} {html_text(name)}" for quantity, name in cards)
        if not deck_text:
            return None
        return {
            **entry,
            "archetype": archetype,
            "source": "mtgdecklists",
            "format": "pioneer",
            "deck_text": deck_text,
        }

    decks: list[dict] = []
    # Keep this deliberately serial: the public source rate-limits bursts of
    # individual deck-page requests, and one archetype fetch is cacheable.
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = [executor.submit(load_deck, entry) for entry in entries]
        for future in as_completed(futures):
            try:
                deck = future.result()
            except RuntimeError:
                continue
            if deck:
                decks.append(deck)
    decks.sort(key=lambda deck: (deck["date"], deck["player"]), reverse=True)
    payload = {
        "schema_version": "1",
        "kind": "mtgdecklists_pioneer_archetype",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "format": "pioneer",
        "source": "mtgdecklists",
        "days": days,
        "events": [{
            "id": f"mtgdecklists-{archetype_slug(archetype)}",
            "url": list_url,
            "title": f"MTG Decklists · {archetype}",
            "publish_date": datetime.now(timezone.utc).date().isoformat(),
            "event_type": "archetype_sample",
            "decks_total": len(decks),
            "decks_cached": len(decks),
            "decks": decks,
        }],
    }
    return payload


def nonnegative_int_env(name: str, default: int) -> int:
    try:
        return max(0, int(os.environ.get(name, default)))
    except ValueError:
        return default


def integer_value(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def moxfield_headers() -> dict[str, str]:
    """Return optional Moxfield credentials without exposing them to the browser."""
    token = os.environ.get("MOXFIELD_AUTH_TOKEN", "").strip()
    user_agent = os.environ.get("MOXFIELD_USER_AGENT", "").strip()
    if not token and not user_agent:
        raise RuntimeError(
            "Moxfield is not configured. Set MOXFIELD_AUTH_TOKEN or a Moxfield-issued "
            "MOXFIELD_USER_AGENT in .env."
        )
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if user_agent:
        headers["User-Agent"] = user_agent
    return headers


def moxfield_mainboard(deck: object) -> str:
    if not isinstance(deck, dict):
        return ""
    boards = deck.get("boards")
    if not isinstance(boards, dict):
        return ""
    mainboard = boards.get("mainboard") or boards.get("main")
    if not isinstance(mainboard, dict):
        return ""
    cards = mainboard.get("cards")
    if not isinstance(cards, dict):
        return ""
    lines: list[str] = []
    for entry in cards.values():
        if not isinstance(entry, dict):
            continue
        card = entry.get("card")
        name = card.get("name") if isinstance(card, dict) else None
        quantity = entry.get("quantity")
        if isinstance(name, str) and isinstance(quantity, int) and quantity > 0:
            lines.append(f"{quantity} {name}")
    return "\n".join(lines)


def moxfield_date(value: object) -> str:
    if not isinstance(value, str):
        return datetime.now(timezone.utc).date().isoformat()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return datetime.now(timezone.utc).date().isoformat()


def fetch_moxfield_archetype(
    archetype: str,
    days: int,
    limit: int = MAX_ARCHETYPE_DECKS,
    *,
    force_refresh: bool = False,
) -> dict:
    """Fetch a filtered, separate community sample from Moxfield when configured."""
    limit = max(1, min(limit, MAX_ARCHETYPE_DECKS))
    min_views = nonnegative_int_env("MOXFIELD_MIN_VIEWS", 50)
    min_likes = nonnegative_int_env("MOXFIELD_MIN_LIKES", 2)
    cache_key = f"moxfield:{archetype_slug(archetype)}:{days}:{limit}:{min_views}:{min_likes}"
    return cached_fetch(
        cache_key,
        ARCHETYPE_CACHE_TTL_SECONDS,
        lambda: fetch_moxfield_archetype_live(archetype, days, limit, min_views, min_likes),
        force_refresh=force_refresh,
    )


def fetch_moxfield_archetype_live(
    archetype: str,
    days: int,
    limit: int,
    min_views: int,
    min_likes: int,
) -> dict:
    from urllib.parse import urlencode

    query = urlencode({
        "fmt": "pioneer",
        "deckName": archetype,
        "pageNumber": 1,
        "pageSize": 100,
        "sortType": "updated",
        "sortDirection": "descending",
        "showIllegal": "false",
    })
    search = fetch_json(f"{MOXFIELD_API_URL}/v2/decks/search?{query}", headers=moxfield_headers())
    if not isinstance(search, dict) or not isinstance(search.get("data"), list):
        raise RuntimeError("Moxfield returned an unexpected deck-search response")
    cutoff = datetime.now(timezone.utc).date().fromordinal(datetime.now(timezone.utc).date().toordinal() - days)
    candidates: list[dict] = []
    for summary in search["data"]:
        if not isinstance(summary, dict):
            continue
        if moxfield_date(summary.get("lastUpdatedAtUtc")) < cutoff.isoformat():
            continue
        if integer_value(summary.get("mainboardCount")) < 60:
            continue
        views = integer_value(summary.get("viewCount"))
        likes = integer_value(summary.get("likeCount"))
        if views < min_views and likes < min_likes:
            continue
        public_id = summary.get("publicId")
        if not isinstance(public_id, str) or not public_id:
            continue
        candidates.append(summary)
    candidates.sort(
        key=lambda deck: (
            integer_value(deck.get("likeCount")),
            integer_value(deck.get("viewCount")),
            str(deck.get("lastUpdatedAtUtc") or ""),
        ),
        reverse=True,
    )

    headers = moxfield_headers()
    decks: list[dict] = []
    for summary in candidates[:limit]:
        public_id = summary["publicId"]
        try:
            full_deck = fetch_json(f"{MOXFIELD_API_URL}/v3/decks/all/{public_id}", headers=headers)
        except RuntimeError:
            continue
        deck_text = moxfield_mainboard(full_deck)
        if not deck_text:
            continue
        author = summary.get("createdByUser")
        player = "Moxfield user"
        if isinstance(author, dict):
            player = author.get("displayName") or author.get("userName") or player
        likes = integer_value(summary.get("likeCount"))
        views = integer_value(summary.get("viewCount"))
        decks.append({
            "number": public_id,
            "date": moxfield_date(summary.get("lastUpdatedAtUtc")),
            "event": "Moxfield community list",
            "result": f"Community · {likes} likes · {views} views",
            "player": player,
            "archetype": archetype,
            "source": "moxfield",
            "format": "pioneer",
            "deck_text": deck_text,
            "source_url": summary.get("publicUrl") or f"https://www.moxfield.com/decks/{public_id}",
        })
    payload = {
        "schema_version": "1",
        "kind": "moxfield_pioneer_archetype",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "format": "pioneer",
        "source": "moxfield",
        "days": days,
        "filters": {"minimum_views": min_views, "minimum_likes": min_likes},
        "events": [{
            "id": f"moxfield-{archetype_slug(archetype)}",
            "url": f"https://www.moxfield.com/decks/public?fmt=pioneer&search={archetype_slug(archetype)}",
            "title": f"Moxfield community · {archetype}",
            "publish_date": datetime.now(timezone.utc).date().isoformat(),
            "event_type": "community_sample",
            "decks_total": len(decks),
            "decks_cached": len(decks),
            "decks": decks,
        }],
    }
    return payload


def videre_mainboard(lines: object) -> str:
    if not isinstance(lines, list):
        return ""
    cards: list[str] = []
    pattern = re.compile(r'^\(\d+,(?:"([^"]+)"|([^,]+)),(\d+)\)$')
    for line in lines:
        if not isinstance(line, str):
            continue
        match = pattern.match(line)
        if not match:
            continue
        name = (match.group(1) or match.group(2)).strip()
        cards.append(f"{match.group(3)} {name}")
    return "\n".join(cards)


def fetch_videre(days: int) -> list[dict]:
    """Fetch a bounded, paginated Pioneer MTGO sample from Videre's public API."""
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date.fromordinal(end_date.toordinal() - days)
    decks: list[dict] = []
    offset = 0
    limit = 200
    while len(decks) < MAX_VIDERE_DECKS:
        url = (
            f"{VIDERE_DECKS_URL}?format=pioneer&min_date={start_date.isoformat()}"
            f"&max_date={end_date.isoformat()}&limit={limit}&offset={offset}"
        )
        payload = fetch_json(url, timeout=25)
        if not isinstance(payload, dict):
            break
        rows = payload.get("data", [])
        if not isinstance(rows, list) or not rows:
            break
        for row in rows:
            if not isinstance(row, dict):
                continue
            deck_text = videre_mainboard(row.get("mainboard"))
            if not deck_text:
                continue
            event_date = str(row.get("date", ""))[:10]
            decks.append({
                "number": str(row.get("id", "")),
                "date": event_date,
                "event": row.get("event_name") or "Magic Online event",
                "result": row.get("event_type") or "Published MTGO list",
                "player": row.get("player") or "Unknown player",
                "archetype": row.get("archetype") or row.get("deck_name") or "Unknown",
                "source": "videre",
                "format": "pioneer",
                "deck_text": deck_text,
                "source_url": "https://www.videreproject.com/",
            })
            if len(decks) >= MAX_VIDERE_DECKS:
                break
        meta = payload.get("meta", {})
        if not isinstance(meta, dict) or not meta.get("has_more"):
            break
        next_offset = meta.get("next_offset")
        if not isinstance(next_offset, int) or next_offset <= offset:
            break
        offset = next_offset
    return decks


def infer_archetype(deck_text: str) -> str:
    """Only infer labels for distinctive shells; otherwise keep the list unclassified."""
    cards = deck_text.lower()
    if "arclight phoenix" in cards:
        return "Izzet Phoenix"
    if "nykthos, shrine to nyx" in cards and "kiora, behemoth beckoner" in cards:
        return "Mono-Green Devotion"
    if "greasefang, okiba boss" in cards and "parhelion ii" in cards:
        return "Greasefang"
    if "lotus field" in cards and "hidden strings" in cards:
        return "Lotus Field"
    return "Unknown"


def fetch_spicerack(days: int) -> list[dict]:
    """Fetch public Pioneer tournaments; a slow/unavailable response is non-fatal."""
    url = f"{SPICERACK_URL}?num_days={days}&event_format=PIONEER&decklist_as_text=true"
    payload = fetch_json(url, timeout=15)
    if not isinstance(payload, list):
        return []
    decks: list[dict] = []
    for tournament in payload:
        if not isinstance(tournament, dict):
            continue
        event_date = iso_date(tournament.get("startDate"))
        for standing, row in enumerate(tournament.get("standings", []), start=1):
            if not isinstance(row, dict):
                continue
            deck_text = row.get("decklist_text")
            if not isinstance(deck_text, str) or not deck_text.strip():
                continue
            wins = (row.get("winsSwiss", 0) or 0) + (row.get("winsBracket", 0) or 0)
            losses = (row.get("lossesSwiss", 0) or 0) + (row.get("lossesBracket", 0) or 0)
            decks.append({
                "number": f"{tournament.get('TID', '')}-{standing}",
                "date": event_date,
                "event": tournament.get("tournamentName") or "Spicerack tournament",
                "result": f"#{standing} · {wins}-{losses}",
                "player": row.get("name") or "Unknown player",
                "archetype": row.get("archetype") or infer_archetype(deck_text),
                "source": "spicerack",
                "format": "pioneer",
                "deck_text": deck_text,
                "source_url": tournament.get("bracketUrl") or "https://www.spicerack.gg/",
            })
    return decks


def deduplicate(decks: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for deck in decks:
        fingerprint = "\n".join(sorted(line.strip().lower() for line in deck["deck_text"].splitlines() if line.strip()))
        if not fingerprint or fingerprint in seen:
            continue
        seen.add(fingerprint)
        unique.append(deck)
    return unique


def fetch_pioneer_sources(days: int, *, force_refresh: bool = False) -> dict:
    """Merge evidence-grade MTGO and paper tournament lists without a single-source dependency."""
    return cached_fetch(
        f"pioneer:{days}",
        SOURCE_CACHE_TTL_SECONDS,
        lambda: fetch_pioneer_sources_live(days),
        force_refresh=force_refresh,
    )


def fetch_pioneer_sources_live(days: int) -> dict:
    sources = {"Videre MTGO": fetch_videre, "Spicerack": fetch_spicerack}
    decks: list[dict] = []
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=len(sources)) as executor:
        futures = {executor.submit(loader, days): name for name, loader in sources.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                decks.extend(future.result())
            except RuntimeError as error:
                errors.append(f"{name}: {error}")
    decks = deduplicate(decks)
    if not decks:
        raise RuntimeError("; ".join(errors) or "No Pioneer tournament decklists returned")
    events = [{
        "id": "pioneer-evidence-sample",
        "url": "https://www.videreproject.com/",
        "title": "Pioneer tournament sample",
        "publish_date": datetime.now(timezone.utc).date().isoformat(),
        "event_type": "multi-source",
        "decks_total": len(decks),
        "decks_cached": len(decks),
        "decks": decks,
    }]
    payload = {
        "schema_version": "1",
        "kind": "pioneer_multi_source_decklists",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "format": "pioneer",
        "source": "videre-spicerack",
        "days": days,
        "events": events,
        "warnings": errors,
        "active_sources": sorted({deck["source"] for deck in decks}),
    }
    return payload


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
        if parsed.path == "/api/archetype":
            query = parse_qs(parsed.query)
            archetype = query.get("name", [""])[0].strip()
            days = int(query.get("days", [90])[0])
            limit = int(query.get("limit", [MAX_ARCHETYPE_DECKS])[0])
            force_refresh = query.get("refresh", [""])[0].lower() in {"1", "true", "yes"}
            days = max(1, min(days, 90))
            if not archetype:
                return self._send_json(400, {"error": "An archetype name is required"})
            try:
                return self._send_json(200, fetch_mtgdecklists_archetype(
                    archetype, days, limit, force_refresh=force_refresh
                ))
            except (RuntimeError, ValueError) as error:
                return self._send_json(502, {"error": str(error)})
        if parsed.path == "/api/community":
            query = parse_qs(parsed.query)
            archetype = query.get("name", [""])[0].strip()
            days = int(query.get("days", [90])[0])
            limit = int(query.get("limit", [MAX_ARCHETYPE_DECKS])[0])
            force_refresh = query.get("refresh", [""])[0].lower() in {"1", "true", "yes"}
            days = max(1, min(days, 90))
            if not archetype:
                return self._send_json(400, {"error": "An archetype name is required"})
            try:
                return self._send_json(200, fetch_moxfield_archetype(
                    archetype, days, limit, force_refresh=force_refresh
                ))
            except (RuntimeError, ValueError) as error:
                return self._send_json(502, {"error": str(error)})
        if parsed.path != "/api/pioneer":
            return super().do_GET()
        query = parse_qs(parsed.query)
        days = int(query.get("days", [30])[0])
        force_refresh = query.get("refresh", [""])[0].lower() in {"1", "true", "yes"}
        days = max(1, min(days, 90))
        try:
            payload = fetch_pioneer_sources(days, force_refresh=force_refresh)
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
    initialize_cache()
    try:
        server = ThreadingHTTPServer(("127.0.0.1", 8080), DelverHandler)
    except OSError as error:
        if error.errno == EADDRINUSE:
            raise SystemExit(
                "Delver is already running at http://127.0.0.1:8080 — open that URL instead."
            ) from error
        raise
    print("Delver is available at http://127.0.0.1:8080")
    server.serve_forever()


if __name__ == "__main__":
    main()
