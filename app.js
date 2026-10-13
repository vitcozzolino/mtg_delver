const sampleDatasets = {
  "Izzet Phoenix": {
    note: "Sample snapshot data — replace this adapter with verified recent tournament results before making metagame calls.",
    decks: [
      { name:"Baseline — Ledger tempo", event:"Pioneer Challenge", finish:"Top 8", date:"6 days ago", ageDays:6, cards:{"Arclight Phoenix":4,"Ledger Shredder":4,"Picklock Prankster":4,"Opt":4,"Consider":4,"Sleight of Hand":4,"Fiery Impulse":3,"Lightning Axe":2,"Dig Through Time":2,"Artist's Talent":2,"Spirebluff Canal":4,"Steam Vents":4,"Riverglide Pathway":4,"Island":6,"Hall of Storm Giants":1,"Otawara, Soaring City":1}},
      { name:"Pyromancer pressure", event:"Regional Challenge", finish:"1st", date:"11 days ago", ageDays:11, cards:{"Arclight Phoenix":4,"Ledger Shredder":4,"Picklock Prankster":4,"Young Pyromancer":3,"Opt":4,"Consider":4,"Sleight of Hand":4,"Fiery Impulse":3,"Lightning Axe":2,"Treasure Cruise":3,"Artist's Talent":1,"Spirebluff Canal":4,"Steam Vents":4,"Riverglide Pathway":4,"Island":6,"Hall of Storm Giants":1,"Otawara, Soaring City":1}},
      { name:"Treasure Cruise velocity", event:"RCQ", finish:"Top 4", date:"17 days ago", ageDays:17, cards:{"Arclight Phoenix":4,"Ledger Shredder":4,"Picklock Prankster":4,"Opt":4,"Consider":4,"Sleight of Hand":4,"Fiery Impulse":2,"Lightning Axe":3,"Treasure Cruise":3,"Artist's Talent":4,"Prismari Command":2,"Spirebluff Canal":4,"Steam Vents":4,"Riverglide Pathway":4,"Island":6,"Hall of Storm Giants":1,"Otawara, Soaring City":1}},
      { name:"Spell Pierce tempo", event:"Pioneer Challenge", finish:"Top 16", date:"23 days ago", ageDays:23, cards:{"Arclight Phoenix":4,"Ledger Shredder":4,"Picklock Prankster":4,"Opt":4,"Consider":4,"Sleight of Hand":4,"Fiery Impulse":3,"Lightning Axe":2,"Dig Through Time":2,"Spell Pierce":3,"Chart a Course":2,"Spirebluff Canal":4,"Steam Vents":4,"Riverglide Pathway":4,"Island":6,"Hall of Storm Giants":1,"Otawara, Soaring City":1}}
    ]
  },
  "Azorius Control": {
    note: "Sample snapshot data — replace this adapter with verified recent tournament results before making metagame calls.",
    decks: [
      { name: "Baseline — Teferi shell", event: "Regional Challenge", finish: "Top 8", date: "12 days ago", ageDays:12, cards: { "Portable Hole":2,"Get Lost":2,"No More Lies":4,"Three Steps Ahead":2,"Absorb":2,"Supreme Verdict":2,"Memory Deluge":2,"Teferi, Hero of Dominaria":3,"The Wandering Emperor":2,"Restless Anchorage":2,"Hallowed Fountain":4,"Deserted Beach":4,"Field of Ruin":2,"Plains":4,"Island":7,"Otawara, Soaring City":1,"Eiganjo, Seat of the Empire":1 } },
      { name: "Draw-go control", event: "Pioneer Challenge", finish: "1st", date: "8 days ago", ageDays:8, cards: { "Portable Hole":2,"Get Lost":3,"No More Lies":4,"Three Steps Ahead":3,"Absorb":2,"Supreme Verdict":2,"Memory Deluge":3,"Teferi, Hero of Dominaria":2,"The Wandering Emperor":2,"Shark Typhoon":2,"Restless Anchorage":2,"Hallowed Fountain":4,"Deserted Beach":4,"Field of Ruin":2,"Plains":4,"Island":6,"Otawara, Soaring City":1,"Eiganjo, Seat of the Empire":1 } },
      { name: "Emperor midrange", event: "RCQ", finish: "Top 4", date: "19 days ago", ageDays:19, cards: { "Portable Hole":3,"Get Lost":2,"No More Lies":4,"Three Steps Ahead":2,"Absorb":2,"Supreme Verdict":3,"Memory Deluge":2,"Teferi, Hero of Dominaria":2,"The Wandering Emperor":3,"Sunfall":1,"Restless Anchorage":3,"Hallowed Fountain":4,"Deserted Beach":4,"Field of Ruin":2,"Plains":4,"Island":6,"Otawara, Soaring City":1,"Eiganjo, Seat of the Empire":1 } },
      { name: "Anchorage pressure", event: "Pioneer Challenge", finish: "Top 16", date: "25 days ago", ageDays:25, cards: { "Portable Hole":2,"Get Lost":3,"No More Lies":4,"Three Steps Ahead":2,"Absorb":2,"Supreme Verdict":2,"Memory Deluge":2,"Teferi, Hero of Dominaria":2,"The Wandering Emperor":2,"Deduce":2,"Restless Anchorage":4,"Hallowed Fountain":4,"Deserted Beach":4,"Field of Ruin":2,"Plains":4,"Island":6,"Otawara, Soaring City":1,"Eiganjo, Seat of the Empire":1 } }
    ]
  },
  "Mono-Green Devotion": {
    note: "Sample snapshot data — replace this adapter with verified recent tournament results before making metagame calls.",
    decks: [
      { name:"Baseline — Nissa Devotion", event:"Regional Challenge", finish:"Top 8", date:"10 days ago", ageDays:10, cards:{"Llanowar Elves":4,"Elvish Mystic":4,"Old-Growth Troll":4,"Cavalier of Thorns":4,"Storm the Festival":4,"Nissa, Who Shakes the World":4,"Kiora, Behemoth Beckoner":4,"Nykthos, Shrine to Nyx":4,"Oath of Nissa":4,"Wolfwillow Haven":4,"Lair of the Hydra":2,"Boseiju, Who Endures":2,"Forest":12}},
      { name:"Leyline acceleration", event:"Pioneer Challenge", finish:"1st", date:"7 days ago", ageDays:7, cards:{"Llanowar Elves":4,"Elvish Mystic":4,"Old-Growth Troll":4,"Cavalier of Thorns":4,"Storm the Festival":4,"Nissa, Who Shakes the World":4,"Kiora, Behemoth Beckoner":3,"Leyline of the Guildpact":4,"Nykthos, Shrine to Nyx":4,"Oath of Nissa":4,"Lair of the Hydra":2,"Boseiju, Who Endures":2,"Forest":12}},
      { name:"Festival toolbox", event:"RCQ", finish:"Top 4", date:"18 days ago", ageDays:18, cards:{"Llanowar Elves":4,"Elvish Mystic":4,"Old-Growth Troll":4,"Cavalier of Thorns":4,"Storm the Festival":4,"Nissa, Who Shakes the World":4,"Kiora, Behemoth Beckoner":4,"Invasion of Ixalan":3,"Nykthos, Shrine to Nyx":4,"Oath of Nissa":4,"Lair of the Hydra":2,"Boseiju, Who Endures":2,"Forest":12}},
      { name:"Polukranos pressure", event:"Pioneer Challenge", finish:"Top 16", date:"24 days ago", ageDays:24, cards:{"Llanowar Elves":4,"Elvish Mystic":4,"Old-Growth Troll":4,"Cavalier of Thorns":4,"Storm the Festival":3,"Nissa, Who Shakes the World":4,"Kiora, Behemoth Beckoner":4,"Polukranos Reborn":3,"Nykthos, Shrine to Nyx":4,"Oath of Nissa":4,"Lair of the Hydra":2,"Boseiju, Who Endures":2,"Forest":12}}
    ]
  }
};

