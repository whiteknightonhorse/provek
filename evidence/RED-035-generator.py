#!/usr/bin/env python3
"""Produces evidence/RED-035-a-tree-published-on-a-reading-git-said-it-had-not-finished.txt.

THE SUBJECT IS A STATE OF THE FILESYSTEM, NOT A COMMIT, so unlike RED-033/034 nothing is fetched
out of history. The defect was never a wrong line: `publishable_tree._porcelain` read `git status`
exactly as its author intended, and `git status` answers a question nobody asked it - it exits 0
over a directory it could not open, warns on stderr, and leaves that subtree out of stdout. The
gate read the number and not the sentence. RED-023 run 4 measured that while repairing a
NEIGHBOURING module, wrote it into `~/orchestra/FINDINGS.md` for the judge, and shipped the hole on
purpose rather than reaching into another task's gate. This file is that hole closed, and the
measurement is re-taken here rather than quoted, because the tree it was taken on no longer exists.

FOUR PARTS.

  1. THE PREMISE, ASSERTED BEFORE ANYTHING IS CLAIMED FROM IT. A fixture repository is built with
     an untracked file under a `chmod 000` directory, and git is run raw: exit 0, empty stdout,
     a warning on stderr. If any of those three moved on this host, every reading below would be
     about a different state and this file refuses to be written.

  2. THE RED. The stderr reading is removed from the shipped module - the behaviour of one commit
     ago - and the same fixture is measured again. The scheduler's gate prints PUBLISHABLE and
     exits 0 over a tree holding a file nothing opened, and `deploy_label`, which shares the
     reader, labels it with the commit's short sha and `COMMIT_DIRTY=false`. Both suites go red.

  3. THE GUARD ONE LAYER DOWN, WHICH THIS CHANGE COULD HAVE QUIETLY DISARMED. `deploy_label`'s
     clean path re-reads every file `git ls-files` names, and the case that armed it - a TRACKED
     file under an unenterable directory - is now caught by part 2's reading before `decide` gets
     there. A guard whose removal nothing notices is already gone (RED-023 run 8, the same guard),
     so the mutation that deletes it is run here: it must still go red, and it must go red on the
     one state the reader above cannot see - git calling a tree clean, with an EMPTY stderr, over
     bytes it never opened.

  4. THE RESTORE. Both subjects back to their committed bytes, verified by sha256, both suites
     green afterwards.

WHAT THIS FILE DOES NOT DO. It never runs `~/orchestra/deploy.sh` and never publishes anything:
the fixture is a throwaway repository in a temporary directory, and the two gates are asked about
it directly. RED-023 states that reason at length and it has not changed.
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
OUT = ROOT / "evidence" / "RED-035-a-tree-published-on-a-reading-git-said-it-had-not-finished.txt"
SCRIPTS = ROOT / "scripts"
TREE_GATE = SCRIPTS / "publishable_tree.py"
LABEL_GATE = SCRIPTS / "deploy_label.py"
TREE_SUITE = "tests/test_publishable_tree.py"
LABEL_SUITE = "tests/test_deploy_label.py"

# The reading T-C8 added, and the shape it had before: `warning` computed from git's stderr, versus
# a constant that can never be truthy. The mutation is the OLD code, not an invented one.
STDERR_READING = '    warning = out.stderr.decode("utf-8", "replace").strip()\n'
STDERR_REMOVED = '    warning = ""   # MUTATION-1: the stderr reading, removed - the shipped behaviour of T-C7\n'

DIGEST_READING = "        if content_digest(root) is None:\n"
DIGEST_REMOVED = "        if False:   # MUTATION-2: the clean path's reading of the bytes, deleted\n"

# The two cases this file exists to arm. Named as constants because part 2 and part 3 each assert
# something about WHICH of them dies, and a node id typed twice is a claim that can drift (L-2).
WARNED_CASE = "test_a_subtree_git_warned_about_is_unreadable_and_not_publishable"
FORWARDED_CASE = "test_the_warned_tree_reaches_the_scheduler_as_a_refusal_that_names_its_cause"
UNENTERABLE_CASE = "test_a_tracked_file_under_an_unenterable_directory_is_unreadable_not_clean"
UNREAD_BYTES_CASE = "test_a_file_git_called_clean_without_reading_it_is_not_labelled"

PROBE = r"""
import pathlib, sys
sys.path.insert(0, sys.argv[1])
import publishable_tree as pt, deploy_label as dl
root = pathlib.Path(sys.argv[2])
NAME = {0: "PUBLISHABLE", 3: "FOREIGN_WORK/DIRTY_REFUSED", 4: "UNREADABLE"}
print("_porcelain(root)      ->", pt._porcelain(root))
code, foreign, owned = pt.classify(root)
print("classify(root)        ->", code, NAME.get(code, "?"), "foreign=%r owned=%r" % (foreign, owned))
code, fields, dirty = dl.decide(root, allow_dirty=False)
print("decide(root, False)   ->", code, NAME.get(code, "?"),
      "LABEL=%s COMMIT_DIRTY=%s" % (fields.get("LABEL"), fields.get("COMMIT_DIRTY")))
