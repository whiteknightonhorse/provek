"""T-S6 - the concurrency lock is taken on a path the project owns, and a lock that was NOT taken
says so instead of reporting contention.

WHY THIS FILE EXISTS. `scripts/run_budgeted.sh` holds the only enforcement of "concurrency = 1
process" in CLAUDE.md's resource budget. Until T-S6 it held it on `/tmp/incubator.slot.lock`, a
fixed name in a mode-1777 directory shared with nine other projects on this host, and it had two
outcomes where there are three: `flock` returning anything other than success was printed as "the
slot is held by another run". So a lock that could not be opened, and a `flock` that was not
installed, both announced a healthy concurrency limit with a neighbour inside it - at the exact
moment the limit had stopped existing. That is invariant 1 pointed at the guarantee itself rather
than at a counter.

WHAT IS ASSERTED HERE: the script's behaviour, by running it. Every case below invokes the real
file with a real command and checks whether that command RAN, because "it printed a refusal" and
"it did not do the work" are two claims and only the second one is the guarantee. The marker file
is the instrument, and `test_the_work_runs_when_the_slot_is_free` is the control that proves the
instrument can register a run at all - without it every refusal test below would pass against a
script that never works.

WHAT IS NOT ASSERTED. The control case stubs `systemd-run`, so it proves the LOCK path reaches the
work; it does not prove the work lands in the right cgroup slice, and nothing here measures the
memory cap. The suite runs on hosts with no user systemd session (CI is one), so asserting the
real `systemd-run` would make this file red over the environment rather than over the script.

Red run: `evidence/RED-033-a-lock-that-was-never-taken-reported-as-contention.txt`.
"""
from __future__ import annotations

import fcntl
import os
import pathlib
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_budgeted.sh"

REFUSED, DEFERRED = 70, 75          # EX_SOFTWARE, EX_TEMPFAIL - and they must not be the same

SYSTEMD_STUB = """#!/bin/sh
# Stand-in for `systemd-run --user --scope ...`: drop the leading options and run the rest.
while [ $# -gt 0 ]; do case "$1" in --*) shift ;; *) break ;; esac; done
exec "$@"
"""

FLOCK_NOT_INSTALLED = """#!/bin/sh
exit 127
"""


def _project(tmp_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """A throwaway checkout holding a copy of the script.

    The script derives its lock from its OWN location, which is what makes this possible: the copy
    locks inside the copy. That is also the property under test - a hardcoded path could not be
    exercised without writing to the real one.
    """
    proj = tmp_path / "proj"
    (proj / "scripts").mkdir(parents=True)
    dst = proj / "scripts" / "run_budgeted.sh"
    shutil.copy2(SCRIPT, dst)
    return proj, dst


def _stubs(tmp_path: pathlib.Path, bodies: dict[str, str]) -> pathlib.Path:
    """A PATH prefix holding stand-ins.

    `systemd-run` is stubbed in EVERY case below, including the ones that expect a refusal, and
    that is load-bearing rather than tidy. Those cases assert that the work did NOT run - and on a
    host with no user systemd session the work cannot run whatever the script decides, so the
    assertion would hold against a completely broken script and report it green. CI is such a host.
    A gate that passes because the environment cannot perform the failure is L-16's "present, not
    armed", so the stub makes the work runnable everywhere and leaves the script as the only thing
    that can prevent it.
    """
    d = tmp_path / "bin"
    d.mkdir(exist_ok=True)
    for name, body in bodies.items():
        p = d / name
        p.write_text(body, encoding="utf-8")
        p.chmod(0o755)
    return d


def _runnable(tmp_path: pathlib.Path, **extra: str) -> pathlib.Path:
    return _stubs(tmp_path, {"systemd-run": SYSTEMD_STUB, **extra})


def _invoke(script: pathlib.Path, marker: pathlib.Path, *,
            path_prefix: pathlib.Path | None = None,
            fd9: pathlib.Path | None = None) -> subprocess.CompletedProcess:
    work = ["touch", str(marker)]
    if fd9 is None:
        cmd = [str(script), *work]
    else:
        # Hand the script a descriptor 9 that is ALREADY OPEN, the way a calling script would.
        cmd = ["bash", "-c", 'exec 9>"$1"; shift; exec "$@"',
               "fd9-probe", str(fd9), str(script), *work]
    env = dict(os.environ)
    if path_prefix is not None:
        env["PATH"] = f"{path_prefix}{os.pathsep}{env['PATH']}"
    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60, check=False)


