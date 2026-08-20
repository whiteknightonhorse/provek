"""T-2.3. Tests must fail on real breakage, not merely confirm that a file exists."""
import subprocess
import tempfile
from pathlib import Path

from src.abs_profile.measured import NotMeasured
from src.collector.repo import collect, tree_digest


def _make_repo(tmp: Path) -> Path:
    r = tmp / "src_repo"
    r.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=r, check=True)
    subprocess.run(["git", "config", "user.email", "a@b.c"], cwd=r, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=r, check=True)
    (r / "a.py").write_text("print(1)\n")
    subprocess.run(["git", "add", "-A"], cwd=r, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=r, check=True)
    return r


def test_unreachable_remote_gives_UNREADABLE_not_zero():
    """The key invariant: an unreachable source is not a source without signatures."""
    ev = collect("/nonexistent/path/repo.git")
    assert ev.signed_commit_share.is_measured is False
    assert ev.signed_commit_share.absent is NotMeasured.UNREADABLE
    assert ev.head_sha is None
    assert ev.notes and "clone failed" in ev.notes[0]


def test_real_repo_is_measured():
    with tempfile.TemporaryDirectory() as d:
        r = _make_repo(Path(d))
        ev = collect(str(r))
        assert ev.head_sha and len(ev.head_sha) == 40
        assert ev.signed_commit_share.is_measured is True
        assert ev.distinct_authors.value == 1
        assert ev.tree_digest


def test_working_copy_is_deleted_after_audit():
    """Disk budget is 10 GB: foreign clones have no right to persist."""
    import glob
    import tempfile as tf
    before = set(glob.glob(f"{tf.gettempdir()}/incub_*"))
    with tempfile.TemporaryDirectory() as d:
        collect(str(_make_repo(Path(d))))
    after = set(glob.glob(f"{tf.gettempdir()}/incub_*"))
    assert after <= before


def test_tree_digest_changes_with_content():
    """The digest must REACT - otherwise the runtime comparison is meaningless."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "x.txt").write_text("one")
        h1 = tree_digest(p)
        (p / "x.txt").write_text("two")
        assert tree_digest(p) != h1
