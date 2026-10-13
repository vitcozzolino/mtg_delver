const CARD_ALTERNATIVES_URL = '/api/card-alternatives';
const LAB_ARCHETYPES = {
  'Izzet Phoenix': ['Arclight Phoenix', 'Artist\'s Talent', 'Consider', 'Fiery Impulse', 'Lightning Axe', 'Opt', 'Picklock Prankster', 'Sleight of Hand', 'Spell Pierce', 'Treasure Cruise'],
  'Azorius Control': ['Absorb', 'Get Lost', 'Memory Deluge', 'No More Lies', 'Supreme Verdict', 'Teferi, Hero of Dominaria', 'The Wandering Emperor'],
  'Mono-Green Devotion': ['Cavalier of Thorns', 'Elvish Mystic', 'Kiora, Behemoth Beckoner', 'Llanowar Elves', 'Nissa, Who Shakes the World', 'Old-Growth Troll', 'Storm the Festival'],
  'Greasefang': ['Esika\'s Chariot', 'Greasefang, Okiba Boss', 'Parhelion II', 'Raffine\'s Informant', 'Satyr Wayfinder'],
  'Lotus Field': ['Hidden Strings', 'Lotus Field', 'Pore Over the Pages', 'Strict Proctor', 'Sylvan Scrying'],
};
const archetypeSelect = document.querySelector('#labArchetype');
const cardInput = document.querySelector('#labCard');
const cardExamples = document.querySelector('#labCardExamples');
const labStatus = document.querySelector('#labStatus');
const labResults = document.querySelector('#labResults');
const cardPreview = document.querySelector('#cardPreview');
const baselineContext = document.querySelector('#baselineContext');
const chatgptConnection = document.querySelector('#chatgptConnection');
const connectChatGPTButton = document.querySelector('#connectChatGPT');
const chatgptModelWrap = document.querySelector('#chatgptModelWrap');
const chatgptModel = document.querySelector('#chatgptModel');
const cardCache = new Map();
let previewTimer;
let currentPreviewName = '';
let baseline = null;
let chatgptPollTimer = null;
let chatgptModelsLoaded = false;
const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, character => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
}[character]));

