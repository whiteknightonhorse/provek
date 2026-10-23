"""T-IN-03 (D-69) - an applicant reads the state of their own request by its id, and only that.

THE DEFECT. The form promised "within about fifteen minutes" and then went silent: a refused
applicant learned nothing, a deferred one learned nothing, a published one had to find their own
row. `GET /api/apply/<id>` is the read path, and its answer is worth exactly two properties, both
asserted by RUNNING the Function (`tests/status_probe.mjs`, the pattern of `tests/intake_probe.mjs`)
rather than reading it:

  1. `state` is exactly one of the five names, taken from the record's own fields. A value the
     endpoint has not learned is `unknown_outcome:<value>`, never a default (invariant 1) - and
     "no such request" is not what an unreadable store or a dangling index says.
  2. The response NEVER carries `contact`, `user_agent`, `source_country` or the consent fields.
     The id is the read capability, and it is held by the applicant; the address they gave us is
     not theirs to be read back by whoever finds the id in a browser history.

Node with a stub is not `workerd`: that the deployed route resolves `/api/apply/<id>` is
Cloudflare's behaviour and is not measured here.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "status_probe.mjs"
ENDPOINT = ROOT / "web" / "functions" / "api" / "apply" / "[id].js"

FIVE = {"received", "deferred", "refused", "published", "withdrawn"}
FORBIDDEN = ("contact", "user_agent", "source_country", "consent", "applicant@example.com",
             "mandate", "delivered")


def run(scenario: str) -> dict:
    """One scenario, or a hard failure. A missing instrument is a red, never a skip (L-16)."""
    assert PROBE.is_file(), f"{PROBE} is missing - every assertion below would be about nothing."
    try:
        done = subprocess.run(["node", str(PROBE), scenario], cwd=ROOT, capture_output=True,
                              timeout=60, check=False)
    except FileNotFoundError:
        raise AssertionError("`node` is not on PATH, so the gate that RUNS the status endpoint "
                             "could not run - reported as a red, not a skip (L-16).") from None
    assert done.returncode == 0, (
        f"the probe exited {done.returncode} on {scenario!r}:\n{done.stderr.decode('utf-8', 'replace')}")
    return json.loads(done.stdout.decode("utf-8"))


@pytest.mark.parametrize("scenario,state", [
    ("received", "received"), ("deferred", "deferred"), ("refused", "refused"),
    ("published", "published"), ("withdrawn", "withdrawn"),
])
def test_each_of_the_five_states_is_named_from_the_record(scenario: str, state: str) -> None:
    r = run(scenario)
    g = r["get"]
    assert g["status"] == 200 and g["body"]["ok"] is True, g
    assert g["body"]["state"] == state, f"{scenario}: {g['body']}"
    assert g["body"]["id"] == r["post"]["body"]["id"], "the id answered is not the id issued"
    assert g["cache"] == "no-store", "a status that can be cached tells the applicant yesterday's state"
    assert g["body"]["received_at"] and g["body"]["repo"] == "https://github.com/example-org/example-repo"


def test_the_reason_and_the_retry_time_are_the_records_own_words() -> None:
    refused = run("refused")["get"]["body"]
    assert refused["reason"] == "repository_did_not_answer_http_404" and refused["next_attempt_after"] is None
    deferred = run("deferred")["get"]["body"]
    assert deferred["reason"] == "github_rate_limited_until_2026-10-23T12:00:00Z", deferred
    assert deferred["next_attempt_after"] == "2026-10-23T12:00:00Z", deferred
    received = run("received")["get"]["body"]
    assert received["reason"] is None and received["next_attempt_after"] is None, (
        f"a reason was invented for a request nobody has judged: {received}")


def test_a_published_request_points_at_its_own_passport() -> None:
    body = run("published")["get"]["body"]
    assert body["registry_url"] == "https://provek.dev/p/git_example-org_example-repo/", body
    assert run("refused")["get"]["body"]["registry_url"] == "https://provek.dev/registry/"


def test_an_outcome_the_endpoint_has_not_learned_is_named_not_defaulted() -> None:
    assert run("unknown_outcome")["get"]["body"]["state"] == "unknown_outcome:quarantined"
    half = run("half_written")["get"]["body"]["state"]
    assert half.startswith("unknown_outcome:") and half not in FIVE, (
        f"a record the run touched but did not conclude was read as {half!r}")


@pytest.mark.parametrize("scenario", [
    "received", "deferred", "refused", "published", "withdrawn", "unknown_outcome", "no_such_request",
])
def test_the_response_never_carries_what_only_the_operator_holds(scenario: str) -> None:
    raw = run(scenario)["get"]["raw"]
    low = raw.lower()
    for word in FORBIDDEN:
        assert word not in low, (
            f"{scenario}: the status response contains {word!r}: {raw}. The id is the read "
            "capability and it is not a licence to read the applicant's address back.")


def test_no_such_request_and_a_malformed_id_are_404_json() -> None:
    for scenario in ("no_such_request", "malformed_id"):
        g = run(scenario)["get"]
        assert g["status"] == 404 and g["body"] == {"ok": False, "state": "no_such_request"}, g


def test_a_dangling_index_is_not_reported_as_no_such_request() -> None:
    g = run("dangling_index")["get"]
    assert g["status"] == 500 and g["body"]["state"] == "record_missing", (
        f"a request that was indexed but cannot be read was called absent: {g}")


def test_the_post_writes_the_index_and_survives_it_failing() -> None:
    ok = run("received")
    assert ok["index"] == ok["key"], f"request-id:<id> does not point at the record's key: {ok['index']}"
    refused = run("index_write_refused")
    assert refused["post"]["status"] == 200 and refused["post"]["body"]["ok"] is True, (
        "a refused index write took the applicant's confirmation down with it")
    assert refused["index"] is None and refused["get"]["status"] == 404


def test_the_endpoint_names_no_private_field_in_its_source() -> None:
    """Belt for the run above: a field the probe's submission leaves empty would not show up there."""
    code = re.sub(r"/\*.*?\*/", "", ENDPOINT.read_text(encoding="utf-8"), flags=re.S)
    code = re.sub(r"//[^\n]*", "", code)
    for field in ("contact", "user_agent", "source_country", "consent"):
        assert field not in code, f"[id].js refers to {field!r} outside a comment"
