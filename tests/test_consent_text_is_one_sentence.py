"""The consent wording exists twice, and this is the gate that keeps the two copies one sentence.

WHY TWO COPIES AT ALL. `functions/api/apply.js` is the source: it decides whether a submission is
recorded, and it quotes ITS OWN constant into the stored record rather than anything the client
sent - a client that could name its own consent text could manufacture a record of somebody
agreeing to words they never saw. `src/pages/Apply.tsx` shows the sentence to the visitor, because
the words someone agrees to have to be on the screen where they agree. Neither copy can be deleted.

WHY A TEST RATHER THAN AN IMPORT. The two live in different bundles - a Cloudflare Pages Function
and a Vite client build - and wiring a shared module across that boundary buys a build-time
dependency to avoid a comparison that costs nothing. The project already answered this shape once:
the README verdict block is a copy with a gate behind it. Same reasoning, same gate.

WHAT DRIFT WOULD COST, and it is not tidiness. The page would show one paragraph while the record
stored a different one, and the stored record is the artefact that would be produced later as
evidence of what a person agreed to. A consent record whose text is not the text on the screen is
worse than no record: it is a confident wrong answer to the only question anybody would ask of it.

HOW TO MAKE IT FAIL: change either sentence without the other, or bump the version on one side.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = ROOT / "web" / "functions" / "api" / "apply.js"
PAGE = ROOT / "web" / "src" / "pages" / "Apply.tsx"

VERSION = re.compile(r'CONSENT_VERSION\s*=\s*"([^"]+)"')
# Both files write the sentence as adjacent double-quoted string literals joined by `+`, so the
# pieces are collected and concatenated rather than matched as one literal.
# ReDoS (CodeQL py/redos, alert #55): the previous shape was
#   ((?:\s*"..."\s*\+?)+)
# - an unbounded outer `+` over a group padded by OPTIONAL whitespace on both sides and an
# OPTIONAL `+`. On input that starts to match and then fails, the engine can distribute the same
# run of whitespace between the trailing `\s*` of one repetition and the leading `\s*` of the next
# in exponentially many ways. Rewritten so the concatenation is unambiguous: one literal, then zero
# or more `+ "literal"` groups, with each space belonging to exactly one place it can be.
TEXT = re.compile(r'CONSENT_TEXT\s*=\s*("(?:[^"\\]|\\.)*"(?:\s*\+\s*"(?:[^"\\]|\\.)*")*)\s*;')


def _version(p: Path) -> str:
    m = VERSION.search(p.read_text(encoding="utf-8"))
    assert m is not None, (
        f"{p.name} declares no CONSENT_VERSION. If the constant was renamed, this gate stopped "
        "guarding anything - rename it here in the same commit rather than deleting the test."
    )
    return m.group(1)


def _text(p: Path) -> str:
    m = TEXT.search(p.read_text(encoding="utf-8"))
    assert m is not None, f"{p.name} declares no CONSENT_TEXT as joined string literals"
    return "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1)))


def test_both_files_declare_the_constants() -> None:
    """An absent constant on either side would make the comparison below vacuously green - the
    empty-set case has to be asserted against, not skipped over."""
    for p in (ENDPOINT, PAGE):
        assert _version(p) and _text(p), f"{p.name} declares an empty consent constant"


def test_the_wording_is_identical_on_the_page_and_in_the_record() -> None:
    a, b = _text(ENDPOINT), _text(PAGE)
    assert a == b, (
        "the consent sentence shown on /apply/ is not the sentence the endpoint stores in the "
        "record, so a stored consent would quote words the visitor never saw.\n"
        f"  {ENDPOINT.name}: {a!r}\n  {PAGE.name}: {b!r}"
    )


def test_the_version_is_identical() -> None:
    a, b = _version(ENDPOINT), _version(PAGE)
    assert a == b, (
        f"consent version differs: {ENDPOINT.name} says {a!r}, {PAGE.name} says {b!r}. The endpoint "
        "refuses a submission whose version is not its own, so this drift is a form that always "
        "fails - and it fails by telling the visitor to reload a page that is already current."
    )


def test_the_endpoint_refuses_an_untitcked_box_and_a_stale_version() -> None:
    """The boundary is the endpoint, not the button. A greyed-out button is a courtesy to a person
    using the page; a hand-built POST goes straight past it, and D-21 drew this same line for the
    mandate after exactly that reasoning."""
    src = ENDPOINT.read_text(encoding="utf-8")
    assert "body.consent !== true" in src, (
        "the endpoint does not check the consent flag itself, so consent would be asserted by "
        "whatever a client chose to send"
    )
    assert "clean(body.consent_version) !== CONSENT_VERSION" in src, (
        "the endpoint does not check WHICH wording the client was shown, so agreement to today's "
        "words could be recorded for someone who read an older page"
    )
