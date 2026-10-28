"""The Content-Security-Policy in web/public/_headers is held to what the built pages load
(T-0579): every loaded origin is allowed, and nothing beyond the inventory is allowed. Able to
fail: the mutation tests add a host to the policy and a script tag to a dist copy."""
from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HEADERS = ROOT / "web" / "public" / "_headers"
DIST = ROOT / "web" / "dist"

_spec = importlib.util.spec_from_file_location("csp_inventory", ROOT / "scripts" / "csp_inventory.py")
csp_inventory = importlib.util.module_from_spec(_spec)
sys.modules["csp_inventory"] = csp_inventory
_spec.loader.exec_module(csp_inventory)

REMOTE = ("script-src", "connect-src", "img-src", "frame-src")
NOT_ORIGINS = {"'self'", "'none'", "'unsafe-inline'", "data:"}


def _block(text: str) -> dict[str, str]:
    """Header lines under the `/*` rule."""
    out, inside = {}, False
    for line in text.splitlines():
        if line.startswith("/"):
            inside = line.strip() == "/*"
        elif inside and line.startswith("  ") and ":" in line:
            k, v = line.strip().split(":", 1)
            out[k.strip()] = v.strip()
    return out


def _policy(text: str) -> dict[str, list[str]]:
    csp = _block(text)["Content-Security-Policy"]
    return {d.split()[0]: d.split()[1:] for d in (x.strip() for x in csp.split(";")) if d}


def _remote(policy: dict, directive: str) -> set[str]:
    return {t for t in policy.get(directive, []) if t not in NOT_ORIGINS and not t.startswith("'sha256-")}


@pytest.fixture(scope="module")
def inv():
    if not DIST.is_dir():
        pytest.fail(f"{DIST} is absent: run `npm run build` in web/ (push.sh does)")
    return csp_inventory.inventory(DIST)


def _problems(headers_text: str, inv: dict) -> list[str]:
    pol = _policy(headers_text)
    bad = []
    for d in REMOTE:
        allowed, needed = _remote(pol, d), set(inv["needs"][d])
        bad += [f"{d}: loaded but not allowed: {o}" for o in sorted(needed - allowed)]
        bad += [f"{d}: allowed but nothing loads it: {o}" for o in sorted(allowed - needed)]
    scripts = pol.get("script-src", [])
    if inv["inline_script_needs_unsafe_inline"] and "'unsafe-inline'" not in scripts:
        bad.append("script-src: inline executable scripts exist but 'unsafe-inline' is absent")
    if not inv["inline_script_needs_unsafe_inline"] and "'unsafe-inline'" in scripts:
        bad.append("script-src: no inline executable script left, drop 'unsafe-inline'")
    styles = pol.get("style-src", [])
    if inv["inline_style_needs_unsafe_inline"] != ("'unsafe-inline'" in styles):
        bad.append("style-src: 'unsafe-inline' must be present exactly when the pages carry inline styles")
    for d in ("frame-ancestors", "object-src"):
        if pol.get(d) != ["'none'"]:
            bad.append(f"{d} must be 'none'")
    return bad


def test_policy_matches_the_inventory(inv):
    assert _problems(HEADERS.read_text(encoding="utf-8"), inv) == []


def test_the_other_security_headers_are_set():
    h = _block(HEADERS.read_text(encoding="utf-8"))
    assert h["X-Frame-Options"] == "DENY"
    assert h["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
    assert "preload" not in h["Strict-Transport-Security"]
    pp = h["Permissions-Policy"]
    assert all(f"{f}=()" in pp for f in ("camera", "microphone", "geolocation"))
    assert "interest-cohort" not in pp


def test_mutation_an_extra_allowed_host_is_red(inv):
    text = HEADERS.read_text(encoding="utf-8").replace(
        "connect-src 'self'", "connect-src 'self' https://evil.example", 1
    )
    assert any("evil.example" in p for p in _problems(text, inv))


def test_mutation_a_new_script_origin_in_dist_is_red(tmp_path, inv):
    copy = tmp_path / "dist"
    shutil.copytree(DIST, copy)
    page = copy / "index.html"
    page.write_text(
        page.read_text(encoding="utf-8").replace("</head>", '<script src="https://cdn.example/x.js"></script></head>', 1),
        encoding="utf-8",
    )
    mutated = csp_inventory.inventory(copy)
    assert any("cdn.example" in p for p in _problems(HEADERS.read_text(encoding="utf-8"), mutated))


def test_mutation_a_dist_without_inline_scripts_makes_unsafe_inline_red(tmp_path):
    copy = tmp_path / "dist"
    copy.mkdir()
    (copy / "index.html").write_text(
        '<html><head><script type="application/ld+json">{}</script></head><body></body></html>', encoding="utf-8"
    )
    mutated = csp_inventory.inventory(copy)
    assert mutated["inline_script_needs_unsafe_inline"] is False
    assert any("drop 'unsafe-inline'" in p for p in _problems(HEADERS.read_text(encoding="utf-8"), mutated))
