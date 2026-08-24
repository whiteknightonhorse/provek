"""LAW-PUBLISH-JUDGED-TREE - the guard that lets the scheduler publish must be able to refuse.

THE TEST THIS FILE REFUSES TO BE. "`scripts/publishable_tree.py` exists" and "it returns 0 on this
repository" are both satisfied by a script whose body is `return 0`, and this project has already
shipped that shape once (L-16: a check that was present but not armed). So every case below builds
a tree in a known state and asserts the code that state must produce - including the two states
that must NOT be publishable.

WHY REAL `git init` REPOSITORIES AND NOT A STUBBED `git status`. The subject is the classification
of git's own output, and porcelain's format - the `XY ` prefix, the NUL separators, the bare second
half of a rename - is the part that can be got wrong. A stub would encode my belief about that
format and then confirm it, which is L-18: a test that builds its own subject cannot find the
subject missing. These repositories cost about a tenth of a second each.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "publishable_tree.py"

sys.path.insert(0, str(ROOT / "scripts"))
import publishable_tree as pt  # noqa: E402


def _repo(tmp_path: pathlib.Path) -> pathlib.Path:
    """A git repository with one commit, so that `clean` is a state it can actually be in."""
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    (tmp_path / "README.md").write_text("seed\n", encoding="utf-8")
    (tmp_path / "web" / "notes" / "src").mkdir(parents=True)
    (tmp_path / "web" / "notes" / "manifest.json").write_text('{"notes": {}}\n', encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-qm", "seed"],
        cwd=tmp_path, check=True,
    )
    return tmp_path


def test_a_clean_tree_is_publishable(tmp_path):
    code, foreign, owned = pt.classify(_repo(tmp_path))
    assert code == pt.PUBLISHABLE
    assert foreign == []
    assert owned == []


def test_parked_work_outside_the_cycles_own_paths_refuses(tmp_path):
    """THE CASE THE GUARD WAS WRITTEN FOR: a modified page nobody pushed, at publication time."""
    repo = _repo(tmp_path)
    (repo / "web").mkdir(exist_ok=True)
    (repo / "web" / "apply.tsx").write_text("parked copy\n", encoding="utf-8")
    code, foreign, _ = pt.classify(repo)
    assert code == pt.FOREIGN_WORK
    assert foreign == ["web/apply.tsx"]


def test_a_modified_tracked_file_refuses_as_well_as_an_untracked_one(tmp_path):
    """Untracked and modified are different porcelain shapes; both are work no gate has judged."""
    repo = _repo(tmp_path)
    (repo / "README.md").write_text("edited after the last commit\n", encoding="utf-8")
    code, foreign, _ = pt.classify(repo)
    assert code == pt.FOREIGN_WORK
    assert foreign == ["README.md"]


def test_the_cycles_own_output_does_not_block_the_cycle(tmp_path):
    """A new note and a rewritten manifest are what a green cycle LOOKS like, not a reason to stop.

    `owned` is asserted non-empty on purpose. Without it this case passes identically against a
    classifier that never read the tree at all, which is the exact failure the module docstring
    names - and it would then pass against every other case too.
    """
    repo = _repo(tmp_path)
    (repo / "web" / "notes" / "src" / "autonomy-levels-l0-l5.md").write_text("# note\n", encoding="utf-8")
    (repo / "web" / "notes" / "manifest.json").write_text('{"notes": {"a": 1}}\n', encoding="utf-8")
    code, foreign, owned = pt.classify(repo)
    assert code == pt.PUBLISHABLE
    assert foreign == []
    assert sorted(owned) == ["web/notes/manifest.json", "web/notes/src/autonomy-levels-l0-l5.md"]


def test_a_tree_that_cannot_be_read_is_not_reported_as_clean(tmp_path):
    """Invariant 1 on the outward label: `unreadable` is neither `publishable` nor `foreign`.

    This is the case that decides whether the guard is honest. A directory git cannot report on
    yields no dirty paths, and a classifier that turned "no paths" into "clean" would hand the
    scheduler a green light earned by a check that never ran.
    """
    not_a_repo = tmp_path / "elsewhere"
    not_a_repo.mkdir()
    code, foreign, owned = pt.classify(not_a_repo)
    assert code == pt.UNREADABLE
    assert code not in (pt.PUBLISHABLE, pt.FOREIGN_WORK)
    assert (foreign, owned) == ([], [])


@pytest.mark.parametrize(
    ("state", "expected"),
    [("clean", pt.PUBLISHABLE), ("foreign", pt.FOREIGN_WORK), ("unreadable", pt.UNREADABLE)],
)
def test_the_exit_code_reaches_the_caller(tmp_path, state, expected):
    """`notes_cron.py` branches on the PROCESS exit code, not on `classify`'s return value.

    Those are two artefacts and only one of them is what the scheduler reads. A `main()` that
    printed the right verdict and returned 0 for all three would satisfy every test above.
    """
    # THE REPOSITORY IS A SIBLING OF `elsewhere`, NOT ITS PARENT, AND THAT COST A RED RUN.
    # The first version of this case called `_repo(tmp_path)` and then made `tmp_path/elsewhere`,
    # which is INSIDE the repository git had just created - so `git status` answered for the parent
    # repo and the `unreadable` case measured a clean tree. It asserted 4, got 0, and the artefact
    # is kept in `evidence/RED-021-*`. A directory outside a repository is the subject here, and
    # "outside" is a property of the path, not of the name.
    repo = _repo(tmp_path / "repo")
    if state == "foreign":
        (repo / "SPEC.md").write_text("parked\n", encoding="utf-8")
    target = repo if state != "unreadable" else tmp_path / "elsewhere"
    if state == "unreadable":
        target.mkdir()
    done = subprocess.run([sys.executable, str(GATE), "--root", str(target)],
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == expected, done.stderr
