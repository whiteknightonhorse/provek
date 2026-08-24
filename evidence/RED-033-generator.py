#!/usr/bin/env python3
"""Produces evidence/RED-033-a-lock-that-was-never-taken-reported-as-contention.txt.

It establishes that LAW-BUDGET-LOCK-UNDER-THE-PROJECT can fail (invariant 5) in each direction it
holds, by applying one mutation at a time to a pristine copy of `scripts/run_budgeted.sh`, proving
the edit landed, running the suite with its output captured SEPARATELY, and restoring the file byte
for byte before the next one. Written in RED-032-generator.py's form and refusing on the same
conditions, each of them earned by a defect this project has already shipped once:

  * a mutation that does not go red;
  * a mutation whose marker cannot be grepped back out of the file afterwards - the edit must be
    proven to have landed, not assumed from the fact that a string was replaced;
  * a pytest that did not RUN. Only exit 1 is a suite that ran and failed; exit 2 is a file that no
    longer parses, and reading any nonzero exit as "red" is invariant 1 inside the instrument;
  * a mutation that kills the instrument control. `test_the_work_runs_when_the_slot_is_free` is
    the only test here that observes a SUCCESSFUL run, and a mutation taking it down has broken
    the apparatus rather than demonstrated a property. It is deliberately the smallest test in the
    suite so that mutation 1 - which is the whole original file - leaves it standing;
  * two mutations with the same failure set;
  * a subject not restored byte for byte, or a suite not green afterwards.

MUTATION 1 IS NOT WRITTEN OUT HERE, IT IS FETCHED FROM HISTORY. The pre-repair script is read back
out of commit e7df7b3 rather than retyped into this file, so the first block below is the bytes
this project actually shipped for five days and not a reconstruction of them that could flatter the
repair by being subtly worse than the original. Retyping it would be exactly the closing-report
defect L-30 records, moved into the evidence corpus.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "RED-033-a-lock-that-was-never-taken-reported-as-contention.txt"
SUITE = "tests/test_run_budgeted_names_its_refusals.py"
SUBJECT = ROOT / "scripts" / "run_budgeted.sh"

PIN = "e7df7b3166b77bac9df42705bc4e82245c4f23c4"   # the commit that still carried the defect


def run(cmd: list[str]) -> tuple[int, str]:
    """One command, one buffer. Nothing here is appended to a shared stream (L-26, RED-013)."""
    done = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=600, check=False)
    return done.returncode, done.stdout + done.stderr


def original_from_history() -> str | None:
    """The shipped pre-repair script, or None if git could not be asked.

    None is a third state and main() treats it as one: "history says the original was different"
    and "we could not read history" are different facts, and silently substituting a retyped copy
    for the second would put an unverified artefact into the evidence corpus.
    """
    done = subprocess.run(["git", "show", f"{PIN}:scripts/run_budgeted.sh"],
                          cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
    return done.stdout if done.returncode == 0 else None


OPEN_GUARD = ('exec 9>"$LOCK"\nopened=$?\n'
              '[ "$opened" -eq 0 ] || refuse "the lock file $LOCK could not be opened for writing"')

IDENTITY_GUARD = ('held=$(readlink -- /proc/self/fd/9 2>/dev/null) || held=""\n'
                  '[ "$held" = "$LOCK" ] || \\\n'
                  "  refuse \"descriptor 9 is open on '${held:-nothing}', not on the lock this "
                  'script named ($LOCK)"')


# (title, edits, marker). edits is None for "replace the whole file with the historical original",
# otherwise a LIST of (find, replace) pairs applied in order.
#
# A LIST RATHER THAN ONE PAIR, BECAUSE THE FIRST DRAFT OF MUTATION 5 DID NOT GO RED. It removed the
# check on the open and left the descriptor-identity check three lines below still standing, which
# caught the same case by a different route, and the generator refused the file - correctly, and
# for the reason it exists. Two guards that overlap can only be shown to be load-bearing by
# removing them together, and a mutation that quietly fails to reproduce its own defect is the
# false green this whole apparatus is built to refuse.
def mutations(original: str) -> list[tuple[str, list[tuple[str, str]] | None, str]]:
    return [
        (
            "the script exactly as it shipped - a fixed name in the host's shared /tmp, and two "
            "outcomes where there are three",
            None,
            "LOCK=/tmp/incubator.slot.lock",
        ),
        (
            "the lock returns to the shared directory and nothing else changes, so the guarantee "
            "is derived from a path ten projects can reach",
            [('STATE="$ROOT/.state"', "STATE=/tmp   # MUTATION-2")],
            "MUTATION-2",
        ),
        (
            "an instrument that did not run is folded back into the deferral branch - the refusal "
            "wearing the face of contention",
            [('  *) refuse "flock exited $rc, so the slot was never tested - this is '
              "not_measured, not 'free'\" ;;",
              '  *) echo "DEFERRED: the slot is held by another run (concurrency=1). This is a '
              'finding, not silence." >&2   # MUTATION-3\n     exit 75 ;;')],
            "MUTATION-3",
        ),
        (
            "the descriptor is no longer resolved back to the path the script named, so a lock "
            "that is a SYMLINK elsewhere is taken and reported as success",
            [(IDENTITY_GUARD, 'held="$LOCK"   # MUTATION-4')],
            "MUTATION-4",
        ),
        (
            "BOTH guards on the open are removed, which is the silent one: with descriptor 9 "
            "arriving open, the work runs to completion, exit 0, no lock and no error",
            [(OPEN_GUARD, 'exec 9>"$LOCK"   # MUTATION-5'),
             (IDENTITY_GUARD, "# MUTATION-5: the identity check goes with it")],
            "MUTATION-5",
        ),
        (
            "the refusal is printed and the exit status says success - the message is right and "
            "every caller that reads a status is told the budget held",
            [("  exit 70\n}", "  exit 0   # MUTATION-6\n}")],
            "MUTATION-6",
        ),
    ]


def failed_tests(output: str) -> frozenset[str]:
    """Node ids out of pytest's `-rf` summary, which reads `FAILED <nodeid> - <message>`."""
    ids = set()
    for line in output.splitlines():
        if not line.startswith("FAILED ") or "::" not in line:
            continue
        nodeid = line[len("FAILED "):].split(" - ", 1)[0].strip()
        ids.add(nodeid.split("::", 1)[1])
    return frozenset(ids)


