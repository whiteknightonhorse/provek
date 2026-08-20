"""T-2.5 - a map without coverage is invalid; a limiting path sets the ceiling."""
from src.verify.control_map import Capability, ControlMap, ControlPath, Coverage, Surface


def _cov(): return Coverage([Surface.GITHUB], {"treasury": "no access"}, "an undiscovered key in CI")


def test_map_without_coverage_is_INVALID():
    """ABI-7-5: a map that publishes no coverage claims more than it knows."""
    assert ControlMap(paths=[], coverage=None).is_valid() is False
    assert ControlMap(paths=[], coverage=_cov()).is_valid() is True


def test_coverage_must_name_what_an_undiscovered_path_would_look_like():
    assert Coverage([Surface.GITHUB], {}, "").is_valid() is False


def test_ability_to_FIX_does_not_limit_autonomy():
    """ABI-7-4. Otherwise every maintained project would count as non-autonomous."""
    m = ControlMap([ControlPath(Surface.GITHUB, Capability.IMPROVE_OR_FIX, True)], _cov())
    assert m.limits_autonomy() == []
    assert m.implied_level_cap() == 5


def test_recorded_privileged_path_caps_at_L4_unrecorded_at_L3():
    """This is exactly what separates L4 from L3 in the brief's ladder."""
    rec = ControlMap([ControlPath(Surface.TREASURY, Capability.OPERATE_REDIRECT_EXTRACT, True)], _cov())
    unrec = ControlMap([ControlPath(Surface.TREASURY, Capability.OPERATE_REDIRECT_EXTRACT, False)], _cov())
    assert rec.implied_level_cap() == 4
    assert unrec.implied_level_cap() == 3
