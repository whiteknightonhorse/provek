"""T-WB-02: twelve sentences the site said that were not true of the site (audit H3, M1-M7, L9,
L10, L13), each fixed where it was said. This module holds the fixes by the exact strings, so a
sentence cannot come back without a red.

Source reads for copy that lives in source (the TSX pages, the generator, the note bodies), the
real handler under Node for the one sentence that depends on a branch (the brief footer), the same
instrument `tests/test_brief_page_carries_the_vector.py` uses.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
PAGES = WEB / "src" / "pages"
PROBE = ROOT / "tests" / "brief_probe.mjs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _brief(scenario: str) -> str:
    done = subprocess.run(["node", str(PROBE), scenario], cwd=ROOT, capture_output=True,
                          text=True, timeout=30)
    assert done.returncode == 0, done.stdout + done.stderr
    return json.loads(done.stdout)["body"]


def _jsx_text(source: str) -> str:
    """The component body with its comments removed: what is left is JSX and the page's own copy."""
    body = source.split("export default function", 1)[1]
    body = re.sub(r"\{/\*.*?\*/\}", "", body, flags=re.S)
    return re.sub(r"/\*.*?\*/", "", body, flags=re.S)


# H3 / M1 ------------------------------------------------------------------------------------

def test_llms_txt_and_the_phase_page_agree_that_phase_two_is_live():
    llms = _read(WEB / "public" / "llms.txt")
    assert "live: the Provider Catalog (a verified subject may publish an Order link)" in llms
    assert "specified and not in service" not in llms.split("Phase 3", 1)[0], (
        "llms.txt still says phase 2 is specified and not in service")
    assert "Phase 3" in llms and "specified, not in service" in llms
    assert "Phase two is live." in _read(PAGES / "Phase2.tsx")


def test_llms_txt_lists_the_pages_the_sitemap_lists():
    llms = _read(WEB / "public" / "llms.txt")
    for route in ("/witness/", "/challenge/", "/registry/corrections/",
                  "/method/notes/autonomy-levels-l0-l5/", "/method/notes/not-measured-is-not-zero/",
                  "/method/notes/what-erc-8004-provides-and-what-it-does-not/"):
        assert f"https://provek.dev{route}" in llms, f"llms.txt omits {route}"


# the passport page, the brief ---------------------------------------------------------------

def test_the_passport_names_the_real_brief_address_not_a_bare_suffix():
    src = _read(PAGES / "Passport.tsx")
    assert "short summary at <code" not in src
    assert "/p/{s}/brief</code>" in src


def test_an_unverified_brief_does_not_say_verified_by_provek():
    unverified = _brief("independent_no_projection")
    assert "Verified by" not in unverified
    assert "Checked by" in unverified and ": unverified." in unverified


def test_a_lapsed_brief_says_it_has_lapsed_and_a_verified_one_says_verified():
    assert "Verified by" in _brief("verified_three_ops")
    lapsed = _brief("lapsed_shows_stale")
    assert "the passport has lapsed." in lapsed


# the method page ----------------------------------------------------------------------------

def test_the_method_page_claims_no_more_than_it_publishes():
    src = _read(PAGES / "Method.tsx")
    assert "Published in full" not in src
    assert "any verdict can be recomputed" not in src
    assert "Three absences" not in src
    assert "Four absences are distinguished" not in src
    assert "Six absences are distinguished" in src
    assert "every published rule can be recomputed" in src
    assert "listed under Open items below" in src
    assert "licensed for reuse" not in src, "LICENSE holds two licences; the page must name them"
    assert "CC BY 4.0" in src and "Apache-2.0" in src


def test_no_backtick_is_printed_inside_the_method_page_text():
    assert "`" not in _jsx_text(_read(PAGES / "Method.tsx")), (
        "a literal backtick would be shown to the reader; use a <code> element")


# the registry and the landing page ----------------------------------------------------------

def test_the_score_is_qualified_by_how_many_operations_were_measured():
    for page in ("Registry.tsx", "Landing.tsx"):
        assert "operationsMeasuredNote(" in _read(PAGES / page), page
    assert ">Issued</th>" in _read(PAGES / "Registry.tsx")
    assert ">Measured</th>" not in _read(PAGES / "Registry.tsx")
    for path in (ROOT / "public" / "registry" / "registry.json", WEB / "public" / "data" / "registry.json"):
        for row in json.loads(_read(path))["subjects"]:
            assert isinstance(row["operations_total"], int), (path, row["subject_id"])
            assert 0 <= row["operations_measured"] <= row["operations_total"]


# the notes ----------------------------------------------------------------------------------

def test_the_public_notes_index_prints_no_ceiling_or_ladder():
    src = _read(WEB / "notes" / "emit.mjs")
    index = src.split("export function notesIndexArticle", 1)[1].split("// --- structured data", 1)[0]
    assert "may stand" not in index.split("console.log", 1)[1].split("\n", 1)[1]
    assert "ladderSentence()" not in index.split("return `<article", 1)[1]


def test_note_bodies_carry_no_task_or_ruling_ids_of_the_kinds_the_audit_named():
    for note in sorted((WEB / "notes" / "src").glob("*.md")):
        text = _read(note)
        for phrase in ("Operator ruling", "task T-", "awaiting operator ratification",
                       "licensed for reuse"):
            assert phrase not in text, f"{note.name}: {phrase!r}"


# the corrections, the template title --------------------------------------------------------

def test_the_corrections_count_is_five_everywhere_it_is_printed():
    for page in ("Corrections.tsx", "Registry.tsx"):
        src = _read(PAGES / page)
        assert "Three corrections" not in src and "Three exist" not in src, page
    assert "Five exist today" in _read(PAGES / "Corrections.tsx")
    assert "Five corrections are on record" in _read(PAGES / "Registry.tsx")


def test_the_youtube_template_title_is_title_cased_like_the_other_six():
    assert '"YouTube Channel Operations Agent"' in _read(ROOT / "templates" / "emit.mjs")
    assert "YouTube channel operations agent" not in _read(WEB / "public" / "llms.txt")


# T-0567: a price for our own work is not excluded; "public only" is a rule for applicants -------

def test_the_phase_page_does_not_promise_no_payment_step_in_a_later_phase():
    text = _jsx_text(_read(PAGES / "Phase2.tsx")).replace("\n", " ")
    flat = " ".join(text.split())
    assert "not in a later one" not in flat
    assert "What A-6 does not exclude is a price for our own work." in flat


def test_the_apply_form_says_public_only_and_names_the_operators_private_rows():
    src = _read(PAGES / "Apply.tsx")
    flat = " ".join(src.split())
    assert "Public repositories only" in flat
    assert "private repositories" in flat
    assert "That path is not open to applicants." in flat


def test_every_surface_that_says_public_only_says_what_the_private_rows_are():
    for rel in ("README.md", "web/public/llms.txt", "web/public/llms-full.txt", "web/discovery.mjs"):
        flat = " ".join(_read(ROOT / rel).split())
        assert "ublic repositories only (the operator" in flat, rel
