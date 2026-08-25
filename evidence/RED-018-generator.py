#!/usr/bin/env python3
"""Produces evidence/RED-018-a-sweep-that-cannot-name-what-it-found.txt.

    python3 evidence/RED-018-generator.py            # writes the artefact beside this file
    python3 evidence/RED-018-generator.py --check    # runs everything, writes nothing

WHAT IT ESTABLISHES. That `tests/test_intake_sweep_distinguishes_its_states.py` CAN fail
(invariant 5), in each of the twenty-two directions the gate is filed under - FOURTEEN of which
were GREEN when Fable applied them, over three rounds of refutation, each round against the repairs
made for the one before it. The subject is a fenced
`bash` block inside a document - the operator's KV sweep - which is exactly the shape a gate cannot
be assumed to hold: nothing in a Markdown file fails a build by itself, and until T-A2-3 the sweep
had been edited twice with no run behind either edit.

WHY IT MUTATES THE DOCUMENT. The gate extracts the block from `docs/INTAKE_OPERATIONS.md` and runs
it, so the document IS the source under test. A mutation applied to a copy would establish that the
harness can fail on a string, which is not the claim.

IT WRITES THE FILE ITSELF rather than being redirected into it: a shell truncates its target before
Python starts, so every refusal below would empty the committed artefact on its way to declining to
replace it (the defect RED-017's generator shipped and names).

WHAT IT REFUSES TO WRITE THE ARTEFACT OVER, each inherited from RED-017 because each caught a real
draft there:
  * a mutation whose anchor is not unique, or whose marker does not appear afterwards - an edit that
    did not land is a transcript about the pristine sweep;
  * a mutation that does not turn the suite red - a gate unarmed against the edit it is filed under
    is the whole subject;
  * a pytest that did not RUN. Only exit 1 is a suite that ran and failed; any other nonzero is an
    instrument that asserted nothing, and reading it as "red" is invariant 1 inside the tool kept to
    defend invariant 1;
  * a mutation that kills the INSTRUMENT CONTROL. Here that is the test asserting the sweep still
    called the store, once per listed key: a block that stopped reaching KV would fail most of the
    suite while establishing nothing about what it prints. The namespace test was in that list and
    had to come out - see CONTROLS below, where a mutation the gate CATCHES was being reported as
    an instrument that had died;
  * two mutations with the same failure set - the transposition RED-013 was corrected for;
  * a document not restored byte for byte, or not green afterwards.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402 - T-S14, every artefact names the tree it was captured against

SRC = ROOT / "docs" / "INTAKE_OPERATIONS.md"
ARTEFACT = ROOT / "evidence" / "RED-018-a-sweep-that-cannot-name-what-it-found.txt"
SUITE = "tests/test_intake_sweep_distinguishes_its_states.py"

# THE ONE TEST THAT PROVES THE EXTRACTED BLOCK WAS STILL REACHING THE STORE: it reads the stub's
# transcript and demands one `list` and one `get` per listed key. A mutation that kills it has
# broken the instrument rather than removed a property, and its red says nothing about labels.
#
# THE NAMESPACE TEST WAS IN THIS LIST AND HAD TO COME OUT, which is a correction worth keeping.
# Mutation 10 points the `get` at another namespace - exactly the defect that test exists to catch -
# and the generator refused the whole artefact, reporting the gate working as an instrument that had
# died. A test cannot be both the control for a mutation and the property it removes: the control
# must be something no mutation in the file is ABOUT.
CONTROLS = ("test_the_sweep_read_every_key_it_listed",)

NO_OUTCOME = """      null)  echo "NO OUTCOME: $k - stored, and nothing recorded what the notice did."
             no_outcome=$((no_outcome + 1)); rc=1 ;;"""

REFUSED_READ = """    if ! v=$(npx wrangler kv key get "$k" --namespace-id "$NS" </dev/null); then
      echo "UNREADABLE: $k - the store refused the read."
      unreadable=$((unreadable + 1)); rc=1; continue
    fi"""

REFUSED_LIST = """  if ! raw=$(npx wrangler kv key list --namespace-id "$NS" </dev/null); then
    echo "SWEEP DID NOT RUN: the namespace could not be listed, so nothing below was measured."
    return 2
  fi"""

READ_THE_VALUE = """    d=$(jq -c 'if type == "object" and has("delivered") then .delivered else "no-such-field" end' \\
          <<<"$v" 2>/dev/null) || d=unreadable"""

COUNT = ('  echo "SWEPT $records records and $marks refusal marks: notified $notified," \\\n'
         '       "NOT NOTIFIED $not_notified, NO OUTCOME $no_outcome, UNREADABLE $unreadable."')

ZERO_LINE = ('  [ "$records" -eq 0 ] && [ "$marks" -eq 0 ] &&\n'
             '    echo "Zero keys is a reading of its own: no submission has ever been made."')

MARK_READ = """      if ! m=$(jq -ce 'if type == "object" and has("of") and has("notice_delivered")
                          and has("reason")
                       then {of, notice_delivered, reason}
                       else error("not a refusal mark") end' <<<"$v" 2>/dev/null) || [ -z "$m" ]; then
        echo "UNREADABLE: $k - the refusal mark itself could not be read."
        unreadable=$((unreadable + 1)); rc=1
      else
        echo "SURVIVED TO ANSWER: $k $m"
      fi"""

MARK_OPEN = """      if ! m=$(jq -ce 'if type == "object" and has("of") and has("notice_delivered")
                          and has("reason")
                       then {of, notice_delivered, reason}
                       else error("not a refusal mark") end' <<<"$v" 2>/dev/null) || [ -z "$m" ]; then"""

NOT_NOTIFIED = """      false) echo "NOT NOTIFIED: $k - stored, and the notice to the operator did not go out."
             not_notified=$((not_notified + 1)); rc=1 ;;"""

UNREADABLE_VALUE = """      *)     echo "UNREADABLE: $k - no readable delivery outcome in the record (got: $d)."
             unreadable=$((unreadable + 1)); rc=1 ;;"""

MUTATIONS = [
    (
        "1-the-original-filter-restored",
        "THE DEFECT T-A2-3 IS FILED UNDER: `select(.delivered == false)`, which is blind to the "
        "state both of T-A2-2's failures land in. The record is durable, its submitter may have "
        "been told the opposite, and the one instrument that would find it passes over it. The "
        "branch is kept and emptied rather than deleted, so what changes is what the sweep DOES "
        "and not whether the block parses.",
        NO_OUTCOME,
        '      null)  : ;;  # MUTATION: back to matching only `delivered == false`',
    ),
    (
        "2-one-label-over-both-states",
        "WHAT T-A2-2'S OWN COMMIT SHIPPED: the filter finds both states and prints them under one "
        "word. Every count above stays correct and stops meaning anything - the operator gets a "
        "list they cannot act on, because `false` is answered by reading the record now and `null` "
        "is answered against the sentinel beside it, and neither instruction is derivable from the "
        "other. Invariant 1 one level up from the field it is usually about.",
        '      null)  echo "NO OUTCOME: $k - stored, and nothing recorded what the notice did."',
        '      null)  echo "NOT NOTIFIED: $k - one label for two states."  # MUTATION',
    ),
    (
        "3-a-refused-read-is-read-anyway",
        "THE INSTRUMENT'S OWN REFUSAL, SWALLOWED. The exit status of the `get` is ignored, so a key "
        "the store declined to hand over is classified from an empty string. It still prints - the "
        "empty value has no readable outcome in it - and it prints the WRONG account: the operator "
        "is told the record is malformed when what actually happened is that nobody read it. A "
        "refusal recorded as a property of the data is §2.9 inside the tool the habit rests on.",
        REFUSED_READ,
        '    v=$(npx wrangler kv key get "$k" --namespace-id "$NS" </dev/null)'
        "  # MUTATION: status ignored",
    ),
    (
        "4-a-refused-list-swept-as-an-empty-namespace",
        "THE SAME DEFECT ONE LEVEL UP, AND THE WORSE ONE: it is silent about every record at once. "
        "A failed `list` yields no keys, no keys is what an empty namespace yields, and the sweep "
        "reports `SWEPT 0 records` and exits 0 - which the document reads as the finding that no "
        "submission has ever been made. A reading that never happened, published as a measurement.",
        REFUSED_LIST,
        '  raw=$(npx wrangler kv key list --namespace-id "$NS" </dev/null)'
        "  # MUTATION: status ignored",
    ),
    (
        "5-the-value-rendered-instead-of-read",
        "`jq -r` INSTEAD OF `jq -c`, which is the smallest edit in this file and looks like "
        "tidying. The delivery outcome stops being compared as a value and starts being compared "
        "as text, so a stored string \"false\" - which this endpoint never writes, and which is "
        "therefore a record written by something else - is reported as a measured `NOT NOTIFIED`. "
        "The operator would then write to an applicant about a notice that was never attempted.",
        READ_THE_VALUE,
        READ_THE_VALUE.replace("jq -c", "jq -r") + "  # MUTATION: rendered, not read",
    ),
    (
        "6-the-sentinel-reported-as-a-submission",
        "THE MARKER READ AS A FINDING. A `writeback-refused:` key carries no `delivered` field at "
        "all, so every filter over that field matches it: the branch that recognises it is left "
        "in place and stops matching, and the sweep reports the endpoint's own mark as an "
        "unconfirmed submission, doubles the count of people on the main path, and drops the "
        "store's reason for the refusal - the one field that says whether this is the documented "
        "429 or a finding.",
        "      writeback-refused:*) mark=1; marks=$((marks + 1)) ;;",
        "      writeback-refused-NEVER-MATCHES:*) mark=1; marks=$((marks + 1)) ;;  # MUTATION",
    ),
    (
        "7-every-sweep-reports-success",
        "THE EXIT STATUS FLATTENED. The document says this becomes a scheduled job the day a record "
        "is ever found this way, and a job whose instrument always returns 0 is the shape of every "
        "silence in this repository. The `return 2` paths are untouched, so what dies is precisely "
        "the difference between `nothing qualified` and `act on these`.",
        "  return $rc",
        "  return 0  # MUTATION: nothing qualified and act-on-these are one status",
    ),
    (
        "8-a-quiet-day-prints-nothing",
        "THE COUNT REMOVED, which is the version of this sweep that looks cleanest: findings only, "
        "no chatter. It cannot then say `I read eleven records and none of them qualified`, so a "
        "quiet day is an empty terminal - indistinguishable from a sweep that listed nothing, and "
        "from one the operator never ran. The zero that has to name which zero it is.",
        COUNT,
        '  : "MUTATION: the sweep prints findings only"',
    ),
    # --- 9 to 13: the five Fable produced against the first draft of this gate, every one of them
    # GREEN when applied. Each is a value or a sentence the operator acts on.
    (
        "9-the-zero-that-does-not-say-which-zero",
        "THE SWEEP'S STRONGEST SENTENCE, PRINTED OVER THREE DIFFERENT ZEROS. `no submission has "
        "ever been made` is a claim about the endpoint's whole history, and guarding it on the "
        "count of READABLE records means a namespace holding one submission the store refused to "
        "hand over prints it - directly underneath the `UNREADABLE` line naming that key - and so "
        "does a namespace holding a refusal mark, which is written only after a submission was "
        "stored. GREEN against the first draft of this gate: the fixture that elicits it was "
        "already in the suite and no assertion looked at the line.",
        ZERO_LINE,
        '  [ "$records" -eq 0 ] &&\n'
        '    echo "Zero keys is a reading of its own: no submission has ever been made."'
        "  # MUTATION: readable records only",
    ),
    (
        "10-the-read-goes-to-another-namespace",
        "THE `get` POINTED ELSEWHERE while the `list` stays correct - which is the half a control "
        "over one call cannot see. In production every value would come back missing and the whole "
        "namespace would print as UNREADABLE; the point is that the gate said it covered this and "
        "covered it for the `list` only. GREEN against the first draft, which ran its namespace "
        "control over an EMPTY namespace, where no `get` is issued at all.",
        '    if ! v=$(npx wrangler kv key get "$k" --namespace-id "$NS" </dev/null); then',
        '    if ! v=$(npx wrangler kv key get "$k" --namespace-id 0 </dev/null); then  # MUTATION',
    ),
    (
        "11-a-counter-that-reads-a-false-zero",
        "`notified` STOPS BEING COUNTED, so a day with three notified records reports `notified 0` "
        "under a count line whose other numbers are right. Invariant 1's literal subject - a "
        "counter that can read zero - inside the summary written to satisfy it. GREEN against the "
        "first draft, where `notified` was only ever exercised in runs whose true value was zero.",
        "      true)  notified=$((notified + 1)) ;;",
        "      true)  : ;;  # MUTATION: notified is no longer counted",
    ),
    (
        "12-an-unreadable-mark-read-as-a-healthy-one",
        "THE SENTINEL'S PARSE, UNCHECKED. `jq` writes its errors to stderr, so a mark whose stored "
        "value cannot be read prints under `SURVIVED TO ANSWER` with an empty summary after it - "
        "and the emptiness is invisible to anything capturing stdout, which is what the scheduled "
        "job this document anticipates would do. The operator reads a mark as saying its applicant "
        "survived to be answered, off a value that said nothing. GREEN against the first draft.",
        MARK_READ,
        "      m=$(jq -c '{of, notice_delivered, reason}' <<<\"$v\" 2>/dev/null)"
        "  # MUTATION: parse unchecked\n"
        '      echo "SURVIVED TO ANSWER: $k $m"',
    ),
    (
        "13-the-marks-are-not-counted",
        "THE SAME FALSE ZERO ON THE OTHER COUNTER: `refusal marks 0` printed directly beneath a "
        "`SURVIVED TO ANSWER` line. It also breaks the accounting the count line rests on - "
        "records plus marks is every key that was listed - so the namespace reported is smaller "
        "than the one that was swept. GREEN against the first draft.",
        "      writeback-refused:*) mark=1; marks=$((marks + 1)) ;;",
        "      writeback-refused:*) mark=1 ;;  # MUTATION: marks are no longer counted",
    ),
    # --- 14 to 19: the six Fable produced against the SECOND draft, every one of them green.
    (
        "14-two-counters-transposed-in-the-summary",
        "RED-013'S TRANSPOSITION, IN THE LINE THE OPERATOR READS. `notified` and `not_notified` "
        "swap places in the summary, so a day with four notified records and three unseen ones "
        "reports the reverse - and the operator writes to four people who were already told and "
        "leaves three who were not. Green until the fixture stopped giving every bucket the count "
        "1: four counters holding the same number print the same line under every permutation of "
        "themselves, which is a count that cannot be wrong because it cannot be read.",
        COUNT,
        COUNT.replace("notified $notified,", "notified $not_notified,")
             .replace("NOT NOTIFIED $not_notified,", "NOT NOTIFIED $notified,")
        + "  # MUTATION: transposed",
    ),
    (
        "15-a-submission-nobody-was-told-about-is-a-clean-run",
        "THE FINDING PRINTED AND THE STATUS SAYING OTHERWISE. `rc` stops rising on the "
        "`NOT NOTIFIED` branch, so a namespace whose only submission never reached the operator "
        "exits 0 - `nothing qualified`, to the scheduled job the document anticipates. Green "
        "because the exit-status test reached `rc` through a `NO OUTCOME` alone: one variable, "
        "four branches that set it, one of them ever exercised.",
        NOT_NOTIFIED,
        '      false) echo "NOT NOTIFIED: $k - stored, and the notice did not go out."\n'
        "             not_notified=$((not_notified + 1)) ;;  # MUTATION: no longer a finding",
    ),
    (
        "16-a-record-that-could-not-be-read-is-a-clean-run",
        "THE SAME BRANCH ONE STATE OVER: a record whose value came back unreadable is printed and "
        "the run still exits 0. The worse half of mutation 15, because what went unmeasured here "
        "is not a delivery outcome but the record itself.",
        UNREADABLE_VALUE,
        '      *)     echo "UNREADABLE: $k - no readable delivery outcome (got: $d)."\n'
        "             unreadable=$((unreadable + 1)) ;;  # MUTATION: no longer a finding",
    ),
    (
        "17-the-unreadable-records-are-not-counted",
        "THE THIRD FALSE ZERO, and the one that reads worst: `UNREADABLE 0` printed directly "
        "beneath an `UNREADABLE:` line. The number that says how much of the namespace went "
        "unmeasured, reporting that all of it was. Green because that counter was only ever "
        "exercised through the refused-READ branch beside it.",
        UNREADABLE_VALUE,
        '      *)     echo "UNREADABLE: $k - no readable delivery outcome in the record (got: $d)."\n'
        "             rc=1 ;;  # MUTATION: the unreadable records stop being counted",
    ),
    (
        "18-a-mark-carrying-nothing-read-as-a-mark",
        "THE REPAIR FOR MUTATION 12, NARROWED TO THE INPUT ITS OWN TEST USED. Checking that `jq` "
        "did not FAIL is not checking that a mark was read: `{of, notice_delivered, reason}` over "
        "a stored `null` or `{}` builds an object of three nulls and succeeds, and jq 1.6 exits 0 "
        "on an empty value having printed nothing at all. Each prints `SURVIVED TO ANSWER` with a "
        "hollow summary - mutation 12's exact symptom, surviving its own fix. Green.",
        MARK_OPEN,
        "      if ! m=$(jq -ce '{of, notice_delivered, reason}' <<<\"$v\" 2>/dev/null); then"
        "  # MUTATION: failure checked, emptiness not",
    ),
    (
        "19-a-notice-that-did-not-go-out-read-as-no-notice-at-all",
        "THE OTHER DIRECTION OF THAT CHECK, which is why it asks `has()` and not for a value. A "
        "mark carrying `notice_delivered: false` is the one the operator most needs read out - the "
        "applicant was answered and nobody was told - and a truthiness test files it under "
        "UNREADABLE, where the reason nobody was told is no longer printed at all.",
        'has("notice_delivered")',
        "(.notice_delivered == true)  # MUTATION: a measured false reads as absent",
    ),
    # --- 20 to 22: the third round, against the repairs for the second. All three green.
    (
        "20-a-finding-filed-under-the-status-that-means-it-did-not-run",
        "NOT A DROPPED STATUS BUT A MISFILED ONE, which is why mutations 15 and 16 did not arm it. "
        "A refused read sets `rc=2` - the status reserved for a sweep that never ran - so the "
        "scheduled job the document anticipates is told `did not run` about a sweep that ran, "
        "printed its count and found an unreadable key, and the operator loses the one distinction "
        "the three statuses exist for. Green because the refused-read test asserted `!= 0`.",
        '      unreadable=$((unreadable + 1)); rc=1; continue',
        "      unreadable=$((unreadable + 1)); rc=2; continue  # MUTATION: misfiled, not dropped",
    ),
    (
        "21-a-mark-that-names-no-record-is-read-as-one-that-does",
        "THE FIRST OF THE THREE REQUIRED FIELDS, DROPPED FROM THE CHECK. `of` is the whole of the "
        "pairing the follow-up runs on, and without it a mark prints `SURVIVED TO ANSWER` carrying "
        "`\"of\": null` - a mark beside a record it does not claim to be about. Green: the "
        "missing-field case in the suite omitted `reason` only, so the fix for mutation 18 was "
        "itself narrowed to the input its own new test used, which is what mutation 18 was about.",
        'has("of") and ',
        "  # MUTATION: `of` no longer required\n                          ",
    ),
    (
        "22-a-mark-that-carries-no-delivery-outcome-is-read-as-a-complete-one",
        "THE SECOND OF THE THREE, and the field the mark exists to carry. Without it the pairing "
        "says the endpoint survived to answer and cannot say what the applicant was told - the "
        "state the sentinel was introduced to end. Green for the same reason as mutation 21: one "
        "missing-field fixture cannot arm a conjunction of three.",
        'and has("notice_delivered")',
        "  # MUTATION: the delivery outcome is no longer required",
    ),
]

HEADER = """# RED-018 - a sweep that finds the record and cannot say what it found
#
# Produced by evidence/RED-018-generator.py, checked in beside this file so the runs below can be
# repeated rather than believed (L-26). It establishes that the gate landing with T-A2-3 CAN fail
# in each of the twenty-two directions it holds. FOURTEEN OF THE TWENTY-TWO WERE GREEN when Fable
# applied them, over three rounds against three drafts of the gate, and that is the honest summary
# of this file: each round refuted the repairs made for the one before it.
#
# Round one, mutations 9 to 13: the sweep's own `no submission has ever been made` sentence printed
# over a namespace it had failed to read; the `get` pointed at another namespace while the `list`
# stayed right; two counters silently reading zero; an unparseable refusal mark printed as a healthy
# one.
#
# Round two, mutations 14 to 19: two counters transposed in the summary line, invisible while the
# fixture written to catch a DROPPED counter gave every bucket the count 1; two branches printing a
# finding and reporting it in a clean exit status, because `rc` is one variable set in four places
# and one of them was ever reached; a third counter reading a false zero; the repair for the
# unreadable mark narrowed to the one input its own new test used, so a mark storing `null`, `{}` or
# nothing at all still printed as a mark that had been read; and a mark's measured
# `notice_delivered: false` read as an absent field by a truthiness test.
#
# Round three, mutations 20 to 22: a finding filed under the exit status that means the sweep did
# NOT run - a misfiled `rc` rather than a dropped one, which the round-two repairs did not arm; and
# two of the sentinel's three required fields left unchecked, because the missing-field fixture
# omitted the third alone. The same narrowing as round two, inside the fix for it.
#
# Each is a number, a sentence or a status the operator acts on, and each passed a suite that
# already RAN the sweep. A gate that runs the code is still a gate about the shapes it runs.
#
# THE SUBJECT IS A FENCED BLOCK IN A DOCUMENT. `docs/INTAKE_OPERATIONS.md` carries the KV sweep the
# operator runs by hand - the only instrument that finds a submission nobody has followed up - and
# a document does not fail a build. That block had been edited twice with nothing behind either
# edit: once to match `delivered == null` as well as `false`, and once to print them, and the
# second edit printed both under one word. So the gate EXTRACTS the block and RUNS it against a
# stubbed namespace (tests/kv_stub.py, put on PATH under the name `npx`), and these mutations are
# applied to the document itself, because the document is the source under test.
#
# WHAT EACH MUTATION IS, in the order they appear below: 1-2, the filter that skips the state both
# of T-A2-2's failures land in, and one label over the two states that are followed up differently;
# 3-4, a refused read classified as a malformed record, and a refused `list` swept as an empty
# namespace; 5, the delivery outcome rendered as text so a stored string reads as a measured
# boolean; 6, the endpoint's own sentinel reported as an unconfirmed submission; 7-8, the exit
# status flattened to 0, and the count removed so that a quiet day and a sweep that read nothing are
# the same empty terminal; 9, `no submission has ever been made` guarded on readable records alone,
# so it prints over a namespace that refused to be read; 10, the `get` pointed at another namespace
# while the `list` stays right; 11, 13 and 17, three counters that stop counting and report zero;
# 12 and 18, a refusal mark printed as one that had been read - first unparseable, then storing
# `null`, `{}` or nothing at all; 14, two counters transposed in the summary; 15, 16 and 20, a
# finding printed and then reported in a clean exit status, twice by a dropped `rc` and once by an
# `rc` filed under the status that means the sweep did not run; 19, a mark's measured
# `notice_delivered: false` read as an absent field; and 21-22, the sentinel's `of` and
# `notice_delivered` dropped from the three fields the check requires.
#
# WHAT THE GENERATOR REFUSES TO WRITE THIS FILE OVER:
#
#   * a mutation that does not go red, or whose marker does not appear in the document afterwards;
#   * a pytest that did not RUN - only exit 1 is a suite that ran and failed;
#   * a mutation that kills the INSTRUMENT CONTROL - the test asserting the sweep still called the
#     store, once per listed key. A block that stopped reaching KV would fail most of the suite and
#     establish nothing about what it prints. The namespace test was in that list until mutation 10
#     was written: it is the property that mutation removes, and a test cannot be both the control
#     for a mutation and the thing the mutation is about;
#   * two mutations with the same failure set;
#   * a document not restored byte for byte, or not green afterwards.
#
# The diff blocks are printed from the same strings that perform the edits, so the prose and the
# edit cannot disagree.
#
# Everything below each `$` line is verbatim output of the command shown.
#
"""

BAR = "# " + "=" * 92


def pytest_run() -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "pytest", SUITE, "-q"],
                          cwd=ROOT, capture_output=True, text=True)


