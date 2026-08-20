"""The SERVED set must equal the LISTED set.

Two artefacts survived a repository rename and a self-apply run: `proofofautonomy` (this project's
own former name) and `incubator/incubator`. Neither appeared in the registry, and both stayed
fetchable at a stable path carrying schema 1.0.0 - the version whose accountability block claimed a
check that never ran. The transport publishes and never retracts, so the served surface drifts
upwards from the listed one and nothing notices.

This is the measured-artefact rule: a registry row is not what a reader fetches. Check the thing
that is served.

The comparison runs in BOTH directions on purpose. Served-minus-listed is an unreachable document
still answering to anyone holding the URL; listed-minus-served is a row whose link is dead. They
fail for opposite reasons and neither is visible from the other side.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "public" / "registry" / "registry.json"
PASSPORTS = ROOT / "public" / "passports"


def _sets() -> tuple[set[str], set[str]]:
    listed = {s["subject_id"] for s in json.loads(REGISTRY.read_text())["subjects"]}
    served = {json.loads(f.read_text())["passport"]["subject_id"]
              for f in sorted(PASSPORTS.glob("*.json"))}
    return listed, served


@pytest.mark.skipif(not REGISTRY.exists(), reason="no registry emitted in this checkout")
def test_every_served_passport_is_listed():
    listed, served = _sets()
    assert served - listed == set(), "served but unlisted - reachable by URL, invisible in the registry"


@pytest.mark.skipif(not REGISTRY.exists(), reason="no registry emitted in this checkout")
def test_every_listed_subject_is_served():
    listed, served = _sets()
    assert listed - served == set(), "listed but not served - the row links to nothing"


@pytest.mark.skipif(not REGISTRY.exists(), reason="no registry emitted in this checkout")
def test_no_served_passport_predates_the_current_schema():
    """A superseded schema left in the served set is a live claim in a retired vocabulary."""
    from src.passport.passport import SCHEMA_VERSION
    stale = {f.name: json.loads(f.read_text())["passport"]["schema_version"]
             for f in sorted(PASSPORTS.glob("*.json"))
             if json.loads(f.read_text())["passport"]["schema_version"] != SCHEMA_VERSION}
    assert stale == {}, f"served under a retired schema: {stale}"
