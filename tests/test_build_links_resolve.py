"""Every internal link under `dist/build/**` resolves to something the build actually emitted.

This is `tests/test_notes_entrance.py::test_the_built_site_has_no_link_that_it_did_not_emit`'s
general check, narrowed to the surface this task ships - and, per this task's own instruction,
proven able to fail before its "the real tree is clean" reading is trusted (CLAUDE.md invariant 5,
"a test MUST BE ABLE TO FAIL"): a planted `/build/no-such/` link is shown turning this exact check
red, on a scratch copy of the real build, before the real tree is read.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "web" / "dist"

# The one real endpoint that carries no emitted file under dist/ (a Cloudflare Pages Function),
# named the same way `tests/test_discovery_maps_agree.py` names it as a real, fetchable resource.
KNOWN_FUNCTION_ROUTES = {"/api/apply"}


def _routes_and_files(dist: Path) -> tuple[set[str], set[str]]:
    routes, files = set(), set()
    for p in dist.rglob("*"):
        if not p.is_file():
            continue
        files.add(p.relative_to(dist).as_posix())
        if p.name == "index.html":
            r = p.parent.relative_to(dist).as_posix()
            routes.add("/" if r == "." else f"/{r}/")
    return routes, files


def _dangling_links_under_build(dist: Path) -> set[tuple[str, str]]:
    routes, files = _routes_and_files(dist)
    build_dir = dist / "build"
    if not build_dir.is_dir():
        return set()
    dangling = set()
    for p in sorted(build_dir.rglob("index.html")):
        r = p.parent.relative_to(dist).as_posix()
        page = "/" if r == "." else f"/{r}/"
        for raw in set(re.findall(r'href="(/[^"]*)"', p.read_text(encoding="utf-8"))):
            href = raw.split("#", 1)[0].split("?", 1)[0]
            if not href:
                continue
            if href in KNOWN_FUNCTION_ROUTES:
                continue
            if href not in routes and href.lstrip("/") not in files:
                dangling.add((page, href))
    return dangling


def test_the_check_catches_a_planted_broken_link(tmp_path):
    """Control before trust: plant a link to an address the build never produced, on a SCRATCH
    copy of the real build (never on `web/dist` itself, which other work may be reading), and show
    the checker used below actually goes red over it."""
    assert DIST.is_dir(), (
        f"{DIST} is absent, so this control has nothing to copy. Run `npm run build` in web/ - "
        "scripts/push.sh does exactly that before the suite."
    )
    scratch = tmp_path / "dist"
    shutil.copytree(DIST, scratch)
    build_index = scratch / "build" / "index.html"
    assert build_index.is_file(), "no dist/build/index.html to plant a link into"

    before = _dangling_links_under_build(scratch)
    assert not before, f"the scratch copy was already dirty before any plant: {before}"

    text = build_index.read_text(encoding="utf-8")
    planted = text.replace(
        "</body>", '<a href="/build/no-such/">nowhere</a></body>', 1
    )
    assert planted != text, "the plant did not change the file - </body> was not found"
    build_index.write_text(planted, encoding="utf-8")

    after = _dangling_links_under_build(scratch)
    assert ("/build/", "/build/no-such/") in after, (
        f"a planted link to an address that does not exist was not caught: {after}"
    )


def test_no_link_under_dist_build_points_at_an_address_the_build_did_not_emit():
    assert DIST.is_dir(), (
        f"{DIST} is absent, so this gate measured nothing. Run `npm run build` in web/ - "
        "scripts/push.sh does exactly that before the suite. A skip here would be a gate present "
        "but not armed."
    )
    dangling = _dangling_links_under_build(DIST)
    assert not dangling, f"dist/build/** links to addresses the build did not produce: {sorted(dangling)}"
