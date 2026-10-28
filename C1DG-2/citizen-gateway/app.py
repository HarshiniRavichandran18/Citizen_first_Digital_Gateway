import json, sqlite3, time, pickle, re, os
from pathlib import Path
from flask import Flask, request, jsonify, render_template
from markupsafe import escape
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dsa import next_question, answer_keywords, build_graph, related
from ml.train_intent import train
import chat, filecheck, langutil

BASE = Path(__file__).parent
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = int((filecheck.MAX_MB + 1) * 1024 * 1024)   # request limit = UPLOAD_MAX_MB (default 5) + 1 MB form overhead; frontend reads it from /api/status
SERVICES = json.load(open(BASE / 'data' / 'services.json', encoding='utf-8'))
INDEX = {s['service_id']: s for s in SERVICES}
CATS = sorted({s['category'] for s in SERVICES})                  # hash map: O(1) lookup
GRAPH = build_graph(SERVICES)
MODEL = pickle.load(open(BASE / 'ml' / 'intent_model.pkl', 'rb')) if (BASE / 'ml' / 'intent_model.pkl').exists() else train()
VEC = TfidfVectorizer(stop_words='english')
MATRIX = VEC.fit_transform([f"{s['service_name']} {s['description']} {' '.join(s['eligibility'])}" for s in SERVICES])
W = {'category': .40, 'eligibility': .25, 'location': .20, 'requirement': .15}   # hand-tuned: test against labelled cases
DB = BASE / 'gateway.db'
PROCS = json.load(open(BASE / 'data' / 'procedures.json', encoding='utf-8'))
chat.init(SERVICES, PROCS, json.load(open(BASE / 'data' / 'faqs.json', encoding='utf-8')))

def db():
    c = sqlite3.connect(DB); c.execute('CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, sid TEXT, ts REAL, event TEXT, detail TEXT)'); return c
def log(sid, event, detail=''):
    with db() as c: c.execute('INSERT INTO events(sid,ts,event,detail) VALUES(?,?,?,?)', (sid, time.time(), event, str(detail)))

@app.get('/')
def home(): return render_template('index.html')

@app.errorhandler(413)
def too_big(e): return jsonify(error='too_big', message=f'File too large (limit {filecheck.MAX_MB:g} MB).'), 413
@app.errorhandler(404)
def nf(e): return jsonify(error='not_found'), 404
@app.errorhandler(Exception)
def boom(e):   # never leak stack traces / secrets
    if hasattr(e, 'code') and isinstance(e.code, int): return jsonify(error=getattr(e, 'name', 'error')), e.code
    app.logger.error('unhandled %s', type(e).__name__); return jsonify(error='server_error', message='Something went wrong. Please try again.'), 500
def body(): return request.get_json(silent=True) or {}

@app.get('/api/status')
def status(): return jsonify(ai=bool(os.environ.get('ANTHROPIC_API_KEY')), max_upload_mb=filecheck.MAX_MB, schemes=len(SERVICES), formats=['PDF', 'JPG', 'PNG', 'WEBP'])

@app.post('/api/understand')
def understand():
    d = body(); sid = d.get('sid', ''); cat = d.get('category'); conf = 1.0
    if not cat:
        q = str(d.get('query', ''))[:500]; log(sid, 'query', f'len={len(q)}')
        p = MODEL.predict_proba([q])[0]; i = p.argmax(); conf = float(p[i]); cat = MODEL.classes_[i] if conf >= 0.28 else None
        log(sid, 'intent', f'{cat}|{conf:.2f}')
    return jsonify(category=cat, confidence=conf, question=next_question(cat, []) if cat else None)

@app.post('/api/question')
def question():
    d = body(); return jsonify(question=next_question(d.get('category'), d.get('answers', [])))

