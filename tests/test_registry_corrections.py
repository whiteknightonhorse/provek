"""The corrections log (phase-2 plan): the first two errata this project ever published moved
from `/registry/` to `/registry/corrections/`, byte-for-byte, and a third (AUD-001, D-54) was
published directly at that address - `/registry/` itself carries exactly one compact line pointing
there, never the full text of any correction again.

WHY THIS IS A FIXTURE TEST, NOT A DIFF AGAINST GIT HISTORY. The two expected texts below are
captured directly from `web/src/pages/Registry.tsx` as it stood BEFORE this task moved them - the
same discipline `tests/test_phase_two_promises_nothing.py` and `tests/test_ratchet_phase3_note.py`
already hold their own migrated/duplicated text to. A test that diffed against a git ref would stop
meaning anything the day that ref is pruned; a literal fixture means the same thing forever, and a
future editor who reworks the wording on the corrections page has to convince THIS test, not merely
convince themselves that nothing important changed.

Checked over the EMITTED HTML, not the `.tsx` source - what a reader receives is the thing that has
to hold (L-3), and `web/markdown.mjs`'s auto-derived `.md` sibling is checked too, since "prerender,
no JS" was the point of putting this content on its own page at all.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORRECTIONS_PAGE = ROOT / "web" / "dist" / "registry" / "corrections" / "index.html"
CORRECTIONS_MD = ROOT / "web" / "dist" / "registry" / "corrections" / "index.md"
REGISTRY_PAGE = ROOT / "web" / "dist" / "registry" / "index.html"

# Captured verbatim from `web/src/pages/Registry.tsx` before this task moved them off that page -
# see the module docstring for why a literal fixture is used rather than a diff against history.
EXPECTED_25AUG = (
    "Erratum, 2026-08-25. Every passport issued under profile 1.0.0 states an evidence window of "
    "30 days. The collector read the last 50 commits by count instead, and never looked at a date. "
    "The whole registry is being re-measured against the window that was published; corrected "
    "verdicts will be re-issued together, in whichever direction each one moves, and the "
    "superseded documents will stay readable rather than disappear."
)
EXPECTED_31AUG = (
    "Erratum, 2026-08-31. A defect in the rule, not the data: the cohort granted L4 to a sole "
    "author without checking the signature share the published methodology requires for that "
    "rung. The rule now matches what is published; APIbase, the one passport the defect affected, "
    "moved from L4 to L3 (projection 80 to 60). Nothing here disappears — this notice stays "
    "up next to the one it follows."
)
# Captured verbatim from `web/src/pages/Corrections.tsx` (AUD-001, D-54) - the third erratum this
# project has published, and the first to be published directly on this page rather than moved
# here from `/registry/`.
EXPECTED_03SEP = (
    "Erratum, 2026-09-03. A defect in the corpus, not the rule that reads it: "
    "cryptocardhub-public, a repository the operator owns, was admitted to the registry on "
    "2026-08-25 marked independent, and no gate ever compared that stored value to the owner the "
    "repository's own name states. The row read as an independent verification of the operator's "
    "own project for the length of that error. It now reads same_owner, the passport has been "
    "re-issued, and a gate added the same day refuses to publish the registry if any subject the "
    "operator owns carries anything else."
)

# The fourth entry (T-WB-02): a change of record for 2026-09-01 (commit b0a5d66, re-measure of
# APIbase, 60 to 40) that was never given a notice. Facts are the passport diff of that commit:
# head 1eeeccb -> 5ef9826, identity_window_closed true -> false, unlinked_commit_share 0.0 -> 0.009,
# unlinked_key_count 0 -> 1, development_initiation L3 -> L2.
EXPECTED_01SEP = (
    "Correction, 2026-09-01. APIbase\u2019s autonomy projection moved from 60 to 40 and its "
    "development-initiation level from L3 to L2 when it was re-measured that day. No defect in the "
    "rule or in the earlier data was found: between the two measurements the repository\u2019s head "
    "moved, and the 30-day window then held a commit whose author the platform did not attribute to "
    "an account (unlinked commit share 0.0 to 0.009; one unlinked key). Under platform closure "
    "\u2014 an author count is a count only when every non-bot commit in the window is attributed "
    "\u2014 an open identity window floors the level at L2. The earlier figure was a true reading of "
    "the window it was taken from, and is superseded."
)

# The fifth entry (T-0540): the retired subject's withdrawal, by the D-72 path.
EXPECTED_26OCT = (
    "Correction, 2026-10-26. Subject withdrawn: project retired 2026-10. The subject "
    "audiobook-shorts-series was removed from the registry, and its passport and badge with it, "
    "because the project it described no longer exists. Its row read unverified with the reason "
    "unreadable and carried no verdict, so no verdict changed. Git history and copies kept by third "
    "parties still hold what was published (D-72)."
)

# The sixth entry (T-0569): the method note that quoted live author counts the registry did not show.
# Values from the committed passports at b8698b3 (2026-10-23) and 47f9846 (2026-10-26).
EXPECTED_26OCT_NOTE = (
    "Correction, 2026-10-26. The method note on the autonomy levels said that \u201cprovek stays L3 "
    "because a second identity remains\u201d and that APIbase had a \u201csingle author\u201d and was L3 "
    "because its signed share was 0.0. The registry showed neither: on 2026-10-23 and again on "
    "2026-10-26, provek had one attributed author (signed share 0.302, then 0.283) and APIbase had "
    "two (signed share 0.013, then 0.022). The note has been rewritten with each live number dated, "
    "and now says what platform attribution does and does not prove: an author address is written by "
    "the committer, so the count is a lower bound only for a subject that does not forge it. No "
    "score, threshold or rule changed. Interested party: the operator\u2019s own subjects; found by an "
    "external audit (Opus, 2026-10-24)."
)

emitted = pytest.mark.skipif(not CORRECTIONS_PAGE.exists(), reason="site not built in this checkout")


def _main_text(html_path: Path) -> str:
    html = html_path.read_text(encoding="utf-8")
    body = html.split("<script>window.__PROVEK__", 1)[0]
    m = re.search(r"<main\b.*?</main>", body, re.S)
    assert m, f"{html_path} has no <main>"
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(0))).strip()


@emitted
def test_all_six_corrections_are_preserved_byte_for_byte_on_the_corrections_page():
    text = _main_text(CORRECTIONS_PAGE)
    assert EXPECTED_25AUG in text, "the 2026-08-25 erratum's text drifted from what was moved here"
    assert EXPECTED_31AUG in text, "the 2026-08-31 erratum's text drifted from what was moved here"
    assert EXPECTED_03SEP in text, "the 2026-09-03 erratum's text drifted from what was published"
    assert EXPECTED_01SEP in text, "the 2026-09-01 correction's text drifted from what was published"
    assert EXPECTED_26OCT in text, "the 2026-10-26 correction's text drifted from what was published"
    assert EXPECTED_26OCT_NOTE in text, "the 2026-10-26 note correction's text drifted from what was published"


@pytest.mark.skipif(not CORRECTIONS_MD.exists(), reason="markdown sibling not built in this checkout")
def test_all_six_corrections_survive_into_the_no_js_markdown_sibling():
    """"prerender, no JS" is the whole point of moving this content to its own page - the markdown
    twin `web/markdown.mjs` derives from every page is what proves a reader (or a crawler) with no
    JavaScript still gets the exact same words."""
    # `**bold**` is the one markdown syntax either fixture's own text would collide with (the
    # converter wraps `<strong>Erratum, ...</strong>` as `**Erratum, ...**`) - stripped the same
    # way `_main_text` strips HTML tags for the sibling page, so both comparisons judge the WORDS.
    text = re.sub(r"\s+", " ", CORRECTIONS_MD.read_text(encoding="utf-8").replace("**", "")).strip()
    assert EXPECTED_25AUG in text
    assert EXPECTED_31AUG in text
    assert EXPECTED_03SEP in text
    assert EXPECTED_01SEP in text
    assert EXPECTED_26OCT in text
    assert EXPECTED_26OCT_NOTE in text


@emitted
def test_the_full_erratum_text_no_longer_lives_on_the_registry_page():
    """The move is real, not a copy: the full bodies leave `/registry/` entirely once they have an
    address of their own - reproducing them in both places would be LAW #ONE-PLACE's own defect,
    applied to prose instead of code."""
    text = _main_text(REGISTRY_PAGE)
    assert EXPECTED_25AUG not in text
    assert EXPECTED_31AUG not in text
    assert EXPECTED_03SEP not in text
    assert EXPECTED_01SEP not in text
    assert EXPECTED_26OCT not in text
    assert EXPECTED_26OCT_NOTE not in text
    assert "will be re-issued together" not in text
    assert "signature share the published" not in text
    assert "verification of the operator's own project" not in text


@emitted
def test_registry_carries_exactly_one_correction_line():
    text = _main_text(REGISTRY_PAGE)
    assert text.count("Erratum, 2026-08-25.") == 0
    assert text.count("Erratum, 2026-08-31.") == 0
    assert text.count("Erratum, 2026-09-03.") == 0
    assert text.count("Correction, 2026-09-01.") == 0
    assert text.count("Six corrections are on record for this registry.") == 1
    assert text.count("All corrections (6)") == 1
    links = re.findall(r'<a\b[^>]*href="([^"]+)"[^>]*>\s*All corrections',
                       REGISTRY_PAGE.read_text(encoding="utf-8"))
    assert links == ["/registry/corrections/"]


def test_the_route_is_wired_and_prerendered():
    app = (ROOT / "web" / "src" / "App.tsx").read_text(encoding="utf-8")
    assert 'if (route === "/registry/corrections/") return <Corrections />;' in app
    prerender = (ROOT / "web" / "prerender.mjs").read_text(encoding="utf-8")
    assert '"/registry/corrections/"' in prerender
    verify = (ROOT / "scripts" / "verify_live.sh").read_text(encoding="utf-8")
    assert "/registry/corrections/:200" in verify, (
        "the door's own live-address check does not cover the new page - a deploy could ship a "
        "404 here and every other check would still read green")


def test_MUTATION_a_reworded_erratum_would_be_CAUGHT():
    """Control: a paraphrase that preserves the MEANING but not the WORDS must still fail - the
    whole point of a byte-for-byte fixture over a "says roughly the same thing" check."""
    reworded = EXPECTED_25AUG.replace("re-measured", "recomputed")
    assert reworded not in EXPECTED_25AUG
    assert EXPECTED_25AUG not in reworded


def test_MUTATION_a_silently_softened_09sep_erratum_would_be_CAUGHT():
    """Same control, for AUD-001's own erratum: a rewrite that quietly drops "independent
    verification of the operator's own project" for something gentler must still fail the
    byte-for-byte check above."""
    softened = EXPECTED_03SEP.replace(
        "read as an independent verification of the operator's own project",
        "carried the wrong label")
    assert softened not in EXPECTED_03SEP
    assert EXPECTED_03SEP not in softened
