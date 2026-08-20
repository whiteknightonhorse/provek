"""A2 — a verdict lapses by time, and the surface has to say so.

`Passport.effective_status` implements ABI-15-5: a verified record becomes `stale` on its own, with
no event. The web never computed it, so a registry generated today would have gone on printing
`verified` for ever. On 2026-09-19 every currently published row lapses in the machine sense — "no
news" and "expired" rendered identically, which is the founding defect in its temporal form.

Checked here at the Python level, where the rule is defined, plus a check that the surface carries
the computation at all rather than inheriting a frozen word.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.registry.lifecycle import Status

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "public" / "registry" / "registry.json"
WEB = ROOT / "web" / "src"


def test_the_python_rule_lapses_without_an_event():
    from src.abs_profile.evidence import EvidenceClass
    from src.abs_profile.identity import Binding, BindingKind
    from src.abs_profile.ladder import L
    from src.abs_profile.measured import Measurement
    from src.passport.passport import Accountability, Provenance, build
    from src.verify.control_map import ControlMap, Coverage, Surface
    from src.verify.scorer import score_operation

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    p = build(Binding(BindingKind.GIT, "a/b"),
              [score_operation("deploy", L.L4, (EvidenceClass.PLATFORM_OBSERVED,))],
              ControlMap([], Coverage([Surface.GITHUB], {"t": "no access"}, "a key")),
              Measurement(value=80), Provenance("1.0.0", "1.0.0", 30), Accountability(), now=now)
    assert p.effective_status(now) is Status.VERIFIED
    assert p.effective_status(p.valid_until + timedelta(seconds=1)) is Status.STALE


def test_the_surface_computes_staleness_rather_than_printing_the_stored_word():
    """The carve-out to DESIGN rule 3 - nothing computed for display - is recorded and used."""
    types = (WEB / "types.ts").read_text(encoding="utf-8")
    assert "export function effectiveStatus" in types
    assert "read time" in types, "the carve-out must be explained where it is taken"

    registry = (WEB / "pages" / "Registry.tsx").read_text(encoding="utf-8")
    passport = (WEB / "pages" / "Passport.tsx").read_text(encoding="utf-8")
    assert "effectiveStatus(" in registry, "the registry table prints the stored status"
    assert "effectiveStatus(" in passport, "the passport prints the stored status"
    # And the raw field must not be rendered beside the computed one, or a reader sees both.
    assert not re.search(r"\{s\.status\}", registry), "raw status still rendered in the table"


@pytest.mark.skipif(not REGISTRY.exists(), reason="no registry emitted")
def test_every_current_row_will_lapse_and_the_date_is_known():
    """Not a defect - a fact that has to remain visible. If this date passes with nothing renewed,
    every row on the public registry reads `stale`, which is correct and should surprise nobody."""
    reg = json.loads(REGISTRY.read_text())
    dates = {row["valid_until"][:10] for row in reg["subjects"]}
    assert dates, "the registry is empty"
    assert all(d >= "2026-09-01" for d in dates), dates
