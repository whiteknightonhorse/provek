"""LAW #ONE-PLACE for ISO-8601 timestamp parsing (ABI-13-6, ABI-16-11, ABI-33-4).

`datetime.fromisoformat` REJECTS a trailing `Z` on Python 3.10 - the interpreter `pyproject.toml`
pins and CI installs - even though `Z` is the commonest ISO spelling of UTC there is. This
repository's own writers never emit it (`datetime.isoformat()` on an aware value always yields
`+00:00`), but readers do not control what wrote the string they are handed: a shallow git clone's
own `%cI` commit-date format, or any timestamp originating outside this codebase, is free to use
it. Reading such a string as unusable would report this interpreter's own limit as a fact about the
artefact - the same "instrument failure reported as evidence" defect `src/abs_profile/measured.py`
exists to forbid, applied here to one specific counter (timestamp parsing) instead of a gate.

`parse_iso_ts` is the one place this workaround lives. `src/collector/repo.py` (AUD-002, 2026-09-03)
called `datetime.fromisoformat` directly and crashed the whole evidence read the first time a `Z`
reached it - a second, independent implementation of a rule `src/liveness/commitments.py` had
already gotten right once. Every caller in this repository that parses a timestamp of unknown
origin goes through this module rather than calling `datetime.fromisoformat` itself.
"""
from __future__ import annotations

from datetime import datetime, timezone


def parse_iso_ts(raw: object) -> datetime | None:
    """An ISO-8601 timestamp, or `None` if `raw` is not a string or does not parse as one.

    Tolerates a trailing `Z` (rewritten to `+00:00` before parsing). A naive result is stamped UTC
    rather than left ambiguous, since every timestamp this repository writes or reads is UTC.
    """
    if not isinstance(raw, str):
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        ts = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
