# Résumé Intelligence — AI Résumé Parser

A small AI agent that reads a résumé (PDF or text) and extracts useful,
structured details — name, contact, links, summary, skills, experience,
education, and an estimate of total years of experience.

It ships in two forms:

| Version | File(s) | Where it runs |
|---------|---------|---------------|
| **Static web app** (deployed) | `index.html` | 100% in the browser — hosted on GitHub Pages |
| **Command-line / Flask** | `resume_agent.py`, `app.py` | Locally, with your key as an env var |

## 🌐 Live (GitHub Pages)

**https://yaswanthme007.github.io/resume-reado/**

1. Paste your free Groq API key (from <https://console.groq.com/keys>) — it's
   stored **only in your browser** (localStorage), never uploaded or committed.
2. Drop a résumé (PDF / TXT / MD).
3. Click **Extract details**.

The browser reads the file (PDFs via [PDF.js](https://mozilla.github.io/pdf.js/))
and calls the Groq API directly — there is no backend, so no secret ever lives
in this repo.

## 🖥️ Run locally (Flask version, key stays server-side)

```powershell
pip install -r requirements.txt
$env:GROQ_API_KEY = "gsk_your_key"
python app.py        # open http://127.0.0.1:5000
```

Or the command line only:

```powershell
python resume_agent.py sample_resume.txt --out result.json
```

## How it works

The model is Groq-hosted **`llama-3.3-70b-versatile`**, called in JSON mode with
the target schema embedded in the prompt, so the response is always valid,
parseable JSON. The static and Flask versions share the same schema and prompt.

> Note: scanned / image-only PDFs have no extractable text — use a text-based
> résumé in that case.

## Files

- `index.html` — the deployed static web app (browser-only)
- `app.py` — Flask server for local use (`/` + `/api/extract`)
- `templates/index.html` — frontend for the Flask version
- `resume_agent.py` — the agent logic (Groq + Pydantic)
- `sample_resume.txt` — a sample résumé to try
- `requirements.txt` — Python dependencies
