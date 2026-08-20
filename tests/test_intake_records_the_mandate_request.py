"""D-23 in machine form: the intake may ASK about an active mandate and may never GRANT one.

WHAT THIS FILE REPLACES, AND WHAT IT KEEPS. Until 2026-08-20 this gate was
`test_intake_offers_no_active_mandate.py`: D-21 had withdrawn the probing mandate from the form
because no prober existed to honour it, and the gate held the withdrawal at the ENDPOINT rather
than only on the page. That distinction was the whole finding. `apply.js` read

    const mandate = body.mandate === "active" ? "active" : "passive";

which honours "active" for every client that is not the form, so a `curl` POST could grant a
probing mandate over production and have it validated, written durably to KV and announced to the
operator as though a person had agreed to it. Removing a control from a page removes the OFFER, not
the capability; the form is not the security boundary (L-2).

T-2.12 built the prober, so the offer returns (D-23) - and the capability must stay exactly where
D-21 put it. So the rule this file enforces is not the old one relaxed. It is two rules:

  1. `mandate_applied` is assigned a CONSTANT "passive" in the endpoint. No request body, from the
     form or from anywhere else, can change what we are permitted to do. A mandate is a legal
     object and not a checkbox (`src/mandate/mandate.py`): it must state permitted actions, their
     limits, what must not be affected, liability, an abort condition and how it is revoked, and an
     HTTP field carries none of that.
  2. The applicant's own answer is recorded rather than overwritten. `mandate_requested` and
     `mandate_applied` are separate keys in the stored record, because "asked for active, refused"
     and "asked for passive" are two states of the world - and until today they were one field.
     The comment in `apply.js` that named this defect deferred it explicitly until a prober existed
     and the two values could differ. They can differ now.

WHY BOTH DIRECTIONS ARE ASSERTED. A gate holding only rule 1 goes green on an endpoint that has
quietly dropped the request field, which is D-21's collapse restored; a gate holding only rule 2
goes green on an endpoint that honours what it recorded. Each rule is the other's failure mode.

WHAT IS NOT ASSERTED, and it is the more important half today. That the DEPLOYED endpoint behaves
this way. `/api/apply` is a Cloudflare Pages Function and this test reads the repository. That gap
used to be named here and left open, which is diligence performed rather than work done (L-25). It
is now MEASURED, and it is open: on 2026-08-20 `GET https://provek.dev/api/apply` answered 404 where
this file's subject answers 405 — what a path serves when its function was never published at all
(`evidence/PROBE-001.txt`, D-23). So every assertion below is true of the repository and false of
the origin, and saying which is which is the entire method of this project.

Two edges on the comment stripper, both put there after Fable found them rather than by foresight.
Line comments are matched as `(?<!:)//`, because a plain `//` swallows the tail of every URL - the
Telegram endpoint and the form's placeholder both contain one, and a ternary sharing a line with a
URL would have been invisible. And the tokens below are matched inside their own syntax rather than
as bare substrings, because `"active"` alone also fires on `interactive`, on a Tailwind `active:`
variant and on `document.activeElement`: a gate that goes red for a word which grants nothing is
how a suite gets skipped.

HOW TO MAKE IT FAIL: restore the ternary in `apply.js`, or collapse the two fields back into one.
The red run is kept as `evidence/RED-014-intake-grants-what-it-was-asked.txt`.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = ROOT / "web" / "functions" / "api" / "apply.js"
FORM = ROOT / "web" / "src" / "pages" / "Apply.tsx"

BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT = re.compile(r"(?<!:)//[^\n]*")
JSX_COMMENT = re.compile(r"\{\s*/\*.*?\*/\s*\}", re.DOTALL)


def _code(path: Path) -> str:
    """Source with comments removed, so the gate never reads its own explanation."""
    text = path.read_text(encoding="utf-8")
    text = JSX_COMMENT.sub("", text)
    text = BLOCK_COMMENT.sub("", text)
    return LINE_COMMENT.sub("", text)


def test_the_files_this_gate_guards_still_exist() -> None:
    """A gate pointed at a moved file reports clean forever - L-16's shape."""
    for path in (ENDPOINT, FORM):
        assert path.is_file(), (
            f"{path} is missing. This gate enforces D-23 against it; if the intake moved, move "
            "this test in the same commit rather than letting it pass over nothing."
        )


