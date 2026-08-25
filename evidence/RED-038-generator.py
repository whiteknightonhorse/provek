#!/usr/bin/env python3
"""Produces evidence/RED-038-a-door-that-read-a-warned-tree-as-clean.txt.

THE SUBJECT IS A STATE OF THE FILESYSTEM, NOT A COMMIT, so like RED-035 nothing is fetched out of
history. The defect T-S11 closes was never a wrong line: `scripts/push.sh` read
`DIRTY=$(git status --porcelain)` exactly as its author intended, and `git status` answers a
question nobody asked it - it exits 0 over a directory it could not open, warns on stderr, and
leaves that subtree out of stdout. The door read the number and not the sentence. D-33 closed the
identical hole one module over, in `scripts/publishable_tree.py._porcelain`; this file closes it at
the door itself, via the new `scripts/clean_tree_gate.sh`.

THREE PARTS.

  1. THE PREMISE, ASSERTED BEFORE ANYTHING IS CLAIMED FROM IT. A fixture repository is built with
     an untracked file under a `chmod 000` directory, and git is run raw: exit 0, empty stdout, a
     warning on stderr. If any of those three moved on this host, every reading below would be
     about a different state and this file refuses to be written.

  2. THE RED. The stderr check is removed from the shipped gate - the behaviour `push.sh` actually
     had before this task, since `clean_tree_gate.sh` is new and its old form IS the inline reading
     it replaced - and the same fixture is measured again. The gate prints CLEAN and exits 0 over a
     tree holding a file nothing opened. The suite goes red on exactly the case built for this.

  3. THE RESTORE. The subject back to its committed bytes, verified by sha256, the suite green
     afterwards, and the fixed gate re-run on the same fixture to show the named refusal it now
     gives.

WHAT THIS FILE DOES NOT DO. It never runs `scripts/push.sh` and never pushes anything: the fixture
is a throwaway repository in a temporary directory, and the gate is asked about it directly.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "RED-038-a-door-that-read-a-warned-tree-as-clean.txt"
GATE = ROOT / "scripts" / "clean_tree_gate.sh"
SUITE = "tests/test_clean_tree_gate_reads_git_stderr.py"

# The check T-S11 added, and its absence - which is the exact shape `push.sh` had before this task:
# `DIRTY=$(git status --porcelain)`, stderr never looked at.
STDERR_CHECK = '''if [ -n "$STATUS_ERR" ]; then
  echo "UNREADABLE: git status wrote to stderr, so its report is not a reading of the whole tree - what follows is git's own sentence, not this gate's:" >&2
  echo "$STATUS_ERR" >&2
  exit "$UNREADABLE"
fi

'''
STDERR_CHECK_REMOVED = "# MUTATION: the stderr check T-S11 added, removed - the door's behaviour one commit ago\n\n"

WARNED_CASE = "test_a_subtree_git_warned_about_is_unreadable_not_clean"


class Bail(Exception):
    """A refusal to write the artefact. Every raise names the reading that was not what it claims."""


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    done = subprocess.run(cmd, cwd=str(cwd or ROOT), capture_output=True, text=True,
                          timeout=600, check=False)
    return done.returncode, done.stdout + done.stderr


def failed_tests(output: str) -> frozenset[str]:
    ids = set()
    for line in output.splitlines():
        if not line.startswith("FAILED ") or "::" not in line:
            continue
        ids.add(line[len("FAILED "):].split(" - ", 1)[0].strip().split("::", 1)[1])
    return frozenset(ids)


def build_fixture(where: Path) -> str:
    run(["git", "init", "-q", "-b", "main", str(where)])
    (where / "README.md").write_text("seed\n", encoding="utf-8")
    run(["git", "add", "-A"], cwd=where)
    run(["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t",
         "commit", "-qm", "seed"], cwd=where)
    locked = where / "locked"
    locked.mkdir()
    (locked / "parked.txt").write_text("somebody's unpushed work\n", encoding="utf-8")
    locked.chmod(0o000)

    raw = subprocess.run(["git", "status", "--porcelain"], cwd=str(where),
                         capture_output=True, timeout=60, check=False)
    stderr = raw.stderr.decode("utf-8", "replace")
    if raw.returncode != 0:
        raise Bail(f"git EXITED {raw.returncode} on the fixture. The whole subject of this file is "
                   f"git exiting 0 while not having read the tree; on this host it does not.")
    if raw.stdout:
        raise Bail(f"git listed the locked subtree ({raw.stdout!r}), so the fixture is not the "
                   f"state it claims and every reading below would be about a visible file.")
    if "warning" not in stderr:
        raise Bail(f"git warned about nothing (stderr={stderr!r}), so there is no sentence for the "
                   f"repaired reader to have read.")
    return (f"$ git status --porcelain\n"
            f"exit   : {raw.returncode}\n"
            f"stdout : {raw.stdout!r}          <- empty: the untracked file is NOT in the report\n"
            f"stderr : {stderr.strip()}\n")


def gate_process(fixture: Path) -> str:
    done = subprocess.run(["bash", str(GATE), str(fixture)],
                          capture_output=True, text=True, timeout=60, check=False)
    return (f"$ bash scripts/clean_tree_gate.sh <fixture>\n"
            f"exit   : {done.returncode}\n"
            f"stdout : {done.stdout.strip() or '(empty)'}\n"
            f"stderr : {done.stderr.strip() or '(empty)'}\n")


def mutate(subject: Path, find: str, repl: str, marker: str) -> None:
    text = subject.read_text(encoding="utf-8")
    if text.count(find) != 1:
        raise Bail(f"the anchor for {marker} appears {text.count(find)} times in "
                   f"{subject.relative_to(ROOT)}, not once.")
    subject.write_text(text.replace(find, repl), encoding="utf-8")
    if marker not in subject.read_text(encoding="utf-8"):
        raise Bail(f"{marker} is not in {subject.relative_to(ROOT)} after the edit; the mutation "
                   f"is assumed to have landed by nobody here.")


def red(marker: str, must_kill: set[str]) -> tuple[str, frozenset[str]]:
    rc, out = run([sys.executable, "-m", "pytest", SUITE, "-q", "-rf"])
    if rc != 1:
        raise Bail(f"{marker}: pytest on {SUITE} exited {rc}. Only exit 1 is a suite that RAN and "
                   f"failed - exit 2 is a file that no longer imports, and reading any nonzero as "
                   f"'red' is invariant 1 inside the instrument.\n{out}")
    dead = failed_tests(out)
    missing = must_kill - dead
    if missing:
        raise Bail(f"{marker}: {SUITE} went red without {sorted(missing)}, so the case this file "
                   f"claims is armed is not what noticed.\n{out}")
    return out, dead


def main() -> int:
    if os.geteuid() == 0:
        print("REFUSED: running as root. `chmod 000` means nothing here, so the fixture cannot be "
              "put into the state this file is about, and a green run would prove nothing.")
        return 1

    pristine = GATE.read_bytes()
    digest = hashlib.sha256(pristine).hexdigest()

    workdir = Path(tempfile.mkdtemp(prefix="red038-"))
    fixture = workdir / "repo"
    fixture.mkdir()
    try:
        premise = build_fixture(fixture)

        rc, base_suite = run([sys.executable, "-m", "pytest", SUITE, "-q"])
        if rc:
            raise Bail(f"the suite is not green before any mutation ({rc}).\n{base_suite}")

        shipped_gate = gate_process(fixture)
        if "exit   : 2" not in shipped_gate or "UNREADABLE" not in shipped_gate:
            raise Bail(f"the SHIPPED gate does not call this fixture UNREADABLE, so there is "
                       f"nothing here to have been repaired:\n{shipped_gate}")

        # ---- the reading removed, which is the door's behaviour one commit ago ----
        mutate(GATE, STDERR_CHECK, STDERR_CHECK_REMOVED, "MUTATION")
        try:
            red_gate = gate_process(fixture)
            red_out, dead = red("MUTATION", {WARNED_CASE})
        finally:
            GATE.write_bytes(pristine)

        if "exit   : 0" not in red_gate or "CLEAN" not in red_gate:
            raise Bail(f"the mutated gate did not hand the door a green light over the unread "
                       f"tree, which is the entire finding:\n{red_gate}")

        # ---- restored, and green ----
        if hashlib.sha256(GATE.read_bytes()).hexdigest() != digest:
            raise Bail(f"{GATE.relative_to(ROOT)} was not restored byte for byte.")
        rc, after_suite = run([sys.executable, "-m", "pytest", SUITE, "-q"])
        if rc:
            raise Bail(f"the suite is not green after the restore ({rc}).\n{after_suite}")

        fixed_gate = gate_process(fixture)

        OUT.write_text(REPORT.format(
            premise=premise,
            base_suite=base_suite.strip(),
            shipped_gate=shipped_gate.strip(),
            red_gate=red_gate.strip(),
            red_out=red_out.strip(),
            dead=", ".join(sorted(dead)),
            after_suite=after_suite.strip(),
            fixed_gate=fixed_gate.strip(),
        ), encoding="utf-8")
    except Bail as exc:
        GATE.write_bytes(pristine)
        print(f"REFUSED: {exc}")
        return 1
    finally:
        locked = fixture / "locked"
        if locked.exists():
            locked.chmod(0o755)
        shutil.rmtree(workdir, ignore_errors=True)

    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


SEP = "=" * 98

REPORT = f"""RED-038 - a door that read a warned tree as clean

