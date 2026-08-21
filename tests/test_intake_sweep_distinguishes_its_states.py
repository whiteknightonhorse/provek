"""T-A2-3 - the operator's sweep names what it found (LAW-INTAKE-SWEEP-NAMES-ITS-STATES).

THE DEFECT. `docs/INTAKE_OPERATIONS.md` carries the only instrument that finds a submission nobody
has followed up. Its filter was `select(.delivered == false)`, and the state both of T-A2-2's
failures land in is `delivered: null` (`web/functions/api/apply.js`, the write before the notice):
durable, unanswered, and never printed. T-A2-2's own commit widened the filter to `false or null`
and printed both under one word - which is the same defect one level up. `false` is a MEASURED
outcome, the notice was attempted and did not go out; `null` is the ABSENCE of that measurement, and
the follow-up for it is a different act, keyed on a sentinel the other state has no use for.
Invariant 1, inside the instrument this project keeps in order to enforce it.

AND THE INSTRUMENT COULD NOT REPORT ITS OWN REFUSAL. `v=$(npx wrangler kv key get ...)` was read
whatever the exit status: a key the store declined to hand over printed nothing, which is exactly
what a healthy `delivered: true` prints. The same held one level up - a failed `list` produced no
keys, and no keys is what an empty namespace produces, so a sweep that never ran read as a quiet
day. That is the §2.9 defect the operator's brief opens with, in the tool the whole habit rests on.

WHY THIS GATE RUNS THE SWEEP INSTEAD OF READING IT. A gate that greps the document for `null` can
see that a string is present and can never see what the sweep PRINTS. Every defect above survives
such a grep: a filter that matches both states and labels them identically contains the string, and
so does one whose `jq` reads a refused read as an ordinary record. So the fenced block is extracted
from the document, run under `bash` against a stubbed namespace (`tests/kv_stub.py`, put on PATH
under the name `npx`), and its stdout and exit status are asserted. It is the second gate here that
executes what it guards rather than matching patterns against it, after
`tests/test_intake_survives_a_failed_writeback.py`.

WHAT IS NOT ASSERTED, and it is the larger half. That the REAL `wrangler` refuses in the shapes the
stub refuses in, that Workers KV returns the JSON shape the stub returns, and that the operator runs
this at all. The sweep is a habit performed on a laptop this host cannot reach (the document says
so), and none of that is measurable from here - it is named rather than folded into a green. What
this gate closes is the gap between the document's fenced block and what that block does when run.

HOW TO MAKE IT FAIL, in the twenty-two ways it is filed under: restore the `== false` filter; print
both states under one label; drop the check on the `get`; drop the check on the `list`; render the
delivery outcome as text so a stored string reads as a boolean; print the sentinel as a submission;
return zero whatever was found; drop the count so a quiet day is silence; guard the
`no submission has ever been made` sentence on readable records alone; point the `get` at another
namespace; stop counting the notified records, the refusal marks, or the unreadable ones; transpose
two counters in the summary; take a sentinel that could not be parsed - or one storing `null`, `{}`
or nothing at all, or missing either of the two fields the third's fixture did not omit - as one
that was read; read a mark's measured `notice_delivered: false` as an absent field; print a finding
and report it in a clean exit status on either of the two branches whose `rc` no test reached; or
file a finding under the status that means the sweep did not run at all.

FOURTEEN OF THE TWENTY-TWO WERE GREEN when Fable applied them, over three rounds against three
drafts of this file, and that is the honest summary of it: each round refuted the repairs made for
the one before it, and twice a repair had narrowed a defect to the single input its own new test
used - the second time inside the fix for the first. Each is a number, a sentence or a status the
operator acts on. The runs are produced by
`evidence/RED-018-generator.py` and kept as
`evidence/RED-018-a-sweep-that-cannot-name-what-it-found.txt`.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "INTAKE_OPERATIONS.md"
STUB = ROOT / "tests" / "kv_stub.py"

NS = "5d93877f53d94f3fbc4863a0195fc9a4"


def sweep_source() -> str:
    """The sweep as the document actually carries it, or a hard failure naming why not.

    THE EXTRACTION IS ITSELF A GATE. If the document grows a second block that reads KV, or the
    sweep is deleted, this returns nothing to run and every assertion below would pass over an
    empty string - a suite that goes green in the state where it measures nothing (L-16). Both
    cases are an assertion failure here instead.
    """
    assert DOC.is_file(), f"{DOC} is missing - the sweep this gate is about lives nowhere else."
    blocks = re.findall(r"```bash\n(.*?)```", DOC.read_text(encoding="utf-8"), re.S)
    sweeps = [b for b in blocks if "kv key get" in b]
    assert len(sweeps) == 1, (
        f"{DOC.name} carries {len(sweeps)} fenced blocks that read KV values, not 1. This gate runs "
        "the one the operator is told to run; two of them means it is guessing which, and none "
        "means the habit has no instrument.")
    return sweeps[0]


def run(keys: dict, list_state: str | None = None) -> dict:
    """Run the document's sweep against a stubbed namespace and report what it printed.

    `keys` maps a KV key to `{"value": "<stored bytes>"}` or `{"refuse": True}`.
    """
    assert STUB.is_file(), (
        f"{STUB} is missing - the instrument this gate reads through is gone, so every assertion "
        "below would be about nothing.")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        binned = tmp / "bin"
        binned.mkdir()
        # The stub answers under the name the sweep calls, so nothing in the block is rewritten for
        # the test. A sweep edited on its way into the harness is not the sweep in the document.
        shutil.copy(STUB, binned / "npx")
        (binned / "npx").chmod(0o755)

        log = tmp / "invocations.log"
        fixture = tmp / "fixture.json"
        fixture.write_text(json.dumps({"list": list_state, "keys": keys, "log": str(log)}),
                           encoding="utf-8")
        script = tmp / "sweep.sh"
        script.write_text(sweep_source(), encoding="utf-8")

        env = dict(os.environ)
        env["PATH"] = f"{binned}{os.pathsep}{env.get('PATH', '')}"
        env["KV_STUB_FIXTURE"] = str(fixture)
        try:
            done = subprocess.run(["bash", str(script)], cwd=ROOT, env=env,
                                  capture_output=True, text=True, timeout=120)
        except FileNotFoundError:
            raise AssertionError(
                "`bash` is not on PATH, so the only gate that RUNS the operator's sweep could not "
                "run. A missing instrument is a red here, never a skip (L-16).") from None
        return {
            "status": done.returncode,
            "out": done.stdout,
            "err": done.stderr,
            "calls": log.read_text(encoding="utf-8").splitlines() if log.exists() else [],
        }


def record(key: str, delivered) -> tuple[str, dict]:
    """One stored submission, in the shape `apply.js` writes."""
    body = {"id": key.rsplit(":", 1)[-1], "received_at": key.split(":", 1)[1].rsplit(":", 1)[0],
            "repo": "https://github.com/a/b", "contact": "a@b.co", "delivered": delivered}
    return key, {"value": json.dumps(body)}


FINDINGS = ("NOT NOTIFIED", "NO OUTCOME", "UNREADABLE", "SURVIVED TO ANSWER")


def labels(result: dict) -> dict[str, str]:
    """Key -> the label it was printed under. A key printed under two labels is a defect.

    ONLY THE FOUR LABELS ARE PARSED. Splitting every line on its first colon read the count and the
    empty-namespace sentence as findings about keys named "SWEPT" and "Zero" - harmless here, and
    the shape in which a gate stops noticing that a real key was never printed at all.
    """
    out: dict[str, str] = {}
    for line in result["out"].splitlines():
        label = next((lab for lab in FINDINGS if line.startswith(lab + ": ")), None)
        if label is None:
            continue
        key = line[len(label) + 2:].split(" ", 1)[0].strip()
        assert key not in out, f"the sweep printed {key} under two labels: {result['out']}"
        out[key] = label
    return out


TRUE = "request:2026-08-21T10:00:00.000Z:aaaaaaaa"
FALSE = "request:2026-08-21T10:01:00.000Z:bbbbbbbb"
NULL = "request:2026-08-21T10:02:00.000Z:cccccccc"
MARK = "writeback-refused:2026-08-21T10:02:00.000Z:cccccccc"
SENTINEL = json.dumps({"of": NULL, "id": "cccccccc", "notice_delivered": True,
                       "refused_at": "2026-08-21T10:02:01.000Z",
                       "reason": "KV PUT failed: 429 Too Many Requests"})


# --- the defect this task is filed under --------------------------------------------------------

def test_a_record_that_never_got_its_outcome_is_found() -> None:
    """`delivered: null` is what both of T-A2-2's failures leave, and the original filter skipped it.

    This is the whole of the original defect: the one record in the namespace nobody has confirmed
    was the one record the habit passed over.
    """
    r = run(dict([record(NULL, None)]))
    assert NULL in labels(r), (
        "a record whose delivery outcome never landed was not printed at all. That is the state a "
        f"refused write-back and a dead invocation both leave: {r['out']!r}")
    assert r["status"] != 0, "the sweep found an unconfirmed submission and reported success"


def test_the_two_states_are_not_one_finding() -> None:
    """A measured `false` and an absent measurement are followed up differently.

    `false`: the record is stored and the operator was not told, so the operator reads it now.
    `null`: nothing recorded what the notice did, and the follow-up turns on a sentinel that has no
    meaning for a `false` at all. One label over both is a count the operator cannot act on -
    invariant 1, one level up from the field it is usually about.
    """
    r = run(dict([record(FALSE, False), record(NULL, None)]))
    seen = labels(r)
    assert FALSE in seen and NULL in seen, f"a state was not printed at all: {r['out']!r}"
    assert seen[FALSE] != seen[NULL], (
        f"both states are printed as {seen[FALSE]!r}. The sweep finds them and cannot say which is "
        "which, so the operator either treats a notified applicant as uninformed or the reverse.")


def test_a_notified_record_is_not_a_finding() -> None:
    """The other direction, without which "print everything" satisfies this file.

    A sweep that prints every record under some label finds the `null` too, and hands the operator
    a list of everyone who has ever applied.
    """
    r = run(dict([record(TRUE, True)]))
    assert TRUE not in labels(r), (
        f"a record whose notice went out was reported as needing follow-up: {r['out']!r}")
    assert r["status"] == 0, (
        f"a namespace with nothing to act on did not exit 0: {r['status']} {r['out']!r}")


# --- the instrument's own refusals, which are not readings --------------------------------------

def test_a_refused_read_is_not_a_record_with_nothing_wrong_with_it() -> None:
    """A `get` that failed printed nothing, and nothing is what a healthy record prints.

    §2.9: a refusal returned as an ordinary answer takes from the follow-up its only evidence that
    anything was missed. The draft before this one read `$v` whatever the exit status.
    """
    r = run({FALSE: {"refuse": True}})
    seen = labels(r)
    assert FALSE in seen, (
        f"a key the store refused to hand over was passed over in silence: {r['out']!r}")
    assert seen[FALSE] == "UNREADABLE", (
        f"a refused read was reported as a measured state ({seen[FALSE]}), which is a claim about a "
        "value nobody read.")
    # `!= 0` WAS THE FIRST DRAFT, and `rc=2` on this branch satisfied it: a sweep that ran, printed
    # its count and found an unreadable key, reporting the status reserved for a sweep that did not
    # run - which the document says appears instead of the count and never beside it. A dropped
    # status and a misfiled one are two defects, and only the first was armed. Found by Fable.
    assert r["status"] == 1, (
        f"a refused read was reported with status {r['status']}, not as something to act on. 2 is "
        f"reserved for a reading that never happened, and this one happened: {r['out']!r}")


def test_a_refused_read_and_an_unreadable_value_are_not_the_same_account() -> None:
    """Both are `UNREADABLE`, and the operator does two different things with them.

    A read the store refused is retried; a value that is not a record is a finding about what wrote
    it. Checking only that something printed leaves the exit status of the `get` ignorable - and
    ignoring it classifies a key nobody read from the empty string it left behind, which reports a
    refusal as a property of the data.
    """
    r = run({FALSE: {"refuse": True}, NULL: {"value": "<html>an error page</html>"}})
    said = {}
    for line in r["out"].splitlines():
        if line.startswith("UNREADABLE: "):
            key, _, why = line[len("UNREADABLE: "):].partition(" - ")
            said[key] = why
    assert set(said) == {FALSE, NULL}, f"both were expected to be unreadable: {r['out']!r}"
    assert "refused the read" in said[FALSE], (
        f"a key the store would not hand over was reported as a bad record: {said[FALSE]!r}. The "
        "sweep did not read it, and saying anything about its contents is a claim about a value "
        "nobody has.")
    assert said[FALSE] != said[NULL], (
        "a refused read and an unreadable value carry the same account, so the operator cannot "
        "tell a store to retry from a record to investigate.")


def test_a_refused_list_is_not_an_empty_namespace() -> None:
    """The same defect one level up, and the more dangerous one: it is silent about EVERY record."""
    r = run({}, list_state="refuse")
    assert "SWEEP DID NOT RUN" in r["out"], (
        f"the namespace could not be listed and the sweep did not say so: {r['out']!r}")
    assert "SWEPT" not in r["out"], (
        f"a sweep that could not list the namespace still reported a count of what it swept: "
        f"{r['out']!r}")
    assert r["status"] == 2, (
        f"a sweep that did not run exited {r['status']}. 0 is 'nothing qualified' and 1 is 'act on "
        "these'; a run that measured nothing is neither, and a scheduled job reading it as either "
        "goes quiet exactly as this document's subject goes quiet.")


def test_a_list_that_comes_back_unreadable_is_not_an_empty_namespace_either() -> None:
    """An exit status of 0 over a body that is not JSON - an error page, a truncated response.

    Checking only the exit status would leave `jq` printing nothing on stdin it could not parse and
    the sweep reporting a clean empty namespace.
    """
    r = run({}, list_state="malformed")
    assert "SWEEP DID NOT RUN" in r["out"] and r["status"] == 2, (
        f"an unreadable key list was swept as though it were empty: {r['status']} {r['out']!r}")


def test_a_value_that_is_not_a_record_is_not_a_delivery_outcome() -> None:
    """Anything in the value slot that carries no `delivered` field is unreadable, not clean."""
    r = run({FALSE: {"value": "<html>an error page</html>"},
             NULL: {"value": json.dumps({"id": "cccccccc"})}})
    seen = labels(r)
    assert seen.get(FALSE) == "UNREADABLE", f"a value that is not JSON was swept over: {r['out']!r}"
    assert seen.get(NULL) == "UNREADABLE", (
        f"a record with no `delivered` field at all was swept over: {r['out']!r}")


def test_a_stored_string_is_not_a_measured_boolean() -> None:
    """`tostring` renders the string "false" and the boolean `false` identically.

    The endpoint writes a boolean or `null` and nothing else, so a string in that field is a record
    written by something other than this endpoint - which is a finding, and specifically not the
    finding "the operator was not told", whose follow-up asserts to an applicant what happened.
    """
    r = run({FALSE: {"value": json.dumps({"id": "bbbbbbbb", "delivered": "false"})}})
    assert labels(r).get(FALSE) == "UNREADABLE", (
        f"a stored string was read as the delivery outcome the endpoint measures: {r['out']!r}")


# --- the sentinel is not a submission -----------------------------------------------------------

def test_the_sweep_does_not_report_its_own_marker_as_a_finding() -> None:
    """A `writeback-refused:` key carries no `delivered` field, so every filter over that field
    matches it. An instrument that reports its own marker as a finding is worse than one that
    ignores it: the operator would follow up a sentinel, and the count of people would double."""
    r = run(dict([record(NULL, None), (MARK, {"value": SENTINEL})]))
    seen = labels(r)
    assert seen.get(MARK) == "SURVIVED TO ANSWER", (
        f"the sentinel was printed as though it were a submission: {r['out']!r}")
    assert "429" in r["out"], (
        "the sentinel's reason was not printed. It is what tells the operator whether they are "
        "looking at the documented same-key limit or at something nobody has seen yet.")
    assert re.search(r"SWEPT 1 records and 1 refusal marks", r["out"]), (
        f"the sentinel was counted among the records, so the count of submissions is not one: "
        f"{r['out']!r}")


def test_a_sentinel_that_cannot_be_read_is_not_a_sentinel_that_was_read() -> None:
    """`jq` writes its parse errors to stderr, so an unparseable mark printed under the healthy
    label with an empty summary after it - and the emptiness is invisible to anything capturing
    stdout, which is what the scheduled job the document anticipates would do. The operator would
    read a mark as saying its applicant survived to be answered, off a value that said nothing.
    Found by Fable."""
    r = run({MARK: {"value": "<html>an error page</html>"}})
    assert labels(r).get(MARK) == "UNREADABLE", (
        f"an unreadable refusal mark was reported as one that had been read: {r['out']!r}")
    assert "UNREADABLE 1" in r["out"] and r["status"] != 0, (
        f"an unreadable mark was counted as measured: {r['out']!r}")


def test_a_mark_that_carries_nothing_is_not_a_mark_that_was_read() -> None:
    """The repair for the case above, refuted: it checked that `jq` had not FAILED.

    `{of, notice_delivered, reason}` over a stored `null` or `{}` builds an object of three nulls
    and succeeds, and on jq 1.6 an empty value exits 0 having printed nothing at all - so each of
    these printed `SURVIVED TO ANSWER` with an empty or hollow summary and exited 0, which is the
    exact symptom the previous test is about. A fix that narrows a defect to the inputs its own
    test used is the shape this whole file is filed under. Found by Fable, on the repair.
    """
    for name, value in (("empty", ""), ("JSON null", "null"), ("an empty object", "{}"),
                        ("an object missing `reason`",
                         json.dumps({"of": NULL, "notice_delivered": True}))):
        r = run({MARK: {"value": value}})
        assert labels(r).get(MARK) == "UNREADABLE", (
            f"a refusal mark whose value is {name} was reported as one that had been read: "
            f"{r['out']!r}")
        assert r["status"] == 1, (
            f"a mark carrying nothing was swept as a clean run: {r['status']} {r['out']!r}")


def test_a_mark_that_does_not_say_which_record_it_is_about_is_unreadable() -> None:
    """`of` is the whole of the pairing the follow-up runs on: a mark without it cannot be read
    beside anything, and the operator is left with a `NO OUTCOME` record and a mark that does not
    claim to be its. Its own test, because the check is a conjunction of three fields and the case
    above exercised one of them - so deleting either of the other two conjuncts was green, which is
    this file's own subject a third time. Found by Fable."""
    r = run({MARK: {"value": json.dumps({"notice_delivered": True, "reason": "429"})}})
    assert labels(r).get(MARK) == "UNREADABLE", (
        f"a refusal mark that names no record was read as one that does: {r['out']!r}")


