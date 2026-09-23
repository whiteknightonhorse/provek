"""T-SG-14 (`~/taskloop/briefs/SG-00-ruling-1.md` §SG-14): "Open verification challenge - accept
as a page and an application flag". The flag is `origin` on `/api/apply`'s stored record, and the
rule guarding it is the same shape D-21/D-23 already hold `mandate` to
(`tests/test_intake_records_the_mandate_request.py`): a value this endpoint did not itself define
must never reach a durable record as though it meant something, so an unrecognised `origin` is
coerced to the ordinary `null` rather than stored verbatim or guessed at.

Run over the real handler under Node (`tests/intake_probe.mjs`), the same instrument
`tests/test_intake_survives_a_failed_writeback.py` uses - a source scan can prove `body.origin` is
read and can never prove what ends up in the stored record.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "intake_probe.mjs"


def run(scenario: str) -> dict:
    done = subprocess.run(["node", str(PROBE), scenario],
                           cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stdout + done.stderr
    return json.loads(done.stdout)


def _stored_record(result: dict) -> dict:
    # writes[0] is the pre-notice record every scenario here writes first (see apply.js: written
    # BEFORE the Telegram notice, so a submission survives a failed announcement).
    stored = [w for w in result["writes"] if w["stored"]]
    assert stored, f"no write landed: {result}"
    return stored[0]["value"]


def test_the_challenge_pages_own_value_is_recorded_verbatim():
    r = run("origin_challenge")
    assert r["outcome"] == "answered" and r["status"] == 200
    assert _stored_record(r)["origin"] == "challenge"


def test_an_unrecognised_origin_is_refused_to_null_not_guessed_or_stored_verbatim():
    """The same D-23 shape as `mandate`: a client-supplied string that is not the one value this
    endpoint defines does not get to name itself in the durable record."""
    r = run("origin_unrecognised")
    assert r["outcome"] == "answered" and r["status"] == 200
    assert _stored_record(r)["origin"] is None, (
        "an unrecognised origin value was stored verbatim rather than coerced to null"
    )


def test_the_ordinary_submission_with_no_origin_field_records_null_not_an_empty_string():
    """Invariant 1: `null` ('not applicable') and `''` ('asked and got nothing') are different
    states, and the plain `/apply/` form - which sends no `origin` key at all - must land on the
    same `null` as an explicit `origin: null` would, not on an empty-string stand-in for it."""
    r = run("origin_absent")
    assert r["outcome"] == "answered" and r["status"] == 200
    rec = _stored_record(r)
    assert "origin" in rec, "the stored record does not carry an origin key at all"
    assert rec["origin"] is None


def test_the_challenge_page_links_to_apply_with_the_via_flag():
    """The other half of "a page and a flag" - the page has to actually send the value the
    endpoint test above exercises, or the two are unconnected artefacts that happen to share a
    name."""
    challenge = (ROOT / "web" / "src" / "pages" / "Challenge.tsx").read_text(encoding="utf-8")
    assert '/apply/?via=challenge' in challenge, (
        "Challenge.tsx's call to action no longer links to /apply/?via=challenge"
    )

    apply_form = (ROOT / "web" / "src" / "pages" / "Apply.tsx").read_text(encoding="utf-8")
    assert '"via"' in apply_form and '"challenge"' in apply_form, (
        "Apply.tsx no longer reads the via=challenge query flag into the origin field it sends"
    )
