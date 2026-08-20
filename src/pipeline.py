"""End-to-end verification pipeline: ONE entry point (the deep-module principle).

A small interface, large logic inside. An agent - or a human - should see ONE function, not fifty:
that directly lowers both token cost and the chance of misunderstanding.

Order and boundaries come from the specification:
    collect -> score -> control map -> passport -> publish(transport) -> registry

WHAT THE PIPELINE DOES NOT DO. It does not write to the subject's systems. It does not decide for
the scorer. It does not know which transport it was given - the transport is passed in from
outside, and that is precisely why the methodology stays transport-independent (spec 4.4).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.identity import Binding
from src.abs_profile.ladder import (
    FEW_AUTHORS_FOR_L3,
    SIGNED_SHARE_FOR_L4,
    SOLE_AUTHOR,
    L,
)
from src.abs_profile.measured import Measurement
from src.collector.divergence import Divergence, compare
from src.collector.repo import collect
from src.passport.passport import Accountability, Passport, Provenance, build
from src.registry.public_registry import PublicRegistry, Row
from src.verify.control_map import ControlMap, Coverage, Surface
from src.verify.scorer import OperationScore, projection, score_operation

PROTOCOL_VERSION = "1.0.0"
PROFILE_VERSION = "1.0.0"


@dataclass(frozen=True)
class Result:
    passport: Passport
    published_ref: str
    divergence: Divergence
    findings: list[str]


def _observed_level(signed_share: Measurement, authors: Measurement) -> L | None:
    """Level for the operation "development initiation", from OBSERVABLE signals.

    HONEST BOUNDARY. This is an APPROXIMATION, not proof of autonomy: signatures and author counts
    do not say who pressed the button (attack T1, unimplementable register U-2). The result is
    recorded as platform_observed and is NEVER presented as a verdict that no human wrote the code.
    """
    if not signed_share.is_measured or not authors.is_measured:
        return None
    if authors.value == SOLE_AUTHOR and signed_share.value >= SIGNED_SHARE_FOR_L4:
        return L.L4
    if authors.value <= FEW_AUTHORS_FOR_L3:
        return L.L3
    return L.L2


def verify(remote: str, binding: Binding, transport, registry: PublicRegistry,
           *, deployed_digest: str | None = None,
           control_map: ControlMap | None = None,
           claims: dict | None = None,
           mandate_ref: str | None = None,
           verifier_affiliation: str = "independent",
           now: datetime | None = None) -> Result:
    """Verify a subject and publish its passport. The single entry point."""
    now = now or datetime.now(timezone.utc)
    findings: list[str] = []

    ev = collect(remote)
    findings.extend(ev.notes)

    div = compare(ev.tree_digest, deployed_digest)
    if div is Divergence.DIVERGED:
        findings.append("DIVERGENCE: what is deployed does not match what is committed (attack T4)")
    elif div is Divergence.NOT_MEASURED:
        findings.append("deployed artefact was not presented - the comparison WAS NOT PERFORMED, "
                        "and that is not a violation by the subject")

    cmap = control_map or ControlMap(
        paths=[],
        coverage=Coverage(inspected=[Surface.GITHUB],
                          out_of_reach={"treasury": "outside MVP scope",
                                        "server": "runtime not presented"},
                          unknown_shape="privileged access through a CI secret or account recovery"))
    cap = cmap.implied_level_cap() if cmap.is_valid() else None

    scores: list[OperationScore] = [
        score_operation("development_initiation",
                        _observed_level(ev.signed_commit_share, ev.distinct_authors),
                        (EvidenceClass.PLATFORM_OBSERVED,), cap,
                        weak_mixed_signal=True, runtime_trace=False),
        score_operation("deployment", None, ()),        # runtime not presented -> not_measured
        score_operation("treasury_control", None, ()),  # outside MVP scope -> not_measured
    ]

    p = build(binding, scores, cmap, projection(scores),
              Provenance(PROTOCOL_VERSION, PROFILE_VERSION, 30),
              # Nothing here inspects accountability, so every field states that plainly.
              # Under schema 1.0.0 this same call emitted "we checked and found none".
              Accountability(),
              now=now, claims=claims, mandate_ref=mandate_ref,
              verifier_affiliation=verifier_affiliation)

    machine = p.to_machine()
    ref = transport.publish(binding.as_subject_id(), machine,
                            machine["verified"]["projection"])
    registry.upsert(Row(subject_id=binding.as_subject_id(),
                        status=p.status,   # the passport's own; the row does not recompute it (NEW-1)
                        projection=machine["verified"]["projection"],
                        absent_reason=machine["verified"]["projection_absent_reason"],
                        protocol_version=PROTOCOL_VERSION,
                        valid_until=p.valid_until, passport_ref=ref))
    return Result(p, ref, div, findings)
