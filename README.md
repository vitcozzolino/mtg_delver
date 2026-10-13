# Delver — Pioneer Deck Explorer

A no-build Pioneer deck explorer: a plain JavaScript frontend with a small local Python API adapter for TopDeck.

## What it does

- Loads the current seven-day Pioneer MTGO snapshot from the public, MIT-licensed [MTGO_Tools_Data](https://github.com/Pedrogush/MTGO_Tools_Data) feed. The page visibly reports the source timestamp and sampled-list count.
- Takes a baseline list and a group of same-archetype snapshots.
- Calls a nonland card **core** when it occurs in at least 67% of sampled lists.
- Marks cards below that threshold as flex/variant space.
- Suggests small, reversible tests: a recurring absent card replaces one of the baseline's least-shared nonland cards.

## Live data boundary

By default, the live loader fetches `data/latest/mtgo-decklists/pioneer.json` from the source's `data-publish` branch. The feed includes published MTGO deck text, player, event, result, archetype, and date; it currently exposes a seven-day window. The app filters to archetypes with at least two usable mainboards and treats each source update as a fresh snapshot.

## Live sources: Videre + Spicerack

The default backend now merges two evidence-grade sources: Videre's public MTGO deck API and Spicerack's public completed-tournament decklist API. It requests the selected 1–90 day Pioneer window, de-duplicates identical mainboards, and preserves each list's source URL. A temporarily slow or unavailable source is recorded as a warning without blocking results from the other source.

For the selected archetype, Delver also loads capped, cached supplemental lists from MTG Decklists, MTGContent's public Pioneer search, and MTGTop8's public Pioneer archetype pages. Source labels remain visible and identical decks are de-duplicated before comparison.

### MTGTop8 supplement

MTGTop8 is deliberately a small, cache-first supplement rather than a bulk crawler: Delver loads the selected Pioneer archetype only, requests no more than the selected **per-source cap** (5, 10, or 20) of individual deck pages, waits between those requests, and retains the result locally for six hours. Its archetype labels are mapped conservatively (for example, MTGTop8's **Arclight Phoenix** maps to Delver's **Izzet Phoenix**); an unmatched label is skipped rather than mixed into the wrong shell.

## Card Lab

Use **Card Lab** in the top navigation to research replacements for a Pioneer-legal card inside a specific archetype. It first applies hard filters: candidates must be Pioneer legal, color-compatible, close on the curve, and preserve a non-generic functional role (such as selection, removal, graveyard setup, or countermagic). For example, a removal spell cannot pass as an Opt replacement merely because both are instants.

When Card Lab is opened from the Deck Explorer, it carries the selected baseline mainboard across: its existing cards are excluded from suggestions and supplied as deck context. Click **Continue with ChatGPT** in Card Lab to connect an eligible ChatGPT plan through OpenAI's local OAuth flow. The local server keeps the resulting credentials in a gitignored owner-only file; browser JavaScript only receives connection status, never a token. After connecting, Card Lab loads the models actually available to that account and lets you select the review model. It then reviews only the bounded candidate set and returns structured recommend/situational/reject decisions with a concise deckbuilding rationale.

If you prefer API billing, `OPENAI_API_KEY` remains an optional fallback. Plan-backed reviews take priority when connected. Reviews are cached locally for seven days; heuristic candidates are cached for one day. If neither credential path is available, the page stays usable and visibly labels the results as heuristic-only.

## Import saved MTGDecks pages

The **Import saved HTML** control reads saved `.html` deck pages directly in the browser. It never sends those files anywhere and does not make a request to MTGDecks. Save one or more individual decklist pages in your browser, choose them together, and they become a local-only supplement to the relevant archetype for the current session.

An archetype overview page is useful for finding links, but it has no card lists to analyze; Delver will report how many deck links it found and ask for the individual saved deck pages.

### Local Phoenix archive

If `output/mtgdecks/decklists.zip` exists, Delver reads it locally and adds verified **Arclight Phoenix** mainboards to Izzet Phoenix only. All loader artifacts—including downloaded pages, progress state, ZIP archives, and AetherHub debug captures—live under `output/` and are ignored by Git. The archive never triggers a network request. It is explicitly marked as historical and is included alongside the chosen recent window so older, coherent Phoenix packages remain visible without being mistaken for current tournament data.

### Local loaders

Run each resumable loader through its dedicated uv command:

```bash
uv run load-mtgdecks
uv run load-aetherhub
```

`load-mtgdecks` writes to `output/mtgdecks/`; `load-aetherhub` writes to `output/aetherhub/` and opens an interactive Playwright browser. Do not run either loader concurrently with another instance of itself, since each source owns a single progress file.

## Moxfield community lists (optional)

Delver can add a separate, filtered Moxfield community sample for the selected archetype. It is never presented as tournament evidence. Leave **Moxfield community lists** enabled in the page and set this read-only identifier in your local `.env` file:

```bash
# Request this from Moxfield for read-only access. Do not use a personal
# browser-session token.
MOXFIELD_USER_AGENT=

# Quality guardrails for community lists; either threshold qualifies a list.
MOXFIELD_MIN_VIEWS=50
MOXFIELD_MIN_LIKES=2
```

The Moxfield integration uses its unofficial read API. It searches recent Pioneer deck names, rejects lists with fewer than 60 mainboard cards, applies the view/like thresholds, and then reads at most the selected **per-source cap** (5, 10, or 20). Results are cached locally for six hours. No credential is sent to browser JavaScript.

## TopDeck key (optional)

The app includes a local-only TopDeck API adapter. It keeps your key on your machine rather than exposing it in browser JavaScript.

Save the key once (the prompt is hidden and writes a gitignored `.env` file):

```bash
uv run python setup_key.py
```

After that, starting the Python backend needs no export or key entry:

```bash
uv run delver
```

Then open [http://127.0.0.1:8080](http://127.0.0.1:8080), rather than opening `index.html` as a file. `uv run delver` watches Python, HTML, CSS, JavaScript, and `pyproject.toml`, restarting the local server whenever they change; caches and loader output are ignored. The recency slider uses 1–90 days. The UI visibly credits the active data source. The key remains local for optional TopDeck support, but the default Pioneer sample is now Videre + Spicerack because TopDeck currently exposes too few public Pioneer decklists.

The frontend remains plain HTML, CSS, and JavaScript. Python is only the local API server that keeps the TopDeck key out of the browser. `uv` creates an isolated `.venv` and locks the project in `uv.lock`; the optional local loaders use `requests`, Beautiful Soup, and Playwright. TopDeck only contributes completed events with public decklists; when it has no usable Pioneer lists, the UI visibly falls back to the public MTGO feed. Never commit a real key; `.env.example` is only a naming reference.

Any importer should normalize records into this shape:

```js
{
  name: "Deck label",
  event: "Event",
  finish: "Top 8",
  date: "2026-10-01",
  cards: { "Card Name": 4 }
}
```

Useful next capabilities are: paste/import a user decklist, event/date/finish filters, sideboard analysis, card role taxonomy, and a live source adapter with date and legality validation.
