"""dependabot-auto-merge.yml runs on pull_request_target with write permission. It must never
check out the PR's code: that would run attacker-controlled files with the elevated token
(T-0579, audit P6-07). Able to fail: the mutation tests append the forbidden forms to a copy."""
from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "dependabot-auto-merge.yml"
FORBIDDEN = [
    ("actions/checkout", re.compile(r"actions/checkout")),
    ("ref: ${{ github.event.pull_request", re.compile(r"ref:\s*\$\{\{\s*github\.event\.pull_request")),
]


def _hits(text: str) -> list[str]:
    return [name for name, rx in FORBIDDEN if rx.search(text)]


def test_the_workflow_never_checks_out_pr_code():
    assert _hits(WORKFLOW.read_text(encoding="utf-8")) == []


def test_mutation_a_checkout_step_is_red(tmp_path):
    copy = tmp_path / "w.yml"
    copy.write_text(WORKFLOW.read_text(encoding="utf-8") + "\n      - uses: actions/checkout@v4\n", encoding="utf-8")
    assert _hits(copy.read_text(encoding="utf-8")) == ["actions/checkout"]


def test_mutation_a_pr_ref_is_red(tmp_path):
    copy = tmp_path / "w.yml"
    copy.write_text(
        WORKFLOW.read_text(encoding="utf-8") + "\n        with:\n          ref: ${{ github.event.pull_request.head.sha }}\n",
        encoding="utf-8",
    )
    assert "ref: ${{ github.event.pull_request" in _hits(copy.read_text(encoding="utf-8"))
