"""T-F3 - re-issue is an obligation, and missing it is a finding (LAW-REISSUE-OR-FINDING).

THIS SUITE DOES NOT SKIP, AND THE REASON IS L-16. The four note suites opened with
`skipif(not sources())` and were counted among the armed while every assertion in them skipped in
the exact state that shipped a defect. The state this one has to speak in is the state where the
cohort has NOT been re-run - the empty case is the case that ships - so there is no condition under
which it stands down. `web/public/data/registry.json` is tracked, so it reaches every clone.

`test_the_incubator_is_meeting_its_own_reissue_obligation` is a TIME BOMB and that is deliberate. It
goes red with no commit and no event when nobody has re-run the cohort within the interval - which
is what "silence becomes a finding" has to mean if it means anything. The way past it is to perform
the obligation; there is no other, and `--no-verify` is forbidden.

A time bomb still needs something to run it, and the first draft of this file did not check that
anything would. Every trigger in `.github/workflows/gates.yml` required a person to push first, so
in the exact state the obligation exists for - nobody acts - the suite would not have run at all.
The daily `schedule:` there is the clock, and `test_the_gate_has_a_clock_and_not_only_a_door` is
what keeps it.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.liveness import commitments as C
from src.liveness.obligations import (
    MAX_AGE,
    PASSPORT_VALIDITY,
    RENEWAL_MARGIN,
    Interval,
    Obligation,
    Registry,
)

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 8, 20, 12, tzinfo=timezone.utc)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _block(lines: list[str], start: int):
    """Indices of the lines nested under `lines[start]`, stopping at the first dedent."""
    base = _indent(lines[start])
    for i in range(start + 1, len(lines)):
        if not lines[i].strip():
            continue
        if _indent(lines[i]) <= base:
            return
        yield i


def _items(lines: list[str], start: int):
    """Indices of the sequence items belonging to the key at `lines[start]`.

    Separate from `_block` because a YAML sequence may sit at ITS KEY'S OWN INDENT - which is
    standard, is what yamllint's default style emits, and is what GitHub's own examples show.
    `_block` stops at the first line indented no further than the key, so it never saw those.
    """
    base = _indent(lines[start])
    for i in range(start + 1, len(lines)):
        if not lines[i].strip():
            continue
        if lines[i].strip().startswith("-") and _indent(lines[i]) >= base:
            yield i
        elif _indent(lines[i]) <= base:
            return


def _has_cron(workflow: str) -> bool:
    """Is there a LIVE `cron:` under a `schedule:` under the workflow's top-level `on:`?

    THE NESTING IS THE POINT, and two independent regexes were what this replaced. That version
    passed a `schedule:` mis-indented to the top level, a `schedule:` under a job, and an empty
    `schedule:` with a cron string somewhere else in the file - three dead triggers - while failing
    an unquoted cron, a `schedule:` with a trailing comment, and flow style, which are three live
    ones. False greens on the defect and false reds on valid YAML, in the check written to prove a
    clock exists. Found by Fable.

    PyYAML is the obvious tool and is deliberately not used: the CI `tests` job installs only
    pytest and pytest-cov, so importing it would make this check fail in the one place it most
    needs to run. The repository already hand-parses its own YAML for the same reason
    (`scripts/ratchet_scope.py`).

    LIMITS, NAMED RATHER THAN LEFT TO BE FOUND. Comments are stripped without respect for quoting,
    which is safe for cron expressions and would not be for a value containing `#`. An aliased
    schedule (`schedule: *defaults`) reads as absent, because this cannot follow an anchor and
    guessing would be a false green. And the honest one: `LIVE_CLOCKS` and `DEAD_CLOCKS` below are
    ENUMERATED FROM CASES SOMEBODY REPORTED, so they are evidence that those shapes are handled and
    not a proof that the parser is correct on YAML in general. Three drafts of this helper each had
    a control table that stopped at the previous round's findings; saying so is the only thing that
    ends that, because a fourth table cannot.
    """
    lines = [ln.split("#", 1)[0].rstrip() for ln in workflow.splitlines()]
    for i, line in enumerate(lines):
        key, _, inline = line.partition(":")
        if _indent(line) or key.strip().strip("\"'") != "on":
            continue
        if "schedule" in inline and "cron:" in inline:   # on: {schedule: [{cron: "..."}]}
            return True
        for j in _block(lines, i):
            head, _, sched_inline = lines[j].strip().partition(":")
            if head.strip("\"'") != "schedule":
                continue
            if "cron:" in sched_inline:                  # schedule: [{cron: "..."}]
                return True
            for k in _items(lines, j):                   # - cron: "..."
                item = lines[k].strip().lstrip("-").strip()
                item_key, _, value = item.partition(":")
                if item_key.strip("\"'") == "cron" and value.strip().strip("\"'"):
                    return True
    return False


def _run(*, ran_days_ago: float, lapses_in_days: float = 30.0, rows: int = 8) -> C.CohortRun:
    generated_at = NOW - timedelta(days=ran_days_ago)
    return C.CohortRun(C.ReadState.READ, generated_at=generated_at,
                       earliest_valid_until=generated_at + timedelta(days=lapses_in_days),
                       rows=rows)


# --- the obligation exists at all -------------------------------------------------------------

def test_the_registry_is_not_empty_which_is_the_state_this_task_found():
    """An empty registry is suspicious by `Registry.sweep`'s own rule, and it WAS the real state.

    The control is the bare `Registry()`: until T-F3 that is what the project had, and the second
    assertion is what the first one would have read like for the whole of T-2.10's life.
    """
    assert "EMPTY OBLIGATION REGISTRY" in Registry().sweep(NOW)[0]
    assert C.declare(_run(ran_days_ago=0)).sweep(NOW) == []


def test_the_obligation_names_a_consumer_so_it_is_not_the_fifth_sleep_state():
    reg = C.declare(_run(ran_days_ago=0))
    assert "NO CONSUMER" not in " ".join(reg.sweep(NOW))
    assert C.CONSUMER.startswith("web/src/App.tsx")


# --- a missed interval produces a NAMED finding ------------------------------------------------

def test_a_missed_interval_is_a_named_finding_with_a_remedy():
    late = MAX_AGE[Interval.BEFORE_REISSUE].days + 1
    out = C.findings(_run(ran_days_ago=late, lapses_in_days=30 + late), NOW)
    assert out, "the interval elapsed and nothing was reported"
    joined = " ".join(out)
    assert "SILENCE" in joined and C.COMPONENT in joined
    assert "scripts/cohort.py" in joined, "a finding whose reader must work out the remedy waits"


def test_a_run_inside_the_interval_reports_nothing():
    assert C.findings(_run(ran_days_ago=MAX_AGE[Interval.BEFORE_REISSUE].days - 1), NOW) == []


def test_the_interval_is_derived_from_the_two_constants_and_not_a_literal():
    """Algebra, and named as algebra.

    It can only fail if someone replaces the subtraction in `MAX_AGE` with a number, which is the
    edit that would silently detach the interval from the margin. The claim about the WORLD - that
    the rows this repository actually ships leave room for the margin - is
    `test_the_real_deadline_lands_before_the_real_lapse`, and it is a different test on purpose.
    """
    assert MAX_AGE[Interval.BEFORE_REISSUE] + RENEWAL_MARGIN <= PASSPORT_VALIDITY
    assert RENEWAL_MARGIN > timedelta(0)


def test_a_shortened_validity_window_is_caught_rather_than_silently_missed():
    """`PASSPORT_VALIDITY` is a copy of the passport's number; this is what keeps the copy honest."""
    out = C.findings(_run(ran_days_ago=0, lapses_in_days=10), NOW)
    assert any("DEADLINE TOO LATE TO ACT ON" in f for f in out), out


