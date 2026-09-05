"""LAW-COPY-IS-THE-ARTEFACT (SPEC 3.7 item 7, ADR-0011 section 6.1) - for every emitted template,
the page's own `<pre>` text, the source `templates/<slug>/SKILL.md`, and the raw sibling served at
`dist/build/<slug>/SKILL.md` are byte-identical. A reader who presses Copy must get exactly what
the coding agent that ran the witnessed dry run received - never a rendering, a re-serialisation,
or a second string carried in the bundle.

T-74 Phase 4 review (ruling `74-...q-1`, section 2.1-2.3) found a second Copy control this file never
armed: the template card on `/build/` itself (`web/src/pages/Build.tsx` `TemplateCard`) does not
read the page's `<pre>` at all - it reads `t.raw` off the `Template` object embedded in
`window.__PROVEK__.templates[]` on `/build/`'s own emitted page. The same object, serialised the
same way, is also what a coding agent fetching `/data/templates.json` or
`/data/templates/<slug>.json` receives (`web/prerender.mjs`: `write("/build/", ...,
{ templatesIndex: templates })`, `writeFileSync(.../"templates.json", JSON.stringify({templates}))`,
`writeFileSync(.../"templates/<slug>.json", JSON.stringify({template: t}))`). Today those three
channels happen to agree with the source because they are emitted from the same in-memory object -
but nothing here had ever measured that; RED-042's precedent (a promise with no kept red run behind
it is not measured, it is asserted) applies to this gate exactly as it did to the two template laws.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
DIST = ROOT / "web" / "dist" / "build"
DATA = ROOT / "web" / "dist" / "data"
BUILD_INDEX = DIST / "index.html"


def _pre_text(page_html: str, slug: str) -> str:
    m = re.search(
        rf'<pre id="skill-source-{re.escape(slug)}"[^>]*>([\s\S]*?)</pre>', page_html
    )
    assert m, f"no <pre id=\"skill-source-{slug}\"> found on the template page"
    # The DOM's own textContent is what a reader's click reads (CopyButton reads
    # `.textContent` off this node) - the served bytes are HTML-escaped (`>` etc.), so the
    # comparison is against what a browser would hand back, not against the raw markup.
    return html.unescape(m.group(1))


def _provek_data(page_html: str) -> dict:
    m = re.search(r"window\.__PROVEK__=(\{.*?\})</script>", page_html)
    assert m, "no window.__PROVEK__=... inline script found on the page"
    return json.loads(m.group(1))


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
    assert BUILD_INDEX.is_file(), f"no /build/ index emitted at {BUILD_INDEX}"
    index_raw_by_slug = {
        t["slug"]: t["raw"] for t in _provek_data(BUILD_INDEX.read_text(encoding="utf-8"))["templates"]
    }
    templates_json = json.loads((DATA / "templates.json").read_text(encoding="utf-8"))
    templates_json_raw_by_slug = {t["slug"]: t["raw"] for t in templates_json["templates"]}

    mismatches = {}
    for slug in slugs:
        source = (TEMPLATES / slug / "SKILL.md").read_text(encoding="utf-8")
        raw_path = DIST / slug / "SKILL.md"
        page_path = DIST / slug / "index.html"
        slug_json_path = DATA / "templates" / f"{slug}.json"
        assert raw_path.is_file(), f"no raw sibling emitted at dist/build/{slug}/SKILL.md"
        assert page_path.is_file(), f"no page emitted at dist/build/{slug}/index.html"
        assert slug_json_path.is_file(), f"no data channel emitted at dist/data/templates/{slug}.json"
        raw = raw_path.read_text(encoding="utf-8")
        pre = _pre_text(page_path.read_text(encoding="utf-8"), slug)
        # The /build/ index card's CopyButton reads `t.raw` off this object, never off a <pre> -
        # this IS the actual read path, not a proxy for it (Build.tsx TemplateCard).
        index_raw = index_raw_by_slug.get(slug)
        # /data/templates.json and /data/templates/<slug>.json are the machine-fetchable siblings
        # of the same object (SPEC 3.7 item 6) - a coding agent may fetch either instead of the
        # rendered page, and LAW-COPY-IS-THE-ARTEFACT makes no exception for that path.
        templates_json_raw = templates_json_raw_by_slug.get(slug)
        slug_json_raw = json.loads(slug_json_path.read_text(encoding="utf-8"))["template"]["raw"]
        values = {
            "source": source, "raw_sibling": raw, "pre_dom": pre,
            "build_index___PROVEK__": index_raw,
            "data_templates_json": templates_json_raw,
            "data_templates_slug_json": slug_json_raw,
        }
        if len(set(values.values())) != 1:
            mismatches[slug] = {k: len(v) if v is not None else None for k, v in values.items()}
    assert not mismatches, f"copy payload diverged from the source: {mismatches}"


# --- control: the equality check must be able to fail ------------------------------------------

def test_the_equality_check_catches_a_single_byte_difference():
    source = "## What to build\n\nSome text.\n"
    mutated = source + "\n"
    assert source != mutated, "the mutation did not change anything - fixture is vacuous"