@app.post('/api/recommend')
def recommend():
    d = body(); cat, ans = d.get('category'), d.get('answers', [])
    if cat not in CATS: return jsonify(error='bad_category'), 400
    kws = answer_keywords(cat, ans); tn = any(a.startswith('Tamil Nadu') for a in ans)
    sims = cosine_similarity(VEC.transform([(d.get('query') or cat) + ' ' + ' '.join(ans)]), MATRIX)[0]
    top = sims.max() or 1; out = []
    for s, sim in zip(SERVICES, sims):
        et = ' '.join(s['eligibility']).lower()
        parts = {'category': float(s['category'] == cat),
                 'eligibility': sum(k in et for k in kws) / len(kws) if kws else .5,
                 'location': 1.0 if s['level'] == 'Central' or (tn and s.get('state') == 'Tamil Nadu') else 0.0,
                 'requirement': float(sim / top)}
        score = round(100 * sum(W[k] * v for k, v in parts.items()))
        why = [t for ok, t in [(parts['category'], f'Category: {cat}'), (kws and parts['eligibility'] > 0, 'Matches your answers'),
                               (parts['location'], 'Applies in your state'), (parts['requirement'] > .5, 'Similar to what you described')] if ok]
        out.append({'id': s['service_id'], 'name': s['service_name'], 'level': s['level'], 'score': score,
                    'label': 'High' if score >= 75 else 'Possible' if score >= 55 else 'Weak', 'why': why})
    out = sorted(out, key=lambda x: -x['score'])[:6]
    log(d.get('sid', ''), 'recommended', f'{cat}|{len(ans)} answers'); return jsonify(results=out)

@app.get('/api/service/<sid_>')
def service(sid_):
    s = INDEX.get(sid_)
    if not s: return jsonify(error='not found'), 404
    log(request.args.get('sid', ''), 'opened', s['service_name'])
    return jsonify(service=s, card=chat.card(s, True), related=[{'id': r, 'name': INDEX[r]['service_name']} for r in related(GRAPH, sid_) if r in INDEX])

@app.post('/api/log')
def api_log():
    d = body(); log(d.get('sid', ''), str(d.get('event', ''))[:40], str(d.get('detail', ''))[:80]); return jsonify(ok=True)

def safe_json(raw, default):
    try: v = json.loads(raw); return v if isinstance(v, type(default)) else default
    except Exception: return default

@app.post('/api/chat')
def chat_api():
    f = request.files.get('file'); msg = request.form.get('message', '').strip()[:1500]
    log(request.form.get('sid', ''), 'chat', 'file' if f else 'text')   # message text is NOT stored
    lang = request.form.get('lang', 'auto'); data = f.read() if f else None; finfo = None
    if f:
        ok, key, finfo = filecheck.validate(f.filename, data)
        if not ok: return jsonify(error=key, message=chat.T['file_err'][key].format(max_mb=filecheck.MAX_MB)), 400
    intent = None
    if msg:
        p = MODEL.predict_proba([msg])[0]; intent = MODEL.classes_[p.argmax()] if p.max() >= .28 else None
    r = chat.reply(msg, safe_json(request.form.get('history', '[]'), []), safe_json(request.form.get('profile', '{}'), {}), data, finfo and finfo['mime'],
                   lang, request.form.get('consent') == '1', request.form.get('context') or None, intent, finfo)
    return jsonify(**r)

@app.post('/api/validate-file')
def validate_file():   # standalone check, no AI, nothing stored
    f = request.files.get('file')
    if not f: return jsonify(ok=False, error='empty', message='No file received.'), 400
    ok, key, info = filecheck.validate(f.filename, f.read())
    return jsonify(ok=ok, code=key, info=info, message='File looks valid and can be processed.' if ok else chat.T['file_err'][key].format(max_mb=filecheck.MAX_MB)), (200 if ok else 400)

@app.get('/api/schemes')
def schemes():
    q = request.args.get('q', '').strip()[:200]; cat = request.args.get('category', ''); lvl = request.args.get('level', '')
    page = max(int(request.args.get('page', 1) or 1), 1); per = 12
    if q:
        ids = [i['id'] for sc, i in chat.search(q, 400, ('Scheme',)) if sc > .06]
        pool = [INDEX[i] for i in ids]
    else: pool = SERVICES
    pool = [s for s in pool if (not cat or s['category'] == cat) and (not lvl or s['level'].startswith(lvl))]
    return jsonify(total=len(pool), page=page, categories=CATS, results=[chat.card(s) for s in pool[(page - 1) * per: page * per]])

