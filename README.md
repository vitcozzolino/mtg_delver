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

## TopDeck: 30–90 day data

The app includes a local-only TopDeck API adapter. It keeps your key on your machine rather than exposing it in browser JavaScript.

Save the key once (the prompt is hidden and writes a gitignored `.env` file):

```bash
uv run python setup_key.py
```

After that, starting the Python backend needs no export or key entry:

```bash
uv run delver
```

Then open [http://127.0.0.1:8080](http://127.0.0.1:8080), rather than opening `index.html` as a file. The server asks TopDeck for Pioneer events and their published decklists; the recency slider uses 1–90 days. The UI visibly credits TopDeck when that source is active.

The frontend remains plain HTML, CSS, and JavaScript. Python is only the local API server that keeps the TopDeck key out of the browser. `uv` creates an isolated `.venv` and locks the project in `uv.lock`; there are currently no third-party dependencies. Never commit a real key; `.env.example` is only a naming reference.

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