let datasets = {};
const TOPDECK_FEED_URL = '/api/pioneer';
const ARCHETYPE_FEED_URL = '/api/archetype';
const COMMUNITY_FEED_URL = '/api/community';
const MTGCONTENT_FEED_URL = '/api/content';
const MTGTOP8_FEED_URL = '/api/mtgtop8';
const LOCAL_PHOENIX_ARCHIVE_URL = '/api/local-phoenix-archive';
const CARD_PROFILE_URL = '/api/card-profiles';
const PUBLIC_FEED_URL = 'https://raw.githubusercontent.com/Pedrogush/MTGO_Tools_Data/data-publish/data/latest/mtgo-decklists/pioneer.json';
const selectArchetype = document.querySelector('#archetypeSelect');
const selectDeck = document.querySelector('#deckSelect');
const range = document.querySelector('#recencyRange');
const supplementLimit = document.querySelector('#supplementLimit');
const moxfieldEnabled = document.querySelector('#moxfieldEnabled');
const savedHtmlFiles = document.querySelector('#savedHtmlFiles');
const importSavedHtml = document.querySelector('#importSavedHtml');
const $ = (selector) => document.querySelector(selector);
const fallbackIsLand = (name) => /Forest|Island|Plains|Mountain|Swamp|Fountain|Beach|Field|Anchorage|Nykthos|Hydra|Boseiju|Otawara|Eiganjo|Canal|Vents|Pathway|Coast|Reef|Verge|Tomb|Sanctum|Courtyard|Ruins|Den|Castle|Cottage|Passage|Harbor|Garden|Catacomb|Cemetery|Fastland|Lair|Port|Mine|Temple|Shock|Triome/.test(name);
const cardPreview = $('#cardPreview');
const cardCache = new Map();
const cardProfiles = new Map();
let previewTimer;
let currentPreviewName = '';
let loadingMessageTimer;
const MIN_LOADING_FEEDBACK_MS = 800;
let archetypeLoadToken = 0;
const importedDecks = [];

