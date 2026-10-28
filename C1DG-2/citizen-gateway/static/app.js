'use strict';
const $ = id => document.getElementById(id);
const el = (t, p = {}, ...kids) => { const e = document.createElement(t); for (const [k, v] of Object.entries(p)) k === 'class' ? e.className = v : k.startsWith('on') ? e.addEventListener(k.slice(2), v) : e.setAttribute(k, v); kids.flat().forEach(c => e.append(c)); return e; };
const sid = (() => { try { let s = sessionStorage.sid; if (!s) s = sessionStorage.sid = Math.random().toString(36).slice(2); return s } catch { return 'x' } })();
const SECTIONS = ['home', 'assistant', 'schemes', 'documents', 'guidance', 'forme', 'about'];
const I18N = {
 en: {brand: 'Citizen Gateway', tag: 'Welfare guidance', langlabel: 'Language', eyebrow: 'Government schemes, explained simply', h1: 'Speak. Understand. Apply with confidence.', lead: 'Ask in Tamil, English or Tanglish. Find schemes that may suit you, learn which documents to prepare and follow the steps on the official website.', cta: 'Talk to Your Citizen Assistant', hint: 'No sign-in. We never ask for Aadhaar numbers, OTPs or passwords.', t1: 'Explore schemes', t1d: 'Browse by category or search in everyday words.', t2: 'Document help', t2d: 'See what to prepare and check your file before uploading.', t3: 'Application steps', t3d: 'Simple numbered steps with official links.', t4: 'Schemes for me', t4d: 'Tell us a little; see possible matches.',
  n_home: 'Home', n_assistant: 'Assistant', n_schemes: 'Schemes', n_documents: 'Documents', n_guidance: 'Apply', n_forme: 'For me', n_about: 'Help', convo: 'Voice conversation', autospeak: 'Read answers aloud', newchat: 'New conversation', send: 'Send', retry: 'Speak again', cancel: 'Cancel', play: '▶ Play', pause: '⏸ Pause', stop: '■ Stop', replay: '↻ Replay', micidle: 'Tap the microphone and speak', listening: 'Listening… speak now', thinking: 'Thinking…', speaking: 'Speaking…', ph: 'Type your question…', sph: 'e.g. scholarship for girls, farmer, vivasayi…', dph: 'e.g. income certificate, Aadhaar address update', gph: 'e.g. community certificate, scholarship, ration card', search: 'Search', remove: 'Remove', consent: 'I agree to send this file to an external AI service so it can be explained. It is not stored by this website.', check: 'Check a file before uploading', checkd: 'Checks type, size and whether the file opens. Nothing is stored. Each government portal has its own limits; confirm them on the portal.', limit: 'This website accepts PDF, JPG, PNG, WEBP up to', show: 'Show possible schemes', clear: 'Clear my details', close: 'Close', formed: 'Optional. Your answers stay in this browser only. Results are possible matches based on the little you share, not a decision on eligibility.', attach: 'Attach a document', heardlabel: 'Recognised text', details: 'View details', docs: 'Required documents', site: 'Official website'},
 ta: {brand: 'குடிமக்கள் நுழைவாயில்', tag: 'நலத்திட்ட வழிகாட்டி', langlabel: 'மொழி', eyebrow: 'அரசு திட்டங்கள், எளிய விளக்கத்துடன்', h1: 'பேசுங்கள். புரிந்துகொள்ளுங்கள். நம்பிக்கையுடன் விண்ணப்பியுங்கள்.', lead: 'தமிழ், ஆங்கிலம் அல்லது டாங்கிலிஷில் கேளுங்கள். உங்களுக்குப் பொருந்தக்கூடிய திட்டங்கள், தேவையான ஆவணங்கள், அதிகாரப்பூர்வ தளத்தில் செய்ய வேண்டிய படிகளை அறியுங்கள்.', cta: 'உங்கள் குடிமக்கள் உதவியாளருடன் பேசுங்கள்', hint: 'உள்நுழைவு தேவையில்லை. ஆதார் எண், OTP, கடவுச்சொல் கேட்க மாட்டோம்.', t1: 'திட்டங்களைப் பாருங்கள்', t1d: 'வகை வாரியாகப் பாருங்கள் அல்லது எளிய சொற்களில் தேடுங்கள்.', t2: 'ஆவண உதவி', t2d: 'என்ன தயாரிக்க வேண்டும் என்று பாருங்கள்; பதிவேற்றும் முன் கோப்பைச் சரிபாருங்கள்.', t3: 'விண்ணப்பப் படிகள்', t3d: 'அதிகாரப்பூர்வ இணைப்புகளுடன் எளிய படிகள்.', t4: 'எனக்கான திட்டங்கள்', t4d: 'சிறிது தகவல் தாருங்கள்; சாத்தியமான திட்டங்களைப் பாருங்கள்.',
  n_home: 'முகப்பு', n_assistant: 'உதவியாளர்', n_schemes: 'திட்டங்கள்', n_documents: 'ஆவணங்கள்', n_guidance: 'விண்ணப்பம்', n_forme: 'எனக்காக', n_about: 'உதவி', convo: 'குரல் உரையாடல்', autospeak: 'பதிலைச் சத்தமாகப் படி', newchat: 'புதிய உரையாடல்', send: 'அனுப்பு', retry: 'மீண்டும் பேசு', cancel: 'ரத்து', play: '▶ இயக்கு', pause: '⏸ இடைநிறுத்து', stop: '■ நிறுத்து', replay: '↻ மீண்டும்', micidle: 'மைக்கை அழுத்திப் பேசுங்கள்', listening: 'கேட்கிறேன்… பேசுங்கள்', thinking: 'யோசிக்கிறேன்…', speaking: 'பேசுகிறேன்…', ph: 'உங்கள் கேள்வியை எழுதுங்கள்…', search: 'தேடு', remove: 'நீக்கு', close: 'மூடு', show: 'சாத்தியமான திட்டங்களைக் காட்டு', clear: 'என் விவரங்களை அழி', details: 'விவரங்கள்', docs: 'தேவையான ஆவணங்கள்', site: 'அதிகாரப்பூர்வ தளம்', check: 'பதிவேற்றும் முன் கோப்பைச் சரிபார்க்கவும்', consent: 'விளக்கம் பெற இந்தக் கோப்பை வெளி AI சேவைக்கு அனுப்ப ஒப்புக்கொள்கிறேன். இந்த இணையதளம் அதைச் சேமிக்காது.'},
 tanglish: {brand: 'Citizen Gateway', tag: 'Welfare guidance', langlabel: 'Language', eyebrow: 'Arasu thittangal, easy-a purira madhiri', h1: 'Pesunga. Purinjukkunga. Nambikkaiyoda apply pannunga.', lead: 'Tamil, English illa Tanglish-la kelunga. Ungalukku porundhum schemes, thevaiyana documents, official website-la seiya vendiya steps therinjukkunga.', cta: 'Citizen Assistant kitta pesunga', hint: 'Sign-in venam. Aadhaar number, OTP, password kekka maatom.', t1: 'Schemes paarunga', t1d: 'Category-wise paarunga illa simple words-la search pannunga.', t2: 'Document help', t2d: 'Enna ready pannanum-nu paarunga; upload-ku munnadi file check pannunga.', t3: 'Apply steps', t3d: 'Official link-oda simple steps.', t4: 'Enakku schemes', t4d: 'Konjam sollunga; possible matches paarunga.',
  n_home: 'Home', n_assistant: 'Assistant', n_schemes: 'Schemes', n_documents: 'Documents', n_guidance: 'Apply', n_forme: 'Enakku', n_about: 'Help', convo: 'Voice conversation', autospeak: 'Pathilai padi', newchat: 'Pudhu conversation', send: 'Send', retry: 'Marubadi pesu', cancel: 'Cancel', micidle: 'Mic-a thotti pesunga', listening: 'Kekkuren… pesunga', thinking: 'Yosikkuren…', speaking: 'Pesuren…', ph: 'Ungal kelvi-a type pannunga…', search: 'Search', details: 'Details', docs: 'Documents', site: 'Official website'}};
