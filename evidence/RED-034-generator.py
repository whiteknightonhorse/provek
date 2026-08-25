#!/usr/bin/env python3
"""Produces evidence/RED-034-the-file-every-gate-read-and-no-parser-had-opened.txt.

Two halves, and the first is not a mutation of anything.

PART ONE PUTS THE FILE `66f61ea` ACTUALLY SHIPPED BACK INTO THE TREE and takes both readings on it:
`scripts/verify_pip_pins.py`, which reported it clean at the time and still does, and
`scripts/verify_workflow_yaml.py`, which refuses it at line 128, column 69. The document is fetched
out of git rather than retyped, for RED-033-generator.py's reason: a reconstruction can flatter the
repair by being subtly worse than the original, and an evidence corpus assembled from memory is the
defect this project sells the detection of.

PART TWO establishes invariant 5 for the gate itself - a test must be ABLE to fail - by mutating
`scripts/verify_workflow_yaml.py` one edit at a time. Every mutation here runs in the PERMISSIVE
direction, which is the direction L-31 is about: each makes the gate accept something, and the
suite must notice. It refuses on the same conditions RED-033 established, each earned by a defect
already shipped once here:

  * a mutation that does not go red;
  * a mutation whose marker cannot be grepped back out of the file - the edit must be proven to
    have landed, not assumed from a string having been replaced;
  * a pytest that did not RUN. Only exit 1 is a suite that ran and failed; exit 2 is a file that no
    longer imports, and reading any nonzero exit as "red" is invariant 1 inside the instrument;
  * a mutation that kills the instrument control. `test_the_repaired_form_is_accepted` is the one
    assertion here that observes an ACCEPTED document; a mutation taking it down has broken the
    apparatus rather than demonstrated a property, and a gate that refuses everything is the false
    red that teaches routing around gates (L-5);
  * two mutations with the same failure set;
  * a subject not restored byte for byte, or a suite not green afterwards.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402 - T-S14, every artefact names the tree it was captured against

OUT = ROOT / "evidence" / "RED-034-the-file-every-gate-read-and-no-parser-had-opened.txt"
SUITE = "tests/test_workflows_parse.py"
SUBJECT = ROOT / "scripts" / "verify_workflow_yaml.py"
WORKFLOW = ROOT / ".github" / "workflows" / "gates.yml"
SCANNER = "scripts/verify_pip_pins.py"
PARSER_GATE = "scripts/verify_workflow_yaml.py"

PIN = "66f61ea"        # the commit whose gates.yml GitHub could not read
CONTROL = "test_the_repaired_form_is_accepted"


def run(cmd: list[str]) -> tuple[int, str]:
    """One command, one buffer. Nothing here is appended to a shared stream (L-26, RED-013)."""
    done = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=600, check=False)
    return done.returncode, done.stdout + done.stderr


def workflow_from_history() -> str | None:
    """The workflow file as `66f61ea` shipped it, or None if git could not be asked.

    None is a third state and main() treats it as one: "history no longer holds that commit" and
    "we could not read history" are different facts, and substituting a retyped copy for the second
    would put an unverified artefact into the evidence corpus.
    """
    done = subprocess.run(["git", "show", f"{PIN}:.github/workflows/gates.yml"],
                          cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
    return done.stdout if done.returncode == 0 else None


# (title, [(find, replace)], marker). Each edit is asserted to have exactly one anchor.
MUTATIONS: list[tuple[str, list[tuple[str, str]], str]] = [
    (
        "the parse failure is swallowed and the file is reported clean - the gate reduced to the "
        "permissiveness it was written to end",
        [("        return [f\"{name}: {UNPARSEABLE} - {str(exc).strip()}\"]",
          "        return []   # MUTATION-1")],
        "MUTATION-1",
    ),
    (
        "an ABSENT parser reports itself with the same marker a parse failure uses, so every "
        "fixture in the suite would pass on a host with no PyYAML at all",
        [('        return [f"{name}: PyYAML is ABSENT, so this file was NOT PARSED - '
          'not_measured, not clean"]',
          '        return [f"{name}: {UNPARSEABLE} - PyYAML is absent"]   # MUTATION-2')],
        "MUTATION-2",
    ),
    (
        "a workflow directory holding no workflow file is reported clean - zero files and zero "
        "failures printing the same green",
        [('        return [f"{workflows} holds NO workflow file, so this gate measured NOTHING - '
          'unknown, "\n                "not clean"]',
          "        return []   # MUTATION-3")],
        "MUTATION-3",
    ),
    (
        "an absent workflow directory is clean, which is what a tree that deleted its CI would "
        "report",
        [('        return [f"{workflows} is ABSENT: this gate measured NOTHING, which differs from '
          'a tree "\n                "whose workflows are all well-formed"]',
          "        return []   # MUTATION-4")],
        "MUTATION-4",
    ),
    (
        "a file that cannot be decoded is skipped in silence instead of named - the unreadable "
        "half of invariant 1, inside the instrument",
        [('            problems.append(f"{path.name}: COULD NOT BE READ ({exc}) - unreadable, '
          'not clean")\n            continue',
          "            continue   # MUTATION-5")],
        "MUTATION-5",
    ),
    (
        "only one of the two extensions GitHub reads is measured, so a workflow saved as .yaml is "
        "invisible to this gate (L-6)",
        [('SUFFIXES = (".yml", ".yaml")', 'SUFFIXES = (".yml",)   # MUTATION-6')],
        "MUTATION-6",
    ),
    (
        "a document that parses to something other than a mapping is accepted, so an empty file "
        "and a top-level sequence both read as a healthy workflow",
        [("    if doc is None:", "    if False:   # MUTATION-7"),
         ("    if not isinstance(doc, dict):", "    if False:   # MUTATION-7 (second half)")],
        "MUTATION-7",
    ),
    # MUTATIONS 8-10 EXIST BECAUSE FABLE COUNTED WHAT THE FIRST SEVEN LEFT UNTOUCHED. The entry in
    # D-32 then claimed "each assertion is load-bearing" over a set of mutations that did not reach
    # four assertions and two sub-assertions - a claim stronger than its artefact, inside the
    # evidence file for a law about checkers that certify more than they measured.
    (
        "the parser's own message is dropped and only the marker survives, so the gate says a file "
        "does not parse and cannot say WHERE - the difference between a diagnosis and a shrug",
        [('        return [f"{name}: {UNPARSEABLE} - {str(exc).strip()}"]',
          '        return [f"{name}: {UNPARSEABLE}"]   # MUTATION-8')],
        "MUTATION-8",
    ),
    (
        "the clean line stops naming what it read, which is how `clean` comes to be printed over "
        "an unknown subject",
        [('    print(f"T-S7: clean ({len(names)} workflow files parsed by yaml.safe_load: '
          "{', '.join(names)})\")",
          '    print("T-S7: clean")   # MUTATION-9')],
        "MUTATION-9",
    ),
    (
        "an absent parser is folded into a clean tree ONE LEVEL ABOVE the function that reports it "
        "- the permissive edit no test on a host WITH PyYAML could see until this round",
        [("    if not workflows.is_dir():",
          "    if yaml is None:   # MUTATION-10\n        return []\n    if not workflows.is_dir():")],
        "MUTATION-10",
    ),
    # 11 AND 12 REACH TWO ASSERTIONS THE FIRST TEN LEFT SHADOWED behind an earlier `assert` in the
    # same test - the granularity limit named under the list at the foot of this file. Fable
    # counted them; they are not a demonstration that the limit is gone.
    (
        "the parser's LOCATION is dropped and its sentence kept, so the gate can say a file is "
        "malformed and not where - the one reading that turns a startup failure into a repair",
        [("        return [f\"{name}: {UNPARSEABLE} - {str(exc).strip()}\"]",
          "        return [f\"{name}: {UNPARSEABLE} - {str(exc).splitlines()[0]}\"]   "
          "# MUTATION-11")],
        "MUTATION-11",
    ),
    (
        "the reader stops taking the DIRECTORY as its work list and remembers a name instead, "
        "which is how a fourth workflow arrives unmeasured",
        [("    return sorted(p for p in workflows.iterdir() if p.is_file() and p.suffix in SUFFIXES)",
          '    return sorted(p for p in workflows.iterdir() if p.name == "gates.yml")   '
          "# MUTATION-12")],
        "MUTATION-12",
    ),
]

# The three tests no mutation above kills, named here so the generator can refuse to emit a list
# that has drifted from the paragraph explaining it. See the UNCOVERED template.
EXPECTED_UNCOVERED = frozenset({
    "test_a_duplicated_key_is_reported_rather_than_silently_resolved",
    "test_the_parser_this_gate_needs_is_in_the_set_the_job_installs",
    "test_the_repaired_form_is_accepted",
})


def failed_tests(output: str) -> frozenset[str]:
    """Node ids out of pytest's `-rf` summary, which reads `FAILED <nodeid> - <message>`."""
    ids = set()
    for line in output.splitlines():
        if not line.startswith("FAILED ") or "::" not in line:
            continue
        nodeid = line[len("FAILED "):].split(" - ", 1)[0].strip()
        ids.add(nodeid.split("::", 1)[1])
    return frozenset(ids)


