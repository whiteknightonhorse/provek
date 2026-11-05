"""/feed/pages.json and the article-only markdown copy (T-WB-06, CCH-MEDIUM-01).

The generator is `web/pages_feed.mjs`; these tests run it standalone (no vite/tsc/ssr build) and
judge its OUTPUT: the feed schema, the markdown copy of a note, the style-lint verdict on a
fixture, and that `scripts/style-lint.py` is the sales file byte for byte.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
LINT = ROOT / "scripts" / "style-lint.py"
SALES_LINT = pathlib.Path("/home/sales/sales-app/style/style-lint.py")
SALES_MD5 = "ca241f901511910c7d7a50633bd86750"
KEYS = {"url", "title", "type", "date_published", "date_modified", "words", "medium_eligible"}
NOTE = "/method/notes/not-measured-is-not-zero/"


@pytest.fixture(scope="module")
def out() -> dict:
    r = subprocess.run(["node", str(WEB / "pages_feed.mjs")], capture_output=True, text=True,
                       timeout=120, cwd=WEB)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_feed_rows_have_exactly_the_seven_keys_and_iso_dates(out):
    feed = out["feed"]
    assert feed, "an empty feed would hide a broken loader"
    for row in feed:
        assert set(row) == KEYS
        for k in ("date_published", "date_modified"):
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", row[k])
        assert isinstance(row["words"], int) and not isinstance(row["words"], bool) and row["words"] > 0
        assert isinstance(row["medium_eligible"], bool)
        assert row["type"] in ("learn", "how-to")


def test_feed_is_newest_first_capped_and_holds_only_notes_and_guides(out):
    feed = out["feed"]
    dates = [r["date_published"] for r in feed]
    assert dates == sorted(dates, reverse=True)
    assert len(feed) <= 200
    for row in feed:
        path = row["url"].removeprefix("https://provek.dev")
        assert re.fullmatch(r"/(method/notes|build)/[a-z0-9-]+/", path), row["url"]
        assert row["type"] == ("learn" if path.startswith("/method/notes/") else "how-to")
    assert any(r["type"] == "learn" for r in feed) and any(r["type"] == "how-to" for r in feed)


def test_markdown_copy_of_a_note_is_the_article_body_only(out):
    md = out["markdown"][NOTE]
    lines = md.splitlines()
    assert lines[0].startswith("# ") and not lines[0].startswith("## ")
    for chrome in ("Breadcrumb", "Drafted by", "Where each statement comes from", "Questions",
                   "Published 20", "[Method](", "[Notes](", "{{figure"):
        assert chrome not in md, chrome
    assert re.search(r"^## ", md, re.M)
    assert "](/" not in md, "relative link left in a copy read on another site"


def _verdict(html: str) -> bool:
    script = ("import {styleVerdicts} from './pages_feed.mjs';"
              "process.stdout.write(JSON.stringify(styleVerdicts([process.argv[1]])))")
    r = subprocess.run(["node", "--input-type=module", "-e", script, html],
                       capture_output=True, text=True, timeout=60, cwd=WEB)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)[0]


def test_exclamation_and_three_em_dashes_make_a_paragraph_ineligible():
    bad = "<h1>T</h1><h2>A</h2><p>One — two — three — four. Stop!</p>"
    good = "<h1>T</h1><h2>A</h2><p>The check ran. It read the file.</p>"
    assert _verdict(bad) is False
    assert _verdict(good) is True


def test_style_lint_is_the_sales_file_verbatim():
    assert hashlib.md5(LINT.read_bytes()).hexdigest() == SALES_MD5
    try:
        sales = SALES_LINT.read_bytes()
    except OSError:
        pytest.skip("sales file not readable from this account; pinned md5 checked above")
    assert sales == LINT.read_bytes()


@pytest.mark.skipif(not (WEB / "dist").exists(), reason="site not built in this checkout")
def test_built_article_siblings_and_feed_are_what_the_generator_emits(out):
    """The article-only copies are exempt from the derived-sibling gate, so they are held here:
    each built `index.md` is the generator's bytes, and the built feed is its feed."""
    for route, md in out["markdown"].items():
        built = (WEB / "dist" / route.strip("/") / "index.md").read_text(encoding="utf-8")
        assert built == md, route
    assert json.loads((WEB / "dist" / "feed" / "pages.json").read_text(encoding="utf-8")) == out["feed"]
