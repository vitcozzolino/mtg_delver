"""Local-only server for Delver's live Pioneer sources.

Run with TOPDECK_API_KEY set in your shell. The key is never returned to the
browser and is only sent to TopDeck's API in the Authorization request.
"""

from __future__ import annotations

import base64
import json
import os
import re
import secrets
import sqlite3
import tempfile
import threading
import time
import uuid
import zipfile
from hashlib import sha256
from errno import EADDRINUSE
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html import escape, unescape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

import jwt
import requests


ROOT = Path(__file__).parent
TOPDECK_URL = "https://topdeck.gg/api/v2/tournaments"
VIDERE_DECKS_URL = "https://api.videreproject.com/decks"
SPICERACK_URL = "https://api.spicerack.gg/api/export-decklists/"
MTG_DECKLISTS_URL = "https://mtgdecklists.com"
MTGCONTENT_DECKLISTS_URL = "https://www.mtgcontent.com/decklists/browse"
MTG_TOP8_URL = "https://www.mtgtop8.com"
MOXFIELD_API_URL = "https://api2.moxfield.com"
MAX_VIDERE_DECKS = 1_000
CACHE_DB = ROOT / "delver-cache.sqlite3"
SOURCE_CACHE_TTL_SECONDS = 30 * 60
ARCHETYPE_CACHE_TTL_SECONDS = 6 * 60 * 60
CARD_PROFILE_CACHE_TTL_SECONDS = 30 * 24 * 60 * 60
CARD_ALTERNATIVE_CACHE_TTL_SECONDS = 24 * 60 * 60
CARD_LAB_REVIEW_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
OPENAI_CARD_LAB_MODEL = "gpt-5.6-terra"
OPENAI_AUTH_AUTHORIZE_URL = "https://auth.openai.com/api/accounts/authorize"
OPENAI_AUTH_TOKEN_URL = "https://auth.openai.com/api/accounts/oauth/token"
OPENAI_AUTH_JWKS_URL = "https://auth.openai.com/.well-known/jwks.json"
OPENAI_CHATGPT_RESOURCE = "https://api.openai.com/v1"
OPENAI_CHATGPT_SCOPES = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct"
OPENAI_DYNAMIC_CLIENT_ID = "dynamic_agent_client"
CHATGPT_AUTH_STORE = ROOT / ".delver-chatgpt-auth.json"
CHATGPT_REDIRECT_URI = "http://127.0.0.1:8080/api/chatgpt/callback"
MAX_ARCHETYPE_DECKS = 20
LOCAL_DECK_ARCHIVE = ROOT / "output" / "mtgdecks" / "decklists.zip"
# MTGTop8 does not publish an API or rate-limit guidance. Keep every live
# lookup intentionally small, serial, and cache-first.
MTG_TOP8_REQUEST_DELAY_SECONDS = 0.75


# MTGTop8's public labels do not always match the labels used by MTGO sources.
# Keep aliases narrow: an ambiguous match is safer than silently mixing shells.
MTG_TOP8_ARCHETYPE_ALIASES = {
    "izzet phoenix": ("arclight phoenix", "izzet phoenix", "izzet arclight"),
    "azorius control": ("azorius control", "uw control", "blue white control"),
    "mono green devotion": ("mono green devotion", "green devotion"),
    "greasefang": ("greasefang",),
    "lotus field": ("lotus field",),
}


CARD_LAB_ARCHETYPES = {
    "Izzet Phoenix": {
        "colors": "UR",
        "strategy": "Spell-density graveyard tempo",
        "win_plan": "Fill the graveyard, chain cheap spells, and recur Arclight Phoenix while protecting the tempo lead.",
        "priorities": {"spell", "selection", "graveyard", "recursion", "tempo", "threat"},
    },
    "Azorius Control": {
        "colors": "WU",
        "strategy": "Reactive control",
        "win_plan": "Trade efficiently, protect card advantage, then close with a resilient planeswalker or land threat.",
        "priorities": {"countermagic", "removal", "selection", "sweeper", "threat"},
    },
    "Mono-Green Devotion": {
        "colors": "G",
        "strategy": "Devotion ramp",
        "win_plan": "Accelerate mana and devotion, then overwhelm the board with oversized permanents and Nykthos turns.",
        "priorities": {"ramp", "devotion", "threat", "selection"},
    },
    "Greasefang": {
        "colors": "WB",
        "strategy": "Graveyard vehicle combo",
        "win_plan": "Put Parhelion II in the graveyard, return it with Greasefang, and attack before the opponent can stabilize.",
        "priorities": {"graveyard", "recursion", "selection", "threat"},
    },
    "Lotus Field": {
        "colors": "U",
        "strategy": "Land-combo mana engine",
        "win_plan": "Assemble Lotus Field mana, untap it repeatedly, and convert the mana burst into a deterministic finish.",
        "priorities": {"ramp", "selection", "spell"},
    },
}

# These labels describe broad card classes, not a job a replacement needs to
# preserve. A one-mana burn spell and Opt are both "spells", but that does not
# make the burn spell an Opt replacement.
CARD_LAB_GENERIC_ROLES = {"spell", "land"}
CARD_LAB_FUNCTIONAL_ROLES = {
    "selection", "graveyard", "recursion", "countermagic", "removal",
    "burn", "sweeper", "ramp", "devotion", "tempo",
}

# OAuth transactions are deliberately short-lived and only held in memory.
# Tokens themselves are stored in a local 0600 file and never cross the API
# boundary to the browser.
CHATGPT_AUTH_PENDING: dict[str, dict] = {}
CHATGPT_AUTH_LOCK = threading.Lock()


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


def load_chatgpt_auth_store() -> dict:
    """Load local OAuth credentials without ever exposing them over HTTP."""
    try:
        payload = json.loads(CHATGPT_AUTH_STORE.read_text())
    except (OSError, json.JSONDecodeError):
        payload = {}
    return payload if isinstance(payload, dict) else {}


def save_chatgpt_auth_store(payload: dict) -> None:
    """Atomically persist OAuth credentials with owner-only permissions."""
    CHATGPT_AUTH_STORE.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=CHATGPT_AUTH_STORE.parent,
            prefix=".delver-chatgpt-", suffix=".tmp", delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            os.chmod(temporary_path, 0o600)
            json.dump(payload, temporary_file, sort_keys=True)
            temporary_file.write("\n")
        os.replace(temporary_path, CHATGPT_AUTH_STORE)
        os.chmod(CHATGPT_AUTH_STORE, 0o600)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink(missing_ok=True)


def chatgpt_host_id() -> str:
    with CHATGPT_AUTH_LOCK:
        stored = load_chatgpt_auth_store()
        host_id = stored.get("ext_agent_host_id")
        if isinstance(host_id, str) and re.fullmatch(r"urn:uuid:[0-9a-fA-F-]{36}", host_id):
            return host_id
        # OpenAI requires a URI-form host identifier, not a bare UUID.
        host_id = f"urn:uuid:{uuid.uuid4()}"
        save_chatgpt_auth_store({"ext_agent_host_id": host_id})
        return host_id


def urlsafe_sha256(value: str) -> str:
    return base64.urlsafe_b64encode(sha256(value.encode()).digest()).decode().rstrip("=")


def chatgpt_connection_status() -> dict:
    """Return only safe connection metadata for the local Card Lab UI."""
    stored = load_chatgpt_auth_store()
    account = stored.get("account")
    if not isinstance(account, dict) or not isinstance(account.get("refresh_token"), str):
        return {"connected": False, "provider": "chatgpt_plan"}
    email = account.get("email")
    return {
        "connected": True,
        "provider": "chatgpt_plan",
        "account": email if isinstance(email, str) and email else None,
        "preferred_model": os.environ.get("OPENAI_MODEL", OPENAI_CARD_LAB_MODEL),
    }