def collected_tests() -> tuple[frozenset[str], str | None]:
    """Every test in the suite, asked of pytest rather than counted by hand.

    The uncovered list at the foot of this file is a SUBTRACTION, and a hand-maintained numerator
    would go stale the first time somebody adds a test - which is the exact failure the list exists
    to report on.

    TWO WAYS TO GET NOTHING, AND THEY ARE DIFFERENT FACTS. `pytest` refusing to collect is
    `check_did_not_run`; `pytest` answering while no line matches the format this function reads is
    `unreadable` - the instrument's output moved under it. The first draft returned an empty set
    for both and the caller named only the first, which is invariant 1 inside the tool that reports
    on invariant 1. Found by Fable. The second element is the REASON, or None when the reading
    stands.
    """
    rc, out = run([sys.executable, "-m", "pytest", SUITE, "-q", "--collect-only"])
    if rc != 0:
        return frozenset(), (f"pytest exited {rc} collecting {SUITE}, so the suite was never "
                             "enumerated - check_did_not_run")
    names = frozenset(line.split("::", 1)[1].strip()
                      for line in out.splitlines() if line.startswith(SUITE) and "::" in line)
    if not names:
        return frozenset(), ("pytest collected successfully and NO line matched the node-id format "
                             "this generator reads, so the enumeration is unreadable rather than "
                             "empty - the output format moved")
    return names, None


