"""LAW-LADDER-NAMING plus ladder properties (ABI-2-2..2-4, ruling A-5)."""
from src.abs_profile.ladder import NOT_MEASURED_BY_LADDER, L, P


def test_ladder_is_monotonic_and_L5_is_the_top():
    """Operator ruling A-5: more autonomy = higher score. L5 is the goal, not a red flag."""
    assert list(L) == sorted(L, key=int)
    assert max(L) is L.L5


def test_L_and_P_are_different_ladders():
    """The name collision from the fleet document. One name for two quantities is a defect."""
    assert L.__name__ != P.__name__
    assert L.L4.name == "L4" and P.P4.name == "P4"


def test_P_indices_match_fleet_catalogue_one_to_one():
    """The fleet's numeric configs (`autonomy_level: N`) must survive the renaming."""
    assert [int(p) for p in P] == [0, 1, 2, 3, 4, 5]


def test_ladder_declares_what_it_does_NOT_measure():
    """ABI-2-4. Silence here means selling the score as a reliability rating."""
    assert "reliability" in NOT_MEASURED_BY_LADDER
    assert "presence of an accountable party" in NOT_MEASURED_BY_LADDER
    assert "profitability" in NOT_MEASURED_BY_LADDER
