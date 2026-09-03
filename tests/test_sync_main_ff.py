"""AUD-003 (Fable, 2026-09-03) - the nightly re-measure must catch `origin/main` moving out from
under it BEFORE it measures, or the push at the end of the chain gets exactly the non-fast-forward
rejection Fable found: `.github/workflows/dependabot-auto-merge.yml` merges patch/minor bumps
straight into GitHub's `main` with no human and no visit to this host, while `scripts/push.sh`
pushes assuming this server's tree already IS the tip. The first auto-merged bump makes both halves
of that assumption false at once.

`scripts/sync_main.sh` is the fix: fetch, then either the fast-forward is free (take it before
`cohort.py` reads a single passport) or the histories have genuinely diverged (refuse by name,
never guess a merge). This suite is the mutation control the task boundary requires: the RED case
below reproduces the exact rejection a real night got with the fix absent from the loop; the GREEN
case shows the same setup succeeding once `sync_main.sh` runs first. A test that could not fail in
the RED case would prove nothing about the GREEN one.

REAL git REPOSITORIES, local-path remotes standing in for GitHub - `sync_main.sh` only splices a
token into the URL when it starts with `https://github.com/` (T-20's own note: this sandbox cannot
even name that token file directly), so these fixtures exercise the fetch/fast-forward/refuse logic
without touching this host's token or network at all.
"""
from __future__ import annotations

import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
SYNC = ROOT / "scripts" / "sync_main.sh"

GIT_ID = ["-c", "user.email=t@example.invalid", "-c", "user.name=t"]


def _run(*args, cwd=None, check=True):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=60, check=check)


def _init_bare(path: pathlib.Path) -> None:
    _run("git", "init", "-q", "--bare", "-b", "main", str(path))


def _clone(origin: pathlib.Path, dest: pathlib.Path) -> None:
    _run("git", "clone", "-q", str(origin), str(dest))


def _commit(repo: pathlib.Path, name: str, text: str) -> str:
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    _run("git", "add", "-A", cwd=repo)
    _run("git", *GIT_ID, "commit", "-qm", name, cwd=repo)
    return _run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()


def _push(repo: pathlib.Path, *, check: bool = True):
    return _run("git", "push", "-q", "origin", "main", cwd=repo, check=check)


def _sync(repo: pathlib.Path) -> subprocess.CompletedProcess:
    """Copies the real script into the fixture repo so `dirname "$0"/..` resolves to it, exactly
    as `nightly_remeasure.sh` invokes `$ROOT/scripts/sync_main.sh` in production."""
    script = repo / "scripts" / "sync_main.sh"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_bytes(SYNC.read_bytes())
    script.chmod(0o755)
    return subprocess.run(["bash", str(script)], cwd=repo, capture_output=True, text=True, timeout=60)


def _dependabot_style_bump(tmp_path: pathlib.Path, name: str):
    """`origin` advances by one commit pushed from a SECOND clone - exactly the shape of an
    auto-merged Dependabot PR: a commit lands on GitHub's `main` that `server`'s own HEAD never
    saw, because nothing on this host was asked."""
    origin = tmp_path / "origin.git"
    _init_bare(origin)

    server = tmp_path / name
    _clone(origin, server)
    base = _commit(server, "seed.txt", "seed\n")
    _push(server)

    dependabot_clone = tmp_path / f"{name}-dependabot"
    _clone(origin, dependabot_clone)
    bumped = _commit(dependabot_clone, "requirements.txt", "dep==2.0\n")
    _push(dependabot_clone)

    return origin, server, base, bumped


def test_red_without_sync_the_nightly_push_is_rejected_non_fast_forward(tmp_path):
    """THE DEFECT ITSELF, reproduced without `sync_main.sh` in the loop: `cohort.py`'s nightly
    commit lands on the stale tree the server still has, and the push at the end of the chain is
    the same non-fast-forward rejection `nightly_remeasure.sh`'s `fail()` alerts on as "STOPPED at
    step push.sh" - not a description of the bug, the bug, reproduced."""
    _, server, base, bumped = _dependabot_style_bump(tmp_path, "red")
    assert base != bumped

    _commit(server, "public/registry/registry.json", "nightly data\n")

    rejected = _push(server, check=False)
    assert rejected.returncode != 0, "a real night got this rejection; the fixture must reproduce it"
    assert "fetch first" in rejected.stderr or "non-fast-forward" in rejected.stderr, rejected.stderr


def test_green_sync_before_measurement_lets_the_same_push_succeed(tmp_path):
    """The fix: `sync_main.sh` runs BEFORE the nightly commit (matching its place in
    `nightly_remeasure.sh`, right after `unset PROVEK_GITHUB_TOKEN` and before `cohort.py`), so the
    server's tree already carries the Dependabot bump by the time it adds its own data commit."""
    _, server, base, bumped = _dependabot_style_bump(tmp_path, "green")

    done = _sync(server)
    assert done.returncode == 0, done.stdout + done.stderr
    head = _run("git", "rev-parse", "HEAD", cwd=server).stdout.strip()
    assert head == bumped, "sync_main.sh should have fast-forwarded onto origin/main's new tip"

    _commit(server, "public/registry/registry.json", "nightly data\n")
    accepted = _push(server, check=False)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr


def test_already_level_is_a_silent_no_op(tmp_path):
    """No Dependabot bump happened tonight - `origin/main` and HEAD already agree, so the fetch
    finds nothing to do."""
    origin = tmp_path / "origin.git"
    _init_bare(origin)
    server = tmp_path / "level"
    _clone(origin, server)
    base = _commit(server, "seed.txt", "seed\n")
    _push(server)

    done = _sync(server)
    assert done.returncode == 0, done.stdout + done.stderr
    assert _run("git", "rev-parse", "HEAD", cwd=server).stdout.strip() == base


def test_a_genuine_divergence_is_a_named_refusal_not_a_guessed_merge(tmp_path):
    """`origin` gained a commit sync_main.sh never saw AND the server independently committed its
    own, unrelated change first - two histories both claiming to be the next `main`. The recommended
    fix picked "fetch + fast-forward OR named red", not "fetch + merge no matter what": resolving a
    real divergence by guessing would publish a choice nobody made."""
    _, server, base, bumped = _dependabot_style_bump(tmp_path, "diverge")
    local_only = _commit(server, "local.txt", "server's own commit, never pushed anywhere\n")

    done = _sync(server)
    assert done.returncode == 1, done.stdout + done.stderr
    assert "DIVERGED" in done.stderr

    head = _run("git", "rev-parse", "HEAD", cwd=server).stdout.strip()
    assert head == local_only, "a refusal must not move HEAD - no merge was attempted"


def test_the_https_token_splice_is_skipped_for_a_non_github_remote(tmp_path):
    """This whole suite runs against local-path origins with no auth of any kind; if
    `sync_main.sh` ever stopped gating its token splice on `https://github.com/` it would try to
    `sudo grep` a token file that does not exist in CI and every case above would fail for the
    wrong reason. Passing is the proof for the fixtures above; this case pins the guard directly by
    reading it back out of the remote configuration the script left behind."""
    _, server, _base, _bumped = _dependabot_style_bump(tmp_path, "guard")
    before = _run("git", "remote", "get-url", "origin", cwd=server).stdout.strip()
    done = _sync(server)
    assert done.returncode == 0, done.stdout + done.stderr
    after = _run("git", "remote", "get-url", "origin", cwd=server).stdout.strip()
    assert after == before, "a local-path remote's URL must be untouched - no token splice applied"
