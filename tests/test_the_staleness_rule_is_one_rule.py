"""ABI-15-5 is implemented three times, and this is the gate that keeps the three one rule.

WHY THREE. `Passport.effective_status` (Python) decides what a passport IS. `web/src/types.ts`
recomputes it at read time, because a value that expires cannot be baked into the artefact that
expires with it. `web/functions/_lib/status.js` recomputes it again inside a Cloudflare Worker,
which can import neither of the other two: the badge is served per request precisely so that a
lapsed passport stops looking green without waiting for a rebuild.

None of the three can be deleted. So the rule is written three times, which is a rule written in
more than one place - and a rule written twice survives its own repeal, because the day somebody
corrects one copy the others go on being believed.

WHAT IS ASSERTED HERE, and it is narrow on purpose: the COMPARISON. `now >= valid_until` versus
`now > valid_until` is a one-character difference that no reviewer notices and that changes the
verdict for every passport at the exact moment of expiry - the boundary each copy already has its
own behavioural test for. Those tests prove each copy does what it says; this one proves they say
the same thing.

WHAT IS NOT ASSERTED: that the three produce identical output over a range of inputs. That would
need a Passport instance built here, and the three behavioural suites already cover each copy's
own boundary. Stated rather than implied, because a docstring that claims a stronger check than
the code performs is the defect this repository is about.

HOW TO MAKE IT FAIL: change `>=` to `>` in any one of the three, or reword the TypeScript
expression without rewording the Worker's.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "src" / "passport" / "passport.py"
TS = ROOT / "web" / "src" / "types.ts"
JS = ROOT / "web" / "functions" / "_lib" / "status.js"

PY_CMP = re.compile(r"now\s*(>=?|<=?)\s*self\.valid_until")
WEB_CMP = re.compile(r"now\s*(>=?|<=?)\s*new Date\(validUntil\)")


def _one(pattern: re.Pattern[str], path: Path) -> str:
    hits = pattern.findall(path.read_text(encoding="utf-8"))
    assert hits, (
        f"{path.name} no longer compares `now` against the expiry in the shape this gate reads. "
        "If the implementation was rewritten, teach this gate the new shape in the same commit - "
        "a gate that silently stops matching reports success on what it cannot see."
    )
    assert len(set(hits)) == 1, f"{path.name} compares the expiry {len(set(hits))} different ways: {hits}"
    return hits[0]


def test_all_three_copies_use_the_same_comparison() -> None:
    ops = {PY.name: _one(PY_CMP, PY), TS.name: _one(WEB_CMP, TS), JS.name: _one(WEB_CMP, JS)}
    assert len(set(ops.values())) == 1, (
        "the staleness rule is spelled differently in different places, so a passport can be "
        f"`stale` in one surface and `verified` in another at the same instant: {ops}"
    )


def test_the_comparison_is_inclusive_so_the_boundary_itself_is_stale() -> None:
    """`>` would leave a passport `verified` for the whole instant it expires. Small, and exactly
    the kind of edge a claim about expiry is judged on."""
    for name, op in (("python", _one(PY_CMP, PY)), ("web", _one(WEB_CMP, TS)), ("worker", _one(WEB_CMP, JS))):
        assert op == ">=", (
            f"the {name} copy uses `{op}`, so a record is still `verified` at the exact moment it "
            "expires. ABI-15-5 lapses ON the boundary, and the badge's own boundary test asserts it."
        )
