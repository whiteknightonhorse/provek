"""The badge and the brief page share one `effectiveStatus` (ABI-15-5's third copy - see the
header of `web/functions/_lib/status.js` for why a fourth was not written instead). This runs it
directly, the way `tests/test_passport_slug_is_judged_before_it_is_fetched.py` runs `slug.js`,
rather than trusting a source scan to know what the function returns.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "effective_status_probe.mjs"


def run(scenario: str):
    assert PROBE.is_file(), f"{PROBE} is missing"
    done = subprocess.run(["node", str(PROBE), scenario],
                           cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stdout + done.stderr
    return json.loads(done.stdout)["result"]


def test_verified_before_expiry_reads_verified():
    assert run("verified_before_expiry") == "verified"


def test_verified_past_expiry_lapses_to_stale_with_no_event():
    assert run("verified_lapsed") == "stale"


def test_the_boundary_itself_is_stale_not_verified():
    """`now >= valid_until`, not `>` - the instant of expiry is already lapsed."""
    assert run("verified_exactly_at_boundary") == "stale"


def test_a_status_other_than_verified_is_never_touched_by_the_date():
    assert run("unverified_untouched_by_the_date") == "unverified"
    assert run("suspended_untouched_by_the_date") == "suspended"
