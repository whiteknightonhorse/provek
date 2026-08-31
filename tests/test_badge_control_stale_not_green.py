"""The control this task's acceptance gate names explicitly: a passport whose STORED status is
still `verified` but whose evidence window has closed must render as `stale` on the badge - never
as the healthy word. `web/functions/badge/[id].js` is the reason an `<img>` tag can ever be
correct about this at all: it runs no JavaScript, so nothing on the reader's side can recompute the
date the way a hydrated page does, and the badge has to be right on its own, per request.

`tests/badge_probe.mjs` runs the real handler under Node with a stubbed `env.ASSETS` (a copy of the
real passport data, dated in the past) - the same instrument shape `tests/intake_probe.mjs` set for
`apply.js`, for the same reason: a source scan can prove `effectiveStatus(...)` is written and can
never prove what the SVG actually says.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "badge_probe.mjs"
FUNCTION = ROOT / "web" / "functions" / "badge" / "[id].js"


def run(scenario: str) -> dict:
    assert PROBE.is_file(), f"{PROBE} is missing"
    assert FUNCTION.is_file(), f"{FUNCTION} is missing"
    done = subprocess.run(["node", str(PROBE), scenario],
                           cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stdout + done.stderr
    return json.loads(done.stdout)


def test_a_healthy_passport_reads_verified():
    r = run("verified_with_projection")
    assert r["status"] == 200
    assert "VERIFIED" in r["body"]
    assert "STALE" not in r["body"]


def test_THE_CONTROL_a_lapsed_passport_reads_stale_not_the_stored_word():
    """Same subject, only `valid_until` moved into the past. The stored `status` field in the
    fixture is still literally "verified" - if this reads VERIFIED, the badge is printing the
    field instead of computing it, which is the exact defect ABI-15-5 exists to name."""
    healthy = run("verified_with_projection")
    lapsed = run("verified_lapsed_shows_stale")
    assert "STALE" in lapsed["body"], lapsed["body"]
    assert "VERIFIED" not in lapsed["body"], (
        "the badge printed the stored word for a lapsed passport - never green over stale")
    # And it is not merely a different colour on the same word: the two bodies must actually say
    # different things, or a control that always renders "STALE" beside a matching colour would
    # pass this file by coincidence.
    assert healthy["body"] != lapsed["body"]


def test_an_unmeasured_projection_says_so_rather_than_a_number():
    r = run("unverified_no_projection")
    assert r["status"] == 200
    assert "projection: not measured" in r["body"]


def test_a_measured_projection_is_labelled():
    r = run("verified_with_projection")
    assert "projection 60/100" in r["body"]


def test_a_negative_verdict_still_answers_200_with_its_own_colour_class():
    r = run("suspended")
    assert r["status"] == 200
    assert "SUSPENDED" in r["body"]


def test_an_unknown_slug_answers_200_not_a_broken_image():
    r = run("unknown_slug")
    assert r["status"] == 200
    assert "PROVEK" in r["body"]


def test_a_malformed_slug_is_refused_before_any_fetch():
    r = run("malformed_id")
    assert r["status"] == 200
    assert r["fetched"] is False, "an unsafe slug reached env.ASSETS.fetch"


def test_a_request_missing_the_svg_suffix_is_400():
    r = run("missing_svg_extension")
    assert r["status"] == 400


def test_an_unreachable_asset_store_is_not_a_500():
    r = run("asset_fetch_throws")
    assert r["status"] == 200
    assert "PROVEK" in r["body"]


def test_content_type_and_cache_headers():
    r = run("verified_with_projection")
    assert r["contentType"] is not None and "image/svg+xml" in r["contentType"]
    assert r["cacheControl"] is not None
    m = re.search(r"max-age=(\d+)", r["cacheControl"])
    assert m, r["cacheControl"]
    # Short - so a lapse into `stale` (needs no new evidence, only the date to pass) is never left
    # showing the old word for long behind the CDN's cache.
    assert int(m.group(1)) <= 600, f"cache is not short: {r['cacheControl']}"
