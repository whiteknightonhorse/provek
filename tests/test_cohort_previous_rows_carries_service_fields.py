"""AUD-004 (Fable, sweep of 2026-09-03) - `scripts/cohort.py`'s `previous_rows()` built every
carried-forward `Row(...)` WITHOUT `service_url`/`service_reachable`, so both silently fell back to
`Row`'s own defaults (`None`) even though the published `registry.json` this function reads
already carries both fields. Latent today (no live subject has declared an `order_url`), but the
day one does, a `PROVEK_ONLY` intake run for a DIFFERENT subject would carry that subject's row
forward with its Order-channel state erased until the next full nightly pass - the button and
column going dark for up to ~24h because of someone else's application, not because the
declaration itself changed (spec 4.2-bis point 3: the button is meant to go dark by TIME, never by
a side effect of an unrelated request).

T-76 (Fable ruling, 2026-09-05) added `issued_at` to the same `Row(...)` call for the same reason:
a carried-forward row must keep the date it was ACTUALLY measured, not silently adopt the fresh
`generated_at` the rest of that night's registry gets stamped with - the tests below at the bottom
of this file pin that the field round-trips exactly like `service_url`/`service_reachable` did.

`scripts/cohort.py` runs a live measurement loop at module scope - it is a script meant to be run,
not imported - so `previous_rows` is lifted out with `ast`, the same technique
`tests/test_cohort_previous_rows_isotime.py` already uses for the same reason.
"""
import ast
import json
from pathlib import Path

from src.abs_profile.isotime import parse_iso_ts
from src.registry.public_registry import Row

_FN_NAME = "previous_rows"


def _load_previous_rows():
    src = Path(__file__).resolve().parents[1] / "scripts" / "cohort.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == _FN_NAME), None)
    assert fn is not None, f"scripts/cohort.py no longer defines {_FN_NAME} - this test targets nothing"
    from datetime import datetime
    ns = {"json": json, "Row": Row, "parse_iso_ts": parse_iso_ts, "datetime": datetime}
    module = ast.Module(body=[fn], type_ignores=[])
    exec(compile(module, str(src), "exec"), ns)
    return ns


def _registry_dir(tmp_path: Path, row: dict) -> Path:
    public = tmp_path / "public"
    (public / "registry").mkdir(parents=True)
    doc = {"generated_at": "2026-09-03T00:00:00+00:00", "subjects": [row]}
    (public / "registry" / "registry.json").write_text(json.dumps(doc), encoding="utf-8")
    return public


_BASE_ROW = {
    "subject_id": "example/repo", "status": "verified", "projection": 40,
    "projection_absent_reason": None, "protocol_version": "1.0.0",
    "valid_until": "2026-10-01T00:00:00+00:00", "passport_ref": "passports/example-repo.json",
    "verifier_affiliation": "independent",
}


def test_MUTATION_a_declared_reachable_order_channel_survives_carry_forward(tmp_path):
    """RED with the pre-fix `Row(...)` (no `service_url`/`service_reachable` kwargs): both come
    back `None` and the Order button predicate this row feeds would go dark. GREEN with the fix:
    both fields round-trip byte-for-byte."""
    row = dict(_BASE_ROW, service_url="https://example.com/order", service_reachable=True)
    ns = _load_previous_rows()
    ns["out"] = _registry_dir(tmp_path, row)
    rows = ns[_FN_NAME]()
    carried = rows["example/repo"]
    assert carried.service_url == "https://example.com/order"
    assert carried.service_reachable is True


def test_MUTATION_a_declared_but_unreachable_order_channel_survives_carry_forward(tmp_path):
    """`service_reachable=False` is a real, meaningful value (distinct from `None` = never
    checked) - it must not be coerced to `None` or to a falsy default by the carry-forward path."""
    row = dict(_BASE_ROW, service_url="https://example.com/order", service_reachable=False)
    ns = _load_previous_rows()
    ns["out"] = _registry_dir(tmp_path, row)
    rows = ns[_FN_NAME]()
    carried = rows["example/repo"]
    assert carried.service_url == "https://example.com/order"
    assert carried.service_reachable is False


def test_no_order_channel_declared_carries_forward_as_none_not_absent_key_crash(tmp_path):
    """A registry.json written before phase 2 (or a row for a subject with no declaration) lacks
    the two keys outright - `.get()`, not `[]`, so an absent field reads as `None` rather than
    raising `KeyError`."""
    row = {k: v for k, v in _BASE_ROW.items()}
    ns = _load_previous_rows()
    ns["out"] = _registry_dir(tmp_path, row)
    rows = ns[_FN_NAME]()
    carried = rows["example/repo"]
    assert carried.service_url is None
    assert carried.service_reachable is None


def test_MUTATION_a_carried_row_keeps_its_own_older_issued_at(tmp_path):
    """T-76 ruling. RED with the pre-fix `Row(...)` (no `issued_at` kwarg): the field silently
    falls back to `Row`'s default of `None`, so a carried-forward row loses the one thing that
    would let a reader tell it apart from a row measured tonight. GREEN: the value this subject was
    ACTUALLY measured at round-trips, unrelated to whatever `generated_at` the containing document
    carries - proven here by using a document-level `generated_at` that differs from the row's own
    `issued_at`, exactly the shape a carried-forward row has in production."""
    row = dict(_BASE_ROW, issued_at="2026-08-20T00:00:00+00:00")
    ns = _load_previous_rows()
    ns["out"] = _registry_dir(tmp_path, row)   # doc generated_at is 2026-09-03, above
    rows = ns[_FN_NAME]()
    carried = rows["example/repo"]
    assert carried.issued_at is not None
    assert carried.issued_at.isoformat() == "2026-08-20T00:00:00+00:00"
    assert carried.issued_at.isoformat()[:10] != "2026-09-03", (
        "the row's own issued_at must not read as the document's generated_at")


def test_a_registry_written_before_this_field_existed_carries_forward_as_none(tmp_path):
    """`.get()`, not `[]`: a registry.json from before T-76 lacks the key outright, and an absent
    field must still read as `None` rather than raising `KeyError` - same discipline as
    `service_url`/`service_reachable` above."""
    row = {k: v for k, v in _BASE_ROW.items()}
    ns = _load_previous_rows()
    ns["out"] = _registry_dir(tmp_path, row)
    rows = ns[_FN_NAME]()
    assert rows["example/repo"].issued_at is None
