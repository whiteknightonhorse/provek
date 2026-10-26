"""LAW-NOTES-LIVE-NUMBERS-CARRY-A-DATE - a note that quotes a live registry number says when.

A method note is prose, and prose outlives the registry it quotes. On 2026-10-26 an external audit
(Opus, 2026-10-24) found the autonomy note still saying that provek "stays L3 because a second
identity remains" while the registry showed one attributed author, and that APIbase had "a single
author" while the registry showed two. Both sentences were once true, neither carried a date, so
nothing told a reader (or a gate) that they were readings rather than rules.

The rule: in `web/notes/src/*.md`, every sentence that states a live quantity - "is L<digit>",
"distinct author", "single author" - contains "as of 20" (a date). A sentence that states the rule
without a number words itself without those phrases. Checked over the committed sources, so it is
armed in CI where `web/dist` does not exist.
"""
from __future__ import annotations

import re

from .notes_support import sources

LIVE = re.compile(r"is L\d|distinct author|single author", re.I)
SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")


def offenders(body: str) -> list[str]:
    return [s.strip() for s in SENTENCE.split(body)
            if LIVE.search(s) and "as of 20" not in s.lower()]


def test_every_sentence_quoting_a_live_number_carries_its_date():
    bad = [(front["slug"], s[:120]) for front, body in sources() for s in offenders(body)]
    assert not bad, f"live numbers without an 'as of 20..' date: {bad}"


def test_the_check_can_fail():
    assert offenders("APIbase has a single author, so it is L3.")
    assert not offenders("As of 2026-10-26, APIbase shows two authors and is L3.")