def test_performing_the_obligation_does_not_accuse_the_operator_of_a_two_second_drift():
    """The gate must not go red on the day the habit is obeyed.

    `scripts/cohort.py` stamps `generated_at` and `valid_until` from one module-level `now`, so the
    published window is exactly thirty days to the microsecond. Nothing pins that: a refactor taking
    the clock twice moves it by seconds in either direction, and without `POLICY_TOLERANCE` the
    negative direction fired `DEADLINE TOO LATE TO ACT ON` - a false red, at the moment the operator
    had just done the right thing. Both directions are checked because only one of them was a bug.
    """
    for skew in (timedelta(seconds=-2), timedelta(0), timedelta(seconds=2)):
        window = PASSPORT_VALIDITY + skew
        run = C.CohortRun(C.ReadState.READ, generated_at=NOW,
                          earliest_valid_until=NOW + window, rows=8)
        assert C.findings(run, NOW) == [], f"false red at a skew of {skew}"


def test_the_tolerance_is_slack_and_not_a_hole():
    """The smallest real change to a policy stated in whole days must still be caught.

    A one-day shortening — `validity_days` 30 to 29 — is the likeliest drift there is, and the
    first tolerance was itself a day wide, so it passed silently. It also passed the suite,
    because the assertion that had caught it was a duplicate implementation removed in the same
    round for being a duplicate. Two fixes cancelling each other out, both found by Fable.
    """
    assert C.POLICY_TOLERANCE < timedelta(days=1), "a day of slack hides a one-day drift"
    one_day_shorter = C.CohortRun(C.ReadState.READ, generated_at=NOW,
                                  earliest_valid_until=NOW + PASSPORT_VALIDITY - timedelta(days=1),
                                  rows=8)
    assert any("DEADLINE TOO LATE TO ACT ON" in f for f in C.findings(one_day_shorter, NOW))


