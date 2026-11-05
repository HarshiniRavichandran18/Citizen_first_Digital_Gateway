# Citizen-First Digital Gateway for Welfare

Voice-first guidance on government schemes, documents and application steps in **Tamil, English and Tanglish**. Flask backend + plain HTML/CSS/JS (no frontend framework).

## Run
```
pip install -r requirements.txt
python ml/train_intent.py     # optional: retrain intent model
python app.py                 # http://127.0.0.1:5000
python tests/test_app.py      # automated tests
```
Voice input/output uses the browser (Chrome/Edge best). Speech recognition needs https or localhost.

## Configuration (environment variables)
| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Optional. Enables natural AI answers and reading photos/PDFs. PowerShell: `$env:ANTHROPIC_API_KEY="..."`; Mac/Linux: `export ANTHROPIC_API_KEY=...` |
| `CLAUDE_MODEL`, `AI_TIMEOUT_SECONDS` | Model name (default `claude-sonnet-5-5`) and timeout (25 s) |
| `UPLOAD_MAX_MB` | Platform upload limit (default 5). Backend limit and frontend check both use it. Not a government-portal limit. |
| `DASHBOARD_KEY` | Enables `/dashboard?key=...`; disabled if unset |
| `FLASK_DEBUG` | `1` only for development. Use a WSGI server (e.g. gunicorn) in production |

**Works without a key:** scheme search, explorer, recommendations, document checklists, steps, file validation, text/voice chat (answers from built-in data, keyword-based Tamil/Tanglish).
**Needs a key:** conversational answers and reading uploaded files (file sent only after the user ticks consent).

## Structure
`app.py` routes · `chat.py` chatbot/search/AI · `langutil.py` language detection + Tamil/Tanglish query expansion · `filecheck.py` upload validation · `dsa.py` question tree + document graph (unchanged) · `ml/` intent model (unchanged) · `data/` datasets (unchanged) · `templates/index.html`, `static/app.css`, `static/app.js` frontend · `tests/`.
No files were moved or deleted.

## Privacy
Uploads are validated in memory and never written to disk. Typed/spoken text is not logged (only event types and lengths). Profile stays in browser localStorage. Browser speech recognition may send audio to the browser vendor.

## Data accuracy
`services.json` is a dated snapshot of myScheme; every scheme is flagged "verify on official site", and incomplete records, missing documents/steps and closing dates are flagged in the UI. Nothing was verified against live government sites during this upgrade. Recommendation weights are hand-tuned, not validated.

## Known limitations
- Tamil/Tanglish understanding in basic mode is keyword expansion plus character n-gram search; it can pick a loosely related scheme. Full understanding needs the AI key.
- Tanglish speech is recognised as Indian English and read with an English voice.
- Tamil text-to-speech requires a Tamil voice installed on the device.
- Scheme content (and FAQs) is English only; Tamil/Tanglish replies translate the assistant's framing, not the dataset.
- Voice, responsive layout and real AI calls were not tested in real browsers/with a live key (see report).

## Future upgrades (NOT implemented)
DigiLocker integration (requires official API access, consent and security review); verified per-portal file-size/format table; Tamil dataset translations; OCR fallback without AI.
