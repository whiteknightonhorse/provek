"""T-0584 - the status page names who a deferred request is waiting on.

THE DEFECT. `ApplyStatus.tsx` said "GitHub's public interface is busy or unreachable" for every
deferred request, which is false for `verifier_red_*` and `live_registry_*` (ours; T-0566-a). The
text is run (`tests/deferral_probe.mjs`), not read, and the source is scanned so the GitHub
sentence stays on the one branch it is true for.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "deferral_probe.mjs"
SRC = ROOT / "web" / "src"


def run(reason: str) -> dict:
    done = subprocess.run(["node", str(PROBE), reason], cwd=ROOT, capture_output=True, timeout=60, check=False)
    assert done.returncode == 0, done.stderr.decode("utf-8", "replace")
    return json.loads(done.stdout.decode("utf-8"))


@pytest.mark.parametrize("reason", [
    "github_rate_limited_until_2026-10-23T12:00:00Z", "github_unreachable_timeout",
    "github_credentials_rejected_http_401",
])
def test_github_reasons_keep_the_github_wording(reason: str) -> None:
    r = run(reason)
    assert r["kind"] == "github" and r["head"] == "Waiting for GitHub."
    assert "busy or unreachable" in r["body"]


@pytest.mark.parametrize("reason,kind", [
    ("verifier_red_measure", "ours"), ("verifier_red_deploy", "ours"), ("verifier_red_confirm", "ours"),
    ("live_registry_unreadable", "registry"),
])
def test_our_own_reasons_do_not_blame_github(reason: str, kind: str) -> None:
    r = run(reason)
    assert r["kind"] == kind
    text = f"{r['head']} {r['body']}".lower()
    assert "github" not in text and "busy or unreachable" not in text, text
    assert "retried" in text


@pytest.mark.parametrize("reason", ["", "something_new"])
def test_an_unread_reason_makes_no_claim_about_who_is_at_fault(reason: str) -> None:
    r = run(reason)
    assert r["kind"] == "unknown"
    assert "github" not in f"{r['head']} {r['body']}".lower()


def test_the_github_sentence_lives_on_the_github_branch_only() -> None:
    hits = [p.relative_to(ROOT).as_posix() for p in SRC.rglob("*")
            if p.is_file() and "busy or unreachable" in p.read_text(encoding="utf-8")]
    assert hits == ["web/src/deferral.js"], hits
    js = (SRC / "deferral.js").read_text(encoding="utf-8")
    branch = re.search(r'case "github":(.*?)case "ours":', js, re.S)
    assert branch and "busy or unreachable" in branch.group(1)
    assert "deferralText(s.reason)" in (SRC / "pages" / "ApplyStatus.tsx").read_text(encoding="utf-8")
