"""LAW-EVIDENCE-STAMPED-TREE, the reading half: `evidence_stamp.tree_stamp` must name the tree it
ran against, and must say so honestly when it could not read it.

REAL `git init` REPOSITORIES, NOT A STUBBED `subprocess.run` - the same reason
`tests/test_publishable_tree.py` gives for its own fixtures: this module's subject is git's own
output, and a stub would encode a belief about that output and then confirm it (L-18).
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp as es  # noqa: E402


def _repo(tmp_path: pathlib.Path) -> pathlib.Path:
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    (tmp_path / "README.md").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-qm", "seed"],
        cwd=tmp_path, check=True,
    )
    return tmp_path


def test_clean_tree_names_head_with_no_suffix(tmp_path):
    repo = _repo(tmp_path)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True,
                           text=True, check=True).stdout.strip()
    assert es.tree_stamp(repo) == f"tree: {head}"


def test_dirty_tree_is_named_dirty_not_folded_into_clean(tmp_path):
    repo = _repo(tmp_path)
    (repo / "README.md").write_text("edited after the last commit\n", encoding="utf-8")
    stamp = es.tree_stamp(repo)
    assert stamp.startswith("tree: ")
    assert stamp.endswith(" (dirty)")


def test_untracked_file_counts_as_dirty_too(tmp_path):
    """An untracked file is not in HEAD either; the stamp must not call that tree clean."""
    repo = _repo(tmp_path)
    (repo / "new.txt").write_text("nobody committed this\n", encoding="utf-8")
    assert es.tree_stamp(repo).endswith(" (dirty)")


def test_not_a_git_repository_is_UNREADABLE_not_clean(tmp_path):
    """The key property (invariant 1): a directory git cannot report on must not stamp itself
    clean by falling through an empty read. `tmp_path` here is never `git init`-ed."""
    assert es.tree_stamp(tmp_path) == "tree: unreadable"
    head, dirty = es.read_tree(tmp_path)
    assert head is None
    assert dirty is None


def test_a_directory_git_cannot_enter_makes_dirty_state_unreadable_not_clean(tmp_path):
    """D-33's hole, one module over: `git status` warns on stderr and exits 0 when a subtree
    cannot be entered, omitting it from stdout entirely. `_porcelain` (imported, not re-copied)
    already turns that into `None`; this proves the stamp keeps HEAD (which git could still read)
    apart from the dirty reading (which it could not) instead of collapsing both into one state.
    """
    repo = _repo(tmp_path)
    blocked = repo / "sub"
    blocked.mkdir()
    (blocked / "f.txt").write_text("x\n", encoding="utf-8")
    blocked.chmod(0o000)
    try:
        stamp = es.tree_stamp(repo)
        head, dirty = es.read_tree(repo)
        if dirty is None:
            assert head is not None
            assert stamp == f"tree: {head} (dirty-state unreadable)"
        else:
            # Running as root (or some CI sandboxes) ignores the permission bit; if git could
            # still read the subtree, the fixture did not produce the state it targets, and the
            # only thing left to assert is that the stamp did not silently claim `unreadable`.
            assert stamp != "tree: unreadable"
    finally:
        blocked.chmod(0o755)


def test_the_stamp_reuses_publishable_trees_porcelain_reader():
    """L-2: a second hand-written `git status` parser is the shape that drifts. Proven by identity
    rather than by re-deriving the same behaviour a second way."""
    from publishable_tree import _porcelain
    assert es._porcelain is _porcelain
