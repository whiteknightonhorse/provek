"""Phase 2 - the Provider Catalog's `service` declaration and `service_endpoint` reachability
check (specification 4.2-bis, points 1-2; Fable's phase-1 backend ruling).

TWO BLOCKS, BOTH OUTSIDE THE SCORE, mirroring `Accountability`'s own guarantee:
  `service`          - self-declared (`order_url`, `offering`, `pricing_url`, `terms_url`),
                        confidence ALWAYS "assumed", schema 1.1.0 (`src/collector/declaration.py`).
  `service_endpoint`  - PLATFORM_OBSERVED: one anonymous GET at the declared `order_url`, SSRF-
                        guarded (`src/collector/reachability.py`).

Every network call in this file is stubbed - either `declaration._fetch_raw` (the same discipline
`tests/test_declaration.py` already keeps) or the SSRF primitives in `reachability` themselves -
so nothing here touches a real socket. The two MANDATORY controls named in the operator's brief
for this backend step are marked `MANDATORY CONTROL` below: (1) a mutation that makes the scorer
read `service`
must fail the projection-invariance test; (2) a declared `order_url` that resolves to a private
address invalidates the WHOLE declaration, not just `service_endpoint.reachable`.
"""
from __future__ import annotations

import ipaddress
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.identity import Binding, BindingKind
from src.abs_profile.ladder import L
from src.abs_profile.measured import NotMeasured
from src.collector import declaration as decl
from src.collector import reachability as reach
from src.passport.passport import Accountability, Fact, Provenance, Service, ServiceEndpoint, build
from src.registry.lifecycle import Status
from src.registry.public_registry import PublicRegistry, Row
from src.verify.control_map import ControlMap, Coverage, Surface
from src.verify.scorer import projection, score_operation

FULL = "whiteknightonhorse/example"


def _stub(monkeypatch, code: int, body: str):
    monkeypatch.setattr(decl, "_fetch_raw", lambda full_name, ref: (code, body))


def _doc(service: dict | None) -> dict:
    doc = {"provek_declaration": "1.1.0"}
    if service is not None:
        doc["service"] = service
    return doc


# --------------------------------------------------------------------------------------------
# DECLARATION SHAPE - order_url required + https, offering <=500, pricing_url/terms_url optional.
# --------------------------------------------------------------------------------------------

def test_MANDATORY_CONTROL_positive_a_plain_https_order_url_is_accepted(monkeypatch):
    """Control-positive: an ordinary, well-formed https declaration passes cleanly."""
    _stub(monkeypatch, 200, json.dumps(_doc({
        "order_url": "https://example.com/order",
        "offering": "We build websites",
        "pricing_url": "https://example.com/pricing",
        "terms_url": "https://example.com/terms",
    })))
    result = decl.collect_declaration(FULL, "deadbeef")

    assert result.service.order_url.measured is True
    assert result.service.order_url.reason is None
    assert result.service.order_url.confidence == "assumed"        # NEVER "measured"
    assert result.service.order_url.value == "https://example.com/order"
    assert result.service.offering.value == "We build websites"
    assert result.service.pricing_url.value == "https://example.com/pricing"
    assert result.service.terms_url.value == "https://example.com/terms"
    # the accountability block is unaffected by a service block being present
    assert result.accountability.claims_addressee.measured is False


def test_order_url_is_required_missing_field_invalidates_whole_declaration(monkeypatch):
    _stub(monkeypatch, 200, json.dumps(_doc({"offering": "no order_url here"})))
    result = decl.collect_declaration(FULL, "deadbeef")
    assert result.service.order_url.reason is NotMeasured.UNREADABLE
    # one bad field invalidates the WHOLE document - accountability too, same as D-43.
    assert result.accountability.claims_addressee.reason is NotMeasured.UNREADABLE


@pytest.mark.parametrize("bad_url", [
    "http://example.com/order",     # not https
    "ftp://example.com/order",
    "not a url at all",
    "https://",                     # no host
    "",
])
def test_non_https_or_malformed_order_url_invalidates_whole_declaration(monkeypatch, bad_url):
    _stub(monkeypatch, 200, json.dumps(_doc({"order_url": bad_url})))
    result = decl.collect_declaration(FULL, "deadbeef")
    assert result.service.order_url.reason is NotMeasured.UNREADABLE
    assert result.accountability.insurance.reason is NotMeasured.UNREADABLE


