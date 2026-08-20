"""Ratified thresholds and the deterministic verdict (Q-D1 closed 2026-08-19)."""
from src.abs_profile.measured import Measurement, NotMeasured
from src.governance.thresholds import (
    CANDIDATES_GO,
    CANDIDATES_REVISIT,
    CLOCK_DAYS,
    MANDATES_GO,
    OFFERS_BEFORE_CLOCK,
    Inputs,
    Verdict,
    evaluate,
)


def M(v):
    return Measurement(value=v)


ABSENT = Measurement(absent=NotMeasured.CHECK_DID_NOT_RUN)


def test_ratified_values_are_exactly_what_the_operator_ratified():
    assert (CANDIDATES_GO, MANDATES_GO, CLOCK_DAYS) == (30, 5, 90)
    assert CANDIDATES_REVISIT == 10
    assert OFFERS_BEFORE_CLOCK == 10


def test_an_unmeasured_input_NEVER_decides():
    """A verifier that decides on data it does not have is the defect this product exposes."""
    v, why = evaluate(Inputs(ABSENT, M(9), M(10)))
    assert v is Verdict.NOT_MEASURED and "not measured" in why


def test_missing_mandate_count_does_not_become_a_stop():
    v, _ = evaluate(Inputs(M(50), ABSENT, M(100)))
    assert v is Verdict.NOT_MEASURED


def test_a_thin_market_is_REVISIT_not_STOP_until_growth_is_measured():
    """Revision 1.1: a terminal stop here would kill the project for being early."""
    v, why = evaluate(Inputs(M(4), M(0), M(0)))
    assert v is Verdict.REVISIT and "not a stop" in why


def test_no_growth_across_the_second_window_IS_a_stop():
    v, why = evaluate(Inputs(M(4), M(0), M(0), growth_observed=False))
    assert v is Verdict.STOP and "not merely early" in why


def test_growth_present_keeps_it_at_revisit():
    v, _ = evaluate(Inputs(M(4), M(0), M(0), growth_observed=True))
    assert v is Verdict.REVISIT


def test_both_thresholds_met_is_GO():
    v, why = evaluate(Inputs(M(30), M(5), M(10)))
    assert v is Verdict.GO and "both thresholds met" in why


def test_window_elapsed_without_mandates_refutes_voluntariness():
    v, why = evaluate(Inputs(M(100), M(1), M(90)))
    assert v is Verdict.STOP and "voluntariness hypothesis is refuted" in why


def test_inside_the_window_is_revisit_not_a_verdict():
    v, why = evaluate(Inputs(M(100), M(2), M(30)))
    assert v is Verdict.REVISIT and "still inside the window" in why


def test_current_real_state_is_NOT_MEASURED():
    """Today: the 2.7 filter has not been run, so no verdict may be claimed either way."""
    v, _ = evaluate(Inputs(ABSENT, ABSENT, ABSENT))
    assert v is Verdict.NOT_MEASURED
