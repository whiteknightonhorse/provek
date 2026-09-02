"""`/w/<id>/` pages (spec 4.2-bis point 4, D-50) are static documents emitted by `web/prerender.mjs`
outside the component set `App.tsx`'s `Body` renders - the identical shape `/method/notes/` already
has. Same defect class as `tests/test_notes_entrance.py` guards for that prefix: a click on a link
into an un-registered route, intercepted by the SPA router, paints "No such page" over a document
that the server serves perfectly well. Checked here for the `/w/` prefix specifically, since that
test's own `ENTRANCE` constant is notes-only and does not generalise automatically.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_TSX = ROOT / "web" / "src" / "App.tsx"


def test_the_router_hands_w_links_to_the_server_instead_of_intercepting_them():
    src = APP_TSX.read_text(encoding="utf-8")
    m = re.search(r'if\s*\(href\.startsWith\("/w/"\)\)\s*return;', src)
    assert m, (
        "App.tsx's click handler must hand off /w/ links to a normal navigation - the same "
        "construction it already uses for /method/notes/ - or a click on a passport's "
        "task-history link renders 'No such page' over a real document")
    # THE HAND-OFF MUST COME BEFORE THE PUSHSTATE, not after - a guard placed after
    # `history.pushState` would already have taken over the URL bar before refusing to render it.
    pushstate_idx = src.index("history.pushState")
    assert m.start() < pushstate_idx, "/w/ hand-off must precede history.pushState in the handler"