def part_one() -> tuple[str, int, frozenset[str]]:
    """The historical file, put back, read by both gates. Block, exit code, tests it killed."""
    shipped = workflow_from_history()
    if shipped is None:
        return (f"REFUSED: git could not be asked for {PIN}:.github/workflows/gates.yml, so the "
                "shipped document is NOT MEASURED - which is not the same as absent.\n",
                1, frozenset())
    if "--only-binary=:all: -r requirements/ci-tests.txt\n" not in shipped:
        return (f"REFUSED: {PIN} does not carry the plain scalar this file claims to "
                "reproduce.\n", 1, frozenset())

    pristine = WORKFLOW.read_bytes()
    digest = hashlib.sha256(pristine).hexdigest()
    WORKFLOW.write_text(shipped, encoding="utf-8")
    try:
        scanner_rc, scanner_out = run([sys.executable, SCANNER])
        pins_rc, pins_out = run([sys.executable, "-m", "pytest", "tests/test_pip_pinned.py", "-q"])
        parser_rc, parser_out = run([sys.executable, PARSER_GATE])
        suite_rc, suite_out = run([sys.executable, "-m", "pytest", SUITE, "-q", "-rf"])
    finally:
        WORKFLOW.write_bytes(pristine)

    if hashlib.sha256(WORKFLOW.read_bytes()).hexdigest() != digest:
        return (f"REFUSED: {WORKFLOW} was not restored byte for byte.\n", 1, frozenset())
    if scanner_rc != 0:
        return (f"REFUSED: {SCANNER} did not report the shipped file clean (exit {scanner_rc}), so "
                f"the premise of L-31 has changed and this evidence file is stale.\n{scanner_out}",
                1, frozenset())
    if parser_rc != 1:
        return (f"REFUSED: {PARSER_GATE} exited {parser_rc} on the shipped file; 1 is the only "
                f"reading that means it ran and refused.\n{parser_out}", 1, frozenset())
    if suite_rc != 1:
        return (f"REFUSED: the suite exited {suite_rc} on the shipped file.\n{suite_out}",
                1, frozenset())

    return (
        f"\n{'=' * 100}\n"
        f"PART ONE - the document {PIN} actually shipped, put back into this tree and read twice\n"
        f"{'=' * 100}\n\n"
        f"The file is `git show {PIN}:.github/workflows/gates.yml`, not a reconstruction. Three\n"
        f"`run:` lines carry `--only-binary=:all: ` in a plain scalar - lines 128, 167 and 192,\n"
        f"written from one pattern.\n"
        f"\n--- `python {SCANNER}` ---   exit={scanner_rc}\n\n{scanner_out}"
        f"\n--- `python -m pytest tests/test_pip_pinned.py -q` ---   exit={pins_rc}\n\n{pins_out}"
        f"\nTHAT IS THE FINDING. The gate that judges these very lines reads all three, reports\n"
        f"them hash-pinned, and its whole suite is green - over a file GitHub answered with a run\n"
        f"created and concluded in the same second, holding ZERO jobs.\n"
        f"\n--- `python {PARSER_GATE}` ---   exit={parser_rc}\n\n{parser_out}"
        f"\n--- `python -m pytest {SUITE} -q -rf` ---   exit={suite_rc}\n\n{suite_out}",
        0,
        failed_tests(suite_out),
    )


