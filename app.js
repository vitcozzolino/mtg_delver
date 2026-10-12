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
const PUBLIC_FEED_URL = 'https://raw.githubusercontent.com/Pedrogush/MTGO_Tools_Data/data-publish/data/latest/mtgo-decklists/pioneer.json';
const selectArchetype = document.querySelector('#archetypeSelect');
const selectDeck = document.querySelector('#deckSelect');
const range = document.querySelector('#recencyRange');
const supplementLimit = document.querySelector('#supplementLimit');
const $ = (selector) => document.querySelector(selector);
const isLand = (name) => /Forest|Island|Plains|Mountain|Swamp|Fountain|Beach|Field|Anchorage|Nykthos|Hydra|Boseiju|Otawara|Eiganjo|Canal|Vents|Pathway|Coast|Reef|Verge|Tomb|Sanctum|Courtyard|Ruins|Den|Castle|Cottage|Passage|Harbor|Garden|Catacomb|Cemetery|Fastland|Lair|Port|Mine|Temple|Shock|Triome/.test(name);
const cardPreview = $('#cardPreview');
const cardCache = new Map();
let previewTimer;
let currentPreviewName = '';
let loadingMessageTimer;
const MIN_LOADING_FEEDBACK_MS = 800;
let archetypeLoadToken = 0;

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
  [selectArchetype, selectDeck, range, supplementLimit, refresh, analyze].forEach(control => { control.disabled = isLoading; });
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
    if (match) cards[match[2].trim()] = Number(match[1]);
  }
  return cards;
}
function formatGeneratedAt(timestamp) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(timestamp));
}
function buildLiveDatasets(feed) {
  const grouped = {};
  feed.events.flatMap(event => event.decks.map(deck => ({ ...deck, event }))).forEach(record => {
    if (!record.deck_text || !record.archetype || /^(unknown|ur|ub|wg|wubg|brg|g|b)$/i.test(record.archetype)) return;
    const cards = parseMainboard(record.deck_text);
    if (!Object.keys(cards).length) return;
    const ageDays = Math.max(0, Math.floor((Date.now() - new Date(`${record.date}T12:00:00Z`)) / 86400000));
    const archetype = record.archetype;
    grouped[archetype] ??= { note: '', source: 'MTGO / Videre Project feed', sourceUrl: PUBLIC_FEED_URL, decks: [] };
    grouped[archetype].decks.push({
      name: `${record.player} — ${record.result || 'published list'}`,
      event: record.event,
      finish: record.result || 'Published list',
      date: record.date,
      ageDays,
      cards,
      player: record.player,
      sourceUrl: record.event.url
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
async function enrichArchetype(archetype, days, { showLoading = false } = {}) {
  const token = ++archetypeLoadToken;
  if (showLoading) setLoading(true, `Expanding ${archetype}`, 'Loading additional published tournament lists…');
  else $('#loadingDetail').textContent = 'Loading additional published tournament lists…';
  try {
    const response = await fetch(`${ARCHETYPE_FEED_URL}?name=${encodeURIComponent(archetype)}&days=${days}&limit=${supplementLimit.value}`, { cache: 'no-store' });
    if (!response.ok) throw new Error('Supplemental archetype source was unavailable');
    const supplemental = buildLiveDatasets(await response.json())[archetype];
    if (!supplemental || token !== archetypeLoadToken || !datasets[archetype]) return;
    const existing = new Set(datasets[archetype].decks.map(deckKey));
    const additions = supplemental.decks.filter(deck => !existing.has(deckKey(deck)));
    if (!additions.length) return;
    datasets[archetype].decks.push(...additions);
    datasets[archetype].decks.sort((a, b) => b.date.localeCompare(a.date) || a.name.localeCompare(b.name));
    datasets[archetype].note += ` · +${additions.length} additional published lists from MTG Decklists`;
    if (selectArchetype.value === archetype) {
      const selected = selectDeck.value;
      updateDeckChoices();
      selectDeck.value = selected;
      render();
    }
  } catch (error) {
    console.warn(error.message);
  } finally {
    if (showLoading && token === archetypeLoadToken) setLoading(false);
  }
}
async function loadLiveData() {
  const loadingStartedAt = Date.now();
  setLoading(true, 'Refreshing Pioneer intelligence', 'Fetching recent MTGO and tournament decklists…');
  $('#dataStatus').innerHTML = '<span class="status-dot is-loading"></span> Updating Pioneer data…';
  try {
    let feed;
    let sourceName = 'MTGO / Videre Project feed';
    let sourceUrl = PUBLIC_FEED_URL;
    let fallbackReason = '';
    try {
      const response = await fetch(`${TOPDECK_FEED_URL}?days=${range.value}`, { cache: 'no-store' });
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
    if (!Object.keys(datasets).length) throw new Error('No usable Pioneer lists returned');
    range.min = 1; range.max = 90; range.value = feed.days;
    $('#rangeOutput').textContent = `${feed.days} days`;
    const sourceWarnings = Array.isArray(feed.warnings) && feed.warnings.length ? ` · Source warnings: ${feed.warnings.join(' | ')}` : '';
    Object.values(datasets).forEach(data => { data.source = sourceName; data.sourceUrl = sourceUrl; data.note = `Live ${sourceName} results · ${data.decks.length} sampled lists in the feed · updated ${formatGeneratedAt(feed.generated_at)}${fallbackReason ? ` · TopDeck fallback: ${fallbackReason}` : ''}${sourceWarnings}`; });
    $('#dataStatus').innerHTML = `<span class="status-dot"></span> Pioneer · ${fallbackReason ? 'public fallback' : sourceName}`;
    populateArchetypes('Izzet Phoenix');
    await enrichArchetype(selectArchetype.value, Number(range.value));
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
function getAnalysis() {
  const data = datasets[selectArchetype.value];
  const base = data.decks[Number(selectDeck.value)];
  const decks = data.decks.filter(deck => deck.ageDays <= Number(range.value));
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
  const sections = { Spells: [], Lands: [] };
  Object.entries(base.cards).sort((a,b) => a[0].localeCompare(b[0])).forEach(([name, quantity]) => sections[isLand(name) ? 'Lands' : 'Spells'].push([name, quantity]));
  $('#deckList').innerHTML = Object.entries(sections).map(([section,cards]) => `<div class="section-name">${section}</div>${cards.map(([name,quantity]) => `<div class="deck-row ${totals[name].appearances >= threshold && section !== 'Lands' ? 'core' : ''} ${section === 'Lands' ? 'land' : ''}"><span class="quantity" title="Copies in your selected list">${quantity}×</span>${cardLabel(name, 'card-name')}<span class="delta" title="Sampled lists containing this card">${totals[name].appearances}/${analysis.decks.length} lists</span></div>`).join('')}`).join('');
}
function renderAnalysis(analysis) {
  const totalCards = Object.values(analysis.base.cards).reduce((a,b)=>a+b,0);
  const flexInBase = Object.keys(analysis.base.cards).filter(card => !isLand(card) && analysis.totals[card].appearances < analysis.threshold).reduce((sum,card)=>sum+analysis.base.cards[card],0);
  $('#dataNote').innerHTML = `<strong>${analysis.decks.length} sampled lists</strong> · window set to ${range.value} days · ${analysis.data.note} · <a href="${analysis.data.sourceUrl}" target="_blank" rel="noreferrer">View source snapshot ↗</a>`;
  $('#summaryGrid').innerHTML = [[analysis.decks.length,'sampled lists'],[analysis.core.length,'backbone cards'],[flexInBase,'flex slots in baseline'],[totalCards,'cards indexed']].map(([value,label])=>`<div class="stat"><div class="stat-value">${value}</div><div class="stat-label">${label}</div></div>`).join('');
  $('#coreCards').innerHTML = analysis.core.map(([name, info]) => `<span class="signal-card" data-card-name="${name}" tabindex="0">${name}<b>${info.appearances}/${analysis.decks.length}</b></span>`).join('') || '<p>No shared nonland cards in the current sample.</p>';
  const packageGroups = analysis.variants.sort((a,b)=>b[1].appearances-a[1].appearances).slice(0,4);
  $('#packages').innerHTML = packageGroups.map(([name,info]) => `<div class="package"><div class="package-name">${cardLabel(name)} <span class="signal-card flex"><b>${info.appearances}/${analysis.decks.length}</b></span></div><p class="package-info">${info.byDeck.map(({deck,quantity})=>`${quantity}× in ${deck.name}`).join(' · ')}</p></div>`).join('') || '<p class="package-info">The sample has no meaningful variant packages yet.</p>';
}
function renderExperiments(analysis) {
  const baseCards = Object.keys(analysis.base.cards);
  const candidates = analysis.variants.filter(([name]) => !baseCards.includes(name)).sort((a,b)=>b[1].appearances-a[1].appearances).slice(0,3);
  const cuts = baseCards.filter(card => !isLand(card) && analysis.totals[card].appearances < analysis.threshold).sort((a,b)=>analysis.totals[a].appearances-analysis.totals[b].appearances);
  const template = $('#experimentTemplate'); const target = $('#experiments'); target.innerHTML = '';
  candidates.forEach(([name, info], index) => {
    const cut = cuts[index] || Object.keys(analysis.base.cards).find(card => !isLand(card) && analysis.totals[card].appearances === analysis.threshold);
    const fragment = template.content.cloneNode(true);
    fragment.querySelector('.experiment-number').textContent = String(index+1).padStart(2,'0');
    fragment.querySelector('.experiment-kicker').textContent = `SEEN IN ${info.appearances}/${analysis.decks.length} LISTS`;
    fragment.querySelector('h3').innerHTML = `Test ${cardLabel(name)}`;
    fragment.querySelector('.experiment-reason').textContent = `${name} is the clearest recurring alternative absent from your baseline. Start with a small, reversible package before changing the engine.`;
    fragment.querySelector('.swap-row').innerHTML = `<span class="cut"${cut ? ` data-card-name="${cut}" tabindex="0"` : ''}>− ${cut || 'flex slot'}</span><span class="swap-arrow">→</span><span class="add" data-card-name="${name}" tabindex="0">+ ${name}</span>`;
    fragment.querySelector('.queue-button').addEventListener('click', event => { event.currentTarget.classList.toggle('queued'); event.currentTarget.innerHTML = event.currentTarget.classList.contains('queued') ? 'Queued ✓' : 'Queue test <span>+</span>'; });
    target.append(fragment);
  });
  if (!candidates.length) target.innerHTML = '<p class="package-info">No new packages are present in the sample. Add more source lists to broaden the search.</p>';
}
function render() { const analysis = getAnalysis(); renderDeck(analysis); renderAnalysis(analysis); renderExperiments(analysis); bindCardPreviews(); }
selectArchetype.addEventListener('change', async () => {
  updateDeckChoices();
  render();
  await enrichArchetype(selectArchetype.value, Number(range.value), { showLoading: true });
});
selectDeck.addEventListener('change', render);
range.addEventListener('input', () => { $('#rangeOutput').textContent = `${range.value} days`; render(); });
range.addEventListener('change', () => {
  if (!$('#dataStatus').textContent.includes('public fallback')) loadLiveData();
});
supplementLimit.addEventListener('change', loadLiveData);
$('#analyzeButton').addEventListener('click', render);
$('#refreshData').addEventListener('click', loadLiveData);
$('#aboutButton').addEventListener('click', () => $('#aboutDialog').showModal());
$('#closeAbout').addEventListener('click', () => $('#aboutDialog').close());
loadLiveData();
