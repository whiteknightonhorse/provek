"""T-S7 - the workflow files are judged by a real YAML parser, and the judgement is watched to fire.

THE DEFECT THIS ARMS AGAINST IS MEASURED, NOT IMAGINED. `66f61ea` left this host with seven green
gates and turned `main` RED in the same second it landed: three `run:` lines carried
`--only-binary=:all: ` in a plain scalar, `: ` ended the key, and GitHub refused the document before
a single job existed - a run created and concluded in the same second with ZERO jobs. The reading is
`evidence/RED-031-seven-green-gates-and-a-workflow-that-never-parsed.txt`; the fixture below is that
line, byte for byte.

WHAT MAKES THIS DIFFERENT FROM THE GATES THAT PASSED IT.
`test_the_scanner_that_passed_the_broken_file_still_passes_it` runs `scripts/verify_pip_pins.py`
over the same fixture and asserts it reports CLEAN. That is not a complaint about that gate - it
reads its three lines correctly and always did. It is the finding in executable form: a checker
more permissive than the machine it stands in for will certify files that machine cannot run
(L-31), and the day somebody widens the hand-written reader to cover parsing, that test is the one
that has to be deleted deliberately rather than a comment somebody may or may not read.

WHERE THIS GATE ACTUALLY BITES, AND IT IS NOT WHERE THE OTHERS DO. In CI this test cannot catch a
broken `gates.yml`: a workflow that does not parse runs no job, so the job that would run this file
never starts. The defect deletes its own detector, which is precisely how `66f61ea` produced seven
green gates and three green check runs. What the CI copy CAN catch is a broken `codeql.yml` or
`scorecard.yml` - separate documents whose failure does not stop this workflow. The copy that
catches the RED-031 case is the one at the DOOR, in `scripts/push.sh`, which runs the suite while
the push does not yet exist. That inverts this repository's usual arrangement, where the door is
the convenience and CI is the guarantee because a gate depending on the pusher's discipline is a
habit. It is written down rather than left implied: "the test runs in CI" would otherwise read as a
protection it structurally cannot give.

NEARLY EVERY TEST IS DRIVEN BY A FIXTURE THAT MAKES IT FAIL, and the survivors are counted rather
than covered by the word "every". THE UNIT IS TESTS, not assertions: `evidence/RED-034-*` reads node
ids out of pytest's summary, so an assertion sitting under an earlier one in the same test is
invisible to it, and several here are - the granularity limit is written out at the foot of that
file. A test that only reads the live tree and finds it clean cannot tell a working parser from a
function returning an empty list - invariant 5, and the reason that evidence file keeps the run
where the RED-031 form is actually caught.

The first draft said EVERY ASSERTION, and Fable counted four tests killed by nothing at all - a
claim stronger than its artefact inside a suite about checkers that certify more than they measured.
Five mutations were added over two rounds and two tests here were SPLIT, so that two assertions
hiding behind an earlier one could be shown to fail on their own. The word ASSERTION then survived
one round longer than the claim it carried, in this very paragraph, which is L-2 in miniature.

Three tests survive every mutation, and they are named in BOTH places rather than pointed at:
`test_the_repaired_form_is_accepted`, the acceptance control, structurally unkillable by a generator
that refuses to break its own apparatus; `test_a_duplicated_key_is_reported_rather_than_silently_resolved`,
which asserts a stated boundary and is reachable only by a STRICTER edit, not a permissive one; and
`test_the_parser_this_gate_needs_is_in_the_set_the_job_installs`, a fact about
`requirements/ci-tests.txt` rather than about the gate. The generator refuses to rewrite its
artefact while the measured set differs from the one it expects, and its refusal names this
docstring, D-32 and the paragraph under the list as the three copies to move in the same edit. That
is an instruction to a person, enforced only at the moment somebody regenerates the evidence - not
a guarantee that the prose cannot drift.

AND THE VACUITY TRAP THIS FILE ITSELF COULD FALL INTO. `check()` reports an absent PyYAML and an
absent directory as problems too, so a fixture test asserting merely "something was returned" would
go GREEN on a host with no parser installed - passing because the instrument was missing, over a
file it never read. Every fixture below asserts the `DOES NOT PARSE` marker instead, and
`test_a_missing_parser_is_not_measured_rather_than_clean` holds the two states apart.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import verify_pip_pins  # noqa: E402
from scripts.verify_workflow_yaml import (  # noqa: E402
    SUFFIXES,
    UNPARSEABLE,
    check,
    parse_problems,
    workflow_files,
)

# WHAT GITHUB READS, WRITTEN OUT INDEPENDENTLY OF THE GATE'S OWN CONSTANT. See
# `test_every_file_in_the_workflows_directory_is_put_in_front_of_the_parser` for why this is not
# `from scripts.verify_workflow_yaml import SUFFIXES` a second time.
GITHUB_SUFFIXES = (".yml", ".yaml")

# A DIGEST-SHAPED DIGEST IN THE FIXTURE BELOW, and that is not decoration. `--hash=sha256:aaaa`
# would tie the L-31 assertion to every future tightening of `verify_pip_pins.py` - a length check
# on the digest, say, which has nothing to do with permissive parsing - and the red would arrive
# under the message "the premise of L-31 has changed", naming the wrong cause. Found by Fable.
FIXTURE_HASH = "sha256:" + "9f" * 32

# THE LINE THAT KILLED `66f61ea`, quoted rather than paraphrased. `run:` is a plain scalar here, so
# the `: ` inside `--only-binary=:all: -r` reads as a nested mapping key and the document dies. The
# repair that shipped was `run: |`, which changes the command BYTE FOR BYTE not at all.
RED_031_FORM = (
    "jobs:\n"
    "  tests:\n"
    "    steps:\n"
    "      - run: pip install --quiet --require-hashes --only-binary=:all: "
    "-r requirements/ci-tests.txt\n"
)
REPAIRED_FORM = (
    "jobs:\n"
    "  tests:\n"
    "    steps:\n"
    "      - run: |\n"
    "          pip install --quiet --require-hashes --only-binary=:all: "
    "-r requirements/ci-tests.txt\n"
)


def _workflows(tmp_path: Path, name: str, body: str) -> Path:
    d = tmp_path / ".github" / "workflows"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(body, encoding="utf-8")
    return d


def _unparseable(problems: list[str]) -> list[str]:
    return [p for p in problems if UNPARSEABLE in p]


# --- the tree itself ------------------------------------------------------------------------------

def test_every_workflow_in_this_tree_parses():
    """The property, on the real files, on every push and at the door."""
    assert check() == []


def test_every_file_in_the_workflows_directory_is_put_in_front_of_the_parser():
    """The work list is the DIRECTORY, not a remembered set of names.

    The count is deliberately not asserted here: `tests/test_door_matches_ci.py` already holds the
    number of workflow files, and a second copy of that number is a rule written in two places
    (L-2). What is asserted is that nothing in the directory is skipped - which is the property a
    hard-coded list would lose the day a fourth workflow arrives.

    THE EXPECTATION IS WRITTEN OUT IN `GITHUB_SUFFIXES` RATHER THAN IMPORTED FROM THE SUBJECT, and
    the first draft of this test did import it. `on_disk` was built with the gate's own `SUFFIXES`,
    so mutation 6 of RED-034 - narrowing it to `.yml` alone - moved BOTH sides of the comparison
    and this test survived, blind to precisely the L-6 defect its neighbour is written to catch. An
    expectation derived from the subject's own constant is a checker certifying itself. The
    suffix comparison is now its OWN test below, so the two properties can be shown to fail
    separately. Found by Fable.
    """
    d = ROOT / ".github" / "workflows"
    on_disk = {p.name for p in d.iterdir() if p.is_file() and p.suffix in GITHUB_SUFFIXES}
    assert {p.name for p in workflow_files()} == on_disk
    assert on_disk, "the workflows directory is empty, so this gate has no subject"


def test_the_gate_reads_the_two_extensions_github_reads():
    """The other half of the test above, split off for the reason that one gives.

    One test asserting both properties can only ever demonstrate the first: it dies at the first
    failing assert, so a mutation narrowing `SUFFIXES` and a mutation replacing the directory
    listing produce the same node id in pytest's summary and RED-034 refuses the pair as
    indistinguishable.
    """
    assert set(SUFFIXES) == set(GITHUB_SUFFIXES), (
        f"the gate reads {SUFFIXES}; GitHub reads {GITHUB_SUFFIXES}")


def test_the_parser_this_gate_needs_is_in_the_set_the_job_installs():
    """The gate runs in CI only because `requirements/ci-tests.txt` carries PyYAML (D-32).

    Without it the `tests` job cannot import this gate at all, and the failure would arrive as a
    collection error about a missing module rather than as a statement about the tree. The set is
    read here so that removing the line is refused by a sentence naming why it is there.
    """
    body = (ROOT / "requirements" / "ci-tests.txt").read_text(encoding="utf-8")
    assert "pyyaml" in verify_pip_pins.pins(body), "PyYAML left ci-tests.txt; this gate cannot run in CI"


# --- the defect that was actually paid for --------------------------------------------------------

def test_the_form_that_reddened_main_is_caught(tmp_path):
    """RED-031, reproduced: a plain scalar carrying `: `."""
    problems = _unparseable(check(_workflows(tmp_path, "gates.yml", RED_031_FORM)))
    assert problems, "the line that killed 66f61ea was accepted"
    assert "mapping values are not allowed" in problems[0], problems


def test_the_refusal_carries_the_position_the_startup_failure_withheld(tmp_path):
    """A SEPARATE TEST, AND THE SPLIT IS WHAT MAKES THE PROPERTY MEASURABLE.

    The parser's mark travels with its message; GitHub's own answer was the word `startup_failure`
    and a run with zero jobs, and finding the three lines took a hand. This assertion lived under
    the one above until RED-034 was asked to show it load-bearing and could not: the mutation that
    drops the LOCATION and keeps the SENTENCE killed exactly the same TEST as the one that drops
    both, because the instrument reads node ids out of pytest's summary and a test dies at its
    first failing assert. Two mutations with one failure set are refused by that generator, which
    is how the shadow was found. Splitting the test is the repair - declaring the granularity
    unreachable would have been the easier one. Found by Fable.
    """
    problems = _unparseable(check(_workflows(tmp_path, "gates.yml", RED_031_FORM)))
    assert problems, "the line that killed 66f61ea was accepted"
    assert "line" in problems[0] and "column" in problems[0], problems[0]


def test_the_repaired_form_is_accepted(tmp_path):
    """The control, and it carries the same command byte for byte. Without it every assertion above
    is satisfied by a gate that refuses everything - which is the false red that teaches people to
    route around a gate (L-5)."""
    assert check(_workflows(tmp_path, "gates.yml", REPAIRED_FORM)) == []


def test_the_scanner_that_passed_the_broken_file_still_passes_it(tmp_path):
    """THE FINDING, IN EXECUTABLE FORM.

    `scripts/verify_pip_pins.py` reads the RED-031 file and reports it clean - correctly, on its own
    terms: the three flags are there and the requirements file exists. It is a hand-written reader,
    and the document it accepted is one GitHub cannot open. Both readings are taken here on the same
    bytes so the gap is a measurement rather than a paragraph.
    """
    d = _workflows(tmp_path, "gates.yml", RED_031_FORM)
    reqs = tmp_path / "requirements"
    reqs.mkdir()
    (reqs / "ci-tests.txt").write_text(f"pytest==9.1.1 \\\n    --hash={FIXTURE_HASH}\n",
                                       encoding="utf-8")

    assert verify_pip_pins.check(workflows=d, root=tmp_path) == [], "the premise of L-31 has changed"
    assert _unparseable(check(d)), "the parser accepted what GitHub refused"


# --- the other shapes a workflow dies of ----------------------------------------------------------

def test_a_tab_indented_document_is_caught(tmp_path):
    """YAML forbids the tab as indentation, and an editor supplies one without being asked."""
    body = "jobs:\n\ttests:\n\t\truns-on: ubuntu-latest\n"
    assert _unparseable(check(_workflows(tmp_path, "gates.yml", body))), "a tab was accepted"


def test_an_unclosed_quote_is_caught(tmp_path):
    body = 'jobs:\n  tests:\n    name: "unclosed\n    runs-on: ubuntu-latest\n'
    assert _unparseable(check(_workflows(tmp_path, "gates.yml", body)))


def test_a_duplicated_key_is_reported_rather_than_silently_resolved(tmp_path):
    """NOT a parse error, and that is why it is here as a control rather than as a catch.

    PyYAML takes the LAST of two identical keys without a word, so a workflow with two `jobs:`
    blocks parses and half of it is discarded. This gate does not claim to see that - it asserts
    well-formedness and nothing else - and the assertion below records the boundary instead of
    leaving a reader to assume a coverage this file does not have.
    """
    body = "jobs:\n  a:\n    runs-on: ubuntu-latest\njobs:\n  b:\n    runs-on: ubuntu-latest\n"
    assert check(_workflows(tmp_path, "gates.yml", body)) == []


def test_a_workflow_saved_as_yaml_is_parsed_too(tmp_path):
    """GitHub reads both extensions; a checker that knew one would be silent about the other (L-6)."""
    assert _unparseable(check(_workflows(tmp_path, "gates.yaml", RED_031_FORM)))


# --- the states that are not "clean" and not a parse error ----------------------------------------

def test_an_empty_document_is_not_a_workflow(tmp_path):
    """A truncated file parses to `None` without raising. Reported as its own state, because "the
    document is empty" and "the workflow declares no jobs" are two facts and only one of them is
    about YAML."""
    problems = check(_workflows(tmp_path, "gates.yml", "\n# nothing but a comment\n"))
    assert any("EMPTY" in p for p in problems), problems


def test_a_top_level_sequence_is_refused(tmp_path):
    """Valid YAML, impossible workflow. Well-formed is not the same claim as well-shaped, and the
    one place this file crosses that line is here, where GitHub's requirement is unambiguous."""
    problems = check(_workflows(tmp_path, "gates.yml", "- jobs\n- steps\n"))
    assert any("mapping" in p for p in problems), problems


