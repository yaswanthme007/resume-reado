"""
Resume Extraction Agent — Web App
=================================

A small Flask server that serves the frontend and exposes an endpoint to
upload a resume and get back structured details via the Groq-powered agent.

Run:
    $env:GROQ_API_KEY = "gsk_..."
    python app.py
    # then open http://127.0.0.1:5000
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request

import resume_agent as agent

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB upload cap

ALLOWED = {".pdf", ".txt", ".md"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/extract", methods=["POST"])
def extract():
    if not os.environ.get("GROQ_API_KEY"):
        return jsonify({"error": "GROQ_API_KEY is not set on the server."}), 500

    file = request.files.get("resume")
    if file is None or not file.filename:
        return jsonify({"error": "No resume file was uploaded."}), 400

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED:
        return jsonify({"error": "Unsupported file type. Use PDF, TXT, or MD."}), 400

    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            file.save(tmp.name)
            tmp_path = Path(tmp.name)

        text = agent.read_resume_text(tmp_path)
        details = agent.extract_resume(text)
        return jsonify(details.model_dump())
    except Exception as exc:  # surface a clean message to the UI
        return jsonify({"error": str(exc)}), 500
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