def test_a_mark_that_does_not_carry_a_delivery_outcome_is_unreadable() -> None:
    """The field the mark exists to carry. Without it the pairing says the endpoint survived to
    answer and cannot say what the applicant was told, which is the state the sentinel was
    introduced to end."""
    r = run({MARK: {"value": json.dumps({"of": NULL, "reason": "429"})}})
    assert labels(r).get(MARK) == "UNREADABLE", (
        f"a refusal mark carrying no delivery outcome was read as a complete one: {r['out']!r}")


def test_a_mark_recording_a_notice_that_did_not_go_out_is_still_a_mark() -> None:
    """The other direction of the check above, and the reason it asks `has()` rather than a
    truthy value: `notice_delivered: false` is a MEASURED outcome, and a sentinel carrying it is
    the one the operator most needs read out - the applicant was answered and nobody was told."""
    value = json.dumps({"of": NULL, "id": "cccccccc", "notice_delivered": False,
                        "refused_at": "2026-08-21T10:02:01.000Z", "reason": "429"})
    r = run({MARK: {"value": value}})
    assert labels(r).get(MARK) == "SURVIVED TO ANSWER", (
        f"a mark recording an undelivered notice was read as unreadable: {r['out']!r}")
    assert '"notice_delivered":false' in r["out"].replace(" ", ""), (
        f"the measured delivery outcome was not printed: {r['out']!r}")