function populateArchetypes() {
  Object.keys(LAB_ARCHETYPES).forEach(name => archetypeSelect.add(new Option(name, name)));
  const requested = new URLSearchParams(location.search).get('archetype');
  if (requested && LAB_ARCHETYPES[requested]) archetypeSelect.value = requested;
  populateExamples();
}
function populateExamples() {
  const sourceCards = baseline?.archetype === archetypeSelect.value && baseline.cards?.length
    ? baseline.cards.map(card => typeof card === 'string' ? card : card.name).filter(Boolean)
    : LAB_ARCHETYPES[archetypeSelect.value];
  cardExamples.innerHTML = sourceCards
    .map(name => `<option value="${escapeHtml(name)}"></option>`).join('');
}
function loadBaseline() {
  try {
    const saved = JSON.parse(sessionStorage.getItem('delver-card-lab-baseline') || 'null');
    if (saved && Array.isArray(saved.cards) && typeof saved.archetype === 'string') {
      baseline = {
        ...saved,
        cards: saved.cards.map(card => typeof card === 'string' ? { name: card, quantity: 1 } : card)
      };
    }
  } catch { baseline = null; }
  baselineContext.textContent = 'Open Card Lab from the Deck Explorer to use its selected mainboard as the replacement context.';
  baselineContext.classList.remove('active');
  if (baseline?.archetype === archetypeSelect.value) {
    baselineContext.textContent = `Using ${baseline.deckName || 'the selected'} mainboard: existing cards are excluded from replacement suggestions.`;
    baselineContext.classList.add('active');
  }
}
function scoreLabel(score) {
  if (score >= 80) return 'strong fit';
  if (score >= 60) return 'good fit';
  return 'situational fit';
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
    cardPreview.innerHTML = `<img src="${image}" alt="${escapeHtml(card.name)}" />`;
  } catch {
    if (currentPreviewName !== name) return;
    cardPreview.innerHTML = `<div class="preview-error">Couldn’t load <strong>${escapeHtml(name)}</strong>.</div>`;
  }
}
function hideCardPreview() {
  previewTimer = setTimeout(() => {
    currentPreviewName = '';
    cardPreview.classList.remove('visible');
    cardPreview.setAttribute('aria-hidden', 'true');
  }, 90);
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
function renderChatGPTStatus(status) {
  if (status?.connected) {
    const account = status.account ? ` as ${status.account}` : '';
    chatgptConnection.textContent = `ChatGPT plan connected${account}. Card Lab will use it before any API key.`;
    connectChatGPTButton.textContent = 'ChatGPT connected';
    connectChatGPTButton.disabled = true;
    connectChatGPTButton.classList.add('connected');
    return;
  }
  chatgptModelsLoaded = false;
  chatgptModelWrap.hidden = true;
  chatgptConnection.textContent = 'Heuristic scoring is ready. Connect ChatGPT to add a plan-backed second opinion.';
  connectChatGPTButton.textContent = 'Continue with ChatGPT';
  connectChatGPTButton.disabled = false;
  connectChatGPTButton.classList.remove('connected');
}
async function loadChatGPTModels(preferredModel) {
  try {
    const response = await fetch('/api/chatgpt/models', { cache: 'no-store' });
    const payload = await response.json();
    if (!response.ok || !Array.isArray(payload.models)) throw new Error(payload.error || 'Model catalog unavailable');
    const previouslySelected = sessionStorage.getItem('delver-chatgpt-model');
    const selected = payload.models.some(model => model.slug === previouslySelected)
      ? previouslySelected
      : payload.models.some(model => model.slug === preferredModel) ? preferredModel : payload.models[0]?.slug;
    chatgptModel.innerHTML = payload.models.map(model => `<option value="${escapeHtml(model.slug)}">${escapeHtml(model.display_name)}</option>`).join('');
    if (selected) chatgptModel.value = selected;
    chatgptModelWrap.hidden = false;
    chatgptModelsLoaded = true;
  } catch (error) {
    chatgptConnection.textContent = `ChatGPT connected, but its model catalog could not load: ${error.message || 'unknown error'}`;
  }
}
async function loadChatGPTStatus() {
  try {
    const response = await fetch('/api/chatgpt/status', { cache: 'no-store' });
    if (!response.ok) throw new Error('Status unavailable');
    const status = await response.json();
    renderChatGPTStatus(status);
    if (status.connected && !chatgptModelsLoaded) loadChatGPTModels(status.preferred_model);
    return status;
  } catch {
    chatgptConnection.textContent = 'ChatGPT connection status is unavailable while the local server reloads.';
    return { connected: false };
  }
}
async function connectChatGPT() {
  connectChatGPTButton.disabled = true;
  connectChatGPTButton.textContent = 'Opening ChatGPT…';
  try {
    const response = await fetch('/api/chatgpt/connect', { cache: 'no-store' });
    const payload = await response.json();
    if (!response.ok || !payload.authorize_url) throw new Error(payload.error || 'Could not begin ChatGPT sign-in');
    window.open(payload.authorize_url, '_blank', 'noopener');
    chatgptConnection.textContent = 'Finish the ChatGPT sign-in in the new tab. This page will update automatically.';
    clearInterval(chatgptPollTimer);
    let checks = 0;
    chatgptPollTimer = setInterval(async () => {
      checks += 1;
      const status = await loadChatGPTStatus();
      if (status.connected || checks >= 80) clearInterval(chatgptPollTimer);
    }, 1500);
  } catch (error) {
    chatgptConnection.textContent = error.message || 'Could not begin ChatGPT sign-in.';
    connectChatGPTButton.disabled = false;
    connectChatGPTButton.textContent = 'Continue with ChatGPT';
  }
}
function renderResults(payload) {
  const source = payload.source_card;
  const sourceTitle = document.querySelector('#sourceCardName');
  sourceTitle.textContent = source.name;
  sourceTitle.dataset.cardName = source.name;
  sourceTitle.tabIndex = 0;
  document.querySelector('#sourceCardMeta').textContent = `${source.type_line} · mana value ${source.mana_value} · roles: ${source.roles.join(', ') || 'none detected'}`;
  document.querySelector('#strategyName').textContent = payload.strategy;
  document.querySelector('#winPlan').textContent = payload.win_plan;
  document.querySelector('#labMethod').textContent = payload.method;
  const reviewNote = document.querySelector('#aiReviewNote');
  if (payload.ai_review?.status === 'complete') {
    const provider = payload.ai_review.provider_label || 'AI';
    reviewNote.textContent = `${provider} deckbuilding review · ${payload.ai_review.model} · ${payload.ai_review.reviewed} candidates assessed, ${payload.ai_review.rejected} rejected.`;
    reviewNote.className = 'ai-review-note complete';
  } else if (payload.ai_review?.status === 'unavailable') {
    reviewNote.textContent = `Heuristic-only results · deckbuilding review unavailable: ${payload.ai_review.detail}`;
    reviewNote.className = 'ai-review-note unavailable';
  } else {
    reviewNote.textContent = '';
    reviewNote.className = 'ai-review-note';
  }
  document.querySelector('#alternativeGrid').innerHTML = payload.alternatives.length
    ? payload.alternatives.map(card => `<article class="alternative-card">
        <div class="alternative-card-top">
          <div><p class="alternative-score">${escapeHtml(card.ai_review?.verdict || scoreLabel(card.score))} · ${escapeHtml(card.ai_review?.score ?? card.score)}</p><h3><a data-card-name="${escapeHtml(card.name)}" href="${escapeHtml(card.scryfall_uri)}" target="_blank" rel="noreferrer">${escapeHtml(card.name)} ↗</a></h3></div>
          <span class="mana-value">MV ${escapeHtml(card.mana_value)}</span>
        </div>
        <p class="alternative-type">${escapeHtml(card.type_line)}</p>
        ${card.ai_review
          ? `<p><strong>Deckbuilder:</strong> ${escapeHtml(card.ai_review.rationale)}</p>${card.ai_review.cautions.length ? `<p><strong>Watch for:</strong> ${escapeHtml(card.ai_review.cautions.join(' · '))}</p>` : ''}`
          : `<p><strong>Functional:</strong> ${escapeHtml(card.functional_reason)}</p><p><strong>Plan:</strong> ${escapeHtml(card.plan_reason)}</p>`}
        <div class="role-chips">${card.roles.map(role => `<span>${escapeHtml(role.replace('_', ' '))}</span>`).join('')}</div>
      </article>`).join('')
    : '<p class="empty-results">No close heuristic matches cleared the quality threshold. Try a different card or use the result as a signal that this effect is unusually unique in Pioneer.</p>';
  labResults.hidden = false;
  bindCardPreviews();
}
async function findAlternatives(event) {
  event.preventDefault();
  const card = cardInput.value.trim();
  if (!card) return;
  labStatus.textContent = 'Reading Pioneer-legal candidates and scoring functional + strategy fit…';
  labResults.hidden = true;
  const button = event.currentTarget.querySelector('button');
  button.disabled = true;
  try {
    const params = new URLSearchParams({ card, archetype: archetypeSelect.value });
    if (chatgptModelsLoaded && chatgptModel.value) params.set('model', chatgptModel.value);
    if (baseline?.archetype === archetypeSelect.value) {
      baseline.cards.forEach(card => {
        const name = typeof card === 'string' ? card : card.name;
        if (name) params.append('exclude', name);
      });
      params.set('mainboard', JSON.stringify(baseline.cards));
    }
    const response = await fetch(`${CARD_ALTERNATIVES_URL}?${params}`, { cache: 'no-store' });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || 'Card Lab could not complete the search');
    renderResults(payload);
    const cacheNote = payload.cache?.status === 'hit' ? ' · cached locally' : '';
    const baselineNote = payload.excluded_cards ? ` · ${payload.excluded_cards} mainboard cards excluded` : '';
    const review = payload.ai_review;
    const reviewNote = review?.status === 'complete'
      ? ` · ${review.provider_label || 'AI'} reviewed ${review.reviewed}, rejected ${review.rejected}`
      : review?.status === 'unavailable' ? ' · deckbuilding review unavailable' : '';
    labStatus.textContent = `${payload.alternatives.length} candidates ranked for ${payload.archetype}${baselineNote}${reviewNote}${cacheNote}.`;
  } catch (error) {
    labStatus.textContent = error.message || 'Card Lab could not complete the search.';
  } finally {
    button.disabled = false;
  }
}

archetypeSelect.addEventListener('change', () => {
  loadBaseline();
  populateExamples();
});
document.querySelector('#cardLabForm').addEventListener('submit', findAlternatives);
connectChatGPTButton.addEventListener('click', connectChatGPT);
chatgptModel.addEventListener('change', () => sessionStorage.setItem('delver-chatgpt-model', chatgptModel.value));
populateArchetypes();
loadBaseline();
populateExamples();
loadChatGPTStatus();