def test_a_file_that_is_not_utf8_is_unreadable_rather_than_clean(tmp_path):
    """`grep` on this host exits 1 with empty output on invalid UTF-8, which is indistinguishable
    from "no matches" - a trap already recorded against the shell. Here the decode failure is a
    named state instead of an absence of findings (invariant 1)."""
    d = tmp_path / ".github" / "workflows"
    d.mkdir(parents=True)
    (d / "gates.yml").write_bytes(b"jobs:\n  a: \xff\xfe not utf-8\n")
    problems = check(d)
    assert any("COULD NOT BE READ" in p for p in problems), problems


def test_an_empty_workflow_directory_reports_unknown_not_clean(tmp_path):
    """Zero files and zero failures print the same green. A gate that has quietly lost its subject
    is how a control disappears in silence - invariant 1, pointed at the instrument."""
    d = tmp_path / "workflows"
    d.mkdir()
    assert any("measured NOTHING" in p for p in check(d)), check(d)


def test_an_absent_workflow_directory_is_not_reported_as_clean(tmp_path):
    assert any("ABSENT" in p for p in check(tmp_path / "nope")), check(tmp_path / "nope")


def test_a_missing_parser_is_not_measured_rather_than_clean(monkeypatch):
    """The instrument's own absence, which is the failure this gate would be least able to see.

    With PyYAML gone the gate must say so. It must ALSO not say `DOES NOT PARSE`, or every fixture
    above would pass on a host with no parser at all - green over a file nobody read, which is
    precisely the shape of the defect they exist to catch.
    """
    monkeypatch.setattr("scripts.verify_workflow_yaml.yaml", None)
    problems = parse_problems(RED_031_FORM, "gates.yml")
    assert problems and "PyYAML is ABSENT" in problems[0], problems
    assert not _unparseable(problems), problems


