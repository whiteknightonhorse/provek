"""T-A2-2 - "Nothing was saved" is shown only where nothing was saved (LAW-INTAKE-SAVED-MEANS-SAVED).

THE DEFECT. `web/functions/api/apply.js` writes the submission to KV, sends the operator a notice,
and writes the record back with the delivery outcome. The third step sat outside any `try`. A throw
there became a 500, and `web/src/pages/Apply.tsx` renders a 500 as *"Not recorded ... Nothing was
saved, so please try again"* - which is true of every other failure this endpoint has and false of
this one, because the record was already durable and the notice may already have reached a human.
The applicant is told to resubmit, the operator holds a record nobody follows up, and the two
readings of the same submission disagree.

IT IS NOT A RARE PATH. Workers KV allows one write per second to the same key and rejects the
second with a 429. These are two writes to one key inside a single invocation, separated by at most
a Telegram round trip - so the documented behaviour puts the failure on the ordinary path.
`docs/INTAKE_OPERATIONS.md` measured that limit, predicted this, and left the endpoint unchanged
with the defect named and dated; a named blind spot is still a blind spot (L-25), and this is the
change that closes it rather than describing it.

WHY THIS TEST RUNS THE CODE INSTEAD OF READING IT. `tests/test_intake_records_the_mandate_request.py`
strips comments from the same file and matches regular expressions, which is all a file-reading gate
can do: it could assert that a `try` is written and never that the handler ANSWERS 200. A `try`
around the wrong line, a `catch` that rethrows, or a `return` moved inside it would each satisfy a
source scan and leave the visitor reading the same false sentence. So this file drives
`onRequestPost` under Node with a stubbed KV binding (`tests/intake_probe.mjs`) and asserts what
comes back. It is the first gate in this repository that measures the intake's behaviour rather
than its text.

BOTH DIRECTIONS, because only one of them is about the fix. A handler that answered `ok: true`
unconditionally would satisfy the first assertion below and destroy the property: when the FIRST
write fails, nothing is stored, and the form's sentence is true and must still be shown. The
`durable_write_fails` scenario holds that half, and a blanket try/catch around the whole handler
turns it red.

AND THE FIX'S OWN DEFECT, which is the third thing asserted here. Catching the refusal gave
`delivered: null` a second meaning: it had meant "the invocation died and its submitter was told
nothing was saved", and it now also means "the submitter was told the truth and needs nothing".
Two states of the world in one value, in the field the operator's sweep keys on - invariant 1,
arriving inside the change that closed another instance of it. The endpoint therefore writes a
sentinel under a different key, which the same-key rate limit does not reach, and this file asserts
that it is written when the write-back is refused, that it carries the delivery outcome and the
store's own reason, and that it is ABSENT when the write-back succeeds.

WHAT IS NOT ASSERTED. That the DEPLOYED endpoint behaves this way - on 2026-08-20 `/api/apply`
answered 404 because the Function has never been published (`evidence/PROBE-001.txt`, L-25). And
Node with a stub is not `workerd`: that a thrown handler becomes a 500 and that the browser renders
it as the failure branch are Cloudflare's behaviour and the form's, stated in the operations note,
not measured here. The gap this file DOES close is the one between the repository's text and the
repository's behaviour.

HOW TO MAKE IT FAIL, in the nine ways this gate is about: remove the `try`/`catch` around the
second `put`; wrap the durable write in one too; drop the sentinel; narrow the `catch` to the one
failure shape a stub is likely to throw; freeze the delivery outcome; read an unreachable Telegram
as a delivered one; store a constant in the write-back; replace the refusal's reason with a
plausible sentence; or put every sentinel under one key. FIVE OF THOSE NINE WERE GREEN when Fable
first applied them, across three rounds of refutation, and each one is a value the operator's sweep
acts on - which is this file's own lesson turned on itself: a gate that RUNS the code is still a
gate about the shapes it runs. The runs are produced by `evidence/RED-017-generator.py`, which
refuses to write its artefact if any mutation goes green, if pytest did not run, if one kills the
instrument control, or if two produce the same failure set; they are kept as
`evidence/RED-017-nothing-was-saved-about-a-saved-record.txt`.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "intake_probe.mjs"
ENDPOINT = ROOT / "web" / "functions" / "api" / "apply.js"
FORM = ROOT / "web" / "src" / "pages" / "Apply.tsx"


def run(scenario: str) -> dict:
    """One scenario, or a hard failure.

    A MISSING INSTRUMENT IS A RED, NEVER A SKIP. `scripts/push.sh` takes the same line about
    `pytest-cov`, and L-16 is the reason: a suite that skips itself in the state that ships is
    counted among the armed. If Node is absent this assertion fails loudly and names what is
    missing, rather than quietly withdrawing the only behavioural gate over the intake.
    """
    assert PROBE.is_file(), (
        f"{PROBE} is missing - the instrument this gate reads through is gone, so every assertion "
        "below would be about nothing.")
    try:
        done = subprocess.run(
            ["node", str(PROBE), scenario],
            cwd=ROOT, capture_output=True, timeout=60, check=False)
    except FileNotFoundError:
        raise AssertionError(
            "`node` is not on PATH, so the only gate that RUNS the intake endpoint could not run. "
            "That is a missing instrument, which this project reports as a red rather than as a "
            "skip - the alternative is a suite that goes green in exactly the state where it "
            "asserts nothing (L-16).") from None
    assert done.returncode == 0, (
        f"the probe exited {done.returncode} on scenario {scenario!r}:\n"
        f"{done.stderr.decode('utf-8', 'replace')}")
    return json.loads(done.stdout.decode("utf-8"))


def stored(result: dict, prefix: str) -> list[dict]:
    """The writes under `prefix` that actually landed. A REFUSED WRITE IS AN ATTEMPT, NOT A RECORD."""
    return [w["value"] for w in result["writes"] if w["stored"] and w["key"].startswith(prefix)]


def records(result: dict) -> list[dict]:
    return stored(result, "request:")


def sentinels(result: dict) -> list[dict]:
    return stored(result, "writeback-refused:")


# --- the defect ---------------------------------------------------------------------------------

def test_a_refused_writeback_still_answers_the_applicant_the_truth() -> None:
    """The submission is durable, so the answer says so."""
    r = run("writeback_fails")
    assert r["outcome"] == "answered", (
        "the endpoint threw when the write-back was refused. Cloudflare turns that into a 500 and "
        "the form reads a 500 as 'Not recorded ... Nothing was saved' - about a record that is "
        "sitting in KV.")
    assert r["status"] == 200 and r["body"]["ok"] is True, (
        f"the applicant is told the submission failed: {r['status']} {r['body']}")
    kept = records(r)
    assert len(kept) == 1 and kept[0]["delivered"] is None, (
        f"the durable write is not what this scenario assumes it is: {kept}")
    assert r["body"]["id"] == kept[0]["id"], (
        "the id the applicant was given is not the id of the stored record, so the confirmation "
        "refers to a submission nobody can find.")


def test_the_delivery_state_reported_is_the_one_that_was_measured() -> None:
    """"Honest" is the load-bearing word: `delivered` is what the notice actually did.

    This is the path that matters most and the one the 500 hid. The operator HAS been told, so the
    applicant may be told that too - and answering `ok: true` while flattening `delivered` to
    `false` would replace one false sentence with a smaller one.
    """
    r = run("notice_sent_writeback_fails")
    assert r["notices"] == 1, "the notice was never attempted; this scenario measures nothing"
    assert r["outcome"] == "answered", (
        "the endpoint threw after the operator had already been told. The visitor gets a 500 and "
        f"reads that nothing was saved, about a record that exists and a notice that went out: {r}")
    assert r["status"] == 200 and r["body"]["ok"] is True
    assert r["body"]["delivered"] is True, (
        f"the notice reached Telegram and the applicant was told otherwise: {r['body']}")
    assert records(r)[0]["delivered"] is None, (
        "the write-back was supposed to have been refused in this scenario, so the stored record "
        "should still carry the value written before the notice.")
    assert sentinels(r)[0]["notice_delivered"] is True, (
        "the sentinel does not carry the delivery outcome the applicant was given, so the operator "
        "cannot tell from the store what this person was told.")


def test_the_delivery_state_is_measured_in_the_false_direction_too() -> None:
    """A control that cannot go false measures nothing.

    The Telegram stub took an `ok` argument that was only ever passed `true`, so `delivered` could
    be hardcoded to `true` in the endpoint with all ten assertions green - and `delivered` is the
    whole of "an honest delivery state". The operator's follow-up reads the same value off the
    sentinel. Found by Fable, who applied exactly that mutation and watched it pass.
    """
    r = run("notice_refused_writeback_fails")
    assert r["notices"] == 1, "the notice was never attempted; this scenario measures nothing"
    assert r["status"] == 200 and r["body"]["ok"] is True
    assert r["body"]["delivered"] is False, (
        f"Telegram refused the message and the applicant was told it went out: {r['body']}")
    assert sentinels(r)[0]["notice_delivered"] is False, (
        "the sentinel says the operator was notified when the notice was refused, so the sweep "
        "would skip a submission nobody has seen.")


# --- invariant 1, on the value the operator's sweep keys on -------------------------------------

def test_a_caught_refusal_is_distinguishable_from_an_invocation_that_died() -> None:
    """`delivered: null` had ONE meaning and the fix silently gave it two.

    Before T-A2-2 a record still holding `null` was one whose invocation died between the writes,
    and its submitter had been told that nothing was saved. Catching the refusal added a second
    world to the same value - told the truth, needs nothing - and the operator's sweep acts on
    those two oppositely. That is invariant 1 arriving inside the change that closed another
    instance of it, and it is why the endpoint writes a sentinel under a DIFFERENT key: the limit
    that produces the failure is one write per second to the same key, so the store is not
    unavailable, only that key is. Found by Fable, against the first draft, which argued the
    silence was forced.
    """
    r = run("writeback_fails")
    marks = sentinels(r)
    assert len(marks) == 1, (
        "no sentinel was written beside the record, so `delivered: null` means both 'the applicant "
        f"was told the truth' and 'the applicant was told nothing was saved': {r['writes']}")
    mark = marks[0]
    written = [w["key"] for w in r["writes"] if w["key"].startswith("request:")]
    assert mark["id"] == r["body"]["id"] and mark["of"] == written[0], (
        # `endswith(id)` was the first draft, and `of: "unrelated:" + id` satisfied it - a sentinel
        # pointing at a key that does not exist, under an assertion whose message says otherwise.
        # The whole key is compared now. Found by Fable.
        f"the sentinel does not point at the record it is about: {mark} vs {written}")
    assert sentinels(r)[0]["notice_delivered"] is r["body"]["delivered"], (
        "the sentinel and the applicant were given different delivery outcomes for the same "
        "submission.")
    assert "429" in mark["reason"], (
        # Truthiness was the first draft, and `reason: "KV unavailable"` - a plausible constant -
        # satisfied it, so every documented same-key 429 would have read to the operator as the
        # one thing the doc says is a finding. The store's own words are what is asserted now.
        f"the sentinel does not carry what the store said. A refusal recorded as a constant cannot "
        f"tell the operator whether they are looking at the documented same-key limit or at "
        f"something new - which is the difference between a known cost and a finding: {mark}")

def test_each_refusal_is_marked_under_a_key_of_its_own() -> None:
    """A constant sentinel key satisfies every other assertion in this file and destroys the
    sentinel's purpose: concurrent refusals overwrite each other's marks, and a second refusal
    inside one second is refused by the very same-key limit the sentinel exists to route around.
    The `of` field was compared to the record's key and the key it is STORED under was not. Found
    by Fable."""
    r = run("writeback_fails")
    key = [w["key"] for w in r["writes"] if w["key"].startswith("writeback-refused:")][0]
    assert key == f"writeback-refused:{records(r)[0]['received_at']}:{r['body']['id']}", (
        f"the sentinel is not stored under a key of its own: {key}")


def test_the_refusal_does_not_have_to_be_recognisable_to_be_caught() -> None:
    """A gate that exercises one failure shape is a gate about that shape.

    Measured, not imagined: `catch (e) { if (!String(e).includes("429")) throw e; }` kept the whole
    of this suite green while the 500-over-a-durable-record defect returned for every other KV
    failure, because the probe only ever threw a 429. This scenario rejects with something that is
    not a 429 and not an `Error` at all.
    """
    r = run("writeback_fails_unrecognisably")
    assert r["outcome"] == "answered" and r["status"] == 200 and r["body"]["ok"] is True, (
        f"a KV failure the endpoint could not recognise was not caught: {r}")
    assert sentinels(r)[0]["reason"] == "KV unavailable", (
        "the sentinel did not record what the store actually said; a rejection that is not an "
        "Error still carries the only account of why the write failed.")


def test_an_unreachable_notice_is_not_a_delivered_one() -> None:
    """The endpoint's `catch` beside the notice, whose body no scenario reached.

    Telegram refusing a message and Telegram being unreachable are two branches, and the repair for
    "the delivery outcome is unmeasured in the false direction" covered only the first. A
    `catch { delivered = true }` passed all eleven assertions: every applicant told the operator had
    been notified, every sentinel recording it, and the sweep skipping them all. Found by Fable.
    """
    r = run("notice_throws_writeback_fails")
    assert r["notices"] == 1, "the notice was never attempted; this scenario measures nothing"
    assert r["status"] == 200 and r["body"]["ok"] is True
    assert r["body"]["delivered"] is False, (
        f"the notice could not be sent at all and the applicant was told it went out: {r['body']}")
    assert sentinels(r)[0]["notice_delivered"] is False


def test_the_write_back_carries_the_delivery_outcome_it_measured() -> None:
    """The ordinary success path with a notice, which no scenario combined.

    Every notice scenario refused the write-back and the one successful write-back sent no notice,
    so the write whose entire purpose is carrying the measured outcome into the store was never
    observed carrying anything but `false`. `delivered: false` hardcoded on that line passed all
    eleven assertions and would flag every notified applicant as unseen in the operator's sweep -
    the sweep acting on a value nothing measured. Found by Fable.
    """
    r = run("notice_sent_both_writes_land")
    assert r["notices"] == 1 and r["body"]["delivered"] is True
    kept = records(r)
    assert len(kept) == 2 and kept[1]["delivered"] is True, (
        f"the stored record does not carry the delivery outcome the applicant was given: {kept}")
    assert not sentinels(r)


def test_when_the_sentinel_is_refused_too_the_answer_still_goes_out() -> None:
    """The nested write is a second chance, never a second way to fail.

    And what it leaves behind is deliberately not distinguished: a record with no sentinel is what
    a dead invocation leaves, and the operator reads both as "we cannot tell whether this person
    was answered" - the true statement about them.
    """
    r = run("both_writes_refused")
    assert r["outcome"] == "answered" and r["status"] == 200 and r["body"]["ok"] is True, (
        f"a refused sentinel took the applicant's confirmation down with it: {r}")
    assert records(r) and not sentinels(r)


# --- the other direction, without which the fix is 'catch everything' ---------------------------

def test_a_submission_that_really_was_lost_is_still_reported_as_lost() -> None:
    """When the durable write fails, "Nothing was saved" is TRUE and must still be shown.

    A biconditional, in LAW-NOTES-ENTRANCE's shape: this gate is as much about not claiming a
    record that does not exist as about not disclaiming one that does. Catching the whole handler
    would satisfy every assertion above and quietly turn the intake into a form that always says
    yes.
    """
    r = run("durable_write_fails")
    assert stored(r, "") == [], "this scenario is supposed to store nothing"
    assert r["outcome"] == "invocation_failed", (
        f"the endpoint answered {r.get('status')} {r.get('body')} after storing nothing. A "
        "confirmation for a submission that does not exist is the same defect facing the other "
        "way - and it is the worse direction, because nobody sweeps for a record that was never "
        "written.")


# --- controls: the probe reaches the real code, and does not answer 200 to everything ------------

def test_the_ordinary_path_is_unchanged_and_leaves_no_sentinel() -> None:
    """A sentinel written unconditionally would be a claim about a refusal that never happened -
    and it would mean the operator's one distinguishing mark distinguishes nothing."""
    r = run("both_writes_land")
    assert r["status"] == 200 and r["body"]["ok"] is True
    kept = records(r)
    assert len(kept) == 2, f"the endpoint no longer performs two writes: {kept}"
    assert kept[0]["delivered"] is None and kept[1]["delivered"] == r["body"]["delivered"], (
        "the record written back does not carry the delivery outcome the applicant was given, so "
        "the sweep and the confirmation describe the same submission differently.")
    assert not sentinels(r), f"a write-back that succeeded left a refusal behind it: {r['writes']}"