# --- a zero that says which zero it is ----------------------------------------------------------

NEVER_MADE = "no submission has ever been made"


def test_an_empty_namespace_is_a_reading_and_not_a_silence() -> None:
    """Zero keys means no submission has ever been made - the state the endpoint has never once
    been exercised in end to end, which the document reads as a finding about the launch. A sweep
    whose findings are its whole output cannot say it, and cannot be told apart from one that
    refused."""
    r = run({})
    assert "SWEPT 0 records" in r["out"], (
        f"an empty namespace produced no statement that it was read: {r['out']!r}")
    assert NEVER_MADE in r["out"], f"the empty namespace was not read as a finding: {r['out']!r}"
    assert r["status"] == 0


def test_a_namespace_it_could_not_read_is_not_a_namespace_nobody_has_used() -> None:
    """The sweep's own strongest sentence, and the first draft printed it over three different zeros.

    `no submission has ever been made` is a claim about the whole history of the endpoint. It was
    guarded on the count of READABLE records, so a namespace holding one submission the store
    refused to hand over printed it - underneath the `UNREADABLE` line naming that very key - and so
    did a namespace holding a refusal mark, which exists only because a submission was made. A claim
    about values nobody read, in the sentence this document exists to forbid. Found by Fable.
    """
    refused = run({FALSE: {"refuse": True}})
    assert NEVER_MADE not in refused["out"], (
        f"the sweep listed a submission, failed to read it, and reported that no submission has "
        f"ever been made: {refused['out']!r}")
    mark_only = run({MARK: {"value": SENTINEL}})
    assert NEVER_MADE not in mark_only["out"], (
        f"a namespace holding the endpoint's own refusal mark - which is written only after a "
        f"submission was stored - was read as one that has never had a submission: "
        f"{mark_only['out']!r}")


