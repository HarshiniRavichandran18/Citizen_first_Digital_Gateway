import os, base64, json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
MODEL = os.environ.get('CLAUDE_MODEL', 'claude-sonnet-5-5')
SYSTEM = ("You are Citizen 1st Assistant, a patient personal assistant helping people in Tamil Nadu, India with government services, documents and schemes. "
 "Reply in the language the person writes in (Tamil, English or Tanglish). Give clear numbered steps, show documents as a checklist, and ask ONE short question if you need more detail. "
 "Use the reference info when relevant. If unsure, say so and point to the official portal. Never say someone is definitely eligible. "
 "Never ask for Aadhaar numbers, OTPs, passwords or bank details, and warn that agents should not be paid extra. "
 "If a photo or PDF is shared, say what it shows (a form, letter or error message) and what to do next, without repeating personal numbers.")
ITEMS, BOOST, VEC, MAT = [], None, None, None
def init(services, procs, faqs):
    global BOOST, VEC, MAT
    for p in procs: ITEMS.append((f"{p['name']} {p['aliases']} {' '.join(p['documents'])}", {**p, 'type': 'Process', 'title': p['name'], 'docs': p['documents']}))
    for s in services: ITEMS.append((f"{s['service_name']} {s['tags']} {s['description'][:300]}", {'type': 'Scheme', 'title': s['service_name'], 'docs': s['required_documents'], 'steps': s['application_steps'][:6], 'url': s['official_url']}))
    for f in faqs: ITEMS.append((f"{f['q']} {f['a'][:200]} {f['n']}", {'type': 'FAQ', 'title': f['n'], 'a': f['a']}))
    BOOST = np.array([.08 if i[1]['type'] == 'Process' else 0 for i in ITEMS])
    VEC = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 4), min_df=2, sublinear_tf=True, max_features=150000)  # char n-grams tolerate Tanglish spellings
    MAT = VEC.fit_transform([t for t, _ in ITEMS])
def search(q, k=3, kinds=None):
    sims = linear_kernel(VEC.transform([q]), MAT)[0] + BOOST; out = []
    for i in sims.argsort()[::-1]:
        if kinds and ITEMS[i][1]['type'] not in kinds: continue
        out.append((float(sims[i]), ITEMS[i][1]))
        if len(out) == k: break
    return out
def fmt(it):
    if it['type'] == 'FAQ': return f"{it['a']}\n\n(From: {it['title']})"
    out = f"{it['title']}\n\nDocuments usually needed:\n" + '\n'.join('☐ ' + d for d in (it['docs'] or ['Not listed - check the official page']))
    if it.get('steps'): out += "\n\nSteps:\n" + '\n'.join(f"{i}. {s}" for i, s in enumerate(it['steps'], 1))
    return out + (f"\n\nOfficial link: {it['url']}" if it.get('url') else '') + (f"\n\n{it['note']}" if it.get('note') else '')
def llm(msg, hist, prof, ctx, fbytes, mime):
    import anthropic
    content = []
    if fbytes:
        if mime not in ('image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'): return 'Please upload a JPG/PNG/WEBP photo or a PDF.'
        content.append({'type': 'document' if mime == 'application/pdf' else 'image', 'source': {'type': 'base64', 'media_type': mime, 'data': base64.b64encode(fbytes).decode()}})
    content.append({'type': 'text', 'text': msg or 'Please look at the attached file and tell me what to do next.'})
    msgs = [h for h in hist[-8:] if h.get('content')]
    while msgs and msgs[0]['role'] != 'user': msgs.pop(0)
    r = anthropic.Anthropic().messages.create(model=MODEL, max_tokens=900, system=f"{SYSTEM}\nPerson's profile: {json.dumps(prof)}\nReference info:\n{ctx}", messages=msgs + [{'role': 'user', 'content': content}])
    return r.content[0].text
def reply(msg, hist, prof, fbytes=None, mime=None):
    hits = search(msg, 4) if msg else []
    key = os.environ.get('ANTHROPIC_API_KEY')
    if key:
        try: return llm(msg, hist, prof, '\n\n'.join(fmt(i) for s, i in hits if s > .12), fbytes, mime), 'ai'
        except Exception: pass
    if fbytes: return "I can read photos and PDFs only when an AI key is set up (see README). You can still type or speak your question.", 'basic'
    if hits and hits[0][0] > .12: return fmt(hits[0][1]), 'basic'
    return "I couldn't find a clear answer. Try other words (for example 'Aadhaar address update' or 'scholarship documents') or use the Documents tab.", 'basic'
