#!/usr/bin/env python3
"""Produces evidence/RED-049-a-swapped-or-invented-video-id-would-have-shipped.txt.

WHAT THIS PROVES (invariant 5: "the section exists" is not a test). T-05 embeds one YouTube short
per `/build/` page, matched to the page by its EXACT url in aipush's map
(`web/public/data/shorts_map.json`). The task's own instruction names the failure mode by name:
"путаница = провал" - one template's video landing on a different template's page. This is the
real-tree counterpart RED-044/045/046/047/048 established as the standard for a new gate: a plant
in the REAL `web/dist`, the real test run as a subprocess against it, the verbatim red output kept,
then the plant removed and the suite proven clean again.

TWO PLANTS, RUN SEQUENTIALLY, EACH RESTORED BEFORE THE NEXT:

  1. SWAPPED: the finance-operations page's own video id is replaced, in its emitted
     `window.__PROVEK__` inline script AND its `/data/templates/<slug>.json` sibling, with a
     DIFFERENT real video id from the map (the market-research page's) - the exact mix-up the task
     forbids.

  2. INVENTED: the customer-support page's own video id is replaced with an 11-character string
     that is shaped like a YouTube id but appears nowhere in the map - the exact thing the task
     forbids under any circumstance ("не выдумывать video_id ни при каких условиях").
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / "RED-049-a-swapped-or-invented-video-id-would-have-shipped.txt"
TEST_NODE = "tests/test_build_shorts_map_matches.py::test_every_emitted_page_s_video_matches_the_map_for_its_own_url"

SHORTS_MAP = ROOT / "web" / "public" / "data" / "shorts_map.json"
SITE = "https://provek.dev"


def run_test() -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_NODE, "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    return p.returncode, (p.stdout + p.stderr).strip()


def plant_and_run(paths: list[Path], find: str, replace: str) -> tuple[int, str, int, str, int, str]:
    originals = [p.read_bytes() for p in paths]
    rc_before, out_before = run_test()
    if rc_before != 0:
        raise RuntimeError(f"REFUSED: {TEST_NODE} is not green before any plant (exit {rc_before}).\n{out_before}")
    try:
        for p, original in zip(paths, originals):
            text = original.decode("utf-8")
            assert find in text, f"REFUSED: {find!r} not found in {p}"
            mutated = text.replace(find, replace)
            p.write_bytes(mutated.encode("utf-8"))
        rc_red, out_red = run_test()
    finally:
        for p, original in zip(paths, originals):
            p.write_bytes(original)
    for p, original in zip(paths, originals):
        if p.read_bytes() != original:
            raise RuntimeError(f"REFUSED: {p} was not restored to its original bytes.")
    if rc_red == 0:
        raise RuntimeError(f"REFUSED: the plant did not turn {TEST_NODE} red (exit {rc_red}).\n{out_red}")
    rc_after, out_after = run_test()
    if rc_after != 0:
        raise RuntimeError(f"REFUSED: {TEST_NODE} is not green again after the plant was removed (exit {rc_after}).\n{out_after}")
    return rc_before, out_before, rc_red, out_red, rc_after, out_after


def main() -> int:
    if not SHORTS_MAP.is_file():
        print(f"REFUSED: {SHORTS_MAP} is absent - run scripts/fetch_shorts_map.py first.")
        return 1
    doc = json.loads(SHORTS_MAP.read_text(encoding="utf-8"))
    videos = (doc.get("measurement") or {}).get("videos", {})
    finance_id = videos.get(f"{SITE}/build/finance-operations-agent/", {}).get("video_id")
    market_id = videos.get(f"{SITE}/build/market-research-agent/", {}).get("video_id")
    support_id = videos.get(f"{SITE}/build/customer-support-agent/", {}).get("video_id")
    if not (finance_id and market_id and support_id):
        print("REFUSED: the map does not carry all three videos this generator plants against - "
              "run scripts/fetch_shorts_map.py again once aipush has published them.")
        return 1
    invented_id = "ZZZZZZZZZZZ"
    assert invented_id not in videos.values(), "REFUSED: the 'invented' id is actually in the map"

    finance_html = ROOT / "web" / "dist" / "build" / "finance-operations-agent" / "index.html"
    finance_json = ROOT / "web" / "dist" / "data" / "templates" / "finance-operations-agent.json"
    support_html = ROOT / "web" / "dist" / "build" / "customer-support-agent" / "index.html"
    support_json = ROOT / "web" / "dist" / "data" / "templates" / "customer-support-agent.json"
    for p in (finance_html, finance_json, support_html, support_json):
        if not p.is_file():
            print(f"REFUSED: {p} is absent - run `npm run build` in web/ first "
                  "(scripts/push.sh does exactly that before this generator would run).")
            return 1

    try:
        b1, o1, r1, ro1, a1, oa1 = plant_and_run(
            [finance_html, finance_json], finance_id, market_id
        )
        b2, o2, r2, ro2, a2, oa2 = plant_and_run(
            [support_html, support_json], support_id, invented_id
        )
    except (RuntimeError, AssertionError) as e:
        print(str(e))
        return 1

    if "finance-operations" not in ro1 and "/build/finance-operations-agent/" not in ro1:
        print(f"REFUSED: the red run for the swap plant does not name the affected page.\n{ro1}")
        return 1
    if "customer-support" not in ro2 and "/build/customer-support-agent/" not in ro2:
        print(f"REFUSED: the red run for the invented-id plant does not name the affected page.\n{ro2}")
        return 1

    body = f"""# RED-049 - a swapped or invented video id would have shipped
#
# {evidence_stamp.tree_stamp()}
#
# Produced by evidence/RED-049-generator.py, checked in beside this file so the two runs below can
# be repeated rather than believed. T-05: one video per /build/ page, matched by the page's own
# exact url in web/public/data/shorts_map.json - never a neighbour's video, never an invented id.
#
# SUBJECT: {TEST_NODE}.

{"=" * 100}
PLANT 1 - SWAPPED: the finance-operations page's own video id ({finance_id}) replaced with the
market-research page's real id ({market_id}) - the "путаница" the task brief forbids by name.
{"=" * 100}

--- before the plant, exit {b1} ---
{o1}

--- with the plant in place, exit {r1} ---
{ro1}

--- after the plant was removed, exit {a1} ---
{oa1}

{"=" * 100}
PLANT 2 - INVENTED: the customer-support page's own video id ({support_id}) replaced with
{invented_id!r}, a string shaped like a YouTube id that appears nowhere in the map - forbidden
under any circumstance by the task brief.
{"=" * 100}

--- before the plant, exit {b2} ---
{o2}

--- with the plant in place, exit {r2} ---
{ro2}

--- after the plant was removed, exit {a2} ---
{oa2}
"""
    OUT.write_text(body, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
