"""LAW-NOTES-ADDRESSED - a note may not say anything it cannot show the address of.

Programmatic page generation is the genre in which a claim outruns its artefact, and that is the
defect this whole product exists to detect. A generator that produces plausible pages about a
subject is indistinguishable, from the outside, from a generator that produces true ones. So the
note format carries its addresses as data and this module refuses to let one through that does not
resolve: not "we were careful", but "an untraceable claim does not build".

The same module holds the numeric norms. All of them are ASSIGNED (2026-08-20) - no note has been
published, no indexation reading exists, and there is no experiment behind any of these bounds.
They are a stated reading, revised when a reading exists, which is the form `abs_profile/ladder.py`
uses for its own thresholds rather than pretending they were measured.
"""
from __future__ import annotations

import re

import pytest

from .notes_support import ROOT, emitted, keyword_base, ld_blocks, normalise, paragraphs, sources, strip_tags

# ASSIGNED 2026-08-20. Ceilings are hard; the body FLOOR is deliberately far below where the prose
# should land, because a floor is a number a model writes TO and a floor set at the target buys
# padding rather than substance (Fable, blocker B-3).
BODY_MIN, BODY_MAX = 3000, 14000
LEAD_MIN, LEAD_MAX = 320, 520
PARA_MAX = 600
FAQ_A_MIN, FAQ_A_MAX = 240, 520
FAQ_MAX = 5
H2_MIN, H2_MAX = 3, 7
KEY_DENSITY_CHARS = 900
TITLE_MAX = 60
DESC_MIN, DESC_MAX = 140, 160
KEYS_MAX = 3
FIG_MAX = 3

pytestmark = pytest.mark.skipif(not sources(), reason="no method notes captured in this checkout")


def test_every_address_resolves_to_a_real_place_in_this_repository():
    for front, _ in sources():
        assert front["addresses"], f"{front['slug']}: a note with no addresses asserts on its own authority"
        for a in front["addresses"]:
            p = ROOT / a["file"]
            assert p.exists(), f"{front['slug']}: address {a['ref']} names a missing file {a['file']}"
            assert a["anchor"] in p.read_text(encoding="utf-8"), (
                f"{front['slug']}: address {a['ref']} anchor {a['anchor']!r} is not in {a['file']}")


def test_a_key_is_a_row_the_base_returned_and_carries_the_state_the_base_recorded():
    """D-17 in the other direction. The base licenses no page; a page may not invent a key either.

    The demand state travels with the key, and an unmeasured demand has no number: writing a zero
    where the instrument refused destroys the only evidence that the reading is missing.
    """
    base = keyword_base()
    for front, _ in sources():
        keys = front.get("keys", [])
        assert len(keys) <= KEYS_MAX, f"{front['slug']}: {len(keys)} keys, ceiling {KEYS_MAX}"
        if not keys:
            assert front.get("keys_absent_reason"), (
                f"{front['slug']}: no keys and no reason - an absence without a reason is a blank")
            continue
        assert sum(1 for k in keys if k["role"] == "primary") == 1, f"{front['slug']}: one primary key"
        for k in keys:
            row = base.get(k["key"])
            assert row is not None, f"{front['slug']}: key {k['key']!r} is not in seo/keywords.csv"
            assert row["demand_state"] == k["demand_state"], (
                f"{front['slug']}: key {k['key']!r} claims {k['demand_state']}, "
                f"base recorded {row['demand_state']}")
            if row["demand_state"] == "measured":
                assert k["impressions_exact"] == int(row["impressions_exact"])
            else:
                assert "impressions_exact" not in k, (
                    f"{front['slug']}: key {k['key']!r} carries a number while {row['demand_state']}")


