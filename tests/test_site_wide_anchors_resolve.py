"""T-78 (Fable ruling, 78-texts-for-the-incubator-funnel.ruling-1.md): a site-wide anchor check,
ordered because the copy pass this task makes touches pages that other pages point at by fragment
- `/method/#the-order-link` above all, linked from Landing, Apply, Registry and Phase2 - and
nothing in the suite before this checked that a `#fragment` a page links to actually names an
element the TARGET page emits.

WHY THIS IS A DIFFERENT CHECK FROM `test_build_links_resolve.py` AND
`test_notes_entrance.py::test_the_built_site_has_no_link_that_it_did_not_emit`. Both of those
strip the fragment before comparing (`raw.split("#", 1)[0]`) - by design, because their job is
route existence, and a route either exists or it does not regardless of what follows `#`. That
means a link to `/method/#no-such-anchor` reads as identical to `/method/#the-order-link` to
either of them: both resolve to the real route `/method/` and neither goes red. This file checks
the half neither of them was built to check: that the fragment itself is a real `id` on the page
it points at - same-page (`href="#main"`) or cross-page (`href="/method/#the-order-link"`).

WHAT COUNTS AS A TARGET PAGE. A bare `#frag` names the page the link lives ON; a `/path/#frag`
names `/path/`. Both are resolved against the SAME map of `route -> {ids on that page}`, built
once from every emitted `index.html` and `404.html`, so a page cannot accidentally be graded
against its own out-of-date copy of somebody else's anchors.

THE CONTROL RUNS FIRST (CLAUDE.md invariant 5: a test that cannot fail is not a test). It removes
a real anchor from a scratch copy of the real build and shows the checker below goes red over
exactly the link that anchor used to satisfy - proving the check can catch the planted defect
before the real tree is trusted to have none.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "web" / "dist"

ID_RE = re.compile(r'\bid="([^"]+)"')
HREF_FRAG_RE = re.compile(r'href="([^"]*#[^"]+)"')


def _route_of(p: Path, dist: Path) -> str:
    if p.name == "404.html":
        return "/404.html"
    r = p.parent.relative_to(dist).as_posix()
    return "/" if r == "." else f"/{r}/"


def _pages(dist: Path) -> list[Path]:
    return sorted([*dist.rglob("index.html"), *dist.glob("404.html")])


def _anchor_map(dist: Path) -> dict[str, set[str]]:
    """route -> the set of ids that page actually emits."""
    ids: dict[str, set[str]] = {}
    for p in _pages(dist):
        ids[_route_of(p, dist)] = set(ID_RE.findall(p.read_text(encoding="utf-8")))
    return ids


def _dangling_fragment_links(dist: Path) -> set[tuple[str, str]]:
    """(page, href) for every `#fragment` link whose target page does not carry that id."""
    ids = _anchor_map(dist)
    dangling: set[tuple[str, str]] = set()
    for p in _pages(dist):
        page = _route_of(p, dist)
        for href in set(HREF_FRAG_RE.findall(p.read_text(encoding="utf-8"))):
            path, frag = href.split("#", 1)
            if not frag:
                continue  # a trailing bare "#" names no element
            target = path if path else page
            target_ids = ids.get(target)
            if target_ids is None:
                # An unresolved PATH is a different defect, already caught by
                # test_build_links_resolve.py / test_notes_entrance.py - not re-litigated here.
                continue
            if frag not in target_ids:
                dangling.add((page, href))
    return dangling


def test_the_check_catches_a_removed_anchor(tmp_path):
    """Control before trust: on a SCRATCH copy of the real build (never `web/dist` itself), delete
    the real `id="the-order-link"` from `/method/` and show the checker goes red over every page
    that links to it by fragment - which, today, is more than one."""
    assert DIST.is_dir(), (
        f"{DIST} is absent, so this control has nothing to copy. Run `npm run build` in web/ - "
        "scripts/push.sh does exactly that before the suite."
    )
    scratch = tmp_path / "dist"
    shutil.copytree(DIST, scratch)

    before = _dangling_fragment_links(scratch)
    assert not before, f"the scratch copy was already dirty before any plant: {before}"

    method_index = scratch / "method" / "index.html"
    assert method_index.is_file(), "no dist/method/index.html to plant the removal into"
    text = method_index.read_text(encoding="utf-8")
    planted = text.replace('id="the-order-link"', 'id="the-order-link-renamed"', 1)
    assert planted != text, 'the plant did not change the file - id="the-order-link" was not found'
    method_index.write_text(planted, encoding="utf-8")

    after = _dangling_fragment_links(scratch)
    assert after, "removing the real anchor produced no dangling link at all - the checker is not armed"
    assert all(href.endswith("#the-order-link") for _page, href in after), (
        f"the plant should only break links ending in #the-order-link: {after}"
    )


def test_no_fragment_link_anywhere_points_at_an_anchor_the_target_page_does_not_emit():
    assert DIST.is_dir(), (
        f"{DIST} is absent, so this gate measured nothing. Run `npm run build` in web/ - "
        "scripts/push.sh does exactly that before the suite. A skip here would be a gate present "
        "but not armed."
    )
    dangling = _dangling_fragment_links(DIST)
    assert not dangling, f"site-wide, these #fragment links resolve to no id on their target page: {sorted(dangling)}"