def test_a_missing_parser_survives_the_path_the_door_actually_walks(monkeypatch, tmp_path):
    """THE SAME STATE, THROUGH `check()` RATHER THAN THROUGH `parse_problems()`.

    The test above holds the property at the granularity of one function. Nothing held it at the
    granularity the door and CI actually use, so a permissive edit ONE LEVEL UP - an early
    `if yaml is None: return []` in `check()` - would have been killed by no test on any host that
    has PyYAML installed, which is every host where the suite runs at all. The gate would print
    `clean` on a machine with no parser and the whole suite would stay green over it. That is
    invariant 1 defeated by the granularity of its own test rather than by its absence. Found by
    Fable, by reading `check()` - the ranking sentence that stood here called it unseeable from the
    assertions, which was flattery and also false.
    """
    monkeypatch.setattr("scripts.verify_workflow_yaml.yaml", None)
    problems = check(_workflows(tmp_path, "gates.yml", RED_031_FORM))
    assert problems, "check() reported a clean tree with no parser installed"
    assert any("PyYAML is ABSENT" in p for p in problems), problems
    assert not _unparseable(problems), problems


def test_the_module_runs_as_a_command_and_says_what_it_measured(capsys):
    """The gate is executable, and its clean line names the files it read rather than asserting a
    tidy word over an unknown subject."""
    from scripts.verify_workflow_yaml import main
    assert main() == 0
    out = capsys.readouterr().out
    assert "gates.yml" in out and "yaml.safe_load" in out, out
