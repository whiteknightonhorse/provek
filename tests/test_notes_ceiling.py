"""LAW-NOTES-CEILING - three notes stand until an instrument says whether anyone reads them.

The precedent this work was modelled on gates its publishing rate on indexation health from Google
Search Console: 5-10 pages a day, then 30, then 50, each step unlocked by a measured reading. We
have no Search Console. The instrument that could answer the same question here is Bing Webmaster.

WHAT CHANGED ON 2026-08-21, AND WHY IT CHANGES NOTHING HERE (D-24). Until that day this docstring
said Bing answers `ErrorCode 14 / NotAuthorized` to every per-site call because ownership
verification was unfinished. It is finished: `provek.dev` is a verified property and the per-site
calls answer. The release condition has two halves and only the FIRST of them is now true. There is
still no indexation reading - `GetQueryStats` and `GetLinkCounts` return zero for this property, and
they return zero for an old verified control site as well, so that zero describes what those calls
can see rather than whether anyone has found us. The snapshot files it as `instrument_blind`.

The ceiling therefore stands at three, and the reason belongs in the file that enforces it: "the
property is verified" reads like the condition and is only half of it, and a rate lifted on that
half would be a publishing schedule justified by a gate we walked halfway through.

A rate gated on an instrument that does not exist is not a gate (L-4). The honest form is a ceiling
with a named condition for lifting it, and a ceiling that lives in a sentence is a promise rather
than a gate - so it lives here, and the fourth note fails the build.

CONDITION FOR RAISING IT, named so that it cannot be raised by mood: an indexation reading taken
from the verified `provek.dev` property in Bing Webmaster - a reading, not the verification. Not a
date, not a decision that enough time has passed, and not the operator's or this agent's judgement
that three feels thin.
"""
from __future__ import annotations

import pytest

from .notes_support import SRC, emitted, sources

CEILING = 3


def test_no_more_notes_exist_than_the_ceiling_allows():
    if not SRC.exists():
        pytest.skip("no method notes in this checkout")
    files = sorted(SRC.glob("*.md"))
    assert len(files) <= CEILING, (
        f"{len(files)} note sources, ceiling is {CEILING}. Raising it requires an indexation "
        f"reading from a verified Bing Webmaster property, not an edit to this number.")


def test_the_ceiling_is_the_same_number_the_emit_enforces():
    """Two copies of a rule survive each other's repeal (L-2). This one has two copies by
    necessity - the build must refuse before it writes, and the test must refuse in CI where the
    build has not run - so they are compared instead of trusted."""
    text = (SRC.parent / "emit.mjs").read_text(encoding="utf-8")
    assert f"export const NOTE_CEILING = {CEILING};" in text, (
        "web/notes/emit.mjs and this test no longer agree on the ceiling")


def test_the_emitted_site_carries_no_more_notes_than_were_captured():
    pages = emitted()
    if not pages:
        pytest.skip("site not built in this checkout")
    assert len(pages) == len(sources()) <= CEILING