const state = {lang: 'auto', hist: [], ctx: null, convo: false, auto: false, lastText: '', lastLang: 'en', status: {}, file: null};
const ui = () => I18N[state.lang === 'auto' ? 'en' : state.lang] || I18N.en;
const t = k => ui()[k] || I18N.en[k] || k;
function applyLang() {
  document.querySelectorAll('[data-i]').forEach(e => e.textContent = t(e.dataset.i));
  document.querySelectorAll('[data-ph]').forEach(e => e.placeholder = t(e.dataset.ph));
  document.documentElement.lang = state.lang === 'ta' ? 'ta' : 'en'; buildNav(); chips(); about();
}
function buildNav() { const n = $('nav'); n.replaceChildren(...SECTIONS.map(s => el('a', {href: '#' + s, 'data-go': s}, t('n_' + s)))); mark(location.hash.slice(1) || 'home'); }
function mark(s) { document.querySelectorAll('#nav a').forEach(a => a.dataset.go === s ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current')); }
function go(s, focus = true) { if (!SECTIONS.includes(s)) s = 'home'; SECTIONS.forEach(x => $(x).hidden = x !== s); mark(s); if (location.hash !== '#' + s) history.replaceState(null, '', '#' + s); if (focus) $('main').focus({preventScroll: true}); window.scrollTo(0, 0); if (s === 'schemes' && !$('slist').children.length) loadSchemes(1); }
document.addEventListener('click', e => { const g = e.target.closest('[data-go]'); if (g) { e.preventDefault(); go(g.dataset.go); if (g.dataset.start) $('msg').focus(); } });
addEventListener('hashchange', () => go(location.hash.slice(1), false));

async function api(url, opt) {
  try { const r = await fetch(url, opt); const j = await r.json().catch(() => ({})); if (!r.ok) throw Object.assign(new Error(j.message || 'Request failed'), {data: j}); return j; }
  catch (e) { if (e.data) throw e; throw Object.assign(new Error('Cannot reach the server. Check your connection and try again.'), {net: true}); }
}
const postJSON = (u, d) => api(u, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({sid, ...d})});
const note = (box, msg) => { box.textContent = msg; box.hidden = !msg; };

/* ---------- safe card rendering (textContent only; links limited to https) ---------- */
const FLAGTXT = {incomplete: 'Incomplete record', no_documents: 'Documents not listed', no_steps: 'Steps not listed', closed: 'May be closed', close_date: 'Has a closing date', snapshot: 'Verify on official site'};
const safeUrl = u => /^https:\/\//.test(u || '') ? u : null;
function schemeCard(c) {
  const row = el('div', {class: 'row'}, el('button', {class: 'ghost', onclick: () => detail(c.id)}, t('details')));
  const u = safeUrl(c.url); if (u) row.append(el('a', {href: u, target: '_blank', rel: 'noopener noreferrer'}, t('site') + ' ↗'));
  return el('article', {class: 'sc'}, el('h3', {}, c.name),
    el('div', {class: 'tags'}, el('span', {class: 'tag'}, c.level === 'Central' ? 'Central govt' : 'Tamil Nadu'), el('span', {class: 'tag'}, c.category), ...c.flags.filter(f => f !== 'snapshot').map(f => el('span', {class: 'tag w'}, '⚠ ' + FLAGTXT[f]))),
    el('p', {}, c.summary + (c.summary.length >= 220 ? '…' : '')), row);
}
const list = (items, ordered) => el(ordered ? 'ol' : 'ul', {class: ordered ? 'steps' : ''}, ...(items.length ? items : ['Not listed — check the official page.']).map(i => el('li', {}, i)));
async function detail(id) {
  const b = $('dlgbody'); b.replaceChildren(el('p', {}, '…')); $('dlg').showModal();
  try {
    const {card: c, related} = await api(`/api/service/${encodeURIComponent(id)}?sid=${sid}`); const u = safeUrl(c.url);
    b.replaceChildren(el('h2', {}, c.name), el('p', {class: 'muted'}, `${c.level === 'Central' ? 'Central government' : 'Tamil Nadu government'} · ${c.category} · Application: ${c.mode || 'see official site'}`),
      el('p', {}, c.description), el('h3', {}, 'Benefits'), list([].concat(c.benefits || [])), el('h3', {}, 'Who may be eligible'), list(c.eligibility),
      ...(c.exclusions ? [el('h3', {}, 'Not eligible / limits'), el('p', {}, String(c.exclusions))] : []),
      el('h3', {}, t('docs')), list(c.documents), el('h3', {}, 'How to apply'), list(c.steps, true),
      el('div', {class: 'banner'}, 'This is a possible match, not a guarantee of eligibility or approval. ' + c.flags.map(f => FLAGTXT[f]).join(' · ') + '. Last checked: ' + c.last_verified + '. Confirm on the official source before applying.'),
      u ? el('p', {}, el('a', {class: 'link', href: u, target: '_blank', rel: 'noopener noreferrer'}, t('site') + ' ↗')) : '');
    postJSON('/api/log', {event: 'opened_ui', detail: id}).catch(() => {});
  } catch (e) { b.replaceChildren(el('p', {class: 'bad'}, e.message)); }
}
$('dlgx').onclick = () => $('dlg').close();

/* ---------- chat ---------- */
function addMsg(role, text, extra = {}) {
  const m = el('div', {class: 'msg ' + role + (extra.err ? ' err' : '')}); m.append(document.createTextNode(text));
  if (extra.notice) m.append(el('small', {}, extra.notice));
  if (extra.cards && extra.cards.length) m.append(el('div', {class: 'cards'}, ...extra.cards.map(schemeCard)));
  $('log').append(m); m.scrollIntoView({block: 'end'}); return m;
}
function welcome() { $('log').replaceChildren(); addMsg('bot', {en: 'Vanakkam! Ask me about a scheme, a certificate or a document, by voice or text. I give possible matches, not final eligibility.', ta: 'வணக்கம்! திட்டம், சான்றிதழ் அல்லது ஆவணம் பற்றி குரல் அல்லது எழுத்தில் கேளுங்கள். நான் சாத்தியமான பொருத்தங்களையே தருவேன்; தகுதி முடிவு அல்ல.', tanglish: 'Vanakkam! Scheme, certificate, document pathi voice-la illa type panni kelunga. Naan possible matches thaan tharuven, final eligibility illai.'}[state.lang === 'auto' ? 'en' : state.lang]); }
function chips() { const q = {en: ['Schemes for college students', 'Documents for income certificate', 'Schemes for farmers'], ta: ['கல்லூரி மாணவர்களுக்கான திட்டங்கள்', 'வருமானச் சான்றிதழுக்கு என்ன ஆவணங்கள்?', 'விவசாயிகளுக்கான திட்டங்கள்'], tanglish: ['Enakku scholarship apply panna enna documents venum?', 'Vivasayi-ku enna schemes irukku?', 'Mudhiyor pension eppadi apply panradhu?']}[state.lang === 'auto' ? 'en' : state.lang]; $('chips').replaceChildren(...q.map(x => el('button', {type: 'button', onclick: () => send(x)}, x))); }
let busy = false;
async function send(text, file = state.file) {
  text = (text || '').trim(); if (busy || (!text && !file)) return;
  if (file && !text && !state.status.ai) { /* allowed: backend validates and explains */ }
  busy = true; stopSpeak(); hideHeard(); addMsg('user', text || ('📎 ' + file.name)); $('msg').value = '';
  setMic('thinking'); const wait = addMsg('bot', t('thinking'));
  const fd = new FormData(); fd.append('message', text); fd.append('sid', sid); fd.append('lang', state.lang); fd.append('history', JSON.stringify(state.hist)); fd.append('context', state.ctx || '');
  fd.append('profile', localStorage.getItem('profile') || '{}'); if (file) { fd.append('file', file); if ($('consent').checked) fd.append('consent', '1'); }
  try {
    const r = await api('/api/chat', {method: 'POST', body: fd}); wait.remove();
    addMsg('bot', r.reply, {notice: r.notice, cards: r.cards}); state.ctx = r.context || state.ctx; state.lastText = r.reply; state.lastLang = r.lang;
    state.hist.push({role: 'user', content: text || '[file]'}, {role: 'assistant', content: r.reply}); state.hist = state.hist.slice(-12);
    if (file && !r.needs_consent) clearFile(); $('speakbar').hidden = false;
    if (state.auto || state.convo) speak(r.reply, r.lang);
  } catch (e) { wait.remove(); addMsg('bot', e.message, {err: true}); if (e.data && e.data.error && file) clearFile(); }
  busy = false; setMic('idle');
}
$('chatform').onsubmit = e => { e.preventDefault(); send($('msg').value); };
$('newchat').onclick = () => { state.hist = []; state.ctx = null; stopSpeak(); clearFile(); welcome(); $('speakbar').hidden = true; };
$('lang').onchange = e => { state.lang = e.target.value; applyLang(); welcome(); setMic('idle'); try { localStorage.lang = state.lang } catch {} };
$('autospeak').onchange = e => state.auto = e.target.checked; $('convo').onchange = e => { state.convo = e.target.checked; if (state.convo) { state.auto = true; $('autospeak').checked = true; } };
$('chatfile').onchange = e => { const f = e.target.files[0]; if (!f) return; const max = state.status.max_upload_mb || 5;
  if (f.size > max * 1048576) { addMsg('bot', `That file is too large (limit ${max} MB). Compress it or use a smaller scan.`, {err: true}); e.target.value = ''; return; }
  state.file = f; $('fname').textContent = '📎 ' + f.name; $('fileinfo').hidden = false; $('consent').parentElement.hidden = !state.status.ai; };
function clearFile() { state.file = null; $('chatfile').value = ''; $('fileinfo').hidden = true; $('consent').checked = false; }
$('fclear').onclick = clearFile;

/* ---------- voice input ---------- */
const SR = window.SpeechRecognition || window.webkitSpeechRecognition; let rec = null, listening = false, autoTimer = null;
const RLANG = {auto: 'en-IN', en: 'en-IN', ta: 'ta-IN', tanglish: 'en-IN'};
function setMic(s) { const mic = $('mic'); mic.setAttribute('aria-pressed', s === 'listening'); mic.disabled = s === 'thinking'; $('micstate').textContent = s === 'listening' ? t('listening') : s === 'thinking' ? t('thinking') : s === 'speaking' ? t('speaking') : t('micidle'); document.body.classList.toggle('speaking', s === 'speaking'); }
function hideHeard() { clearTimeout(autoTimer); $('heard').hidden = true; }
function showHeard(txt) { $('heardtext').value = txt; $('heard').hidden = false; clearTimeout(autoTimer);
  if (state.convo && txt.trim()) { autoTimer = setTimeout(() => send($('heardtext').value), 2500); } }
$('heardtext').oninput = () => clearTimeout(autoTimer); $('heardsend').onclick = () => send($('heardtext').value); $('heardx').onclick = hideHeard; $('heardretry').onclick = () => { hideHeard(); startListen(); };
function startListen() {
  const vn = $('voicenote');
  if (!SR) { note(vn, 'Voice input is not supported in this browser (try Chrome or Edge). You can still type your question below.'); $('msg').focus(); return; }
  if (!window.isSecureContext && !['localhost', '127.0.0.1'].includes(location.hostname)) { note(vn, 'Voice input needs a secure (https) page.'); return; }
  stopSpeak(); note(vn, ''); rec = new SR(); rec.lang = RLANG[state.lang] || 'en-IN'; rec.interimResults = true; rec.continuous = false; let final = '';
  rec.onstart = () => { listening = true; setMic('listening'); };
  rec.onresult = ev => { let tmp = ''; final = ''; for (const r of ev.results) (r.isFinal ? (final += r[0].transcript) : (tmp += r[0].transcript)); showHeard(final || tmp); clearTimeout(autoTimer); };
  rec.onerror = ev => { const m = {'not-allowed': 'Microphone permission was blocked. Allow it in the browser address bar, or type instead.', 'service-not-allowed': 'Speech service is blocked in this browser. Type instead.', 'no-speech': 'I did not hear anything. Tap the microphone and try again.', 'language-not-supported': 'This browser cannot recognise the selected language. Try English or type.', 'audio-capture': 'No microphone found.', 'network': 'Speech recognition needs an internet connection.'}; note(vn, m[ev.error] || 'Voice input failed. You can type instead.'); };
  rec.onend = () => { listening = false; setMic('idle'); if (final.trim()) showHeard(final); };
  try { rec.start(); } catch { note(vn, 'Could not start the microphone.'); }
}
$('mic').onclick = () => listening ? rec.stop() : startListen();
if (!SR) note($('voicenote'), 'Voice input is not supported in this browser (try Chrome or Edge). Text chat works normally.');

/* ---------- voice output ---------- */
const TTS = 'speechSynthesis' in window; let voices = [];
if (TTS) { const lv = () => voices = speechSynthesis.getVoices(); lv(); speechSynthesis.onvoiceschanged = lv; }
function pick(lang) { const want = lang === 'ta' ? 'ta' : 'en'; const v = voices.filter(x => x.lang.toLowerCase().startsWith(want)); return lang === 'en' || lang === 'tanglish' ? (v.find(x => /en-IN/i.test(x.lang)) || v[0]) : v[0]; }
const clean = s => s.replace(/https?:\/\/\S+/g, '').replace(/[☐•]/g, '').replace(/\n+/g, '. ').trim();
function speak(text, lang) {
  if (!TTS) { note($('voicenote'), 'Reading aloud is not supported in this browser. The written answer is shown.'); return; }
  speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(clean(text)); const v = pick(lang || state.lastLang);
  if (lang === 'ta' && !v) { note($('voicenote'), 'No Tamil voice is installed on this device, so I cannot read this aloud in Tamil. The written answer is shown. (Android/Chrome and Windows can add Tamil voices in system settings.)'); return; }
  if (lang === 'tanglish') note($('voicenote'), 'Tanglish is read with an English voice, so pronunciation may sound unusual.');
  if (v) { u.voice = v; u.lang = v.lang; } else u.lang = 'en-IN';
  u.onstart = () => setMic('speaking'); u.onend = u.onerror = () => setMic('idle'); speechSynthesis.speak(u);
}
function stopSpeak() { if (TTS) { speechSynthesis.cancel(); } if (!busy) setMic('idle'); }
$('sp-play').onclick = () => state.lastText && speak(state.lastText, state.lastLang); $('sp-replay').onclick = $('sp-play').onclick;
$('sp-stop').onclick = stopSpeak; $('sp-pause').onclick = () => { if (!TTS) return; const b = $('sp-pause'); if (speechSynthesis.paused) { speechSynthesis.resume(); b.textContent = t('pause'); } else if (speechSynthesis.speaking) { speechSynthesis.pause(); b.textContent = '▶ ' + 'Resume'; } };

/* ---------- scheme explorer ---------- */
let spage = 1;
async function loadSchemes(p) {
  spage = p; const q = new URLSearchParams({q: $('sq').value, category: $('scat').value, level: $('slevel').value, page: p});
  $('scount').textContent = '…'; try {
    const r = await api('/api/schemes?' + q);
    if ($('scat').options.length === 1) r.categories.forEach(c => $('scat').append(el('option', {value: c}, c)));
    $('scount').textContent = `${r.total} scheme(s) — possible matches only; confirm on the official site.`;
    $('slist').replaceChildren(...(r.results.length ? r.results.map(schemeCard) : [el('p', {}, 'No schemes found. Try different words.')]));
    const pages = Math.ceil(r.total / 12), prev = el('button', {class: 'ghost', onclick: () => loadSchemes(p - 1)}, '← Prev'), next = el('button', {class: 'ghost', onclick: () => loadSchemes(p + 1)}, 'Next →');
    prev.disabled = p <= 1; next.disabled = p >= pages; $('spager').replaceChildren(...(pages > 1 ? [prev, el('span', {}, `${p} / ${pages}`), next] : []));
  } catch (e) { $('scount').textContent = e.message; }
}
$('sform').onsubmit = e => { e.preventDefault(); loadSchemes(1); };

/* ---------- documents + guidance (same endpoint, two views) ---------- */
async function procs(q, box, steps) {
  box.replaceChildren(el('p', {}, '…')); try {
    const r = await api(`/api/documents?sid=${sid}&q=${encodeURIComponent(q)}`);
    box.replaceChildren(...(r.results.length ? r.results.map(i => { const u = safeUrl(i.url);
      return el('div', {class: 'panel'}, el('h3', {}, i.title), el('span', {class: 'tag'}, i.type),
        ...(steps ? [el('h4', {}, 'Steps'), list(i.steps, true), el('h4', {}, t('docs')), list(i.docs)] : [el('h4', {}, 'Checklist'), list(i.docs.map(d => '☐ ' + d))]),
        i.note ? el('p', {class: 'muted'}, i.note) : '', el('p', {class: 'muted'}, 'File format and size limits differ by portal; none are assumed here. Check the portal’s own instructions.'),
        u ? el('p', {}, el('a', {class: 'link', href: u, target: '_blank', rel: 'noopener noreferrer'}, t('site') + ' ↗')) : el('p', {class: 'muted'}, 'No official link on record — search the official portal.')); }) : [el('p', {}, 'Nothing found. Try another name (e.g. "income certificate").')]));
  } catch (e) { box.replaceChildren(el('p', {class: 'bad'}, e.message)); }
}
$('dform').onsubmit = e => { e.preventDefault(); $('dq').value.trim() && procs($('dq').value, $('dres'), false); };
$('gform').onsubmit = e => { e.preventDefault(); $('gq').value.trim() && procs($('gq').value, $('gres'), true); };
$('vfile').onchange = async e => { const f = e.target.files[0]; if (!f) return; const box = $('vres'); box.textContent = '…'; const fd = new FormData(); fd.append('file', f);
  try { const r = await api('/api/validate-file', {method: 'POST', body: fd}); box.className = 'ok'; box.textContent = '✔ ' + r.message + ` (${r.info.size_kb} KB${r.info.pages ? ', ' + r.info.pages + ' page(s)' : ''})`; }
  catch (er) { box.className = 'bad'; box.textContent = '✖ ' + er.message; } };

/* ---------- my recommendations ---------- */
const PF = ['age', 'gender', 'occupation', 'education', 'community', 'state', 'widow', 'disabled'];
function loadProfile() { try { const p = JSON.parse(localStorage.getItem('profile') || '{}'); PF.forEach(k => { const e = $('p_' + k); if (e && p[k] !== undefined) e.type === 'checkbox' ? e.checked = !!p[k] : e.value = p[k]; }); } catch {} }
$('pform').onsubmit = async e => { e.preventDefault(); const p = {}; PF.forEach(k => { const e = $('p_' + k); p[k] = e.type === 'checkbox' ? e.checked : e.value; }); try { localStorage.setItem('profile', JSON.stringify(p)); } catch {}
  const filled = Object.values(p).filter(v => v && v !== 'Tamil Nadu').length; $('pres').replaceChildren(el('p', {}, '…'));
  try { const r = await postJSON('/api/matches', {profile: p});
    $('pres').replaceChildren(el('div', {class: 'banner'}, filled < 3 ? 'Based on very little information, so these are broad possibilities. Add more details for better matches.' : 'Possible matches based on what you shared. This is not a decision on eligibility.'),
      el('div', {class: 'grid'}, ...(r.matches.length ? r.matches.map(m => el('article', {class: 'sc'}, el('h3', {}, m.name), el('p', {}, 'Matched on: ' + m.why.join(', ')), el('div', {class: 'row'}, el('button', {class: 'ghost', onclick: () => detail(m.id)}, t('details'))))) : [el('p', {}, 'No matches yet. Fill in more details.')])));
  } catch (er) { $('pres').replaceChildren(el('p', {class: 'bad'}, er.message)); } };
$('pclear').onclick = () => { try { localStorage.removeItem('profile'); } catch {} $('pform').reset(); $('pres').replaceChildren(); };

function about() { $('abouttext').replaceChildren(el('h3', {}, 'What this is'), el('p', {}, 'A guidance tool that helps you understand welfare schemes and documents. It is not a government website and cannot apply for you or approve anything.'),
  el('h3', {}, 'How to use the assistant'), list(['Tap the big microphone and speak in Tamil, English or Tanglish. Check the recognised text, edit it if needed, then Send.', 'Turn on “Read answers aloud” to hear replies. Tamil voice needs a Tamil voice installed on your device.', 'Prefer typing? Use the text box. It works in every browser.']),
  el('h3', {}, 'Limits'), list(['Scheme data is a dated snapshot of the myScheme portal and some records are incomplete. Always confirm on the official source.', 'Results are possible matches, never a guarantee of eligibility or approval.', 'Without an AI key the assistant answers from built-in data only and cannot read your files.']),
  el('h3', {}, 'Privacy'), list(['Never share Aadhaar numbers, OTPs, passwords, PINs or bank details. The assistant will not use them.', 'Uploaded files are checked in memory and are not saved. If you choose AI explanation, the file is sent to an external AI service only after you tick the consent box.', 'Your profile stays in your browser. Typed or spoken questions are not stored by this website. Browser speech recognition may send audio to your browser vendor’s speech service.', 'Voice features depend on your browser: Chrome/Edge work best.'])); }

(async () => { try { state.lang = localStorage.lang || 'auto'; $('lang').value = state.lang; } catch {}
  loadProfile(); applyLang(); welcome(); go(location.hash.slice(1) || 'home', false);
  try { state.status = await api('/api/status'); $('maxmb').textContent = state.status.max_upload_mb; note($('statusbar'), state.status.ai ? '' : 'Basic mode: answers come from built-in scheme data. Tamil/Tanglish understanding is keyword-based and file reading is off until an AI key is configured.'); }
  catch (e) { note($('statusbar'), e.message); } })();