def test_the_work_runs_when_the_slot_is_free(tmp_path):
    """THE CONTROL, and it asserts nothing else on purpose.

    Without this, every refusal below is satisfied by a script that refuses unconditionally. It is
    kept minimal - exit 0 and the work ran - so that a mutation reproducing the ORIGINAL defect
    still leaves the measuring apparatus standing to be measured with.
    """
    _proj, script = _project(tmp_path)
    marker = tmp_path / "ran"
    r = _invoke(script, marker, path_prefix=_runnable(tmp_path))
    assert r.returncode == 0, r.stderr
    assert marker.exists(), "the work did not run on a free slot, so nothing below measures a refusal"


def test_the_lock_is_taken_inside_the_project_and_not_on_a_shared_path(tmp_path):
    """The move itself, read off behaviour rather than off the source.

    The script derives its lock from its own location, so the copy under `tmp_path` must lock
    inside the copy. A script still naming `/tmp` passes the control above and fails here.
    """
    proj, script = _project(tmp_path)
    marker = tmp_path / "ran"
    r = _invoke(script, marker, path_prefix=_runnable(tmp_path))
    assert r.returncode == 0, r.stderr
    assert (proj / ".state" / "slot.lock").exists(), \
        "the run did not leave a lock inside the project it was launched from"


def test_a_state_directory_that_cannot_be_created_is_a_refusal_and_runs_nothing(tmp_path):
    proj, script = _project(tmp_path)
    marker = tmp_path / "ran"
    proj.chmod(0o500)                      # readable and traversable, not writable
    try:
        r = _invoke(script, marker, path_prefix=_runnable(tmp_path))
    finally:
        proj.chmod(0o700)                  # or the tmp_path teardown cannot remove it
    assert r.returncode == REFUSED, r.stderr
    assert not marker.exists(), "the budget was not established and the work ran anyway"
    assert "REFUSED" in r.stderr


def test_a_lock_that_cannot_be_opened_is_a_refusal_and_not_a_report_of_contention(tmp_path):
    proj, script = _project(tmp_path)
    marker = tmp_path / "ran"
    state = proj / ".state"
    state.mkdir(mode=0o700)
    (state / "slot.lock").touch()
    (state / "slot.lock").chmod(0o000)
    r = _invoke(script, marker, path_prefix=_runnable(tmp_path))
    assert r.returncode == REFUSED, r.stderr
    assert not marker.exists()
    assert "REFUSED" in r.stderr
    assert "held by another run" not in r.stderr, \
        "a lock that was never opened was reported as a busy neighbour - the defect T-S6 repaired"


def test_an_unopenable_lock_does_not_sail_through_on_an_inherited_descriptor(tmp_path):
    """THE SILENT ONE. `exec 9>` failing does not close a descriptor 9 that arrived open.

    Measured on the previous form: with fd 9 inherited, the failed open left the CALLER's file in
    place, `flock -n 9` locked that instead, and the work ran to completion with exit 0 and no
    error printed anywhere. Neither exit codes nor stderr wording can catch this one - only asking
    whether the work ran.
    """
    proj, script = _project(tmp_path)
    marker = tmp_path / "ran"
    state = proj / ".state"
    state.mkdir(mode=0o700)
    (state / "slot.lock").touch()
    (state / "slot.lock").chmod(0o000)
    unrelated = tmp_path / "someone-elses-file"
    unrelated.touch()
    r = _invoke(script, marker, fd9=unrelated, path_prefix=_runnable(tmp_path))
    assert not marker.exists(), \
        "the work ran while the slot lock was never taken - concurrency=1 silently did not exist"
    assert r.returncode == REFUSED, r.stderr


