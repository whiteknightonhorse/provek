#!/usr/bin/env python3
"""Produces evidence/RED-032-a-slug-that-walked-out-of-the-passport-directory.txt.

It establishes that LAW-SLUG-JUDGED-BEFORE-FETCH can fail (invariant 5) in each direction it
holds, by applying one mutation at a time to a pristine copy of the subject, proving the edit
landed, running the suite with its output captured SEPARATELY, and restoring the file byte for byte
before the next one.

The separate capture is not fastidiousness. RED-013 carried one mutation's output under another's
heading because a single shell block redirected four runs into one stream, and the file read
exactly as it would have if it were true (L-26). Nothing here shares a buffer.

WHAT THIS REFUSES TO WRITE THE FILE OVER, each condition earned by a defect this project has
already shipped once:

  * a mutation that does not go red;
  * a mutation whose marker cannot be grepped back out of the file afterwards - the edit must be
    proven to have landed, not assumed from the fact that a string was replaced;
  * a pytest that did not RUN. Only exit 1 is a suite that ran and failed. Reading any nonzero
    exit as "red" is invariant 1 inside the instrument, and exit 2 is what a file that no longer
    parses produces - a red that says nothing about any property (L-28, RED-017 mutation 3);
  * a mutation that kills EVERY test. The suite carries an instrument control
    (`test_the_probe_can_fail`, a POSITIVE reading an inert probe cannot produce), and a mutation
    that takes the control down with it has broken the measuring apparatus rather than
    demonstrated a property;
  * two mutations with the same failure set. Distinct edits that kill the same tests are either
    the same mutation twice or a transposition, and both read as thoroughness;
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

OUT = ROOT / "evidence" / "RED-032-a-slug-that-walked-out-of-the-passport-directory.txt"
SUITE = "tests/test_passport_slug_is_judged_before_it_is_fetched.py"

SLUG = ROOT / "web" / "src" / "slug.js"
APP = ROOT / "web" / "src" / "App.tsx"

# (title, file, find, replace, marker). `marker` is grepped back out to prove the edit landed.
MUTATIONS = [
    (
        "the character class admits the separator - the defect exactly as it stood",
        SLUG,
        "const SLUG = /^[A-Za-z0-9_-]+$/;",
        "const SLUG = /^[A-Za-z0-9_/-]+$/; // MUTATION-1",
        "MUTATION-1",
    ),
    (
        "the anchors are dropped, so the class need only appear SOMEWHERE in the slug",
        SLUG,
        "const SLUG = /^[A-Za-z0-9_-]+$/;",
        "const SLUG = /[A-Za-z0-9_-]+/; // MUTATION-2",
        "MUTATION-2",
    ),
    (
        "the empty slug is admitted, so `/p//` requests the passport directory itself",
        SLUG,
        "const SLUG = /^[A-Za-z0-9_-]+$/;",
        "const SLUG = /^[A-Za-z0-9_-]*$/; // MUTATION-3",
        "MUTATION-3",
    ),
    (
        "the type check goes, and `RegExp.test` coerces a non-string into a matching one",
        SLUG,
        'return typeof slug === "string" && SLUG.test(slug);',
        "return SLUG.test(slug); // MUTATION-4",
        "MUTATION-4",
    ),
    (
        "the guard is correct and NOBODY CALLS IT - L-21's shape, the repair that documents "
        "itself into looking done",
        APP,
        """    if (!isSafeSlug(slugInRoute)) {
      setPassports((p) => ({ ...p, [key]: { state: "invalid" } }));
      return;
    }
