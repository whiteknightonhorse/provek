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