# --- absence keeps its own name (invariant 1) --------------------------------------------------

def test_an_absent_registry_is_not_reported_as_a_missed_run(tmp_path: Path):
    """Both halves matter, and the second half is the one the first draft got wrong.

    Reporting NOT MEASURED is not enough while the line beside it still says the component "has
    never presented evidence of participation ... This is a FINDING, not missing data" - that is
    the conclusion an unreadable instrument may not draw, printed next to the admission that it
    could not read. `Obligation.evidence_unreadable` is the third state that separates them.
    """
    out = C.sweep(NOW, root=tmp_path)
    assert any(f.startswith("NOT MEASURED") for f in out), out
    assert any(C.ReadState.FILE_ABSENT.value in f for f in out), out
    assert any(f.startswith("NOT ASSESSED") for f in out), out
    assert not any("has never presented evidence" in f for f in out), out


def test_an_unreadable_registry_is_not_reported_as_a_missed_run(tmp_path: Path):
    p = tmp_path / C.SHIPPED
    p.parent.mkdir(parents=True)
    p.write_text("{not json", encoding="utf-8")
    out = C.sweep(NOW, root=tmp_path)
    assert any(C.ReadState.NOT_JSON.value in f for f in out), out
    assert not any("SILENCE" in f for f in out), out


def test_a_timestamp_that_was_read_is_not_thrown_away_because_the_rest_was_not():
    """`NO_SUBJECTS_FIELD` carries a `generated_at` that parsed. Reporting UNKNOWN over a quantity
    the instrument is holding is the same defect as reporting a zero for it - and it silently
    dropped the remedy too, because the remedy rides on SILENCE. Found by Fable."""
    stale = C.CohortRun(C.ReadState.NO_SUBJECTS_FIELD,
                        generated_at=NOW - timedelta(days=100))
    out = C.findings(stale, NOW)
    assert any(f.startswith("PARTIALLY READ") for f in out), out
    assert any("SILENCE" in f for f in out), out
    assert not any("NOT ASSESSED" in f for f in out), out
    assert any("scripts/cohort.py" in f for f in out), "the remedy went missing with the finding"


def test_a_shipped_copy_no_cohort_run_produced_is_a_finding():
    """The other direction of the same comparison, and the only forgery this gate can catch."""
    out = C.findings(_run(ran_days_ago=0), NOW, emitted=_run(ran_days_ago=90))
    assert any("SHIPPED AHEAD OF THE RUN" in f for f in out), out


def test_conditions_that_are_all_true_are_all_reported():
    """Three of these can hold at once, and a single return value made them race.

    The race was found twice, once in each direction: first SILENCE hid a missing consumer, then
    the fix made a missing consumer hide a four-hundred-day outage. Neither ordering is right - a
    string nobody filled in must not silence a measured fact, and a measured fact must not silence
    a structural one. Both found by Fable, one round apart.
    """
    silent_and_unread = Obligation("prober", "execution record", Interval.BEFORE_REISSUE,
                                   last_seen=NOW - timedelta(days=400), consumer=None)
    out = silent_and_unread.findings(NOW)
    assert any("NO CONSUMER" in f for f in out), out
    assert any("SILENCE" in f for f in out), out


def test_the_fifth_state_is_not_masked_by_an_unreadable_instrument():
    """Whether a consumer was declared needs no evidence read, so a readability flag may not hide
    it. The first draft of `evidence_unreadable` short-circuited above the check. Found by Fable.

    The combination below is not producible by the only caller there is today - `declare()` derives
    the flag from `generated_at is None`, and it always passes a consumer. This guards the
    dataclass's contract for the next caller rather than a state on the ground, and says so instead
    of reading as though it had found one.
    """
    o = Obligation("c", "e", Interval.BEFORE_REISSUE, last_seen=NOW, consumer=None,
                   evidence_unreadable=True)
    out = o.findings(NOW)
    assert any("NO CONSUMER" in f for f in out), out
    assert any("NOT ASSESSED" in f for f in out), out