""",
        "    // MUTATION-5: the call removed, the module left in place and still imported.\n",
        "MUTATION-5",
    ),
    (
        "the refusal renders as a missing passport - invariant 1 at the point a reader sees it",
        APP,
        '    if (p.state === "invalid")',
        '    if (p.state === "__never__") // MUTATION-6',
        "MUTATION-6",
    ),
]


def run(cmd: list[str]) -> tuple[int, str]:
    """One command, one buffer. Nothing here is appended to a shared stream."""
    done = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300)
    return done.returncode, done.stdout + done.stderr


def failed_tests(output: str) -> frozenset[str]:
    """Node ids out of pytest's `-rf` summary, which reads `FAILED <nodeid> - <message>`.

    Splitting the line on whitespace was the first version and it was WRONG in a way that only
    showed up in the artefact: a parametrised id containing a space (`test_x['git x']`) was cut at
    the space, so the "Tests killed" line named a test that does not exist while the verbatim
    output below it named the real one. A summary assembled by a script and disagreeing with the
    transcript underneath it is precisely L-26, and it would have shipped inside the evidence file.
    The message is delimited by ` - `, so that is what is split on.
    """
    ids = set()
    for line in output.splitlines():
        if not line.startswith("FAILED ") or "::" not in line:
            continue
        nodeid = line[len("FAILED "):].split(" - ", 1)[0].strip()
        ids.add(nodeid.split("::", 1)[1])
    return frozenset(ids)


def main() -> int:
    pristine = {p: p.read_bytes() for p in (SLUG, APP)}
    digests = {p: hashlib.sha256(b).hexdigest() for p, b in pristine.items()}

    rc, before = run([sys.executable, "-m", "pytest", SUITE, "-q"])
    if rc != 0:
        print(f"REFUSED: the suite is not green before any mutation (exit {rc}).\n{before}")
        return 1

    blocks: list[str] = []
    seen: dict[frozenset[str], str] = {}

    for i, (title, path, find, repl, marker) in enumerate(MUTATIONS, 1):
        src = pristine[path].decode()
        if src.count(find) != 1:
            print(f"REFUSED: mutation {i} anchor appears {src.count(find)} times, not once.")
            return 1
        path.write_text(src.replace(find, repl))
        try:
            landed = marker in path.read_text()
            rc, out = run([sys.executable, "-m", "pytest", SUITE, "-q", "-rf"])
        finally:
            path.write_bytes(pristine[path])

        if not landed:
            print(f"REFUSED: mutation {i} marker {marker} is not in the file after the edit.")
            return 1
        if rc != 1:
            print(f"REFUSED: mutation {i} exited {rc}; only exit 1 is a suite that RAN and failed.\n{out}")
            return 1
        dead = failed_tests(out)
        if not dead:
            print(f"REFUSED: mutation {i} went red with no FAILED line to name.\n{out}")
            return 1
        if "test_the_probe_can_fail" in dead:
            print(f"REFUSED: mutation {i} kills the instrument control, so it broke the apparatus.")
            return 1
        if dead in seen:
            print(f"REFUSED: mutation {i} has the same failure set as {seen[dead]}.")
            return 1
        seen[dead] = f"mutation {i}"

        blocks.append(
            f"\n{'=' * 100}\nMUTATION {i} - {title}\n{'=' * 100}\n"
            f"\nApplied to {path.relative_to(ROOT)}:\n\n"
            + "".join(f"  - {ln}\n" for ln in find.strip("\n").splitlines())
            + "".join(f"  + {ln}\n" for ln in repl.strip("\n").splitlines())
            + f"\nMarker {marker!r} grepped back out of the file after the edit: yes.\n"
            f"Tests killed ({len(dead)}): {', '.join(sorted(dead))}\n"
            f"\n--- verbatim output of `python -m pytest {SUITE} -q -rf` ---\n\n{out}"
        )

    for p, b in pristine.items():
        if hashlib.sha256(p.read_bytes()).hexdigest() != digests[p]:
            print(f"REFUSED: {p} was not restored byte for byte.")
            return 1
    rc, after = run([sys.executable, "-m", "pytest", SUITE, "-q"])
    if rc != 0:
        print(f"REFUSED: the suite is not green after the restore (exit {rc}).\n{after}")
        return 1

    OUT.write_text(HEADER + "".join(blocks) + FOOTER.format(before=before.strip(), after=after.strip()))
    print(f"wrote {OUT.relative_to(ROOT)} - {len(MUTATIONS)} mutations, all distinct")
    return 0


HEADER = f"""# RED-032 - a passport slug that walked out of the passport directory
#
# {evidence_stamp.tree_stamp()}
#
# Produced by evidence/RED-032-generator.py, checked in beside this file so the runs below can be
# repeated rather than believed. It establishes that LAW-SLUG-JUDGED-BEFORE-FETCH CAN FAIL
# (invariant 5) in each of the directions it holds.
#
# THE FINDING WAS NOT A SCANNER'S. CodeQL raised #6 and #7 against `web-1.0/src/App.tsx`, the
# FROZEN phase-2 rollback point, and both were dismissed on 2026-08-24 because the deploy builds
# `web/` only and nothing under `web-1.0/` is ever served. That dismissal is correct and it is not
# the whole reading: the frozen copy built its fetch through `.replace(/[:/]/g, "_")`, which
# removes the separator, and the LIVE `web/src/App.tsx` interpolated the route substring raw.
# The live tree was a superset of the code the scanner objected to in the dead one, and carried no
# alert of its own. Absence of an alert on the product path is `not_measured`, not `clean`.
#
# THE SIX MUTATIONS ARE NOT SIX SPELLINGS OF ONE. Four attack the rule (the class, the anchors, the
# empty case, the type coercion) and two attack its wiring - the guard nobody calls, and the
# refusal rendered as a measured absence. The last two are the ones a diff would not catch: in both
# the module is correct, present, imported and green on its own terms.
#
# Each mutation is applied to a pristine copy, its marker grepped back out to prove the edit
# landed, run with its output captured in its OWN buffer, and the file restored and compared by
# sha256 before the next one - because RED-013 came to carry one mutation's output under another's
# heading when four runs shared one redirect (L-26). The generator refuses to write this file if
# any mutation exits other than 1 (exit 2 is a file that stopped parsing, which is a red about
# nothing), if any two mutations kill the same set of tests, or if any mutation kills
# `test_the_probe_can_fail` - the suite's instrument control, a POSITIVE reading that an inert
# probe cannot produce, and the reason the refusals here are worth something.
#
# The gate is {SLUG.relative_to(ROOT)} and the suite RUNS it under Node
# (tests/slug_probe.mjs) rather than matching patterns against its source. That is the point of it:
# `^[A-Za-z0-9_-]+$` accepts a trailing newline in Python's `re` and refuses it in JavaScript, so a
# gate that re-implemented the rule in the test's own language would have asserted a property the
# browser does not have.
#
# Everything below the line in each block is verbatim tool output.
"""

FOOTER = """
{sep}
THE SUITE, GREEN, BEFORE ANY MUTATION AND AFTER THE LAST RESTORE
{sep}

before:

{before}

after (both subjects compared by sha256 against their pristine bytes first):

{after}
""".replace("{sep}", "=" * 100)


if __name__ == "__main__":
    raise SystemExit(main())
