"""T-03 (Fable ruling, 03-landing-never-names-the-agents.ruling-1.md, D-59): the landing's own
"What you can build today" section must name every published template, in the manifest's own
order, in its own words - never a subset, never a stale copy, never a hand-typed second list.

THREE THINGS CHECKED, ALL AGAINST THE SAME TWO SOURCES OF TRUTH
(`templates/manifest.json` and the emitted `dist/data/templates.json`, never a third):

  1. The ordered list of `/build/<slug>/` hrefs inside the new section on `dist/index.html` equals
     `templates/manifest.json`'s own key order, exactly - a template added or reordered in the
     manifest and not reflected here is the drift this gate exists to catch.
  2. The text following each link equals that template's `businessOperation` field in
     `dist/data/templates.json`, verbatim (HTML entities decoded) - not truncated, not
     paraphrased.
  3. `dist/index.md` (the markdown sibling `web/markdown.mjs` builds) carries the same seven
     links - the two renderings of the landing cannot drift into naming a different set.

THE CONTROL RUNS FIRST (CLAUDE.md invariant 5): on a SCRATCH copy of the real build, one row is
removed and one `businessOperation` is swapped for a different template's - both are shown turning
this exact check red before the real tree is trusted to have none.
"""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "web" / "dist"
MANIFEST = ROOT / "templates" / "manifest.json"

ROW_RE = re.compile(
    r'<a href="/build/([a-z0-9-]+)/"[^>]*>([\s\S]*?)</a>\s*—\s*([^<]*)</li>'
)
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(https://provek\.dev/build/([a-z0-9-]+)/\)")


def _manifest_slugs() -> list[str]:
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return list(doc["templates"].keys())


def _templates_json(dist: Path) -> dict[str, dict]:
    doc = json.loads((dist / "data" / "templates.json").read_text(encoding="utf-8"))
    return {t["slug"]: t for t in doc["templates"]}


def _landing_rows(dist: Path) -> list[tuple[str, str]]:
    """[(slug, businessOperation-as-shown), ...] in document order, read from the section's own
    <li> markup rather than from a slug regex over the whole page, so a stray /build/ link
    elsewhere on the page (there is none today, but a future edit might add one) is not
    silently folded in."""
    text = (dist / "index.html").read_text(encoding="utf-8")
    m = re.search(r'What you can build today</h2>([\s\S]*?)</section>', text)
    assert m, "no 'What you can build today' section found on dist/index.html"
    section = m.group(1)
    rows = [(slug, html.unescape(op.strip())) for slug, _title, op in ROW_RE.findall(section)]
    return rows


def _landing_md_slugs(dist: Path) -> list[str]:
    text = (dist / "index.md").read_text(encoding="utf-8")
    m = re.search(r"## What you can build today\n\n([\s\S]*?)\n\n", text)
    assert m, "no 'What you can build today' section found on dist/index.md"
    return [slug for _title, slug in MD_LINK_RE.findall(m.group(1))]


def _check(dist: Path) -> dict:
    """Returns a dict of problems; empty means everything agreed."""
    problems: dict[str, object] = {}
    manifest_slugs = _manifest_slugs()
    templates = _templates_json(dist)
    rows = _landing_rows(dist)
    row_slugs = [s for s, _op in rows]

    if row_slugs != manifest_slugs:
        problems["order_or_membership"] = {"landing": row_slugs, "manifest": manifest_slugs}

    if set(row_slugs) != set(templates.keys()):
        problems["landing_vs_templates_json"] = {
            "landing": sorted(row_slugs), "templates_json": sorted(templates.keys()),
        }

    mismatched_ops = {
        slug: {"landing": op, "templates_json": templates[slug]["businessOperation"]}
        for slug, op in rows
        if slug in templates and op != templates[slug]["businessOperation"]
    }
    if mismatched_ops:
        problems["business_operation_text"] = mismatched_ops

    md_slugs = _landing_md_slugs(dist)
    if md_slugs != manifest_slugs:
        problems["markdown_sibling"] = {"index_md": md_slugs, "manifest": manifest_slugs}

    return problems


def test_the_check_catches_a_removed_row_and_a_swapped_operation(tmp_path):
    assert DIST.is_dir(), (
        f"{DIST} is absent, so this control has nothing to copy. Run `npm run build` in web/ - "
        "scripts/push.sh does exactly that before the suite."
    )
    scratch = tmp_path / "dist"
    shutil.copytree(DIST, scratch)

    before = _check(scratch)
    assert not before, f"the scratch copy was already dirty before any plant: {before}"

    index = scratch / "index.html"
    text = index.read_text(encoding="utf-8")

    # Plant 1: drop the first row's <li> entirely.
    m = re.search(r'What you can build today</h2>([\s\S]*?)</section>', text)
    section = m.group(1)
    first_li = re.search(r"<li>[\s\S]*?</li>", section)
    assert first_li, "no <li> row found to remove in the plant"
    planted = text.replace(first_li.group(0), "", 1)
    assert planted != text, "the plant did not change the file - no row was removed"
    index.write_text(planted, encoding="utf-8")

    after_removal = _check(scratch)
    assert "order_or_membership" in after_removal, (
        f"removing a row was not caught: {after_removal}"
    )

    # Restore, then plant 2: swap one template's businessOperation text for another's.
    index.write_text(text, encoding="utf-8")
    rows = _landing_rows(scratch)
    slug_a, op_a = rows[0]
    slug_b, op_b = rows[1]
    swapped = text.replace(f"— {op_a}</li>", f"— {op_b}</li>", 1)
    assert swapped != text, "the plant did not change the file - businessOperation text not found"
    index.write_text(swapped, encoding="utf-8")

    after_swap = _check(scratch)
    assert "business_operation_text" in after_swap, (
        f"swapping a businessOperation string was not caught: {after_swap}"
    )


def test_landing_names_every_published_template_in_manifest_order_with_its_own_operation():
    problems = _check(DIST)
    assert not problems, f"landing/manifest/templates.json/index.md disagree: {problems}"
