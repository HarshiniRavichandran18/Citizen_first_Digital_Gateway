import json, sqlite3, time, pickle, re
from pathlib import Path
from flask import Flask, request, jsonify, render_template
from markupsafe import escape
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dsa import next_question, answer_keywords, build_graph, related
from ml.train_intent import train
import chat

BASE = Path(__file__).parent
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024   # photo/PDF uploads up to ~5 MB
SERVICES = json.load(open(BASE / 'data' / 'services.json', encoding='utf-8'))
INDEX = {s['service_id']: s for s in SERVICES}                  # hash map: O(1) lookup
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

@app.post('/api/understand')
def understand():
    d = request.get_json(); sid = d.get('sid', ''); cat = d.get('category'); conf = 1.0
    if not cat:
        q = d.get('query', ''); log(sid, 'query', q)
        p = MODEL.predict_proba([q])[0]; i = p.argmax(); conf = float(p[i]); cat = MODEL.classes_[i] if conf >= 0.28 else None
        log(sid, 'intent', f'{cat}|{conf:.2f}')
    return jsonify(category=cat, confidence=conf, question=next_question(cat, []) if cat else None)

@app.post('/api/question')
def question():
    d = request.get_json(); return jsonify(question=next_question(d['category'], d.get('answers', [])))

@app.post('/api/recommend')
def recommend():
    d = request.get_json(); cat, ans = d['category'], d.get('answers', [])
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
    return jsonify(service=s, related=[{'id': r, 'name': INDEX[r]['service_name']} for r in related(GRAPH, sid_) if r in INDEX])

@app.post('/api/log')
def api_log():
    d = request.get_json(); log(d.get('sid', ''), d['event'], d.get('detail', '')); return jsonify(ok=True)

@app.post('/api/chat')
def chat_api():
    f = request.files.get('file'); msg = request.form.get('message', '').strip()
    log(request.form.get('sid', ''), 'chat', msg[:200] + (' [file]' if f else ''))
    text, mode = chat.reply(msg, json.loads(request.form.get('history', '[]')), json.loads(request.form.get('profile', '{}')),
                            f.read()[:5_000_000] if f else None, f.mimetype if f else None)
    return jsonify(reply=text, mode=mode)

@app.get('/api/documents')
def documents():
    log(request.args.get('sid', ''), 'documents', request.args.get('q', ''))
    hits = [h for h in chat.search(request.args.get('q', ''), 5, ('Process', 'Scheme')) if h[0] > .08]
    return jsonify(results=[{'type': i['type'], 'title': i['title'], 'docs': i.get('docs', []), 'steps': i.get('steps', []), 'url': i.get('url', ''), 'note': i.get('note', '')} for _, i in hits])

OCC = {'Student': ['student', 'scholarship'], 'Farmer': ['farmer', 'agricultur'], 'Self-employed / unemployed': ['entrepreneur', 'skill training', 'self employ'], 'Worker': ['worker', 'labour'], 'Retired': ['old age', 'pension']}
COM = {'SC': ['scheduled caste', 'adi dravidar'], 'ST': ['scheduled tribe', 'tribal'], 'BC/MBC': ['backward class', 'most backward', 'denotified']}
@app.post('/api/matches')
def matches():
    p = request.get_json().get('profile', {}); t = {}
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
    with db() as c:
        funnel = [(e, c.execute('SELECT COUNT(DISTINCT sid) FROM events WHERE event=?', (e,)).fetchone()[0]) for e in ['query', 'recommended', 'opened', 'apply_click']]
        intents = c.execute("SELECT substr(detail,1,instr(detail,'|')-1), COUNT(*) FROM events WHERE event='intent' GROUP BY 1 ORDER BY 2 DESC").fetchall()
        opened = c.execute("SELECT detail, COUNT(*) FROM events WHERE event='opened' GROUP BY 1 ORDER BY 2 DESC LIMIT 5").fetchall()
    t = lambda title, rows: f'<h3>{title}</h3><table border=1 cellpadding=6>' + ''.join(f'<tr><td>{escape(a)}</td><td>{b}</td></tr>' for a, b in rows) + '</table>'
    return f'<body style="font-family:sans-serif;max-width:640px;margin:2rem auto"><h2>Pilot analytics</h2>{t("Funnel (unique sessions)", funnel)}{t("Detected intents", intents)}{t("Most opened services", opened)}</body>'

if __name__ == '__main__': app.run(debug=True)