def test_the_probe_is_exercising_the_real_endpoint() -> None:
    """INSTRUMENT CONTROL. A probe that had stopped reaching `apply.js` - a moved file, a stubbed
    import, a handler that no longer runs - would answer the scenarios above by doing nothing, and
    every assertion here is of the form "the response is fine". A rejected submission is the cheap
    proof that real validation ran: it can only come from the endpoint's own regular expression."""
    r = run("invalid_repo")
    assert r["status"] == 400 and r["body"]["ok"] is False, (
        f"an invalid repository URL was accepted: {r['status']} {r['body']}")
    assert "GitHub" in r["body"]["error"], f"the refusal did not come from the endpoint: {r['body']}"
    assert r["writes"] == [], "a rejected submission reached the store"


# --- the sentence this whole gate is about lives in the other file ------------------------------

def test_the_form_says_nothing_was_saved_only_on_a_refusal() -> None:
    """Two copies of one rule, and nothing else compares them (L-20).

    The endpoint's `ok: true` is worth exactly what the page does with it. If the form ever stopped
    keying its failure branch on `ok`, the endpoint could answer honestly all day and the visitor
    would still read the false sentence - so the coupling is asserted rather than assumed.
    """
    form = FORM.read_text(encoding="utf-8")
    assert re.search(r"if\s*\(\s*!r\.ok\s*\|\|\s*!d\.ok\s*\)", form), (
        "web/src/pages/Apply.tsx no longer enters its failure branch on `!r.ok || !d.ok`. The "
        "endpoint answers `ok: true` for a submission that is durable; a page that decides "
        "otherwise makes that answer meaningless.")
    failure_branch = form.split('sent.state === "failed"', 1)
    assert len(failure_branch) == 2, "the form no longer has a failed state to render"
    assert form.count("Nothing was saved") == 1 and "Nothing was saved" in failure_branch[1], (
        "'Nothing was saved' is shown outside the failure branch, or more than once. It is the "
        "one sentence on this site that asserts a record does NOT exist, and it may be rendered "
        "only where the endpoint refused the submission.")


def test_the_endpoint_this_gate_guards_still_exists() -> None:
    """A gate pointed at a moved file reports clean forever - L-16's shape."""
    for path in (ENDPOINT, FORM):
        assert path.is_file(), (
            f"{path} is missing. If the intake moved, move this gate in the same commit rather "
            "than letting it pass over nothing.")
