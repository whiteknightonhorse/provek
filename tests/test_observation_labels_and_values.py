"""Closes two defects found on the live passport page (measured 2026-08-31, not hypothesised):

DEFECT 1 - `identity_window_closed: {"value": true, "measured": true}` rendered as an EMPTY
CELL. The observations table did `<span>{o.value}</span>`; React renders a bare JS boolean child
as nothing at all, so a measured `true`/`false` - itself the verdict for that row - vanished
silently. `web/src/formatObservation.js` now sits between the raw value and the JSX for exactly
this reason, and this file runs it under Node (`observation_format_probe.mjs`, the way
`tests/slug_probe.mjs` runs `slug.js`) so the proof is about what the function RETURNS, not about
whether a source scan can find its name.

DEFECT 2 - `OBS_LABEL` in `Passport.tsx` carried 5 labels for the 8 observations
`scripts/cohort.py`'s `observations()` actually emits; `identity_window_closed`,
`unlinked_commit_share` and `unlinked_key_count` fell through to their raw machine name. The first
test below reads the SAME dict the emitter returns, not a hand-typed copy of it, so a ninth
observation added later fails this test on day one rather than shipping unlabelled.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PASSPORT_TSX = ROOT / "web" / "src" / "pages" / "Passport.tsx"
COHORT_PY = ROOT / "scripts" / "cohort.py"
PROBE = ROOT / "tests" / "observation_format_probe.mjs"


def _braced_block(text: str, start_marker: str, open_char: str = "{", close_char: str = "}") -> str:
    """Text between the first `open_char` after `start_marker` and its matching `close_char`."""
    i = text.index(start_marker)
    open_pos = text.index(open_char, i)
    depth, end = 0, None
    for j in range(open_pos, len(text)):
        if text[j] == open_char:
            depth += 1
        elif text[j] == close_char:
            depth -= 1
            if depth == 0:
                end = j
                break
    assert end is not None, f"{start_marker!r}: no matching {close_char!r}"
    return text[open_pos:end]


def _emitted_observation_keys() -> set[str]:
    """The keys `scripts/cohort.py::observations()` actually puts in a passport - the ground
    truth, not a hand-maintained list that can drift from it.

    NOT brace-matched: `observations()` defines an inner helper `def m(x): return {...}` before
    its own `return {...}`, and the first `{` after the function signature belongs to THAT inner
    dict (whose keys are `value`/`measured`/`absent_reason`, one level too deep). Anchoring on
    `"key": m(ev.` / `"key": ev.` - the shape only the outer dict's lines have - finds the right
    keys without needing to pick the right brace at all. Bounded by the next top-level `def ` so
    a change elsewhere in the file cannot leak into the match."""
    src = COHORT_PY.read_text(encoding="utf-8")
    start = src.index("def observations(ev) -> dict:")
    end = src.index("\ndef ", start + 1)
    body = src[start:end]
    keys = set(re.findall(r'"(\w+)":\s*(?:m\(ev\.\w+\)|ev\.\w+)', body))
    return keys


def _obs_label_keys() -> set[str]:
    src = PASSPORT_TSX.read_text(encoding="utf-8")
    body = _braced_block(src, "const OBS_LABEL: Record<string, string> = ")
    return set(re.findall(r'(\w+):\s*"', body))


def test_every_emitted_observation_has_a_human_label():
    emitted = _emitted_observation_keys()
    assert emitted, "parsed zero keys out of scripts/cohort.py::observations() - parser is broken"
    labelled = _obs_label_keys()
    missing = emitted - labelled
    assert not missing, (
        f"OBS_LABEL in Passport.tsx has no entry for {sorted(missing)} - these observations "
        "render under their raw machine name instead of a reader-facing label"
    )


def _run(scenario: str):
    assert PROBE.is_file(), f"{PROBE} is missing"
    done = subprocess.run(["node", str(PROBE), scenario],
                           cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stdout + done.stderr
    return json.loads(done.stdout)["result"]


def test_a_measured_boolean_true_renders_as_a_visible_string():
    """The exact shape of defect 1: `identity_window_closed` measured `true` on the live
    provek.dev passport. `result` must be the STRING "true", not the boolean `True` - a formatter
    that forgot the conversion and returned the value unchanged would still pass a truthiness
    check but would still vanish under React's `{value}`, which is the whole defect."""
    result = _run("identity_window_closed_true")
    assert result == "true"
    assert isinstance(result, str)


def test_a_measured_boolean_false_renders_as_a_visible_string_too():
    """`false` is the more dangerous half: `{false}` and `{undefined}` render identically empty,
    so a regression here reads as "nothing measured" rather than as the measured negative it is."""
    result = _run("identity_window_closed_false")
    assert result == "false"


def test_a_zero_share_renders_as_a_percentage_not_a_bare_zero():
    """`signed_commit_share: 0` must read as "0%" (measured, zero of the commits) - the digit
    alone reads as a raw count and invites "zero commits" rather than "zero percent of them"."""
    assert _run("signed_commit_share_zero") == "0%"


def test_a_nonzero_share_renders_as_a_percentage():
    assert _run("signed_commit_share_five_percent") == "5%"


def test_a_share_that_does_not_land_on_a_round_number_keeps_one_decimal():
    assert _run("bot_author_share_third") == "33.3%"


def test_counts_are_not_turned_into_percentages():
    """`distinct_authors`, `workflow_runs` and `unlinked_key_count` are STUCK, not shares -
    multiplying one by 100 would misstate what it counts (317900% CI runs is not a real number)."""
    assert _run("distinct_authors_count") == "2"
    assert _run("workflow_runs_count") == "318"
    assert _run("unlinked_key_count_count") == "0"


def test_the_share_key_list_matches_what_the_collector_actually_divides():
    """`src/collector/github.py` computes exactly these three as `round(n / len(commits), 3)`;
    `distinct_authors`, `workflow_runs` and `unlinked_key_count` are plain `len(...)`/`int(...)`
    counts. A key added to one side without the other is either a count shown as a percentage or
    a percentage shown as a bare integer - this pins the set so that drift fails loudly."""
    assert set(_run("share_keys_list")) == {
        "signed_commit_share", "bot_author_share", "unlinked_commit_share",
    }


def test_passport_tsx_actually_calls_the_tested_formatter():
    """A function this file exercises thoroughly is worth nothing if `Passport.tsx` still renders
    the raw value beside it. Ties the proof above to the live render path."""
    src = PASSPORT_TSX.read_text(encoding="utf-8")
    assert "formatObservationValue" in src, (
        "Passport.tsx no longer imports/uses formatObservationValue - the tests above would be "
        "exercising a function nothing on the page actually calls"
    )
    assert re.search(r"\{\s*o\.value\s*\}", src) is None, (
        "Passport.tsx renders a bare {o.value} again - this is the exact pattern that swallowed "
        "identity_window_closed's measured `true`"
    )