def test_offering_over_500_chars_invalidates_whole_declaration(monkeypatch):
    _stub(monkeypatch, 200, json.dumps(_doc({
        "order_url": "https://example.com/order",
        "offering": "x" * (decl.FIELD_MAX_CHARS + 1),
    })))
    result = decl.collect_declaration(FULL, "deadbeef")
    assert result.service.offering.reason is NotMeasured.UNREADABLE
    assert result.service.order_url.reason is NotMeasured.UNREADABLE   # whole block, not one field


@pytest.mark.parametrize("bad_url", ["http://example.com/pricing", "not a url"])
def test_optional_url_fields_are_held_to_the_same_https_boundary(monkeypatch, bad_url):
    """pricing_url and terms_url are optional, but a PRESENT value is held to the same https+valid
    rule as order_url - a weaker gate on two of three URL fields would be the inconsistency
    LAW #ONE-PLACE forbids."""
    _stub(monkeypatch, 200, json.dumps(_doc({
        "order_url": "https://example.com/order",
        "pricing_url": bad_url,
    })))
    result = decl.collect_declaration(FULL, "deadbeef")
    assert result.service.order_url.reason is NotMeasured.UNREADABLE


def test_service_absent_from_document_is_not_declared_for_every_field(monkeypatch):
    _stub(monkeypatch, 200, json.dumps(_doc(None)))
    result = decl.collect_declaration(FULL, "deadbeef")
    for f in ("order_url", "offering", "pricing_url", "terms_url"):
        fact = getattr(result.service, f)
        assert fact.measured is False
        assert fact.reason is NotMeasured.NOT_DECLARED


def test_service_missing_entirely_is_the_SAME_shape_as_a_404_declaration(monkeypatch):
    """world 3 for `service` is not a special case - a subject with no `provek.json` at all gets
    the identical `not_declared` reason `_not_declared()` already gives `accountability`."""
    _stub(monkeypatch, 404, "404: Not Found")
    result = decl.collect_declaration(FULL, "deadbeef")
    assert result.service.order_url.measured is False
    assert result.service.order_url.reason is NotMeasured.NOT_DECLARED


# --------------------------------------------------------------------------------------------
# MANDATORY CONTROL - a private/reserved address in order_url invalidates the WHOLE declaration,
# not just service_endpoint.reachable. Checked AFTER resolution (mocked here, no real DNS).
# --------------------------------------------------------------------------------------------

def test_MANDATORY_CONTROL_private_address_in_order_url_invalidates_whole_declaration(monkeypatch):
    monkeypatch.setattr(decl, "resolve_public_ip",
                        lambda host: (_ for _ in ()).throw(
                            reach.SSRFRefused(f"{host} resolves to a private address")))
    _stub(monkeypatch, 200, json.dumps(_doc({"order_url": "https://evil.example/order"})))
    result = decl.collect_declaration(FULL, "deadbeef")

    assert result.service.order_url.reason is NotMeasured.UNREADABLE
    # the WHOLE declaration, not a quietly-dropped field - accountability is unreadable too.
    assert result.accountability.dispute_path.reason is NotMeasured.UNREADABLE
    assert result.present is None            # world 4, existence itself is unknown


def test_a_url_that_resolves_publicly_is_not_refused(monkeypatch):
    """CONTROL-POSITIVE for the SSRF check itself: a hostname `resolve_public_ip` accepts must not
    be refused - proving the mock above tests the refusal path and not a permanently-red gate."""
    monkeypatch.setattr(decl, "resolve_public_ip", lambda host: "93.184.216.34")
    _stub(monkeypatch, 200, json.dumps(_doc({"order_url": "https://example.com/order"})))
    result = decl.collect_declaration(FULL, "deadbeef")
    assert result.service.order_url.measured is True
    assert result.service.order_url.reason is None


