"""Chatbot: works offline from the datasets (basic mode); uses Claude when ANTHROPIC_API_KEY is set (ai mode)."""
import os, re, base64, json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import langutil, filecheck
MODEL = os.environ.get('CLAUDE_MODEL', 'claude-sonnet-5-5')
AI_TIMEOUT = float(os.environ.get('AI_TIMEOUT_SECONDS', 25))
LANG_NAME = {'ta': 'Tamil (Tamil script)', 'tanglish': 'Tanglish (Tamil written in English letters)', 'en': 'English'}
SYSTEM = ("You are Citizen Assistant, a patient helper for people in Tamil Nadu, India, explaining government services, documents and schemes in simple words. "
 "Reply in {lang}. Give short numbered steps, show documents as a checklist, and ask ONE short question if you need more detail. "
 "Use ONLY the reference info for scheme facts; never invent schemes, eligibility, benefits, dates, file-size limits or links. If unsure, say so and tell the person to confirm on the official source. "
 "Say 'may be eligible', never 'you are eligible'. Never ask for Aadhaar numbers, OTPs, passwords, PINs or bank credentials, and warn that agents should not be paid extra. "
 "If a photo or PDF is shared, explain what kind of document it appears to be and what to do next, without repeating personal numbers.")
T = {  # fixed phrases in the three styles
 'sensitive': {'en': "Please don't share Aadhaar numbers, OTPs, passwords, PINs or bank details here. I never need them. Ask your question without them.",
               'ta': "ஆதார் எண், OTP, கடவுச்சொல், PIN, வங்கி விவரங்களை இங்கே பகிர வேண்டாம். அவை எனக்குத் தேவையில்லை. அவை இல்லாமல் கேளுங்கள்.",
               'tanglish': "Aadhaar number, OTP, password, PIN, bank details-a inga share panna vendam. Enakku adhu thevai illai. Adhu illama kelunga."},
 'unclear': {'en': "I couldn't find a clear match. Which one do you mean: a scheme (scholarship, farmer, pension...) or a document/certificate?",
             'ta': "தெளிவான பதில் கிடைக்கவில்லை. எதைப் பற்றி கேட்கிறீர்கள்: திட்டம் (கல்வி உதவித்தொகை, விவசாயி, ஓய்வூதியம்...) அல்லது சான்றிதழ்/ஆவணமா?",
             'tanglish': "Clear-a match kidaikkala. Edhai pathi kekkureenga: scheme (scholarship, farmer, pension...) illa document/certificate-a?"},
 'found': {'en': "Here is what I found. These are possible matches, not a guarantee of eligibility. Please confirm on the official source.",
           'ta': "கிடைத்த தகவல் இது. இவை சாத்தியமான பொருத்தங்கள் மட்டுமே; தகுதி உறுதி அல்ல. அதிகாரப்பூர்வ தளத்தில் சரிபார்க்கவும். (திட்ட விவரங்கள் ஆங்கிலத்தில் உள்ளன.)",
           'tanglish': "Idhu dhaan kidaichadhu. Idhu possible match mattum, eligibility guarantee illai. Official site-la confirm pannunga. (Scheme details English-la irukku.)"},
 'ai_off': {'en': "AI mode is not set up, so I am answering from the built-in scheme data.",
            'ta': "AI வசதி அமைக்கப்படவில்லை; உள்ளமைந்த திட்டத் தரவிலிருந்து பதிலளிக்கிறேன்.",
            'tanglish': "AI mode set up aagala, so built-in scheme data-la irundhu pathil solren."},
 'ai_fail': {'en': "The AI service did not respond, so this answer comes from the built-in data.",
             'ta': "AI சேவை பதிலளிக்கவில்லை; உள்ளமைந்த தரவிலிருந்து இந்தப் பதில்.",
             'tanglish': "AI service respond pannala, so built-in data-la irundhu indha pathil."},
 'consent': {'en': "To read your file I must send it to an external AI service. Tick the consent box and send again, or ask without the file.",
             'ta': "கோப்பைப் படிக்க அதை வெளி AI சேவைக்கு அனுப்ப வேண்டும். ஒப்புதல் பெட்டியைத் தேர்வு செய்து மீண்டும் அனுப்பவும்; அல்லது கோப்பு இல்லாமல் கேளுங்கள்.",
             'tanglish': "File padikka adhai external AI service-ku anuppa vendum. Consent box tick panni marubadi anuppunga, illa file illama kelunga."},
 'nofile_ai': {'en': "I can't read the contents of files without the AI service. Your file looks valid ({info}). Tell me the document name and I will list what is usually needed.",
               'ta': "AI சேவை இல்லாமல் கோப்பின் உள்ளடக்கத்தைப் படிக்க முடியாது. கோப்பு சரியாக உள்ளது ({info}). ஆவணத்தின் பெயரைச் சொன்னால் வழக்கமாகத் தேவையானவற்றைக் கூறுகிறேன்.",
               'tanglish': "AI service illama file content padikka mudiyadhu. File valid-a irukku ({info}). Document peyar sonna, usually enna venum-nu solren."},
 'file_err': {'bad_ext': "Unsupported file type. Use PDF, JPG, PNG or WEBP.", 'empty': "The file is empty.", 'too_big': "The file is too large (platform limit {max_mb} MB). Compress it or send a smaller scan.",
              'type_mismatch': "The file content does not match its extension.", 'encrypted': "This PDF is password-protected. Remove the password and try again.",
              'corrupt': "The file is damaged or cannot be opened. Try scanning or saving it again."},
}
ITEMS, BOOST, VEC, MAT, SERV = [], None, None, None, {}
def init(services, procs, faqs):
    global BOOST, VEC, MAT
    ITEMS.clear(); SERV.clear(); SERV.update({s['service_id']: s for s in services})
    for p in procs: ITEMS.append((f"{p['name']} {p['aliases']} {' '.join(p['documents'])}", {**p, 'type': 'Process', 'title': p['name'], 'docs': p['documents']}))
    for s in services: ITEMS.append((f"{s['service_name']} {s['tags']} {s['description'][:300]}", {'type': 'Scheme', 'id': s['service_id'], 'category': s['category'], 'title': s['service_name'], 'docs': s['required_documents'], 'steps': s['application_steps'][:6], 'url': s['official_url']}))
    for f in faqs: ITEMS.append((f"{f['q']} {f['a'][:200]} {f['n']}", {'type': 'FAQ', 'title': f['n'], 'a': f['a']}))
    BOOST = np.array([.08 if i[1]['type'] == 'Process' else 0 for i in ITEMS])
    VEC = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 4), min_df=2, sublinear_tf=True, max_features=150000)  # char n-grams tolerate Tanglish spellings
    MAT = VEC.fit_transform([t for t, _ in ITEMS])
