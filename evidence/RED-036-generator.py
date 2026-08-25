#!/usr/bin/env python3
"""Produces evidence/RED-036-a-ladder-that-climbed-on-a-control-that-had-said-nothing.txt.

THE SUBJECT IS A GATE THAT REPLACED A CONSTANT. `NOTE_CEILING` was the literal `3` and could only be
broken by editing a digit; D-35 replaced it with a ladder whose height is read from
`web/notes/reach.json`, and a reading can now be mis-read in two directions, not one. Most of the
mutations below over-read it - open a step nothing measured, publishing more pages than anything has
said may be published - but mutation 9 misfiles one silence under the other's name and mutation 10
stops the ladder climbing at all, a gate nothing can pass being reported the same as a gate nothing
has passed yet: the flattering direction, and just as false a report of what was measured. So the
mutations below are not "what if somebody edits the number" - they are ten ways a reading can be
mis-read, or the two copies of the rule (the build and the test) can drift apart.

TWO PARTS.

  1. THE CLOSED STEP, MEASURED ON THE REAL GATE. The first rung is shut today: `crawl_stats` reads
     0 rows for this site against 6 at a control that proves the call can report them. Two extra
     note sources are put into `web/notes/src/`, taking the corpus to four, and both halves of the
     law are asked - `loadNotes()` in the build, which must throw, and the suite, which must go red.
     The sources are removed afterwards and the directory is compared file by file against its
     sha256 map. This is the red run the task asks to be kept: the step is closed, the ceiling is
     three, and the fourth note does not reach a reader.

  2. TEN MUTATIONS OF `web/notes/emit.mjs`, each a single anchored edit, each asserted to leave
     the instrument control green and to kill a set of tests no other mutation killed. Two of them -
     1 and 6 - are the T-B10 defect rebuilt on the other side of the same account: a state asserted
     about an instrument on the strength of no evidence about the instrument.

WHAT THIS FILE DOES NOT DO. It never runs `~/orchestra/deploy.sh` and publishes nothing. It writes
two files into the working tree and removes them; if it dies between those two acts the two files
are named `zz-red036-fixture-*.md` so that the wreckage is identifiable as wreckage, which is what
CLAUDE.md's rollback procedure asks of anything that leaves untracked files behind.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402 - T-S14, every artefact names the tree it was captured against

OUT = ROOT / "evidence" / "RED-036-a-ladder-that-climbed-on-a-control-that-had-said-nothing.txt"
SUBJECT = ROOT / "web" / "notes" / "emit.mjs"
SRC = ROOT / "web" / "notes" / "src"
SUITE = "tests/test_notes_ceiling.py"
CONTROL = "test_the_reading_in_this_tree_is_control_paired_at_all"
"""INSTRUMENT CONTROL. It reads `reach.json` in Python and never touches `emit.mjs`, so no mutation
below may kill it. One that does has broken the apparatus rather than demonstrated a property."""

FIXTURES = ("zz-red036-fixture-a.md", "zz-red036-fixture-b.md")
FIXTURE_BODY = ("---\n{\"slug\": \"zz-red036-fixture\"}\n---\nA fixture source, written by "
                "evidence/RED-036-generator.py and removed by it. If this file is in the tree, that "
                "generator died between writing it and its own `finally`.\n")


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout + p.stderr


def failed_tests(output: str) -> frozenset[str]:
    """Node ids out of pytest's `-rf` summary, which reads `FAILED <nodeid> - <message>`."""
    ids = set()
    for line in output.splitlines():
        if not line.startswith("FAILED ") or "::" not in line:
            continue
        ids.add(line[len("FAILED "):].split(" - ", 1)[0].strip().split("::", 1)[1])
    return frozenset(ids)


def src_map() -> dict[str, str]:
    """Every note source and its digest. The restore is compared against this rather than against a
    count: two files removed and two different ones left behind is a clean count and a wrecked tree."""
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SRC.glob("*.md"))}


