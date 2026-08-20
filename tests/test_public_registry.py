"""T-2.9b - status registry: absent projection and expiry by time."""
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.registry.lifecycle import Status
from src.registry.public_registry import PublicRegistry, Row

NOW = datetime(2026, 8, 19, tzinfo=timezone.utc)


def _row(**kw):
    base = dict(subject_id="git:a/b", status=Status.VERIFIED, projection=80,
                absent_reason=None, protocol_version="1.0.0",
                valid_until=NOW + timedelta(days=30), passport_ref="p.json")
    base.update(kw)
    return Row(**base)


def test_absent_projection_stays_None_with_its_reason():
    """A zero in the public registry would mean "measured and non-autonomous" - slander when no data exists."""
    r = PublicRegistry(Path(tempfile.mkdtemp()))
    r.upsert(_row(projection=None, absent_reason="nothing_qualified"))
    m = r.to_machine(NOW)
    assert m["subjects"][0]["projection"] is None
    assert m["subjects"][0]["projection_absent_reason"] == "nothing_qualified"


def test_expired_entry_shows_stale_not_verified():
    r = PublicRegistry(Path(tempfile.mkdtemp()))
    r.upsert(_row())
    assert r.to_machine(NOW)["subjects"][0]["status"] == "verified"
    later = NOW + timedelta(days=31)
    assert r.to_machine(later)["subjects"][0]["status"] == "stale"


def test_registry_carries_the_disclaimer_next_to_the_numbers():
    """The caveat sits next to the score, not in a footnote - otherwise the score reads as reliability."""
    r = PublicRegistry(Path(tempfile.mkdtemp()))
    m = r.to_machine(NOW)
    assert "does not measure reliability" in m["disclaimer"]


def test_registry_is_written_as_machine_readable_file():
    d = Path(tempfile.mkdtemp())
    r = PublicRegistry(d)
    r.upsert(_row())
    import json
    got = json.loads(Path(r.write(NOW)).read_text(encoding="utf-8"))
    assert got["count"] == 1 and got["subjects"][0]["subject_id"] == "git:a/b"
