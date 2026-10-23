"""T-IN-06 (QA-1023 D-1, D-4, D-5) - the intake judges what was sent, not a prefix of it.

THE DEFECTS, each measured against the pre-change endpoint:
  * `clean()` did `slice(0, 2000)` BEFORE the regex ran, so a 2100-character URL was stored as 2000
    characters (record 9d6d3dbb...): a value the applicant never sent, accepted as the one they did.
  * a body of `null` parsed, then threw on `body.website` - Cloudflare 1101 instead of a sentence.
  * `request.json()` ignores the content-type, so a cross-origin `text/plain` POST (no preflight)
    wrote a record.
  * `<b>@x.y` was a stored contact address; `../..` was a stored repository.

WHAT RUNS: the real Function under Node with a stub KV (`tests/intake_probe.mjs`), asserting on the
ANSWER and on what reached the store. WHAT DOES NOT: `workerd`, and the 1101 itself - the stub
reports the handler's own answer, so "a sentence, not a throw" is what is measured.

THE ORDER MUTATION. With the tightened regexes a 2000-character prefix of an over-long URL is
refused anyway (the name is capped at 100), so reverting ONLY the order is invisible. The mutant
therefore restores the old `clean` (slice first) AND the old looser regexes - the pair the 2100-char
record passed through - and must answer 200 where the real file answers 400.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "intake_probe.mjs"
APPLY = ROOT / "web" / "functions" / "api" / "apply.js"


def run(scenario: str, module: Path | None = None) -> dict:
    assert PROBE.is_file(), f"{PROBE} is missing - every assertion below would be about nothing."
    argv = ["node", str(PROBE), scenario] + ([str(module)] if module else [])
    try:
        done = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=60, check=False)
    except FileNotFoundError:
        raise AssertionError("`node` is not on PATH, so the gate that RUNS the intake could not "
                             "run - a red, not a skip (L-16).") from None
    assert done.returncode == 0, f"probe exited {done.returncode}: {done.stderr.decode()}"
    return json.loads(done.stdout.decode())


def stored_requests(r: dict) -> list:
    return [w for w in r["writes"] if w["key"].startswith("request:") and w["stored"]]


@pytest.mark.parametrize("scenario,status", [
    ("repo_2100_chars", 400), ("body_null", 400), ("body_array", 400), ("body_text_plain", 415),
    ("contact_tag", 400), ("repo_dotdot", 400), ("repo_dotdot_name", 400),
])
def test_refused_inputs_answer_a_sentence_and_store_nothing(scenario: str, status: int) -> None:
    r = run(scenario)
    assert r["outcome"] == "answered", f"{scenario}: the handler threw ({r.get('error')}), not a sentence"
    assert r["status"] == status, r
    assert r["body"]["ok"] is False and isinstance(r["body"]["error"], str) and r["body"]["error"]
    assert r["writes"] == [], f"{scenario}: a refused request reached the store: {r['writes']}"


def test_text_plain_is_refused_with_the_json_sentence() -> None:
    assert run("body_text_plain")["body"]["error"] == "Send JSON (content-type: application/json)."


def test_null_body_is_the_unreadable_body_sentence() -> None:
    assert run("body_null")["body"]["error"] == "The request body could not be read."


@pytest.mark.parametrize("scenario", ["contact_dotted", "repo_dotted_name", "both_writes_land"])
def test_the_controls_still_pass(scenario: str) -> None:
    """Without these, every refusal above would also pass on a handler that refuses everything."""
    r = run(scenario)
    assert r["status"] == 200 and r["body"]["ok"] is True, r
    assert len(stored_requests(r)) >= 1


def test_the_dotted_repository_is_stored_as_sent() -> None:
    rec = stored_requests(run("repo_dotted_name"))[0]["value"]
    assert rec["repo"] == "https://github.com/o/r.name"


def test_the_order_mutant_accepts_what_the_real_file_refuses() -> None:
    src = APPLY.read_text(encoding="utf-8")
    mutant, n1 = re.subn(
        r"function clean\(v, max = MAX\) \{.*?\n\}\n",
        'function clean(v, max = MAX) {\n  return typeof v === "string" ? v.trim().slice(0, MAX) : "";\n}\n',
        src, count=1, flags=re.S)
    mutant, n2 = re.subn(r"/\^https:\\/\\/github\\\.com\\/\[A-Za-z0-9\].*?\$/\.test\(repo\)",
                         r"/^https:\\/\\/github\\.com\\/[\\w.-]+\\/[\\w.-]+\\/?$/.test(repo)",
                         mutant, count=1)
    assert (n1, n2) == (1, 1), "the mutation no longer applies - rewrite it rather than delete it"
    assert mutant != src
    with tempfile.TemporaryDirectory() as d:
        copy = Path(d) / "apply_mutant.mjs"
        copy.write_text(mutant, encoding="utf-8")
        r = run("repo_2100_chars", copy)
    assert r["status"] == 200, (
        f"the slice-first mutant answered {r['status']}: the scenario cannot tell the orders apart")
    stored = stored_requests(r)[0]["value"]["repo"]
    assert len(stored) == 2000, "the mutant stored something other than the 2000-character prefix"