function profileFor(name) { return cardProfiles.get(name); }
function isLand(name) {
  const profile = profileFor(name);
  return profile ? /\bLand\b/i.test(profile.type_line) : fallbackIsLand(name);
}
function primaryCardType(name) {
  const typeLine = profileFor(name)?.type_line?.toLowerCase() || '';
  if (typeLine.includes('land')) return 'land';
  if (typeLine.includes('creature')) return 'creature';
  if (typeLine.includes('planeswalker')) return 'planeswalker';
  if (typeLine.includes('artifact')) return 'artifact';
  if (typeLine.includes('enchantment')) return 'enchantment';
  if (typeLine.includes('instant')) return 'instant';
  if (typeLine.includes('sorcery')) return 'sorcery';
  return 'other';
}
function cardRoles(name) {
  const profile = profileFor(name);
  const type = primaryCardType(name);
  const text = (profile?.oracle_text || '').toLowerCase();
  const roles = new Set();
  if (type === 'land') roles.add('land');
  if (type === 'creature' || type === 'planeswalker') roles.add('threat');
  if (/counter target/.test(text)) roles.add('countermagic');
  if (/(destroy|exile) target|deals? \d+ damage to target|fight target/.test(text)) roles.add('removal');
  if (/draw (a|two|three|four) card|surveil|connive|loot/.test(text)) roles.add('selection');
  if (/mill|discard|from your graveyard|escape|delve/.test(text)) roles.add('graveyard');
  if (type === 'instant' || type === 'sorcery') roles.add('spell');
  return roles;
}
function sharedRoleCount(first, second) {
  let count = 0;
  first.forEach(role => { if (second.has(role)) count++; });
  return count;
}
function swapCompatibility(addName, cutName) {
  const addType = primaryCardType(addName);
  const cutType = primaryCardType(cutName);
  if (addType === 'land' || cutType === 'land') return -Infinity;
  const addRoles = cardRoles(addName);
  const cutRoles = cardRoles(cutName);
  const sharedRoles = sharedRoleCount(addRoles, cutRoles);
  if (!sharedRoles && addType !== cutType) return -Infinity;
  const addMana = Number(profileFor(addName)?.mana_value || 0);
  const cutMana = Number(profileFor(cutName)?.mana_value || 0);
  return sharedRoles * 100 + (addType === cutType ? 30 : 0) - Math.abs(addMana - cutMana) * 8;
}
async function ensureCardProfiles(archetype) {
  const data = datasets[archetype];
  if (!data) return;
  const missing = [...new Set(data.decks.flatMap(deck => Object.keys(deck.cards)).filter(name => !cardProfiles.has(name)))];
  for (let index = 0; index < missing.length; index += 75) {
    const params = new URLSearchParams();
    missing.slice(index, index + 75).forEach(name => params.append('name', name));
    const response = await fetch(`${CARD_PROFILE_URL}?${params}`, { cache: 'no-store' });
    if (!response.ok) throw new Error('Card type data was unavailable');
    const { profiles } = await response.json();
    Object.entries(profiles || {}).forEach(([name, profile]) => cardProfiles.set(name, profile));
  }
}

function setLoading(isLoading, title = 'Loading current decklists', detail = 'Connecting to the tournament sources…') {
  const overlay = $('#loadingOverlay');
  const progress = $('#syncProgress');
  const refresh = $('#refreshData');
  const analyze = $('#analyzeButton');
  clearInterval(loadingMessageTimer);
  overlay.hidden = !isLoading;
  progress.hidden = !isLoading;
  document.body.classList.toggle('is-loading', isLoading);
  document.querySelector('.app-shell').setAttribute('aria-busy', String(isLoading));
  [selectArchetype, selectDeck, range, supplementLimit, moxfieldEnabled, importSavedHtml, refresh, analyze].forEach(control => { control.disabled = isLoading; });
  refresh.classList.toggle('is-spinning', isLoading);
  if (!isLoading) return;
  $('#loadingTitle').textContent = title;
  $('#syncProgressLabel').textContent = 'Loading data…';
  const messages = [detail, 'Normalizing decklists and finding archetype matches…', 'Comparing the shared core against flex slots…'];
  let messageIndex = 0;
  $('#loadingDetail').textContent = messages[messageIndex];
  loadingMessageTimer = setInterval(() => {
    messageIndex = (messageIndex + 1) % messages.length;
    $('#loadingDetail').textContent = messages[messageIndex];
  }, 1800);
}

function parseMainboard(deckText) {
  const cards = {};
  for (const line of deckText.split(/\r?\n/)) {
    if (/^sideboard\s*$/i.test(line.trim())) break;
    const match = line.match(/^(\d+)\s+(.+)$/);
    if (match) {
      const name = match[2].trim();
      cards[name] = (cards[name] || 0) + Number(match[1]);
    }
  }
  return cards;
}
function formatGeneratedAt(timestamp) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(timestamp));
}
function buildLiveDatasets(feed) {
  const grouped = {};
  feed.events.flatMap(feedEvent => feedEvent.decks.map(deck => ({ ...deck, feedEvent }))).forEach(record => {
    if (!record.deck_text || !record.archetype || /^(unknown|ur|ub|wg|wubg|brg|g|b)$/i.test(record.archetype)) return;
    const cards = parseMainboard(record.deck_text);
    if (!Object.keys(cards).length) return;
    const ageDays = Math.max(0, Math.floor((Date.now() - new Date(`${record.date}T12:00:00Z`)) / 86400000));
    const archetype = record.archetype;
    grouped[archetype] ??= { note: '', source: 'MTGO / Videre Project feed', sourceUrl: PUBLIC_FEED_URL, decks: [] };
    grouped[archetype].decks.push({
      name: `${record.player} — ${record.result || 'published list'}`,
      event: typeof record.event === 'string' ? record.event : record.feedEvent.title,
      finish: record.result || 'Published list',
      date: record.date,
      ageDays,
      cards,
      player: record.player,
      sourceUrl: record.source_url || record.feedEvent.url,
      historicalArchive: Boolean(record.historical_archive)
    });
  });
  return Object.fromEntries(Object.entries(grouped)
    .filter(([, data]) => data.decks.length >= 2)
    .map(([archetype, data]) => {
      data.decks.sort((a, b) => b.date.localeCompare(a.date) || a.name.localeCompare(b.name));
      data.note = `Live MTGO results · ${data.decks.length} sampled lists in the feed · updated ${formatGeneratedAt(feed.generated_at)} · Data: Videre Project`;
      return [archetype, data];
    }));
}
function deckKey(deck) {
  return `${deck.date}|${deck.player || deck.name}|${Object.entries(deck.cards).sort(([a], [b]) => a.localeCompare(b)).map(([name, quantity]) => `${quantity} ${name}`).join('|')}`;
}

