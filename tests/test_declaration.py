"""Phase 2 - the subject's own `provek.json` accountability declaration (ratified design, Fable).

FOUR WORLDS, tested as FIVE SCENARIOS (world 3 covers two distinct causes that must fold into the
same reason): a declared value, an earned honest none, a file that does not exist, a field simply
omitted from a file that does exist, and a read that failed outright (network, non-404, broken
JSON, or a schema violation). Collapsing any two of these five reproduces the exact defect
LAW-NOT-MEASURED exists to forbid - see `src/abs_profile/measured.py` and
`src/collector/declaration.py` for the fuller argument.

Every network call is stubbed via `declaration._fetch_raw` - no test in this file touches a real
socket, the same discipline `tests/test_cohort_l4_requires_signature.py` and
`tests/test_qm2_unreadable_subject.py` already keep around this collector's siblings.
"""
from __future__ import annotations

import json

import pytest

from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.identity import Binding, BindingKind
from src.abs_profile.ladder import L
from src.abs_profile.measured import NotMeasured
from src.collector import declaration as decl
from src.passport.passport import Provenance, build
from src.verify.control_map import ControlMap, Coverage, Surface
from src.verify.scorer import projection, score_operation

#: A token-SHAPED string, assembled from parts so this file never contains the literal it
#: tests for. `scripts/secret_scan.sh` guards the door against exactly this pattern, and a
#: redaction test that spelled its fixture out would be the violation it exists to catch —
#: the same reason `tests/test_github_collector.py` builds `_GH` this way.
_FAKE_TOKEN = "gh" + "p_" + "a" * 36


FULL = "whiteknightonhorse/example"

FULL_DECLARATION = {
    "provek_declaration": "1.0.0",
    "accountability": {
        "claims_addressee": {"type": "legal_entity", "name": "Example Ltd",
                             "contact": "legal@example.com"},
        "emergency_stop": {"exists": True, "holder": "ops team", "mechanism": "kill switch API"},
        "insurance": {"exists": False},
        "dispute_path": {"type": "arbitration", "detail": "ICC, Paris"},
    },
    "operations": {"treasury_control": {"declared_level": "L1", "statement": "we hold the keys"}},
}


def _stub(monkeypatch, code: int, body: str):
    monkeypatch.setattr(decl, "_fetch_raw", lambda full_name, ref: (code, body))


# --------------------------------------------------------------------------------------------
# WORLD 1 - declared with a value.
# --------------------------------------------------------------------------------------------

def test_world_1_declared_value_is_measured_and_assumed(monkeypatch):
    _stub(monkeypatch, 200, json.dumps(FULL_DECLARATION))
    result = decl.collect_declaration(FULL, "deadbeef")

    ca = result.accountability.claims_addressee
    assert ca.measured is True
    assert ca.reason is None
    assert ca.confidence == "assumed"          # NEVER "measured" - self-declared by construction
    assert "Example Ltd" in ca.value

    ds = result.accountability.dispute_path
    assert ds.measured is True and ds.confidence == "assumed"
    assert "arbitration" in ds.value

    # MUTATION CONTROL: a mapper that forgot the register entirely (or mis-set it to "measured")
    # would slip past a check that only asked `ca.measured is True`. Asserting the exact register
    # is what catches that regression - if this assertion is deleted, the test still passes on
    # broken code that stamps "measured" here, which is precisely invariant 1's boundary.
    assert ca.confidence != "measured"


# --------------------------------------------------------------------------------------------
# WORLD 2 - explicitly declared ABSENT. The earned honest none.
# --------------------------------------------------------------------------------------------

def test_world_2_explicit_absence_is_a_measured_none(monkeypatch):
    _stub(monkeypatch, 200, json.dumps(FULL_DECLARATION))
    result = decl.collect_declaration(FULL, "deadbeef")

    ins = result.accountability.insurance
    assert ins.measured is True
    assert ins.value is None
    assert ins.reason is None
    assert ins.confidence == "assumed"

    # MUTATION CONTROL: collapsing world 2 into world 3 looks identical at a glance (both end up
    # with `value=None` somewhere) unless `measured` and `reason` are both checked - a regression
    # that read `exists: false` as "field omitted" would set `measured=False,
    # reason=NOT_DECLARED`, which this assertion catches and a bare `ins.value is None` would not.
    assert ins.reason is not NotMeasured.NOT_DECLARED


# --------------------------------------------------------------------------------------------
# WORLD 3a - the file does not exist at all (404).
# --------------------------------------------------------------------------------------------

