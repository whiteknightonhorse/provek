"""Shared readers for the method-note gates. No assertions here - only loading.

The four note laws are separate test modules so that each one has its own kept red run under
`evidence/`, but they read the same three things: the committed sources, the freshness manifest,
and (when this checkout has been built) the emitted HTML.

WHAT RUNS WHERE, AND WHY IT MATTERS. Everything that can be judged from the SOURCE is judged from
the source, so the gate is armed in CI, where `web/dist` does not exist. Only the checks that are
genuinely about the shipped document - structured data, the rendered figures, the sitemap - are
allowed to depend on a build, and those are the ones that would otherwise be checking a template
instead of an artefact (L-3).
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "notes" / "src"
MANIFEST = ROOT / "web" / "notes" / "manifest.json"
DIST = ROOT / "web" / "dist"
NOTES_DIST = DIST / "method" / "notes"

FRONT = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


def sources() -> list[tuple[dict, str]]:
    """(front matter, body) for every committed note, sorted by slug."""
    if not SRC.exists():
        return []
    out = []
    for f in sorted(SRC.glob("*.md")):
        m = FRONT.match(f.read_text(encoding="utf-8"))
        assert m, f"{f.name}: no front matter"
        out.append((json.loads(m.group(1)), m.group(2).strip()))
    return out


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["notes"] if MANIFEST.exists() else {}


def keyword_base() -> dict[str, dict]:
    rows = {}
    with (ROOT / "seo" / "keywords.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows[r["key"]] = r
    return rows


def emitted() -> dict[str, str]:
    """slug -> emitted HTML, empty when this checkout has not been built."""
    if not NOTES_DIST.exists():
        return {}
    return {
        d.name: (d / "index.html").read_text(encoding="utf-8")
        for d in sorted(NOTES_DIST.iterdir())
        if d.is_dir() and (d / "index.html").exists()
    }


def strip_tags(html: str) -> str:
    """The reading text of an emitted page: no script, no style, no markup."""
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S)
    html = re.sub(r"<svg.*?</svg>", " ", html, flags=re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html).strip()


def ld_blocks(html: str) -> list[dict]:
    return [json.loads(m) for m in
            re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]


def paragraphs(body: str) -> list[str]:
    return [b.strip() for b in body.split("\n\n")
            if b.strip() and not b.strip().startswith(("#", "|", "{{", "-", "*"))]


def normalise(s: str) -> str:
    """Case and punctuation folded. Without this a test that wants the key in the title forces the
    title to be written as a lowercase search string, which is how pages start looking machine-made."""
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
