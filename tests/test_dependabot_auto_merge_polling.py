"""T-07 - the dependabot auto-merge poll loop is judged against a stub `gh`, because the real
polling loop cannot be exercised without a live PR and six hours to spare.

Fable's ruling-1 on `e5e613c` (`taskloop/disputes/07-automerge-waits-for-itself.ruling-1.md`)
rejected that commit for reading an EMPTY check-runs list as "everything is green": on the very
first poll, before GitHub has registered the other nine check-runs against a head SHA that has
existed for a few seconds, `$others` is `[]` - nothing is pending because nothing has been
measured, and `pending -eq 0` was true regardless. The commit merged the PR before a single real
check had run. That is invariant 1 (CLAUDE.md) read backwards, inside the one workflow in this
repository that decides whether to merge unattended.

None of the four distinctions the brief requires - a green patch merges, a red check blocks it by
name, checks that never get registered time out on their own clock rather than merging, and major
never reaches the step at all - can be measured against a live PR in this sandbox: no network, no
`gh` token (the same boundary the ruling and the prior attempt's own report both hit). So the
step's `run:` script is extracted from the workflow YAML EXACTLY AS WRITTEN - not retyped, not
paraphrased - and executed against a `gh` stub this suite fully controls, on loopback/subprocess
boundaries only. `test_workflows_parse.py` already reads this file with a real YAML parser for the
same reason: a checker that retypes what it means to test drifts from what actually ships (L-2).

WHAT THIS SUITE DOES NOT CLAIM. A stub `gh` is not GitHub: it proves the SCRIPT's own branching is
correct given the JSON shapes GitHub's check-runs API is documented to return, not that GitHub
will return them in that shape, or that `gh api`'s pagination and streaming behave exactly as
assumed. The residue is the same one `verify_workflow_yaml.py` names for its own parser - named
rather than closed, because closing it means running GitHub's own infrastructure, which is not on
this host.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "dependabot-auto-merge.yml"
STEP_NAME = "wait for the other checks, then merge patch and minor updates"

REAL_CHECK_NAMES = [
    "CodeQL", "analyze (python)", "analyze (javascript-typescript)", "reproduce",
    "the shipped site", "ratchets", "secret scan", "tests and coverage", "lint and types",
]

# A `gh` that never leaves this process tree. `api` answers from a numbered fixture directory (one
# file per poll, clamped to the last file once the script polls more times than fixtures exist -
# GH_STUB_MAX_INDEX names that clamp explicitly rather than letting a missing file crash the stub
# and get misread as "gh itself failed"). `pr merge` writes a marker instead of touching a real PR.
_GH_STUB = """#!/usr/bin/env bash
set -euo pipefail
if [ "$1" = "api" ]; then
    n=0
    if [ -f "$GH_STUB_COUNTER" ]; then n=$(cat "$GH_STUB_COUNTER"); fi
    echo $((n + 1)) > "$GH_STUB_COUNTER"
    if [ "$n" -gt "$GH_STUB_MAX_INDEX" ]; then n="$GH_STUB_MAX_INDEX"; fi
    jq -c '.[]' "$GH_STUB_SEQ_DIR/$n.json"
elif [ "$1" = "pr" ] && [ "$2" = "merge" ]; then
    echo MERGED > "$GH_STUB_MERGE_MARKER"
else
    echo "unexpected gh invocation: $*" >&2
    exit 99
fi
"""


def _extract_step_script() -> str:
    """The step's `run:` block, read by PyYAML from the live file - never retyped by hand."""
    doc = yaml.safe_load(WORKFLOW.read_text())
    for step in doc["jobs"]["auto-merge"]["steps"]:
        if step.get("name") == STEP_NAME:
            return step["run"]
    raise AssertionError(f"{STEP_NAME!r} step not found in {WORKFLOW}")


def _run_script(script_text: str, seq: list[list[dict]], tmp_path: pathlib.Path,
                 *, wait_limit: int = 5, poll_interval: int = 1,
                 self_run_id: str = "111"):
    """Runs `script_text` (the step's shell body) against a `gh` stub that answers `seq[0]`,
    `seq[1]`, ... on successive `gh api` calls. Returns (returncode, stderr, merged, poll_count)."""
    script_path = tmp_path / "step.sh"
    script_path.write_text(script_text)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_stub = bin_dir / "gh"
    gh_stub.write_text(_GH_STUB)
    gh_stub.chmod(0o755)

    seq_dir = tmp_path / "seq"
    seq_dir.mkdir()
    for i, checks in enumerate(seq):
        (seq_dir / f"{i}.json").write_text(json.dumps(checks))

    marker = tmp_path / "merged.marker"
    counter = tmp_path / "counter"

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env.update(
        PR_URL="https://github.com/whiteknightonhorse/provek/pull/18",
        HEAD_SHA="deadbeefcafe",
        GH_TOKEN="stub",
        GITHUB_REPOSITORY="whiteknightonhorse/provek",
        GITHUB_RUN_ID=self_run_id,
        WAIT_LIMIT_SECONDS=str(wait_limit),
        POLL_INTERVAL_SECONDS=str(poll_interval),
        GH_STUB_SEQ_DIR=str(seq_dir),
        GH_STUB_MAX_INDEX=str(len(seq) - 1),
        GH_STUB_COUNTER=str(counter),
        GH_STUB_MERGE_MARKER=str(marker),
    )
    proc = subprocess.run(
        ["bash", str(script_path)], env=env, capture_output=True, text=True,
        timeout=wait_limit + 20,
    )
    poll_count = int(counter.read_text()) if counter.exists() else 0
    return proc.returncode, proc.stderr, marker.exists(), poll_count