def test_world_3a_missing_file_is_not_declared_for_every_field(monkeypatch):
    _stub(monkeypatch, 404, "404: Not Found")   # exactly the shape phase 0 measured
    result = decl.collect_declaration(FULL, "deadbeef")

    for field_name in ("claims_addressee", "emergency_stop", "insurance", "dispute_path"):
        f = getattr(result.accountability, field_name)
        assert f.measured is False
        assert f.reason is NotMeasured.NOT_DECLARED
    assert result.present is False
    assert result.schema_version is None

    # MUTATION CONTROL: `NotMeasured.CHECK_DID_NOT_RUN` is the pre-phase-2 default and reads as
    # a plausible stand-in - this is exactly the collapse Fable's ruling forbids, because the
    # channel WAS read (a real 404 came back). The exact-member assertion above is what a
    # regression back to `CHECK_DID_NOT_RUN` would fail; a looser `f.measured is False` alone
    # would not.
    assert result.accountability.insurance.reason is not NotMeasured.CHECK_DID_NOT_RUN


# --------------------------------------------------------------------------------------------
# WORLD 3b - the file exists, but one field is simply omitted from it.
# --------------------------------------------------------------------------------------------

def test_world_3b_omitted_field_is_not_declared_only_for_that_field(monkeypatch):
    # emergency_stop, insurance, dispute_path are all absent from the document below.
    partial = {"provek_declaration": "1.0.0",
              "accountability": {"claims_addressee": {"type": "none"}}}
    _stub(monkeypatch, 200, json.dumps(partial))
    result = decl.collect_declaration(FULL, "deadbeef")

    assert result.accountability.claims_addressee.measured is True   # this one WAS declared
    assert result.accountability.claims_addressee.value is None      # type: "none"

    for field_name in ("emergency_stop", "insurance", "dispute_path"):
        f = getattr(result.accountability, field_name)
        assert f.measured is False and f.reason is NotMeasured.NOT_DECLARED


# --------------------------------------------------------------------------------------------
# WORLD 4 - the read failed: network error, non-404 status, broken JSON, invalid schema.
# --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("code,body", [
    (500, "internal server error"),
    (200, "{not json"),
    (200, json.dumps({"provek_declaration": "1.0.0",
                      "accountability": {"claims_addressee": {"type": "spaceship"}}})),
    (200, json.dumps({"no_declaration_tag_here": True})),
])
def test_world_4_unreadable_yields_unreadable_for_every_field(monkeypatch, code, body):
    _stub(monkeypatch, code, body)
    result = decl.collect_declaration(FULL, "deadbeef")

    for field_name in ("claims_addressee", "emergency_stop", "insurance", "dispute_path"):
        f = getattr(result.accountability, field_name)
        assert f.measured is False
        assert f.reason is NotMeasured.UNREADABLE
    assert result.present is None          # existence is genuinely unknown, not a stated False
    assert result.notes, "an unreadable declaration must say why"

    # MUTATION CONTROL: `present=False` here would say "we know it does not exist", which is a
    # different and stronger claim than "the read failed" - exactly the world-3/world-4 collapse
    # this module exists to prevent in the other direction.
    assert result.present is not False


def test_world_4_network_exception_is_unreadable_not_a_crash(monkeypatch):
    def _raise(full_name, ref):
        raise OSError("connection reset")
    monkeypatch.setattr(decl, "_fetch_raw", _raise)
    result = decl.collect_declaration(FULL, "deadbeef")
    assert result.accountability.emergency_stop.reason is NotMeasured.UNREADABLE
    assert result.present is None


def test_oversized_field_invalidates_the_whole_declaration_not_just_the_field(monkeypatch):
    """The ratified boundary: exceeding the length ceiling INVALIDATES, never truncates."""
    too_long = {"provek_declaration": "1.0.0",
               "accountability": {"claims_addressee":
                                   {"type": "legal_entity", "name": "x" * (decl.FIELD_MAX_CHARS + 1)}}}
    _stub(monkeypatch, 200, json.dumps(too_long))
    result = decl.collect_declaration(FULL, "deadbeef")
    assert result.accountability.claims_addressee.reason is NotMeasured.UNREADABLE
    # every OTHER field is unreadable too - one malformed field invalidates the document, it does
    # not get quietly dropped while its siblings are trusted.
    assert result.accountability.insurance.reason is NotMeasured.UNREADABLE