def test_every_number_in_the_count_is_counted() -> None:
    """The count line printing is not the same fact as its numbers being true.

    Asserted over one namespace holding every state at once, because a counter is only observed to
    work when it has something to count: with `notified`, `UNREADABLE` and the refusal marks each
    exercised only in runs where their true value was zero, dropping any of those three increments
    left the whole suite green and printed `notified 0` on a day with three notified records - a
    counter reading a false zero, which is invariant 1's literal subject. Found by Fable, who
    applied all three.

    AND A DIFFERENT COUNT IN EVERY BUCKET, where the draft before this one gave each of them
    exactly 1.
    Four counters holding the same number print the same line under every permutation of
    themselves, so swapping `$notified` and `$not_notified` in the summary - a day with four
    notified records reported as four unseen ones, and the operator writing to all of them - kept
    the suite green. That is RED-013's transposition, reintroduced by the fixture written to close
    a different defect in the same line. Found by Fable.
    """
    keys = dict([record(TRUE, True), record(FALSE, False), record(NULL, None),
                 (MARK, {"value": SENTINEL})])
    for n in range(3):  # notified: 4
        keys.update([record(f"request:2026-08-21T11:0{n}:00.000Z:1111111{n}", True)])
    for n in range(2):  # not notified: 3
        keys.update([record(f"request:2026-08-21T12:0{n}:00.000Z:2222222{n}", False)])
    keys.update([record("request:2026-08-21T13:00:00.000Z:33333333", None)])  # no outcome: 2
    keys["request:2026-08-21T14:00:00.000Z:44444444"] = {"refuse": True}  # unreadable: 1
    keys["writeback-refused:2026-08-21T15:00:00.000Z:55555555"] = {"value": SENTINEL}  # marks: 2
    r = run(keys)
    assert ("SWEPT 10 records and 2 refusal marks: notified 4, NOT NOTIFIED 3, NO OUTCOME 2, "
            "UNREADABLE 1." in r["out"]), (
        f"the count does not describe the namespace it swept: {r['out']!r}. Every state above is "
        "present a different number of times, so a number that is wrong cannot be a number that "
        "was copied from its neighbour.")