def _green_checks(other_run_id: str = "1115") -> list[dict]:
    """The nine real checks, all green, plus this job's OWN run (id 111) still `in_progress` -
    included so the fixture also exercises self-exclusion, not just the merge decision. `1115`
    deliberately shares the `111` prefix with the self run id: the exclusion filter matches on
    `/runs/111/` with trailing slashes, so a naive substring match on `111` alone would wrongly
    exclude this real check too."""
    checks = [
        {"name": name, "status": "completed", "conclusion": "success",
         "details_url": f"https://github.com/whiteknightonhorse/provek/actions/runs/{other_run_id}/job/1"}
        for name in REAL_CHECK_NAMES
    ]
    checks.append({
        "name": "auto-merge", "status": "in_progress", "conclusion": None,
        "details_url": "https://github.com/whiteknightonhorse/provek/actions/runs/111/job/2",
    })
    return checks


def test_all_green_merges_and_excludes_only_the_self_run(tmp_path):
    rc, stderr, merged, polls = _run_script(_extract_step_script(), [_green_checks()], tmp_path)
    assert rc == 0, stderr
    assert merged, "nine green checks plus the self run should have merged the PR"
    assert polls == 1, "should not have needed a second poll when the first already read all-green"


def test_a_red_check_blocks_the_merge_and_names_it(tmp_path):
    checks = _green_checks()
    checks[3]["conclusion"] = "failure"  # "reproduce"
    rc, stderr, merged, _ = _run_script(_extract_step_script(), [checks], tmp_path)
    assert rc == 1
    assert not merged, "a red check must never merge"
    assert "reproduce" in stderr


def test_checks_never_registered_times_out_instead_of_merging(tmp_path):
    """The exact shape ruling-1 rejected: `gh api` answers `[]` on every poll, forever - GitHub
    has not registered a single other check-run against this head SHA. The pre-fixup script
    (`e5e613c`) read that as `pending == 0` and merged on the very first poll; see
    `evidence/RED-050-empty-check-runs-read-as-all-green.txt` for that script run through this
    same harness. The current script must instead time out, distinguishing "nothing measured yet"
    from "measured and pending" in its own error text (invariant 1)."""
    rc, stderr, merged, polls = _run_script(
        _extract_step_script(), [[]], tmp_path, wait_limit=2, poll_interval=1,
    )
    assert rc == 1
    assert not merged, "an empty check-runs list must never read as all-green"
    assert polls >= 2, "must have kept polling rather than accepting the first empty read"
    assert "no other checks were ever registered" in stderr


def test_checks_pending_past_the_ceiling_times_out_with_its_own_reason(tmp_path):
    """Distinct from the empty case above: here a real check IS registered (`reproduce`,
    `in_progress`) and simply never finishes. The ceiling must still fire, and the error text must
    say "pending", not "never registered" - the two are different states (invariant 1) and an
    operator reading the log needs to know which one happened."""
    stuck = [{
        "name": "reproduce", "status": "in_progress", "conclusion": None,
        "details_url": "https://github.com/whiteknightonhorse/provek/actions/runs/1115/job/1",
    }]
    rc, stderr, merged, polls = _run_script(
        _extract_step_script(), [stuck], tmp_path, wait_limit=2, poll_interval=1,
    )
    assert rc == 1
    assert not merged
    assert polls >= 2
    assert "still pending after" in stderr
    assert "never registered" not in stderr


def test_checks_appearing_after_an_empty_first_poll_still_merge(tmp_path):
    """The guard must not turn into a NEW way to never merge: once the other checks do show up
    and are green, the loop has to notice and merge, not stay stuck refusing forever."""
    seq = [[], [], _green_checks()]
    rc, stderr, merged, polls = _run_script(
        _extract_step_script(), seq, tmp_path, wait_limit=10, poll_interval=1,
    )
    assert rc == 0, stderr
    assert merged
    assert polls == 3, "should have taken exactly the three polls the fixture staged"


def test_major_bumps_never_reach_the_merge_step():
    """Not a runtime fixture - a major bump never reaching this step is enforced by the step's
    OWN `if:`, gated on `dependabot/fetch-metadata`'s output, which this suite cannot fabricate
    without also faking that action. Read the condition instead of assuming it, the same standard
    the brief asked for the `gh` flag check. This is the fourth of the four required distinctions;
    the other three are the runtime tests above."""
    doc = yaml.safe_load(WORKFLOW.read_text())
    job = doc["jobs"]["auto-merge"]
    assert job["if"] == "github.event.pull_request.user.login == 'dependabot[bot]'"
    step = next(s for s in job["steps"] if s.get("name") == STEP_NAME)
    condition = step["if"]
    assert "semver-patch" in condition
    assert "semver-minor" in condition
    assert "major" not in condition.lower()
