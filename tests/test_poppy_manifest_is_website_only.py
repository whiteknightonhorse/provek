"""/.well-known/poppy.json (Personal Agent Protocol, discovery): a website-only manifest. The
`web` block is empty because this site runs no API a Poppy client could call; naming one would be
an invented capability (evidence/RED-077)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POPPY = ROOT / "web" / "public" / ".well-known" / "poppy.json"


def test_poppy_manifest_is_exactly_the_website_only_shape():
    assert POPPY.is_file()
    doc = json.loads(POPPY.read_text(encoding="utf-8"))
    assert set(doc) == {"protocol_version", "organization", "web"}
    assert doc["protocol_version"] == "0.1"
    assert doc["organization"]["domain"] == "provek.dev"
    assert doc["web"] == {}


def test_a_manifest_with_an_added_capability_would_fail_the_shape():
    doc = {"protocol_version": "0.1", "organization": {"domain": "provek.dev"}, "web": {}, "mcp": {}}
    assert set(doc) != {"protocol_version", "organization", "web"}