DATE (UTC): 2026-08-25
SUBJECT   : scripts/clean_tree_gate.sh, judged by tests/test_clean_tree_gate_reads_git_stderr.py
LAWS      : LAW-DOOR-MATCHES-ARBITER, invariant 1 (not_measured is a state of its own)
TASK      : T-S11. The fork was named at D-33's own line: that decision closed
            `scripts/publishable_tree.py._porcelain` and named two more readers with the identical
            defect rather than fixing them in passing - `scripts/push.sh`'s own dirty-tree check
            (this file) and `~/orchestra/orch.sh`'s `untracked_inventory` (evidence in the
            orchestra's own tree, not here - it is outside every gate this repository has).
PRODUCED  : evidence/RED-038-generator.py, checked in beside this file so the runs below can be
            repeated rather than believed. It refuses to write this file if any premise it depends
            on is not the state it claims.

WHY THIS FILE EXISTS

Invariant 1 says a counter that can read zero must distinguish `nothing_qualified` from
`check_did_not_run`. `git status --porcelain` returns a LIST, and an empty list is that zero. The
door's job is to tell "the tree is clean" apart from "git did not read the whole tree", and until
this task it could not: `DIRTY=$(git status --porcelain)` read the porcelain list and nothing else,
so a directory this process cannot enter - warn on stderr, exit 0, subtree missing from stdout -
came back as an empty `$DIRTY` and the door would have pushed on the strength of a check that never
ran.

