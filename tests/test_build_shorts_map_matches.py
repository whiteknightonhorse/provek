"""T-05 - every emitted `/build/` page carries the video the map names for its OWN url, never a
neighbour's and never an invented one.

WHAT THIS CHECKS, against THREE INDEPENDENT SOURCES for each of the 8 pages (the index and the
seven templates): the video id `web/prerender.mjs` read out of `web/public/data/shorts_map.json`
at build time (the source of truth), the video id embedded in the page's own
`window.__PROVEK__` inline script (what a browser without a second fetch sees), and the video id
served at the machine-readable sibling (`/data/templates.json` for the index,
`/data/templates/<slug>.json` for a template) - the same three-channel discipline
`test_template_copy_is_the_artefact.py` already holds `t.raw` to, applied to a different field.

A page the map has not reached yet (or whose raw entry failed validation) must read `null` on
every channel - never an invented id, and never a stale one left over from an older map.

THE CONTROL RUNS FIRST (CLAUDE.md invariant 5): on a SCRATCH copy of the real build, one
template's inline video id is swapped for a different template's real id, which is exactly the
mix-up the task brief names outright as a failure, whatever caused it - and this is shown turning the check below red
before the real tree is trusted to have none.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "web" / "dist"
SHORTS_MAP = ROOT / "web" / "public" / "data" / "shorts_map.json"
SITE = "https://provek.dev"

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _map_videos() -> dict[str, dict]:
    doc = json.loads(SHORTS_MAP.read_text(encoding="utf-8"))
    return (doc.get("measurement") or {}).get("videos", {})


def _provek_data(html: str) -> dict:
    m = re.search(r"window\.__PROVEK__=(\{.*?\})</script>", html)
    assert m, "no window.__PROVEK__=... inline script found on the page"
    return json.loads(m.group(1))


def _pages(dist: Path) -> dict[str, Path]:
    """route -> index.html path, for the 8 pages this task closes."""
    slugs = sorted(
        p.name for p in (ROOT / "templates").iterdir()
        if p.is_dir() and (p / "SKILL.md").exists()
    )
    pages = {"/build/": dist / "build" / "index.html"}
    for slug in slugs:
        pages[f"/build/{slug}/"] = dist / "build" / slug / "index.html"
    return pages


def _video_ids(dist: Path) -> dict[str, dict]:
    """route -> {source: "..." or None, inline: ..., data_json: ...} for each of the 8 pages."""
    map_videos = _map_videos()
    out: dict[str, dict] = {}
    for route, path in _pages(dist).items():
        assert path.is_file(), f"no page emitted at {path}"
        html = path.read_text(encoding="utf-8")
        provek = _provek_data(html)

        expected = map_videos.get(SITE + route)
        expected_id = expected["video_id"] if expected else None

        if route == "/build/":
            inline_id = (provek.get("buildIndexVideo") or {}).get("videoId")
            data_json = json.loads((dist / "data" / "templates.json").read_text(encoding="utf-8"))
            data_id = (data_json.get("buildIndexVideo") or {}).get("videoId")
        else:
            slug = route.split("/")[2]
            inline_id = (provek["template"].get("video") or {}).get("videoId")
            slug_json = json.loads(
                (dist / "data" / "templates" / f"{slug}.json").read_text(encoding="utf-8")
            )
            data_id = (slug_json["template"].get("video") or {}).get("videoId")

        out[route] = {"map": expected_id, "inline": inline_id, "data_json": data_id}
    return out


def test_the_check_catches_a_swapped_video_id(tmp_path):
    """Control before trust: on a SCRATCH copy of the real build, swap the customer-support
    template's video for a DIFFERENT real video id (never one that just happens to be absent),
    and show the checker below goes red over exactly that page."""
    assert DIST.is_dir(), (
        f"{DIST} is absent, so this control has nothing to copy. Run `npm run build` in web/ - "
        "scripts/push.sh does exactly that before the suite."
    )
    map_videos = _map_videos()
    assert len(map_videos) >= 2, "fewer than two videos in the map - nothing to swap with"

    scratch = tmp_path / "dist"
    shutil.copytree(DIST, scratch)

    before = _video_ids(scratch)
    mismatches_before = {r: v for r, v in before.items() if v["map"] != v["inline"] or v["map"] != v["data_json"]}
    assert not mismatches_before, f"the scratch copy was already dirty before any plant: {mismatches_before}"

    target_route = "/build/customer-support-agent/"
    own_id = map_videos[SITE + target_route]["video_id"]
    other_id = next(v["video_id"] for u, v in map_videos.items() if v["video_id"] != own_id)
    assert other_id != own_id

    page = scratch / "build" / "customer-support-agent" / "index.html"
    text = page.read_text(encoding="utf-8")
    assert text.count(own_id) >= 1, f"the page's own video id {own_id} was not found to swap"
    planted = text.replace(own_id, other_id)
    assert planted != text
    page.write_text(planted, encoding="utf-8")

    after = _video_ids(scratch)
    assert after[target_route]["inline"] == other_id
    mismatches_after = {r: v for r, v in after.items() if v["map"] != v["inline"] or v["map"] != v["data_json"]}
    assert target_route in mismatches_after, "the swapped video id was not caught"
    assert set(mismatches_after) == {target_route}, (
        f"the plant should only affect {target_route}: {mismatches_after}"
    )


def test_every_emitted_page_s_video_matches_the_map_for_its_own_url():
    assert DIST.is_dir(), (
        f"{DIST} is absent, so this gate measured nothing. Run `npm run build` in web/ - "
        "scripts/push.sh does exactly that before the suite."
    )
    ids = _video_ids(DIST)
    mismatches = {r: v for r, v in ids.items() if v["map"] != v["inline"] or v["map"] != v["data_json"]}
    assert not mismatches, f"page video does not match the map for its own url: {mismatches}"


def test_every_video_id_the_map_names_has_the_shape_youtube_actually_uses():
    """Never a guessed id: whatever is published must be exactly what a real YouTube id looks
    like (11 chars, the fixed base64url-ish alphabet), the same shape `web/prerender.mjs`'s own
    `videoFor` filters on before it will publish anything."""
    ids = [v["video_id"] for v in _map_videos().values()]
    assert ids, "no videos in the map to check"
    bad = [i for i in ids if not VIDEO_ID_RE.match(i)]
    assert not bad, f"malformed video ids present in the map: {bad}"
