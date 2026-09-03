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
from src.collector.declaration import apply_declaration, github_full_name
from src.collector.divergence import Divergence, compare
from src.collector.github import (
    EVIDENCE_WINDOW_DAYS,
    collect_github,
    publishable_source,
    reads_completed,
)
from src.collector.reachability import probe_service_endpoint
from src.collector.repo import collect
from src.passport.passport import (
    PROFILE_VERSION,
    PROTOCOL_VERSION,
    Accountability,
    Passport,
    Provenance,
    Service,
    build,
)
from src.registry.public_registry import PublicRegistry, Row
from src.verify.control_map import (
    GITHUB_DID_NOT_ANSWER,
    GITHUB_PARTIAL_READ,
    ControlMap,
    build_coverage,
)
from src.verify.scorer import OperationScore, projection, score_operation

# PROTOCOL_VERSION and PROFILE_VERSION are imported, not declared here (LAW #ONE-PLACE, Fable,
# 2026-09-01). This module used to carry its own "1.0.0" / "1.0.0" - a second and third literal
# beside `scripts/cohort.py`'s `Provenance("1.0.0", "1.1.0", ...)`, disagreeing about which
# methodology version is live. `src/passport/passport.py` is the canonical source; see its
# docstring for why 1.1.0 is the correct value.


@dataclass(frozen=True)
class Result:
    passport: Passport
    published_ref: str
    divergence: Divergence
    findings: list[str]


