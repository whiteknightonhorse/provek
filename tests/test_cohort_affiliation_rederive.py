"""AUD-013 (Fable, sweep of 2026-09-03) - the MECHANISM that produced AUD-001, not just its one
live instance. `verifier_affiliation` was a fact `~/orchestra/intake_cron.py` derived once at
admission and every re-measure since simply carried forward from `data/subjects.json` - a
repository TRANSFER (owner change after admission, in either direction) would go unnoticed
silently and forever, because nothing here ever looked at the owner again.

`scripts/cohort.py`'s point fix for AUD-001 (`affiliation_violations`, a SystemExit gate at import
time) catches a BAD VALUE sitting in the file before a run starts - it does not re-derive the fact
from a live read. `derive_affiliation` does that: it is called on every subject, every pass, using
`GitHubEvidence.owner` - the login the SAME `/repos/{full}` call already reads (no second request,
see `src/collector/github.py`) - so the stored file only ever supplies a FALLBACK for a pass that
could not read an owner at all, never the live answer.

`scripts/cohort.py` runs a live measurement loop at module scope - it is a script meant to be run,
not imported - so `derive_affiliation` is lifted out with `ast`, the same technique
`tests/test_subjects_affiliation_matches_owner.py` already uses for the same reason.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SRC = ROOT / "scripts" / "cohort.py"


def _load():
    tree = ast.parse(_SRC.read_text(encoding="utf-8"))
    fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef)
               and n.name == "derive_affiliation"), None)
    assert fn is not None, (
        "scripts/cohort.py no longer defines derive_affiliation - AUD-013's fix was removed or "
        "renamed, and this test targets nothing")
    ns: dict = {"OPERATOR": OPERATOR}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(_SRC), "exec"), ns)
    return ns["derive_affiliation"]


OPERATOR = "whiteknightonhorse"
DERIVE = _load()


def test_MUTATION_a_transfer_away_from_the_operator_is_caught_this_pass():
    """RED under the old mechanism (trust `data/subjects.json` forever, as AUD-013 found it): a
    repository that was `same_owner` at intake and has since been transferred AWAY from the
    operator would keep publishing `same_owner` indefinitely - exactly the "stored once, never
    re-checked" shape that produced AUD-001. GREEN: the owner read on THIS pass overrides the
    stale stored value the moment it disagrees."""
    assert DERIVE("someone-else", "same_owner", operator=OPERATOR) == "independent"


def test_MUTATION_a_transfer_to_the_operator_is_caught_this_pass():
    """The other direction: a subject transferred TO the operator must stop reading as
    independent the moment the new owner is visible, not one intake cycle later - this is AUD-001's
    exact shape, reproduced as a live transfer instead of a one-time intake mistake."""
    assert DERIVE("whiteknightonhorse", "independent", operator=OPERATOR) == "same_owner"


def test_owner_match_is_case_insensitive():
    """`~/orchestra/intake_cron.py`'s own comparison is `.lower()`'d; this has to agree with it or
    a differently-cased owner would derive one answer here and another at intake."""
    assert DERIVE("WhiteKnightOnHorse", "independent", operator=OPERATOR) == "same_owner"
    assert DERIVE("whiteknightonhorse", "independent", operator="WhiteKnightOnHorse") == "same_owner"


def test_unread_owner_falls_back_to_the_stored_value_not_a_guess():
    """A private or unreadable repository (`GitHubEvidence.owner is None`, the source did not
    answer THIS pass) must not be reported as independent or same_owner on a guess - the last
    known value stands until a real read can update it, the same discipline `skip_rate_limited`
    already applies to a whole carried-forward row."""
    assert DERIVE(None, "same_owner", operator=OPERATOR) == "same_owner"
    assert DERIVE(None, "independent", operator=OPERATOR) == "independent"