def search(q, k=3, kinds=None, category=None):
    sims = linear_kernel(VEC.transform([langutil.expand(q)]), MAT)[0] + BOOST
    if category: sims = sims + np.array([.05 if i[1].get('category') == category else 0 for i in ITEMS])
    out = []
    for i in sims.argsort()[::-1]:
        if kinds and ITEMS[i][1]['type'] not in kinds: continue
        out.append((float(sims[i]), ITEMS[i][1]))
        if len(out) == k: break
    return out
def flags(s):
    """Data-quality warnings shown to users. All data is a dated snapshot of myScheme and must be re-checked."""
    f = []
    if not s.get('complete'): f.append('incomplete')
    if not s.get('required_documents'): f.append('no_documents')
    if not s.get('application_steps'): f.append('no_steps')
    if s.get('closed'): f.append('closed')
    if s.get('scheme_close_date'): f.append('close_date')
    return f + ['snapshot']
def card(s, detail=False):
    c = {'id': s['service_id'], 'name': s['service_name'], 'level': s['level'], 'state': s.get('state'), 'category': s['category'], 'summary': s['description'][:220].strip(), 'url': s['official_url'], 'flags': flags(s)}
    if detail: c.update(description=s['description'], benefits=s['benefits'], eligibility=s['eligibility'], exclusions=s['exclusions'], documents=s['required_documents'], steps=s['application_steps'], mode=s['application_mode'], close_date=s.get('scheme_close_date'), last_verified=s['last_verified'])
    return c
def fmt_scheme(s, what=None):
    n = s['service_name']
    if what == 'eligibility': body = '\n'.join('• ' + e for e in s['eligibility'][:8]) or 'Eligibility not listed.'
    elif what == 'documents': body = '\n'.join('☐ ' + d for d in s['required_documents']) or 'Documents not listed - check the official page.'
    elif what == 'steps': body = '\n'.join(f'{i}. {x}' for i, x in enumerate(s['application_steps'][:8], 1)) or 'Steps not listed - check the official page.'
    elif what == 'link': body = s['official_url']
    else: body = s['description'][:300]
    return f"{n}\n\n{body}" + (f"\n\nOfficial source: {s['official_url']}" if what != 'link' else '')