function htmlFragmentText(value) {
  const element = document.createElement('textarea');
  element.innerHTML = value.replace(/<[^>]+>/g, ' ');
  return element.value.replace(/\s+/g, ' ').trim();
}

function dateFromSavedPage(documentNode) {
  const datetime = documentNode.querySelector('time[datetime]')?.getAttribute('datetime');
  const matched = datetime?.match(/^\d{4}-\d{2}-\d{2}/)?.[0]
    || documentNode.body.textContent.match(/\b20\d{2}-\d{2}-\d{2}\b/)?.[0];
  return matched || new Date().toISOString().slice(0, 10);
}

function archetypeFromSavedPage(documentNode, fallbackArchetype) {
  const listingHeading = [...documentNode.querySelectorAll('h1, h2')]
    .map(element => element.textContent.replace(/\s+/g, ' ').trim())
    .map(text => text.match(/^Pioneer (.+?) decklists$/i)?.[1])
    .find(Boolean);
  if (listingHeading) return listingHeading;
  const archetypeLink = [...documentNode.querySelectorAll('a[href^="/Pioneer/"]')]
    .find(link => /^\/Pioneer\/[a-z0-9-]+$/i.test(link.getAttribute('href') || ''));
  const label = archetypeLink?.textContent.replace(/\s+/g, ' ').trim();
  return label || fallbackArchetype;
}

function deckLinksFromSavedPage(documentNode) {
  return [...documentNode.querySelectorAll('a[href^="/Pioneer/"]')]
    .map(link => link.getAttribute('href'))
    .filter(href => /-decklist-by-[^/]+$/i.test(href || ''))
    .map(href => `https://mtgdecks.net${href}`)
    .filter((href, index, links) => links.indexOf(href) === index);
}