# --------------------------------------------------------------------------------------------
# THE SSRF PRIMITIVE ITSELF (`src/collector/reachability.py`) - real ipaddress checks, no network.
# --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("ip", [
    "127.0.0.1", "10.1.2.3", "172.16.0.1", "192.168.1.1", "169.254.169.254",
    "::1", "fc00::1", "fe80::1", "::ffff:127.0.0.1",   # IPv4-mapped loopback
])
def test_disallowed_addresses_are_all_caught(ip):
    assert reach._is_disallowed(ipaddress.ip_address(ip)) is True


@pytest.mark.parametrize("ip", ["8.8.8.8", "1.1.1.1", "2606:4700:4700::1111"])
def test_public_addresses_are_not_caught(ip):
    assert reach._is_disallowed(ipaddress.ip_address(ip)) is False


def test_resolve_public_ip_refuses_a_literal_private_address():
    """`socket.getaddrinfo` resolves a numeric literal without touching the network, so this
    exercises the real resolve-then-check path with no stub at all."""
    with pytest.raises(reach.SSRFRefused):
        reach.resolve_public_ip("169.254.169.254")


def test_resolve_public_ip_accepts_a_literal_public_address():
    assert reach.resolve_public_ip("8.8.8.8") == "8.8.8.8"


def test_resolve_public_ip_fails_closed_on_a_mixed_result(monkeypatch):
    """A hostname answering BOTH a public and a private address is refused outright - picking "the
    public one" would let an attacker control the outcome via DNS answer order."""
    monkeypatch.setattr(reach.socket, "getaddrinfo", lambda host, port: [
        (None, None, None, None, ("8.8.8.8", 0)),
        (None, None, None, None, ("127.0.0.1", 0)),
    ])
    with pytest.raises(reach.SSRFRefused):
        reach.resolve_public_ip("mixed.example")


def test_probe_reachable_refuses_non_https():
    with pytest.raises(reach.SSRFRefused):
        reach.probe_reachable("http://example.com/order")


def test_probe_reachable_is_get_only_and_ssrf_pinned(monkeypatch):
    """Inspects the actual command built for the GET - proves `--request GET`, `--resolve` pinning
    to the CHECKED address, and `--max-redirs 0` (this module drives redirects itself, never curl)
    are really there, not merely documented."""
    seen = {}

    def _fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        class R:
            returncode = 0
            stdout = "200\n"
        return R()

    monkeypatch.setattr(reach, "resolve_public_ip", lambda host: "93.184.216.34")
    monkeypatch.setattr(reach.subprocess, "run", _fake_run)
    ok = reach.probe_reachable("https://example.com/order")
    assert ok is True
    cmd = seen["cmd"]
    assert "GET" in cmd and cmd[cmd.index("--request") + 1] == "GET"
    assert "--max-redirs" in cmd and cmd[cmd.index("--max-redirs") + 1] == "0"
    assert any(c.startswith("example.com:443:93.184.216.34") for c in cmd)


def test_probe_reachable_stops_after_max_redirects(monkeypatch):
    """MANDATORY: no more than `MAX_REDIRECTS` hops are followed - a subject redirecting forever
    must resolve to `False`, not loop or raise."""
    calls = {"n": 0}

    def _always_redirect(url, *, timeout):
        calls["n"] += 1
        return 302, "https://example.com/next"

    monkeypatch.setattr(reach, "_one_hop", _always_redirect)
    assert reach.probe_reachable("https://example.com/start") is False
    assert calls["n"] == reach.MAX_REDIRECTS + 1     # the original request plus each redirect followed


def test_probe_reachable_true_on_2xx_false_on_4xx(monkeypatch):
    monkeypatch.setattr(reach, "_one_hop", lambda url, *, timeout: (200, None))
    assert reach.probe_reachable("https://example.com/x") is True
    monkeypatch.setattr(reach, "_one_hop", lambda url, *, timeout: (404, None))
    assert reach.probe_reachable("https://example.com/x") is False


# --------------------------------------------------------------------------------------------
# `probe_service_endpoint` - the four worlds of `service_endpoint`.
# --------------------------------------------------------------------------------------------

