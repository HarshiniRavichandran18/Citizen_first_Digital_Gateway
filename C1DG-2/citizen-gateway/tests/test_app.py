"""Run: python -m pytest -q tests  (or: python tests/test_app.py)"""
import io, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.pop('ANTHROPIC_API_KEY', None)
import app as A, chat, langutil, filecheck
from PIL import Image
C = A.app.test_client()
def png(): b = io.BytesIO(); Image.new('RGB', (40, 40), 'white').save(b, 'PNG'); return b.getvalue()
def pdf():
    from pypdf import PdfWriter
    w = PdfWriter(); w.add_blank_page(100, 100); b = io.BytesIO(); w.write(b); return b.getvalue()
def ask(m, **kw): return C.post('/api/chat', data={'message': m, **kw}).get_json()
def test_lang_detect():
    assert langutil.detect('எனக்கு அரசு உதவித்தொகைக்கு எப்படி விண்ணப்பிப்பது?') == 'ta'
    assert langutil.detect('How can I apply for a government scholarship?') == 'en'
    assert langutil.detect('Enakku scholarship apply panna enna documents venum?') == 'tanglish'
def test_text_chat_three_styles():
    for q in ['எனக்கு விவசாயி திட்டங்கள் என்ன?', 'Are there any schemes for farmers?', 'Enakku vivasayi schemes enna irukku?']:
        r = ask(q); assert r['mode'] == 'basic' and r['reply'] and r['cards'], q
def test_followup_uses_context():
    r = ask('scholarship for college students'); sid = r['context']; assert sid
    r2 = ask('eligibility enna?', context=sid); assert 'Official source' in r2['reply'] and r2['context'] == sid
def test_unclear_asks_question():
    assert '?' in ask('zzzz qqqq')['reply']
def test_sensitive_blocked():
    assert 'Aadhaar' in ask('my aadhaar is 1234 5678 9012')['reply']
def test_ai_failure_falls_back(monkeypatch=None):
    os.environ['ANTHROPIC_API_KEY'] = 'bad'; old = chat.llm
    chat.llm = lambda *a, **k: (_ for _ in ()).throw(TimeoutError())
    try: r = ask('farmer schemes'); assert r['mode'] == 'basic' and r['notice'] and r['cards']
    finally: chat.llm = old; os.environ.pop('ANTHROPIC_API_KEY')
def test_files():
    up = lambda n, d, **kw: C.post('/api/validate-file', data={'file': (io.BytesIO(d), n)})
    assert up('a.png', png()).status_code == 200 and up('a.pdf', pdf()).status_code == 200
    assert up('a.exe', b'MZ').get_json()['code'] == 'bad_ext'
    assert up('a.png', b'not an image').get_json()['code'] == 'type_mismatch'
    assert up('a.png', png()[:60]).get_json()['code'] in ('corrupt',)
    assert up('a.pdf', b'%PDF-1.4 garbage').get_json()['code'] == 'corrupt'
    r = C.post('/api/validate-file', data={'file': (io.BytesIO(b'0' * int(7 * 1048576)), 'a.pdf')}); assert r.status_code == 413
def test_doc_without_text_basic_mode():
    r = C.post('/api/chat', data={'file': (io.BytesIO(png()), 'a.png'), 'message': ''}).get_json(); assert 'AI service' in r['reply'] and r['mode'] == 'basic'
def test_schemes_and_detail():
    r = C.get('/api/schemes?q=scholarship&category=Education').get_json(); assert r['total'] > 0
    d = C.get('/api/service/' + r['results'][0]['id']).get_json(); assert 'snapshot' in d['card']['flags'] and d['card']['url'].startswith('https://')
    assert C.get('/api/service/nope').status_code == 404
def test_matches_documents_errors():
    assert C.post('/api/matches', json={'profile': {'age': 70}}).get_json()['matches']
    assert C.get('/api/documents?q=income certificate').get_json()['results']
    assert C.post('/api/understand', data='bad').status_code == 200   # malformed body must not crash
    assert C.get('/dashboard').status_code == 404
def test_pages():
    h = C.get('/').get_data(as_text=True); assert 'Talk to Your Citizen Assistant' in h and 'digilocker' not in h.lower()
if __name__ == '__main__':
    import traceback; fails = 0
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            try: f(); print('PASS', n)
            except Exception: fails += 1; print('FAIL', n); traceback.print_exc()
    sys.exit(fails)