def test_a_day_on_which_nothing_was_notified_reports_nothing_notified() -> None:
    """A zero in the count that has to BE a zero, and the pair that tells two defects apart.

    A counter that stopped counting and a counter transposed with its neighbour both print a wrong
    summary over a namespace holding every state, and they print DIFFERENT wrong summaries here:
    with nothing notified and three submissions unseen, a `notified` that stopped counting is still
    right, and one carrying its neighbour's value reports three notified applicants who do not
    exist. Without this the two are one finding, which is the transposition RED-013 was corrected
    for, this time between mutations rather than inside one.
    """
    keys = dict([record(FALSE, False)])
    for n in range(2):
        keys.update([record(f"request:2026-08-21T16:0{n}:00.000Z:6666666{n}", False)])
    r = run(keys)
    assert "notified 0, NOT NOTIFIED 3" in r["out"], (
        f"three submissions nobody was told about were not counted as three, or the run invented "
        f"notified records to sit beside them: {r['out']!r}")


def test_the_count_accounts_for_every_key_that_was_listed() -> None:
    """`records + marks` is the whole namespace, readable or not.

    A key the store refused was still LISTED, so a count that rises only on a successful read drops
    exactly the keys the sweep exists to surface - and then reports a smaller namespace than the one
    it swept, which reads as though those submissions had never been made.
    """
    r = run({FALSE: {"refuse": True}, MARK: {"refuse": True}})
    assert "SWEPT 1 records and 1 refusal marks" in r["out"], (
        f"keys that could not be read fell out of the count of what was swept: {r['out']!r}")
    assert "UNREADABLE 2" in r["out"], (
        f"the count does not say how much of the namespace went unmeasured: {r['out']!r}")


