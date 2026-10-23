"""/.well-known/security.txt exists and has not expired.

A TIME BOMB BY DESIGN, like the liveness tests: RFC 9116 requires `Expires`, and a file that
outlived it is worse than none. When this goes red, renew `Expires` (one year ahead) in
web/public/.well-known/security.txt.
"""
from __future__ import annotations

import datetime as dt
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEC = ROOT / "web" / "public" / ".well-known" / "security.txt"


def _fields() -> dict[str, str]:
    assert SEC.is_file(), "web/public/.well-known/security.txt is missing"
    out = {}
    for line in SEC.read_text(encoding="utf-8").splitlines():
        if ":" in line and not line.startswith("#"):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def test_required_fields_present():
    f = _fields()
    assert f["Contact"].startswith("https://github.com/whiteknightonhorse/provek/security/advisories")
    assert f["Canonical"] == "https://provek.dev/.well-known/security.txt"
    assert "SECURITY.md" in f["Policy"]


def test_expires_parses_and_is_in_the_future():
    expires = dt.datetime.fromisoformat(_fields()["Expires"].replace("Z", "+00:00"))
    assert expires > dt.datetime.now(dt.timezone.utc), f"security.txt expired {expires}"