def test_never_run_and_could_not_look_are_different_findings():
    """The distinction at the level of the mechanism, where it was missing until T-F3."""
    never = Obligation("c", "e", Interval.BEFORE_REISSUE, last_seen=None,
                       consumer="x").findings(NOW)
    unread = Obligation("c", "e", Interval.BEFORE_REISSUE, last_seen=None, consumer="x",
                        evidence_unreadable=True).findings(NOW)
    assert never and unread and never != unread
    assert "never presented evidence" in never[0] and "IS UNKNOWN" in unread[0]


def test_a_read_file_listing_nothing_is_a_measured_zero_not_an_unread_file():
    empty = C.CohortRun(C.ReadState.READ, generated_at=NOW, earliest_valid_until=None, rows=0)
    out = C.findings(empty, NOW)
    assert any("EMPTY SHIPPED REGISTRY" in f for f in out), out
    assert not any(f.startswith("NOT MEASURED") for f in out), "the file WAS read"


def test_rows_without_a_readable_lapse_date_do_not_pass_as_clean():
    out = C.findings(C.CohortRun(C.ReadState.READ, generated_at=NOW, rows=8), NOW)
    assert any(f.startswith("NOT MEASURED") for f in out), out


# --- the run has to reach the artefact that ships (L-3) ----------------------------------------

def test_a_cohort_run_that_never_reached_the_build_copy_is_a_finding():
    shipped = _run(ran_days_ago=5)
    emitted = _run(ran_days_ago=0)
    out = C.findings(shipped, NOW, emitted=emitted)
    assert any("RUN NOT SHIPPED" in f for f in out), out


def test_a_comparison_that_could_not_run_does_not_report_the_same_nothing_as_a_clean_one():
    """Half the input missing produced zero findings, which reads identically to "in step"."""
    out = C.findings(_run(ran_days_ago=0), NOW, emitted=C.CohortRun(C.ReadState.NOT_JSON))
    assert any(f.startswith("NOT COMPARED") for f in out), out


def test_evidence_is_taken_from_the_copy_a_reader_receives():
    """Instrument control, and it has to reach past the constant to the consumer.

    Asserting that `SHIPPED` equals its own literal proves nothing: the L-3 claim in this module's
    docstring rests entirely on `web/src/App.tsx` fetching that path, and until this test that link
    lived only in a comment (L-7). Move the fetch and the gate would go on reading a file nobody
    ships, green throughout.
    """
    assert C.SHIPPED.as_posix() == "web/public/data/registry.json"
    assert (ROOT / C.SHIPPED).exists(), "the shipped copy must reach a clone or this gate is blind"

    # web/public is Vite's static root: what sits at web/public/data/x is served at /data/x.
    served_as = "/" + C.SHIPPED.relative_to("web/public").as_posix()
    app = (ROOT / "web" / "src" / "App.tsx").read_text(encoding="utf-8")
    assert f'fetch("{served_as}")' in app, (
        f"{C.CONSUMER} no longer fetches {served_as}, so the file this gate reads is not the one "
        "the reader receives and the L-3 claim in commitments.py is false")


# --- and the live reading, which is the whole point --------------------------------------------

def test_the_gate_has_a_clock_and_not_only_a_door():
    """An obligation about abandonment cannot be checked only when somebody shows up.

    This asserts the trigger exists in the workflow. It does NOT assert GitHub dispatched it -
    that is not observable from this host, and the first scheduled run in the Actions log is the
    evidence for it (L-10: the instrument has to be able to see the quantity).
    """
    wf = (ROOT / ".github" / "workflows" / "gates.yml").read_text(encoding="utf-8")
    assert _has_cron(wf), (
        "gates.yml runs only on push, pull_request and workflow_dispatch. Every one of those needs "
        "a person to act first, so the re-issue finding would never fire in the state it is for")


