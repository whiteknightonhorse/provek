"""Phase 2 - the SSRF-guarded anonymous GET behind `service_endpoint` (spec 4.2-bis point 2).

⛔ SSRF BOUNDARY, MANDATORY (Fable's ruling - reachability and declaration validity may never move
the score or the projection; see `src/passport/passport.py:Service`/`ServiceEndpoint`). Every
probe here obeys all five of:

  1. https only - never plain http, never any other scheme;
  2. private and reserved addresses are refused AFTER DNS resolution, never by inspecting the
     hostname string. A hostname check is defeated trivially: `evil.example` can carry an A record
     that answers `169.254.169.254`, and the string `evil.example` contains nothing to catch that.
     Checking the resolved IP is the only check a rebinding attack cannot route around;
  3. the resolved address that is CHECKED is the address CONNECTED TO. A second, independent DNS
     resolution at connect time reopens exactly the TOCTOU gap point 2 exists to close (an attacker
     can answer the check-time lookup with a public IP and the connect-time lookup, moments later,
     with a private one). `curl --resolve host:port:ip` pins the two together;
  4. a bounded timeout, so one slow or hanging subject can never stall a batch re-measure;
  5. GET only, at most `MAX_REDIRECTS` hops followed, and EVERY hop is independently re-validated
     from scratch (points 1-3 again) before being followed - a redirect is exactly as capable of
     naming a private address as the original URL, and curl's own `-L` does not re-run this
     module's checks on a hop it follows internally, which is why this file drives the redirect
     loop itself rather than delegating it to curl.

WHAT THIS FILE DOES NOT DO. It is not a general HTTP client - it answers exactly one question
("is this declared URL reachable, right now, without ever touching a private network"), returns a
bool or raises `SSRFRefused`, and callers decide what a refusal MEANS (this module has no opinion
on whether the subject's declaration is a genuine mistake or a probe of our own infrastructure).
`src/collector/declaration.py` also imports `resolve_public_ip` from here, at DECLARATION PARSE
TIME rather than only at re-measure time - a declared `order_url` that already resolves privately
is rejected as an invalid declaration outright (LAW #ONE-PLACE: one resolve-and-check routine, two
callers, so the private-address rule cannot drift between "invalid declaration" and "unreachable
now").
"""
from __future__ import annotations

import ipaddress
import socket
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlparse

from src.passport.passport import Fact, ServiceEndpoint

TIMEOUT_SECONDS = 10
MAX_REDIRECTS = 2

HTTP_REDIRECT_LOW = 300
HTTP_REDIRECT_HIGH = 400   # exclusive
HTTP_OK_LOW = 200
HTTP_OK_HIGH = 300         # exclusive


class SSRFRefused(Exception):
    """A URL - or a redirect hop - fails the SSRF boundary: not https, no host, does not resolve,
    or resolves to a private/reserved/loopback/link-local/multicast/unspecified address."""


def _is_disallowed(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Every non-public IPv4/IPv6 shape, INCLUDING an IPv4-mapped IPv6 literal (`::ffff:127.0.0.1`)
    whose mapped v4 address is itself private - `IPv6Address.is_loopback`/`is_private` in the
    standard library check the address's OWN bit pattern and do not unwrap the mapping, so a
    literal that only *carries* a private v4 address inside a v6 wrapper would otherwise pass.

    `not ip.is_global` is the FLOOR (Fable's review of this module, 2026-09-02): `is_private` alone missed
    100.64.0.0/10 (RFC 6598 carrier-grade NAT) on this host's Python 3.10 - that range is folded
    into `is_private` only from Python 3.13, so a 3.10 interpreter reading a CGNAT literal answered
    "not private" while it is manifestly not a public address either. `is_global` has existed
    since 3.4 and correctly reads False for CGNAT space on 3.10 (verified live), so the named
    flags below stay as a readable enumeration of WHY, while `is_global` is what actually decides
    - strictly tightening, never loosening, since every one of the named flags already implies
    `not is_global`."""
    if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
            or ip.is_multicast or ip.is_unspecified or not ip.is_global):
        return True
    if getattr(ip, "is_site_local", False):          # IPv6-only attribute
        return True
    mapped = getattr(ip, "ipv4_mapped", None)
    return mapped is not None and _is_disallowed(mapped)


def resolve_public_ip(host: str) -> str:
    """Resolve `host` and return ONE literal public IP address, or raise `SSRFRefused`.

    Fails CLOSED on a mixed result (some resolved addresses public, some not): a name that answers
    both a public and a private address on the same lookup is the shape of a rebinding setup, not
    a subject's honest hosting choice, and picking "the public one" would let an attacker control
    which address wins by controlling DNS answer order.
    """
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError as e:
        raise SSRFRefused(f"could not resolve {host}: {e}") from e
    ips = {info[4][0] for info in infos}
    if not ips:
        raise SSRFRefused(f"{host} resolved to no addresses")
    parsed = [ipaddress.ip_address(ip) for ip in ips]
    if any(_is_disallowed(ip) for ip in parsed):
        raise SSRFRefused(f"{host} resolves to a private or reserved address")
    return str(parsed[0])


def _one_hop(url: str, *, timeout: float) -> tuple[int, str | None]:
    """One GET, fully re-validated from scratch. Returns (status_code, redirect_location) - status
    0 means the request never completed (refused, timed out, TLS failure, curl missing)."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise SSRFRefused(f"{url} is not https")
    host = parsed.hostname
    if not host:
        raise SSRFRefused(f"{url} has no host")
    port = parsed.port or 443
    ip = resolve_public_ip(host)
    resolve_literal = f"[{ip}]" if ":" in ip else ip
    p = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}\n%{redirect_url}",
         "--request", "GET",
         "--max-time", str(timeout), "--max-redirs", "0",
         "--resolve", f"{host}:{port}:{resolve_literal}",
         url],
        capture_output=True, text=True, timeout=timeout + 5)
    if p.returncode != 0:
        return 0, None
    lines = p.stdout.splitlines()
    status = int(lines[0]) if lines and lines[0].isdigit() else 0
    location = lines[1] if len(lines) > 1 and lines[1] else None
    return status, location