function deckFromSavedMtgDecksPage(html, fileName, fallbackArchetype) {
  const documentNode = new DOMParser().parseFromString(html, 'text/html');
  const mainStart = html.search(/<h2[^>]*>\s*Main deck\s*<\/h2>/i);
  const sideStart = mainStart >= 0
    ? html.slice(mainStart).search(/<h2[^>]*>\s*Sideboard\s*<\/h2>/i)
    : -1;
  if (mainStart < 0 || sideStart < 0) return null;
  const mainHtml = html.slice(mainStart, mainStart + sideStart);
  const cards = {};
  for (const [, quantity, rawName] of mainHtml.matchAll(/<figcaption[^>]*>\s*<span[^>]*class=["']qty["'][^>]*>(\d+)<\/span>(.*?)<\/figcaption>/gis)) {
    const name = htmlFragmentText(rawName);
    if (name) cards[name] = (cards[name] || 0) + Number(quantity);
  }
  if (Object.values(cards).reduce((total, quantity) => total + quantity, 0) < 40) return null;
  const rawHeading = documentNode.querySelector('h1')?.textContent.replace(/\s+/g, ' ').trim();
  const player = documentNode.body.textContent.match(/\bBy\s+([^\n|]{2,70})/)?.[1]?.replace(/\s+/g, ' ').trim();
  const cleanFileName = fileName.replace(/\.(html?|txt)$/i, '').replace(/[-_]+/g, ' ');
  const date = dateFromSavedPage(documentNode);
  return {
    archetype: archetypeFromSavedPage(documentNode, fallbackArchetype),
    name: `${player || rawHeading || cleanFileName} — saved page`,
    event: 'Imported saved MTGDecks page',
    finish: 'Local import',
    date,
    ageDays: Math.max(0, Math.floor((Date.now() - new Date(`${date}T12:00:00Z`)) / 86400000)),
    cards,
    player: player || cleanFileName,
    sourceUrl: 'https://mtgdecks.net/',
  };
}

function mergeImportedDecks() {
  const additions = new Map();
  importedDecks.forEach(deck => {
    const archetype = deck.archetype || selectArchetype.value;
    if (!datasets[archetype]) {
      datasets[archetype] = {
        source: 'Local saved pages',
        sourceUrl: 'https://mtgdecks.net/',
        note: 'Locally imported saved MTGDecks pages',
        decks: [],
      };
    }
    const existing = new Set(datasets[archetype].decks.map(deckKey));
    if (existing.has(deckKey(deck))) return;
    datasets[archetype].decks.push(deck);
    additions.set(archetype, (additions.get(archetype) || 0) + 1);
  });
  additions.forEach((count, archetype) => {
    datasets[archetype].decks.sort((a, b) => b.date.localeCompare(a.date) || a.name.localeCompare(b.name));
    datasets[archetype].note += ` · +${count} locally imported saved page${count === 1 ? '' : 's'}`;
  });
  return additions;
}

async function importSavedHtmlPages(files) {
  if (!files.length) return;
  const fallbackArchetype = selectArchetype.value || 'Imported Pioneer deck';
  setLoading(true, 'Reading saved deck pages', 'Parsing local HTML in your browser…');
  try {
    const pages = await Promise.all([...files].map(async file => ({
      name: file.name,
      html: await file.text(),
    })));
    const parsedDecks = pages
      .map(page => deckFromSavedMtgDecksPage(page.html, page.name, fallbackArchetype))
      .filter(Boolean);
    const linkedDecks = pages.flatMap(page => {
      const documentNode = new DOMParser().parseFromString(page.html, 'text/html');
      return deckLinksFromSavedPage(documentNode);
    });
    if (!parsedDecks.length) {
      const uniqueLinks = [...new Set(linkedDecks)];
      $('#localImportStatus').textContent = uniqueLinks.length
        ? `Found ${uniqueLinks.length} deck links, but this overview page has no card lists. Save the individual deck pages, then import them together.`
        : 'No MTGDecks mainboards found. Select individual saved deck pages (not a Cloudflare challenge or overview page).';
      return;
    }
    const knownKeys = new Set(importedDecks.map(deckKey));
    const newDecks = parsedDecks.filter(deck => !knownKeys.has(deckKey(deck)));
    importedDecks.push(...newDecks);
    const additions = mergeImportedDecks();
    const preferredArchetype = newDecks[0]?.archetype || fallbackArchetype;
    populateArchetypes(preferredArchetype);
    try { await ensureCardProfiles(selectArchetype.value); } catch (error) { console.warn(error.message); }
    render();
    const added = [...additions.values()].reduce((total, count) => total + count, 0);
    $('#localImportStatus').textContent = added
      ? `Imported ${added} local deck page${added === 1 ? '' : 's'} into ${preferredArchetype}.`
      : 'Those saved deck pages were already part of this local session.';
  } finally {
    savedHtmlFiles.value = '';
    setLoading(false);
  }
}
async function enrichArchetype(archetype, days, { showLoading = false, forceRefresh = false } = {}) {
  const token = ++archetypeLoadToken;
  if (showLoading) setLoading(true, `Expanding ${archetype}`, 'Loading additional published tournament lists…');
  else $('#loadingDetail').textContent = 'Loading additional published tournament lists…';
  try {
    const refresh = forceRefresh ? '&refresh=1' : '';
    const sources = [{
      label: 'MTG Decklists',
      url: `${ARCHETYPE_FEED_URL}?name=${encodeURIComponent(archetype)}&days=${days}&limit=${supplementLimit.value}${refresh}`,
    }, {
      label: 'MTGContent',
      url: `${MTGCONTENT_FEED_URL}?name=${encodeURIComponent(archetype)}&days=${days}&limit=${supplementLimit.value}${refresh}`,
    }, {
      label: 'MTGTop8',
      url: `${MTGTOP8_FEED_URL}?name=${encodeURIComponent(archetype)}&days=${days}&limit=${supplementLimit.value}${refresh}`,
    }];
    if (archetype === 'Izzet Phoenix') sources.push({
      label: 'local Phoenix archive',
      url: LOCAL_PHOENIX_ARCHIVE_URL,
    });
    if (moxfieldEnabled.checked) sources.push({
      label: 'Moxfield community',
      url: `${COMMUNITY_FEED_URL}?name=${encodeURIComponent(archetype)}&days=${days}&limit=${supplementLimit.value}${refresh}`,
    });
    const results = await Promise.all(sources.map(async source => {
      const response = await fetch(source.url, { cache: 'no-store' });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(`${source.label}: ${body.error || 'source unavailable'}`);
      }
      return { ...source, feed: await response.json() };
    }).map(promise => promise.catch(error => ({ error }))));
    if (token !== archetypeLoadToken || !datasets[archetype]) return;
    const existing = new Set(datasets[archetype].decks.map(deckKey));
    const additionsBySource = [];
    const sourceErrors = [];
    results.forEach(result => {
      if (result.error) {
        sourceErrors.push(result.error.message);
        return;
      }
      const supplemental = buildLiveDatasets(result.feed)[archetype];
      if (!supplemental) return;
      const additions = supplemental.decks.filter(deck => !existing.has(deckKey(deck)));
      additions.forEach(deck => existing.add(deckKey(deck)));
      if (!additions.length) return;
      datasets[archetype].decks.push(...additions);
      const cacheSuffix = result.feed.cache?.status === 'hit' ? ' (local cache)' : result.feed.cache?.status === 'stale' ? ' (stale local cache)' : '';
      additionsBySource.push(`+${additions.length} ${result.label} lists${cacheSuffix}`);
    });
    datasets[archetype].decks.sort((a, b) => b.date.localeCompare(a.date) || a.name.localeCompare(b.name));
    if (additionsBySource.length) datasets[archetype].note += ` · ${additionsBySource.join(' · ')}`;
    const moxfieldError = sourceErrors.find(message => message.startsWith('Moxfield community:'));
    if (moxfieldError) datasets[archetype].note += ' · Moxfield community source needs local access configured';
    if (selectArchetype.value === archetype) {
      const selected = selectDeck.value;
      updateDeckChoices();
      selectDeck.value = selected;
      try { await ensureCardProfiles(archetype); } catch (error) { console.warn(error.message); }
      render();
    }
  } catch (error) {
    console.warn(error.message);
  } finally {
    if (showLoading && token === archetypeLoadToken) setLoading(false);
  }
}
async function loadLiveData({ forceRefresh = false } = {}) {
  const loadingStartedAt = Date.now();
  setLoading(true, 'Refreshing Pioneer intelligence', 'Fetching recent MTGO and tournament decklists…');
  $('#dataStatus').innerHTML = '<span class="status-dot is-loading"></span> Updating Pioneer data…';
  try {
    let feed;
    let sourceName = 'MTGO / Videre Project feed';
    let sourceUrl = PUBLIC_FEED_URL;
    let fallbackReason = '';
    try {
      const refresh = forceRefresh ? '&refresh=1' : '';
      const response = await fetch(`${TOPDECK_FEED_URL}?days=${range.value}${refresh}`, { cache: 'no-store' });
      if (!response.ok) throw new Error('TopDeck is not configured');
      feed = await response.json();
      if (feed.source === 'videre-spicerack') {
        const activeSources = new Set(feed.active_sources || []);
        sourceName = activeSources.has('spicerack') ? 'Videre MTGO + Spicerack' : 'Videre MTGO';
        sourceUrl = 'https://www.videreproject.com/';
      } else {
        sourceName = 'TopDeck.gg API';
        sourceUrl = 'https://topdeck.gg';
      }
    } catch (error) {
      fallbackReason = error.message || 'TopDeck was unavailable';
      const response = await fetch(PUBLIC_FEED_URL, { cache: 'no-store' });
      if (!response.ok) throw new Error(`Public feed responded ${response.status}`);
      feed = await response.json();
    }
    datasets = buildLiveDatasets(feed);
    mergeImportedDecks();
    if (!Object.keys(datasets).length) throw new Error('No usable Pioneer lists returned');
    range.min = 1; range.max = 90; range.value = feed.days;
    $('#rangeOutput').textContent = `${feed.days} days`;
    const sourceWarnings = Array.isArray(feed.warnings) && feed.warnings.length ? ` · Source warnings: ${feed.warnings.join(' | ')}` : '';
    const cacheNote = feed.cache?.status === 'hit' ? ' · served from local cache' : feed.cache?.status === 'stale' ? ' · showing stale local cache (source refresh failed)' : '';
    Object.values(datasets).forEach(data => { data.source = sourceName; data.sourceUrl = sourceUrl; data.note = `Live ${sourceName} results · ${data.decks.length} sampled lists in the feed · updated ${formatGeneratedAt(feed.generated_at)}${cacheNote}${fallbackReason ? ` · TopDeck fallback: ${fallbackReason}` : ''}${sourceWarnings}`; });
    $('#dataStatus').innerHTML = `<span class="status-dot"></span> Pioneer · ${fallbackReason ? 'public fallback' : sourceName}${feed.cache?.status === 'hit' ? ' · cached' : ''}`;
    populateArchetypes('Izzet Phoenix');
    await enrichArchetype(selectArchetype.value, Number(range.value), { forceRefresh });
    try { await ensureCardProfiles(selectArchetype.value); } catch (error) { console.warn(error.message); }
    render();
  } catch (error) {
    $('#dataStatus').innerHTML = '<span class="status-dot"></span> Pioneer · feed unavailable';
    $('#dataNote').textContent = `Couldn’t load the live feed: ${error.message}. Refresh to retry.`;
    $('#summaryGrid').innerHTML = '';
  } finally {
    const remainingFeedbackTime = MIN_LOADING_FEEDBACK_MS - (Date.now() - loadingStartedAt);
    if (remainingFeedbackTime > 0) await new Promise(resolve => setTimeout(resolve, remainingFeedbackTime));
    setLoading(false);
  }
}

function movePreview(event) {
  const gap = 18;
  const width = 245;
  const height = 345;
  const rect = event.currentTarget?.getBoundingClientRect?.();
  const x = Number.isFinite(event.clientX) ? event.clientX : (rect?.right || 12);
  const y = Number.isFinite(event.clientY) ? event.clientY : (rect?.top || 12);
  const left = x + gap + width > window.innerWidth ? x - width - gap : x + gap;
  const top = y + gap + height > window.innerHeight ? Math.max(12, y - height - gap) : y + gap;
  cardPreview.style.left = `${left}px`;
  cardPreview.style.top = `${top}px`;
}
async function showCardPreview(name, event) {
  clearTimeout(previewTimer);
  currentPreviewName = name;
  movePreview(event);
  cardPreview.classList.add('visible');
  cardPreview.setAttribute('aria-hidden', 'false');
  cardPreview.innerHTML = '<div class="preview-loading">Loading card…</div>';
  try {
    let card = cardCache.get(name);
    if (!card) {
      const response = await fetch(`https://api.scryfall.com/cards/named?exact=${encodeURIComponent(name)}`);
      if (!response.ok) throw new Error('Card lookup failed');
      card = await response.json();
      cardCache.set(name, card);
    }
    if (currentPreviewName !== name) return;
    const image = card.image_uris?.normal || card.card_faces?.[0]?.image_uris?.normal;
    if (!image) throw new Error('No preview image');
    cardPreview.innerHTML = `<img src="${image}" alt="${card.name}" />`;
  } catch {
    if (currentPreviewName !== name) return;
    cardPreview.innerHTML = `<div class="preview-error">Couldn’t load <strong>${name}</strong>.<br />Check your connection and try again.</div>`;
  }
}
function hideCardPreview() {
  previewTimer = setTimeout(() => {
    currentPreviewName = '';
    cardPreview.classList.remove('visible');
    cardPreview.setAttribute('aria-hidden', 'true');
  }, 90);
}
function cardLabel(name, className = '') {
  return `<span class="${className}" data-card-name="${name}" tabindex="0">${name}</span>`;
}
function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[character]));
}
function packageListRow({ deck, quantity }) {
  const source = deck.sourceUrl
    ? `<a class="package-source-link" href="${escapeHtml(deck.sourceUrl)}" target="_blank" rel="noreferrer">Source ↗</a>`
    : '<span class="package-source-label">Local archive</span>';
  return `<div class="package-list-row">
    <span class="package-list-copies">${quantity}×</span>
    <strong class="package-list-player">${escapeHtml(deck.player || deck.name)}</strong>
    <span class="package-list-event">${escapeHtml(deck.event)}</span>
    <span class="package-list-result">${escapeHtml(deck.finish)}</span>
    <time datetime="${escapeHtml(deck.date)}">${escapeHtml(deck.date)}</time>
    ${source}
  </div>`;
}
function bindCardPreviews() {
  document.querySelectorAll('[data-card-name]').forEach(element => {
    element.addEventListener('pointerenter', event => showCardPreview(element.dataset.cardName, event));
    element.addEventListener('pointermove', movePreview);
    element.addEventListener('pointerleave', hideCardPreview);
    element.addEventListener('focus', event => showCardPreview(element.dataset.cardName, event));
    element.addEventListener('blur', hideCardPreview);
  });
}

