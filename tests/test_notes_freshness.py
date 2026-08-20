"""LAW-NOTES-FRESHNESS - `dateModified` moves when the text moves, and at no other time.

PRODUCT.md holds that historical passports are never silently recomputed. Published prose had no
equivalent, and prose is easier to change quietly than a passport: a rebuild would have stamped
today's date on three unchanged notes and told every crawler they were revised. A freshness signal
that fires on rebuilds is not a freshness signal, and the surface would be making a claim - *this
was revised* - with nothing behind it. That is the shape of D-15, in miniature and automated.

So the manifest pins each note's body by hash, `dateModified` is read from the manifest rather than
from the clock, and this module refuses to let the two drift apart.
"""
from __future__ import annotations

import hashlib
import re

import pytest

from .notes_support import DIST, emitted, ld_blocks, manifest, sources

pytestmark = pytest.mark.skipif(not sources(), reason="no method notes captured in this checkout")


def test_every_note_is_pinned_by_the_hash_of_the_text_that_was_captured():
    m = manifest()
    for front, body in sources():
        entry = m.get(front["slug"])
        assert entry, f"{front['slug']}: not in web/notes/manifest.json"
        got = hashlib.sha256(body.encode()).hexdigest()
        assert entry["body_sha256"] == got, (
            f"{front['slug']}: the text has changed since it was captured, but the manifest still "
            f"pins the old hash - so dateModified would be reporting a revision that is not this one")


def test_the_manifest_holds_nothing_that_is_not_a_note():
    slugs = {front["slug"] for front, _ in sources()}
    for slug in manifest():
        assert slug in slugs, f"manifest pins {slug}, which no longer exists as a note"


def test_a_revision_date_is_never_earlier_than_a_publication_date():
    for slug, entry in manifest().items():
        assert entry["date_modified"] >= entry["date_published"], slug


def test_the_emitted_page_and_the_sitemap_both_take_the_date_from_the_manifest():
    pages = emitted()
    if not pages:
        pytest.skip("site not built in this checkout")
    m = manifest()
    sitemap = (DIST / "sitemap.xml").read_text(encoding="utf-8")
    for front, _ in sources():
        entry = m[front["slug"]]
        art = next(b for b in ld_blocks(pages[front["slug"]]) if b["@type"] == "Article")
        assert art["dateModified"] == entry["date_modified"], front["slug"]
        assert art["datePublished"] == entry["date_published"], front["slug"]
        loc = f"https://provek.dev/method/notes/{front['slug']}/"
        block = re.search(rf"<url>\s*<loc>{re.escape(loc)}</loc>\s*<lastmod>([^<]+)</lastmod>", sitemap)
        assert block, f"{front['slug']}: absent from the sitemap - Bing is the channel this is for"
        assert block.group(1) == entry["date_modified"], (
            f"{front['slug']}: sitemap lastmod {block.group(1)} is not the manifest's "
            f"{entry['date_modified']} - a build clock has leaked into a freshness claim")