LIVE_CLOCKS = {
    "double quotes": 'on:\n  push:\n  schedule:\n    - cron: "17 7 * * *"\n',
    "single quotes": "on:\n  push:\n  schedule:\n    - cron: '17 7 * * *'\n",
    "unquoted": "on:\n  push:\n  schedule:\n    - cron: 17 7 * * *\n",
    "trailing comment": 'on:\n  schedule:   # daily\n    - cron: "17 7 * * *"\n',
    "flow sequence": 'on:\n  schedule: [{cron: "17 7 * * *"}]\n',
    "flow mapping": 'on: {push: null, schedule: [{cron: "17 7 * * *"}]}\n',
    "quoted on": '"on":\n  schedule:\n    - cron: "17 7 * * *"\n',
    "single-quoted on": "'on':\n  schedule:\n    - cron: '17 7 * * *'\n",
    "sequence at the key's indent": 'on:\n  schedule:\n  - cron: "17 7 * * *"\n',
    "sequence at the key's indent, unquoted": "on:\n  schedule:\n  - cron: 17 7 * * *\n",
    "with a jobs sibling": 'on:\n  schedule:\n    - cron: "17 7 * * *"\njobs:\n  a:\n    steps: []\n',
}

DEAD_CLOCKS = {
    "commented out": 'on:\n  push:\n  # schedule:\n  #   - cron: "17 7 * * *"\n',
    "not under on": 'on:\n  push:\n\nschedule:\n  - cron: "17 7 * * *"\n',
    "under a job": 'on:\n  push:\njobs:\n  a:\n    schedule:\n      - cron: "17 7 * * *"\n',
    "empty schedule": 'on:\n  push:\n  schedule:\njobs:\n  a:\n    name: "cron: 17 7 * * *"\n',
    "no schedule at all": "on:\n  push:\n  pull_request:\n  workflow_dispatch:\n",
    "aliased schedule": "on:\n  push:\n  schedule: *cron_defaults\n",
}


def test_the_clock_check_is_able_to_fail():
    """Instrument control, and it has been wrong twice - each time fitted to the last finding.

    Draft one asked `"schedule:" in wf and "cron:" in wf`, which a commented-out trigger satisfies
    as well as a live one - `present` reported as `armed`, L-16 inside the gate written to close
    L-19. Draft two anchored two regexes to line starts and had its control exercise exactly the
    one disarm shape that had been reported. Draft three parsed properly and its table listed
    exactly the six shapes reported against draft two - and missed a sequence sitting at its key's
    own indent, which is standard YAML and what yamllint emits. Three rounds, one pattern: a
    control whose beneficiary is yesterday's finding rather than the class of defect (L-13). All
    three found by Fable.

    So the table is a table, and it is a table with a stated limit rather than a fourth attempt at
    completeness: these are shapes somebody reported, they are evidence that these shapes are
    handled, and they are not a proof of coverage. Saying that is what ends the loop; another row
    would not.
    """
    for name, sample in LIVE_CLOCKS.items():
        assert _has_cron(sample), f"false red on a valid live trigger: {name}"
    for name, sample in DEAD_CLOCKS.items():
        assert not _has_cron(sample), f"false green on a dead trigger: {name}"


def test_the_incubator_is_meeting_its_own_reissue_obligation():
    """The one assertion here that is about the world rather than about the code.

    It reads the tree as it stands, at the real clock. When it fails, nothing is broken - the
    obligation is simply unmet, and the finding is the point rather than the accident.
    """
    out = C.sweep(datetime.now(timezone.utc))
    assert out == [], "\n".join(out)


def test_the_real_deadline_lands_before_the_real_lapse():
    """Not a synthetic case: the numbers the tree actually ships, on every run of this suite.

    Deliberately NOT written as "the rows lapse on 2026-09-19". That date is true today and stops
    being true the first time the obligation is met, so a test asserting it would fail on the act of
    performing the thing it guards - a rule whose last useful day is today (L-13).
    """
    run = C.read_run(ROOT / C.SHIPPED)
    assert run.state is C.ReadState.READ, run.state
    assert run.rows, "no rows ship, so nothing lapses and nothing is being re-issued"
    assert run.earliest_valid_until is not None

    # THROUGH `findings()`, NOT A SECOND COMPARISON OF THE SAME QUANTITIES.
    #
    # This assertion used to recompute the deadline here and compare instants strictly. When
    # `POLICY_TOLERANCE` was added to close a false red, the tolerance landed in `findings()` and
    # this copy kept the strict form - so the false red the new test certified as fixed still fired
    # from this line, in the same suite, at the door, on the day the operator performs the habit.
    # L-2 in its purest shape, committed inside the fix for a defect raised as L-2's shape. There
    # is now one implementation of the rule and this test calls it. Found by Fable.
    late = [f for f in C.findings(run, run.generated_at) if "DEADLINE TOO LATE" in f]
    assert late == [], late