def test_the_primary_key_is_where_it_was_promised_and_not_repeated_into_the_ground():
    for front, body in sources():
        keys = front.get("keys", [])
        if not keys:
            continue
        primary = next(k["key"] for k in keys if k["role"] == "primary")
        n = normalise(primary)
        assert n in normalise(front["title"]), f"{front['slug']}: primary key not in the title"
        assert n in normalise(front["h1"]), f"{front['slug']}: primary key not in the h1"
        assert n in normalise(front["description"]), f"{front['slug']}: primary key not in the description"
        lead = paragraphs(body)[0]
        assert n in normalise(lead), f"{front['slug']}: primary key not in the lead"
        for k in keys:
            occ = len(re.findall(re.escape(k["key"]), body, re.I))
            ceiling = max(1, len(body) // KEY_DENSITY_CHARS)
            assert occ <= ceiling, (
                f"{front['slug']}: {k['key']!r} appears {occ} times in {len(body)} chars (max {ceiling})")


def test_an_address_that_has_a_public_url_is_linked_where_it_is_first_used():
    """The link gate, derived rather than assigned.

    A floor of "at least five internal links" on a site of twelve URLs can only be met by three
    notes linking to each other, which is a link farm with a small n. So there is no floor: an
    address that resolves to a page on this site must be reachable from the prose that spends it,
    and a link in the prose must be to something the note declared an address of. It fails in both
    directions, which a counter cannot do.
    """
    for front, body in sources():
        urls = {a["url"] for a in front["addresses"] if a.get("url")}
        for u in urls:
            assert f"]({u})" in body, (
                f"{front['slug']}: address with public url {u} is never linked in the prose")
        linked = set(re.findall(r"\]\((/[^)]*)\)", body))
        for u in linked:
            assert u in urls or u.startswith("/method/notes/"), (
                f"{front['slug']}: links to {u}, which is not one of this note's addresses")


def test_lengths_are_within_the_assigned_bounds():
    for front, body in sources():
        assert len(front["title"]) <= TITLE_MAX, f"{front['slug']}: title {len(front['title'])} chars"
        assert DESC_MIN <= len(front["description"]) <= DESC_MAX, (
            f"{front['slug']}: description {len(front['description'])} chars")
        assert BODY_MIN <= len(body) <= BODY_MAX, f"{front['slug']}: body {len(body)} chars"
        paras = paragraphs(body)
        assert LEAD_MIN <= len(paras[0]) <= LEAD_MAX, f"{front['slug']}: lead {len(paras[0])} chars"
        for p in paras:
            assert len(p) <= PARA_MAX, f"{front['slug']}: paragraph of {len(p)} chars: {p[:70]!r}"
        h2 = re.findall(r"^## (.+)$", body, re.M)
        assert H2_MIN <= len(h2) <= H2_MAX, f"{front['slug']}: {len(h2)} H2 sections"


def test_figures_are_declared_or_their_absence_is_reasoned():
    for front, body in sources():
        figs = front.get("figures", [])
        assert len(figs) <= FIG_MAX, f"{front['slug']}: {len(figs)} figures"
        if not figs:
            assert front.get("figures_absent_reason"), (
                f"{front['slug']}: no figure and no reason - a slot left empty silently")
        placed = set(re.findall(r"\{\{figure:([a-z0-9-]+)\}\}", body))
        assert placed == {f["id"] for f in figs}, (
            f"{front['slug']}: declared figures {figs} do not match those placed in the body")


def test_faq_answers_are_quotable_and_every_question_came_from_the_base():
    base = keyword_base()
    for front, _ in sources():
        faq = front.get("faq", [])
        assert len(faq) <= FAQ_MAX, f"{front['slug']}: {len(faq)} FAQ entries"
        for f in faq:
            assert f["q"] in base, f"{front['slug']}: FAQ question {f['q']!r} is not a captured key"
            assert FAQ_A_MIN <= len(f["a"]) <= FAQ_A_MAX, (
                f"{front['slug']}: FAQ answer {len(f['a'])} chars: {f['q']!r}")


def test_the_provenance_of_the_capture_is_recorded_on_the_note():
    """The fields are PRESENT. Whether `generator_sha256` is TRUE is not decidable here.

    D-17 keeps the capture outside this repository, and the named cost has a second half worth
    stating where a reader meets the field: the bytes that hash to `generator_sha256` are not in a
    clone, so nothing under `tests/` can resolve the pin. A green here means the note carries a
    pin, never that the pin names the code that produced the note - and the two read alike unless
    the difference is written down.

    What can decide it is `~/orchestra/notes_pin_verify.py`, which reads the pin against the
    generator's own history and against the step names the capture logged, with a known mispin as
    its control. Both live notes were judged MATCH there on 2026-08-24.

    `topics_sha256` is the same sentence with the second half missing, and this line is added
    because the loop below asserts the two fields identically. `notes_topics.json` does not reach a
    clone either, so the pin is unresolvable here for the same reason - and no instrument decides it
    anywhere: the verifier above knows only the generator. For that field a present pin is the whole
    of what any reading in this repository establishes. What the capture guarantees instead is
    structural and invisible from here: since 2026-08-24 the generator parses the topic spec and
    hashes it from ONE read, so the pin cannot name bytes the run did not plan from. Before that it
    re-read the file at the end of a capture, thirteen to sixteen minutes later, and the red run
    that reproduces the mispin is `~/orchestra/evidence/RED-H9-H10-*`, outside this tree with
    everything else about the capture (D-17).
    """
    for front, _ in sources():
        p = front["provenance"]
        assert p["plan_model"] == "claude-sonnet-5"
        assert p["prose_model"] == "claude-haiku-4-5"
        for field in ("generated_at", "plan_sha256", "generator_sha256", "topics_sha256"):
            assert p.get(field), f"{front['slug']}: provenance is missing {field}"


# --- the shipped document ------------------------------------------------------------------------
# L-3: a file in the repository is not what the consumer receives. These read `web/dist`, and skip
# where it has not been built - which is why everything above reads the source instead.

def test_structured_data_holds_and_the_faq_it_declares_is_visible_verbatim():
    pages = emitted()
    if not pages:
        pytest.skip("site not built in this checkout")
    for front, _ in sources():
        html = pages[front["slug"]]
        blocks = {b["@type"]: b for b in ld_blocks(html)}
        assert "Article" in blocks and "BreadcrumbList" in blocks, front["slug"]
        art = blocks["Article"]
        assert isinstance(art["author"], dict), "author as a bare string is invalid"
        assert art["dateModified"] >= art["datePublished"], front["slug"]
        assert "image" not in art, "no raster is emitted, so none may be claimed"
        assert len(blocks["BreadcrumbList"]["itemListElement"]) == 4, front["slug"]
        text = strip_tags(html)
        if front.get("faq"):
            assert "FAQPage" in blocks, front["slug"]
            for q in blocks["FAQPage"]["mainEntity"]:
                assert q["name"] in text, f"{front['slug']}: FAQ question in schema but not on the page"
                assert q["acceptedAnswer"]["text"] in text, (
                    f"{front['slug']}: FAQ answer in schema but not on the page")
        else:
            assert "FAQPage" not in blocks, f"{front['slug']}: FAQPage with no questions"


def test_the_figures_carry_the_numbers_that_are_in_the_artefacts_today():
    """Computed from the files at build time, so the only way to fail is to stop reading them."""
    import json as _json
    pages = emitted()
    if not pages:
        pytest.skip("site not built in this checkout")
    demand = _json.loads((ROOT / "seo" / "sources.json").read_text())["demand_states"]
    registry = _json.loads((ROOT / "web" / "public" / "data" / "registry.json").read_text())
    for front, _ in sources():
        ids = {f["id"] for f in front.get("figures", [])}
        html = pages[front["slug"]]
        if "keyword-demand-states" in ids:
            for state, n in demand.items():
                assert f">{n}</text>" in html, f"{front['slug']}: figure lost the {state} count"
        if "registry-coverage" in ids:
            for s in registry["subjects"]:
                short = s["subject_id"].split("/")[-1][:30]
                assert short in html, f"{front['slug']}: figure lost subject {short}"


def test_no_figure_smuggles_a_colour_past_the_palette():
    """DESIGN.md's palette is enforced over components; an inline SVG is the one place a hex
    literal would never be looked for."""
    pages = emitted()
    if not pages:
        pytest.skip("site not built in this checkout")
    for slug, html in pages.items():
        for svg in re.findall(r"<svg.*?</svg>", html, re.S):
            hexes = re.findall(r"#[0-9a-fA-F]{3,8}\b", svg)
            assert not hexes, f"{slug}: hex literal in a figure: {hexes[:3]}"


def test_a_note_ships_without_the_application_bundle():
    """A document does not need a router. If a note ever starts hydrating, the open item in
    DESIGN.md stops being a fixed 222 KB and starts growing per note."""
    pages = emitted()
    if not pages:
        pytest.skip("site not built in this checkout")
    for slug, html in pages.items():
        assert '<script type="module"' not in html, f"{slug}: ships the application entry"
        assert "window.__PROVEK__" not in html, f"{slug}: ships bootstrap data it cannot use"
