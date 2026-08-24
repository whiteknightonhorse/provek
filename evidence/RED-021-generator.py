#!/usr/bin/env python3
"""Produces evidence/RED-021-a-deploy-gate-that-reads-less-every-release.txt.

    python3 evidence/RED-021-generator.py            # writes the artefact beside this file
    python3 evidence/RED-021-generator.py --check    # runs everything, writes nothing

WHAT IT ESTABLISHES. That the two repairs T-C4 made to the deploy check can fail (invariant 5).
Both are about a list of addresses, and neither is about a value in it.

T-C4 published the note surface and added two routes to `CHECKS` in `scripts/verify_live.sh`. The
suite went red - not because the routes were wrong, but because `tests/test_verify_live_reads_the_
function.py` carried its own hand-written copy of that list in `HEALTHY`, and the copies had just
drifted. Patching the literal would have been the repair L-20 refuses: it returns the file to the
day before the drift and leaves standing the thing that let it drift, which is that nothing compared
the two copies. So `HEALTHY` is now READ OUT OF the script and there is one list.

THAT FIX BUYS A SECOND HOLE, AND MUTATIONS 3 AND 4 ARE ABOUT IT. A derived fixture shrinks with its
source: delete an address from `CHECKS` and `HEALTHY` loses it too, every assertion in the file goes
on passing, and `DEPLOY CONFIRMED` quietly covers less of the site than it did last week. That is
the same silence that let `GET /api/apply` answer 404 through four confirmed deployments (L-25), so
a floor was added under the derived list - a subset assertion, which fires when something
load-bearing stops being read and stays quiet when addresses are merely added.

TWO CLASSES OF RED, AND THEY ARE NOT REPORTED AS ONE. RED-020's generator requires exit code 1 from
pytest, on the ground that any other nonzero is an instrument that asserted nothing. That rule is
right and it does not fit mutations 1 and 2 here, whose whole subject is a fixture REFUSING TO BE
BUILT: when the parser cannot find the address list, the module raises at import and pytest exits 2
with a collection error. Reading that as "the gate is armed" would be invariant 1 inside the tool
kept to defend invariant 1 - a suite that never ran, filed under the same word as a suite that ran
and failed. So each mutation declares which class it belongs to, the class is checked, and the
REFUSAL MESSAGE is required verbatim in the output. A collection error that says something else is
an ordinary crash and is refused.

WHAT IT REFUSES TO WRITE THE ARTEFACT OVER, inherited from RED-017/018/020 because each caught a
real draft there:
  * a mutation whose anchor is not unique, or which leaves the file unchanged - an edit that did
    not land is a transcript about a pristine file;
  * a mutation that does not produce its DECLARED class of failure;
  * a mutation that does not name the expected test or refusal string;
  * for the assertion class, a mutation that killed the INSTRUMENT CONTROL - see CONTROL below;
  * two mutations with the same failure set, which would mean one proves nothing the other did not
    (the transposition RED-013 was corrected for);
  * a file not restored byte for byte, or the suite not green again afterwards.

It writes the file itself rather than being redirected into it: a shell truncates its target before
Python starts, so every refusal above would empty the committed artefact on its way to declining to
replace it (the defect RED-017's generator shipped and names).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_live.sh"
SUITE_FILE = ROOT / "tests" / "test_verify_live_reads_the_function.py"
SUITE = "tests/test_verify_live_reads_the_function.py"
ARTEFACT = ROOT / "evidence" / "RED-021-a-deploy-gate-that-reads-less-every-release.txt"

CONTROL = "test_the_probe_never_writes"
"""THE TEST THAT PROVES THE SUITE STILL RAN AND STILL DROVE THE SCRIPT.