def test_a_lock_path_that_resolves_somewhere_else_is_refused(tmp_path):
    """THE HIJACK IN ITS PRECISE FORM, and the one case an open-succeeded check cannot see.

    A neighbour who got to the path first leaves a SYMLINK. `exec 9>` follows it and succeeds,
    `flock` locks the target's inode perfectly happily, and this project's runs then serialise
    against a file of somebody else's choosing - or against nothing, if the target is shared with
    a process that never locks it. Every status code involved says success, so the descriptor is
    resolved back through `/proc/self/fd/9` and compared with the path the script named.
    """
    proj, script = _project(tmp_path)
    marker = tmp_path / "ran"
    state = proj / ".state"
    state.mkdir(mode=0o700)
    elsewhere = tmp_path / "a-neighbours-file"
    elsewhere.touch()
    (state / "slot.lock").symlink_to(elsewhere)
    r = _invoke(script, marker, path_prefix=_runnable(tmp_path))
    assert not marker.exists(), \
        "the work ran while the lock held was a file the project never named"
    assert r.returncode == REFUSED, r.stderr


def test_an_instrument_that_did_not_run_is_not_reported_as_a_busy_slot(tmp_path):
    """`flock` exiting 127 is what a MISSING flock looks like. It is not_measured, not 'busy'."""
    proj, script = _project(tmp_path)
    marker = tmp_path / "ran"
    r = _invoke(script, marker, path_prefix=_runnable(tmp_path, flock=FLOCK_NOT_INSTALLED))
    assert r.returncode == REFUSED, r.stderr
    assert not marker.exists()
    assert "REFUSED" in r.stderr
    assert "DEFERRED" not in r.stderr, "an absent instrument was announced as a neighbour's run"


def test_a_slot_genuinely_held_by_another_run_defers_and_says_so(tmp_path):
    proj, script = _project(tmp_path)
    marker = tmp_path / "ran"
    state = proj / ".state"
    state.mkdir(mode=0o700)
    with open(state / "slot.lock", "w") as holder:
        fcntl.flock(holder.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        r = _invoke(script, marker, path_prefix=_runnable(tmp_path))
    assert r.returncode == DEFERRED, r.stderr
    assert not marker.exists()
    assert "DEFERRED" in r.stderr
    assert "REFUSED" not in r.stderr, \
        "a real deferral was reported as a broken guarantee - the confusion runs both ways"


def test_neither_repaired_path_still_names_the_shared_tmp_directory(tmp_path):
    """The two write paths T-S6 moved, asserted by source.

    NARROW ON PURPOSE. This covers exactly the two files the task repaired. A repository-wide ban
    on `/tmp/` literals is imaginable and cheap, and it is deliberately NOT here: the finding that
    raised these two paths left that question to the judge, and an executor arming a rule nobody
    ratified is the same overreach in the opposite direction. `tests/test_amadeus_demo.py:345` and
    `tests/test_pip_pinned.py:93` hold the only other `/tmp/` literals in the tree; both are string
    arguments inside assertions, neither opens anything, and they are named here so the next reader
    does not recount them.
    """
    for rel in ("scripts/run_budgeted.sh", "scripts/measure_qm2.py"):
        src = (ROOT / rel).read_text(encoding="utf-8")
        code = [ln for ln in src.splitlines()
                if ln.strip() and not ln.lstrip().startswith("#")]
        assert not any("/tmp/" in ln for ln in code), \
            f"{rel} still names a fixed path under the host's shared /tmp"
