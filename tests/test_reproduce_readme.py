"""T-63 - the README's own "## Run it" block is EXECUTED, not merely read.

WHY THIS EXISTS. A dispatcher's audit on 2026-09-03, from a fresh clone under a user with none of
this project's dependencies preinstalled, found `python3 -m pip install -r requirements/ci-tests.txt`
refused by pip: "In --require-hashes mode, all requirements must have their versions pinned with
==... coverage[toml]>=7.10.6 ... (from pytest-cov==7.1.0)". `requirements/ci-tests.txt` was not
the defect - it installs cleanly under the pip this host had already upgraded to, which is exactly
the blindness AUD-011 named about T-62's own "verified on a fresh clone" check: the verifying
environment already held the thing being verified. There it was a preinstalled PyYAML; here it was
an already-modern pip. pytest-cov 7.1.0 unconditionally declares `coverage[toml]>=7.10.6` in its
own METADATA (checked directly, not guessed), and a stock pip - whatever `python -m venv`
bootstraps from ensurepip, untouched - does not treat the plain `coverage==7.15.4` pin already in
the file as satisfying that extras-qualified request. It goes looking for a fresh, unpinned
`coverage[toml]` instead, and hash-checking mode (armed automatically the moment any requirement in
the file carries a hash - D-30) correctly refuses an unpinned line. README.md now upgrades pip
before installing the pinned set, which fixes this regardless of which pip the reader started with
(measured directly: pip 22.0.2 fails, pip 26.2.1 succeeds, upgrading a 22.0.2 venv in place fixes
it). This test is what stands watch over that line staying there.

WHAT IT DOES, NOT WHAT IT ARGUES. Every command under "## Run it" is extracted from README.md
itself - not retyped - and RUN, in order, inside a genuinely fresh clone and a genuinely fresh
virtualenv (ensurepip's own pip, never upgraded by anything outside the commands under test). A
hand-maintained copy of the commands is exactly the drift this project's own audit already found
once (AUD-011: a line was fixed, a fresh clone stayed red, because the fix was verified somewhere
that had already stopped being fresh).

WHY IT SKIPS BY DEFAULT, AND WHAT ARMS IT. This is the one test in the suite that clones itself:
the tree it clones carries this very file, and the README command it runs includes `python3 -m
pytest -q` - the WHOLE suite, including this test again. Unguarded, that does not merely cost time,
it recurses without bound. `_REPRODUCE_ENV` is read once, at import time: absent - the default,
and what every OTHER invocation of this suite sees (the bare "tests" CI job, `scripts/push.sh`'s
step 7, a nested clone) - this test SKIPS; the one job that means to run it (`reproduce` in
gates.yml, and its door counterpart) sets it, and the subprocess environment built below
deliberately DROPS the variable before the nested `pytest -q` runs, so recursion is exactly one
clone deep and no deeper. A test that recurses without a floor is not a stricter check, it is a
fork bomb wearing a green tick.

WHAT THIS DOES NOT PROVE. That pip stays broken forever on an old release, or that `--upgrade pip`
remains sufficient against a future `pytest-cov` that changes its own dependency shape again - this
test is only as good as pytest-cov 7.1.0's actual metadata staying what pip resolves today, which
is exactly the part `--require-hashes` already pins for the RESULT and cannot pin for pip's own
resolution BEHAVIOUR. Nor does it prove the block works for a reader whose network cannot reach
GitHub: the clone below is a local path, substituted for the README's own URL, because gating this
suite on github.com's reachability would be a new, unrelated failure mode. See
`_run_it_commands` for exactly where that substitution happens and why the untouched line is still
asserted against, so a future change to it is a decision and not a silent drift.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import venv

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CLONE_LINE = "git clone https://github.com/whiteknightonhorse/provek && cd provek"

_REPRODUCE_ENV = "PROVEK_REPRODUCE_README"

pytestmark = pytest.mark.skipif(
    os.environ.get(_REPRODUCE_ENV) != "1",
    reason=(f"clones, installs and builds from scratch - too slow and too networked for the bare "
            f"suite; armed by {_REPRODUCE_ENV}=1 in its own CI job and door step, see the module "
            f"docstring for why a default run must NOT include this test"),
)


def _run_it_commands() -> list[str]:
    """The fenced ```bash block under '## Run it' in README.md, one shell command per element."""
    text = README.read_text(encoding="utf-8")
    m = re.search(r"## Run it\n.*?```bash\n(.*?)\n```", text, re.DOTALL)
    assert m, "README.md's '## Run it' section no longer holds a ```bash fence - fix the extraction here, not just the doc"
    commands = []
    for raw in m.group(1).splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if line.strip():
            commands.append(line.strip())
    assert commands, "the extracted Run it block is empty"
    assert commands[0] == CLONE_LINE, (
        f"the clone line changed shape ({commands[0]!r}) - update the local-path substitution in "
        "this test along with it; widening this assertion instead would hide the change from the "
        "one place that is supposed to notice it")
    return commands


def test_readme_run_it_succeeds_from_a_genuinely_fresh_clone(tmp_path):
    """Clone this tree fresh, then run README's own commands, unmodified, against that clone."""
    commands = _run_it_commands()

    clone_dir = tmp_path / "provek"
    subprocess.run(
        ["git", "clone", "--depth", "1", f"file://{ROOT}", str(clone_dir)],
        check=True, capture_output=True, text=True,
    )

    venv_dir = tmp_path / "venv"
    venv.create(venv_dir, with_pip=True)

    env = dict(os.environ)
    env.pop(_REPRODUCE_ENV, None)  # exactly one clone deep - see the module docstring
    env["PATH"] = f"{venv_dir / 'bin'}{os.pathsep}{env.get('PATH', '')}"

    for command in commands[1:]:  # [0] is the clone above, done with a local path instead of the URL
        result = subprocess.run(
            ["bash", "-c", command], cwd=clone_dir, env=env,
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            continue
        # `scripts/cohort.py` reads the public GitHub API with no credential (the README's own
        # promise), and `skip_rate_limited` in that script deliberately raises SystemExit -
        # printing "rate_limited: ..." rather than swallowing it - the moment the anonymous 60/hr
        # budget runs out mid-run. That is cohort.py refusing to publish a half-updated registry
        # in silence (invariant 1, not_measured is a state of its own), not a defect this gate
        # exists to catch, and a shared CI runner IP is exactly where an anonymous budget runs out
        # fastest. Failing the WHOLE gate on somebody else's rate limit would be the false-red L-5
        # warns about, so only THIS command, and only THIS one documented cause, is let through.
        if command == commands[-1] and "rate_limited:" in result.stderr:
            continue
        assert result.returncode == 0, (
            f"`{command}` failed (exit {result.returncode}) on a fresh clone + fresh venv:\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}")
