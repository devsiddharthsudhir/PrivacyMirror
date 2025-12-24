# Ethical Mirror 🪞 (Fully Offline Privacy Risk Dashboard)

**Ethical Mirror** is a **local-only** tool that shows what a “random company” could infer about you from **your own** emails, notes, and browsing history — while keeping everything **offline**, on your machine.

It’s built to raise privacy awareness and help you reduce oversharing:
- **Inferences:** interests, daily rhythm (wake/sleep tendencies), work patterns, and browsing-derived signals
- **Explainability:** for each inference, it shows the **strongest signals** (keywords, domains, timestamps) that drove it
- **Data minimization:** raw text is processed in-memory by default; you can store only *derived summaries* (encrypted)
- **Secure local vault:** optional encrypted storage of results using AES-GCM (never uploads anything)

> ✅ No cloud calls. No telemetry. No external APIs.  
> ✅ You choose exactly what files to scan.  
> ✅ You can wipe everything with one click.

---

## Quick start

### 1) Requirements
- Python **3.10+** (recommended 3.11)
- Works on Windows / macOS / Linux

### 2) Setup
```bash
git clone <your-repo-url>
cd ethical-mirror

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3) Run
```bash
streamlit run app/main.py
```

Open the local URL Streamlit prints (usually `http://localhost:8501`).

---

## Importing your data (offline)
Ethical Mirror supports:

### Emails
**Option A: Google Takeout (recommended)**
1. Google Takeout → Gmail → export → download
2. Locate the `.mbox` file in the takeout download
3. In the app, choose **Import → Email (MBOX)** and point to that file

**Option B: EML directory**
If you have `.eml` files in a folder, import them.

### Notes
Point to a folder containing `.txt` / `.md` files.

### Browsing history
You can import either:
- Chrome/Edge history SQLite file (you pick the path manually), OR
- A browser export (`.json` / `.html`) if you prefer (limited but safer)

**Chrome/Edge History path (typical)**
- Windows: `C:\Users\<you>\AppData\Local\Google\Chrome\User Data\Default\History`
- macOS: `~/Library/Application Support/Google/Chrome/Default/History`
- Linux: `~/.config/google-chrome/Default/History`

**Important:** browsers lock this file while open.  
Close Chrome/Edge before importing, or copy it to your Desktop and import the copy.

More: see `docs/importing_browser_history.md`

---

## Threat model (what this tool is / is not)
- This tool is **not** spyware and should never be used on other people’s data.
- It requires **explicit user consent** and **explicit file selection**.
- It runs locally, performs analysis, and shows results to the user.

---

## Repo structure
```
ethical-mirror/
  app/                 # Streamlit UI
  core/
    ingest/            # Data import (mbox, eml, notes, browser history)
    nlp/               # cleaning + vectorization
    infer/             # inferences (interests, rhythms, work patterns)
    explain/           # attribution (signals → inference)
    security/          # encrypted local vault
    report/            # assemble report objects
  docs/                # user docs
  tests/               # minimal tests
```

---

## License
MIT (see `LICENSE`).