"""


class Bail(Exception):
    """A refusal to write the artefact. Every raise names the reading that was not what it claims."""


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    """One command, one buffer. Nothing here is appended to a shared stream (L-26, RED-013)."""
    done = subprocess.run(cmd, cwd=str(cwd or ROOT), capture_output=True, text=True,
                          timeout=600, check=False)
    return done.returncode, done.stdout + done.stderr


def failed_tests(output: str) -> frozenset[str]:
    """Node ids out of pytest's `-rf` summary, which reads `FAILED <nodeid> - <message>`."""
    ids = set()
    for line in output.splitlines():
        if not line.startswith("FAILED ") or "::" not in line:
            continue
        ids.add(line[len("FAILED "):].split(" - ", 1)[0].strip().split("::", 1)[1])
    return frozenset(ids)


def build_fixture(where: Path) -> str:
    """A repository whose only uncommitted content is inside a directory nobody can enter.

    The file is UNTRACKED on purpose: that is the half RED-023 could not close from where it stood,
    because `git ls-files` omits it exactly as `git status` does, so no re-reading of tracked paths
    could ever have seen it. It is also the realistic half - parked work arrives untracked.
    """
    run(["git", "init", "-q", "-b", "main", str(where)])
    (where / "README.md").write_text("seed\n", encoding="utf-8")
    run(["git", "add", "-A"], cwd=where)
    run(["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t",
         "commit", "-qm", "seed"], cwd=where)
    locked = where / "locked"
    locked.mkdir()
    (locked / "parked.txt").write_text("somebody's unpushed work\n", encoding="utf-8")
    locked.chmod(0o000)

    raw = subprocess.run(["git", "status", "--porcelain", "-z", "--untracked-files=all"],
                         cwd=str(where), capture_output=True, timeout=60, check=False)
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
    return (f"$ git status --porcelain -z --untracked-files=all\n"
            f"exit   : {raw.returncode}\n"
            f"stdout : {raw.stdout!r}          <- empty: the untracked file is NOT in the report\n"
            f"stderr : {stderr.strip()}\n")


def probe(fixture: Path) -> str:
    rc, out = run([sys.executable, "-c", PROBE, str(SCRIPTS), str(fixture)])
    if rc != 0:
        raise Bail(f"the probe itself failed (exit {rc}):\n{out}")
    return out


