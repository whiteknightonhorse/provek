"""T-2.9b - the PUBLIC status registry (ABI-19-2, ABI-4-6).

This component was nearly lost. The first draft of the plan had no ticket for it at all: passports
were produced and nobody published them. Found by Fable while reviewing the plan.

Why it is ours even though we deliberately do not build an identity registry: ERC-8004 supplies
IDENTITY and a distribution channel, but the registry of VERIFICATION STATUSES is the subject of
our product and a direct requirement of the brief. Conflating the two registries means either
building something redundant or losing something mandatory.

The registry answers "who can be trusted" and therefore must be machine-readable first (ABI-14-3)
and carry the same caveats as a passport: the score measures autonomy, not reliability.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.registry.lifecycle import Status

DISCLAIMER = ("The score measures AUTONOMY. It does not measure reliability, decision quality, "
              "profitability, or the presence of an accountable party. An absent projection is "
              "not a zero.")


@dataclass(frozen=True)
class Row:
    subject_id: str
    status: Status
    projection: int | None          # None = NOT MEASURED, not zero
    absent_reason: str | None
    protocol_version: str
    valid_until: datetime
    passport_ref: str
    verifier_affiliation: str = "independent"
    """CARRIED IN THE DATA, not in the interface's copy (Fable, R4).

    Until 2026-08-20 the registry page printed the literal string "affiliated" into every row and
    the landing page asserted in prose that every subject was the operator's own. True for eight
    rows; false and silent on the day a genuine independent subject lands, which would have libelled
    it as affiliated. D-12 required the disclosure to be on the face of the record - it was on the
    face of the template instead."""
    service_url: str | None = None
    """Phase 2 - the subject's self-declared `order_url` (spec 4.2-bis), or `None` if never
    declared. Carried here so the registry row - the shop window - can show it without a reader
    opening the passport first; the passport's own `service` block remains the source of truth
    and carries the full self-declared/assumed provenance this single string does not."""
    service_reachable: bool | None = None
    """The LATEST anonymous GET result against `service_url` (spec 4.2-bis point 2), or `None` when
    no URL was declared or the check has never run. Never a proxy for the score - see
    `ServiceEndpoint` in `src/passport/passport.py`."""
    issued_at: datetime | None = None
    """WHEN THIS ROW WAS ACTUALLY MEASURED - the passport's own `issued_at`, not the registry's
    `generated_at` (T-76 ruling, Fable, 2026-09-05).

    A row carried forward unread (budget exhausted, or `PROVEK_ONLY` skipping a subject not named)
    keeps its OLD `issued_at` while every other row in the same file gets a fresh one - `write()`
    stamps one `generated_at` on the whole document, and a page that prints only that date reports
    a carried-forward row as measured today. That is the exact lie ABI-5-3's anonymity boundary was
    drawn against, just moved from "who read it" to "when". `None` only for a `Row` built by code
    that predates this field (a registry.json written before this ruling) - `.get()` in
    `previous_rows()` reads that as `None` rather than raising, the same discipline `service_url`
    already has."""


class PublicRegistry:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._rows: dict[str, Row] = {}

    def upsert(self, row: Row) -> None:
        self._rows[row.subject_id] = row

    def to_machine(self, now: datetime) -> dict:
        """A snapshot. Expired entries show as stale rather than quietly staying verified."""
        out = []
        for r in self._rows.values():
            status = (Status.STALE if r.status is Status.VERIFIED and now >= r.valid_until
                      else r.status)
            out.append({
                "subject_id": r.subject_id,
                "status": status.value,
                "projection": r.projection,
                "projection_absent_reason": r.absent_reason,
                "protocol_version": r.protocol_version,
                "valid_until": r.valid_until.isoformat(),
                "passport_ref": r.passport_ref,
                "verifier_affiliation": r.verifier_affiliation,
                "service_url": r.service_url,
                "service_reachable": r.service_reachable,
                "issued_at": r.issued_at.isoformat() if r.issued_at else None,
            })
        return {"generated_at": now.isoformat(), "disclaimer": DISCLAIMER,
                "count": len(out), "subjects": sorted(out, key=lambda x: x["subject_id"])}

    def write(self, now: datetime) -> str:
        p = self.root / "registry.json"
        p.write_text(json.dumps(self.to_machine(now), ensure_ascii=False, indent=2),
                     encoding="utf-8")
        return p.as_posix()
