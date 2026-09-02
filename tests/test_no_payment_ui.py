"""Spec 4.2-bis point 6: "no 'pay' button on the site" - newly load-bearing now that
`witnessed_fee_paid` exists on a published schema (WitnessRecord v0). A5/A-6: money never flows
through us, in any phase, so no control on this site may ever be labelled to imply otherwise.

DELIBERATELY A PLAIN PYTEST TEST, NOT A NEW `push.sh` GATE STEP. Adding an eighth door step risks
exactly the door/CI-divergence class of bug this project has paid for twice (`scripts/push.sh`'s
own header) - a pytest test rides the door's EXISTING test step instead.

WHAT THIS DOES NOT CATCH: prose ABOUT payment - "there is no payment step anywhere on this site"
(Apply.tsx, Phase2.tsx) and "a customer pays the agent directly" (describing money that moves
BETWEEN OTHER PARTIES, never through us) are exactly the sentences this project wants on the page.
This test looks for the shape of an actual PRESSABLE LABEL (`>Pay<`, `>Checkout<`, ...), not the
word in prose - the same distinction `tests/test_phase_two_promises_nothing.py`'s
`test_the_page_carries_no_control_that_could_be_pressed` already draws between a control and a
description of one.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_SRC = ROOT / "web" / "src"

# A pressable label, not a word inside a sentence: `>Pay<`, `>Pay Now<`, `>Checkout<`, trailing
# whitespace before the closing tag, or the same words as an aria-label/button value attribute.
_LABEL_SHAPE = re.compile(
    r'>\s*(Pay|Checkout|Purchase|Buy)\b[^<]*<|(?:aria-label|value)="(?:Pay|Checkout|Purchase|Buy)\b',
    re.IGNORECASE)


def test_no_pressable_payment_label_anywhere_in_the_web_source():
    offenders = []
    for f in WEB_SRC.rglob("*.tsx"):
        text = f.read_text(encoding="utf-8")
        for m in _LABEL_SHAPE.finditer(text):
            offenders.append(f"{f.relative_to(ROOT)}: {m.group(0)!r}")
    assert not offenders, (
        "a pressable payment-shaped label was found - A-6 forbids a control implying money moves "
        f"through us, in any phase: {offenders}")


def test_MUTATION_a_real_pay_button_would_be_CAUGHT():
    """Control: proves `_LABEL_SHAPE` actually matches a real offending control, so the assertion
    above is not vacuously green against a pattern that matches nothing."""
    assert _LABEL_SHAPE.search('<button className="cta">Pay</button>')
    assert _LABEL_SHAPE.search('<button aria-label="Checkout">→</button>')
    # Prose is NOT caught - the distinction this test exists to hold.
    assert not _LABEL_SHAPE.search("a customer pays the agent directly")
    assert not _LABEL_SHAPE.search("there is no payment step anywhere on this site")
