"""ABI-5-4: the evidence class is the forgery cost; a self-report never enters the score."""
from src.abs_profile.evidence import FORGERY_COST, SCORABLE, EvidenceClass


def test_forgery_cost_orders_the_classes():
    assert FORGERY_COST[EvidenceClass.SELF_REPORTED] < FORGERY_COST[EvidenceClass.PLATFORM_OBSERVED]
    assert FORGERY_COST[EvidenceClass.PLATFORM_OBSERVED] < FORGERY_COST[EvidenceClass.CRYPTOGRAPHICALLY_BOUND]


def test_self_reported_is_NOT_scorable():
    """Otherwise the score says the same of a claim as it does of a signature."""
    assert EvidenceClass.SELF_REPORTED not in SCORABLE
    assert EvidenceClass.CRYPTOGRAPHICALLY_BOUND in SCORABLE