RED-017 shipped a mutation that was an `if (false) {` facing a `catch`: the module stopped parsing,
every test died, and eight reds were filed under a heading claiming one property had been removed.
A red run is evidence only if the subject was still running when it went red (L-28). For the
assertion-class mutations below the script must still be executed against a stub origin, and this
test is the one that can only pass if that happened - it reads the METHODS the origin was asked.
"""

REFUSED_TO_BUILD = "refused-to-build"
ASSERTION_RED = "assertion-red"


def _checks_block() -> str:
    """The whole `CHECKS=( ... )` array, read from the pristine script.

    Mutation 1 needs to empty the list, and spelling the addresses out here would put a NINTH copy
    of them inside the tool whose subject is that there were two. Read once, at import, while the
    file is still pristine; if it were read later a previous mutation could define the anchor.
    """
    m = re.search(r"^CHECKS=\(\n.*?^\)", SCRIPT.read_text(encoding="utf-8"), re.S | re.M)
    if not m:
        sys.stderr.write(f"REFUSED: no CHECKS=( ... ) block in {SCRIPT.name} to mutate\n")
        raise SystemExit(2)
    return m.group(0)


CHECKS_BLOCK = _checks_block()

MUTATIONS = [
    {
        "name": "every address is removed, leaving the array present but empty",
        "klass": REFUSED_TO_BUILD,
        "file": SCRIPT,
        # Resolved from the pristine file at run time: the whole `CHECKS=( ... )` block. Written as
        # a literal it would be a ninth copy of the address list inside the tool that exists
        # because there were two.
        "anchor": CHECKS_BLOCK,
        "replace": "CHECKS=(\n  # every address removed by RED-021 mutation 1\n)",
        "expect": "CHECKS parsed to zero addresses",
        "why": (
            "An empty list is the shape that makes every assertion in the suite vacuous: no\n"
            "  address is checked, nothing can disagree, and the run is green. The fixture must\n"
            "  refuse to be built rather than hand back an empty dict - a parser that returns\n"
            "  nothing must never read as 'every address is fine'."
        ),
    },
    {
        "name": "the array is renamed, so the parser finds nothing to read",
        "klass": REFUSED_TO_BUILD,
        "file": SCRIPT,
        "anchor": "CHECKS=(\n",
        "replace": "CHECKS_RENAMED=(\n",
        "expect": "no CHECKS=( ... ) array to read",
        "why": (
            "The fixture now depends on a shape inside another file. If that shape moves, the\n"
            "  honest answer is 'I could not read the list', and the dangerous one is 'the list is\n"
            "  empty'. This is L-10 in a test fixture: an instrument that cannot see the quantity\n"
            "  must not report absence of it."
        ),
    },
    {
        "name": "the note index is dropped from the address list",
        "klass": ASSERTION_RED,
        "file": SCRIPT,
        "anchor": '  "/method/notes/:200"\n',
        "replace": "",
        "expect": "test_the_address_list_cannot_silently_shrink",
        "why": (
            "The defect the floor exists for, and the one the derived fixture would otherwise have\n"
            "  introduced. Before the floor, deleting this line deleted it from HEALTHY too and the\n"
            "  whole suite stayed green over a deploy check that had stopped reading the note\n"
            "  surface entirely - a page can 404 on the live site with every gate reporting clean."
        ),
    },
    {
        "name": "the page carrying the intake form is dropped from the address list",
        "klass": ASSERTION_RED,
        "file": SCRIPT,
        "anchor": '  "/apply/:200"\n',
        "replace": "",
        "expect": "test_the_address_list_cannot_silently_shrink",
        "why": (
            "THE FLOOR'S FIRST DRAFT WAS GREEN OVER THIS EDIT, and mutation 3 could not have found\n"
            "  it: that one deletes a route the draft happened to pin, so it fired for the same\n"
            "  reason a test passes on the one example it was built from. Four of the eight\n"
            "  addresses were unpinned, and `/apply/` is the sharpest of them - it is the page the\n"
            "  intake form lives on, so the endpoint was protected while the door to it was not.\n"
            "  Found by Fable, refuting the change that added the floor."
        ),
    },
    {
        "name": "the intake endpoint is expected to answer 200",
        "klass": ASSERTION_RED,
        "file": SCRIPT,
        "anchor": '  "/api/apply:405"\n',
        "replace": '  "/api/apply:200"\n',
        "expect": "test_the_floor_pins_the_code_and_not_only_the_path",
        "why": (
            "The address stays in the list and the gate still goes through the motions, which is\n"
            "  why the floor pins the CODE and not only the path. T-H1's defect was a static 404\n"
            "  page served where a Function should be; an expectation of 200 there passes on\n"
            "  exactly the deployment that has no Function at all."
        ),
    },
]


def run_suite() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", SUITE, "-q", "-rf"],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )


def failed_tests(out: str) -> set[str]:
    return {
        ln.split("::")[1].split()[0]
        for ln in out.splitlines()
        if ln.startswith("FAILED") and "::" in ln
    }


def failure_lines(out: str) -> tuple[str, ...]:
    """The FAILED lines verbatim, message and all - the fingerprint the distinctness check uses.

    IT USED TO BE THE SET OF TEST NAMES, AND THAT WAS TOO COARSE RATHER THAN TOO STRICT. Two
    mutations that delete different addresses both fail `test_the_address_list_cannot_silently_
    shrink` and were refused as duplicates, although their output differs in the part that matters:
    each names the address that went missing. Widening the floor to cover all eight addresses is
    what made them collide, so the coarse fingerprint would have blocked exactly the fix for the
    blind spot Fable found.

    This is STRICTER, not looser, and the direction is worth stating because relaxing a guard to
    let one's own evidence through is the failure this file is otherwise about. RED-013's defect
    was a transcript carrying another run's output; that produces byte-identical failure lines and
    is still caught here. What is no longer caught is the case where the same assertion fires with
    a demonstrably different message, which was never the thing being guarded against.
    """
    # The `E ` lines, which carry the assertion's own message and therefore the ADDRESS that went
    # missing. The `FAILED` summary lines under `-q` carry only test names and are identical for
    # any two deletions, which is what made the first version of this too coarse.
    return tuple(sorted(ln.strip() for ln in out.splitlines() if ln.startswith("E ")))


def die(msg: str) -> None:
    sys.stderr.write(f"REFUSED: {msg}\n")
    raise SystemExit(2)


def main() -> int:
    check_only = "--check" in sys.argv

    green = run_suite()
    if green.returncode != 0:
        die("the suite is not green before any mutation; there is nothing to prove a red against")

    blocks, seen_failures = [], {}
    for i, mut in enumerate(MUTATIONS, 1):
        target: Path = mut["file"]
        original = target.read_text(encoding="utf-8")
        if original.count(mut["anchor"]) != 1:
            die(f"mutation {i}: anchor is not unique in {target.name} "
                f"({original.count(mut['anchor'])} occurrences) - the edit would be ambiguous")

        mutated = original.replace(mut["anchor"], mut["replace"])
        if mutated == original:
            die(f"mutation {i}: the edit left {target.name} unchanged")
        target.write_text(mutated, encoding="utf-8")
        try:
            run = run_suite()
            out = run.stdout + run.stderr
        finally:
            target.write_text(original, encoding="utf-8")
            if target.read_text(encoding="utf-8") != original:
                die(f"mutation {i}: {target.name} was not restored byte for byte")

        if mut["klass"] == REFUSED_TO_BUILD:
            # A fixture that cannot be built is a COLLECTION error, not a failing assertion. Exit 1
            # here would mean the module imported fine and something else broke - a different fact.
            if run.returncode != 2:
                die(f"mutation {i}: expected pytest to exit 2 (collection error, the fixture "
                    f"refusing to be built) and it exited {run.returncode}")
            if mut["expect"] not in out:
                die(f"mutation {i}: the refusal did not name itself - {mut['expect']!r} is absent, "
                    f"so this is an ordinary crash and not the guard firing")
            fingerprint = f"collection-error:{mut['expect']}"
        else:
            if run.returncode != 1:
                die(f"mutation {i}: expected pytest to exit 1 (ran and failed) and it exited "
                    f"{run.returncode} - any other nonzero asserted nothing")
            failures = failed_tests(out)
            if mut["expect"] not in failures:
                die(f"mutation {i}: {mut['expect']} did not fail; the gate is not armed against "
                    f"this edit (failures were {sorted(failures)})")
            if CONTROL in failures:
                die(f"mutation {i}: the instrument control {CONTROL} died, so the suite was not "
                    f"exercising the script and this red establishes nothing (L-28)")
            fingerprint = "failed:" + "|".join(failure_lines(out))

        if fingerprint in seen_failures:
            die(f"mutation {i}: identical failure set to mutation {seen_failures[fingerprint]}; "
                f"one of the two proves nothing the other did not (RED-013)")
        seen_failures[fingerprint] = i

        blocks.append(
            f"{'=' * 98}\n"
            f"MUTATION {i} [{mut['klass']}] - {mut['name']}\n"
            f"{'=' * 98}\n\n"
            f"FILE:    {target.relative_to(ROOT)}\n"
            f"REMOVED: {mut['anchor']!r}\n"
            f"ADDED:   {mut['replace']!r}\n\n"
            f"WHY THIS MUTATION:\n  {mut['why']}\n\n"
            f"pytest exit code: {run.returncode}\n\n"
            f"Everything below this line is verbatim tool output.\n"
            f"{'-' * 98}\n{out.rstrip()}\n"
        )

    restored = run_suite()
    if restored.returncode != 0:
        die("the suite is not green after the mutations were restored")

    header = (
        f"RED-021 - a deploy gate that reads less every release\n"
        f"{'=' * 98}\n\n"
        f"Regenerate with:  python3 evidence/RED-021-generator.py\n"
        f"Verify with:      python3 evidence/RED-021-generator.py --check\n\n"
        f"SUBJECT: {SUITE}\n"
        f"         scripts/verify_live.sh\n\n"
        f"T-C4 published the first method note and added its two routes to the live check. The\n"
        f"suite went red on the addition, because the address list existed twice - once in the\n"
        f"script and once as a hand-written HEALTHY fixture beside the tests - and nothing had ever\n"
        f"compared them. The repair was not to patch the literal (L-20: the finding in a divergence\n"
        f"between two copies is the absence of the comparison, not the value that differed) but to\n"
        f"read the fixture out of the script, so there is one list.\n\n"
        f"That repair introduces its own hole, and half of this file is about it. A derived fixture\n"
        f"SHRINKS WITH ITS SOURCE: an address deleted from the script disappears from the fixture\n"
        f"too, and every assertion here keeps passing over a deploy check that reads less of the\n"
        f"site than it used to. So a floor sits under the derived list, asserting that the\n"
        f"load-bearing addresses are still in it, and pinning the CODE as well as the path.\n\n"
        f"THE FOUR MUTATIONS BELOW ARE OF TWO CLASSES, AND THE DISTINCTION IS LOAD-BEARING:\n\n"
        f"  [{REFUSED_TO_BUILD}]  the parser cannot read the list, so the fixture refuses to exist\n"
        f"                      and pytest exits 2 with a collection error. This is NOT a failing\n"
        f"                      assertion and is not filed as one - a suite that never ran and a\n"
        f"                      suite that ran and failed are two states of the world. Each is\n"
        f"                      required to print its own refusal message verbatim; a collection\n"
        f"                      error saying anything else is an ordinary crash and is refused.\n\n"
        f"  [{ASSERTION_RED}]     the suite runs, drives the script against a stub origin, and one\n"
        f"                      named test fails (pytest exit 1). The instrument control\n"
        f"                      {CONTROL} must SURVIVE each of these, because it\n"
        f"                      can only pass if the script was really executed - a red produced by\n"
        f"                      a suite that stopped running proves nothing (L-28).\n\n"
        f"Every mutation was applied to a clean tree, run alone, and restored byte for byte before\n"
        f"the next. The four failure sets are DISTINCT, which the generator checks rather than\n"
        f"asserts: identical output from different mutations is how RED-013 shipped a transcript\n"
        f"belonging to a different run.\n\n"
    )

    body = header + "\n".join(blocks)
    if check_only:
        print(f"--check: {len(MUTATIONS)} mutations, each produced its declared class of failure, "
              f"controls held, files restored, suite green again")
        return 0
    ARTEFACT.write_text(body, encoding="utf-8")
    print(f"wrote {ARTEFACT.relative_to(ROOT)} ({len(body)} bytes, {len(MUTATIONS)} mutations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
