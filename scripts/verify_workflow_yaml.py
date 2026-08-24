#!/usr/bin/env python3
"""T-S7 - every workflow file is put in front of a REAL YAML parser, because GitHub uses one.

WHY THIS EXISTS, AND IT IS A MEASUREMENT RATHER THAN A PRECAUTION. `66f61ea` went out with seven
green gates behind it - 642 passed, coverage 92.87% - and turned `main` red in the same second it
landed. Three `run:` lines carried `--only-binary=:all: ` in a PLAIN scalar, and `: ` is how YAML
spells "the key ended here", so the document GitHub received was not a document. The run was
created and concluded in the same second with ZERO jobs: nothing in the workflow failed, because
nothing in the workflow ever started. The whole reading is kept in
`evidence/RED-031-seven-green-gates-and-a-workflow-that-never-parsed.txt`.

`scripts/verify_pip_pins.py` read those three lines correctly and still does. It was not fooled and
it did not lie - it simply reads the file with what D-30 calls, in its own words, "a hand-written
approximation of a shell lexer inside a hand-written approximation of a YAML reader", and that
scanner accepted a document the real parser rejects. A CHECKER MORE PERMISSIVE THAN THE MACHINE IT
STANDS IN FOR WILL CERTIFY FILES THAT MACHINE CANNOT RUN (L-31). Until this module, nothing in this
repository loaded a workflow with a YAML parser at all.

WHAT IS CLAIMED, AT THE STRENGTH THE ARTEFACT SUPPORTS. PyYAML is not GitHub's parser: GitHub reads
these files with its own implementation, and PyYAML implements YAML 1.1 where most modern parsers
implement 1.2. So a file this module accepts is NOT thereby proven to be a file GitHub accepts, and
this module makes no schema claim either - a document with a misspelt key, an unknown `runs-on` or
a job that cannot start parses perfectly and fails somewhere this gate cannot see. What is claimed
is the one thing RED-031 was: a document that is not well-formed YAML is refused HERE, at the door,
instead of on `main` after a push. The residue between the two parsers is named rather than closed,
because closing it would mean running GitHub's parser, which is not on this host.

WHERE IT MAY RUN. It imports PyYAML, which the `tests` job installs (D-32 put it in
`requirements/ci-tests.in`) and the `ratchets` job does not - that job installs nothing at all, by
design, so `scripts/ratchet_*.py` hand-parse. A missing PyYAML is reported here as `not_measured`
and never as a clean tree (invariant 1): an absent instrument that returns "no problems found" is
the defect this repository is built to refuse, and it would be the more embarrassing one inside the
gate written about permissive readers.
"""
from __future__ import annotations

import pathlib
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - see the note below on what the suite does and does not do
    # WHAT IS EXERCISED IS THE STATE, NOT THIS BRANCH. The suite reaches `yaml is None` by
    # monkeypatching the module attribute, so every consequence of an absent parser is measured;
    # this `except` itself runs only on a host that genuinely lacks PyYAML, and nothing in the tree
    # arranges one. The distinction is written out because the first draft of this line claimed the
    # branch was "exercised through _IMPORT_ERROR in the suite" - a mechanism that exists nowhere
    # in this repository. A dead reference dressed as coverage, inside the gate whose law is about
    # checkers claiming more than they measured. Found by Fable.
    yaml = None  # type: ignore[assignment]

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

# GitHub reads both extensions. A checker that knew one would be silent about the other, which is
# the shape of L-6 and is already a fixture in tests/test_pip_pinned.py.
SUFFIXES = (".yml", ".yaml")

UNPARSEABLE = "DOES NOT PARSE"
"""The marker every parse failure carries.

The suite asserts on THIS rather than on "check() returned something", because `check()` also
reports an absent PyYAML and an absent directory. A fixture test that only asked whether the list
was non-empty would go green on a host with no parser at all - passing because the instrument was
missing, over a workflow it never read.
"""


def workflow_files(workflows: pathlib.Path = WORKFLOWS) -> list[pathlib.Path]:
    """Every candidate file, sorted. The directory listing IS the work list: a hard-coded set of
    names would go quiet about the fourth workflow somebody adds, which is exactly how a new file
    escapes a gate."""
    return sorted(p for p in workflows.iterdir() if p.is_file() and p.suffix in SUFFIXES)


def parse_problems(text: str, name: str) -> list[str]:
    """What the real parser says about one document, or why it could not be asked."""
    if yaml is None:
        return [f"{name}: PyYAML is ABSENT, so this file was NOT PARSED - not_measured, not clean"]
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        # The parser's own mark carries line and column, and that is the whole value of using it:
        # RED-031 cost an hour partly because the failure arrived as "startup_failure" with no
        # location. Reproduced here, the same defect reads `line 128, column 69`.
        return [f"{name}: {UNPARSEABLE} - {str(exc).strip()}"]
    if doc is None:
        return [f"{name}: {UNPARSEABLE} as a workflow - the document is EMPTY, which is a state of "
                "its own and is not a workflow with no jobs"]
    if not isinstance(doc, dict):
        return [f"{name}: {UNPARSEABLE} as a workflow - the top level is "
                f"{type(doc).__name__}, and GitHub requires a mapping"]
    return []


def check(workflows: pathlib.Path = WORKFLOWS) -> list[str]:
    """Every problem, or an empty list. Never None, and never an empty list for a reason other than
    "every workflow parsed"."""
    if not workflows.is_dir():
        return [f"{workflows} is ABSENT: this gate measured NOTHING, which differs from a tree "
                "whose workflows are all well-formed"]
    files = workflow_files(workflows)
    if not files:
        # Invariant 1 turned on the instrument. Zero files and zero failures print the same green,
        # and a gate that has quietly stopped having a subject is how a control is lost in silence.
        return [f"{workflows} holds NO workflow file, so this gate measured NOTHING - unknown, "
                "not clean"]
    problems: list[str] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            # Unreadable is its own state. Reading it as "no parse errors found" would be the
            # instrument's failure wearing the shape of a pass.
            problems.append(f"{path.name}: COULD NOT BE READ ({exc}) - unreadable, not clean")
            continue
        problems.extend(parse_problems(text, path.name))
    return problems


def main() -> int:
    problems = check()
    if problems:
        sys.stderr.write("\nX T-S7:\n" + "".join(f"  - {p}\n" for p in problems))
        return 1
    names = [p.name for p in workflow_files()]
    # The COUNT is printed because "all of them parsed" is satisfied vacuously by parsing none, and
    # a reader of this line deserves to see which files were actually put in front of the parser.
    print(f"T-S7: clean ({len(names)} workflow files parsed by yaml.safe_load: {', '.join(names)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