{SEP}
PART 1 - THE PREMISE (raw git, on the fixture, before any gate touches it)
{SEP}

{{premise}}

Suite green before any mutation:
{{base_suite}}

The SHIPPED gate on this fixture (T-S11's fix, already in the tree):
{{shipped_gate}}

{SEP}
PART 2 - THE RED (the stderr check removed - the door's own behaviour one commit ago)
{SEP}

The mutated gate on the SAME fixture:
{{red_gate}}

pytest on the mutated gate:
{{red_out}}

Case(s) that died: {{dead}}

{SEP}
PART 3 - THE RESTORE
{SEP}

scripts/clean_tree_gate.sh restored byte-for-byte (sha256 verified). Suite green again:
{{after_suite}}

The fixed gate, re-run on the same fixture, for the record:
{{fixed_gate}}

{SEP}
READING
{SEP}

Part 1 is the premise this file refuses to be written without: git DOES exit 0, DOES leave the
locked subtree out of stdout, and DOES warn on stderr, on this host, today. Part 2 is the shipped
gate with T-S11's stderr check removed - i.e. the door's actual behaviour before this task - printing
CLEAN and exiting 0 over that same unread tree, which is the defect this task closes. Part 3 shows
the fix restored and the suite green, plus the fixed gate's actual answer on the identical fixture:
UNREADABLE, exit 2, git's own warning printed rather than summarised.
"""


if __name__ == "__main__":
    raise SystemExit(main())