def probe_reachable(url: str, *, timeout: float = TIMEOUT_SECONDS,
                    max_redirects: int = MAX_REDIRECTS) -> bool:
    """One anonymous GET at `url`, following at most `max_redirects` hops - each hop independently
    SSRF-checked before it is followed. `True` iff the final hop answered 2xx.

    An `SSRFRefused` hop is NOT caught here - it propagates to the caller exactly like any other
    programming exception, because a private-address hop is not "the site is down", it is a
    boundary violation the caller must not silently fold into an ordinary `False`.
    """
    current = url
    redirects_followed = 0
    while True:
        status, location = _one_hop(current, timeout=timeout)
        if HTTP_REDIRECT_LOW <= status < HTTP_REDIRECT_HIGH:
            if location is None or redirects_followed >= max_redirects:
                return False
            current = location
            redirects_followed += 1
            continue
        return HTTP_OK_LOW <= status < HTTP_OK_HIGH


def probe_service_endpoint(order_url: Fact, *, now: datetime | None = None) -> ServiceEndpoint:
    """One anonymous GET at `order_url` if - and only if - one was actually declared, run once per
    re-measure (spec 4.2-bis point 2: "one GET on the re-measure", never on a schedule of its own).

    `order_url` is the ALREADY-PARSED `Fact` from `src/collector/declaration.py`'s `Service`, not a
    raw string - so this function never has to re-derive whether a URL was declared, and a
    declaration that came back `unreadable` or `not_declared` propagates the SAME reason into
    `service_endpoint` rather than inventing a fifth world for "there was nothing to probe".
    """
    if not order_url.measured:
        return ServiceEndpoint(declared=False,
                               reachable=Fact(measured=False, reason=order_url.reason),
                               checked_at=None)
    checked_at = (now or datetime.now(timezone.utc)).isoformat()
    try:
        ok = probe_reachable(order_url.value)
    except Exception:
        # THE ATTEMPT ITSELF FAILED - world 4 ("the check did not run cleanly"), distinct from a plain
        # non-2xx or refused connection, which `probe_reachable` already resolves to `False`
        # without raising. `SSRFRefused` lands here too: a declared URL that now resolves
        # privately (DNS changed since the declaration was accepted) is a check that could not
        # honestly run, not a quiet "unreachable".
        return ServiceEndpoint(declared=True, reachable=Fact.unreadable(), checked_at=checked_at)
    return ServiceEndpoint(declared=True, reachable=Fact.of(ok, confidence="measured"),
                           checked_at=checked_at)


def demo() -> None:
    """ponytail: smallest runnable self-check, not a test suite. Exercises the two load-bearing
    branches without a real network call: a private literal is refused, and a plain public literal
    (a real routable address is not required - the resolver never has to succeed to prove the
    disallow-list itself works) is accepted by `_is_disallowed`."""
    assert _is_disallowed(ipaddress.ip_address("169.254.169.254")) is True   # cloud metadata
    assert _is_disallowed(ipaddress.ip_address("127.0.0.1")) is True
    assert _is_disallowed(ipaddress.ip_address("10.0.0.5")) is True
    assert _is_disallowed(ipaddress.ip_address("::1")) is True
    assert _is_disallowed(ipaddress.ip_address("::ffff:127.0.0.1")) is True   # mapped loopback
    assert _is_disallowed(ipaddress.ip_address("100.64.0.1")) is True   # RFC 6598 CGNAT, Fable's review
    assert _is_disallowed(ipaddress.ip_address("8.8.8.8")) is False
    refused = False
    try:
        resolve_public_ip("169.254.169.254")
    except SSRFRefused:
        refused = True
    assert refused, "a literal private IP as the host must be refused"
    print("reachability demo: ok")


if __name__ == "__main__":
    demo()