def test_endpoint_not_declared_when_order_url_was_never_declared():
    fact = Fact(measured=False, reason=NotMeasured.NOT_DECLARED)
    ep = reach.probe_service_endpoint(fact)
    assert ep.declared is False
    assert ep.reachable.reason is NotMeasured.NOT_DECLARED
    assert ep.checked_at is None


def test_endpoint_declared_and_reachable(monkeypatch):
    monkeypatch.setattr(reach, "probe_reachable", lambda url, **kw: True)
    fact = Fact.of("https://example.com/order")
    ep = reach.probe_service_endpoint(fact)
    assert ep.declared is True
    assert ep.reachable.measured is True
    assert ep.reachable.value is True
    assert ep.reachable.confidence == "measured"      # PLATFORM_OBSERVED, not "assumed"
    assert ep.checked_at is not None


def test_endpoint_declared_and_unreachable(monkeypatch):
    monkeypatch.setattr(reach, "probe_reachable", lambda url, **kw: False)
    fact = Fact.of("https://example.com/order")
    ep = reach.probe_service_endpoint(fact)
    assert ep.declared is True
    assert ep.reachable.value is False


def test_endpoint_declared_but_the_check_itself_could_not_run(monkeypatch):
    """world 4 - the SSRF boundary (or any other exception) fires DURING the probe, distinct from
    an ordinary non-2xx or refused connection, which resolves to `False` without raising."""
    def _raise(url, **kw):
        raise reach.SSRFRefused("resolved privately after the declaration was accepted")
    monkeypatch.setattr(reach, "probe_reachable", _raise)
    fact = Fact.of("https://example.com/order")
    ep = reach.probe_service_endpoint(fact)
    assert ep.declared is True
    assert ep.reachable.reason is NotMeasured.UNREADABLE


# --------------------------------------------------------------------------------------------
# `service`/`service_endpoint` LIVE OUTSIDE `verified` - structural check on the machine document.
# --------------------------------------------------------------------------------------------

def _minimal_passport(**kw):
    scores = [score_operation("development_initiation", L.L3, (EvidenceClass.PLATFORM_OBSERVED,)),
             score_operation("deployment", None, ()),
             score_operation("treasury_control", None, ())]
    cov = Coverage([Surface.GITHUB], {"treasury": "no access"}, "a key in CI")
    binding = Binding(BindingKind.GIT, FULL)
    return build(binding, scores, ControlMap([], cov), projection(scores),
                Provenance("1.1.0", "1.1.0", 30), Accountability(), **kw)


def test_service_and_service_endpoint_are_top_level_not_inside_verified():
    p = _minimal_passport(service=Service(order_url=Fact.of("https://example.com/order")),
                          service_endpoint=ServiceEndpoint(declared=True,
                                                           reachable=Fact.of(True, "measured"),
                                                           checked_at="2026-09-02T00:00:00+00:00"))
    m = p.to_machine()
    assert "service" in m and "service_endpoint" in m
    assert "service" not in m["verified"] and "service_endpoint" not in m["verified"]
    assert m["service"]["order_url"]["value"] == "https://example.com/order"
    assert m["service_endpoint"]["value"] is True
    assert m["service_endpoint"]["declared"] is True


# --------------------------------------------------------------------------------------------
# MANDATORY CONTROL - `service` and `service_endpoint` can NEVER move the score or the projection.
# --------------------------------------------------------------------------------------------

def test_MANDATORY_CONTROL_service_block_never_moves_the_score():
    """A passport with a fully-populated `service`+`service_endpoint` and one with neither, built
    from otherwise IDENTICAL inputs, must produce a byte-identical `verified` branch - the same
    proof `tests/test_declaration.py` already holds `accountability` to."""
    bare = _minimal_passport().to_machine()
    full = _minimal_passport(
        service=Service(order_url=Fact.of("https://example.com/order"),
                        offering=Fact.of("we do things"),
                        pricing_url=Fact.of("https://example.com/pricing"),
                        terms_url=Fact.of("https://example.com/terms")),
        service_endpoint=ServiceEndpoint(declared=True, reachable=Fact.of(True, "measured"),
                                         checked_at="2026-09-02T00:00:00+00:00"),
    ).to_machine()

    assert bare["verified"] == full["verified"]
    assert bare["status"] == full["status"]
    # the two DO differ - in the branches that are allowed to differ.
    assert bare["service"] != full["service"]
    assert bare["service_endpoint"] != full["service_endpoint"]