def gate_process(fixture: Path) -> str:
    done = subprocess.run([sys.executable, str(TREE_GATE), "--root", str(fixture)],
                          capture_output=True, text=True, timeout=60, check=False)
    return (f"$ python3 scripts/publishable_tree.py --root <fixture>\n"
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


def red(suite: str, marker: str, must_kill: set[str], must_survive: set[str]) -> tuple[str, frozenset[str]]:
    rc, out = run([sys.executable, "-m", "pytest", suite, "-q", "-rf"])
    if rc != 1:
        raise Bail(f"{marker}: pytest on {suite} exited {rc}. Only exit 1 is a suite that RAN and "
                   f"failed - exit 2 is a file that no longer imports, and reading any nonzero as "
                   f"'red' is invariant 1 inside the instrument.\n{out}")
    dead = failed_tests(out)
    missing = must_kill - dead
    if missing:
        raise Bail(f"{marker}: {suite} went red without {sorted(missing)}, so the case this file "
                   f"claims is armed is not what noticed.\n{out}")
    wrongly = must_survive & dead
    if wrongly:
        raise Bail(f"{marker}: {sorted(wrongly)} also died, which contradicts the claim that these "
                   f"two readings cover different states.\n{out}")
    return out, dead


def main() -> int:
    if os.geteuid() == 0:
        print("REFUSED: running as root. `chmod 000` means nothing here, so the fixture cannot be "
              "put into the state this file is about, and a green run would prove nothing.")
        return 1

    pristine = {p: p.read_bytes() for p in (TREE_GATE, LABEL_GATE)}
    digests = {p: hashlib.sha256(b).hexdigest() for p, b in pristine.items()}

    workdir = Path(tempfile.mkdtemp(prefix="red035-"))
    fixture = workdir / "repo"
    fixture.mkdir()
    try:
        premise = build_fixture(fixture)

        rc, base_tree = run([sys.executable, "-m", "pytest", TREE_SUITE, "-q"])
        rc2, base_label = run([sys.executable, "-m", "pytest", LABEL_SUITE, "-q"])
        if rc or rc2:
            raise Bail(f"a suite is not green before any mutation ({rc}, {rc2}).\n"
                       f"{base_tree}\n{base_label}")

        shipped_probe = probe(fixture)
        shipped_gate = gate_process(fixture)
        if "classify(root)        -> 4" not in shipped_probe:
            raise Bail(f"the SHIPPED code does not call this fixture unreadable, so there is "
                       f"nothing here to have been repaired:\n{shipped_probe}")
        if "exit   : 4" not in shipped_gate:
            raise Bail(f"the shipped gate PROCESS did not exit 4; the scheduler reads the exit "
                       f"code and this file would be describing a verdict it never receives:\n"
                       f"{shipped_gate}")

        # ---- part 2: the reading removed, which is the code of one commit ago ----
        mutate(TREE_GATE, STDERR_READING, STDERR_REMOVED, "MUTATION-1")
        try:
            red_probe = probe(fixture)
            red_gate = gate_process(fixture)
            red_tree_out, tree_dead = red(TREE_SUITE, "MUTATION-1", {WARNED_CASE, FORWARDED_CASE},
                                          set())
            red_label_out, label_dead = red(LABEL_SUITE, "MUTATION-1", {UNENTERABLE_CASE}, set())
        finally:
            TREE_GATE.write_bytes(pristine[TREE_GATE])

        if "classify(root)        -> 0 PUBLISHABLE" not in red_probe:
            raise Bail(f"the mutation did not restore the old behaviour, so it is not the defect "
                       f"this file claims to reproduce:\n{red_probe}")
        if "exit   : 0" not in red_gate or "PUBLISHABLE" not in red_gate:
            raise Bail(f"the mutated gate PROCESS did not hand the scheduler a green light, which "
                       f"is the entire finding:\n{red_gate}")

        # ---- part 3: the guard one layer down, which must still be able to die ----
        mutate(LABEL_GATE, DIGEST_READING, DIGEST_REMOVED, "MUTATION-2")
        try:
            red_digest_out, digest_dead = red(LABEL_SUITE, "MUTATION-2", {UNREAD_BYTES_CASE},
                                              {UNENTERABLE_CASE})
        finally:
            LABEL_GATE.write_bytes(pristine[LABEL_GATE])

        # ---- part 4: restored, and green ----
        for path, want in digests.items():
            if hashlib.sha256(path.read_bytes()).hexdigest() != want:
                raise Bail(f"{path.relative_to(ROOT)} was not restored byte for byte.")
        rc, after_tree = run([sys.executable, "-m", "pytest", TREE_SUITE, "-q"])
        rc2, after_label = run([sys.executable, "-m", "pytest", LABEL_SUITE, "-q"])
        if rc or rc2:
            raise Bail(f"a suite is not green after the restore ({rc}, {rc2}).\n"
                       f"{after_tree}\n{after_label}")

        OUT.write_text(REPORT.format(
            premise=premise,
            base_tree=base_tree.strip(), base_label=base_label.strip(),
            shipped_probe=shipped_probe.strip(), shipped_gate=shipped_gate.strip(),
            red_probe=red_probe.strip(), red_gate=red_gate.strip(),
            red_tree=red_tree_out.strip(), red_label=red_label_out.strip(),
            tree_dead=", ".join(sorted(tree_dead)), label_dead=", ".join(sorted(label_dead)),
            red_digest=red_digest_out.strip(), digest_dead=", ".join(sorted(digest_dead)),
            after_tree=after_tree.strip(), after_label=after_label.strip(),
        ), encoding="utf-8")
    except Bail as exc:
        for path, blob in pristine.items():
            path.write_bytes(blob)
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

REPORT = f"""RED-035 - a tree published on a reading git had said it did not finish

DATE (UTC): 2026-08-24
SUBJECT   : scripts/publishable_tree.py (`_porcelain`), judged by tests/test_publishable_tree.py
            scripts/deploy_label.py, which imports that reader, judged by tests/test_deploy_label.py
LAWS      : LAW-PUBLISH-JUDGED-TREE, LAW-DEPLOY-LABEL-TRUE
TASK      : T-C8. The finding it closes was raised by T-H2 and left standing on purpose - see the
            last section of evidence/RED-023-*, and the erratum beside it.
PRODUCED  : evidence/RED-035-generator.py, checked in beside this file so the runs below can be
            repeated rather than believed. It refuses to write this file if any premise it depends
            on is not the state it claims.

WHY THIS FILE EXISTS

Invariant 1 says a counter that can read zero must distinguish `nothing_qualified` from
`check_did_not_run`. `git status --porcelain` returns a LIST, and an empty list is that zero. The
instrument has one way of saying it did not look - a line on stderr, next to an exit code of 0 -
and until this task both gates built on it read only the number. So "I could not open that
directory" arrived as "there is nothing in that directory", which is the exact substitution this
project exists to detect, sitting inside the gate that decides whether an unattended publisher may
ship.

{{SEP}}
1. THE PREMISE - the state, before anything is claimed from it
{{SEP}}

A throwaway repository: one commit, plus an untracked file inside a directory at mode 000.

{{premise}}
git exits 0. That is the whole defect: a failing instrument answering with a number that has the
shape of a measurement. Nothing about that exit code is wrong - git DID succeed at what it was
asked - and nothing about the old reading was a typo.

{{SEP}}
2. THE SHIPPED CODE - the same tree, refused by name
{{SEP}}

{{shipped_probe}}

{{shipped_gate}}

The refusal carries git's own sentence rather than this gate's summary of it, because UNREADABLE
with no cause sends the operator hunting for uncommitted work that is not there, and a refusal
nobody can act on is the one that gets routed around (L-5).

{{SEP}}
3. THE RED - the reading removed, which is the code of one commit ago
{{SEP}}

    - {STDERR_READING.strip()}
    + {STDERR_REMOVED.strip()}

{{red_probe}}

{{red_gate}}

PUBLISHABLE, exit 0, over a tree holding a file nothing opened - and `deploy_label`, which shares
this reader, signs it with the commit's short sha and COMMIT_DIRTY=false. Two gates, one reading,
one hole; that shared import is why the repair had to be made here and not twice (L-2).

Tests killed in {TREE_SUITE} ({{tree_dead}})
Tests killed in {LABEL_SUITE} ({{label_dead}})

--- verbatim `python -m pytest {TREE_SUITE} -q -rf` ---

{{red_tree}}

--- verbatim `python -m pytest {LABEL_SUITE} -q -rf` ---

{{red_label}}

{{SEP}}
4. THE GUARD ONE LAYER DOWN, WHICH THIS REPAIR COULD HAVE DISARMED IN SILENCE
{{SEP}}

`deploy_label.decide` re-reads every file `git ls-files` names before labelling a CLEAN tree, and
RED-023 run 8 proved that reading load-bearing by deleting it and watching
`{UNENTERABLE_CASE}` go red. After part 2 that case is caught
by the reader above, before the digest is ever consulted - so the same deletion would have gone
green again, and a guard whose removal nothing notices is already gone.

    - {DIGEST_READING.strip()}
    + {DIGEST_REMOVED.strip()}

Tests killed ({{digest_dead}})

--- verbatim `python -m pytest {LABEL_SUITE} -q -rf` ---

{{red_digest}}

The case that died is the one built on the state the reader above CANNOT see: git reporting a tree
clean, with an EMPTY stderr, over a file it did not open (`assume-unchanged`, or any stat cache it
trusts). `{UNENTERABLE_CASE}` survived this mutation,
which is the measured form of the claim that the two readings cover different states rather than
one of them being redundant.

{{SEP}}
5. RESTORED - both subjects back to their committed bytes, verified by sha256
{{SEP}}

baseline, before any mutation:
    {TREE_SUITE:<34} {{base_tree}}
    {LABEL_SUITE:<34} {{base_label}}

after the restore:
    {TREE_SUITE:<34} {{after_tree}}
    {LABEL_SUITE:<34} {{after_label}}

WHAT IS STILL NOT MEASURED, NAMED RATHER THAN IMPLIED

The reader refuses every unreadable path git NOTICES, and the digest opens every path git LISTS.
Neither can see a filesystem that answers without error and without the truth, and neither claims
to. The price of the first is stated where it is paid, in `_porcelain`'s docstring and beside D-26:
ANY stderr is a refusal, the text is not parsed, so an unrelated warning reddens a cycle over a
tree that may be perfectly publishable. That false red announces that THE INSTRUMENT stopped and
prints git's reason for stopping; the false green it replaces publishes content nothing opened and
says nothing at all.
""".replace("{SEP}", SEP)


if __name__ == "__main__":
    raise SystemExit(main())
