"""T-01-ci-red-isoformat-z, second consumer. `scripts/cohort.py`'s `previous_rows()` reads
`valid_until` off the registry this project itself last published - the writer
(`src/registry/public_registry.py`) never emits a trailing `Z`, so this call site was not the one
that broke CI, but it was a second, independent `datetime.fromisoformat(...)` call on a timestamp of
external origin (the file on disk, not a value still in memory) - exactly the shape that let AUD-002
regrow the same defect a first fix (`src/liveness/commitments.py`) had already closed. Routed
through the shared `parse_iso_ts` (LAW #ONE-PLACE) so a third copy cannot drift the same way.

`scripts/cohort.py` runs a live measurement loop at module scope - it is a script meant to be run,
not imported - so the function under test is lifted out of its source with `ast`, the same technique
`tests/test_cohort_l4_requires_signature.py` already uses for the same reason.
"""
import ast
import json
from datetime import datetime
from pathlib import Path

from src.abs_profile.isotime import parse_iso_ts
from src.registry.public_registry import Row

_FN_NAME = "previous_rows"


def _load_previous_rows():
    src = Path(__file__).resolve().parents[1] / "scripts" / "cohort.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == _FN_NAME), None)
    assert fn is not None, f"scripts/cohort.py no longer defines {_FN_NAME} - this test targets nothing"
    # `datetime` is injected so that reverting the fix under test (back to a bare
    # `datetime.fromisoformat` call) reproduces the REAL mutation - a ValueError on a trailing `Z` -
    # instead of a NameError artefact of this harness lifting the function without its module scope.
    ns = {"json": json, "Row": Row, "parse_iso_ts": parse_iso_ts, "datetime": datetime}
    module = ast.Module(body=[fn], type_ignores=[])
    exec(compile(module, str(src), "exec"), ns)
    return ns


def _registry_dir(tmp_path: Path, valid_until: str) -> Path:
    public = tmp_path / "public"
    (public / "registry").mkdir(parents=True)
    doc = {"generated_at": "2026-09-03T00:00:00+00:00", "subjects": [{
        "subject_id": "example/repo", "status": "verified", "projection": 40,
        "projection_absent_reason": None, "protocol_version": "1.0.0",
        "valid_until": valid_until, "passport_ref": "passports/example-repo.json",
        "verifier_affiliation": "independent"}]}
    (public / "registry" / "registry.json").write_text(json.dumps(doc), encoding="utf-8")
    return public


def test_a_published_valid_until_spelled_with_a_trailing_Z_is_read_not_crashed(tmp_path):
    """RED with `datetime.fromisoformat(_r["valid_until"])` restored in place of
    `parse_iso_ts(_r["valid_until"])` at scripts/cohort.py: this raises ValueError. GREEN with the
    fix: the row is read and carries the right instant."""
    from datetime import datetime, timezone
    ns = _load_previous_rows()
    ns["out"] = _registry_dir(tmp_path, "2026-09-19T00:00:00Z")
    rows = ns[_FN_NAME]()
    assert rows["example/repo"].valid_until == datetime(2026, 9, 19, tzinfo=timezone.utc)


def test_a_genuinely_unreadable_valid_until_still_fails_loudly(tmp_path):
    """`valid_until` is load-bearing (it decides VERIFIED vs STALE on every future run): swapping
    to a `None`-returning parser must not let corruption pass through as a missing field would."""
    import pytest
    ns = _load_previous_rows()
    ns["out"] = _registry_dir(tmp_path, "not a timestamp")
    with pytest.raises(ValueError):
        ns[_FN_NAME]()
