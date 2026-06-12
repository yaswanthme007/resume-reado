"""
Resume Extraction Agent (Groq)
==============================

A simple AI agent that reads a resume (PDF or text) and extracts useful,
structured details using a model served by the Groq API.

Usage:
    python resume_agent.py path/to/resume.pdf
    python resume_agent.py path/to/resume.txt --out result.json

Requires the GROQ_API_KEY environment variable to be set.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from groq import Groq
from pydantic import BaseModel, Field, ValidationError

# A fast, capable open model on Groq. Swap for another listed at
# https://console.groq.com/docs/models if you prefer.
MODEL = "llama-3.3-70b-versatile"


# ---------------------------------------------------------------------------
# 1. Define the shape of the data we want to pull out of a resume.
# ---------------------------------------------------------------------------
class Education(BaseModel):
    institution: Optional[str] = Field(default=None, description="School / university name")
    degree: Optional[str] = Field(default=None, description="Degree or qualification")
    field_of_study: Optional[str] = Field(default=None, description="Major or field")
    graduation_year: Optional[str] = Field(default=None, description="Year completed or expected")


class Experience(BaseModel):
    company: Optional[str] = Field(default=None, description="Employer / organization name")
    title: Optional[str] = Field(default=None, description="Job title or role")
    start_date: Optional[str] = Field(default=None, description="When the role started")
    end_date: Optional[str] = Field(default=None, description="When it ended, or 'Present'")
    summary: Optional[str] = Field(default=None, description="One-line summary of what they did")


class ResumeDetails(BaseModel):
    name: Optional[str] = Field(default=None, description="Candidate's full name")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: Optional[str] = Field(default=None, description="City / region")
    links: List[str] = Field(default_factory=list, description="LinkedIn, GitHub, portfolio, etc.")
    summary: Optional[str] = Field(default=None, description="Short professional summary")
    skills: List[str] = Field(default_factory=list, description="Technical and soft skills")
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    total_years_experience: Optional[float] = Field(
        default=None, description="Rough estimate of total years of work experience"
    )


# ---------------------------------------------------------------------------
# 2. Read a resume file into plain text. PDFs are parsed with pypdf.
# ---------------------------------------------------------------------------
def read_resume_text(resume_path: Path) -> str:
    if resume_path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            raise SystemExit("Reading PDFs needs pypdf. Install it with: pip install pypdf")

        reader = PdfReader(str(resume_path))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        if not text.strip():
            raise SystemExit(
                "Could not extract text from this PDF (it may be scanned images). "
                "Try a text-based resume instead."
            )
        return text

    # Treat everything else (.txt, .md, etc.) as plain text.
    return resume_path.read_text(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# 3. The agent: send the resume text to Groq and get back structured details.
# ---------------------------------------------------------------------------
def extract_resume(resume_text: str) -> ResumeDetails:
    client = Groq()  # reads GROQ_API_KEY from the environment

    schema = json.dumps(ResumeDetails.model_json_schema(), indent=2)
    system_prompt = (
        "You are a precise resume-parsing assistant. Read the resume and extract "
        "structured candidate information. Only use information present in the "
        "document — never invent values. Use null for missing fields and [] for "
        "missing lists.\n\n"
        "Respond with a single JSON object that matches this JSON schema:\n"
        f"{schema}"
    )

    completion = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"RESUME:\n\n{resume_text}"},
        ],
    )

    raw = completion.choices[0].message.content
    try:
        return ResumeDetails.model_validate_json(raw)
    except ValidationError:
        # Model returned JSON that doesn't fully fit the schema — surface it raw.
        data = json.loads(raw)
        return ResumeDetails.model_validate(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract useful details from a resume using AI.")
    parser.add_argument("resume", help="Path to the resume file (.pdf, .txt, .md)")
    parser.add_argument("--out", help="Optional path to write the JSON result", default=None)
    args = parser.parse_args()

    if not os.environ.get("GROQ_API_KEY"):
        print("Error: set the GROQ_API_KEY environment variable first.", file=sys.stderr)
        return 1

    resume_path = Path(args.resume)
    if not resume_path.is_file():
        print(f"Error: file not found: {resume_path}", file=sys.stderr)
        return 1

    print(f"Reading {resume_path.name} ...", file=sys.stderr)
    resume_text = read_resume_text(resume_path)
    details = extract_resume(resume_text)

    output = details.model_dump_json(indent=2)
    print(output)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"\nSaved to {args.out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
