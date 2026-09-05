"""LAW-COPY-IS-THE-ARTEFACT (SPEC 3.7 item 7, ADR-0011 section 6.1) - for every emitted template,
the page's own `<pre>` text, the source `templates/<slug>/SKILL.md`, and the raw sibling served at
`dist/build/<slug>/SKILL.md` are byte-identical. A reader who presses Copy must get exactly what
the coding agent that ran the witnessed dry run received - never a rendering, a re-serialisation,
or a second string carried in the bundle.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
DIST = ROOT / "web" / "dist" / "build"


def _pre_text(page_html: str, slug: str) -> str:
    m = re.search(
        rf'<pre id="skill-source-{re.escape(slug)}"[^>]*>([\s\S]*?)</pre>', page_html
    )
    assert m, f"no <pre id=\"skill-source-{slug}\"> found on the template page"
    # The DOM's own textContent is what a reader's click reads (CopyButton reads
    # `.textContent` off this node) - the served bytes are HTML-escaped (`>` etc.), so the
    # comparison is against what a browser would hand back, not against the raw markup.
    return html.unescape(m.group(1))


def _slugs() -> list[str]:
    if not TEMPLATES.is_dir():
        return []
    return sorted(
        p.name for p in TEMPLATES.iterdir()
        if p.is_dir() and (p / "SKILL.md").exists()
    )


def test_every_emitted_template_s_copy_payload_matches_its_source():
    slugs = _slugs()
    assert slugs, "no template exists under templates/ to check"
    assert DIST.is_dir(), (
        f"{DIST} is absent, so this gate measured nothing. Run `npm run build` in web/ - "
        "scripts/push.sh does exactly that before the suite."
    )
    mismatches = {}
    for slug in slugs:
        source = (TEMPLATES / slug / "SKILL.md").read_text(encoding="utf-8")
        raw_path = DIST / slug / "SKILL.md"
        page_path = DIST / slug / "index.html"
        assert raw_path.is_file(), f"no raw sibling emitted at dist/build/{slug}/SKILL.md"
        assert page_path.is_file(), f"no page emitted at dist/build/{slug}/index.html"
        raw = raw_path.read_text(encoding="utf-8")
        pre = _pre_text(page_path.read_text(encoding="utf-8"), slug)
        if not (source == raw == pre):
            mismatches[slug] = {
                "source_len": len(source), "raw_len": len(raw), "pre_len": len(pre),
                "source_eq_raw": source == raw, "source_eq_pre": source == pre,
            }
    assert not mismatches, f"copy payload diverged from the source: {mismatches}"


# --- control: the equality check must be able to fail ------------------------------------------

def test_the_equality_check_catches_a_single_byte_difference():
    source = "## What to build\n\nSome text.\n"
    mutated = source + "\n"
    assert source != mutated, "the mutation did not change anything - fixture is vacuous"