function populateArchetypes(preferredArchetype) {
  selectArchetype.innerHTML = '';
  Object.keys(datasets).sort().forEach(name => selectArchetype.add(new Option(name, name)));
  if (preferredArchetype && datasets[preferredArchetype]) selectArchetype.value = preferredArchetype;
  updateDeckChoices();
}
function updateDeckChoices() {
  selectDeck.innerHTML = '';
  datasets[selectArchetype.value].decks.forEach((deck, index) => selectDeck.add(new Option(deck.name, index)));
}
function updateCardLabLink(analysis) {
  const archetype = selectArchetype.value;
  $('#cardLabLink').href = archetype ? `./card-lab.html?archetype=${encodeURIComponent(archetype)}` : './card-lab.html';
  if (!analysis) return;
  sessionStorage.setItem('delver-card-lab-baseline', JSON.stringify({
    archetype,
    deckName: analysis.base.name,
    cards: Object.entries(analysis.base.cards)
      .map(([name, quantity]) => ({ name, quantity }))
      .sort((first, second) => first.name.localeCompare(second.name))
  }));
}
function getAnalysis() {
  const data = datasets[selectArchetype.value];
  const base = data.decks[Number(selectDeck.value)];
  const decks = data.decks.filter(deck => deck.historicalArchive || deck.ageDays <= Number(range.value));
  if (!decks.includes(base)) decks.unshift(base);
  const totals = {};
  decks.forEach(deck => Object.entries(deck.cards).forEach(([card, quantity]) => {
    totals[card] ??= { appearances: 0, copies: 0, byDeck: [] };
    totals[card].appearances++; totals[card].copies += quantity; totals[card].byDeck.push({ deck, quantity });
  }));
  const threshold = Math.ceil(decks.length * .67);
  const core = Object.entries(totals).filter(([card,info]) => info.appearances >= threshold && !isLand(card)).sort((a,b) => b[1].appearances - a[1].appearances || b[1].copies-a[1].copies);
  const variants = Object.entries(totals).filter(([card,info]) => info.appearances > 0 && info.appearances < threshold && !isLand(card));
  return { data, base, decks, totals, core, variants, threshold };
}
function renderDeck(analysis) {
  const { base, totals, threshold } = analysis;
  $('#baselineTitle').textContent = base.name;
  $('#baselineMeta').innerHTML = `${base.finish}<br>${base.date}${base.player ? `<br>${base.player}` : ''}`;
  const sectionOrder = ['Creatures', 'Planeswalkers', 'Instants', 'Sorceries', 'Artifacts', 'Enchantments', 'Other spells', 'Lands'];
  const sectionForType = {
    creature: 'Creatures', planeswalker: 'Planeswalkers', instant: 'Instants', sorcery: 'Sorceries',
    artifact: 'Artifacts', enchantment: 'Enchantments', land: 'Lands', other: 'Other spells',
  };
  const sections = Object.fromEntries(sectionOrder.map(section => [section, []]));
  Object.entries(base.cards)
    .sort((a,b) => a[0].localeCompare(b[0]))
    .forEach(([name, quantity]) => sections[sectionForType[primaryCardType(name)]].push([name, quantity]));
  $('#deckList').innerHTML = sectionOrder
    .filter(section => sections[section].length)
    .map(section => `<div class="section-name">${section}</div>${sections[section].map(([name,quantity]) => `<div class="deck-row ${totals[name].appearances >= threshold && section !== 'Lands' ? 'core' : ''} ${section === 'Lands' ? 'land' : ''}"><span class="quantity" title="Copies in your selected list">${quantity}×</span>${cardLabel(name, 'card-name')}<span class="delta" title="Sampled lists containing this card">${totals[name].appearances}/${analysis.decks.length} lists</span></div>`).join('')}`)
    .join('');
}
function renderAnalysis(analysis) {
  const totalCards = Object.values(analysis.base.cards).reduce((a,b)=>a+b,0);
  const flexInBase = Object.keys(analysis.base.cards).filter(card => !isLand(card) && analysis.totals[card].appearances < analysis.threshold).reduce((sum,card)=>sum+analysis.base.cards[card],0);
  const historicalCount = analysis.decks.filter(deck => deck.historicalArchive && deck.ageDays > Number(range.value)).length;
  const historicalNote = historicalCount ? ` · includes ${historicalCount} historical local Phoenix archive list${historicalCount === 1 ? '' : 's'}` : '';
  $('#dataNote').innerHTML = `<strong>${analysis.decks.length} sampled lists</strong> · window set to ${range.value} days${historicalNote} · ${analysis.data.note} · <a href="${analysis.data.sourceUrl}" target="_blank" rel="noreferrer">View source snapshot ↗</a>`;
  $('#summaryGrid').innerHTML = [[analysis.decks.length,'sampled lists'],[analysis.core.length,'backbone cards'],[flexInBase,'flex slots in baseline'],[totalCards,'cards indexed']].map(([value,label])=>`<div class="stat"><div class="stat-value">${value}</div><div class="stat-label">${label}</div></div>`).join('');
  $('#coreCards').innerHTML = analysis.core.map(([name, info]) => `<span class="signal-card" data-card-name="${name}" tabindex="0">${name}<b>${info.appearances}/${analysis.decks.length}</b></span>`).join('') || '<p>No shared nonland cards in the current sample.</p>';
  const packageGroups = analysis.variants.sort((a,b)=>b[1].appearances-a[1].appearances).slice(0,4);
  $('#packages').innerHTML = packageGroups.map(([name, info]) => {
    const lists = [...info.byDeck]
      .sort((first, second) => second.deck.date.localeCompare(first.deck.date) || first.deck.name.localeCompare(second.deck.name));
    return `<details class="package">
      <summary class="package-summary">
        <span class="package-title">
          ${cardLabel(name, 'package-card-name')}
          <span class="package-prevalence">${info.appearances}<span>/ ${analysis.decks.length}</span></span>
        </span>
        <span class="package-toggle">View ${info.appearances} list${info.appearances === 1 ? '' : 's'} <b aria-hidden="true">⌄</b></span>
      </summary>
      <div class="package-lists" aria-label="Lists using ${escapeHtml(name)}">
        <div class="package-list-header" aria-hidden="true"><span>Copies</span><span>Pilot</span><span>Event</span><span>Result</span><span>Date</span><span></span></div>
        ${lists.map(packageListRow).join('')}
      </div>
    </details>`;
  }).join('') || '<p class="package-info">The sample has no meaningful variant packages yet.</p>';
}
function renderExperiments(analysis) {
  const baseCards = Object.keys(analysis.base.cards);
  const experimentCards = [...new Set([
    ...baseCards,
    ...analysis.variants.map(([name]) => name),
  ])];
  if (experimentCards.some(name => !profileFor(name))) {
    $('#experiments').innerHTML = '<p class="package-info">Analyzing card roles before proposing swaps…</p>';
    return;
  }
  const candidates = analysis.variants
    .filter(([name]) => !baseCards.includes(name) && primaryCardType(name) !== 'land')
    .sort((a,b)=>b[1].appearances-a[1].appearances);
  const cuts = baseCards
    .filter(card => !isLand(card) && analysis.totals[card].appearances < analysis.threshold)
    .sort((a,b)=>analysis.totals[a].appearances-analysis.totals[b].appearances);
  const template = $('#experimentTemplate'); const target = $('#experiments'); target.innerHTML = '';
  const usedCuts = new Set();
  const experiments = candidates.map(([name, info]) => {
    const compatibleCuts = cuts
      .filter(cut => !usedCuts.has(cut))
      .map(cut => ({ cut, score: swapCompatibility(name, cut) }))
      .filter(({ score }) => Number.isFinite(score) && score >= 30)
      .sort((a, b) => b.score - a.score);
    if (!compatibleCuts.length) return null;
    const cut = compatibleCuts[0].cut;
    usedCuts.add(cut);
    const copies = Math.max(1, Math.min(
      analysis.base.cards[cut],
      Math.round(info.copies / info.appearances),
    ));
    return { name, info, cut, copies };
  }).filter(Boolean).slice(0, 3);
  experiments.forEach(({ name, info, cut, copies }, index) => {
    const fragment = template.content.cloneNode(true);
    fragment.querySelector('.experiment-number').textContent = String(index+1).padStart(2,'0');
    fragment.querySelector('.experiment-kicker').textContent = `SEEN IN ${info.appearances}/${analysis.decks.length} LISTS`;
    fragment.querySelector('h3').innerHTML = `Test ${cardLabel(name)}`;
    const sharedRoles = [...cardRoles(name)].filter(role => cardRoles(cut).has(role));
    const roleLabel = sharedRoles.length ? `${sharedRoles.join(' / ')} role` : 'same card type';
    fragment.querySelector('.experiment-reason').textContent = `${name} recurs as a ${roleLabel} alternative, at a compatible mana value. Test a small, reversible ${copies}-card package without changing the shared engine.`;
    fragment.querySelector('.swap-row').innerHTML = `<span class="cut" data-card-name="${cut}" tabindex="0">− ${copies}× ${cut}</span><span class="swap-arrow">→</span><span class="add" data-card-name="${name}" tabindex="0">+ ${copies}× ${name}</span>`;
    fragment.querySelector('.queue-button').addEventListener('click', event => { event.currentTarget.classList.toggle('queued'); event.currentTarget.innerHTML = event.currentTarget.classList.contains('queued') ? 'Queued ✓' : 'Queue test <span>+</span>'; });
    target.append(fragment);
  });
  if (!experiments.length) target.innerHTML = '<p class="package-info">No role-compatible swaps are present in the sample. Add more source lists to broaden the search.</p>';
}
function render() { const analysis = getAnalysis(); updateCardLabLink(analysis); renderDeck(analysis); renderAnalysis(analysis); renderExperiments(analysis); bindCardPreviews(); }
selectArchetype.addEventListener('change', async () => {
  updateDeckChoices();
  try { await ensureCardProfiles(selectArchetype.value); } catch (error) { console.warn(error.message); }
  render();
  await enrichArchetype(selectArchetype.value, Number(range.value), { showLoading: true });
});
selectDeck.addEventListener('change', render);
range.addEventListener('input', () => { $('#rangeOutput').textContent = `${range.value} days`; render(); });
range.addEventListener('change', () => {
  if (!$('#dataStatus').textContent.includes('public fallback')) loadLiveData();
});
supplementLimit.addEventListener('change', loadLiveData);
moxfieldEnabled.addEventListener('change', loadLiveData);
importSavedHtml.addEventListener('click', () => savedHtmlFiles.click());
savedHtmlFiles.addEventListener('change', () => importSavedHtmlPages(savedHtmlFiles.files));
$('#analyzeButton').addEventListener('click', render);
$('#refreshData').addEventListener('click', () => loadLiveData({ forceRefresh: true }));
$('#aboutButton').addEventListener('click', () => $('#aboutDialog').showModal());
$('#closeAbout').addEventListener('click', () => $('#aboutDialog').close());
loadLiveData();