def main() -> int:
    original = original_from_history()
    if original is None:
        print(f"REFUSED: git could not be asked for {PIN}:scripts/run_budgeted.sh, so the "
              "pre-repair script is NOT MEASURED - which is not the same as absent, and this file "
              "will not substitute a retyped copy for it.")
        return 1
    if "LOCK=/tmp/incubator.slot.lock" not in original:
        print(f"REFUSED: {PIN} does not carry the defect this file claims to reproduce.")
        return 1

    pristine = SUBJECT.read_bytes()
    digest = hashlib.sha256(pristine).hexdigest()

    rc, before = run([sys.executable, "-m", "pytest", SUITE, "-q"])
    if rc != 0:
        print(f"REFUSED: the suite is not green before any mutation (exit {rc}).\n{before}")
        return 1

    blocks: list[str] = []
    seen: dict[frozenset[str], str] = {}

    for i, (title, edits, marker) in enumerate(mutations(original), 1):
        mutated = pristine.decode()
        if edits is None:
            mutated = original
            shown = f"  (the entire file, replaced with the one commit {PIN[:7]} shipped)\n"
        else:
            shown = ""
            for find, repl in edits:
                if mutated.count(find) != 1:
                    print(f"REFUSED: mutation {i} anchor appears {mutated.count(find)} times, "
                          "not once.")
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
        if "test_the_work_runs_when_the_slot_is_free" in dead:
            print(f"REFUSED: mutation {i} kills the instrument control, so it broke the apparatus "
                  "rather than demonstrating a property.")
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

    OUT.write_text(HEADER + "".join(blocks)
                   + FOOTER.format(before=before.strip(), after=after.strip()),
                   encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} - {len(seen)} mutations, all distinct")
    return 0


HEADER = f"""RED-033 - a lock that was never taken, reported as a busy neighbour

DATE (UTC): 2026-08-24
SUBJECT   : scripts/run_budgeted.sh, judged by tests/test_run_budgeted_names_its_refusals.py
LAW       : LAW-BUDGET-LOCK-UNDER-THE-PROJECT
PRODUCED  : evidence/RED-033-generator.py, checked in beside this file so the runs below can be
            repeated rather than believed.

WHY THIS FILE EXISTS

Invariant 5: a test must be ABLE to fail. `scripts/run_budgeted.sh` carries the only enforcement of
"concurrency = 1 process" in CLAUDE.md's resource budget, and until T-S6 nothing in the suite ran
it at all - the module was bound to ABI-33-1 in the requirement map and judged by no assertion.

TWO DEFECTS, AND THE SECOND IS THE ONE THAT COULD NOT BE SEEN

  1. THE PATH. `LOCK=/tmp/incubator.slot.lock` is a fixed name in a mode-1777 directory shared with
     nine other projects on this host. Whoever creates the path owns it: the sticky bit stops
     others deleting it, not others getting there first, and a neighbour who arrived first could
     leave a file with the wrong mode or a symlink pointing anywhere. Measured before the move and
     recorded in evidence/MEASURED-002-the-shared-lock-this-project-was-relying-on.txt - the path
     was in fact still ours, which is a fact about luck and not about design.

  2. THE REPORT. `if ! flock -n 9` folded every non-success into one branch, so a lock that could
     not be OPENED, and a `flock` that is not installed, both printed "the slot is held by another
     run (concurrency=1). This is a finding, not silence." That sentence announces a healthy
     concurrency limit with a neighbour inside it, at the moment the limit has stopped existing.
     It is invariant 1 pointed at the guarantee rather than at a counter, and it returns
     EX_TEMPFAIL, telling the caller to retry something that will never succeed.

     Measured on the shipped script: `flock` exits 65 on a bad descriptor and 127 when it is not
     installed, and the original read both as contention.

AND THE SILENT ONE, WHICH NO EXIT STATUS REPORTS

`exec 9>"$LOCK"` failing does not stop the script - bash prints to stderr, returns 1 and carries
on - and it does not close a descriptor 9 that arrived ALREADY OPEN from a calling script. Measured
on the shipped form: with fd 9 inherited and the lock path unopenable, `flock -n 9` locks the
caller's unrelated file, the work runs to completion, and the script exits 0 with no error printed
anywhere. That is mutation 5 below. Nothing about the exit status or the wording can catch it; the
only question that can is whether the work RAN, which is what every assertion in the suite asks.

THE SUBJECT IS RESTORED BYTE FOR BYTE BETWEEN MUTATIONS, verified by sha256, and the suite is run
green afterwards. Each mutation's output is captured into its own buffer.
"""

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
