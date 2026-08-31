"""ABI-2-3, restated for the badge specifically (see the header of `web/functions/badge/[id].js`):
a level is assigned to an operation, never to a company, and a badge is the most viral artefact
this project makes. This asserts the negative directly, over every status this file can render and
over a fixture drawn from the actual data on disk, plus a static-source floor so the guarantee does
not depend only on today's fixtures.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "badge_probe.mjs"
REAL_DATA_PROBE = ROOT / "tests" / "badge_real_data_probe.mjs"
FUNCTION = ROOT / "web" / "functions" / "badge" / "[id].js"
PASSPORTS = ROOT / "web" / "public" / "data" / "passports"

# A bare ladder level, standing alone rather than beside its operation name. `L3` inside a longer
# token (a hex fragment, a file path) is not this defect; a level word-bounded on both sides is.
BARE_LEVEL = re.compile(r"(?<![A-Za-z0-9_])L[0-5](?![A-Za-z0-9_])")


def run(scenario: str) -> dict:
    done = subprocess.run(["node", str(PROBE), scenario],
                           cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stdout + done.stderr
    return json.loads(done.stdout)


SCENARIOS = [
    "verified_with_projection",
    "verified_lapsed_shows_stale",
    "unverified_no_projection",
    "suspended",
    "unknown_slug",
]


def test_no_scenario_prints_a_bare_ladder_level():
    for name in SCENARIOS:
        body = run(name)["body"]
        assert not BARE_LEVEL.search(body), f"{name}: badge printed a bare level: {body}"


def test_projection_never_appears_without_its_own_name_beside_it():
    """The number and the word "projection" are never separable - a reader with the SVG's text
    but not its layout (a screen reader, a text extraction) still gets the label."""
    for name in ("verified_with_projection", "unverified_no_projection"):
        body = run(name)["body"]
        for m in re.finditer(r"\b\d{1,3}/100\b", body):
            start = max(0, m.start() - 20)
            assert "projection" in body[start:m.start()], (
                f"{name}: a /100 figure appeared without the word 'projection' immediately before it")


def test_the_source_never_reads_a_bare_operation_level_as_the_headline():
    """A floor under the fixtures above: the handler must not even HOLD a code path that reads
    `p.verified.operations[...].level` as the thing it prints as the subject's own status. Only
    `p.status` (via `effectiveStatus`) and `p.verified.projection` may reach the template."""
    src = FUNCTION.read_text(encoding="utf-8")
    assert "operations" not in src, (
        "the badge source touches per-operation data at all - it must only ever read "
        "p.status and p.verified.projection"
    )


def test_at_least_one_real_passport_on_disk_has_a_measured_level_and_still_prints_clean():
    """The most direct falsification: run the badge over a subject whose passport actually
    carries an `L`-prefixed level (not just a synthetic fixture), and check the SVG anyway."""
    measured = [
        f for f in sorted(PASSPORTS.glob("*.json"))
        if re.search(r'"level":\s*"L[0-5]"', f.read_text(encoding="utf-8"))
    ]
    assert measured, "no passport on disk carries a measured L0-L5 level - nothing to check against"
    slug = measured[0].stem
    proc = subprocess.run(["node", str(REAL_DATA_PROBE), str(measured[0]), slug],
                           cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not BARE_LEVEL.search(proc.stdout), (
        f"badge for a real passport with a measured level leaked it: {proc.stdout}")
