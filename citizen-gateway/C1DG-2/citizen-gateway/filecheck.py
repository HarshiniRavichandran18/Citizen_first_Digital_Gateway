"""Backend validation of uploaded documents. Files are inspected in memory only - nothing is written to disk."""
import io, os
MAX_MB = float(os.environ.get('UPLOAD_MAX_MB', 5))
ALLOWED = {'.pdf': 'application/pdf', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}
def sniff(b):
    if b[:5] == b'%PDF-': return 'application/pdf'
    if b[:3] == b'\xff\xd8\xff': return 'image/jpeg'
    if b[:8] == b'\x89PNG\r\n\x1a\n': return 'image/png'
    if b[:4] == b'RIFF' and b[8:12] == b'WEBP': return 'image/webp'
def validate(filename, data):
    """-> (ok, message_key, info). message_key is a stable code; the frontend/chat localise it."""
    ext = os.path.splitext(filename or '')[1].lower()
    if ext not in ALLOWED: return False, 'bad_ext', {}
    if not data: return False, 'empty', {}
    if len(data) > MAX_MB * 1024 * 1024: return False, 'too_big', {'max_mb': MAX_MB}
    real = sniff(data)
    if real is None or real != ALLOWED[ext] and not (real == 'image/jpeg' and ext in ('.jpg', '.jpeg')): return False, 'type_mismatch', {}
    info = {'mime': real, 'size_kb': round(len(data) / 1024, 1)}
    try:
        if real == 'application/pdf':
            from pypdf import PdfReader
            r = PdfReader(io.BytesIO(data))
            if r.is_encrypted: return False, 'encrypted', {}
            info['pages'] = len(r.pages)
            if not info['pages']: return False, 'corrupt', {}
        else:
            from PIL import Image
            im = Image.open(io.BytesIO(data)); im.verify(); im = Image.open(io.BytesIO(data)); im.load()
            info['width'], info['height'] = im.size
    except Exception: return False, 'corrupt', {}
    return True, 'ok', info
