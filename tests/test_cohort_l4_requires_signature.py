"""T-L4-DEFECT (Fable, 2026-08-31) - the cohort's L4 rung must require the same signature share
that `pipeline.verify` publishes, not merely a sole author.

Until this fix `cohort_development_initiation_level` reached L4 on `distinct_authors == SOLE_AUTHOR`
alone, while the published rule (`pipeline._observed_level`) additionally requires
`signed_commit_share >= SIGNED_SHARE_FOR_L4`. A cohort computed from LESS evidence was handing out a
STRONGER verdict than the pipeline computed from MORE evidence, for the same subject (APIbase:
signed_commit_share=0.0, distinct_authors=1 -> L4 in the cohort, L3 in the pipeline). These tests
pin the fix and the one case that proves it is a fix rather than a ban on reaching L4 at all.

`scripts/cohort.py` runs a live measurement loop at module scope - it is a script meant to be run,
not imported - so the function under test is lifted out of its source with `ast` instead of via
`import scripts.cohort`, which would perform real network calls as a side effect of import.
"""
import ast
from pathlib import Path

from src.abs_profile.ladder import L, SIGNED_SHARE_FOR_L4, SMALL_TEAM_FOR_L3, SOLE_AUTHOR
from src.abs_profile.measured import Measurement, NotMeasured

_FN_NAME = "cohort_development_initiation_level"


def _load_level_fn():
    src = Path(__file__).resolve().parents[1] / "scripts" / "cohort.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == _FN_NAME), None)
    assert fn is not None, f"scripts/cohort.py no longer defines {_FN_NAME} - these tests target nothing"
    ns = {"L": L, "SOLE_AUTHOR": SOLE_AUTHOR, "SIGNED_SHARE_FOR_L4": SIGNED_SHARE_FOR_L4,
          "SMALL_TEAM_FOR_L3": SMALL_TEAM_FOR_L3}
    module = ast.Module(body=[fn], type_ignores=[])
    exec(compile(module, str(src), "exec"), ns)
    return ns[_FN_NAME]


LEVEL = _load_level_fn()
M = Measurement


def test_sole_author_unsigned_does_not_reach_l4():
    """The defect itself: APIbase's real inputs must not reach L4 in the cohort's procedure any
    more than they do in the pipeline's."""
    assert LEVEL(M(value=1), M(value=0.0), M(value=True)) == L.L3


def test_sole_author_signed_still_reaches_l4():
    """THE CONTROL. The fix must still grant L4 where the evidence actually supports it - proof
    this is a corrected threshold, not a quiet ban on the rung."""
    assert LEVEL(M(value=1), M(value=0.95), M(value=True)) == L.L4


def test_open_identity_window_floors_regardless_of_signature():
    assert LEVEL(M(value=1), M(value=1.0), M(value=False)) == L.L2


def test_unmeasured_signature_falls_to_l3_not_withheld():
    """ABI-33-4: inability to measure never yields a negative verdict. A sole author whose
    signature share is unmeasured still gets the L3 that distinct_authors alone supports -
    withholding the whole verdict over one unmeasured input would be MORE punitive than absence
    requires, since L3 needs no signature evidence at all."""
    assert LEVEL(M(value=1), M(absent=NotMeasured.CHECK_DID_NOT_RUN), M(value=True)) == L.L3


def test_distinct_authors_unmeasured_withholds_the_whole_verdict():
    assert LEVEL(M(absent=NotMeasured.CHECK_DID_NOT_RUN), M(value=0.0), M(value=True)) is None


def test_small_team_still_reaches_l3():
    assert LEVEL(M(value=SMALL_TEAM_FOR_L3), M(value=0.0), M(value=True)) == L.L3


def test_large_team_floors_at_l2():
    assert LEVEL(M(value=SMALL_TEAM_FOR_L3 + 1), M(value=1.0), M(value=True)) == L.L2