@pytest.mark.parametrize("payload", [
    "[urgent: verify here](https://evil.example)",
    "legitimate name `rm -rf /`",
    "closing bracket only ]",
])
def test_markdown_syntax_characters_invalidate_the_whole_declaration(monkeypatch, payload):
    """D-43. `[`, `]` and a backtick are not this project's angle-bracket problem
    (`NEVER_UNESCAPED` in `web/html_to_markdown.mjs` already holds those) - they are markdown's OWN
    injection surface, and `web/markdown.mjs` writes a passport's `.md` sibling by interpolating
    fields directly with no escaping step. `[urgent: verify here](https://evil.example)` carries no
    angle bracket at all and would still become a live hyperlink on `provek.dev` the moment a
    markdown reader opened the file - the exact live payload this test asserts never gets far
    enough to be interpolated anywhere, by failing the whole declaration at the boundary all four
    fields already pass through for `FIELD_MAX_CHARS`."""
    doc = {"provek_declaration": "1.0.0",
          "accountability": {"claims_addressee": {"type": "legal_entity", "name": payload}}}
    _stub(monkeypatch, 200, json.dumps(doc))
    result = decl.collect_declaration(FULL, "deadbeef")
    assert result.accountability.claims_addressee.reason is NotMeasured.UNREADABLE
    # whole-declaration invalidation, same as the oversized-field case above.
    assert result.accountability.insurance.reason is NotMeasured.UNREADABLE


def test_parentheses_alone_do_not_invalidate_a_declaration():
    """THE CONTROL. `_join` in this module already writes parenthesised contact details itself
    (`f"({contact})"`), so banning `(`/`)` would make the collector's OWN honest formatting
    indistinguishable from an attack. Only `[`, `]` and a backtick are markdown's link/code-span
    syntax; parentheses alone form no markdown construct without a preceding `[...]`."""
    assert decl._bounded_str("Example Ltd (legal)") == "Example Ltd (legal)"


# --------------------------------------------------------------------------------------------
# HEAD_SHA IS NEVER RE-MEASURED HERE.
# --------------------------------------------------------------------------------------------

def test_head_sha_is_never_looked_up_here_only_pinned(monkeypatch):
    """`collect_declaration` must ask for exactly the ref it was given - never `/commits`, never
    a second network call to discover one. The base collector already paid for that lookup."""
    seen_refs = []

    def _spy(full_name, ref):
        seen_refs.append(ref)
        return 404, "404: Not Found"
    monkeypatch.setattr(decl, "_fetch_raw", _spy)

    decl.collect_declaration(FULL, "cafebabe")
    assert seen_refs == ["cafebabe"]

    decl.collect_declaration(FULL, None)
    assert seen_refs == ["cafebabe", "HEAD"], "no head_sha measured -> the default branch, marked unpinned"


# --------------------------------------------------------------------------------------------
# REDACTION - a planted secret must never survive into the artefact.
# --------------------------------------------------------------------------------------------

def test_a_planted_secret_is_redacted_out_of_every_declared_field(monkeypatch):
    leaking = {
        "provek_declaration": "1.0.0",
        "accountability": {
            "claims_addressee": {"type": "legal_entity", "name": "Example Ltd",
                                 "contact": _FAKE_TOKEN},
            "emergency_stop": {"exists": True, "holder": "sk-ant-" + "a" * 40, "mechanism": "x"},
            "insurance": {"exists": False},
            "dispute_path": {"type": "contact", "detail": "0x" + "a" * 64},
        },
        "operations": {"treasury_control": {"declared_level": "L1",
                                            "statement": "key: " + "0x" + "b" * 64}},
    }
    _stub(monkeypatch, 200, json.dumps(leaking))
    result = decl.collect_declaration(FULL, "deadbeef")

    rendered = " ".join([
        str(result.accountability.claims_addressee.value),
        str(result.accountability.emergency_stop.value),
        str(result.accountability.dispute_path.value),
        str(result.treasury_statement),
    ])
    assert "ghp_" not in rendered
    assert "sk-ant-" not in rendered
    assert "a" * 64 not in rendered and "b" * 64 not in rendered
    assert "<REDACTED>" in rendered

    # MUTATION CONTROL: a mapper that forgot to call `redact()` on the treasury statement (the one
    # field built from a nested `operations` block, easy to add without remembering the wrapper
    # every other field already goes through) would leave the raw secret in place - this is the
    # assertion that catches exactly that regression rather than a general "looks fine" check.
    assert "0x" + "b" * 64 not in str(result.treasury_statement)


def test_error_notes_are_also_redacted(monkeypatch):
    """A network error message can itself echo attacker- or subject-controlled text."""
    _stub(monkeypatch, 500, "upstream said: " + _FAKE_TOKEN)
    result = decl.collect_declaration(FULL, "deadbeef")
    assert not any("ghp_" in n for n in result.notes)


