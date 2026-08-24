"""T-F4 - the door runs every gate the arbiter can fail on (LAW-DOOR-MATCHES-ARBITER).

`.github/workflows/gates.yml` opens with "THE SAME GATES AS scripts/push.sh". That sentence has
now been false twice. The first time cost four red runs on `main` (5-8, bedb764..9deafa6): CI ran
`ruff`, the door never had, so a commit satisfied every check a human sees before pushing and
failed one nobody runs until after. It was fixed by adding ruff to the door - which fixes the
INSTANCE and leaves the mechanism, because the thing that kept the drift invisible was the header
claiming the two lists were identical while nothing compared them. A rule written in more than one
place survives its own repeal (L-2), and here the two copies were a workflow and a shell script.

This file is the comparison. Every step in `gates.yml` that can turn `main` red must name a
counterpart at the door, or be listed as deliberately CI-only with a reason. Both directions are
checked, so a step added to CI and forgotten at the door is a red build, and so is a table row
describing a step that no longer exists.

WHAT THIS IS NOT. It compares a declared correspondence, not semantics: it can see that the door
runs `pytest` with `--cov-fail-under=70` because CI does, and it cannot see that the two run the
same tests against the same tree. The table below is the claim; these assertions keep the claim
from drifting away from the two files it describes. That is weaker than proving the gates are
equivalent and much stronger than a sentence in a header.

THE ADVISORY STEP IS THE OTHER HALF. `mypy` runs with its findings suppressed, so it cannot redden
`main` and therefore needs no counterpart at the door TODAY. The promise that it becomes blocking
"once a clean baseline exists" lived in `.github/workflows/README.md` with nothing measuring the
condition and nothing noticing if it were never met - L-7, a rule that lives only in prose, in the
document describing this project's gates. It is armed here instead: the advisory state carries an
expiry, this suite goes red on its own once that date passes, and when the step stops being
advisory the correspondence check above forces mypy through the door in the same commit.

PyYAML is not imported here, and THE REASON PRINTED HERE UNTIL 2026-08-24 HAS LAPSED. It read: the
CI `tests` job installs only pytest and pytest-cov, so importing it would break this check in one
of the two places it most needs to run. That job installs PyYAML as of D-32, which put it in
`requirements/ci-tests.in` so `tests/test_workflows_parse.py` could ask the real parser whether
GitHub can open these files at all - the gap `evidence/RED-031-*` measured. The sentence is
corrected rather than left standing: a stale reason is what makes an arrangement look decided when
it is merely inherited (L-2), and this file is the one that exists to catch two lists claiming to
be one.

What is NOT claimed is that hand-parsing here is now wrong. This file matches STEPS between two
documents and its reader is exercised by fixtures below; rewriting it onto a parser is a change
with its own failure modes and belongs to whoever takes it deliberately, not to the commit that
made it possible. It is recorded as a named deferral rather than done in passing.
`scripts/ratchet_scope.py` keeps the ORIGINAL reason intact and unaffected: the `ratchets` job
installs nothing at all, so a ratchet that imported PyYAML would not run there.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "gates.yml"
DOOR = ROOT / "scripts" / "push.sh"
WORKFLOW_README = ROOT / ".github" / "workflows" / "README.md"

# The date the advisory state expires. Written ONCE, here, and the assertions below require the two
# documents that state it to state this same value - the pattern `PASSPORT_VALIDITY` uses to keep a
# copied constant honest.
#
# WHY THIS DATE, since a number nobody can derive is the kind that quietly gets moved. It is 56 days
# from 2026-08-20, when the promise was armed, and the bound that chose it is L-19's: GitHub
# disables a public repository's `schedule:` after sixty days without repository activity, and that
# schedule is what runs this suite in the world where nobody pushes. A deadline set past the sixty
# would be unreachable by the clock in exactly the state it exists for - an expiry that expires
# only if somebody turns up to watch it.
ADVISORY_UNTIL = date(2026, 10, 15)

# The measured baseline on the day the promise was armed, kept so the next reader can tell a
# baseline that is nearly clean from one that is not: `mypy src --ignore-missing-imports` reported
# 28 errors across 7 files on 2026-08-20, almost all of them `None` flowing into a comparison or an
# attribute access. That is not an incidental backlog - it is invariant 1's own defect class, which
# is the argument for the expiry rather than an indefinite advisory.
BASELINE_2026_08_20 = (28, 7)

SENTINEL = "ADVISORY-UNTIL:"


class Door:
    """This CI step can fail the build, so the door must run it too.

    `must_appear` is matched against the EXECUTABLE lines of `scripts/push.sh` - see
    `executable_lines`, and the finding that made it necessary.
    """

    def __init__(self, must_appear: str) -> None:
        self.must_appear = must_appear


class Advisory:
    """This CI step cannot fail the build on its findings, and says until when."""

    def __init__(self, until: date) -> None:
        self.until = until


# THE CORRESPONDENCE. Keyed by the step's `name:` in gates.yml.
CI_GATES: dict[str, Door | Advisory] = {
    "scope - every module bound to an ABI requirement": Door("scripts/ratchet_scope.py"),
    "laws - no law without an armed gate and test": Door("scripts/ratchet_decisions.py"),
    "language - the GitHub surface is English only": Door("scripts/ratchet_language.py"),
    # The threshold, not merely the tool. The door ran a bare `pytest` while CI required 70%
    # coverage, so a commit could drop coverage and pass the door - the ruff defect exactly, still
    # open, found by writing this table out.
    "full suite, whole tree": Door("--cov-fail-under=70"),
    # Likewise. CI builds the site; the door never did, so the assertions that read `web/dist`
    # judged whatever build happened to be lying on this host, or skipped when there was none.
    # TWO JOBS NOW CARRY A STEP OF THIS NAME, and one row covers both because the door's single
    # build is the counterpart of each. The `tests` job grew one because
    # `tests/test_emitted_ids_are_unique.py` refuses to call an empty `web/dist` a clean sweep -
    # correctly, since zero pages and zero duplicates are the same green (invariant 1) - and that
    # job never built, so it read `check_did_not_run` and turned `main` red while the door stayed
    # green. `push.sh` builds at step 6 and runs the suite at step 7, so on this host the artefact
    # was simply lying there.
    #
    # That is this file's own blind spot, named rather than papered over: it compares which
    # COMMANDS each side runs, never the STATE each side runs them against. Both sides ran
    # `pytest`; only one of them ran it after a build. A correspondence of commands is not a
    # correspondence of trees - the header has always said so, and this is the first instance to
    # cost a red `main`.
    "build the site": Door("npm run build"),
    "gates that read the emitted artefact": Door("-m pytest"),
    "ruff": Door("-m ruff"),
    "mypy": Advisory(until=ADVISORY_UNTIL),
    "repository secret scan": Door("scripts/secret_scan.sh"),
}

# Steps that prepare the runner rather than judge the tree. A step whose command IS one of these is
# not a gate; anything else without a table row is a finding.
#
# The whole line must be preparation. This read `first.startswith(...)`, and Fable broke it with
# `pip install bandit && bandit -r src --strict` - a real gate chained behind a real setup command,
# classified as runner preparation and reported as no divergence at all. A prefix test on a line
# that can hold a second command answers a question about the prefix, not about the step.
#
# COMMAND SUBSTITUTION IS A CHAIN TOO. `pip install --quiet $(python scripts/choose_gate.py)` holds
# no `&&`, satisfies every prefix, and runs an arbitrary script whose failure fails the step under
# GitHub's `bash -e`. A predicate that reasons about `&&` is reasoning about tokens; what matters is
# whether a second program can execute on that line. Found by Fable.
SETUP_PREFIXES = ("pip install", "pip3 install", "npm ci", "apt-get")
CHAINS = ("&&", "||", ";", "|", "$(", "`", "<(", ">(", "\n")

# Actions that configure the runner. Anything else arriving as `uses:` is a third-party gate that
# can fail the build - which is how most of them ship - and needs a row like any other.
BENIGN_ACTIONS = ("actions/checkout", "actions/setup-python", "actions/setup-node")


# EVERY WORKFLOW THAT CAN REDDEN `main`, DECLARED - because this file reads exactly one of them.
#
# The law was first written "no check can fail on main that the door did not run", and the checker
# it names reads `gates.yml` alone. Two other workflows trigger on push to main, so the law's text
# was broader than its gate the day it was ratified - the header-outlives-its-list shape this task
# was opened about, in the law closing it. Found by Fable.
#
# The honest scope is narrower and is now what the law says: OUR suite is mirrored at the door;
# third-party analyses are not, because the door cannot run them and pretending otherwise would be
# the same defect again. What this table buys is that a FOURTH workflow cannot appear unnoticed -
# the README's "three workflows" was prose that nothing counted.
DECLARED_WORKFLOWS = {
    "gates.yml": "ours: every step is compared against the door, above",
    "codeql.yml": "third-party analysis. It can fail on main and the door does NOT run it - CodeQL "
                  "is not installable here, and its findings go to the Security tab by design.",
    "scorecard.yml": "third-party analysis, same reasoning. Its own header records a run that died "
                     "in setup on an unresolvable ref - a red on main the door cannot see.",
}


def executable_lines(door: str) -> str:
    """`scripts/push.sh` with its comments removed.

    THE MOST DANGEROUS FALSE GREEN THIS FILE HAD, and it was introduced by writing the file. The
    match was a raw substring test against the whole script, and `push.sh` now carries long comments
    naming `npm run build`, `--cov-fail-under=70` and `mypy` - so commenting OUT steps 5, 6 and 7
    left a door that runs no lint, no build, no tests and no coverage floor, and this comparison
    still returned no divergences. Commenting a step out is exactly how one gets disabled "just for
    a moment", and the prose explaining why the step matters is what would have kept vouching for
    it. A gate that reads its own documentation as evidence of compliance is the whole subject of
    this repository, committed inside the check written to end it. Found by Fable.

    STRING LITERALS GO TOO, and that is the same finding one context over. Stripping only `#`
    comments left `echo "5/7 lint skipped today: -m ruff is broken"` vouching for a step it
    announces the absence of - a door running no lint, reported as matching CI, because the excuse
    contained the string being matched. Disabling a step with a printed excuse is at least as
    ordinary as commenting it out. Quoted text is a message to a human, never a command, so it is
    removed before matching. Found by Fable, in the commit that claimed the comment case was fixed.

    Removing quotes FIRST also retires the `#`-inside-a-string truncation this docstring used to
    concede: `echo "step #5"; python3 -m ruff check` keeps its ruff, because the `#` leaves with the
    string that contained it. What remains unhandled is an escaped or nested quote, which can only
    hide text from the match - a false red, the safe direction, and the one deliberately kept.
    """
    out = []
    for raw in door.splitlines():
        if raw.strip().startswith("#"):
            continue
        line = re.sub(r"'[^']*'|\"[^\"]*\"", " ", raw)
        out.append(line.split("#", 1)[0])
    return "\n".join(out)


def _is_pure_setup(run: str) -> bool:
    """Every line of this step's body is runner preparation and nothing else.

    A step with no `name:` cannot be matched to a row, so it is waved through as setup. That makes
    this predicate the hole an unnamed gate would enter by, and it has to hold on two counts: EVERY
    line must be preparation, not just the first, and no line may chain a second command onto one.
    `pip install bandit && bandit -r src --strict` satisfies a `startswith` test and runs a gate.
    """
    lines = [ln.strip() for ln in run.strip().splitlines()]
    lines = [ln for ln in lines if ln and not ln.startswith("#")]
    if not lines:
        return False        # an empty body is unreadable, not preparation
    return all(
        any(ln.startswith(p) for p in SETUP_PREFIXES) and not any(c in ln for c in CHAINS)
        for ln in lines)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _step_keys(block: str) -> dict[str, str]:
    """The mapping keys of one step, block scalars included, from an already-dedented block."""
    lines = block.split("\n")
    keys: dict[str, str] = {}
    i = 0
    while i < len(lines):
        raw, s = lines[i], lines[i].strip()
        if _indent(raw) == 0 and s and not s.startswith("#") and ":" in s:
            k, _, v = s.partition(":")
            k, v = k.strip(), v.strip()
            if v in ("|", ">", "|-", ">-", "|+", ">+"):
                body, j = [], i + 1
                while j < len(lines):
                    if not lines[j].strip():
                        body.append("")
                    elif _indent(lines[j]) == 0:
                        break
                    else:
                        body.append(lines[j])
                    j += 1
                keys[k] = "\n".join(body)
                i = j
                continue
            keys[k] = v
        i += 1
    return keys


def parse_steps(text: str) -> list[tuple[str, dict[str, str]]]:
    """(job, step) for every step in a workflow.

    LIMITS, NAMED RATHER THAN LEFT TO BE FOUND. It assumes the two-space nesting this file uses and
    GitHub's own examples emit. Comments are stripped only OUTSIDE block scalars, because `#` is
    meaningful in a shell body. Anchors and aliases are not followed, so a step defined by an alias
    reads as absent - which fails the coverage check below rather than passing it, and that
    direction is the deliberate one. `continue-on-error:` and step-level `if:` are not modelled at
    all, and their mere presence is a hard failure below rather than a silent pass: a construct this
    parser cannot see must not be readable as a gate the door already has.
    """
    lines = text.split("\n")
    steps: list[tuple[str, dict[str, str]]] = []
    in_jobs, job, i = False, None, 0
    while i < len(lines):
        raw, s, ind = lines[i], lines[i].strip(), _indent(lines[i])
        if not s or s.startswith("#"):
            i += 1
            continue
        if ind == 0:
            in_jobs, job = s == "jobs:", None
            i += 1
            continue
        if in_jobs and ind == 2:
            # A TRAILING COMMENT ON A JOB ID USED TO HIDE EVERY STEP UNDER IT. This required the
            # line to END with `:`, so `evil:  # bandit, strict` was not a job header, `job` stayed
            # None, and the `in_jobs and job` guard below skipped the whole job in silence -
            # partial unreadability rendered as clean, which is invariant 1 on this parser itself.
            # Annotating a job id is ordinary YAML. Found by Fable.
            head = s.split("#", 1)[0].strip()
            if head.endswith(":"):
                job = head[:-1].strip()
                i += 1
                continue
        if in_jobs and job and ind == 4 and s.split("#", 1)[0].strip().startswith("uses:"):
            # A WHOLE EXTERNAL WORKFLOW, RUN AS A JOB. `uses:` at job level is a reusable workflow:
            # legal, ordinary, and able to fail `main` on anything it contains. This parser only
            # ever read `- ` items under a job, so the job-level key was never seen and the file
            # reported no divergence at all. The docstring named anchors and `if:` as its limits;
            # this one was not named, and unlike anchors it failed GREEN. Found by Fable.
            steps.append((job, {"__job_uses__": s.split(":", 1)[1].strip()}))
            i += 1
            continue
        if in_jobs and job and s.startswith("- "):
            if s[2:].lstrip().startswith("{"):
                # A FLOW-MAPPING STEP - `- { name: x, run: y }`. Valid YAML, accepted by Actions,
                # and `_step_keys` reads it as one nonsense key with no `run`, so `divergences`
                # dropped it through the same `run is None: continue` that once swallowed
                # `uses:`. Reported as unreadable rather than parsed. Found by Fable.
                steps.append((job, {"__unparsed__": s}))
                i += 1
                continue
            cut = ind + 2
            block, j = [raw[cut:]], i + 1
            while j < len(lines):
                if not lines[j].strip():
                    block.append("")
                elif _indent(lines[j]) <= ind:
                    break
                else:
                    block.append(lines[j][cut:])
                j += 1
            steps.append((job, _step_keys("\n".join(block))))
            i = j
            continue
        i += 1
    return steps


def divergences(workflow: str, door: str) -> list[str]:
    """Every way the two gate lists fail to be the one list they claim to be."""
    problems: list[str] = []
    # THE COMMENTS OF THE DOOR ARE NOT THE DOOR. Every `must_appear` below is matched against the
    # executable lines only, because a step commented out still leaves its prose behind and the
    # prose is what would otherwise vouch for it. See `executable_lines`.
    door = executable_lines(door)
    steps = parse_steps(workflow)
    if not steps:
        # Invariant 1 on this file's own instrument. An empty parse is "could not read the
        # workflow", and reporting it as "no divergences" would be a green built out of silence.
        return ["NO STEPS PARSED from the workflow - that is unreadable, not clean"]

    seen: set[str] = set()
    for job, step in steps:
        if "__job_uses__" in step:
            problems.append(
                f"{job}: the job IS a reusable workflow (`uses: {step['__job_uses__']}`). Every "
                "gate it runs is outside this file and can fail `main`; the door cannot be shown "
                "to match a workflow this comparison never reads.")
            continue
        if "__unparsed__" in step:
            problems.append(
                f"{job}: step `{step['__unparsed__']}` is a flow mapping, which this checker does "
                "not parse - it cannot tell whether that step can fail the build, and unknown is "
                "reported rather than assumed.")
            continue
        for unmodelled in ("continue-on-error", "if"):
            if unmodelled in step:
                problems.append(
                    f"{job}: step '{step.get('name', step.get('run', '?'))}' uses "
                    f"`{unmodelled}:`, which this checker does not model - it cannot tell whether "
                    "that step can fail the build, and unknown is reported rather than assumed")
        uses = step.get("uses")
        if uses is not None:
            # A THIRD-PARTY ACTION IS A GATE THAT CAN REDDEN `main`, and most of them ship exactly
            # to do that. This arm read `if run is None: continue`, so `uses: gitleaks-action` -
            # a step that fails the build on its own findings - was skipped as "not a command" and
            # reported as no divergence. Only the actions that configure the runner are exempt.
            action = uses.split("@", 1)[0].strip()
            if action not in BENIGN_ACTIONS:
                problems.append(
                    f"{job}: step `uses: {uses}`, a third-party action that is not runner "
                    "preparation. It can fail the build while the door knows nothing about it; "
                    "give it a row in CI_GATES or add it to BENIGN_ACTIONS with a reason.")
            continue
        run = step.get("run")
        if run is None:
            continue
        name = step.get("name")
        if name is None:
            if not _is_pure_setup(run):
                first = run.strip().splitlines()[0].strip() if run.strip() else ""
                problems.append(
                    f"{job}: an UNNAMED step runs `{first}`, which is not runner preparation. "
                    "A gate with no name cannot be matched to the door; name it and add a row.")
            continue
        seen.add(name)
        rule = CI_GATES.get(name)
        if rule is None:
            problems.append(
                f"{job}: CI step '{name}' has NO ROW in CI_GATES. It can turn `main` red while "
                "the door knows nothing about it - which is the defect this table exists for.")
        elif isinstance(rule, Door):
            if rule.must_appear not in door:
                problems.append(
                    f"{job}: CI step '{name}' is blocking, but scripts/push.sh does not contain "
                    f"`{rule.must_appear}` - the door checks LESS than the arbiter.")
        elif SENTINEL not in run:
            problems.append(
                f"{job}: CI step '{name}' is declared advisory, but its body carries no "
                f"`{SENTINEL}` - an advisory gate with no expiry is a permanent one.")

    for name in CI_GATES:
        if name not in seen:
            problems.append(
                f"CI_GATES names a step '{name}' that gates.yml no longer has. A stale "
                "correspondence describes gates that are not running.")
    return problems


def _mypy_step() -> dict[str, str]:
    for _job, step in parse_steps(WORKFLOW.read_text(encoding="utf-8")):
        if step.get("name") == "mypy":
            return step
    raise AssertionError("gates.yml has no step named 'mypy'")


# --- the two lists are one list ----------------------------------------------------------------

def test_every_blocking_ci_gate_is_also_at_the_door():
    """The assertion the header of gates.yml has been making, now measured."""
    assert divergences(WORKFLOW.read_text(encoding="utf-8"),
                       DOOR.read_text(encoding="utf-8")) == []


def test_the_comparison_is_able_to_fail():
    """L-16: present is not armed, and a checker nobody has seen fire is a promise.

    Each control is a divergence that really happened or really could: a blocking step the door
    lacks, a step CI grew that the table never heard of, a row outliving its step, and an advisory
    step with no expiry - which is the exact state this task found `mypy` in.
    """
    def door_gap(problems):
        return [p for p in problems if "checks LESS than the arbiter" in p]

    blocking = "jobs:\n  j:\n    steps:\n      - name: ruff\n        run: ruff check src\n"
    assert door_gap(divergences(blocking, "#!/usr/bin/env bash\npytest\n"))
    # The control for the control: the SAME workflow against a door that does run ruff reports no
    # gap. Without it, an assertion that merely finds a substring passes on a checker that reports
    # every step as missing, and the fire it demonstrates would be indiscriminate rather than real.
    assert not door_gap(divergences(blocking, "python3 -m ruff check src\n"))

    untabled = ("jobs:\n  j:\n    steps:\n      - name: a gate nobody told the door about\n"
                "        run: bandit -r src\n")
    assert any("NO ROW in CI_GATES" in p for p in divergences(untabled, DOOR.read_text()))

    assert any("'ruff' that gates.yml no longer has" not in p for p in divergences(blocking, "x"))
    assert any("'mypy' that gates.yml no longer has" in p for p in divergences(blocking, "x"))

    no_expiry = ("jobs:\n  j:\n    steps:\n      - name: mypy\n"
                 "        run: mypy src --ignore-missing-imports || true\n")
    assert any("no expiry" in p for p in divergences(no_expiry, DOOR.read_text()))


def test_a_step_commented_out_at_the_door_is_not_vouched_for_by_its_own_comment():
    """The false green that shipped inside the check written to prevent it.

    `executable_lines` existed, was documented as the fix, and was never called - so the assertion
    below passed on a door whose lint, site and test steps were all commented out, because the long
    comments explaining why those steps matter still contained the strings being matched. The
    helper is only a fix once something fails without it; this is that something.
    """
    door = DOOR.read_text(encoding="utf-8")
    disabled = "\n".join(
        ("# " + ln) if ln.strip().startswith(('echo "5/7', 'echo "6/7', 'echo "7/7')) else ln
        for ln in door.splitlines())
    # The prose survives the commenting-out; that is precisely why the raw substring test passed.
    assert "-m ruff" in disabled and "npm run build" in disabled
    gaps = [p for p in divergences(WORKFLOW.read_text(encoding="utf-8"), disabled)
            if "checks LESS than the arbiter" in p]
    # 4 -> 5 on 2026-08-24. This number moves ONLY together with the NAME of the gap that was
    # added; a bare bump is a gate weakened while wearing the clothes of a fix. Exactly one arrived:
    # `tests: CI step 'build the site'`. The `tests` job (whole-tree suite) did not build the site,
    # so `test_emitted_ids_are_unique` failed in CI against an empty `web/dist` - which that test
    # correctly calls `check_did_not_run` rather than a clean sweep. Excluding it was not available:
    # the whole-tree suite is deliberately BARE. So that job builds too, under the SAME step name as
    # the one in `shipped`, which means the same CI_GATES row and the same door (`npm run build`).
    # The prior four are untouched: tests/cov, shipped/build, shipped/pytest, lint/ruff.
    assert len(gaps) == 5, f"a disabled door was reported as matching CI: {gaps}"


def test_a_gate_chained_behind_a_setup_command_is_not_read_as_setup():
    """`pip install bandit && bandit -r src` passes a prefix test and runs a gate."""
    chained = ("jobs:\n  j:\n    steps:\n"
               "      - run: pip install bandit && bandit -r src --strict\n")
    assert any("not runner preparation" in p for p in divergences(chained, DOOR.read_text()))
    # And the control for the control: genuine preparation is still waved through, or the check
    # above would be satisfied by a predicate that simply rejects everything.
    plain = "jobs:\n  j:\n    steps:\n      - run: pip install --quiet pytest pytest-cov\n"
    assert not any("not runner preparation" in p for p in divergences(plain, DOOR.read_text()))


def test_a_third_party_action_is_a_gate_and_not_merely_not_a_command():
    """`uses:` steps were skipped wholesale; most third-party actions fail the build by design."""
    uses = ("jobs:\n  j:\n    steps:\n      - name: gitleaks\n"
            "        uses: gitleaks/gitleaks-action@v2\n")
    assert any("third-party action" in p for p in divergences(uses, DOOR.read_text()))
    benign = "jobs:\n  j:\n    steps:\n      - uses: actions/checkout@v4\n"
    assert not any("third-party action" in p for p in divergences(benign, DOOR.read_text()))


def test_no_workflow_can_appear_without_being_declared():
    """This file reads one workflow; the repository may hold others that redden `main`.

    A fourth workflow file would be invisible to every assertion here while being perfectly able to
    fail the build - and the only thing that counted the workflows was the word "three" in a README.
    """
    found = {p.name for p in (ROOT / ".github" / "workflows").glob("*.yml")}
    assert found == set(DECLARED_WORKFLOWS), (
        f"undeclared: {sorted(found - set(DECLARED_WORKFLOWS))}; "
        f"declared but absent: {sorted(set(DECLARED_WORKFLOWS) - found)}. Every workflow that can "
        "fail `main` is either mirrored at the door or declared here with the reason it is not.")


def test_a_reusable_workflow_job_is_not_invisible():
    """`uses:` at JOB level runs an entire external workflow; the parser only read `- ` steps."""
    reusable = ("jobs:\n  audit:\n"
                "    uses: octo-org/sec/.github/workflows/strict-audit.yml@main\n")
    assert any("reusable workflow" in p for p in divergences(reusable, DOOR.read_text()))


def test_a_flow_mapping_step_is_reported_unreadable_rather_than_skipped():
    flow = "jobs:\n  j:\n    steps:\n      - { name: bandit, run: bandit -r src --strict }\n"
    assert any("flow mapping" in p for p in divergences(flow, DOOR.read_text()))


def test_a_commented_job_id_does_not_hide_the_steps_beneath_it():
    """Partial unreadability rendered as clean is invariant 1 turned on the parser."""
    hidden = ("jobs:\n  evil:   # bandit, strict\n    steps:\n      - name: bandit strict\n"
              "        run: bandit -r src --strict\n")
    assert any("NO ROW in CI_GATES" in p for p in divergences(hidden, DOOR.read_text()))


def test_a_gate_reached_by_command_substitution_is_not_setup():
    subst = ("jobs:\n  j:\n    steps:\n"
             "      - run: pip install --quiet $(python scripts/choose_gate.py)\n")
    assert any("not runner preparation" in p for p in divergences(subst, DOOR.read_text()))


def test_a_printed_excuse_does_not_vouch_for_the_step_it_replaces():
    """The RED-5.1 false green, one string context over: prose moved from a comment into an echo.

    `executable_lines` removed `#` comments, so the fix held for the way a step gets commented out
    and not for the way it gets announced as skipped - and the excuse message contains the very
    string the table matches on. A door running no lint reported as matching CI.
    """
    door = DOOR.read_text(encoding="utf-8")
    excused = "\n".join(
        'echo "5/7 lint skipped today: -m ruff release is broken"'
        if ln.strip().startswith('echo "5/7') else ln
        for ln in door.splitlines())
    assert "-m ruff" in excused, "the excuse still contains the matched string; that is the trap"
    assert any("'ruff' is blocking" in p for p in divergences(WORKFLOW.read_text(), excused))


def test_removing_string_literals_does_not_hide_a_gate_the_door_really_runs():
    """The control: stripping quotes must not manufacture false reds on the real door."""
    assert divergences(WORKFLOW.read_text(encoding="utf-8"),
                       DOOR.read_text(encoding="utf-8")) == []
    assert "-m ruff" in executable_lines('echo "step #5 lint"; python3 -m ruff check src\n')


def test_an_unreadable_workflow_is_not_reported_as_clean():
    assert divergences("", DOOR.read_text(encoding="utf-8")) == ["NO STEPS PARSED from the "
                                                                 "workflow - that is unreadable, "
                                                                 "not clean"]


def test_a_construct_the_parser_cannot_model_is_a_red_and_not_a_pass():
    swallowed = ("jobs:\n  j:\n    steps:\n      - name: ruff\n        continue-on-error: true\n"
                 "        run: ruff check src\n")
    assert any("does not model" in p for p in divergences(swallowed, DOOR.read_text()))


# --- the advisory step carries an expiry, and the expiry is armed -------------------------------

def test_the_mypy_advisory_state_has_not_expired():
    """A TIME BOMB, deliberately, and the reason is the file it is written against.

    `.github/workflows/README.md` carries a section about a dated condition that expired while
    every document went on repeating it, kept as a record because "a stale condition in a CI
    document is how a pipeline comes to be described as dead while it is running". The promise
    about mypy sat four lines above that section with no date and nothing to fire - the same defect
    with the clock removed. This is the clock. The way past it is to make mypy blocking, or to move
    the date deliberately and record why; both are decisions, which is the whole point, and drift
    is not among the options.
    """
    today = datetime.now(timezone.utc).date()
    assert today <= ADVISORY_UNTIL, (
        f"mypy has been advisory past {ADVISORY_UNTIL.isoformat()}. Either it is clean and the "
        "step becomes blocking (and joins scripts/push.sh in the same commit), or the baseline is "
        f"still dirty - it was {BASELINE_2026_08_20[0]} errors in {BASELINE_2026_08_20[1]} files "
        "on 2026-08-20 - and a new date is ratified in DECISIONS.md with the count that justifies "
        "it. Moving the date silently is the failure this test exists to prevent.")


def test_the_date_is_stated_identically_everywhere_it_is_stated():
    """One date, three copies, and the copies are checked - L-2 in its cheapest form."""
    stamp = ADVISORY_UNTIL.isoformat()
    assert f"{SENTINEL} {stamp}" in _mypy_step()["run"], (
        "the workflow step must carry the expiry it is governed by, so a reader of the step does "
        "not have to know this file exists")
    assert stamp in WORKFLOW_README.read_text(encoding="utf-8"), (
        "the document that makes the promise must state the date the promise expires")


def test_mypy_is_advisory_about_its_findings_and_never_about_whether_it_ran():
    """The three states `|| true` collapsed into one.

    `mypy ... || true` suppressed the findings, which was intended; it also suppressed mypy failing
    to start, which was not. An instrument that did not run reported exactly what a clean baseline
    reports, and the clean baseline is the trigger for ending the advisory state - so the one shape
    that could have moved this gate forward was indistinguishable from a crash.
    """
    body = _mypy_step()["run"]
    assert "|| true" not in body, "`|| true` cannot tell a clean run from a broken one"
    assert "set +e" in body, (
        "GitHub runs `run:` under `bash -e`, so mypy exiting 1 would fail the step; the advisory "
        "state depends on -e being lifted deliberately rather than by accident")
    assert "not_measured" in body, "the exit>=2 branch must name the state it is reporting"
    for branch in ('"$rc" -ge 2', '"$rc" -eq 0'):
        assert branch in body, f"the {branch} branch is missing: the three states are not separated"


def test_the_clean_baseline_ends_the_advisory_state_rather_than_being_reported_as_success():
    """The condition is armed where it can be measured, and only there.

    mypy is not installed on the audit host, so a local reading of "zero errors" would be the
    instrument's absence returning as a measurement - L-1, and L-11's sharper form, where the
    refusal arrives wearing the shape of a result. The condition is therefore evaluated in CI,
    which installs mypy, and what is checked HERE is that the workflow does the trip: a clean run
    fails the step and says what to do about it, rather than passing quietly for another year.
    """
    body = _mypy_step()["run"]
    assert "exit 1" in body, "no branch of an advisory step ends the advisory state"
    assert "push.sh" in body, (
        "the step that trips must name the door, because becoming blocking without joining "
        "scripts/push.sh recreates the divergence this whole file is about")
