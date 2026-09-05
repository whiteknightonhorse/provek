#!/usr/bin/env python3
"""Produces evidence/RED-043-a-copy-payload-that-diverged-only-in-a-machine-channel-would-have-shipped.txt.

WHAT THIS PROVES (invariant 5: "the section exists" is not a test). T-74 Ф4 review (ruling
`74-ai-agent-templates-phase4-final-walk.ruling-1.md`, section 2.1-2.3) found that
`tests/test_template_copy_is_the_artefact.py` armed LAW-COPY-IS-THE-ARTEFACT for exactly two
channels - a template page's own `<pre>` and its raw sibling `dist/build/<slug>/SKILL.md` - and
missed three others that carry the identical `Template.raw` string: the `/build/` index card's own
Copy button (`web/src/pages/Build.tsx` `TemplateCard`, which reads `t.raw` off
`window.__PROVEK__.templates[]` embedded on `/build/`'s own page, never off a `<pre>`), and the two
machine-fetchable siblings `dist/data/templates.json` and `dist/data/templates/<slug>.json`
(SPEC 3.7 item 6). Today all five channels agree because they are emitted from the same in-memory
object in `web/prerender.mjs` - but until the test above was extended, nothing had ever measured
that agreement, and until this file existed nothing had proved the extended test can actually catch
a real divergence between them. RED-042's precedent applies again: a gate that has never gone red
is a claim, not a measurement.

ONE MUTATION, IN THE ACTUAL BUILT ARTEFACT. This generator builds nothing and plants nothing under
`templates/` (the source is not the surface under test here); it flips one template's `raw` field
inside the already-built `web/dist/data/templates.json` - a machine channel a coding agent may
legitimately fetch instead of the rendered page - runs the extended test, and requires the failure
to name exactly that channel and that slug, and only that mismatch key. The original bytes are
restored in a `finally`, and the run refuses to write an artefact unless the suite is provably green
both before the plant and after its removal.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / "RED-043-a-copy-payload-that-diverged-only-in-a-machine-channel-would-have-shipped.txt"
TEST_FILE = "tests/test_template_copy_is_the_artefact.py"
TEMPLATES_JSON = ROOT / "web" / "dist" / "data" / "templates.json"


def run_tests() -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_FILE, "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    return p.returncode, (p.stdout + p.stderr).strip()


def main() -> int:
    if not TEMPLATES_JSON.is_file():
        print(f"REFUSED: {TEMPLATES_JSON} is absent - run `npm run build` in web/ first "
              "(scripts/push.sh does exactly that before this generator would run).")
        return 1

    original = TEMPLATES_JSON.read_bytes()

    rc_before, out_before = run_tests()
    if rc_before != 0:
        print(f"REFUSED: {TEST_FILE} is not green before any plant (exit {rc_before}).\n{out_before}")
        return 1

    data = json.loads(original.decode("utf-8"))
    templates = data["templates"]
    if not templates:
        print("REFUSED: dist/data/templates.json carries zero templates - nothing to mutate.")
        return 1
    plant_slug = templates[0]["slug"]

    try:
        templates[0]["raw"] = templates[0]["raw"] + "\n"
        mutated = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if mutated == original:
            print("REFUSED: the mutation did not change the file - fixture is vacuous.")
            return 1
        TEMPLATES_JSON.write_bytes(mutated)

        rc_red, out_red = run_tests()
    finally:
        TEMPLATES_JSON.write_bytes(original)

    if TEMPLATES_JSON.read_bytes() != original:
        print(f"REFUSED: {TEMPLATES_JSON} was not restored to its original bytes.")
        return 1
    if rc_red == 0:
        print(f"REFUSED: planting the mutation did not turn the suite red (exit {rc_red}).\n{out_red}")
        return 1
    if "test_every_emitted_template_s_copy_payload_matches_its_source" not in out_red:
        print(f"REFUSED: the red run does not name the extended copy-payload test.\n{out_red}")
        return 1
    if plant_slug not in out_red:
        print(f"REFUSED: the red run does not name the mutated slug {plant_slug!r}.\n{out_red}")
        return 1
    if "data_templates_json" not in out_red:
        print(f"REFUSED: the red run does not name the mutated channel (data_templates_json).\n{out_red}")
        return 1

    rc_after, out_after = run_tests()
    if rc_after != 0:
        print(f"REFUSED: the suite is not green again after the plant was removed (exit {rc_after}).\n{out_after}")
        return 1

    body = f"""# RED-043 - a copy payload that diverged only in a machine channel would have shipped
#
# {evidence_stamp.tree_stamp()}
#
# Produced by evidence/RED-043-generator.py, checked in beside this file so the run below can be
# repeated rather than believed. Closes the gap T-74 Ф4 review found: LAW-COPY-IS-THE-ARTEFACT's
# test armed a template page's own `<pre>` and its raw sibling, and never measured the `/build/`
# index card's Copy button (which reads `window.__PROVEK__.templates[].raw`, never a `<pre>`) or
# the two machine-fetchable JSON siblings a coding agent may fetch instead of the rendered page.
# One byte appended to `dist/data/templates.json`'s first template's `raw` field - a mutation the
# old two-channel test would have missed entirely, because it never opened this file - now turns
# the extended test red, naming the mutated slug and the mutated channel.
#
# SUBJECT: {TEST_FILE}, arming LAW-COPY-IS-THE-ARTEFACT (SPEC 3.7 item 7, ADR-0011 section 6.1).
# CHANNEL PLANTED: web/dist/data/templates.json, template {plant_slug!r}.

{"=" * 100}
BEFORE THE PLANT - `python3 -m pytest {TEST_FILE} -q`, exit {rc_before}
{"=" * 100}

{out_before}

{"=" * 100}
THE PLANT - one byte appended to templates[0].raw ({plant_slug!r}) in dist/data/templates.json,
restored from the original bytes in a `finally` regardless of outcome
{"=" * 100}

{"=" * 100}
WITH THE PLANT IN PLACE - `python3 -m pytest {TEST_FILE} -q`, exit {rc_red}
{"=" * 100}

{out_red}

{"=" * 100}
AFTER THE PLANT WAS REMOVED - `python3 -m pytest {TEST_FILE} -q`, exit {rc_after}
{"=" * 100}

{out_after}
"""
    OUT.write_text(body, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
