"""LAW-ONE-PROCEDURE-ONE-THRESHOLD - development initiation is computed by one function (D-74).

The cohort and the pipeline once held two bands (3 and 2) on the stated ground that one of them
weighs signatures at L3. Neither did. This grid is asserted through BOTH call sites, so a constant
or a branch changed in one place turns it red.
"""
import ast
from pathlib import Path

import pytest

import src.abs_profile.ladder as ladder
from src.abs_profile.ladder import FEW_AUTHORS_FOR_L3, SIGNED_SHARE_FOR_L4, L, development_initiation_level
from src.abs_profile.measured import Measurement, NotMeasured
from src.pipeline import _observed_level

ROOT = Path(__file__).resolve().parents[1]
M = Measurement
GONE = M(absent=NotMeasured.CHECK_DID_NOT_RUN)


def _cohort_fn():
    src = ROOT / "scripts" / "cohort.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
              and n.name == "cohort_development_initiation_level")
    ns = {"L": L, "development_initiation_level": development_initiation_level}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(src), "exec"), ns)
    return ns["cohort_development_initiation_level"]


COHORT = _cohort_fn()
PIPELINE = lambda a, s, c: _observed_level(s, a, c)  # noqa: E731 - argument order differs by design
DIRECT = development_initiation_level

# (authors, signed share, window closed) -> level
GRID = [
    (M(value=1), M(value=0.95), M(value=True), L.L4),
    (M(value=1), M(value=0.0), M(value=True), L.L3),
    (M(value=1), GONE, M(value=True), L.L3),
    (M(value=1), M(value=1.0), M(value=False), L.L2),
    (M(value=1), M(value=1.0), GONE, L.L2),
    (M(value=2), M(value=0.0), M(value=True), L.L3),
    (M(value=2), M(value=1.0), M(value=True), L.L3),
    (M(value=3), M(value=0.0), M(value=True), L.L2),
    (M(value=3), M(value=1.0), M(value=True), L.L2),
    (M(value=9), M(value=1.0), M(value=True), L.L2),
    (GONE, M(value=1.0), M(value=True), None),
]


@pytest.mark.parametrize("door", [COHORT, PIPELINE, DIRECT], ids=["cohort", "pipeline", "direct"])
@pytest.mark.parametrize("authors,share,closed,want", GRID)
def test_the_grid_through_every_door(door, authors, share, closed, want):
    assert door(authors, share, closed) == want


def test_a_plain_clone_makes_no_closure_claim():
    assert _observed_level(M(value=1.0), M(value=1)) == L.L4
    assert _observed_level(M(value=0.0), M(value=2)) == L.L3
    assert _observed_level(M(value=0.0), M(value=3)) == L.L2


def test_there_is_one_threshold_and_it_is_two():
    assert FEW_AUTHORS_FOR_L3 == 2
    assert not hasattr(ladder, "SMALL_TEAM_FOR_L3")
    for rel in ("scripts/cohort.py", "src/pipeline.py"):
        assert "SMALL_TEAM_FOR_L3" not in (ROOT / rel).read_text(encoding="utf-8"), rel


def test_the_grid_can_fail_when_the_constant_moves(monkeypatch):
    """MUTATION: widening the band in the one place turns the three-author row red through both
    doors at once."""
    monkeypatch.setattr(ladder, "FEW_AUTHORS_FOR_L3", 3)
    assert DIRECT(M(value=3), M(value=0.0), M(value=True)) == L.L3
    assert COHORT(M(value=3), M(value=0.0), M(value=True)) == L.L3
    assert PIPELINE(M(value=3), M(value=0.0), M(value=True)) == L.L3
    assert SIGNED_SHARE_FOR_L4 == 0.9