# (title, [(find, replace)], marker)
MUTATIONS: list[tuple[str, list[tuple[str, str]], str]] = [
    (
        "THE T-B10 DEFECT REBUILT: the control pair stops being consulted, so rows for this site "
        "open a step while nothing has shown the call able to report them",
        [('  if (c.control_proven_capable !== true)\n'
          '    return { open: false, state: "capability_unproven", detail: '
          '`${counter}: the control did not prove this call can see the quantity` };\n',
          "  // MUTATION-1\n")],
        "MUTATION-1",
    ),
    (
        "a zero row count opens the step - the whole ladder climbed by an instrument answering "
        "that nothing qualified, which is the literal reading of the condition D-35 replaced",
        [('  if (c.count === 0)\n'
          '    return { open: false, state: "nothing_qualified", detail: '
          '`${counter}: the call sees, and no row qualified for this site` };\n',
          "  // MUTATION-2\n")],
        "MUTATION-2",
    ),
    (
        "a reading nobody took is climbed as though it had been taken - a missing file defaulting "
        "to the top of the ladder instead of the floor (invariant 1)",
        [("  let climbing = reach.state === \"measured\";",
          "  let climbing = true;   // MUTATION-3")],
        "MUTATION-3",
    ),
    (
        "the ladder in the build moves and the ladder in the test does not - the drift the watchdog "
        "exists to catch, and the one an editor wanting a fourth note would actually perform",
        [('  { ceiling: 7, opens_on: "crawl_stats", link: "a crawl of this site" },',
          '  { ceiling: 8, opens_on: "crawl_stats", link: "a crawl of this site" },   // MUTATION-4')],
        "MUTATION-4",
    ),
    (
        "the reading stops having to be ABOUT this site, so the control property's 6 crawl rows and "
        "64 query rows decide our ceiling",
        [("  if (doc.subject !== REACH_SUBJECT)\n"
          "    return { state: \"unreadable\", why: `reading is about ${doc.subject}, "
          "not ${REACH_SUBJECT}`, chain: {} };\n",
          "  // MUTATION-5\n")],
        "MUTATION-5",
    ),
    (
        "a counter that is not in the reading at all opens the step it was supposed to gate - "
        "`check_did_not_run` promoted to a measurement, one branch away from mutation 1",
        [('  if (c === undefined) return { open: false, state: "check_did_not_run", '
          'detail: `${counter} is not in the reading` };',
          '  if (c === undefined) return { open: true, state: "check_did_not_run", '
          'detail: `${counter} is not in the reading` };   // MUTATION-6')],
        "MUTATION-6",
    ),
    (
        "the ladder becomes a menu: a closed rung no longer blocks the ones above it, so an "
        "impressions row would carry the corpus to fifteen without a crawl row ever being read",
        [("    else climbing = false;", "    // MUTATION-7")],
        "MUTATION-7",
    ),
    (
        "a count that is not a number stops being unreadable, and `null` - which is what the probe "
        "writes when a payload carries no countable rows - opens the step",
        [('  if (typeof c.count !== "number")\n'
          '    return { open: false, state: "unreadable", detail: '
          '`${counter}: count is ${JSON.stringify(c.count)}, not a number` };\n',
          "  // MUTATION-8\n")],
        "MUTATION-8",
    ),
    (
        "the two silences are collapsed into one: a reading nobody took is filed under the name "
        "for a reading that did not parse, and the red build can no longer say which happened",
        [('  if (!existsSync(path)) return { state: "check_did_not_run", '
          'why: `no reading at ${path}`, chain: {} };',
          '  if (!existsSync(path)) return { state: "unreadable", '
          'why: `no reading at ${path}`, chain: {} };   // MUTATION-9')],
        "MUTATION-9",
    ),
    (
        "the ladder stops climbing at all - the wall in a ladder's clothes. Every step reports open "
        "and the ceiling never leaves the floor, which is the failure mode that flatters us: a gate "
        "nothing can pass looks identical to a gate nothing has passed yet",
        [("    if (s.open) ceiling = rung.ceiling;",
          "    if (s.open) ceiling = ceiling;   // MUTATION-10")],
        "MUTATION-10",
    ),
]


