"""T-IN-08 - the form names the edge rate limit.

A Cloudflare rule limits POST /api/apply to 5 per 10 s per IP (on since 2026-10-23). Its 429 is an
HTML page, so the form used to say "HTTP 429" with no instruction. It now says what to do, and the
operations doc records that the rule is on.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / "web" / "src" / "pages" / "Apply.tsx"
OPS = ROOT / "docs" / "INTAKE_OPERATIONS.md"


def test_the_form_handles_429_with_an_instruction() -> None:
    text = FORM.read_text(encoding="utf-8")
    assert "r.status === 429" in text, "Apply.tsx does not special-case the edge 429"
    assert "Wait ten seconds" in text, "the 429 sentence does not tell the visitor what to do"


def test_the_operations_doc_says_the_edge_limit_is_on() -> None:
    text = OPS.read_text(encoding="utf-8")
    assert "5 per 10 s per IP" in text, "INTAKE_OPERATIONS.md does not record the edge rule"