def fmt(it):
    if it['type'] == 'FAQ': return f"{it['a']}\n\n(From: {it['title']})"
    out = f"{it['title']}\n\nDocuments usually needed:\n" + '\n'.join('☐ ' + d for d in (it['docs'] or ['Not listed - check the official page']))
    if it.get('steps'): out += "\n\nSteps:\n" + '\n'.join(f"{i}. {s}" for i, s in enumerate(it['steps'], 1))
    return out + (f"\n\nOfficial link: {it['url']}" if it.get('url') else '') + (f"\n\n{it['note']}" if it.get('note') else '')
SENSITIVE = re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b|\botp\b.*\d{4,6}|\b(password|pin|cvv)\b\s*(is|:|=)?\s*\S+', re.I)
def llm(msg, lang, hist, prof, ctx, fbytes, mime):
    import anthropic
    content = []
    if fbytes: content.append({'type': 'document' if mime == 'application/pdf' else 'image', 'source': {'type': 'base64', 'media_type': mime, 'data': base64.b64encode(fbytes).decode()}})
    content.append({'type': 'text', 'text': msg or 'Please look at the attached file and tell me what to do next.'})
    msgs = [h for h in hist[-8:] if isinstance(h, dict) and h.get('content') and h.get('role') in ('user', 'assistant')]
    while msgs and msgs[0]['role'] != 'user': msgs.pop(0)
    cl = anthropic.Anthropic(timeout=AI_TIMEOUT, max_retries=0)
    r = cl.messages.create(model=MODEL, max_tokens=900, system=f"{SYSTEM.format(lang=LANG_NAME[lang])}\nProfile (optional, may be empty): {json.dumps(prof)[:500]}\nReference info:\n{ctx}", messages=msgs + [{'role': 'user', 'content': content}])
    return r.content[0].text
def reply(msg, hist=None, prof=None, fbytes=None, mime=None, lang_pref='auto', consent=False, ctx_id=None, intent=None, finfo=None):
    """-> dict(reply, mode, lang, cards, context, notice)"""
    hist, prof = hist or [], prof or {}
    lang = lang_pref if lang_pref in LANG_NAME else langutil.detect(msg)
    res = {'reply': '', 'mode': 'basic', 'lang': lang, 'cards': [], 'context': ctx_id, 'notice': None}
    if SENSITIVE.search(msg or ''): res['reply'] = T['sensitive'][lang]; return res
    key = bool(os.environ.get('ANTHROPIC_API_KEY'))
    if fbytes and key and not consent: res['reply'] = T['consent'][lang]; res['needs_consent'] = True; return res
    follow = langutil.follow_intent(msg) if msg else None
    last = SERV.get(ctx_id) if ctx_id else None
    if last and follow and len(msg.split()) <= 8 and not fbytes: hits = [(1.0, {'type': 'Scheme', 'id': ctx_id})]   # short follow-up about the scheme under discussion
    else: hits = search(msg, 4, category=intent) if msg else []
    good = [(s, i) for s, i in hits if s > .12]
    schemes = [SERV[i['id']] for s, i in good if i['type'] == 'Scheme'][:3]
    if key:
        try:
            ctx = '\n\n'.join(fmt_scheme(SERV[i['id']], follow) if i['type'] == 'Scheme' and follow else fmt(i) if i['type'] != 'Scheme' else fmt_scheme(SERV[i['id']]) for s, i in good)
            res.update(reply=llm(msg, lang, hist, prof, ctx, fbytes, mime), mode='ai')
            res['cards'] = [card(s) for s in schemes]; res['context'] = schemes[0]['service_id'] if schemes else ctx_id; return res
        except Exception: res['notice'] = T['ai_fail'][lang]
    else: res['notice'] = T['ai_off'][lang]
    if fbytes:
        res['reply'] = T['nofile_ai'][lang].format(info=', '.join(f'{k}: {v}' for k, v in (finfo or {}).items())); return res
    if not good: res['reply'] = T['unclear'][lang]; return res
    top = good[0][1]
    if top['type'] == 'FAQ' and good and any(i['type'] == 'Scheme' and good[0][0] - sc < .15 for sc, i in good): top = next(i for sc, i in good if i['type'] == 'Scheme')   # the 10k FAQ rows would otherwise crowd out scheme cards
    if top['type'] == 'Scheme':
        s = SERV[top['id']]; res['reply'] = (fmt_scheme(s, follow) if follow else T['found'][lang] + '\n\n' + fmt_scheme(s)); res['context'] = s['service_id']
        res['cards'] = [card(x) for x in (schemes if not follow else [s])]
    else: res['reply'] = fmt(top); res['cards'] = [card(x) for x in schemes[:2]]
    return res
