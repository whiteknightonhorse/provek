"""T-SG-14 (`~/taskloop/briefs/SG-00-ruling-1.md` §SG-14, incubator's own decision in
`DECISIONS.md`): `?plain=1` on `web/functions/badge/[id].js` renders status and expiry only - no
projection row, labelled or otherwise. `tests/test_badge_never_prints_a_bare_level.py` already
proves the default badge never leaks a BARE level; this file proves the plain branch goes further
and never prints the projection AT ALL, over the real handler under Node (`tests/badge_probe.mjs`),
not a source read.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "badge_probe.mjs"

NUMBER = re.compile(r"\d")


def run(scenario: str) -> dict:
    done = subprocess.run(["node", str(PROBE), scenario],
                           cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stdout + done.stderr
    return json.loads(done.stdout)


TEXT_CONTENT = re.compile(r"<text\b[^>]*>([^<]*)</text>")


def test_the_healthy_plain_badge_carries_no_digit_at_all():
    """The strongest statement this file can make: not "no bare level", not "no number without
    its label" - literally no digit in anything a reader (or a screen reader, off `<title>`) would
    see, except the date, which this test allows for explicitly rather than by omission. Scoped to
    the rendered text nodes and the `<title>`, not the raw markup - `width="280"`, `viewBox`, pixel
    coordinates and `font-size` are SVG plumbing no reader ever sees as a number about the subject."""
    r = run("verified_plain")
    assert r["status"] == 200
    title = re.search(r"<title>([^<]*)</title>", r["body"]).group(1)
    visible = "".join(TEXT_CONTENT.findall(r["body"])) + title
    visible_without_date = visible.replace("2099-01-01", "")
    assert not NUMBER.search(visible_without_date), (
        f"plain badge printed a digit outside the date: {visible!r}")


def test_plain_still_recomputes_stale_from_the_date_not_the_stored_word():
    """The one guarantee `?plain=1` may not drop: ABI-15-5. A plain badge that kept reading
    `stale` correctly but only the numbered one recomputed it would be a regression hiding behind
    a feature that looks unrelated."""
    healthy = run("verified_plain")
    lapsed = run("verified_lapsed_plain")
    assert "VERIFIED" in healthy["body"] and "STALE" not in healthy["body"]
    assert "STALE" in lapsed["body"] and "VERIFIED" not in lapsed["body"], lapsed["body"]


def test_plain_still_names_status_and_the_expiry_date():
    """SG-14's own words: "only status and term" - dropping the projection row must not silently
    drop the two things the ruling explicitly kept."""
    r = run("verified_plain")
    assert "VERIFIED" in r["body"]
    assert "valid until 2099-01-01" in r["body"]


def test_plain_drops_the_projection_row_entirely_not_just_its_number():
    """SG-14's own words: "only status and term" - `?plain=1` on an unmeasured subject must not
    fall through to a THIRD row reading "projection: not measured". That row carries no digit
    (`test_the_healthy_plain_badge_carries_no_digit_at_all` would not catch it), but it is still
    the projection row the ruling asked to be gone, not merely de-numbered."""
    r = run("verified_plain")
    assert "projection" not in r["body"].lower(), (
        f"plain badge still carries a projection row: {r['body']}")


def test_the_default_badge_is_unchanged_when_plain_is_absent():
    """`?plain=1` is an addition, not a rewrite - the existing numbered badge (and every test in
    `tests/test_badge_never_prints_a_bare_level.py` and
    `tests/test_badge_control_stale_not_green.py`) must keep reading exactly as before."""
    r = run("verified_with_projection")
    assert "projection 60/100" in r["body"]
