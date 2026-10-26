"""T-0567: the registry header says every row is the operator's own, and says it only while that
is true. The sentence is rendered from the data (`noIndependentSubjectYet` in `web/src/types.ts`),
so the first independent row removes it without anyone editing a page.

Two checks: the built page with today's data (sentence present), and the REAL SSR bundle rendered
over a mixed fixture (sentence absent) and an all-affiliated fixture (present). Skipped without the
build artefacts, as `tests/test_order_link_predicate.py` is; `scripts/push.sh` builds first.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
ENTRY = WEB / "dist-ssr" / "entry-server.js"
PAGE = WEB / "dist" / "registry" / "index.html"
SENTENCE = "No independent applicant has been published yet"


def _row(subject_id: str, affiliation: str) -> dict:
    return {
        "subject_id": subject_id, "status": "unverified", "projection": None,
        "projection_absent_reason": "unreadable", "protocol_version": "1.1.0",
        "valid_until": "2099-01-01T00:00:00+00:00", "passport_ref": "x",
        "verifier_affiliation": affiliation, "service_url": None, "service_reachable": None,
    }


def _render(rows: list[dict]) -> str:
    reg = {"generated_at": "2026-10-26T00:00:00+00:00", "disclaimer": "fixture", "count": len(rows),
           "subjects": rows}
    script = (
        f"import {{ renderRoute }} from {json.dumps(ENTRY.as_posix())};\n"
        f"process.stdout.write(renderRoute('/registry/', {json.dumps(reg)}, null));\n"
    )
    p = subprocess.run(["node", "--input-type=module"], input=script, capture_output=True,
                       text=True, cwd=WEB, timeout=60)
    assert p.returncode == 0, p.stderr
    return " ".join(p.stdout.replace("&#x27;", "'").split())


@pytest.mark.skipif(not PAGE.exists(), reason="web/dist not built")
def test_the_built_registry_says_it_while_every_row_is_the_operators():
    reg = json.loads((WEB / "public" / "data" / "registry.json").read_text(encoding="utf-8"))
    assert all(s["verifier_affiliation"] == "same_owner" for s in reg["subjects"]), (
        "an independent row exists: this sentence must be gone from the page, update this test")
    assert SENTENCE in " ".join(PAGE.read_text(encoding="utf-8").split())


@pytest.mark.skipif(not ENTRY.exists(), reason="web/dist-ssr not built")
def test_a_mixed_registry_does_not_carry_the_sentence():
    html = _render([_row("git:a/one", "same_owner"), _row("git:b/two", "independent")])
    assert SENTENCE not in html


@pytest.mark.skipif(not ENTRY.exists(), reason="web/dist-ssr not built")
def test_an_all_affiliated_registry_carries_it_and_an_empty_one_does_not():
    assert SENTENCE in _render([_row("git:a/one", "same_owner"), _row("git:a/two", "same_owner")])
    assert SENTENCE not in _render([])