def part_one() -> tuple[str, int, frozenset[str]]:
    """The closed step, with a fourth and fifth note standing on top of it."""
    before_map = src_map()
    if len(before_map) >= 3:
        return (f"REFUSED: {SRC.relative_to(ROOT)} already holds {len(before_map)} sources, so two "
                "more would not be the first crossing of the ceiling and this part measures "
                "something other than what it says.\n", 1, frozenset())

    written: list[Path] = []
    try:
        for name in FIXTURES:
            p = SRC / name
            if p.exists():
                return (f"REFUSED: {p.relative_to(ROOT)} already exists.\n", 1, frozenset())
            p.write_text(FIXTURE_BODY, encoding="utf-8")
            written.append(p)
        count = len(src_map())
        build_rc, build_out = run([
            "node", "--input-type=module", "-e",
            "import {loadNotes, NOTE_CEILING, NOTE_STEP} from './web/notes/emit.mjs';"
            "console.log('ceiling=' + NOTE_CEILING + ' step=' + JSON.stringify(NOTE_STEP.steps[0]));"
            "try { loadNotes(); console.log('BUILD RETURNED - the ceiling did not refuse'); }"
            "catch (e) { console.log('BUILD REFUSED: ' + e.message); process.exit(3); }"])
        suite_rc, suite_out = run([sys.executable, "-m", "pytest", SUITE, "-q", "-rf"])
    finally:
        for p in written:
            p.unlink(missing_ok=True)

    if src_map() != before_map:
        return (f"REFUSED: {SRC.relative_to(ROOT)} was not restored - digests differ.\n",
                1, frozenset())
    if build_rc != 3:
        return (f"REFUSED: the build exited {build_rc}; 3 is the only reading that means "
                f"`loadNotes()` ran and threw.\n{build_out}", 1, frozenset())
    if suite_rc != 1:
        return (f"REFUSED: the suite exited {suite_rc} over {count} sources.\n{suite_out}",
                1, frozenset())

    return (
        f"\n{'=' * 100}\n"
        f"PART ONE - the step is closed, and the fourth note does not reach a reader\n"
        f"{'=' * 100}\n\n"
        f"Nothing is mutated here. The gate is the shipped one and the reading is the shipped one:\n"
        f"`crawl_stats` answers for both sites, returns 6 rows for the control property and 0 for\n"
        f"this one, so the first rung is `nothing_qualified` and the ceiling is the floor. Two\n"
        f"fixture sources are added to web/notes/src/, taking the corpus from "
        f"{len(before_map)} to {count}.\n"
        f"\n--- `node -e \"loadNotes()\"` ---   exit={build_rc}\n\n{build_out}"
        f"\n--- `python -m pytest {SUITE} -q -rf` ---   exit={suite_rc}\n\n{suite_out}"
        f"\nBoth fixtures removed; every remaining source compared against its sha256: unchanged.\n",
        0,
        failed_tests(suite_out),
    )


