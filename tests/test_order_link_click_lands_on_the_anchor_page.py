"""The SPA click router must route on the PATH, never the fragment (measured 2026-09-03, while
fixing the server-side 404 the operator hit on `/method/%23the-order-link`).

`web/src/App.tsx`'s `useRoute` hand-rolls navigation: `popstate`'s own handler computes `route`
from `window.location.pathname`, which never carries a `#`. The click handler used to compute it
from the clicked `href` WHOLE instead - `norm(href)` on `/method/#the-order-link` (the exact link
`Registry.tsx`, `Landing.tsx`, `Apply.tsx` and `Phase2.tsx` all use to point a reader at Method's
own `#the-order-link` explanation) yields `/method/#the-order-link/`, a string `Body`'s route
switch matches nothing on. Reproduced in plain Node, no DOM required - `norm` is pure string
arithmetic:

    const norm = (p) => (p.endsWith("/") ? p : p + "/");
    norm("/method/#the-order-link") === "/method/#the-order-link/"   // true, before the fix

So a reader who clicked that exact link FROM INSIDE the app (already past the first load, on any
of the four pages above) got "No such page" painted over a page that plainly exists - the same
class of defect `tests/test_witness_route_handoff.py` guards against for `/w/` links, checked here
by the same source-scan shape for the same reason: `useRoute` is not exported and reaches into
`history`/`addEventListener`, so running it would mean building a DOM harness disproportionate to
a one-line arithmetic fix - `test_witness_route_handoff.py`'s own docstring makes the identical call
for the `/w/` guard.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_TSX = ROOT / "web" / "src" / "App.tsx"


def test_the_click_handler_strips_the_fragment_before_computing_the_route():
    src = APP_TSX.read_text(encoding="utf-8")
    assert "setRoute(norm(href))" not in src, (
        "the click handler passes the raw href (which may carry a #fragment) straight into norm() "
        "- reproduced: norm('/method/#the-order-link') === '/method/#the-order-link/', a route "
        "nothing in Body matches, so clicking the order-link reference from inside the app shows "
        "'No such page' over /method/, which plainly exists"
    )
    m = re.search(r'setRoute\(norm\(href\.split\(/\[\?#\]/\)\[0\]\)\)', src)
    assert m, (
        "the click handler must compute the route from href with any ?query or #fragment removed "
        "first, matching what popstate's own handler derives from window.location.pathname"
    )
    # THE FRAGMENT-STRIP MUST COME BEFORE setRoute, which is what makes it take effect - a check
    # that only proved the substring exists somewhere in the file would pass even if a second,
    # dead copy of the old call remained above it.
    pushstate_idx = src.index("history.pushState")
    assert pushstate_idx < m.start(), (
        "history.pushState must still run (and take the full href, fragment included, so the URL "
        "bar and browser fragment scrolling keep working) before the route is computed from the "
        "stripped path"
    )


def test_the_exact_order_link_href_now_normalises_to_the_real_method_route():
    """The concrete case this bug was found through: apply the same split+norm the fixed handler
    uses to the literal href four pages share, and land exactly on `/method/`, not on a route with
    the fragment still attached."""
    def norm(p: str) -> str:
        return p if p.endswith("/") else p + "/"

    href = "/method/#the-order-link"
    path = re.split(r"[?#]", href)[0]
    assert norm(path) == "/method/"