def test_MANDATORY_CONTROL_a_scorer_that_read_service_would_be_CAUGHT(monkeypatch):
    """THE MUTATION, run live rather than only argued: patch `build()` so that a declared,
    reachable `order_url` bumps the projection by one point - exactly the regression the invariant
    test above exists to catch - and prove that invariant test WOULD go red against it.

    This does not mutate the shipped `build()` on disk; it wraps the imported name for the
    duration of this test only, the same discipline `tests/test_ratchet_staged_media.py` and
    `tests/test_ratchet_phase3_note.py` hold their own live-mutation tests to (there restoring a
    file's bytes in `finally`; here restoring the monkeypatched attribute automatically when the
    test ends, since `monkeypatch` does that itself).
    """
    scores = [score_operation("development_initiation", L.L3, (EvidenceClass.PLATFORM_OBSERVED,)),
             score_operation("deployment", None, ()),
             score_operation("treasury_control", None, ())]
    cov = Coverage([Surface.GITHUB], {"treasury": "no access"}, "a key in CI")
    binding = Binding(BindingKind.GIT, FULL)
    real_build = build

    def mutant_build(*args, **kwargs):
        p = real_build(*args, **kwargs)
        service = kwargs.get("service")
        if service is not None and service.order_url.measured and p.verified.get("projection") is not None:
            # THE DEFECT: mutating the dict IN PLACE. A frozen dataclass forbids rebinding
            # `p.verified` to a new object, not mutating the mutable dict it already points to -
            # exactly the loophole a careless scorer patch could exploit for real.
            p.verified["projection"] += 1
        return p

    bare = mutant_build(binding, scores, ControlMap([], cov), projection(scores),
                        Provenance("1.1.0", "1.1.0", 30), Accountability()).to_machine()
    full = mutant_build(
        binding, scores, ControlMap([], cov), projection(scores),
        Provenance("1.1.0", "1.1.0", 30), Accountability(),
        service=Service(order_url=Fact.of("https://example.com/order")),
        service_endpoint=ServiceEndpoint(declared=True, reachable=Fact.of(True, "measured")),
    ).to_machine()

    # THE MANDATORY ASSERTION: the mutant DOES move the score, so the real invariant assertion
    # (`bare["verified"] == full["verified"]`) FAILS against it - proving the check above is not
    # vacuously green.
    assert bare["verified"] != full["verified"]
    assert full["verified"]["projection"] == bare["verified"]["projection"] + 1


# --------------------------------------------------------------------------------------------
# REGISTRY ROW - service_url / service_reachable.
# --------------------------------------------------------------------------------------------

def test_registry_row_carries_service_url_and_reachable():
    now = datetime(2026, 9, 2, tzinfo=timezone.utc)
    r = PublicRegistry(Path(tempfile.mkdtemp()))
    r.upsert(Row(subject_id="git:a/b", status=Status.VERIFIED, projection=60, absent_reason=None,
                protocol_version="1.1.0", valid_until=now + timedelta(days=30),
                passport_ref="p.json", service_url="https://example.com/order",
                service_reachable=True))
    row = r.to_machine(now)["subjects"][0]
    assert row["service_url"] == "https://example.com/order"
    assert row["service_reachable"] is True


def test_registry_row_defaults_service_fields_to_none():
    now = datetime(2026, 9, 2, tzinfo=timezone.utc)
    r = PublicRegistry(Path(tempfile.mkdtemp()))
    r.upsert(Row(subject_id="git:c/d", status=Status.UNVERIFIED, projection=None,
                absent_reason="check_did_not_run", protocol_version="1.1.0",
                valid_until=now + timedelta(days=30), passport_ref="p2.json"))
    row = r.to_machine(now)["subjects"][0]
    assert row["service_url"] is None
    assert row["service_reachable"] is None
