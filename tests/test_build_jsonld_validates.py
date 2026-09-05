"""SPEC 3.7 / ruling section 6.3 - every emitted `/build/**` page carries JSON-LD that parses as
valid JSON and matches schema.org's expected shape for its own `@type`.

Every template page carries exactly two blocks: a `TechArticle` (the artefact, as a document) and
a `FAQPage` built from the SAME three fixed questions `templates/faq.json` and
`web/prerender.mjs:ldTemplate` both key off - `FAQPage` is never emitted without the matching
visible `Questions` block `BuildTemplate.tsx` renders (no structured data with nothing behind it,
the same rule `web/notes/emit.mjs`'s own FAQ block already holds itself to). The index page carries
one `CollectionPage` whose `hasPart` names every emitted template and nothing else.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST_BUILD = ROOT / "web" / "dist" / "build"

LD_BLOCK = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)

FIXED_QUESTIONS = [
    "What does a human still do?",
    "What do I need before I start?",
    "What happens after it runs?",
]


def _blocks(html: str) -> list[dict]:
    return [json.loads(m) for m in LD_BLOCK.findall(html)]


def _template_pages() -> list[Path]:
    assert DIST_BUILD.is_dir(), (
        f"{DIST_BUILD} is absent, so this gate measured nothing. Run `npm run build` in web/ - "
        "scripts/push.sh does exactly that before the suite."
    )
    return sorted(p for p in DIST_BUILD.glob("*/index.html"))


def test_every_template_page_carries_a_techarticle_and_a_faqpage_and_nothing_else():
    pages = _template_pages()
    assert pages, "no template page emitted under dist/build/"
    for page in pages:
        blocks = _blocks(page.read_text(encoding="utf-8"))
        types = sorted(b.get("@type") for b in blocks)
        assert types == ["FAQPage", "TechArticle"], f"{page}: unexpected JSON-LD block set {types}"


def test_every_techarticle_carries_its_required_fields():
    required = ("@context", "@type", "headline", "description", "url", "datePublished",
                "dateModified", "license", "about", "publisher")
    for page in _template_pages():
        article = next(b for b in _blocks(page.read_text(encoding="utf-8")) if b["@type"] == "TechArticle")
        missing = [k for k in required if k not in article]
        assert not missing, f"{page}: TechArticle missing {missing}"
        assert article["about"]["@type"] == "SoftwareApplication"
        assert article["publisher"] == {"@type": "Organization", "name": "Provek"}


def test_every_faqpage_answers_exactly_the_three_fixed_questions_in_order():
    for page in _template_pages():
        faq = next(b for b in _blocks(page.read_text(encoding="utf-8")) if b["@type"] == "FAQPage")
        questions = [q["name"] for q in faq["mainEntity"]]
        assert questions == FIXED_QUESTIONS, f"{page}: FAQ questions do not match the fixed set: {questions}"
        for q in faq["mainEntity"]:
            assert q["@type"] == "Question"
            assert q["acceptedAnswer"]["@type"] == "Answer"
            assert q["acceptedAnswer"]["text"].strip(), f"{page}: empty FAQ answer for {q['name']!r}"


def test_faqpage_answers_are_not_boilerplate_copied_across_templates():
    """'Answered in the template's own words, not boilerplate' (task brief) - each template's set
    of three answers must be unique to it, not a shared paragraph reused verbatim."""
    seen: dict[tuple[str, ...], Path] = {}
    for page in _template_pages():
        faq = next(b for b in _blocks(page.read_text(encoding="utf-8")) if b["@type"] == "FAQPage")
        answers = tuple(q["acceptedAnswer"]["text"] for q in faq["mainEntity"])
        assert answers not in seen, f"{page} and {seen.get(answers)} share identical FAQ answers"
        seen[answers] = page


def test_the_index_page_collectionpage_hasPart_names_every_emitted_template():
    index = DIST_BUILD / "index.html"
    assert index.is_file(), "dist/build/index.html is missing"
    blocks = _blocks(index.read_text(encoding="utf-8"))
    collection = next(b for b in blocks if b["@type"] == "CollectionPage")
    part_urls = {p["url"] for p in collection["hasPart"]}
    page_urls = {f"https://provek.dev/build/{p.parent.name}/" for p in _template_pages()}
    assert part_urls == page_urls, f"CollectionPage.hasPart does not match the emitted set: {part_urls ^ page_urls}"


# --- control: the parser must be shown catching a malformed block before it is trusted ---------

def test_the_json_parser_catches_a_malformed_block():
    bad_html = '<script type="application/ld+json">{not: valid json}</script>'
    try:
        _blocks(bad_html)
        raised = False
    except json.JSONDecodeError:
        raised = True
    assert raised, "a malformed JSON-LD block was not caught by the parser"
