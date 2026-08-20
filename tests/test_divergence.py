"""T-2.4 - three outcomes, and "could not measure" is NOT a violation."""
from src.collector.divergence import Divergence, compare


def test_match_and_divergence_are_detected():
    assert compare("aaa", "aaa") is Divergence.MATCH
    assert compare("aaa", "bbb") is Divergence.DIVERGED


def test_missing_side_is_NOT_MEASURED_not_DIVERGED():
    """Otherwise the verifier punishes the subject for its own blindness (ABI-33-4)."""
    assert compare(None, "bbb") is Divergence.NOT_MEASURED
    assert compare("aaa", None) is Divergence.NOT_MEASURED
    assert compare(None, None) is Divergence.NOT_MEASURED


def test_three_outcomes_are_distinct():
    assert len({d.value for d in Divergence}) == 3
