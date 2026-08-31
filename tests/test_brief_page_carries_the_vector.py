"""The short client-facing page a verified subject links to from its own site. ABI-2-3 requires it
to carry the vector across operations rather than a compressed scalar; this task's acceptance gate
requires the SAME live-status guarantee the badge has, proved the same way - a lapsed passport must
read `stale`, never the stored word.

Runs the real handler under Node via `tests/brief_probe.mjs`, for the reason every other Function
gate in this suite runs the code instead of reading it: a source scan can prove a template string
mentions "stale" and can never prove which branch a given passport actually takes.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "brief_probe.mjs"
FUNCTION = ROOT / "web" / "functions" / "p" / "[id]" / "brief.js"

BARE_LEVEL = re.compile(r"(?<![A-Za-z0-9_])L[0-5](?![A-Za-z0-9_])")


def run(scenario: str) -> dict:
    assert PROBE.is_file(), f"{PROBE} is missing"
    assert FUNCTION.is_file(), f"{FUNCTION} is missing"
    done = subprocess.run(["node", str(PROBE), scenario],
                           cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stdout + done.stderr
    return json.loads(done.stdout)


def test_every_operation_is_named_individually():
    """The vector, not the scalar - all three operations appear on their own, by name."""
    r = run("verified_three_ops")
    assert r["status"] == 200
    for label in ("Development initiation", "Deployment", "Treasury control"):
        assert label in r["body"], f"{label} missing from the brief page"


def test_a_measured_level_appears_but_never_as_a_lone_company_figure():
    """L3 is fine ATTACHED to its operation row - what must never appear is a bare level standing
    for the subject as a whole. The projection, when shown, must carry its own name and its own
    section, never a bare figure floating beside the subject's name."""
    r = run("verified_three_ops")
    assert "L3" in r["body"]
    assert "Autonomy projection" in r["body"]
    block = r["body"].split('<div class="projection">', 1)[1].split("</section>", 1)[0]
    assert "60" in block, "the projection value is not inside its own labelled section"


def test_an_unmeasured_operation_says_why_rather_than_scoring_zero():
    r = run("verified_three_ops")
    assert "not measured: the check did not run" in r["body"]


def _status_span(body: str) -> str:
    """The one element carrying the computed word - not the stylesheet, which legitimately
    defines a rule for every possible status regardless of which one is active."""
    m = re.search(r'<span class="status status--(\w+)">(\w+)</span>', body)
    assert m, "no status span found in the brief page"
    return m.group(1)


def test_THE_CONTROL_a_lapsed_passport_reads_stale_not_the_stored_word():
    healthy = run("verified_three_ops")
    lapsed = run("lapsed_shows_stale")
    assert _status_span(healthy["body"]) == "verified"
    assert _status_span(lapsed["body"]) == "stale", (
        "the stored status field is still literally 'verified' in this fixture - a lapsed "
        "passport read the stored word instead of the computed one")
    assert "This passport has lapsed" in lapsed["body"]
    assert healthy["body"] != lapsed["body"]


def test_affiliated_verification_is_disclosed_here_too():
    """ABI-19-2's warning does not stop at the full passport - a page meant to be shown to a
    subject's OWN clients must not omit that the verifier and the subject share an owner."""
    r = run("verified_three_ops")
    assert "Affiliated verification" in r["body"]


def test_an_unaffiliated_subject_carries_no_affiliation_warning():
    r = run("independent_no_projection")
    assert "Affiliated verification" not in r["body"]


def test_an_absent_projection_says_so_under_its_own_name():
    r = run("independent_no_projection")
    assert "Autonomy projection" in r["body"]
    block = r["body"].split('<div class="projection">', 1)[1].split("</section>", 1)[0]
    assert "not measured" in block
    assert not BARE_LEVEL.search(r["body"])


def test_it_links_to_the_full_passport():
    r = run("verified_three_ops")
    assert 'href="/p/git_whiteknightonhorse_provek/"' in r["body"]


def test_unknown_slug_is_a_named_404():
    r = run("unknown_slug")
    assert r["status"] == 404
    assert "No such passport" in r["body"]


def test_malformed_slug_is_refused_before_any_fetch():
    r = run("malformed_id")
    assert r["status"] == 404


def test_cache_is_short():
    r = run("verified_three_ops")
    m = re.search(r"max-age=(\d+)", r["cacheControl"] or "")
    assert m, r["cacheControl"]
    assert int(m.group(1)) <= 600