def main(argv: list[str]) -> int:
    pristine = SRC.read_text(encoding="utf-8")
    _title, _rest = HEADER.split("\n", 1)
    stamped_header = f"{_title}\n# {evidence_stamp.tree_stamp()}\n{_rest}"
    out, seen = [stamped_header], {}
    try:
        for n, (name, prose, old, new) in enumerate(MUTATIONS, start=1):
            if pristine.count(old) != 1:
                raise SystemExit(f"{name}: anchor found {pristine.count(old)} times in {SRC.name}")
            SRC.write_text(pristine.replace(old, new), encoding="utf-8")
            grep = subprocess.run(["grep", "-n", "MUTATION", str(SRC)],
                                  capture_output=True, text=True)
            run = pytest_run()
            SRC.write_text(pristine, encoding="utf-8")
            if SRC.read_text(encoding="utf-8") != pristine:
                raise SystemExit(f"{name}: the document was NOT restored; stopping")

            if not grep.stdout.strip():
                raise SystemExit(f"{name}: no MUTATION marker in the document - the edit did not "
                                 "land, so the run below is a transcript of the pristine sweep")
            if run.returncode == 0:
                raise SystemExit(f"{name} did NOT go red: the gate is unarmed against it")
            if run.returncode != 1:
                raise SystemExit(
                    f"{name}: pytest exited {run.returncode}, which is not a suite that ran and "
                    "failed. A red must be an assertion, never an instrument that did not run")
            for control in CONTROLS:
                if control in run.stdout:
                    raise SystemExit(
                        f"{name} killed an instrument control ({control}): the sweep stopped "
                        "reaching the store, so this red is about a broken block and not about "
                        "what it prints")
            failed = tuple(sorted(ln for ln in run.stdout.splitlines() if ln.startswith("FAILED ")))
            if failed in seen:
                raise SystemExit(f"{name} and {seen[failed]} produce the SAME failure set")
            seen[failed] = name

            diff = "\n".join(f"# - {ln}" for ln in old.split("\n"))
            diff += "\n" + "\n".join(f"# + {ln}" for ln in new.split("\n"))
            out.append(
                f"{BAR}\n# RED {n}.\n# {prose}\n#\n{diff}\n#\n"
                "# $ grep -n 'MUTATION' docs/INTAKE_OPERATIONS.md\n"
                + "".join(f"# {ln}\n" for ln in grep.stdout.splitlines())
                + f"#\n# $ python3 -m pytest {SUITE} -q\n" + run.stdout + run.stderr + "\n")
    finally:
        SRC.write_text(pristine, encoding="utf-8")

    green = pytest_run()
    if green.returncode != 0:
        raise SystemExit("the restored document is not green; the reds above prove nothing")
    out.append(f"{BAR}\n# GREEN, on the restored document, so the reds above are known to be the "
               "mutations' doing\n# and not a suite that fails on everything.\n#\n"
               f"# $ python3 -m pytest {SUITE} -q\n" + green.stdout + green.stderr)

    if "--check" in argv:
        print(f"{len(MUTATIONS)} mutations, all red, all distinct; nothing written")
        return 0
    tmp = ARTEFACT.with_suffix(".txt.new")
    tmp.write_text("".join(out), encoding="utf-8")
    tmp.replace(ARTEFACT)
    print(f"{ARTEFACT.relative_to(ROOT)}: {len(MUTATIONS)} mutations, all red, all distinct")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
