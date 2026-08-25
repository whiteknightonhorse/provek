"""T-S11 - the door's dirty-tree check must not read a warned `git status` as a clean tree.

WHY THIS EXISTS. `scripts/push.sh` used to read `DIRTY=$(git status --porcelain)` straight into a
variable and call an empty result clean. Empty is also what git hands back when it could not enter
a directory: it writes `warning: could not open directory 'sub/': Permission denied` to STDERR,
EXITS 0, and leaves that subtree out of stdout entirely. D-33 measured and closed the identical
hole one module over, in `scripts/publishable_tree.py._porcelain`; this suite proves the same
closure for `scripts/clean_tree_gate.sh`, the module the door now calls.

THREE CASES, MATCHING THE THREE STATES THE GATE MUST NAME (invariant 1): a clean tree passes, a
dirty tree is refused with the dirty paths printed, and a tree git could not fully read is refused
as UNREADABLE - which is neither of the other two and must never print "CLEAN".

REAL `git init` REPOSITORIES, NOT A STUBBED `git status` - for the same reason
`test_publishable_tree.py` gives: the subject is git's own behaviour under a permission fault, and
a stub would encode a belief about that behaviour and then confirm it (L-18).
"""
from __future__ import annotations

import os
import pathlib
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "clean_tree_gate.sh"

CLEAN, DIRTY, UNREADABLE = 0, 1, 2


def _repo(tmp_path: pathlib.Path) -> pathlib.Path:
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    (repo / "a.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-qm", "seed"],
        cwd=repo, check=True,
    )
    return repo


def _run(repo: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(GATE), str(repo)], capture_output=True, text=True, timeout=60)


def test_a_clean_tree_passes(tmp_path):
    done = _run(_repo(tmp_path))
    assert done.returncode == CLEAN, done.stdout + done.stderr
    assert "CLEAN" in done.stdout


def test_an_untracked_file_is_refused_and_named(tmp_path):
    repo = _repo(tmp_path)
    (repo / "parked.txt").write_text("somebody's work in progress\n", encoding="utf-8")
    done = _run(repo)
    assert done.returncode == DIRTY, done.stdout + done.stderr
    assert "REFUSED" in done.stderr
    assert "parked.txt" in done.stderr
    assert "CLEAN" not in done.stdout


# A `chmod 000` means nothing to root, so the case below could not express its own subject there:
# it would build a directory git reads happily and assert a refusal that never comes. Same guard,
# same reason, as `tests/test_publishable_tree.py` and `tests/test_deploy_label.py`.
_needs_permissions = pytest.mark.skipif(
    os.geteuid() == 0, reason="root ignores the permission bits this case is made of")


@_needs_permissions
def test_a_subtree_git_warned_about_is_unreadable_not_clean(tmp_path):
    """THE CASE THAT SHIPPED WRONG BEFORE THIS TASK. `git status` does not fail on a directory it
    cannot enter: it warns on stderr, EXITS 0, and leaves that subtree out of stdout. The old
    `DIRTY=$(git status --porcelain)` reading in push.sh saw no dirty paths and let the door
    through - a tree nothing had read, called clean.

    THE FIXTURE ASSERTS ITS OWN PREMISE FIRST: if git ever stops warning here, or starts exiting
    nonzero, this case would pass while measuring something else - the failure mode
    `evidence/RED-023-*` names in the neighbouring gate.
    """
    repo = _repo(tmp_path)
    locked = repo / "locked"
    locked.mkdir()
    (locked / "parked.txt").write_text("untracked, and about to become invisible\n", encoding="utf-8")
    locked.chmod(0o000)
    try:
        raw = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, timeout=60)
        assert raw.returncode == 0, "git FAILED here; the old exit-code reading would have caught it"
        assert raw.stdout == b"", "git listed the locked subtree; this is not the state the case claims"
        assert b"warning" in raw.stderr, f"git warned about nothing: {raw.stderr!r}"

        done = _run(repo)
        assert done.returncode == UNREADABLE, done.stdout + done.stderr
        assert "UNREADABLE" in done.stderr
        assert "could not open directory" in done.stderr, "git's cause was swallowed"
        assert "CLEAN" not in done.stdout
    finally:
        locked.chmod(0o755)