def main() -> int:
    pristine = SUBJECT.read_bytes()
    digest = hashlib.sha256(pristine).hexdigest()

    rc, before = run([sys.executable, "-m", "pytest", SUITE, "-q"])
    if rc != 0:
        print(f"REFUSED: the suite is not green before any mutation (exit {rc}).\n{before}")
        return 1

    one, code, killed_by_the_shipped_file = part_one()
    if code:
        print(one)
        return 1

    blocks: list[str] = []
    seen: dict[frozenset[str], str] = {}

    for i, (title, edits, marker) in enumerate(MUTATIONS, 1):
        mutated = pristine.decode()
        shown = ""
        for find, repl in edits:
            if mutated.count(find) != 1:
                print(f"REFUSED: mutation {i} anchor appears {mutated.count(find)} times, not once.")
                return 1
            mutated = mutated.replace(find, repl)
            shown += ("".join(f"  - {ln}\n" for ln in find.strip("\n").splitlines())
                      + "".join(f"  + {ln}\n" for ln in repl.strip("\n").splitlines()))
        SUBJECT.write_text(mutated, encoding="utf-8")
        try:
            landed = marker in SUBJECT.read_text(encoding="utf-8")
            rc, out = run([sys.executable, "-m", "pytest", SUITE, "-q", "-rf"])
        finally:
            SUBJECT.write_bytes(pristine)

        if not landed:
            print(f"REFUSED: mutation {i} marker {marker!r} is not in the file after the edit.")
            return 1
        if rc != 1:
            print(f"REFUSED: mutation {i} exited {rc}; only exit 1 is a suite that RAN and "
                  f"failed.\n{out}")
            return 1
        dead = failed_tests(out)
        if not dead:
            print(f"REFUSED: mutation {i} went red with no FAILED line to name.\n{out}")
            return 1
        if CONTROL in dead:
            print(f"REFUSED: mutation {i} kills the instrument control {CONTROL}, so it broke the "
                  "apparatus rather than demonstrating a property.")
            return 1
        if dead in seen:
            print(f"REFUSED: mutation {i} has the same failure set as {seen[dead]}.")
            return 1
        seen[dead] = f"mutation {i}"

        blocks.append(
            f"\n{'=' * 100}\nMUTATION {i} - {title}\n{'=' * 100}\n"
            f"\nApplied to {SUBJECT.relative_to(ROOT)}:\n\n{shown}\n"
            f"Marker {marker!r} grepped back out of the file after the edit: yes.\n"
            f"Tests killed ({len(dead)}): {', '.join(sorted(dead))}\n"
            f"\n--- verbatim output of `python -m pytest {SUITE} -q -rf` ---\n\n{out}"
        )

    if hashlib.sha256(SUBJECT.read_bytes()).hexdigest() != digest:
        print(f"REFUSED: {SUBJECT} was not restored byte for byte.")
        return 1
    rc, after = run([sys.executable, "-m", "pytest", SUITE, "-q"])
    if rc != 0:
        print(f"REFUSED: the suite is not green after the restore (exit {rc}).\n{after}")
        return 1

    # WHAT NOTHING ABOVE KILLED, SUBTRACTED RATHER THAN RECALLED. The previous draft of this file
    # was closed over with "each assertion is load-bearing"; the arithmetic below is what that
    # sentence should have been, and it is computed from pytest's own collection so it cannot go
    # stale when a test is added.
    #
    # THE UNMEASURED BRANCH PRINTS NO ARITHMETIC AND NO PROSE ABOUT SURVIVORS, and the first repair
    # of this section got that wrong in both directions: the heading formatted "15 of 0" one line
    # above the words NOT MEASURED, and three sentences describing the survivors were emitted
    # unconditionally over a subtraction that had not happened. A branch written against claims
    # stronger than their artefact was making them itself. Found by Fable.
    killed = set(killed_by_the_shipped_file).union(*seen.keys())
    collected, why_not = collected_tests()
    if why_not:
        section = UNMEASURED.format(reason=why_not, killed=len(killed))
    else:
        uncovered = sorted(collected - killed)
        if uncovered != sorted(EXPECTED_UNCOVERED):
            # THE PROSE UNDER THE LIST NAMES THESE THREE BY HAND, so the list moving without the
            # prose moving is exactly the drift this file exists to refuse. It is cheaper to refuse
            # here than to discover a stale paragraph later - and a generator that quietly emitted
            # a new list under an old explanation would be the "six ways" defect a third time.
            print("REFUSED: the uncovered set has moved.\n"
                  f"  expected: {sorted(EXPECTED_UNCOVERED)}\n  measured: {uncovered}\n"
                  "This check compares a frozenset, and updating the frozenset alone satisfies it.\n"
                  "THREE PROSE COPIES NAME THESE TESTS AND NOTHING VERIFIES THEM - move all three\n"
                  "in the same edit:\n"
                  "  - EXPECTED_UNCOVERED, above;\n"
                  "  - the paragraph under the list in the UNCOVERED template, below;\n"
                  "  - the module docstring of tests/test_workflows_parse.py;\n"
                  "  - the closing paragraphs of D-32 in DECISIONS.md.")
            return 1
        section = UNCOVERED.format(
            killed=len(killed), total=len(collected),
            listing="".join(f"  - {name}\n" for name in uncovered) or "  (none)\n")

    OUT.write_text(
        HEADER + one + "\n" + PART_TWO + "".join(blocks) + section
        + FOOTER.format(before=before.strip(), after=after.strip()),
        encoding="utf-8")
    measured = "uncovered set measured" if not why_not else f"uncovered set NOT MEASURED ({why_not})"
    print(f"wrote {OUT.relative_to(ROOT)} - {len(seen)} mutations, all distinct, {measured}")
    return 0


