"""A published passport must be reproducible by a reader who holds nothing.

`optional_token` says a token "changes the budget, never the evidence". Measured 2026-08-25, that
is true of the SCORE and false of the DOCUMENT: run the cohort with a credential and the passport
of a private subject stops saying `unreadable` and starts carrying signed_commit_share,
distinct_authors, workflow_runs and head_sha -- none of which an anonymous reader can recompute.
The projection stays withheld and the access channel is stamped, so nothing published is a lie;
but the artefact begins to depend on who built it, and every page of this site promises a verdict
a third party can reproduce from the same inputs.

The refusal lives at the point of writing. This test keeps it there.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(env_extra):
    import os
    env = dict(os.environ)
    env.pop("PROVEK_GITHUB_TOKEN", None)
    env.update(env_extra)
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "cohort.py")],
                          cwd=str(ROOT), capture_output=True, text=True, env=env, timeout=120)


def test_a_credentialed_run_refuses_before_writing_anything():
    before = (ROOT / "public" / "registry" / "registry.json").read_bytes()
    r = _run({"PROVEK_GITHUB_TOKEN": "ghp_this_is_not_a_real_token"})
    assert r.returncode != 0, "a credentialed run was allowed to proceed"
    assert "REFUSED" in (r.stdout + r.stderr), f"refused without saying so: {r.stdout[-300:]}"
    after = (ROOT / "public" / "registry" / "registry.json").read_bytes()
    assert before == after, "the refusal came AFTER something was already written"


def test_the_refusal_names_the_variable_and_the_reason():
    """A refusal whose cause is invisible is the shape that gets a gate deleted."""
    r = _run({"PROVEK_GITHUB_TOKEN": "ghp_this_is_not_a_real_token"})
    text = r.stdout + r.stderr
    assert "PROVEK_GITHUB_TOKEN" in text, "the refusal does not name what to unset"
    assert "reproduc" in text.lower(), "the refusal does not say why it refuses"