def main() -> int:
    pristine = SUBJECT.read_bytes()
    digest = hashlib.sha256(pristine).hexdigest()

    rc, before = run([sys.executable, "-m", "pytest", SUITE, "-q"])
    if rc != 0:
        print(f"REFUSED: the suite is not green before anything is touched (exit {rc}).\n{before}")
        return 1

    one, code, killed_by_the_fourth_note = part_one()
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
            f"\n--- verbatim output of `python -m pytest {SUITE} -q -rf` ---\n\n{out}")

    if hashlib.sha256(SUBJECT.read_bytes()).hexdigest() != digest:
        print(f"REFUSED: {SUBJECT} was not restored byte for byte.")
        return 1
    rc, after = run([sys.executable, "-m", "pytest", SUITE, "-q"])
    if rc != 0:
        print(f"REFUSED: the suite is not green after the restore (exit {rc}).\n{after}")
        return 1

    killed = set(killed_by_the_fourth_note).union(*seen.keys())
    rc, collected_out = run([sys.executable, "-m", "pytest", SUITE, "-q", "--collect-only"])
    if rc != 0:
        section = (f"\n{'=' * 100}\nWHAT NOTHING ABOVE KILLED\n{'=' * 100}\n\n"
                   f"NOT MEASURED: pytest exited {rc} enumerating {SUITE}, so the subtraction was\n"
                   "never performed. That is check_did_not_run, and it is not the same as a list\n"
                   f"that came back empty. {len(killed)} distinct tests were killed above.\n")
    else:
        collected = {ln.split("::", 1)[1].strip()
                     for ln in collected_out.splitlines() if ln.startswith(SUITE) and "::" in ln}
        uncovered = sorted(collected - killed)
        section = (
            f"\n{'=' * 100}\nWHAT NOTHING ABOVE KILLED\n{'=' * 100}\n\n"
            f"{len(killed)} of {len(collected)} collected tests were killed by part one or by a "
            "mutation.\nThe rest are named rather than counted, because a survivor is either a test "
            "that cannot\nfail or a hole in this list, and both are findings:\n\n"
            + ("".join(f"  - {n}\n" for n in uncovered) or "  (none)\n"))

    OUT.write_text(HEADER + one + PART_TWO + "".join(blocks) + section
                   + FOOTER.format(before=before.strip(), after=after.strip()), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} - {len(seen)} mutations, all distinct")
    return 0


HEADER = f"""RED-036 - a ladder that climbed on a control that had said nothing

{evidence_stamp.tree_stamp()}
DATE (UTC): 2026-08-24
SUBJECT   : web/notes/emit.mjs, judged by tests/test_notes_ceiling.py
LAW       : LAW-NOTES-CEILING
DECISION  : D-35
PRODUCED  : evidence/RED-036-generator.py, checked in beside this file so the runs below can be
            repeated rather than believed.

WHY THIS FILE EXISTS

Until D-35 the ceiling was `export const NOTE_CEILING = 3;` and there was exactly one way past it:
edit a digit, which a watchdog test compared against. D-35 replaced the digit with a ladder read
from a measurement, and that trade is not free. A number can only be edited; a measurement can be
over-read - a zero taken for a row, a silence taken for a zero, an absent file taken for a silence,
another property's traffic taken for ours. Every one of those is a way to publish more pages than
anything has said may be published, and none of them is a digit anybody typed.

T-B10 removed exactly this class of error from `~/orchestra/bing_probe.py`: a control that had
returned zero was allowed to settle a question about the instrument, and the state published for it
asserted blindness on no evidence. The ladder now consumes that probe's output. Mutations 1 and 6
below are that defect rebuilt on this side of the copy - a step opened by a reading that never
proved anything - and the suite is red under both.
"""

PART_TWO = f"""
{'=' * 100}
PART TWO - {len(MUTATIONS)} mutations of the gate
{'=' * 100}

Each is a single anchored edit to web/notes/emit.mjs, applied to the real file and reverted. The
generator refuses to write this evidence unless every anchor matched exactly once, every marker was
read back out of the file after the edit, every mutation left the instrument control
`{CONTROL}` green, and no two mutations killed the same set of
tests - a mutation with a duplicate failure set demonstrates nothing the earlier one did not.
"""

FOOTER = f"""
{'=' * 100}
GREEN BEFORE AND AFTER
{'=' * 100}
""" + """
Before anything was touched:

{before}

After the last mutation was reverted and web/notes/emit.mjs compared against its sha256:

{after}
"""


if __name__ == "__main__":
    sys.exit(main())