HEADER = f"""RED-034 - the file every gate read, and no parser had ever opened

{evidence_stamp.tree_stamp()}
DATE (UTC): 2026-08-24
SUBJECT   : scripts/verify_workflow_yaml.py, judged by tests/test_workflows_parse.py
LAW       : LAW-WORKFLOWS-PARSE
PRODUCED  : evidence/RED-034-generator.py, checked in beside this file so the runs below can be
            repeated rather than believed.

WHY THIS FILE EXISTS

`66f61ea` was pushed with a local TREE GREEN behind it - 7/7 gates, 642 passed, coverage 92.87% -
and turned `main` RED in the same second it landed. `--only-binary=:all: ` sat in a PLAIN scalar,
`: ` is how YAML spells "the key ended here", and the run GitHub created was concluded in the same
second holding ZERO jobs: nothing in the workflow failed, because nothing in it ever started. The
diagnosis is kept in evidence/RED-031-seven-green-gates-and-a-workflow-that-never-parsed.txt, which
ends by naming the gap and declining to close it - closing it meant either a new dependency in a
hash-pinned set, which D-30 says moves by a DECISION and not by a repair, or another hand-written
rule bolted onto the scanner whose permissiveness is the finding. D-32 is that decision.

WHAT IS BEING SHOWN HERE, IN TWO PARTS

PART ONE is not a mutation and not a fixture. The document {PIN} shipped is fetched out of git and
written back into this tree, and both gates read it: the hand-written scanner reports it CLEAN, the
parser refuses it at line 128, column 69. That pair is L-31 in one screen - a checker more
permissive than the machine it stands in for will certify files that machine cannot run.

PART TWO answers the obvious next question, which is whether the new gate can fail at all
(invariant 5). Twelve mutations, each in the PERMISSIVE direction, each restored byte for byte and
verified by sha256, each with its output captured into its own buffer.

IT WAS SEVEN, AND THE COUNT IS PART OF THE RECORD. D-32 closed over those seven with "each
assertion in the suite is load-bearing", and Fable counted what they did not reach: four whole
tests and several sub-assertions hidden behind an earlier `assert` in the same test. Five mutations
were added over two rounds - the parser's message dropped, its location dropped separately, the
clean line stripped of what it read, the directory listing replaced by a remembered name, and an
absent parser folded into a clean tree one level ABOVE the function that reports it, which no test
on a host WITH PyYAML could have seen. What remains uncovered is COUNTED at the foot of this file,
in TESTS, with the granularity limit named there rather than covered by the word "assertion".

WHERE THE GATE BITES, WHICH PART ONE MAKES LOOK STRONGER THAN IT IS. The runs below are taken at the
DOOR, and that is not incidental: in CI this test cannot catch a broken gates.yml, because a
workflow that does not parse runs no job and the job holding the test never starts. The defect
deletes its own detector - which is how {PIN} produced seven green gates and three green check runs
in the first place. CI catches a broken codeql.yml or scorecard.yml, whose failure does not stop the
gates workflow; scripts/push.sh is the only place the {PIN} case can be refused before it reaches
main. Said here rather than left to be inferred from a transcript that happens to have been taken
locally.
"""

