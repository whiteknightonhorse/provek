"""LAW-EMITTED-IDS-UNIQUE - no emitted page may define the same `id` twice.

WHY THIS EXISTS, AND WHY IT IS NOT A TIDINESS GATE. The note figures are inline SVGs, and their
hatch patterns lived in a module-level `<defs>` block with fixed ids (`pv-hatch`, `pv-cross`). One
figure to a page hid that completely. The first note to place TWO figures emitted both blocks, so
the page carried each id twice, and the W3C validator refused the live page on 2026-08-24.

The validation error is the smaller half. `url(#pv-hatch)` resolves to the FIRST element with that
id, so the second figure's hatched areas were painted from the first figure's definition - and the
hatch is the fill that distinguishes an instrument's refusal from a small measurement. A duplicate
id here is not a lint finding; it is the one drawing on the site whose whole job is to keep
`unreadable` from looking like a low number, quietly reading from the wrong source.

WHAT IT SWEEPS. Every emitted page, not only the notes. The defect was found on a note, but nothing
about it is note-specific: any two components that hard-code the same id collide the moment a page
renders both, and the emitted document is the only place that is visible (L-3 - a component in
isolation is not what the reader receives).

WHAT IS NOT ASSERTED. That ids are referenced correctly, or that every `url(#...)` resolves. This
reads duplicates only. The narrower claim is the one the evidence supports.
"""
from __future__ import annotations

import re
from collections import Counter

from .notes_support import DIST

# `id="..."` in emitted HTML and SVG. The emit is ours and quotes every attribute; a bare unquoted
# id would be missed here, and would also be a shape nothing in this repository produces.
ID = re.compile(r'\sid="([^"]+)"')


def emitted_pages() -> dict[str, str]:
    return {
        str(p.relative_to(DIST)): p.read_text(encoding="utf-8")
        for p in sorted(DIST.rglob("*.html"))
    }


def test_the_sweep_has_something_to_read():
    """A build that emitted nothing must not report every page as clean.

    Zero pages and zero duplicates are the same green, and this is the counter that separates them
    (invariant 1). `scripts/push.sh` and CI both build the site before the suite runs, so an empty
    `web/dist` here means the sweep did not run rather than that the site is small.
    """
    pages = emitted_pages()
    assert pages, (
        f"no emitted pages under {DIST} - the site was not built, so this sweep measured nothing. "
        f"That is 'check_did_not_run', not a clean result."
    )


def test_no_emitted_page_defines_an_id_twice():
    offenders = {}
    for name, html in emitted_pages().items():
        dupes = {i: n for i, n in Counter(ID.findall(html)).items() if n > 1}
        if dupes:
            offenders[name] = dupes
    assert not offenders, (
        "duplicate ids in emitted pages: "
        + "; ".join(f"{page} -> {d}" for page, d in sorted(offenders.items()))
        + ". A reference like url(#x) or href=#x resolves to the first match, so the second "
          "element is silently painted or linked from the first one's definition."
    )
