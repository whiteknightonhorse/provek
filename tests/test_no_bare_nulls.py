"""LAW-NO-BARE-NULLS - a null in the machine artefact must say which world it means.

Ordered by Fable, 2026-08-20, as the CLASS-level fix behind the accountability defect. His
diagnosis: LAW-NOT-MEASURED was embodied in the `Measurement` class rather than enforced at the
artefact boundary, so every field that reached `to_machine()` by another path was protected by
nothing. The invariant that slipped was the one no machine proved; the one proven by an AST test
(scorer/transport independence) never slipped.

A null is admissible only if the document itself says which state of the world it means:

  1. it sits beside a `measured` flag - the wrapper carries the distinction, and carries it under
     quotation, which is why the wrapper is per field rather than a coverage list elsewhere;
  2. it is a `*_absent_reason` whose paired value key is present - the pair is the wrapper;
  3. it is named in WHITELIST below, with its single meaning written HERE, in code that runs.

Anything else fails. That direction is deliberate: a checker that skips the shapes it does not
recognise reports success on precisely what it cannot handle. Comments asserting what a null means
are what failed in schema 1.0.0 - `passport.py` documented "an honest none" while three emitters
shipped "nobody looked", and nothing was positioned to notice.
"""
from __future__ import annotations

import pytest

from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.identity import Binding, BindingKind
from src.abs_profile.ladder import L
from src.passport.passport import Accountability, Fact, Provenance, build
from src.verify.control_map import ControlMap, Coverage, Surface
from src.verify.scorer import projection, score_operation

# Each entry states the ONE meaning the null carries. An entry is a decision, not a silence:
# adding one means writing the meaning down where a test can be pointed at it.
WHITELIST: dict[str, str] = {
    "/mandate_ref": (
        "no active probing was performed. Single meaning today because no code path emits a "
        "mandate reference it failed to read - if one ever does, this field needs the wrapper. "
        "Flagged to Fable as the same species as the accountability fields, not yet acute."
    ),
}

PROV = Provenance("1.0.0", "1.0.0", 30)
COV = Coverage([Surface.GITHUB], {"treasury": "no access"}, "a key in CI")


def _bare_nulls(node: object, path: str = "", parent: dict | None = None) -> list[str]:
    """Every null path that the document does not explain."""
    out: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            out += _bare_nulls(v, f"{path}/{k}", node)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out += _bare_nulls(v, f"{path}[{i}]", parent)
    elif node is None:
        key = path.rsplit("/", 1)[-1]
        wrapped = parent is not None and "measured" in parent
        paired = (key.endswith("_absent_reason") and parent is not None
                  and key[: -len("_absent_reason")] in parent)
        if not (wrapped or paired or path in WHITELIST):
            out.append(path)
    return out


def _passport(**kw):
    scores = [
        score_operation("development_initiation", L.L2, (EvidenceClass.PLATFORM_OBSERVED,), 5,
                        weak_mixed_signal=True, runtime_trace=False),
        score_operation("deployment", None, ()),
        score_operation("treasury_control", None, ()),
    ]
    return build(Binding(BindingKind.GIT, "a/b"), scores, ControlMap([], COV),
                 projection(scores), PROV, kw.pop("accountability", Accountability()), **kw)


@pytest.mark.parametrize("accountability", [
    Accountability(),                                        # nothing inspected
    Accountability(claims_addressee=Fact.none_found()),      # inspected, none found
    Accountability(emergency_stop=Fact.of(True),             # inspected, present
                   insurance=Fact.unreadable()),             # inspected, source refused
])
def test_no_bare_nulls_in_the_emitted_artefact(accountability):
    machine = _passport(accountability=accountability).to_machine()
    assert _bare_nulls(machine) == []


def test_the_gate_actually_fires():
    """A control. A checker never exercised against a real failure is not evidence of anything.

    This is the shape schema 1.0.0 shipped: a null with nothing beside it to say which world it
    means. If this assertion ever stops failing, the gate has gone blind.
    """
    machine = _passport().to_machine()
    machine["accountability"]["claims_addressee"] = None      # the 1.0.0 encoding, replanted
    assert _bare_nulls(machine) == ["/accountability/claims_addressee"]


def test_a_whitelist_entry_must_state_a_meaning():
    """An empty entry would be a silence dressed as a decision."""
    for path, meaning in WHITELIST.items():
        assert path.startswith("/") and len(meaning) > 40, path
