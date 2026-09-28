"""T-GL-04 - one digest formula, two readers, proven to agree (D-63; ruling-2 SS2 "Golden-vector").

`integrations/genlayer-witness/tests/fixtures/digest_golden.json` holds `(url, result, checked_at)
-> digest` triples for the ONE formula that is byte-identical between this repository's own
`src.witness.witness._digest("url_reachable", url, result, checked_at)` (this Python 3.10) and the
GenLayer contract's `_url_reachable_digest` (a separate Python 3.12 reader, checked against the
same file by T-GL-03's own direct tests under `~/orchestra/glenv`). This side proves the OTHER
half: that this repository's formula still produces exactly those digests. Two readers of one file
converging is the actual claim T-GL-03's contract docstring makes ("byte-for-byte
`src.witness.witness._digest`") - unverified here, it would just be an assertion in a comment.

Only the `url_reachable` formula is pinned this way (see the fixture file's own directory README):
`artifact_hash`'s "unreachable" branch deliberately diverges (a fixed token stands in for `str(e)`,
which does not survive the nondet boundary - named in both READMEs, not a shared invariant).
"""
from __future__ import annotations

import json
import pathlib

from src.witness.witness import _digest

GOLDEN = (pathlib.Path(__file__).resolve().parents[1] / "integrations" / "genlayer-witness" /
          "tests" / "fixtures" / "digest_golden.json")


def _vectors() -> list[dict]:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_golden_vector_file_is_not_empty():
    """Instrument control: a fixture that lost its rows would make every check below vacuously
    pass (invariant 1 - zero comparisons and zero mismatches read the same as a clean sweep)."""
    assert len(_vectors()) > 0


def test_digest_matches_the_golden_vector_produced_by_the_contract_side():
    for vector in _vectors():
        computed = _digest("url_reachable", vector["url"], vector["result"], vector["checked_at"])
        assert computed == vector["digest"], vector


def test_the_convergence_check_is_ABLE_to_fail():
    """Instrument control: a formula that dropped a field would not reproduce the fixture (see
    evidence/RED-056-*, which plants exactly that and shows this test go red)."""
    vector = _vectors()[0]
    wrong = _digest("url_reachable", vector["url"], "WRONG-RESULT", vector["checked_at"])
    assert wrong != vector["digest"]
