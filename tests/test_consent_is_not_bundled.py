"""T-IN-05 (D-71) - a verification request needs an address to be answered; product updates are a
separate, unticked, optional question on both sides of the wire.

THE DEFECT. `Apply.tsx` disabled the button until the updates box was ticked, hard-coded
`consent: true` in the payload, and `apply.js` refused anything else. Every stored consent record
was therefore `true` whatever the applicant felt - which is not evidence of anything, by the
record's own standard (the comment above CONSENT_VERSION in apply.js).

WHAT THIS RUNS AND WHAT IT READS. The endpoint is RUN under Node with a stubbed KV
(`tests/intake_probe.mjs`, the same instrument as test_intake_survives_a_failed_writeback.py). The
form can only be READ: no browser is available here, so the two source assertions are text gates
over Apply.tsx with its comments stripped - a `consent: true` literal, and a `disabled` expression
that mentions the tick - and each is shown able to fail in evidence/RED-071.

HOW TO MAKE IT FAIL: restore `body.consent !== true`; store `consent_text` for a `false`; accept the
string "true"; put `|| !agreed` back on the button; or write `consent: true` in the payload.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "intake_probe.mjs"
FORM = ROOT / "web" / "src" / "pages" / "Apply.tsx"
ENDPOINT = ROOT / "web" / "functions" / "api" / "apply.js"


def run(scenario: str) -> dict:
    try:
        done = subprocess.run(["node", str(PROBE), scenario], cwd=ROOT, capture_output=True,
                              timeout=60, check=False)
    except FileNotFoundError:
        raise AssertionError("`node` is not on PATH: a missing instrument is a red, not a skip (L-16)") from None
    assert done.returncode == 0, done.stderr.decode("utf-8", "replace")
    return json.loads(done.stdout.decode("utf-8"))


def record(result: dict) -> dict:
    kept = [w["value"] for w in result["writes"] if w["stored"] and w["key"].startswith("request:")]
    # Two puts under one key: the record, then the write-back with the delivery outcome.
    assert len(kept) == 2 and kept[0]["id"] == kept[1]["id"], f"unexpected request writes: {kept}"
    return kept[-1]


def code(p: Path) -> str:
    """The source with block, JSX and line comments removed, so a sentence in a comment that
    describes the old behaviour cannot satisfy or trip an assertion about the code."""
    s = p.read_text(encoding="utf-8")
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", "", s)


def test_an_unticked_box_is_a_recorded_false_and_the_request_goes_through() -> None:
    r = run("consent_false")
    assert r["status"] == 200 and r["body"]["ok"] is True, (r["status"], r["body"])
    rec = record(r)
    assert rec["consent"] is False
    # MEASURED ABSENCE: the keys exist and are null, so a reader cannot mistake "not asked" for "lost".
    for k in ("consent_at", "consent_version", "consent_text"):
        assert k in rec and rec[k] is None, (k, rec.get(k, "<missing>"))
    assert rec["contact"] == "applicant@example.com", "the address is needed to answer the request"


def test_a_ticked_box_stores_the_four_fields() -> None:
    r = run("consent_true_notice")
    rec = record(r)
    assert rec["consent"] is True
    assert rec["consent_version"] == "updates-1.1.0"
    assert rec["consent_at"] and rec["consent_text"].startswith("Also send me product updates")


def test_a_non_boolean_answer_is_refused_not_guessed() -> None:
    for scenario in ("consent_string", "consent_missing"):
        r = run(scenario)
        assert r["status"] == 400, (scenario, r["status"])
        assert "must be true or false" in r["body"]["error"], r["body"]
        assert not [w for w in r["writes"] if w["stored"]], f"{scenario}: something was stored"


def test_a_ticked_box_with_a_stale_version_is_refused() -> None:
    r = run("consent_true_stale_version")
    assert r["status"] == 400 and "out of date" in r["body"]["error"], r
    assert not [w for w in r["writes"] if w["stored"]]


def test_the_notice_says_which_way_the_box_went() -> None:
    assert "updates: no" in run("consent_false_notice")["notice_texts"][0]
    assert "updates: yes" in run("consent_true_notice")["notice_texts"][0]


def test_the_form_never_hard_codes_consent() -> None:
    src = code(FORM)
    assert not re.search(r"consent\s*:\s*true\b", src), "Apply.tsx sends a literal `consent: true`"
    assert 'form.get("updates") === "on"' in src, "the payload does not read the box"


def test_the_buttons_disabled_expression_does_not_mention_the_tick() -> None:
    src = code(FORM)
    exprs = re.findall(r"disabled=\{([^}]*)\}", src)
    assert exprs, "Apply.tsx has no `disabled={...}` expression - the instrument found nothing to judge"
    for e in exprs:
        assert not re.search(r"agreed|updates|consent|checked", e, re.I), (
            f"the button is gated on the updates tick again: disabled={{{e}}}")
    box = re.search(r"<input[^>]*name=\"updates\"[^>]*>", src, re.S)
    assert box, "the `updates` checkbox is gone"
    assert "checked" not in box.group(0).lower(), "the updates box must start unticked"


def test_the_endpoint_source_no_longer_requires_true() -> None:
    assert "body.consent !== true)" not in code(ENDPOINT).replace("body.consent !== true && body.consent !== false)", "")