PART_TWO = f"""
{'=' * 100}
PART TWO - the gate is watched to fire, twelve ways
{'=' * 100}

Every mutation below makes `verify_workflow_yaml.py` ACCEPT something it should refuse, because
that is the direction this whole law is about: a stricter approximation announces itself as a false
red on a working file, while a looser one is silent until GitHub refuses a document the gates have
already blessed. `{CONTROL}` is the instrument control - the one assertion that
observes an accepted document - and a mutation killing it would mean the apparatus broke rather
than a property being shown, so the generator refuses that outcome.
"""

UNCOVERED = """
{sep}
WHAT NOTHING HERE KILLED - {killed} of {total} tests were seen to fail, and these were not
{sep}

{listing}
This list is a SUBTRACTION over pytest's own collection, not a remembered figure. The generator
refuses to rewrite this file while the measured set differs from the one it expects, and its refusal
NAMES the four places these three tests are written down - its own `EXPECTED_UNCOVERED`, the
paragraph you are reading, the docstring of the suite, and D-32 - so that a new list cannot appear
under an old explanation, which would be the "six ways" defect a third time. That check compares a
frozenset: updating the frozenset alone satisfies it, and moving the prose is an INSTRUCTION the
refusal prints rather than a property it verifies. Said plainly because the first draft of this
sentence claimed the explanation "cannot outlive the measurement", which one edit to one field
falsifies - the anti-drift repair making the exact claim it was written to end. Found by Fable.

  * `test_the_repaired_form_is_accepted` is the acceptance control, and its absence here is
    STRUCTURAL rather than an omission: this generator runs permissive mutations only and refuses
    any outcome that kills a control, so no red run for it can come out of this file - a red there
    would mean the apparatus broke, not that a property was shown.
  * `test_a_duplicated_key_is_reported_rather_than_silently_resolved` asserts a stated BOUNDARY: a
    duplicated key parses and PyYAML keeps the last one silently. It IS reachable by editing the
    subject - a duplicate-key check would fail it - just not by a PERMISSIVE edit, which is a limit
    of this generator rather than a property of the gate. The first draft of this paragraph said
    "neither is reachable by editing the subject", which was true of the other one only.
  * `test_the_parser_this_gate_needs_is_in_the_set_the_job_installs` asserts a fact about
    `requirements/ci-tests.txt` rather than about the gate, and no edit to the subject can reach it.

WHAT THIS COUNT IS IN, WHICH IS NOT WHAT A READER WILL ASSUME. The unit is TESTS. `failed_tests()`
reads node ids out of pytest's `-rf` summary, so a sub-assertion shadowed by an earlier `assert` in
the same test is invisible to it: the test dies at the first failure and the ones below it are
never reached. Mutations 8, 9, 11 and 12 exist because Fable counted exactly those, and even so the
instrument cannot demonstrate the property at assertion granularity - it can only be said that no
mutation here leaves a whole test standing except the three above. Named rather than implied by the
word "assertion", which is what the previous draft used.
""".replace("{sep}", "=" * 100)

UNMEASURED = """
{sep}
WHAT NOTHING HERE KILLED - NOT MEASURED
{sep}

The subtraction that belongs here was NOT PERFORMED, and no list, count or explanation of survivors
is printed in its place - an unmeasured residue described in the words of a measured one would be
the exact defect this file is evidence for.

  reason: {reason}

{killed} tests were seen to fail across the runs above, which stands. What cannot be stated is what
that leaves, because the denominator was never read.
""".replace("{sep}", "=" * 100)

FOOTER = """
{sep}
BASELINE - the suite before any mutation
{sep}

{before}

{sep}
RESTORED - the subject back to its committed bytes, the suite green again
{sep}

{after}
""".replace("{sep}", "=" * 100)


if __name__ == "__main__":
    raise SystemExit(main())
