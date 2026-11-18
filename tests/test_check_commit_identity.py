"""T-ID-01 - the door reads who wrote an unpushed commit.

On 2026-11-12 a task session committed c57c779 with
`git -c user.name=incubator -c user.email=incubator@localhost commit`. The platform attributed it to
no account, this repository's identity window opened and its level fell from L3 to L2. Nothing at
the door read the author of a commit. scripts/check_commit_identity.py reads author and committer of
every commit in `origin/main..HEAD`, and only that range.

Each case runs in a temporary repository with a bare `origin`.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_commit_identity.py"
DOOR = ROOT / "scripts" / "push.sh"

ALLOWED = ("Claude", "noreply@anthropic.com")


def _git(repo: Path, *args: str, ident: tuple[str, str] = ALLOWED) -> str:
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
           "GIT_AUTHOR_NAME": ident[0], "GIT_AUTHOR_EMAIL": ident[1],
           "GIT_COMMITTER_NAME": ident[0], "GIT_COMMITTER_EMAIL": ident[1]}
    r = subprocess.run(["git", "-C", str(repo), *args], env=env, capture_output=True, text=True)
    assert r.returncode == 0, f"git {args}: {r.stderr}"
    return r.stdout.strip()


def _repo(tmp_path: Path, *, fetch: bool = True) -> Path:
    """A working repository whose `origin` is a bare repository holding one pushed commit."""
    bare = tmp_path / "origin.git"
    work = tmp_path / "work"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)
    _git(work, "remote", "add", "origin", str(bare))
    (work / "a.txt").write_text("a\n", encoding="utf-8")
    _git(work, "add", "a.txt")
    _git(work, "commit", "-q", "-m", "first")
    if fetch:
        _git(work, "push", "-q", "origin", "main")
        _git(work, "fetch", "-q", "origin")
    return work


def _commit(work: Path, name: str, *extra: str, ident: tuple[str, str] = ALLOWED) -> str:
    (work / f"{name}.txt").write_text(name + "\n", encoding="utf-8")
    _git(work, "add", f"{name}.txt")
    _git(work, *extra, "commit", "-q", "-m", name, ident=ident)
    return _git(work, "rev-parse", "HEAD")


def _run(work: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(work)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def test_allowed_identity_is_ok(tmp_path):
    work = _repo(tmp_path)
    _commit(work, "one")
    _commit(work, "two")
    rc, out = _run(work)
    assert rc == 0 and "identity: ok 2 commits" in out, out


def test_a_commit_made_with_the_2026_11_12_command_is_refused_and_named(tmp_path):
    work = _repo(tmp_path)
    sha = _commit(work, "bad", "-c", "user.name=incubator", "-c", "user.email=incubator@localhost",
                  ident=("incubator", "incubator@localhost"))
    rc, out = _run(work)
    assert rc == 1, out
    assert f"identity: REFUSED {sha[:7]} author " in out and "incubator@localhost" in out, out
    assert "git commit --amend --reset-author --no-edit" in out
    assert "never force-push" in out


def test_allowed_author_with_a_foreign_committer_is_refused(tmp_path):
    work = _repo(tmp_path)
    (work / "x.txt").write_text("x\n", encoding="utf-8")
    _git(work, "add", "x.txt")
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
           "GIT_AUTHOR_NAME": ALLOWED[0], "GIT_AUTHOR_EMAIL": ALLOWED[1],
           "GIT_COMMITTER_NAME": "incubator", "GIT_COMMITTER_EMAIL": "incubator@localhost"}
    subprocess.run(["git", "-C", str(work), "commit", "-q", "-m", "x"], env=env, check=True)
    sha = _git(work, "rev-parse", "HEAD")
    rc, out = _run(work)
    assert rc == 1, out
    assert f"identity: REFUSED {sha[:7]} author noreply@anthropic.com committer incubator@localhost" \
        in out, out


def test_no_origin_main_is_unreadable_not_empty(tmp_path):
    work = _repo(tmp_path, fetch=False)
    rc, out = _run(work)
    assert rc == 2 and out.startswith("identity: unreadable "), out
    assert "nothing_to_check" not in out and "identity: ok" not in out


def test_an_empty_range_is_nothing_to_check(tmp_path):
    work = _repo(tmp_path)
    rc, out = _run(work)
    assert rc == 0 and "identity: nothing_to_check" in out, out


def test_the_door_runs_it_before_step_one_and_not_through_and():
    lines = DOOR.read_text(encoding="utf-8").splitlines()
    step1 = next(n for n, ln in enumerate(lines) if ln.startswith('echo "1/9'))
    hits = [n for n, ln in enumerate(lines) if "check_commit_identity.py" in ln
            and not ln.lstrip().startswith("#")]
    assert len(hits) == 1 and hits[0] < step1, hits
    line = lines[hits[0]].strip()
    assert line.startswith("python3 scripts/check_commit_identity.py"), line
    assert "&&" not in line and "||" not in line and ";" not in line, line
    prev = [ln for ln in lines[:hits[0]] if ln.strip() and not ln.lstrip().startswith("#")]
    assert not prev[-1].rstrip().endswith("&&"), "joined to the line before it"
    assert [ln for ln in lines if ln.startswith('echo "')][:1] == [lines[step1]]