@app.get('/api/documents')
def documents():
    log(request.args.get('sid', ''), 'documents')
    hits = [h for h in chat.search(request.args.get('q', ''), 5, ('Process', 'Scheme')) if h[0] > .08]
    return jsonify(results=[{'type': i['type'], 'title': i['title'], 'docs': i.get('docs', []), 'steps': i.get('steps', []), 'url': i.get('url', ''), 'note': i.get('note', '')} for _, i in hits])

OCC = {'Student': ['student', 'scholarship'], 'Farmer': ['farmer', 'agricultur'], 'Self-employed / unemployed': ['entrepreneur', 'skill training', 'self employ'], 'Worker': ['worker', 'labour'], 'Retired': ['old age', 'pension']}
COM = {'SC': ['scheduled caste', 'adi dravidar'], 'ST': ['scheduled tribe', 'tribal'], 'BC/MBC': ['backward class', 'most backward', 'denotified']}
@app.post('/api/matches')
def matches():
    p = body().get('profile', {}); t = {}
    if int(p.get('age') or 0) >= 60: t['Senior citizen'] = ['old age', 'senior citizen', 'elderly', '60 years']
    if p.get('gender') == 'Female': t['Woman'] = ['women', 'woman', 'girl']
    if p.get('widow'): t['Widow'] = ['widow']
    if p.get('disabled'): t['Differently abled'] = ['differently abled', 'disab']
    if p.get('occupation') in OCC: t[p['occupation']] = OCC[p['occupation']]
    if p.get('occupation') == 'Student' and p.get('education'): t[p['education']] = {'School': ['school'], 'College': ['college', 'higher education']}[p['education']]
    if p.get('community') in COM: t[p['community']] = COM[p['community']]
    out = []
    for s in SERVICES:
        if s.get('closed') or not (s['level'] == 'Central' or (p.get('state', 'Tamil Nadu') == 'Tamil Nadu' and s.get('state') == 'Tamil Nadu')): continue
        blob = f"{s['service_name']} {' '.join(s['eligibility'])} {s['tags']} {s['description']}".lower()
        why = [n for n, kws in t.items() if any(re.search(r'\b' + re.escape(k), blob) for k in kws)]
        if why: out.append({'id': s['service_id'], 'name': s['service_name'], 'why': why, 'n': len(why) + (.5 if s['complete'] else 0)})
    out.sort(key=lambda x: -x['n']); return jsonify(matches=out[:15])

@app.get('/dashboard')
def dashboard():
    if not os.environ.get('DASHBOARD_KEY') or request.args.get('key') != os.environ['DASHBOARD_KEY']: return jsonify(error='not_found'), 404   # disabled unless DASHBOARD_KEY is set
    with db() as c:
        funnel = [(e, c.execute('SELECT COUNT(DISTINCT sid) FROM events WHERE event=?', (e,)).fetchone()[0]) for e in ['query', 'recommended', 'opened', 'apply_click']]
        intents = c.execute("SELECT substr(detail,1,instr(detail,'|')-1), COUNT(*) FROM events WHERE event='intent' GROUP BY 1 ORDER BY 2 DESC").fetchall()
        opened = c.execute("SELECT detail, COUNT(*) FROM events WHERE event='opened' GROUP BY 1 ORDER BY 2 DESC LIMIT 5").fetchall()
    t = lambda title, rows: f'<h3>{title}</h3><table border=1 cellpadding=6>' + ''.join(f'<tr><td>{escape(a)}</td><td>{b}</td></tr>' for a, b in rows) + '</table>'
    return f'<body style="font-family:sans-serif;max-width:640px;margin:2rem auto"><h2>Pilot analytics</h2>{t("Funnel (unique sessions)", funnel)}{t("Detected intents", intents)}{t("Most opened services", opened)}</body>'

if __name__ == '__main__': app.run(host=os.environ.get('HOST', '127.0.0.1'), port=int(os.environ.get('PORT', 5000)), debug=os.environ.get('FLASK_DEBUG') == '1')
