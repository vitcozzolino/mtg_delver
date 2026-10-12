import requests
import zipfile
import time
import random
import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


# ----------------------------------
# Configuration
# ----------------------------------

SEARCH_URL = "https://aetherhub.com/Decks/Pioneer/"

NAME_FILTER = "phoenix"
CONTENT_FILTER = "arclight phoenix"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output" / "aetherhub"
DOWNLOAD_DIR = OUTPUT_DIR / "decklists"
STATE_PATH = OUTPUT_DIR / "progress.json"
ZIP_PATH = OUTPUT_DIR / "decklists.zip"
DEBUG_HTML_PATH = OUTPUT_DIR / "debug.html"
DEBUG_SCREENSHOT_PATH = OUTPUT_DIR / "debug.png"

MIN_DELAY = 3.0
MAX_DELAY = 120.0
MAX_RETRIES = 5
MAX_RESULT_PAGES = 100

# Show browser so we can see what's happening
HEADLESS = False

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
delay = MIN_DELAY


# ----------------------------------
# Persistent state
# ----------------------------------

def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))

    return {
        "search_url": SEARCH_URL,
        "deck_links": [],
        "downloaded": {},
        "rejected": [],
        "search_complete": False
    }


state = load_state()

if state.get("search_url") != SEARCH_URL:
    raise RuntimeError("Search URL changed. Use a new progress file.")

state.setdefault("deck_links", [])
state.setdefault("downloaded", {})
state.setdefault("rejected", [])
state.setdefault("search_complete", False)


def save_state():
    temp = STATE_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    os.replace(temp, STATE_PATH)


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
# Extract Phoenix deck links
# ----------------------------------

def extract_deck_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a in soup.find_all("a", href=True):
        link = urljoin(base_url, a["href"])
        parsed = urlparse(link)
        path = parsed.path.lower()

        if (
            parsed.netloc.lower() in ("aetherhub.com", "www.aetherhub.com")
            and path.startswith("/deck/")
            and NAME_FILTER in path
        ):
            links.add(link)

    return links


# ----------------------------------
# Discover decks using Playwright
# ----------------------------------

if not state["search_complete"]:
    print("\nOpening AetherHub Pioneer listing...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            response = page.goto(
                SEARCH_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            print("HTTP status:", response.status if response else "Unknown")
            print("Page title:", page.title())
            print("Final URL:", page.url)

            print("Waiting for deck results...")

            try:
                page.locator('a[href*="/Deck/"]').first.wait_for(
                    state="attached",
                    timeout=15000
                )
            except PlaywrightTimeout:
                print("No deck links appeared within 15 seconds.")

            page.wait_for_timeout(3000)

            print("Total links:", page.locator("a[href]").count())

            all_deck_links = page.locator('a[href*="/Deck/"]')
            print("All deck links:", all_deck_links.count())

            for a in all_deck_links.all()[:10]:
                print("Example:", a.get_attribute("href"))

            # Save initial debug output
            DEBUG_HTML_PATH.write_text(
                page.content(),
                encoding="utf-8"
            )
            page.screenshot(
                path=str(DEBUG_SCREENSHOT_PATH),
                full_page=True
            )

            links = set(state["deck_links"])
            previous_found = None

            for page_number in range(MAX_RESULT_PAGES):
                page.wait_for_timeout(2000)

                found = extract_deck_links(page.content(), page.url)

                print(
                    f"Page {page_number + 1}: "
                    f"{len(found)} Phoenix links"
                )

                for link in sorted(found):
                    print(" ", link)

                if previous_found is not None and found == previous_found:
                    print("Results unchanged. Stopping pagination.")
                    break

                previous_found = found
                links.update(found)

                state["deck_links"] = sorted(links)
                save_state()

                next_button = page.locator(
                    'a[rel="next"], '
                    'a:has-text("Next"), '
                    'button:has-text("Next"), '
                    'a:has-text("›")'
                ).first

                if (
                    next_button.count() == 0
                    or not next_button.is_visible()
                    or not next_button.is_enabled()
                ):
                    print("No usable Next button found.")
                    break

                if next_button.get_attribute("aria-disabled") == "true":
                    break

                print("Moving to next page...")
                next_button.click()

                page.wait_for_timeout(3000)

            # Only mark complete when results were actually discovered
            if links:
                state["search_complete"] = True
                save_state()
            else:
                print(
                    "\nNo Phoenix links found. "
                    f"Check {DEBUG_HTML_PATH} and {DEBUG_SCREENSHOT_PATH}."
                )

        finally:
            browser.close()


# ----------------------------------
# Validate previous downloads
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

    if CONTENT_FILTER not in html.lower():
        print(f"Removing {filename}")
        path.unlink()
        del downloaded[link]
        rejected.add(link)

state["downloaded"] = downloaded
state["rejected"] = sorted(rejected)
save_state()


# ----------------------------------
# Download missing decks
# ----------------------------------

counter = max(
    (
        int(p.stem.split("_")[1])
        for p in DOWNLOAD_DIR.glob("deck_*.html")
        if p.stem.split("_")[1].isdigit()
    ),
    default=-1
) + 1

links = sorted(set(state["deck_links"]))

print(f"\nFound {len(links)} Phoenix deck URLs")
print(f"Already downloaded: {len(downloaded)}")

paused = False

for i, link in enumerate(links, 1):

    if link in downloaded:
        print(f"[{i}/{len(links)}] Already downloaded")
        continue

    if link in rejected:
        print(f"[{i}/{len(links)}] Previously rejected")
        continue

    print(f"[{i}/{len(links)}] Downloading {link}")

    try:
        response = get_page(link)

        if CONTENT_FILTER not in response.text.lower():
            rejected.add(link)
            state["rejected"] = sorted(rejected)
            save_state()

            print("Rejected: Arclight Phoenix not found")
            continue

        filename = f"deck_{counter:05d}.html"
        path = DOWNLOAD_DIR / filename
        temp = DOWNLOAD_DIR / f"{filename}.tmp"

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
        print(f"Stopping: {e}")
        paused = True
        break


# ----------------------------------
# Create ZIP
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


# ----------------------------------
# Summary
# ----------------------------------

print("\nDone!")
print(f"Decks discovered: {len(links)}")
print(f"Decks downloaded: {len(downloaded)}")
print(f"Decks rejected: {len(rejected)}")
print(f"Remaining: {len(set(links) - set(downloaded) - rejected)}")
print(f"ZIP: {ZIP_PATH}")

if paused:
    print("Rate limited. Run the script again later to resume.")