def _observed_level(signed_share: Measurement, authors: Measurement,
                    identity_window_closed: Measurement | None = None) -> L | None:
    """Level for the operation "development initiation", from OBSERVABLE signals.

    HONEST BOUNDARY. This is an APPROXIMATION, not proof of autonomy: signatures and author counts
    do not say who pressed the button (attack T1, unimplementable register U-2). The result is
    recorded as platform_observed and is NEVER presented as a verdict that no human wrote the code.

    `identity_window_closed` is `None` for a plain git clone (`src.collector.repo`), which has no
    platform to attribute an unsigned commit's identity to and so has no closure claim to make -
    the gate below simply does not apply there, exactly as before this parameter existed. For
    GitHub-sourced evidence (`src.collector.github.collect_github`) it is ALWAYS a real Measurement,
    and PLATFORM CLOSURE (Fable, 2026-08-25) applies: `authors` is only an author COUNT when every
    non-bot commit in the window was attributed by the platform or by a signature; an open window
    makes it a lower bound only, and the ladder answers that with the L2 floor rather than a guess
    in either direction (AUD-002 - this gate used to live only in `scripts/cohort.py`, so a GitHub
    subject scored through this "single entry point" skipped it entirely).

    Deliberately keeps its OWN thresholds (`FEW_AUTHORS_FOR_L3`, weighing the signature share for
    L4) rather than `scripts/cohort.py`'s `cohort_development_initiation_level` and
    `SMALL_TEAM_FOR_L3` - see that constant's docstring for why two procedures exist on purpose.
    """
    if not signed_share.is_measured or not authors.is_measured:
        return None
    if identity_window_closed is not None and not (
            identity_window_closed.is_measured and identity_window_closed.value):
        return L.L2
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

    # `collect()` (a plain git clone) is the ONLY source of `tree_digest`, so it runs regardless of
    # remote shape - it is what the divergence check below (T-2.4, attack T4) compares against
    # `deployed_digest`, and the GitHub API this function may ALSO call below has no equivalent
    # full-tree content read to offer it.
    ev = collect(remote, now=now)
    findings.extend(ev.notes)

    div = compare(ev.tree_digest, deployed_digest)
    if div is Divergence.DIVERGED:
        findings.append("DIVERGENCE: what is deployed does not match what is committed (attack T4)")
    elif div is Divergence.NOT_MEASURED:
        findings.append("deployed artefact was not presented - the comparison WAS NOT PERFORMED, "
                        "and that is not a violation by the subject")

    # AUD-002 (2026-09-03). Until this fix, EVERY remote - including a real github.com one - was
    # scored from `ev` above: a 50-commit COUNT window (the errata already published against
    # `collect_github` on 2026-08-25 for a different reader), no platform closure, no bot-exclusion
    # rule, and a `github_inspected=True` coverage claim stamped even when the clone above had just
    # failed. Production (`scripts/cohort.py`) never had that defect because it never went through
    # `ev` at all - it reads GitHub through `collect_github`, the same function this "single entry
    # point" is supposed to be equivalent to and was not.
    #
    # A GitHub remote is now ALSO read through `collect_github` - the same collector, the same
    # published `EVIDENCE_WINDOW_DAYS`, the same platform-closure and bot-exclusion rules - and that
    # second, richer read is what scores `development_initiation` and builds coverage. A non-GitHub
    # remote (a local path, in every test this module's own suite runs offline) has no such second
    # reader available and keeps scoring from `ev`, now itself windowed by time rather than count.
    full_name = github_full_name(remote)
    gh = collect_github(full_name) if full_name is not None else None
    if gh is not None:
        findings.extend(gh.notes)
        publishable = publishable_source(gh)
        lvl = _observed_level(gh.signed_commit_share, gh.distinct_authors,
                              gh.identity_window_closed)
        observed = (EvidenceClass.PLATFORM_OBSERVED,) if publishable else ()
        runtime_trace = gh.has_runtime_trace
        default_inspected = reads_completed(gh)
        default_absent_reason = GITHUB_DID_NOT_ANSWER if not publishable else GITHUB_PARTIAL_READ
    else:
        local_read_ok = ev.tree_digest is not None
        lvl = _observed_level(ev.signed_commit_share, ev.distinct_authors)
        observed = (EvidenceClass.PLATFORM_OBSERVED,) if local_read_ok else ()
        runtime_trace = False
        default_inspected = local_read_ok
        default_absent_reason = GITHUB_DID_NOT_ANSWER

    cmap = control_map or ControlMap(paths=[], coverage=build_coverage(
        github_inspected=default_inspected, github_absent_reason=default_absent_reason))
    cap = cmap.implied_level_cap() if cmap.is_valid() else None

    scores: list[OperationScore] = [
        score_operation("development_initiation", lvl, observed, cap,
                        weak_mixed_signal=True, runtime_trace=runtime_trace),
        score_operation("deployment", None, ()),        # runtime not presented -> not_measured
        score_operation("treasury_control", None, ()),  # outside MVP scope -> not_measured
    ]

    # PHASE 2 - the subject's own `provek.json`, if `remote` names a GitHub repository. Pinned to
    # the head_sha the base collector for THIS remote already measured - never a second lookup for
    # it: `gh.head_sha` (from `collect_github`, matching what `scripts/cohort.py` pins to) when one
    # was read, `ev.head_sha` (from the local clone) otherwise. `github_full_name` returns `None`
    # for anything that is not a GitHub remote (a local path in this module's own tests included),
    # and the accountability block then stays at its default - the check genuinely did not run for
    # a subject this collector cannot name a declaration location for.
    accountability, service, claims = Accountability(), Service(), dict(claims or {})
    if full_name is not None:
        head_sha = gh.head_sha if gh is not None else ev.head_sha
        accountability, service, claims = apply_declaration(full_name, head_sha, claims)

    # ONE anonymous GET per re-measure (spec 4.2-bis point 2) - `verify()` already runs once per
    # subject per re-measure cycle, so calling this here, exactly once, IS the "one GET" rule; no
    # separate throttle is needed on top of it.
    service_endpoint = probe_service_endpoint(service.order_url, now=now)

    p = build(binding, scores, cmap, projection(scores),
              Provenance(PROTOCOL_VERSION, PROFILE_VERSION, EVIDENCE_WINDOW_DAYS),
              accountability,
              now=now, claims=claims, mandate_ref=mandate_ref,
              verifier_affiliation=verifier_affiliation,
              service=service, service_endpoint=service_endpoint)

    machine = p.to_machine()
    ref = transport.publish(binding.as_subject_id(), machine,
                            machine["verified"]["projection"])
    registry.upsert(Row(subject_id=binding.as_subject_id(),
                        status=p.status,   # the passport's own; the row does not recompute it (NEW-1)
                        projection=machine["verified"]["projection"],
                        absent_reason=machine["verified"]["projection_absent_reason"],
                        protocol_version=PROTOCOL_VERSION,
                        valid_until=p.valid_until, passport_ref=ref,
                        service_url=(service.order_url.value if service.order_url.measured
                                    else None),
                        service_reachable=(service_endpoint.reachable.value
                                           if service_endpoint.reachable.measured else None)))
    return Result(p, ref, div, findings)