def test_a_submission_nobody_was_told_about_is_a_finding_in_the_status_too() -> None:
    """`rc` is one variable and four branches set it; the exit-status test reaches it through a
    `NO OUTCOME` alone. So dropping `rc=1` from the `NOT NOTIFIED` branch - a submission the
    operator was never told about, printed and then reported as a clean run to the scheduled job
    the document anticipates - left the suite green. Found by Fable.

    ONE STATE PER TEST, not a loop over all of them: a loop stops at its first failure and reports
    one finding for two defects, which is how mutations 15 and 16 of RED-018 arrived carrying the
    same transcript.
    """
    r = run(dict([record(FALSE, False)]))
    assert r["status"] == 1, (
        f"the sweep printed a submission the operator was never told about and exited "
        f"{r['status']}, which is what it exits when there is nothing to act on: {r['out']!r}")


def test_a_record_that_could_not_be_read_is_a_finding_in_the_status_too() -> None:
    """The same branch one state over, and the worse half: what went unmeasured is not a delivery
    outcome but the record itself."""
    r = run({NULL: {"value": "<html>an error page</html>"}})
    assert r["status"] == 1, (
        f"the sweep could not read a stored record and reported a clean run: {r['out']!r}")


def test_a_value_that_could_not_be_read_is_counted_as_unmeasured() -> None:
    """The unreadable-VALUE branch, whose counter was only ever exercised through the refused-READ
    branch: dropping the increment printed `UNREADABLE 0` directly beneath an `UNREADABLE:` line -
    a false zero in the number that says how much of the namespace went unmeasured. Found by Fable.
    """
    r = run({NULL: {"value": "<html>an error page</html>"}})
    assert "UNREADABLE 1" in r["out"], (
        f"a record that could not be read was not counted as unmeasured: {r['out']!r}")


