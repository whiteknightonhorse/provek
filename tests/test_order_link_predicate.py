"""Phase 2's mandatory control (specification 4.2-bis point 3): a synthetic registry proves the
"Order" link's predicate on BOTH sides, and a deliberately broken predicate is proven to be
CAUGHT rather than merely trusted.

WHY THIS RENDERS THE REAL COMPONENT RATHER THAN REIMPLEMENTING THE PREDICATE IN PYTHON. The
predicate (`orderLinkUrl` in `web/src/types.ts`) is TypeScript, and no runtime in this pipeline
executes TypeScript directly (`tests/test_the_staleness_rule_is_one_rule.py` accepts the weaker
regex check for exactly this reason, on the SAME function's sibling `effectiveStatus`). But this
project's own SSR build already exports `renderRoute` from `web/src/entry-server.tsx` - the exact
function `web/prerender.mjs` calls to build every live page - so this file imports the REAL,
ALREADY-COMPILED bundle (`web/dist-ssr/entry-server.js`) and renders `/registry/` against
synthetic data via a small Node subprocess. This is not a reimplementation: it is the shipped code,
running.

FOUR SYNTHETIC ROWS, one per branch the predicate has to get right:
  a: verified, but the passport LAPSED (stale)        -> no link, "passport expired"
  b: never verified at all (unverified)               -> no link, "not verified"
  c: verified and declared, but NOT reachable          -> no link, "order channel not reachable"
  d: verified, declared, reachable                     -> THE link, and only this one

THE MANDATORY MUTATION. `test_MANDATORY_CONTROL_a_broken_predicate_would_be_CAUGHT` rewrites
`orderLinkUrl` for the duration of one test to return the declared URL unconditionally, rebuilds
the SSR bundle from the mutated source, and asserts all three previously-ineligible rows above now
carry a link - proving the two tests above are not vacuously green. Both the source file and the
built bundle are restored to their exact original bytes in `finally`.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
ENTRY = WEB / "dist-ssr" / "entry-server.js"
TYPES_TS = WEB / "src" / "types.ts"

_SKIP_REASON = (
    "web/dist-ssr/entry-server.js is a build artefact this file does not create - run "
    "`npm run build` in web/ first (scripts/push.sh's own step 6 always does, before step 7 runs "
    "this suite, so the door never sees this skip)"
)


def _row(subject_id: str, status: str, valid_until: str, service_url: str | None,
        service_reachable: bool | None, *, projection=60, absent=None) -> dict:
    return {
        "subject_id": subject_id, "status": status, "projection": projection,
        "projection_absent_reason": absent, "protocol_version": "1.1.0",
        "valid_until": valid_until, "passport_ref": "x", "verifier_affiliation": "independent",
        "service_url": service_url, "service_reachable": service_reachable,
    }


STALE_URL = "https://a.example/order"
UNVERIFIED_URL = "https://b.example/order"
UNREACHABLE_URL = "https://c.example/order"
ELIGIBLE_URL = "https://d.example/order"
INELIGIBLE_URLS = (STALE_URL, UNVERIFIED_URL, UNREACHABLE_URL)

SYNTHETIC_REGISTRY = {
    "generated_at": "2026-09-02T00:00:00+00:00",
    "disclaimer": "test fixture - never served",
    "count": 4,
    "subjects": [
        _row("git:a/stale", "verified", "2020-01-01T00:00:00+00:00", STALE_URL, True),
        _row("git:b/unverified", "unverified", "2099-01-01T00:00:00+00:00", UNVERIFIED_URL, True,
             projection=None, absent="check_did_not_run"),
        _row("git:c/unreachable", "verified", "2099-01-01T00:00:00+00:00", UNREACHABLE_URL, False),
        _row("git:d/eligible", "verified", "2099-01-01T00:00:00+00:00", ELIGIBLE_URL, True),
    ],
}


def _render_registry(entry_path: Path) -> str:
    """Renders `/registry/` via the REAL `renderRoute` export - an absolute import specifier,
    since a relative one resolves against the throwaway script file, not the process cwd."""
    script = (
        f"import {{ renderRoute }} from {json.dumps(entry_path.as_posix())};\n"
        f"const reg = {json.dumps(SYNTHETIC_REGISTRY)};\n"
        f'process.stdout.write(renderRoute("/registry/", reg, null));\n'
    )
    p = subprocess.run(["node", "--input-type=module"], input=script, capture_output=True,
                       text=True, cwd=WEB, timeout=60)
    assert p.returncode == 0, p.stderr
    return p.stdout


@pytest.mark.skipif(not ENTRY.exists(), reason=_SKIP_REASON)
def test_stale_unverified_and_unreachable_rows_carry_no_order_link():
    html = _render_registry(ENTRY)
    for url in INELIGIBLE_URLS:
        assert url not in html, f"{url} must not be linked - its row fails the predicate"
    assert "passport expired" in html
    assert "not verified" in html
    assert "order channel not reachable" in html


@pytest.mark.skipif(not ENTRY.exists(), reason=_SKIP_REASON)
def test_verified_declared_reachable_row_DOES_carry_the_order_link():
    html = _render_registry(ENTRY)
    assert ELIGIBLE_URL in html
    assert 'rel="noopener noreferrer nofollow"' in html
    assert 'target="_blank"' in html


@pytest.mark.skipif(not ENTRY.exists(), reason=_SKIP_REASON)
def test_MANDATORY_CONTROL_a_broken_predicate_would_be_CAUGHT():
    original_ts = TYPES_TS.read_text(encoding="utf-8")
    original_bundle = ENTRY.read_bytes()
    marker = "export function orderLinkUrl("
    assert marker in original_ts, "orderLinkUrl moved or was renamed - update this test's marker"
    start = original_ts.index(marker)
    end = original_ts.index("\n}", start) + len("\n}")
    mutated_fn = (
        "export function orderLinkUrl(\n"
        "  status: string,\n"
        "  validUntil: string,\n"
        "  serviceUrl: string | null,\n"
        "  serviceReachable: boolean | null,\n"
        "  now: Date = new Date(),\n"
        "): string | null {\n"
        "  return serviceUrl;   // THE DEFECT: status and reachability are ignored entirely\n"
        "}"
    )
    mutated_ts = original_ts[:start] + mutated_fn + original_ts[end:]
    assert mutated_ts != original_ts
    try:
        TYPES_TS.write_text(mutated_ts, encoding="utf-8")
        built = subprocess.run(["npm", "run", "build:ssr"], cwd=WEB, capture_output=True,
                               text=True, timeout=120)
        assert built.returncode == 0, built.stdout + built.stderr
        html = _render_registry(ENTRY)
        # THE MANDATORY ASSERTION: with the predicate broken, ALL THREE previously-ineligible rows
        # now carry a link - proving the two tests above are not vacuously green.
        for url in INELIGIBLE_URLS:
            assert url in html, (
                f"the mutant predicate should have linked {url} too - if it did not, this "
                "control is not exercising the mutation it claims to"
            )
    finally:
        TYPES_TS.write_text(original_ts, encoding="utf-8")
        ENTRY.write_bytes(original_bundle)