def test_the_comment_stripper_still_strips() -> None:
    """INSTRUMENT CONTROL. Every assertion below reads `_code()`, and a stripper that returned the
    whole file - or an empty string - would turn several of them into statements about prose. The
    old version of this gate quoted the forbidden ternary in its own docstring for exactly this
    reason, and a stripper that had stopped working would have found it there."""
    assert _code(ENDPOINT).count("D-21") == 0, "the stripper is leaking comments into the code"
    assert "onRequestPost" in _code(ENDPOINT), "the stripper has eaten the code as well"


def test_the_applied_policy_is_a_constant_and_not_a_choice_the_caller_makes() -> None:
    code = _code(ENDPOINT)
    assert re.search(r'\bconst\s+mandate_applied\s*=\s*"passive"\s*;', code), (
        "web/functions/api/apply.js no longer assigns `mandate_applied` the constant \"passive\". "
        "The intake may ask about an active probing mandate and may never grant one: a mandate is "
        "a legal object, not a checkbox, and no HTTP field can carry permitted actions, a rate "
        "ceiling, a blast radius, liability, an abort condition and a revocation route. The "
        "version this gate was written against made exactly this mistake with "
        '`body.mandate === "active" ? "active" : "passive"`, which honours "active" for any client '
        "that is not the form - see D-21 and D-23."
    )


def test_the_applied_policy_is_never_computed_from_the_request() -> None:
    """The specific shape D-21 found: a value reaching the applied field from the body.

    Asserting the constant above is not enough on its own. A second assignment, a reassignment, or
    a ternary written elsewhere would leave the constant standing and the property gone - which is
    L-21, where three repairs in a gate were defined, documented and never called.
    """
    code = _code(ENDPOINT)
    for line in re.findall(r"[^\n]*mandate_applied[^\n]*", code):
        assert "body." not in line, (
            f"`mandate_applied` is computed from the request body in: {line.strip()!r}. What we "
            "are permitted to do may not be decided by the party asking us to do it."
        )


def test_the_request_is_recorded_rather_than_overwritten() -> None:
    """Invariant 1 at the intake: "asked for active, refused" is not "asked for passive"."""
    code = _code(ENDPOINT)
    assert "mandate_requested" in code, (
        "web/functions/api/apply.js no longer records `mandate_requested`. Collapsing it into the "
        "applied policy makes a refused request and a request that never asked read identically in "
        "KV - the one-value-two-worlds defect, in the field that decides whether a human has to "
        "write back with a document."
    )
    assert re.search(r"\brecord\s*=\s*\{[^}]*\bmandate_requested\b[^}]*\bmandate_applied\b",
                     code, re.DOTALL), (
        "the stored record does not carry BOTH mandate fields. A value the endpoint computes and "
        "does not store is a measurement taken and thrown away."
    )


def test_an_unrecognised_mandate_value_is_refused_rather_than_guessed() -> None:
    """A default would put our assumption in the field that records the applicant's answer.

    This is the fail-closed direction of the pair: coercing an unknown value to `passive` sounds
    safe and is the exact move that made the old single field meaningless.
    """
    code = _code(ENDPOINT)
    assert re.search(r'requested\s*!==\s*"passive"\s*&&\s*requested\s*!==\s*"active"', code), (
        "web/functions/api/apply.js no longer refuses an unrecognised `mandate` value. Guessing "
        "one records our assumption as the applicant's request."
    )


def test_the_form_sends_a_value_the_endpoint_will_accept() -> None:
    """The two halves are edited by different hands at different times, and nothing else compares
    them. D-20's lesson in miniature: when two copies of a rule exist, the finding is the absence
    of the comparison and not the value that differed."""
    code = _code(FORM)
    offered = set(re.findall(r'value="(passive|active)"', code))
    assert offered == {"passive", "active"}, (
        f"the form offers {sorted(offered) or 'no mandate values'}; the endpoint accepts exactly "
        '"passive" and "active" and refuses everything else, so any other option on the page is a '
        "control that returns an error when it is used."
    )
    assert re.search(r"\bmandate:\s*asked\b", code), (
        "the form no longer sends the applicant's choice to the endpoint. A control that does not "
        "reach the endpoint is a question asked and discarded, which is worse than not asking."
    )