def test_the_exit_status_carries_three_states() -> None:
    """0 / 1 / 2 - nothing qualified, act on these, did not run. Asserted together, because the
    three are only meaningful against each other."""
    clean = run(dict([record(TRUE, True)]))
    found = run(dict([record(NULL, None)]))
    refused = run({}, list_state="refuse")
    assert (clean["status"], found["status"], refused["status"]) == (0, 1, 2), (
        "the sweep's exit status does not distinguish a clean read, a finding and a reading that "
        f"never happened: {clean['status']}, {found['status']}, {refused['status']}")


# --- controls: the sweep really ran, and really read the store ----------------------------------

def test_the_sweep_read_every_key_it_listed() -> None:
    """INSTRUMENT CONTROL. Every assertion above is of the form "the output says X", and a block
    that had stopped reaching the store - a renamed subcommand, a `jq` that errored on every value,
    a loop that never entered - could produce plausible output by doing nothing. The stub records
    what it was asked for: one `list`, and one `get` per key listed."""
    keys = dict([record(TRUE, True), record(FALSE, False), (MARK, {"value": SENTINEL})])
    r = run(keys)
    assert sum(1 for c in r["calls"] if c.startswith("wrangler kv key list")) == 1, (
        f"the sweep did not list the namespace exactly once: {r['calls']}")
    got = {c.split()[4] for c in r["calls"] if c.startswith("wrangler kv key get")}
    assert got == set(keys), (
        f"the sweep did not read every key it was given: asked for {sorted(got)}, listed "
        f"{sorted(keys)}")
    assert "unrecognised invocation" not in r["err"], (
        f"the sweep called the store in a shape this gate does not model, so what it did there is "
        f"not measured here: {r['err']!r}")


