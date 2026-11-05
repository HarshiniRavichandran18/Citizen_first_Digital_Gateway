# Citizen 1st Digital Gateway
Run: `pip install -r requirements.txt && python ml/train_intent.py && python app.py` -> http://127.0.0.1:5000 (analytics at /dashboard)
Layers: UI (templates) -> intent ML (ml/) -> question tree + ranking (dsa.py, app.py) -> data/services.json (28 schemes from myScheme, verify before use) -> SQLite log (gateway.db).
Ranking score = 0.40 category + 0.25 eligibility-keyword + 0.20 location + 0.15 TF-IDF similarity. Results are "possible matches", never "eligible".

## New: Assistant, Documents, For Me
- **Assistant** (chat): works offline from the data (basic mode). For natural answers, Tamil/Tanglish understanding and reading photos/PDFs, set an API key before `python app.py`:
  Windows PowerShell `$env:ANTHROPIC_API_KEY="your-key"`; Mac/Linux `export ANTHROPIC_API_KEY=your-key`. Voice typing uses the browser (Chrome/Edge).
- **Documents**: ask for any process (Aadhaar update, income certificate, scheme) to get a checklist + steps. Curated processes live in data/procedures.json - verify on official sites.
- **For Me**: profile is stored only in the browser (localStorage); schemes possibly relevant to it are flagged with a count on the tab.
