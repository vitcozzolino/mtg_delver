import requests
import zipfile
import time
import random
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

URL = "https://mtgdecks.net/Pioneer/izzet-phoenix/min_ranking:1/platform:tabletop/deck_type:BO3"

DOWNLOAD_DIR = Path("decklists")
ZIP_PATH = Path("decklists.zip")
STATE_PATH = Path("progress.json")

KEYWORD = "arclight phoenix"

MIN_DELAY = 3.0
MAX_DELAY = 120.0
MAX_RETRIES = 5

DOWNLOAD_DIR.mkdir(exist_ok=True)

session = requests.Session()
delay = MIN_DELAY


# ----------------------------------
# Persistent state
# ----------------------------------

def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))

    return {
        "pages_scanned": [],
        "pages_pending": [URL],
        "deck_links": [],
        "downloaded": {},
        "rejected": []
    }


def save_state():
    temp = STATE_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    os.replace(temp, STATE_PATH)


state = load_state()
state.setdefault("pages_scanned", [])
state.setdefault("pages_pending", [URL])
state.setdefault("deck_links", [])
state.setdefault("downloaded", {})
state.setdefault("rejected", [])


# ----------------------------------
# Adaptive requests
# ----------------------------------

def get_page(url):
    global delay

    for attempt in range(MAX_RETRIES):
        time.sleep(delay + random.uniform(0, 1))

        try:
            response = session.get(url, timeout=30)

        except requests.RequestException as e:
            delay = min(delay * 2, MAX_DELAY)
            print(f"Network error: {e}")
            continue

        if response.status_code == 429:
            delay = min(delay * 2, MAX_DELAY)

            retry_after = response.headers.get("Retry-After")

            if retry_after:
                try:
                    wait = float(retry_after)
                except ValueError:
                    try:
                        retry_date = parsedate_to_datetime(retry_after)
                        wait = (
                            retry_date -
                            datetime.now(timezone.utc)
                        ).total_seconds()
                    except (TypeError, ValueError, OverflowError):
                        wait = 0

                delay = max(delay, max(0, wait))

            print(
                f"429: attempt {attempt + 1}/{MAX_RETRIES}, "
                f"next wait {delay:.1f}s"
            )
            continue

        response.raise_for_status()

        if "cf-chl" in response.text.lower():
            raise RuntimeError("Cloudflare challenge detected.")

        delay = max(MIN_DELAY, delay * 0.9)
        return response

    raise RuntimeError(f"Maximum retries exceeded: {url}")


# ----------------------------------
# Discover pagination and deck links
# ----------------------------------

print("Discovering pages and decklists...")

scanned = set(state["pages_scanned"])
pending = set(state["pages_pending"])
deck_links = set(state["deck_links"])

if not scanned and not pending:
    pending.add(URL)

try:
    while pending:
        page = sorted(pending)[0]

        if page in scanned:
            pending.remove(page)
            continue

        print(f"Scanning: {page}")

        response = get_page(page)
        soup = BeautifulSoup(response.text, "html.parser")

        for a in soup.find_all("a", href=True):
            link = urljoin(response.url, a["href"])
            path = urlparse(link).path

            if (
                path.startswith("/Pioneer/izzet-phoenix/page:")
                and "/min_ranking:1/platform:tabletop/deck_type:BO3" in path
                and link not in scanned
            ):
                pending.add(link)

            if (
                path.startswith("/Pioneer/")
                and "-decklist-by-" in path
            ):
                deck_links.add(link)

        scanned.add(page)
        pending.discard(page)

        state["pages_scanned"] = sorted(scanned)
        state["pages_pending"] = sorted(pending)
        state["deck_links"] = sorted(deck_links)
        save_state()

except (requests.RequestException, RuntimeError) as e:
    print(f"Pagination paused: {e}")

print(f"Pages scanned: {len(scanned)}")
print(f"Decklists discovered: {len(deck_links)}")


# ----------------------------------
# Validate existing downloads
# ----------------------------------

downloaded = state["downloaded"]
rejected = set(state["rejected"])

print("\nChecking previously downloaded HTML...")

for link, filename in list(downloaded.items()):
    path = DOWNLOAD_DIR / filename

    if not path.exists():
        del downloaded[link]
        continue

    html = path.read_text(encoding="utf-8", errors="ignore")

    if KEYWORD not in html.lower():
        print(f"Removing {filename} (keyword missing)")
        path.unlink()
        del downloaded[link]
        rejected.add(link)

state["downloaded"] = downloaded
state["rejected"] = sorted(rejected)
save_state()


# ----------------------------------
# Download and filter decklists
# ----------------------------------

counter = max(
    (
        int(p.stem.split("_")[1])
        for p in DOWNLOAD_DIR.glob("deck_*.html")
        if p.stem.split("_")[1].isdigit()
    ),
    default=-1
) + 1

print("\nDownloading decklists...")

paused = False

for i, link in enumerate(sorted(deck_links), 1):

    if link in downloaded:
        print(f"[{i}/{len(deck_links)}] Already downloaded")
        continue

    if link in rejected:
        print(f"[{i}/{len(deck_links)}] Previously rejected")
        continue

    print(f"[{i}/{len(deck_links)}] Downloading {link}")

    try:
        response = get_page(link)

        # Only save pages containing Arclight Phoenix
        if KEYWORD not in response.text.lower():
            print(f"Rejected (no {KEYWORD}): {link}")

            rejected.add(link)
            state["rejected"] = sorted(rejected)
            save_state()
            continue

        filename = f"deck_{counter:05d}.html"
        path = DOWNLOAD_DIR / filename
        temp = DOWNLOAD_DIR / f"{filename}.tmp"

        # Atomic HTML write
        temp.write_bytes(response.content)
        os.replace(temp, path)

        downloaded[link] = filename
        state["downloaded"] = downloaded
        save_state()

        counter += 1
        print(f"Saved {filename}")

    except requests.RequestException as e:
        print(f"Request failed: {e}")
        continue

    except RuntimeError as e:
        print(f"Stopping downloads: {e}")
        paused = True
        break


# ----------------------------------
# Build ZIP from accepted HTML files
# ----------------------------------

print("\nCreating ZIP...")

temp_zip = ZIP_PATH.with_suffix(".zip.tmp")

with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as z:
    for link, filename in sorted(downloaded.items()):
        path = DOWNLOAD_DIR / filename

        if path.exists():
            z.write(path, arcname=filename)

    z.writestr(
        "urls.txt",
        "\n".join(
            f"{filename} {link}"
            for link, filename in sorted(downloaded.items())
            if (DOWNLOAD_DIR / filename).exists()
        )
    )

os.replace(temp_zip, ZIP_PATH)

print("\nDone!")
print(f"Pages scanned: {len(scanned)}")
print(f"Decklists discovered: {len(deck_links)}")
print(f"Accepted decklists: {len(downloaded)}")
print(f"Rejected decklists: {len(rejected)}")
print(f"Remaining: {len(deck_links - set(downloaded) - rejected)}")
print(f"ZIP: {ZIP_PATH}")

if paused:
    print("Rate limited. Run the script again later to resume.")