def begin_chatgpt_sign_in() -> dict:
    """Create a PKCE-protected OpenAI OAuth authorization URL."""
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    with CHATGPT_AUTH_LOCK:
        stored = load_chatgpt_auth_store()
        account = stored.get("account") if isinstance(stored.get("account"), dict) else {}
        issued_client_id = account.get("client_id") if isinstance(account.get("client_id"), str) else None
        client_id = issued_client_id or OPENAI_DYNAMIC_CLIENT_ID
        CHATGPT_AUTH_PENDING[state] = {
            "nonce": nonce,
            "verifier": verifier,
            "client_id": client_id,
            "is_new_registration": issued_client_id is None,
            "created_at": time.time(),
        }
        # Keep at most ten short-lived transactions. States expire after ten
        # minutes, so a stale browser tab cannot become a long-lived secret.
        stale_states = [key for key, value in CHATGPT_AUTH_PENDING.items() if value["created_at"] < time.time() - 600]
        for stale_state in stale_states:
            CHATGPT_AUTH_PENDING.pop(stale_state, None)
    parameters = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": CHATGPT_REDIRECT_URI,
        "scope": OPENAI_CHATGPT_SCOPES,
        "resource": OPENAI_CHATGPT_RESOURCE,
        "state": state,
        "nonce": nonce,
        "code_challenge": urlsafe_sha256(verifier),
        "code_challenge_method": "S256",
        "ext_agent_host_id": chatgpt_host_id(),
    }
    if issued_client_id is None:
        parameters["agent_name_hint"] = "Delver"
    else:
        if isinstance(account.get("id_token"), str):
            parameters["id_token_hint"] = account["id_token"]
        if isinstance(account.get("email"), str):
            parameters["login_hint"] = account["email"]
    return {"authorize_url": f"{OPENAI_AUTH_AUTHORIZE_URL}?{urlencode(parameters)}"}


def request_chatgpt_token(parameters: dict[str, str]) -> dict:
    encoded = urlencode(parameters).encode()
    response = fetch_json(
        OPENAI_AUTH_TOKEN_URL,
        timeout=30,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=encoded,
    )
    if not isinstance(response, dict) or not isinstance(response.get("access_token"), str):
        raise RuntimeError("ChatGPT did not return a usable access token")
    return response


def validate_chatgpt_id_token(id_token: str, *, client_id: str, nonce: str) -> dict:
    """Validate signature, issuer, audience, expiry, and nonce for OpenAI OAuth."""
    try:
        algorithm = jwt.get_unverified_header(id_token).get("alg")
        if algorithm not in {"RS256", "ES256"}:
            raise RuntimeError("ChatGPT sign-in used an unsupported token algorithm")
        jwk_client = jwt.PyJWKClient(OPENAI_AUTH_JWKS_URL)
        signing_key = jwk_client.get_signing_key_from_jwt(id_token)
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=[algorithm],
            audience=client_id,
            issuer="https://auth.openai.com",
        )
    except (jwt.PyJWTError, RuntimeError) as error:
        raise RuntimeError("ChatGPT sign-in token validation failed") from error
    if claims.get("nonce") != nonce:
        raise RuntimeError("ChatGPT sign-in nonce did not match")
    return claims if isinstance(claims, dict) else {}


def complete_chatgpt_sign_in(query: dict[str, list[str]]) -> dict:
    error = query.get("error", [""])[0]
    if error:
        description = query.get("error_description", [""])[0]
        raise RuntimeError(description or f"ChatGPT sign-in was declined ({error})")
    state = query.get("state", [""])[0]
    code = query.get("code", [""])[0]
    if not state or not code:
        raise RuntimeError("ChatGPT sign-in did not return an authorization code")
    with CHATGPT_AUTH_LOCK:
        transaction = CHATGPT_AUTH_PENDING.pop(state, None)
    if not transaction or transaction["created_at"] < time.time() - 600:
        raise RuntimeError("ChatGPT sign-in expired. Return to Card Lab and try again.")
    callback_client_id = query.get("client_id", [""])[0]
    if transaction["is_new_registration"]:
        if not callback_client_id or callback_client_id == OPENAI_DYNAMIC_CLIENT_ID:
            raise RuntimeError("ChatGPT registration did not return an issued client ID")
        issued_client_id = callback_client_id
    else:
        if callback_client_id and callback_client_id != transaction["client_id"]:
            raise RuntimeError("ChatGPT sign-in returned a different client ID")
        issued_client_id = transaction["client_id"]
    token_payload = request_chatgpt_token({
        "grant_type": "authorization_code",
        "client_id": issued_client_id,
        "code": code,
        "code_verifier": transaction["verifier"],
        "redirect_uri": CHATGPT_REDIRECT_URI,
        "resource": OPENAI_CHATGPT_RESOURCE,
    })
    id_token = token_payload.get("id_token")
    scope = str(token_payload.get("scope") or "")
    if not isinstance(id_token, str):
        raise RuntimeError("ChatGPT sign-in did not issue complete credentials")
    claims = validate_chatgpt_id_token(id_token, client_id=issued_client_id, nonce=transaction["nonce"])
    granted_scopes = set(scope.split())
    if "chatgpt.tokens.use.direct" not in granted_scopes:
        raise RuntimeError("This ChatGPT account is not enabled for direct plan-token use")
    expires_in = token_payload.get("expires_in")
    expires_at = time.time() + int(expires_in) if isinstance(expires_in, (int, float, str)) and str(expires_in).isdigit() else time.time() + 300
    account = {
        "client_id": issued_client_id,
        "access_token": token_payload["access_token"],
        "refresh_token": token_payload.get("refresh_token"),
        "id_token": id_token,
        "expires_at": expires_at,
        "scope": scope,
        "email": claims.get("email") if isinstance(claims.get("email"), str) else None,
    }
    if not isinstance(account["refresh_token"], str):
        raise RuntimeError("ChatGPT sign-in did not return a refresh token")
    with CHATGPT_AUTH_LOCK:
        stored = load_chatgpt_auth_store()
        stored["account"] = account
        save_chatgpt_auth_store(stored)
    return chatgpt_connection_status()


def chatgpt_plan_access_token() -> str | None:
    """Return a valid plan access token, refreshing it locally when needed."""
    with CHATGPT_AUTH_LOCK:
        stored = load_chatgpt_auth_store()
        account = stored.get("account")
        if not isinstance(account, dict):
            return None
        token = account.get("access_token")
        expires_at = account.get("expires_at")
        if isinstance(token, str) and isinstance(expires_at, (int, float)) and expires_at > time.time() + 120:
            return token
        refresh_token = account.get("refresh_token")
        client_id = account.get("client_id")
        if not isinstance(refresh_token, str) or not isinstance(client_id, str):
            return None
        token_payload = request_chatgpt_token({
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh_token,
            "resource": OPENAI_CHATGPT_RESOURCE,
        })
        account["access_token"] = token_payload["access_token"]
        if isinstance(token_payload.get("refresh_token"), str):
            account["refresh_token"] = token_payload["refresh_token"]
        expires_in = token_payload.get("expires_in")
        account["expires_at"] = time.time() + int(expires_in) if isinstance(expires_in, (int, float, str)) and str(expires_in).isdigit() else time.time() + 300
        stored["account"] = account
        save_chatgpt_auth_store(stored)
        return account["access_token"]