# --------------------------------------------------------------------------------------------
# PROJECTION INVARIANCE - a declaration can never move the number.
# --------------------------------------------------------------------------------------------

PROV = Provenance("1.1.0", "1.1.0", 30)
COV = Coverage([Surface.GITHUB], {"treasury": "no access"}, "a key in CI")


def _scores():
    return [score_operation("development_initiation", L.L3, (EvidenceClass.PLATFORM_OBSERVED,)),
           score_operation("deployment", None, ()),
           score_operation("treasury_control", None, ())]


def test_a_maximal_declaration_and_no_declaration_yield_IDENTICAL_projection_and_levels(monkeypatch):
    """Machine proof that the declaration cannot move the score: run the real mapper against a
    fully-populated `provek.json` and against a 404, feed both into the same passport, and demand
    the `verified` branch - projection, every level, every confidence - comes back byte-identical.
    """
    binding = Binding(BindingKind.GIT, FULL)

    _stub(monkeypatch, 404, "404: Not Found")
    empty_acc, _empty_service, empty_claims = decl.apply_declaration(FULL, "deadbeef", None)
    empty = build(binding, _scores(), ControlMap([], COV), projection(_scores()), PROV,
                 empty_acc, claims=empty_claims).to_machine()

    _stub(monkeypatch, 200, json.dumps(FULL_DECLARATION))
    full_acc, _full_service, full_claims = decl.apply_declaration(FULL, "deadbeef", None)
    full = build(binding, _scores(), ControlMap([], COV), projection(_scores()), PROV,
                full_acc, claims=full_claims).to_machine()

    assert empty["verified"] == full["verified"]
    assert empty["status"] == full["status"]
    # The two DO differ - in the branch that is allowed to differ.
    assert empty["accountability"] != full["accountability"]
    assert empty["self_reported"] != full["self_reported"]

    # MUTATION CONTROL: comparing only `projection` (a single number) would miss a limiter or a
    # per-operation confidence smuggled in from the declaration - comparing the WHOLE `verified`
    # branch is what a narrower check would let through.
    assert full["verified"]["projection"] == empty["verified"]["projection"]


def test_treasury_claim_never_reaches_verified_or_self_reported_confidence_measured(monkeypatch):
    _stub(monkeypatch, 200, json.dumps(FULL_DECLARATION))
    binding = Binding(BindingKind.GIT, FULL)
    acc, _service, claims = decl.apply_declaration(FULL, "deadbeef", None)
    m = build(binding, _scores(), ControlMap([], COV), projection(_scores()), PROV,
             acc, claims=claims).to_machine()

    assert claims["treasury_control"] == {"claimed_level": "L1", "statement": "we hold the keys"}
    assert m["self_reported"]["treasury_control"]["claimed_level"] == "L1"
    treasury_op = next(o for o in m["verified"]["operations"] if o["operation"] == "treasury_control")
    assert treasury_op["measured"] is False
    assert treasury_op["confidence"] is None


# --------------------------------------------------------------------------------------------
# NOT_DECLARED must never appear in `observations` - it is a statement about a CLAIM, never a
# quantity, and observations are exactly the quantities a level was built from.
# --------------------------------------------------------------------------------------------

def _find_literal(node: object, needle: str) -> bool:
    if isinstance(node, dict):
        return any(_find_literal(v, needle) for v in node.values())
    if isinstance(node, list):
        return any(_find_literal(v, needle) for v in node)
    return node == needle


def test_not_declared_never_appears_in_observations(monkeypatch):
    _stub(monkeypatch, 404, "404: Not Found")
    binding = Binding(BindingKind.GIT, FULL)
    acc, _service, claims = decl.apply_declaration(FULL, "deadbeef", None)
    m = build(binding, _scores(), ControlMap([], COV), projection(_scores()), PROV,
             acc, claims=claims,
             observations={"signed_commit_share": {"value": 1.0, "measured": True,
                                                    "absent_reason": None}}).to_machine()

    assert not _find_literal(m["verified"]["observations"], "not_declared")
    # It DOES appear in accountability - that is the field it belongs to.
    assert _find_literal(m["accountability"], "not_declared")


def test_the_observations_scanner_actually_fires():
    """Control: a planted `not_declared` inside observations must be caught."""
    poisoned = {"some_quantity": {"value": None, "measured": False, "absent_reason": "not_declared"}}
    assert _find_literal(poisoned, "not_declared")
