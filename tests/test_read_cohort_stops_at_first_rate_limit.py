"""T-76 ruling (Fable, 2026-09-05), question 4 point 1, and the defect the FIRST attempt at this
task left standing: on 2026-09-05 all ten subjects each paid for a 403 plus a confirming
`/rate_limit` read against an anonymous budget the FIRST subject's 403 had already proved was at
zero (`~/orchestra/logs/cohort_refresh.log:589-598`). `scripts/budget_journal.py` (Phase 1) stops
the budget being spent BEFORE the pass starts; this file pins the other half the ruling ordered and
the prior pass at this task did not deliver - carry the remainder forward with no new reads - a
budget that goes empty MID-PASS must not cost a read for every subject still left in the cohort.

`scripts/cohort.py` runs a live measurement loop at module scope - it is a script meant to be run,
not imported - so `read_cohort` is lifted out with `ast`, the same technique
`tests/test_cohort_l4_requires_signature.py` already uses for the same reason.
"""
import ast
from pathlib import Path

from src.collector.github import RateLimited

_FN_NAME = "read_cohort"


def _load_read_cohort():
    src = Path(__file__).resolve().parents[1] / "scripts" / "cohort.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == _FN_NAME), None)
    assert fn is not None, f"scripts/cohort.py no longer defines {_FN_NAME} - this test targets nothing"
    ns = {"RateLimited": RateLimited}
    module = ast.Module(body=[fn], type_ignores=[])
    exec(compile(module, str(src), "exec"), ns)
    return ns[_FN_NAME]


READ_COHORT = _load_read_cohort()

COHORT = ["a/one", "b/two", "c/three", "d/four", "e/five"]


def test_MUTATION_a_rate_limit_on_the_second_subject_reads_none_of_the_rest():
    """RED with the pre-fix loop (a bare `for full in cohort: try: read_one(full) ...`): every
    later subject still calls `read_one` and pays for its own 403 plus confirming `/rate_limit`
    read. GREEN: `read_one` is called exactly once per subject UP TO AND INCLUDING the one that
    raises - never again after."""
    calls: list[str] = []

    def read_one(full: str) -> str:
        calls.append(full)
        if full == "b/two":
            raise RateLimited("anonymous budget of this address is spent: remaining=0")
        return f"evidence-for-{full}"

    results = READ_COHORT(COHORT, read_one)

    assert calls == ["a/one", "b/two"], (
        "the three subjects after the exhaustion were read again instead of carried forward")
    assert results["a/one"] == "evidence-for-a/one"
    assert isinstance(results["b/two"], RateLimited)
    for full in ("c/three", "d/four", "e/five"):
        assert results[full] is results["b/two"], (
            "a later subject got its own RateLimited instance instead of the SAME one carried "
            "forward - that would mean a second read happened to manufacture it")


def test_no_exhaustion_reads_every_subject_exactly_once():
    """Control: the fix must not turn into a ban on reading past the first subject."""
    calls: list[str] = []

    def read_one(full: str) -> str:
        calls.append(full)
        return f"evidence-for-{full}"

    results = READ_COHORT(COHORT, read_one)

    assert calls == COHORT
    assert all(results[full] == f"evidence-for-{full}" for full in COHORT)


def test_exhaustion_on_the_first_subject_reads_nothing_else():
    calls: list[str] = []

    def read_one(full: str) -> str:
        calls.append(full)
        raise RateLimited("anonymous budget of this address is spent: remaining=0")

    results = READ_COHORT(COHORT, read_one)

    assert calls == ["a/one"], "a budget already spent before the first read must cost only one try"
    assert all(isinstance(results[full], RateLimited) for full in COHORT)


def test_exhaustion_on_the_last_subject_reads_every_subject_once_not_twice():
    """Boundary: nothing is left over to skip, so this must behave exactly like the no-exhaustion
    case for calls, while still reporting the last subject's own RateLimited."""
    calls: list[str] = []

    def read_one(full: str) -> str:
        calls.append(full)
        if full == COHORT[-1]:
            raise RateLimited("anonymous budget of this address is spent: remaining=0")
        return f"evidence-for-{full}"

    results = READ_COHORT(COHORT, read_one)

    assert calls == COHORT
    assert isinstance(results[COHORT[-1]], RateLimited)
