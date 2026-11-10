"""/auth.md is the one statement of this site's authentication, and today that statement is
"none". It must never name a credential, an endpoint or a token flow this site does not run
(web/discovery.mjs header). Held by exact strings; able to fail (evidence/RED-077)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "public" / "auth.md"
BUILT = ROOT / "web" / "dist" / "auth.md"

FORBIDDEN = ["client_id", "token_endpoint", "register_uri", "Bearer"]


def test_auth_md_exists_and_opens_with_an_h1_naming_auth_md():
    assert SRC.is_file(), "web/public/auth.md is missing"
    first = SRC.read_text(encoding="utf-8").splitlines()[0]
    assert first.startswith("# ") and "auth.md" in first


def test_auth_md_says_authentication_none():
    assert "Authentication: none" in SRC.read_text(encoding="utf-8")


def test_auth_md_names_no_credential_or_token_flow():
    text = SRC.read_text(encoding="utf-8")
    for word in FORBIDDEN:
        assert word not in text, f"auth.md contains {word!r}"
    assert not re.search(r"API key:\s*\S", text), "auth.md names an API key value"


def test_the_checker_can_fail():
    bad = SRC.read_text(encoding="utf-8") + "\ntoken_endpoint: https://x/\nAPI key: abc\n"
    assert "token_endpoint" in bad and re.search(r"API key:\s*\S", bad)


def test_built_auth_md_is_byte_identical_to_the_source():
    assert BUILT.is_file(), f"{BUILT} is absent: run `npm run build` in web/ (push.sh does)"
    assert BUILT.read_bytes() == SRC.read_bytes()


OPENAPI = ROOT / "web" / "public" / "openapi.json"


def _openapi_write_paths() -> set[str]:
    """POST operations that take a body: the writes. (Badge and brief also export a POST handler,
    which only answers 405 and takes nothing.)"""
    import json
    doc = json.loads(OPENAPI.read_text(encoding="utf-8"))
    return {p for p, item in doc["paths"].items() if "requestBody" in item.get("post", {})}


def _auth_md_post_paths(text: str) -> set[str]:
    return set(re.findall(r"`POST (/[^`\s]+)`", text))


def test_every_anonymous_write_in_openapi_is_named_in_auth_md_and_the_reverse():
    text = SRC.read_text(encoding="utf-8")
    assert _openapi_write_paths() == {"/api/apply", "/api/witness-submit"}
    assert _auth_md_post_paths(text) == _openapi_write_paths()


def test_auth_md_no_longer_says_one_write():
    assert "one write" not in SRC.read_text(encoding="utf-8")


def test_auth_md_quotes_the_witness_limits_from_the_module():
    text = SRC.read_text(encoding="utf-8")
    src = (ROOT / "web" / "functions" / "_lib" / "witnessRelay.js").read_text(encoding="utf-8")
    ip, day = (re.search(rf"{k}:\s*(\d+)", src).group(1) for k in ("per_ip_per_hour", "per_day_global"))
    assert f"{ip} per client per hour and {day} per UTC day" in text
    m = re.search(r"\((\d+) per (\d+) s per IP", (ROOT / "web" / "src" / "pages" / "Apply.tsx").read_text(encoding="utf-8"))
    assert f"({m.group(1)} per {m.group(2)} s)" in text
    om = re.search(r"EDGE_APPLY_LIMIT = Object\.freeze\(\{ requests: (\d+), perSeconds: (\d+) \}\)",
                   (ROOT / "web" / "openapi.mjs").read_text(encoding="utf-8"))
    assert (om.group(1), om.group(2)) == (m.group(1), m.group(2))
    assert f"({om.group(1)} per {om.group(2)} s)" in text


def test_the_pairing_check_can_fail():
    text = SRC.read_text(encoding="utf-8").replace("`POST /api/witness-submit`", "the relay")
    assert _auth_md_post_paths(text) != _openapi_write_paths()
