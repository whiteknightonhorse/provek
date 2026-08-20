#!/usr/bin/env python3
"""T-2.12 - the production caller. Spends the incubator's own mandate on one real probe
(ABI-6-4, ABI-5-1, ABI-16-5).

WHY A SCRIPT AND NOT A TEST. A test that reaches the network has two failure modes that look
identical - the subject changed, or this host has no route out - and the usual repair is a
`skipif`, which is the line that made four suites in this repository assert nothing in exactly the
state that shipped a defect (L-16). So the suite exercises the prober through an injected
transport and never skips, and the LIVE reading is taken here, deliberately, and kept in
`evidence/` where a run that found something is an artefact rather than a build status.

WHAT IT MAY COST THE SUBJECT: three GET requests - a public page, a path that does not exist, and
the probed path. The mandate's blast radius forbids the POST that would write a durable record and
page a human (`src/prober/self_probe.py`), and this file makes no POST - the method comes from the
claim.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.prober.prober import ProbeResult, probe  # noqa: E402
from src.prober.self_probe import SELF_MANDATE, SOURCE_EXPOSURE_CLAIM  # noqa: E402

TIMEOUT_S = 20

USER_AGENT = "provek-verifier/0.1 (+https://provek.dev; mandate self-mandate-0002)"
"""THE PROBE SAYS WHO IT IS AND UNDER WHAT AUTHORITY, and both halves are load-bearing.

An unauthenticated access attempt arriving anonymously is indistinguishable, in the subject's logs,
from the attack it imitates. A subject who has signed a mandate must be able to find our requests
and match them to the document they signed - otherwise the mandate governs an act nobody can
attribute, and the abort condition it carries is unusable by the only person entitled to invoke it.

It is also what makes the reading possible at all here: this origin answers 403 to Python's default
agent and 200 to a named one (L-11). Note carefully that identifying ourselves is not a way of
DEFEATING that refusal - the control request is. If the origin refuses this agent too, the probe
reports ORIGIN_UNREADABLE instead of dressing the refusal up as a finding."""

CURL_FAILURE = {
    # A NUMBER IS NOT A REASON (L-23). `curl rc=35` was once written into a report as the cause,
    # and establishing that it meant "this host offers no certificate at all" - a fact about the
    # subject - rather than "we timed out" - a fact about us - took a separate investigation.
    6: "the host name did not resolve",
    7: "the connection was refused",
    28: f"no answer within {TIMEOUT_S}s",
    35: "the TLS handshake failed - the host may serve no certificate at all",
    60: "the certificate did not verify",
}


def fetch(method: str, url: str):
    """The transport. Returns a `Response`, and names every failure rather than numbering it."""
    from src.prober.prober import Response

    try:
        p = subprocess.run(
            ["curl", "-4", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "-X", method, "-A", USER_AGENT, "--max-time", str(TIMEOUT_S), url],
            capture_output=True, text=True, timeout=TIMEOUT_S + 10)
    except (subprocess.SubprocessError, OSError) as e:
        return Response(None, f"the probe could not run curl at all: {type(e).__name__}")
    if p.returncode != 0:
        return Response(None, CURL_FAILURE.get(
            p.returncode, f"transport failure curl reports as {p.returncode} and this table does "
                          f"not name - open it before treating the reading as absence"))
    code = p.stdout.strip()
    if not code.isdigit() or code == "000":
        # curl prints 000 when it exited zero without an HTTP exchange. Reading that as a status
        # would put a fake number where a named absence belongs.
        return Response(None, f"curl succeeded without an HTTP status (wrote {code!r})")
    return Response(int(code), f"http {code}")


def report(r: ProbeResult) -> list[str]:
    """The reading, in full. Everything a reader needs to recompute the verdict."""
    out = [
        "=== ACTIVE PROBE, live run ===",
        f"subject:        {r.claim.subject_id}",
        f"origin:         {r.claim.origin}",
        f"claim:          {r.claim.method} {r.claim.protected_path} answers "
        f"{sorted(r.claim.expected_refusal)}",
        f"claimed by:     {r.claim.claimed_by}",
        f"mandate:        {r.mandate_ref or '(none - nothing authorised this)'}",
        f"calls made:     {r.calls_made}",
    ]
    if r.denial is not None:
        out.append(f"denied:         {r.denial.value}")
    readings = (("control ", r.control, r.claim.control_path),
                ("absent  ", r.absent, r.claim.absent_path),
                ("subject ", r.subject, r.claim.protected_path))
    for name, resp, path in readings:
        if resp is None:
            out.append(f"{name}{path}: NOT REQUESTED")
        else:
            out.append(f"{name}{path}: status={resp.status if resp.answered else 'none'} "
                       f"({resp.reason})")
    out += [
        f"state:          {r.state.value}",
        f"not measured:   {r.not_measured.value if r.not_measured else '(a measurement was taken)'}",
        f"VERDICT:        {r.verdict()}",
    ]
    return out


CALLS_LAST_HOUR = 0
"""WHAT THIS DOES NOT DO, NAMED RATHER THAN IMPLIED BY A ZERO (Fable's finding).

`may_probe` enforces the mandate's hourly ceiling against the number it is given, and nothing here
persists a count between invocations - so what the ceiling actually bounds today is ONE run, not an
hour. This script makes exactly one probe and exits, so no run has ever approached twelve; that is
a property of the caller and not of the limiter, and the difference is precisely the kind that gets
described as working until something loops.

The zero is therefore a declared position and not a default: a persistent ledger is what a caller
that runs on a schedule would need, and it is not built. Anything that starts calling `probe()`
more than once must thread a real count through here, and this constant is where it goes.
"""


def main() -> int:
    result = probe(SOURCE_EXPOSURE_CLAIM, SELF_MANDATE, datetime.now(timezone.utc), fetch,
                   calls_last_hour=CALLS_LAST_HOUR)
    print("\n".join(report(result)))
    # THE EXIT CODE SEPARATES THREE STATES AND NOT TWO. A probe that could not run is not a probe
    # that found nothing wrong, and a caller handed 0 for both would treat our own blindness as the
    # subject's clean bill of health - which is the defect this whole repository is about.
    return {"PASS": 0, "FAIL": 1, "NOT_MEASURED": 2}[result.verdict()]


if __name__ == "__main__":
    sys.exit(main())