def test_the_sweep_addresses_the_namespace_the_document_names() -> None:
    """A sweep pointed at another namespace would pass every assertion above against the stub and
    read nothing in production. The id is the one fact in the block that no run can check.

    OVER A NAMESPACE WITH KEYS IN IT, because the first draft ran this against an empty one: the
    only call it could inspect was the `list`, and the id on the `get` - the call that fetches every
    value the operator acts on - was never in the transcript at all. The docstring said "a sweep
    pointed at another namespace", the assertion covered half of one, and pointing the `get`
    elsewhere kept the whole suite green. Found by Fable.
    """
    r = run(dict([record(TRUE, True), (MARK, {"value": SENTINEL})]))
    verbs = {c.split()[3] for c in r["calls"]}
    assert verbs == {"list", "get"}, (
        f"this control did not observe both calls, so it cannot speak for both: {r['calls']}")
    for call in r["calls"]:
        assert f"--namespace-id {NS}" in call, (
            f"a call went to a namespace other than the one the document names: {call!r}")


def test_the_block_is_valid_bash_before_it_is_anything_else() -> None:
    """A snippet nobody can run is not an instrument. `bash -n` parses without executing."""
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "sweep.sh"
        script.write_text(sweep_source(), encoding="utf-8")
        done = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
    assert done.returncode == 0, (
        f"the sweep in {DOC.name} does not parse, so the operator's daily habit is a paste that "
        f"fails: {done.stderr}")


def test_the_document_and_the_stub_this_gate_reads_through_both_exist() -> None:
    """A gate pointed at a moved file reports clean forever - L-16's shape."""
    for path in (DOC, STUB):
        assert path.is_file(), (
            f"{path} is missing. If it moved, move this gate in the same commit rather than "
            "letting it pass over nothing.")
