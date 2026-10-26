"""LAW-PASSPORT-PAGE-SHOWS-EVIDENCE-CLASS - the passport page says what its author count rests on.

Platform attribution is a claim the commit makes about its author: the address is written by the
committer and GitHub resolves it against the addresses on an account (src/collector/github.py,
`authors_and_bot_commits`). Only a signature binds. A passport page that showed `distinct_authors`
without that sentence, and without the signed share beside it, let a reader take a forgeable count
for a proven one - and the weakness favours the operator's own passports, so it is stated on every
one. Checked over the EMITTED pages (what a reader receives, L-3); skipped, never passed, when the
site is not built.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST_P = ROOT / "web" / "dist" / "p"
PASSPORTS = ROOT / "web" / "public" / "data" / "passports"

pytestmark = pytest.mark.skipif(not DIST_P.exists(), reason="site not built in this checkout")

LINE = re.compile(r"Evidence class: platform-observed .{1,3} identities are GitHub.s attribution of "
                  r"commit addresses, which the subject writes itself; signed commits: ([^<]+?)\.\s*<")


def _text(slug: str) -> str:
    html = (DIST_P / slug / "index.html").read_text(encoding="utf-8")
    return re.sub(r"<!-- -->", "", html)


def _slugs():
    return sorted(p.stem for p in PASSPORTS.glob("*.json") if (DIST_P / p.stem / "index.html").exists())


def test_there_are_passport_pages_to_judge():
    assert _slugs()


@pytest.mark.parametrize("slug", _slugs())
def test_every_passport_page_states_the_evidence_class_and_the_signed_share(slug):
    m = LINE.search(re.sub(r"&mdash;|—", "-", _text(slug)).replace("&#x27;", "'").replace("&rsquo;", "'"))
    assert m, f"{slug}: no evidence-class line on the passport page"
    obs = json.loads((PASSPORTS / f"{slug}.json").read_text(encoding="utf-8"))["passport"]["verified"]["observations"]
    sc = obs.get("signed_commit_share")
    if isinstance(sc, dict) and sc.get("measured"):
        assert m.group(1).strip() == f"{round(sc['value'] * 1000) / 10:g}%", (slug, m.group(1))
    else:
        assert m.group(1).strip() == "not measured", (slug, m.group(1))


def test_the_check_can_fail():
    assert not LINE.search("Evidence class: self-reported <")
