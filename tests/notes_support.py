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
    """The reading text of an emitted page: no script, no style, no markup.

    THIS FILTER IS A MEASURING INSTRUMENT, NOT A SANITISER, AND THAT IS WHY IT IS TIGHTENED HERE.

    `test_notes.py` proves "the FAQ answer reaches the reader" by asserting the answer appears in
    `strip_tags(html)`. The same answer text also sits in the JSON-LD block, inside a `<script>`.
    So a script this filter fails to remove does not produce a visible defect - it produces a
    PASS, taken from the schema copy of a sentence that may be nowhere on the page. A gate that
    goes green off the artefact it was supposed to be checking against is invariant 1 wearing
    somebody else's clothes: the instrument failed and reported success.

    Nothing here measures the shape of the tags the generator emits, so the assertions rested on
    it emitting lowercase `<script>` and an exact `</script>` - true when measured 2026-08-24, and
    one formatting change away from being false. `re.I` and the `\\s*` before `>` cost nothing and
    remove that dependency. Raised as CodeQL #40 (`py/bad-tag-filter`), which was very nearly
    dismissed as noise on the grounds that a test helper has no untrusted input to defend against.
    It has no attacker; it does have a claim resting on it.

    TIGHTENED A SECOND TIME, AND #51 IS NOT #40 COMING BACK. The scan that ran after the first
    tightening reported #40 `fixed` at 2026-08-24T11:59:23Z and opened #51 two seconds earlier on
    the replacement line. It is easy to read that pair as one alert re-raised over an edit, and the
    messages say otherwise: #40 was "does not match upper case <SCRIPT> tags", which `re.I` closed,
    and #51 is "does not match script end tags like `</script\\t\\n bar>`" - the NEXT corner case in
    the same query's list, on a hole `\\s*` never covered. A browser ends a script at
    `</script foo="bar">`; this filter did not, so the escape #40 was tightened against was still
    open in a second spelling.

    The lookahead is the part worth reading. `</script[^>]*>` alone would also eat `</scriptfoo>`,
    which is not an end tag in any parser, and a filter that removes MORE than the thing it is
    named for is the same instrument defect pointed the other way - it would delete page text and
    report the page as not containing it. `(?=[\\s/>])` is the HTML end-tag-name rule written out:
    after the name comes whitespace, `/` or `>`, or it is not that tag. The same edit is applied to
    `style` and `svg`, which carry the identical hole and no alert - and absence of an alert is
    `not_measured`, not `clean`.

    What is NOT claimed: that the query is now satisfied. Whether CodeQL accepts a lookahead cannot
    be measured from this host, so #51 is closed by DISMISSAL with the basis below, not by this
    edit, and a future scan is the only thing that can settle it. See `docs/ALERT_TRIAGE.md`.
    """
    html = re.sub(r"<script(?=[\s/>]).*?</script(?=[\s/>])[^>]*>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style(?=[\s/>]).*?</style(?=[\s/>])[^>]*>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<svg(?=[\s/>]).*?</svg(?=[\s/>])[^>]*>", " ", html, flags=re.S | re.I)
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