def chatgpt_plan_models() -> list[dict[str, str]]:
    """Return the signed-in account's visible model catalog, never cached globally."""
    token = chatgpt_plan_access_token()
    if not token:
        raise RuntimeError("Connect ChatGPT before loading the plan model catalog")
    response = fetch_json(
        "https://api.openai.com/v1/models",
        timeout=30,
        headers={"Authorization": f"Bearer {token}"},
    )
    raw_models = response.get("models") if isinstance(response, dict) else None
    if not isinstance(raw_models, list):
        raise RuntimeError("ChatGPT did not return a usable model catalog")
    models = []
    for model in raw_models:
        if not isinstance(model, dict) or model.get("visibility") != "list":
            continue
        slug, display_name = model.get("slug"), model.get("display_name")
        if isinstance(slug, str) and slug and isinstance(display_name, str) and display_name:
            models.append({"slug": slug, "display_name": display_name})
    if not models:
        raise RuntimeError("This ChatGPT account has no models available for Card Lab")
    return models


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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS card_profiles (
                card_name TEXT PRIMARY KEY,
                profile TEXT NOT NULL,
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


def fetch_json(
    url: str,
    timeout: int = 20,
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
) -> object:
    request_headers = {
        "Accept": "application/json",
        "User-Agent": "mtg-delver/0.1 (+https://github.com/vitcozzolino/mtg_delver)",
    }
    if headers:
        request_headers.update(headers)
    request = Request(url, data=data, headers=request_headers, method="POST" if data else "GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:200]
        raise RuntimeError(f"Source returned HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach source: {error.reason}") from error


def fetch_response_text_streaming(request_payload: dict, access_token: str) -> str:
    """Consume the Responses SSE stream required for ChatGPT plan tokens."""
    headers = {
        "Accept": "text/event-stream",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "mtg-delver/0.1 (+https://github.com/vitcozzolino/mtg_delver)",
    }
    deltas: list[str] = []
    completed = False
    seen_types: list[str] = []

    def consume_event(event: object) -> None:
        nonlocal completed
        if not isinstance(event, dict):
            return
        event_type = event.get("type")
        if isinstance(event_type, str):
            seen_types.append(event_type)
        if event_type == "response.output_text.delta" and isinstance(event.get("delta"), str):
            deltas.append(event["delta"])
        elif event_type in {"response.completed", "response.done"}:
            completed = True
            if not deltas and isinstance(event.get("response"), dict):
                completed_text = output_text_from_response(event["response"])
                if completed_text:
                    deltas.append(completed_text)
        elif event_type in {"response.failed", "response.incomplete", "error"}:
            response_data = event.get("response") if isinstance(event.get("response"), dict) else {}
            error = response_data.get("error") or event.get("error")
            message = error.get("message") if isinstance(error, dict) else None
            if event_type == "response.incomplete" and not message:
                details = response_data.get("incomplete_details")
                reason = details.get("reason") if isinstance(details, dict) else None
                message = f"ChatGPT plan review was incomplete ({reason or 'unknown reason'})"
            raise RuntimeError(message or "ChatGPT plan review did not complete")

    try:
        with requests.post(
            OPENAI_RESPONSES_URL, headers=headers, json=request_payload,
            stream=True, timeout=(15, 45),
        ) as response:
            if not response.ok:
                raise RuntimeError(f"ChatGPT plan returned HTTP {response.status_code}: {response.text[:300]}")
            # Accept a completed JSON response as well as the normal SSE
            # response. requests handles stream encoding/decompression safely.
            if "application/json" in response.headers.get("Content-Type", ""):
                completed_response = response.json()
                if not isinstance(completed_response, dict):
                    raise RuntimeError("ChatGPT plan returned an invalid completed response")
                if isinstance(completed_response.get("error"), dict):
                    raise RuntimeError(completed_response["error"].get("message") or "ChatGPT plan review failed")
                completed = True
                completed_text = output_text_from_response(completed_response)
                if completed_text:
                    deltas.append(completed_text)
            else:
                data_lines: list[str] = []
                for line in response.iter_lines(decode_unicode=True):
                    if isinstance(line, bytes):
                        line = line.decode("utf-8", errors="replace")
                    if not line:
                        if data_lines:
                            data = "\n".join(data_lines)
                            data_lines = []
                            if data != "[DONE]":
                                try:
                                    consume_event(json.loads(data))
                                except json.JSONDecodeError:
                                    continue
                        continue
                    if line.startswith("data:"):
                        data_lines.append(line[5:].lstrip())
                if data_lines:
                    try:
                        consume_event(json.loads("\n".join(data_lines)))
                    except json.JSONDecodeError:
                        pass
    except requests.RequestException as error:
        raise RuntimeError(f"Could not reach ChatGPT plan inference: {error}") from error
    if not completed:
        observed = ", ".join(dict.fromkeys(seen_types)) or "no readable stream events"
        raise RuntimeError(f"ChatGPT plan stream ended before completion ({observed})")
    return "".join(deltas)


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


def mtgdecks_arena_mainboard(page: str) -> str:
    """Read a saved MTGDecks Arena export without making any network request."""
    match = re.search(
        r'<textarea[^>]*id=["\']arena_deck["\'][^>]*>(?P<deck>.*?)</textarea>',
        page,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ""
    deck_text = unescape(match.group("deck")).replace("\r\n", "\n").strip()
    return re.split(r"\n\s*Sideboard\s*\n", deck_text, maxsplit=1, flags=re.IGNORECASE)[0].strip()


def local_archive_metadata(page: str, file_name: str) -> dict[str, str]:
    description_match = re.search(
        r'<meta\s+name=["\']description["\']\s+content=["\'](?P<description>.*?)["\']',
        page,
        re.IGNORECASE | re.DOTALL,
    )
    description = unescape(description_match.group("description")) if description_match else ""
    details_match = re.search(
        r"played by (?P<player>.*?) in (?P<event>.*?) on (?P<date>20\d{2}-\d{2}-\d{2})",
        description,
        re.IGNORECASE,
    )
    title_match = re.search(r"<title>(?P<title>.*?)</title>", page, re.IGNORECASE | re.DOTALL)
    title = html_text(title_match.group("title")) if title_match else file_name
    return {
        "player": details_match.group("player").strip() if details_match else "Unknown player",
        "event": details_match.group("event").strip() if details_match else "Saved MTGDecks page",
        "date": details_match.group("date") if details_match else datetime.now(timezone.utc).date().isoformat(),
        "title": title.replace("• MTG DECKS", "").strip(),
    }


def fetch_local_phoenix_archive() -> dict:
    """Import user-supplied saved pages, keeping only real Phoenix mainboards.

    The archive is local data supplied by the user. It is deliberately not
    fetched from MTGDecks and it is marked historical in the returned payload.
    """
    if not LOCAL_DECK_ARCHIVE.is_file():
        raise RuntimeError("Local deck archive not found. Run the MTGDecks loader to create output/mtgdecks/decklists.zip.")
    decks: list[dict] = []
    with zipfile.ZipFile(LOCAL_DECK_ARCHIVE) as archive:
        for info in archive.infolist():
            if info.is_dir() or not info.filename.lower().endswith((".html", ".htm")):
                continue
            if info.file_size > 2_000_000:
                continue
            page = archive.read(info).decode("utf-8", errors="replace")
            deck_text = mtgdecks_arena_mainboard(page)
            cards = to_deck_text(deck_text)
            if not re.search(r"^\d+\s+Arclight Phoenix\s*$", cards, re.IGNORECASE | re.MULTILINE):
                continue
            metadata = local_archive_metadata(page, Path(info.filename).name)
            decks.append({
                "date": metadata["date"],
                "event": metadata["event"],
                "result": "Historical local archive",
                "player": metadata["player"],
                "archetype": "Izzet Phoenix",
                "source": "local-archive",
                "format": "pioneer",
                "deck_text": cards,
                "source_url": "",
                "historical_archive": True,
                "title": metadata["title"],
            })
    if not decks:
        raise RuntimeError("No Izzet Phoenix mainboards found in the local deck archive.")
    decks.sort(key=lambda deck: (deck["date"], deck["player"]), reverse=True)
    return {
        "schema_version": "1",
        "kind": "local_izzet_phoenix_archive",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "format": "pioneer",
        "source": "local-archive",
        "events": [{
            "id": "local-izzet-phoenix-archive",
            "url": "",
            "title": "Local saved Izzet Phoenix archive",
            "publish_date": datetime.now(timezone.utc).date().isoformat(),
            "event_type": "historical_archive",
            "decks_total": len(decks),
            "decks_cached": len(decks),
            "decks": decks,
        }],
    }


def card_profile_from_scryfall(card: object) -> dict:
    if not isinstance(card, dict):
        return {"type_line": "", "mana_value": 0, "oracle_text": ""}
    return {
        "type_line": str(card.get("type_line") or ""),
        "mana_value": card.get("cmc") if isinstance(card.get("cmc"), (int, float)) else 0,
        "oracle_text": str(card.get("oracle_text") or ""),
    }


def fetch_card_profiles(names: list[str]) -> dict[str, dict]:
    """Resolve card type/rules data once, then keep it in the local SQLite cache."""
    requested = list(dict.fromkeys(name.strip() for name in names if name and name.strip()))[:75]
    if not requested:
        return {}
    cached: dict[str, dict] = {}
    missing: list[str] = []
    now = time.time()
    placeholders = ", ".join("?" for _ in requested)
    with sqlite3.connect(CACHE_DB, timeout=5) as connection:
        rows = connection.execute(
            f"SELECT card_name, profile, fetched_at FROM card_profiles WHERE card_name IN ({placeholders})",
            requested,
        ).fetchall()
    rows_by_name = {row[0]: row for row in rows}
    for name in requested:
        row = rows_by_name.get(name)
        if not row or now - float(row[2]) >= CARD_PROFILE_CACHE_TTL_SECONDS:
            missing.append(name)
            continue
        try:
            profile = json.loads(row[1])
        except (TypeError, json.JSONDecodeError):
            missing.append(name)
            continue
        if isinstance(profile, dict) and profile.get("type_line"):
            cached[name] = profile
        else:
            missing.append(name)
    if not missing:
        return cached

    payload = json.dumps({"identifiers": [{"name": name} for name in missing]}).encode()
    response = fetch_json(
        "https://api.scryfall.com/cards/collection",
        headers={"Content-Type": "application/json"},
        data=payload,
    )
    if not isinstance(response, dict):
        raise RuntimeError("Scryfall returned an unexpected card-profile response")
    resolved: dict[str, dict] = {}
    requested_by_normalized_name = {name.casefold(): name for name in missing}
    for card in response.get("data", []):
        if isinstance(card, dict) and isinstance(card.get("name"), str):
            profile = card_profile_from_scryfall(card)
            # Scryfall identifies adventures and modal double-faced cards by
            # their combined name, while decklists commonly use the front face.
            for card_name in card["name"].split(" // "):
                requested_name = requested_by_normalized_name.get(card_name.casefold())
                if requested_name:
                    resolved[requested_name] = profile
    profiles_to_store: dict[str, dict] = {}
    for name in missing:
        profiles_to_store[name] = resolved.get(name, {"type_line": "", "mana_value": 0, "oracle_text": ""})
    with sqlite3.connect(CACHE_DB, timeout=5) as connection:
        connection.executemany(
            """
            INSERT INTO card_profiles (card_name, profile, fetched_at) VALUES (?, ?, ?)
            ON CONFLICT(card_name) DO UPDATE SET profile = excluded.profile, fetched_at = excluded.fetched_at
            """,
            [(name, json.dumps(profile), now) for name, profile in profiles_to_store.items()],
        )
    cached.update(profiles_to_store)
    return cached


def card_lab_primary_type(type_line: str) -> str:
    lowered = type_line.casefold()
    for card_type in ("land", "creature", "planeswalker", "artifact", "enchantment", "instant", "sorcery"):
        if card_type in lowered:
            return card_type
    return "other"


def card_lab_roles(type_line: str, oracle_text: str) -> set[str]:
    """Map rules text to compact, explainable deckbuilding roles."""
    text = oracle_text.casefold()
    card_type = card_lab_primary_type(type_line)
    roles: set[str] = set()
    if card_type in {"instant", "sorcery"}:
        roles.add("spell")
    if card_type in {"creature", "planeswalker"}:
        roles.add("threat")
    if card_type == "land":
        roles.add("land")
    if re.search(r"draw (?:a|two|three|four)|surveil|connive|scry|look at the top", text):
        roles.add("selection")
    if re.search(r"mill|discard|from your graveyard|delve|escape|return .*graveyard", text):
        roles.add("graveyard")
    if re.search(r"return .*graveyard.*battlefield|return .*graveyard.*hand|escape", text):
        roles.add("recursion")
    if re.search(r"counter target|spells? can't be countered", text):
        roles.add("countermagic")
    if re.search(r"destroy target|exile target|deals? \d+ damage to target|fight target", text):
        roles.add("removal")
    if re.search(r"deals? \d+ damage to any target|deals? \d+ damage to each", text):
        roles.add("burn")
    if re.search(r"destroy all|exile all|each creature gets -", text):
        roles.add("sweeper")
    if re.search(r"add \{|search your library for a basic land|create a treasure", text):
        roles.add("ramp")
    if re.search(r"devotion", text):
        roles.add("devotion")
    if re.search(r"tap target|return target.*owner.?s hand|can.?t attack|can.?t block", text):
        roles.add("tempo")
    return roles


def card_lab_required_roles(source_roles: set[str]) -> set[str]:
    """Return the actual job that needs preserving in a swap.

    Generic labels such as ``spell`` are deliberately excluded. This prevents
    false equivalences such as offering a colour-hosing removal spell in place
    of a cantrip simply because both happen to be instants.
    """
    return source_roles & CARD_LAB_FUNCTIONAL_ROLES


def card_lab_is_narrow_removal(card: dict) -> bool:
    """Flag removal limited by a colour, tribe, or similarly narrow condition."""
    text = str(card.get("oracle_text") or "").casefold()
    return bool(re.search(
        r"\b(?:white|blue|black|red|green)(?:\s+or\s+(?:white|blue|black|red|green))*\s+"
        r"(?:creature|permanent)\b|\b(?:multicolored|monocolored|artifact|enchantment|"
        r"legendary|token)\s+(?:creature|permanent)\b|\b(?:creature|permanent) with\b",
        text,
    ))


def card_lab_card(card: object) -> dict | None:
    if not isinstance(card, dict) or not isinstance(card.get("name"), str):
        return None
    legalities = card.get("legalities")
    if not isinstance(legalities, dict) or legalities.get("pioneer") != "legal":
        return None
    type_line = str(card.get("type_line") or "")
    oracle_text = str(card.get("oracle_text") or "")
    colors = "".join(card.get("color_identity") or [])
    mana_value = card.get("cmc") if isinstance(card.get("cmc"), (int, float)) else 0
    effective_mana_value = max(1, mana_value - 6) if "delve" in oracle_text.casefold() else mana_value
    return {
        "name": card["name"],
        "type_line": type_line,
        "oracle_text": oracle_text,
        "mana_value": mana_value,
        "effective_mana_value": effective_mana_value,
        "colors": colors,
        "roles": sorted(card_lab_roles(type_line, oracle_text)),
        "scryfall_uri": card.get("scryfall_uri") or "",
        "image_uri": (card.get("image_uris") or {}).get("normal") if isinstance(card.get("image_uris"), dict) else "",
    }


def card_lab_query(card_type: str, colors: str, source_roles: set[str]) -> str:
    type_query = {
        "instant": "t:instant",
        "sorcery": "t:sorcery",
        "creature": "t:creature",
        "planeswalker": "t:planeswalker",
        "artifact": "t:artifact",
        "enchantment": "t:enchantment",
        "land": "t:land",
    }.get(card_type, "")
    color_query = f"ci<={colors}" if colors else ""
    role_query = ""
    if "selection" in source_roles:
        role_query = "o:draw"
    elif "countermagic" in source_roles:
        role_query = "o:counter"
    elif "removal" in source_roles:
        role_query = "o:target"
    return " ".join(part for part in ("f:pioneer", color_query, type_query, role_query) if part)


def card_lab_score(source: dict, candidate: dict, plan: dict) -> tuple[int, list[str], list[str]]:
    source_roles = set(source["roles"])
    candidate_roles = set(candidate["roles"])
    shared_roles = sorted((source_roles & candidate_roles) - CARD_LAB_GENERIC_ROLES)
    plan_roles = sorted(candidate_roles & set(plan["priorities"]))
    mana_delta = abs(float(source["effective_mana_value"]) - float(candidate["effective_mana_value"]))
    score = 28 if card_lab_primary_type(source["type_line"]) == card_lab_primary_type(candidate["type_line"]) else 0
    score += len(shared_roles) * 20
    score += len(plan_roles) * 9
    score += 12 if mana_delta <= 1 else 0
    score -= int(mana_delta * 10)
    if candidate["name"].casefold() == source["name"].casefold():
        return -1_000, shared_roles, plan_roles
    if "removal" in source_roles and not card_lab_is_narrow_removal(source) and card_lab_is_narrow_removal(candidate):
        score -= 28
    return score, shared_roles, plan_roles


def fetch_card_alternatives(
    card_name: str,
    archetype: str,
    *,
    excluded_cards: set[str] | None = None,
    mainboard: list[dict] | None = None,
    review_model: str | None = None,
    force_refresh: bool = False,
) -> dict:
    plan = CARD_LAB_ARCHETYPES.get(archetype)
    if not plan:
        raise RuntimeError(f"Card Lab does not have a strategy profile for {archetype} yet")
    cache_key = f"card-lab:v2:{archetype_slug(archetype)}:{card_name.casefold()}"
    payload = cached_fetch(
        cache_key,
        CARD_ALTERNATIVE_CACHE_TTL_SECONDS,
        lambda: fetch_card_alternatives_live(card_name, archetype, plan),
        force_refresh=force_refresh,
    )
    excluded = {name.casefold() for name in (excluded_cards or set())}
    filtered_payload = payload
    # The candidate pool is safely cached, while this presentation-level
    # filter remains specific to the baseline deck that opened Card Lab.
    if excluded:
        filtered_payload = {
            **payload,
            "alternatives": [
                candidate for candidate in payload.get("alternatives", [])
                if str(candidate.get("name") or "").casefold() not in excluded
            ],
            "excluded_cards": len(excluded),
        }
    return review_card_alternatives_with_llm(
        filtered_payload,
        mainboard=mainboard or [],
        review_model=review_model,
        force_refresh=force_refresh,
    )


def card_lab_mainboard_lines(mainboard: list[dict]) -> list[str]:
    """Validate the browser-provided local deck context before prompting."""
    lines: list[str] = []
    for entry in mainboard[:120]:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        quantity = entry.get("quantity")
        if not name or not isinstance(quantity, int) or not 1 <= quantity <= 20:
            continue
        lines.append(f"{quantity}x {name}")
    return lines


def card_lab_review_schema() -> dict:
    return {
        "type": "json_schema",
        "name": "pioneer_card_lab_review",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "reviews": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "verdict": {"type": "string", "enum": ["recommended", "situational", "reject"]},
                            "score": {"type": "integer", "minimum": 0, "maximum": 100},
                            "rationale": {"type": "string"},
                            "cautions": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["name", "verdict", "score", "rationale", "cautions"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["reviews"],
            "additionalProperties": False,
        },
    }


def card_lab_review_prompt(payload: dict, mainboard: list[dict]) -> str:
    source = payload["source_card"]
    # Review the strongest heuristic matches only. This keeps the structured
    # response bounded and avoids making the user wait on a long plan request.
    candidates = payload.get("alternatives", [])[:8]
    return json.dumps({
        "task": "Judge these possible Pioneer deck replacements. Return one review for every candidate supplied.",
        "format": "Pioneer",
        "archetype": payload["archetype"],
        "strategy": payload["strategy"],
        "win_plan": payload["win_plan"],
        "baseline_mainboard": card_lab_mainboard_lines(mainboard),
        "source_card": {
            "name": source["name"], "type_line": source["type_line"],
            "mana_value": source["mana_value"], "oracle_text": source["oracle_text"],
            "detected_roles": source["roles"],
        },
        "candidates": [{
            "name": card["name"], "type_line": card["type_line"],
            "mana_value": card["mana_value"], "oracle_text": card["oracle_text"],
            "roles": card["roles"],
        } for card in candidates],
        "rules": [
            "Use only the candidates supplied; never invent another card.",
            "Judge the actual role of the source card, not merely colour, card type, or mana value.",
            "Reject a candidate that does not preserve the source card's important function in this deck.",
            "Reject narrow hate cards as general replacements unless the baseline and matchup role clearly justify them.",
            "For Izzet Phoenix, distinguish cantrips/graveyard velocity from removal, and preserve spell density only when the card also has the needed job.",
            "Keep rationales concrete and short; name the strategic tradeoff where one exists.",
        ],
    })


def output_text_from_response(response: object) -> str:
    if not isinstance(response, dict):
        return ""
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    for item in response.get("output", []):
        if not isinstance(item, dict):
            continue
        for part in item.get("content", []):
            if isinstance(part, dict) and part.get("type") == "output_text" and isinstance(part.get("text"), str):
                return part["text"]
    return ""


def review_card_alternatives_with_llm(
    payload: dict, *, mainboard: list[dict], review_model: str | None, force_refresh: bool,
) -> dict:
    """Ask a bounded deckbuilding reviewer, never to generate arbitrary cards."""
    plan_error = ""
    try:
        chatgpt_token = chatgpt_plan_access_token()
    except RuntimeError as error:
        chatgpt_token = None
        plan_error = str(error)
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if chatgpt_token:
        credential = chatgpt_token
        provider = "chatgpt_plan"
        provider_label = "ChatGPT plan"
    elif api_key:
        credential = api_key
        provider = "api_key"
        provider_label = "OpenAI API"
    else:
        detail = plan_error or "Connect ChatGPT to enable a plan-backed deckbuilding review."
        return {**payload, "ai_review": {"status": "unavailable", "detail": detail}}
    candidates = payload.get("alternatives", [])
    if not candidates:
        return {**payload, "ai_review": {"status": "skipped", "detail": "No heuristic candidates to review."}}
    context_fingerprint = sha256(json.dumps({
        "mainboard": card_lab_mainboard_lines(mainboard),
        "candidates": [card["name"] for card in candidates],
        "source": payload["source_card"]["name"],
        "archetype": payload["archetype"],
        "model": review_model or os.environ.get("OPENAI_MODEL", OPENAI_CARD_LAB_MODEL),
    }, sort_keys=True).encode()).hexdigest()[:20]
    cache_key = f"card-lab:review:v2:{provider}:{context_fingerprint}"

    def request_review() -> dict:
        request_payload = {
            "model": review_model or os.environ.get("OPENAI_MODEL", OPENAI_CARD_LAB_MODEL),
            "instructions": "You are a precise competitive Magic: The Gathering Pioneer deckbuilder. Follow the supplied rules text and return only the requested JSON schema.",
            # ChatGPT plan inference requires the Responses message-list form
            # (the API-key path accepts it too), rather than a bare string.
            "input": [{"role": "user", "content": card_lab_review_prompt(payload, mainboard)}],
            "reasoning": {"effort": "low"},
            # Structured reviews for a dozen candidates can exceed 1,400
            # tokens (especially with reasoning). Leave room to finish.
            "max_output_tokens": 2_000,
            "store": False,
            "text": {"format": card_lab_review_schema()},
        }
        if provider == "chatgpt_plan":
            request_payload["stream"] = True
            response_text = fetch_response_text_streaming(request_payload, credential)
        else:
            response = fetch_json(
                OPENAI_RESPONSES_URL,
                timeout=60,
                headers={"Authorization": f"Bearer {credential}", "Content-Type": "application/json"},
                data=json.dumps(request_payload).encode(),
            )
            response_text = output_text_from_response(response)
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"{provider_label} returned an unreadable card review") from error
        if not isinstance(parsed, dict) or not isinstance(parsed.get("reviews"), list):
            raise RuntimeError(f"{provider_label} returned an invalid card review")
        return {"reviews": parsed["reviews"]}

    try:
        review_payload = cached_fetch(cache_key, CARD_LAB_REVIEW_CACHE_TTL_SECONDS, request_review, force_refresh=force_refresh)
    except RuntimeError as error:
        return {**payload, "ai_review": {"status": "unavailable", "detail": str(error)}}

    permitted_names = {str(card["name"]).casefold(): card for card in candidates}
    reviews: dict[str, dict] = {}
    for review in review_payload.get("reviews", []):
        if not isinstance(review, dict) or not isinstance(review.get("name"), str):
            continue
        candidate = permitted_names.get(review["name"].casefold())
        score = review.get("score")
        rationale, cautions = review.get("rationale"), review.get("cautions")
        if not candidate or review.get("verdict") not in {"recommended", "situational", "reject"} or not isinstance(score, int) or not 0 <= score <= 100:
            continue
        if not isinstance(rationale, str) or not isinstance(cautions, list) or not all(isinstance(item, str) for item in cautions):
            continue
        reviews[candidate["name"].casefold()] = {"verdict": review["verdict"], "score": score, "rationale": rationale.strip()[:500], "cautions": [item.strip()[:180] for item in cautions if item.strip()][:3]}
    reviewed = []
    for candidate in candidates:
        review = reviews.get(candidate["name"].casefold())
        if review and review["verdict"] != "reject":
            reviewed.append({**candidate, "ai_review": review})
    verdict_rank = {"recommended": 0, "situational": 1}
    reviewed.sort(key=lambda card: (verdict_rank[card["ai_review"]["verdict"]], -card["ai_review"]["score"], -card["score"], card["name"]))
    return {**payload, "alternatives": reviewed, "ai_review": {
        "status": "complete", "model": review_model or os.environ.get("OPENAI_MODEL", OPENAI_CARD_LAB_MODEL),
        "provider": provider,
        "provider_label": provider_label,
        "cache": review_payload.get("cache", {}).get("status", "refreshed"),
        "reviewed": len(candidates), "rejected": len(candidates) - len(reviewed),
    }}


def fetch_card_alternatives_live(card_name: str, archetype: str, plan: dict) -> dict:
    source_payload = fetch_json(
        f"https://api.scryfall.com/cards/named?{urlencode({'exact': card_name})}"
    )
    source = card_lab_card(source_payload)
    if not source:
        raise RuntimeError("Card Lab needs an exact Pioneer-legal card name")
    source_roles = set(source["roles"])
    required_roles = card_lab_required_roles(source_roles)
    query = card_lab_query(
        card_lab_primary_type(source["type_line"]), plan["colors"], source_roles
    )
    candidates_payload = fetch_json(
        f"https://api.scryfall.com/cards/search?{urlencode({'q': query, 'unique': 'cards', 'order': 'cmc'})}"
    )
    if not isinstance(candidates_payload, dict) or not isinstance(candidates_payload.get("data"), list):
        raise RuntimeError("Scryfall returned no compatible Pioneer card pool")
    alternatives: list[dict] = []
    for raw_candidate in candidates_payload["data"]:
        candidate = card_lab_card(raw_candidate)
        if not candidate:
            continue
        if (
            card_lab_primary_type(source["type_line"]) != "land"
            and abs(float(source["effective_mana_value"]) - float(candidate["effective_mana_value"])) > 2
        ):
            continue
        score, shared_roles, plan_roles = card_lab_score(source, candidate, plan)
        candidate_roles = set(candidate["roles"])
        # A candidate must perform at least one non-generic job in common. If
        # the source has a specific job (cantrip/selection, interaction,
        # ramp, graveyard setup…), preserve that exact job instead of merely
        # matching card type and colour identity.
        if score < 42 or not shared_roles or (required_roles and not (required_roles & candidate_roles)):
            continue
        functional_reason = ", ".join(shared_roles).replace("_", " ")
        plan_reason = ", ".join(plan_roles).replace("_", " ") if plan_roles else "same curve and color identity"
        alternatives.append({
            **candidate,
            "score": score,
            "functional_reason": f"Shares {functional_reason} with {source['name']}.",
            "plan_reason": f"Supports {plan_reason} in this {plan['strategy'].casefold()} shell.",
        })
    alternatives.sort(key=lambda candidate: (-candidate["score"], candidate["mana_value"], candidate["name"]))
    return {
        "kind": "card_lab_alternatives",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": "Pioneer legality + non-generic functional-role + archetype-plan hard filters",
        "source_card": source,
        "archetype": archetype,
        "strategy": plan["strategy"],
        "win_plan": plan["win_plan"],
        "alternatives": alternatives[:12],
    }


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


def mtgcontent_date(value: object) -> str:
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%b %d, %Y").date().isoformat()
        except ValueError:
            pass
    return datetime.now(timezone.utc).date().isoformat()


def mtgcontent_mainboard(cards: object) -> str:
    if not isinstance(cards, list):
        return ""
    lines: list[str] = []
    for card in cards:
        if not isinstance(card, dict):
            continue
        name = card.get("name")
        quantity = card.get("quantity")
        if isinstance(name, str) and isinstance(quantity, int) and quantity > 0:
            lines.append(f"{quantity} {name}")
    return "\n".join(lines)


def parse_mtgcontent_decks(page: str) -> list[dict]:
    """Extract deck objects embedded in MTGContent's public server-rendered page."""
    payload = page.replace(r'\"', '"')
    decoder = json.JSONDecoder()
    decks: list[dict] = []
    seen: set[str] = set()
    for match in re.finditer(r'\{"id":"', payload):
        try:
            record, _ = decoder.raw_decode(payload[match.start():])
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict) or not isinstance(record.get("cards"), dict):
            continue
        deck_id = record.get("id")
        if not isinstance(deck_id, str) or deck_id in seen:
            continue
        mainboard = mtgcontent_mainboard(record["cards"].get("mainboard"))
        if not mainboard:
            continue
        seen.add(deck_id)
        decks.append({
            "number": deck_id,
            "date": mtgcontent_date(record.get("displayDate")),
            "event": record.get("eventName") or "MTGContent published result",
            "result": record.get("result") or "Published list",
            "player": record.get("pilotUsername") or "Unknown player",
            "archetype": record.get("archetype") or "Unknown",
            "source": "mtgcontent",
            "format": "pioneer",
            "deck_text": mainboard,
            "source_url": record.get("url") or "https://www.mtgcontent.com/decklists",
        })
    return decks


def fetch_mtgcontent_archetype(
    archetype: str,
    days: int,
    limit: int = MAX_ARCHETYPE_DECKS,
    *,
    force_refresh: bool = False,
) -> dict:
    limit = max(1, min(limit, MAX_ARCHETYPE_DECKS))
    cache_key = f"mtgcontent:{archetype_slug(archetype)}:{days}:{limit}"
    return cached_fetch(
        cache_key,
        ARCHETYPE_CACHE_TTL_SECONDS,
        lambda: fetch_mtgcontent_archetype_live(archetype, days, limit),
        force_refresh=force_refresh,
    )


def fetch_mtgcontent_archetype_live(archetype: str, days: int, limit: int) -> dict:
    from urllib.parse import urlencode

    start_date = datetime.now(timezone.utc).date().fromordinal(
        datetime.now(timezone.utc).date().toordinal() - days
    )
    query = urlencode({
        "format": "pioneer",
        "type": "all",
        "deck": archetype,
        "from": start_date.isoformat(),
    })
    list_url = f"{MTGCONTENT_DECKLISTS_URL}?{query}"
    decks = [
        deck for deck in parse_mtgcontent_decks(fetch_html(list_url))
        if deck["archetype"].casefold() == archetype.casefold() and deck["date"] >= start_date.isoformat()
    ][:limit]
    return {
        "schema_version": "1",
        "kind": "mtgcontent_pioneer_archetype",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "format": "pioneer",
        "source": "mtgcontent",
        "days": days,
        "events": [{
            "id": f"mtgcontent-{archetype_slug(archetype)}",
            "url": list_url,
            "title": f"MTGContent · {archetype}",
            "publish_date": datetime.now(timezone.utc).date().isoformat(),
            "event_type": "archetype_sample",
            "decks_total": len(decks),
            "decks_cached": len(decks),
            "decks": decks,
        }],
    }


def mtgtop8_date(value: str) -> str | None:
    """Convert MTGTop8's DD/MM/YY list date into the common ISO format."""
    try:
        return datetime.strptime(value.strip(), "%d/%m/%y").date().isoformat()
    except ValueError:
        return None


def mtgtop8_meta_window(page: str, days: int) -> str:
    """Find the current MTGTop8 meta id closest to the requested date window."""
    windows: dict[str, str] = {}
    for match in re.finditer(
        r'href=["\']?\?f=PI&meta=(?P<meta>\d+)&a=["\']?[^>]*>'
        r'(?P<label>.*?)</a>',
        page,
        re.IGNORECASE | re.DOTALL,
    ):
        label = html_text(match.group("label")).casefold()
        windows[label] = match.group("meta")
    current_year_meta = next(
        (meta_id for label, meta_id in windows.items() if re.fullmatch(r"all \d{4} decks", label)),
        None,
    )
    if days > 62 and current_year_meta:
        return current_year_meta
    preferred_labels = (
        ("last 2 weeks", "last 2 months", "all pioneer decks")
        if days <= 14
        else ("last 2 months", "all pioneer decks")
        if days <= 62
        else ("all pioneer decks", "last 2 months")
    )
    for label in preferred_labels:
        if label in windows:
            return windows[label]
    if current_year_meta:
        return current_year_meta
    if not windows:
        raise RuntimeError("MTGTop8's Pioneer meta windows could not be read")
    return next(iter(windows.values()))


def mtgtop8_archetype_id(page: str, archetype: str) -> str:
    """Resolve a local archetype label to MTGTop8's public numeric id."""
    aliases = MTG_TOP8_ARCHETYPE_ALIASES.get(archetype.casefold(), (archetype,))
    candidates: list[tuple[str, str]] = []
    pattern = re.compile(
        r'href=["\']?archetype\?a=(?P<id>\d+)&meta=(?P<meta>\d+)&f=PI["\']?[^>]*>'
        r'(?P<label>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(page):
        candidates.append((html_text(match.group("label")), match.group("id")))
    for alias in aliases:
        alias_key = alias.casefold()
        for label, identifier in candidates:
            if label.casefold() == alias_key:
                return identifier
    if not candidates:
        raise RuntimeError("MTGTop8 has no Pioneer archetype index for the selected window")
    raise RuntimeError(f"MTGTop8 has no unambiguous match for {archetype}")


def parse_mtgtop8_entries(page: str, cutoff: str, limit: int) -> list[dict]:
    """Extract ranked public deck links from one MTGTop8 archetype page."""
    entries: list[dict] = []
    for row in re.findall(r"<tr[^>]*class=[\"']?hover_tr[^>]*>(.*?)</tr>", page, re.IGNORECASE | re.DOTALL):
        deck_match = re.search(
            r'href=["\']?(?P<href>/event\?e=(?P<event_id>\d+)&d=(?P<deck_id>\d+)&f=PI)["\']?'
            r'[^>]*>(?P<name>.*?)</a>',
            row,
            re.IGNORECASE | re.DOTALL,
        )
        columns = [html_text(column) for column in re.findall(r"<td[^>]*>(.*?)</td>", row, re.IGNORECASE | re.DOTALL)]
        if not deck_match or len(columns) < 7:
            continue
        deck_date = mtgtop8_date(columns[-1])
        if not deck_date or deck_date < cutoff:
            continue
        entries.append({
            "number": deck_match.group("deck_id"),
            "date": deck_date,
            "event": columns[3] or "MTGTop8 event",
            "result": f"#{columns[-2] or 'published'}",
            "player": columns[2] or "Unknown player",
            "title": html_text(deck_match.group("name")) or "Published deck",
            "source_url": f"{MTG_TOP8_URL}{deck_match.group('href')}",
        })
        if len(entries) >= limit:
            break
    return entries


def mtgtop8_mainboard(page: str) -> str:
    """Read only main-deck card rows; MTGTop8 marks those rows with an md id."""
    lines: list[str] = []
    pattern = re.compile(
        r'<div\s+id=["\']?md[^>]*class=["\'][^"\']*deck_line[^"\']*["\'][^>]*>'
        r'\s*(?P<quantity>\d+)\s*<span[^>]*>(?P<name>.*?)</span>',
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(page):
        name = html_text(match.group("name"))
        quantity = int(match.group("quantity"))
        if name and quantity > 0:
            lines.append(f"{quantity} {name}")
    total = sum(int(line.split(" ", 1)[0]) for line in lines)
    return "\n".join(lines) if 40 <= total <= 100 else ""


def fetch_mtgtop8_archetype(
    archetype: str,
    days: int,
    limit: int = MAX_ARCHETYPE_DECKS,
    *,
    force_refresh: bool = False,
) -> dict:
    """Fetch a small, cached Pioneer sample from MTGTop8's public pages."""
    limit = max(1, min(limit, MAX_ARCHETYPE_DECKS))
    cache_key = f"mtgtop8:{archetype_slug(archetype)}:{days}:{limit}"
    return cached_fetch(
        cache_key,
        ARCHETYPE_CACHE_TTL_SECONDS,
        lambda: fetch_mtgtop8_archetype_live(archetype, days, limit),
        force_refresh=force_refresh,
    )


def fetch_mtgtop8_archetype_live(archetype: str, days: int, limit: int) -> dict:
    """Serial, capped MTGTop8 lookup: index, one archetype page, then deck pages."""
    pioneer_index_url = f"{MTG_TOP8_URL}/format?f=PI"
    pioneer_index = fetch_html(pioneer_index_url)
    meta_id = mtgtop8_meta_window(pioneer_index, days)
    current_meta_id = mtgtop8_meta_window(pioneer_index, 14)
    archetype_index = pioneer_index
    if meta_id != current_meta_id:
        # An archetype that was quiet this fortnight may still have useful
        # lists in the requested two-month/current-year window.
        archetype_index = fetch_html(f"{pioneer_index_url}&meta={meta_id}")
    archetype_id = mtgtop8_archetype_id(archetype_index, archetype)
    list_url = f"{MTG_TOP8_URL}/archetype?a={archetype_id}&meta={meta_id}&f=PI"
    cutoff = datetime.now(timezone.utc).date().fromordinal(
        datetime.now(timezone.utc).date().toordinal() - days
    ).isoformat()
    entries = parse_mtgtop8_entries(fetch_html(list_url), cutoff, limit)
    decks: list[dict] = []
    for entry in entries:
        # MTGTop8 is a public HTML source rather than an API. Do not burst
        # requests: one selected archetype, one request at a time, then cache.
        time.sleep(MTG_TOP8_REQUEST_DELAY_SECONDS)
        try:
            deck_text = mtgtop8_mainboard(fetch_html(entry["source_url"]))
        except RuntimeError:
            continue
        if not deck_text:
            continue
        decks.append({
            **entry,
            "archetype": archetype,
            "source": "mtgtop8",
            "format": "pioneer",
            "deck_text": deck_text,
        })
    payload = {
        "schema_version": "1",
        "kind": "mtgtop8_pioneer_archetype",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "format": "pioneer",
        "source": "mtgtop8",
        "days": days,
        "events": [{
            "id": f"mtgtop8-{archetype_slug(archetype)}-{meta_id}",
            "url": list_url,
            "title": f"MTGTop8 · {archetype}",
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
    """Return a Moxfield-issued read-only identifier without browser credentials."""
    user_agent = os.environ.get("MOXFIELD_USER_AGENT", "").strip()
    if not user_agent:
        raise RuntimeError(
            "Moxfield is not configured. Set a Moxfield-issued MOXFIELD_USER_AGENT in .env."
        )
    return {"User-Agent": user_agent}


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


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    """Avoid transient port conflicts while the source watcher replaces us."""

    allow_reuse_address = True


class DelverHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format: str, *args) -> None:
        """Keep OAuth authorization codes out of the local development log."""
        redacted_args = tuple(
            re.sub(r"/api/chatgpt/callback\?[^\s\"]+", "/api/chatgpt/callback?redacted", str(argument))
            for argument in args
        )
        super().log_message(format, *redacted_args)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/chatgpt/status":
            return self._send_json(200, chatgpt_connection_status())
        if parsed.path == "/api/chatgpt/connect":
            return self._send_json(200, begin_chatgpt_sign_in())
        if parsed.path == "/api/chatgpt/models":
            try:
                return self._send_json(200, {"models": chatgpt_plan_models()})
            except RuntimeError as error:
                return self._send_json(502, {"error": str(error)})
        if parsed.path == "/api/chatgpt/callback":
            try:
                connection = complete_chatgpt_sign_in(parse_qs(parsed.query))
                account = connection.get("account") or "your ChatGPT account"
                return self._send_html(200, f"""<!doctype html><title>Delver connected</title>
<style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#090c11;color:#edf3fb;font:16px system-ui}}main{{max-width:430px;padding:36px;border:1px solid #344354;border-radius:12px;background:#111720}}h1{{margin-top:0;color:#b9f56a}}p{{color:#b8c4d1;line-height:1.55}}</style>
<main><h1>ChatGPT connected</h1><p>Delver can now use the plan token for Card Lab reviews as <strong>{escape(str(account))}</strong>.</p><p>You can close this tab and return to Card Lab.</p></main>""")
            except RuntimeError as error:
                return self._send_html(400, f"""<!doctype html><title>Delver connection failed</title>
<style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#090c11;color:#edf3fb;font:16px system-ui}}main{{max-width:430px;padding:36px;border:1px solid #6b3a35;border-radius:12px;background:#111720}}h1{{margin-top:0;color:#ff8860}}p{{color:#b8c4d1;line-height:1.55}}</style>
<main><h1>Couldn’t connect ChatGPT</h1><p>{escape(str(error))}</p><p>Return to Card Lab and try again.</p></main>""")
        if parsed.path == "/api/card-profiles":
            names = parse_qs(parsed.query).get("name", [])
            if not names:
                return self._send_json(400, {"error": "At least one card name is required"})
            try:
                return self._send_json(200, {"profiles": fetch_card_profiles(names)})
            except (RuntimeError, ValueError) as error:
                return self._send_json(502, {"error": str(error)})
        if parsed.path == "/api/card-alternatives":
            query = parse_qs(parsed.query)
            card_name = query.get("card", [""])[0].strip()
            archetype = query.get("archetype", [""])[0].strip()
            review_model = query.get("model", [""])[0].strip()
            force_refresh = query.get("refresh", [""])[0].lower() in {"1", "true", "yes"}
            excluded_cards = {name.strip() for name in query.get("exclude", []) if name.strip()}
            try:
                mainboard = json.loads(query.get("mainboard", ["[]"])[0])
            except json.JSONDecodeError:
                return self._send_json(400, {"error": "The Card Lab mainboard context is invalid"})
            if not isinstance(mainboard, list):
                return self._send_json(400, {"error": "The Card Lab mainboard context must be a list"})
            if not card_name or not archetype:
                return self._send_json(400, {"error": "A card name and archetype are required"})
            try:
                return self._send_json(200, fetch_card_alternatives(
                    card_name, archetype, excluded_cards=excluded_cards,
                    mainboard=mainboard, review_model=review_model or None,
                    force_refresh=force_refresh,
                ))
            except (RuntimeError, ValueError) as error:
                return self._send_json(502, {"error": str(error)})
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
        if parsed.path == "/api/content":
            query = parse_qs(parsed.query)
            archetype = query.get("name", [""])[0].strip()
            days = int(query.get("days", [90])[0])
            limit = int(query.get("limit", [MAX_ARCHETYPE_DECKS])[0])
            force_refresh = query.get("refresh", [""])[0].lower() in {"1", "true", "yes"}
            days = max(1, min(days, 90))
            if not archetype:
                return self._send_json(400, {"error": "An archetype name is required"})
            try:
                return self._send_json(200, fetch_mtgcontent_archetype(
                    archetype, days, limit, force_refresh=force_refresh
                ))
            except (RuntimeError, ValueError) as error:
                return self._send_json(502, {"error": str(error)})
        if parsed.path == "/api/mtgtop8":
            query = parse_qs(parsed.query)
            archetype = query.get("name", [""])[0].strip()
            days = int(query.get("days", [90])[0])
            limit = int(query.get("limit", [MAX_ARCHETYPE_DECKS])[0])
            force_refresh = query.get("refresh", [""])[0].lower() in {"1", "true", "yes"}
            days = max(1, min(days, 90))
            if not archetype:
                return self._send_json(400, {"error": "An archetype name is required"})
            try:
                return self._send_json(200, fetch_mtgtop8_archetype(
                    archetype, days, limit, force_refresh=force_refresh
                ))
            except (RuntimeError, ValueError) as error:
                return self._send_json(502, {"error": str(error)})
        if parsed.path == "/api/local-phoenix-archive":
            try:
                return self._send_json(200, fetch_local_phoenix_archive())
            except (RuntimeError, ValueError, zipfile.BadZipFile) as error:
                return self._send_json(404, {"error": str(error)})
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

    def _send_html(self, status: int, body: str):
        encoded = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    initialize_cache()
    server = None
    # The watcher starts a replacement process just before the old child has
    # released its socket on some macOS/Python combinations. Give that child a
    # short, bounded hand-off window instead of leaving the old code running.
    for attempt in range(20):
        try:
            server = ReusableThreadingHTTPServer(("127.0.0.1", 8080), DelverHandler)
            break
        except OSError as error:
            if error.errno != EADDRINUSE or attempt == 19:
                raise SystemExit(
                    "Delver is already running at http://127.0.0.1:8080 — open that URL instead."
                ) from error
            time.sleep(0.15)
    if server is None:
        raise SystemExit("Delver could not start its local server")
    print("Delver is available at http://127.0.0.1:8080")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        # watchfiles interrupts the child before starting its replacement.
        # Explicitly close the listening socket so the replacement can bind.
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
