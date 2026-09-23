"""T-SG-14 (`~/taskloop/briefs/SG-00-ruling-1.md` §SG-14; incubator's own decision, `DECISIONS.md`
D-61). `ShareActions` in `web/src/pages/Passport.tsx` gained two artefacts beyond the existing
"copy link" / "copy badge code" pair:

  - a "no score" badge snippet, the same `<img>` shape as the existing one but pointed at
    `?plain=1` on the SAME `web/functions/badge/[id].js` Function (checked at the handler level by
    `tests/test_badge_plain_variant_drops_the_number.py`, against the real endpoint under Node -
    this file only checks that the passport page's button actually asks for that query string);
  - a plain-text "Verified by Provek" snippet, which - unlike either badge - is copied once and
    then sits wherever it was pasted with no further contact with this site, so it has to stay
    honest on its own: always carrying the expiry date, and offered only while the subject can
    honestly be described as "Verified by Provek" in the present tense.

No component test runner exists in this repository (`web/package.json` carries no jsdom/vitest);
`tests/test_stale_on_the_surface.py` already establishes source-scan-over-`Passport.tsx` as this
project's way of checking page logic without one, and this file follows the same shape.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PASSPORT = ROOT / "web" / "src" / "pages" / "Passport.tsx"


def src() -> str:
    return PASSPORT.read_text(encoding="utf-8")


def test_the_no_score_badge_snippet_points_at_the_plain_query_flag():
    s = src()
    assert "?plain=1" in s, "the no-score badge button does not point at the badge Function's plain variant"
    assert "plainBadgeUrl" in s and "badgeUrl}?plain=1" in s.replace(" ", ""), (
        "the plain badge URL is not built from the same badgeUrl as the numbered one - "
        "two independently-typed URLs for one subject can drift"
    )


def test_the_verified_by_provek_snippet_always_carries_the_expiry_date():
    """SG-14's own words, verbatim: "Provek passport · autonomy verified · valid until <date>".
    The date is what makes a snippet copied once, with no further contact with this site, stay
    honest forever - a reader can check it against today, unlike a bare "Verified"."""
    s = src()
    m = re.search(r'verifiedByProvekSnippet\s*=\s*\n?\s*`([^`]*)`', s)
    assert m, "verifiedByProvekSnippet template literal not found"
    snippet_src = m.group(1)
    assert "validUntil" in snippet_src, "the snippet does not interpolate the passport's valid_until"
    assert "Verified by Provek" in snippet_src


def test_the_verified_by_provek_button_is_gated_to_the_verified_status_only():
    """A subject that is stale, suspended, unverified or in_progress may not hand out text
    claiming "Verified by Provek" in the present tense - that claim belongs to the two badges,
    which recompute their own word (`effectiveStatus`) on every load instead of being copied once
    and left to go stale silently."""
    s = src()
    assert "canClaimVerified = status ===" in s.replace('"verified"', '"verified"'), (
        "no status === \"verified\" gate found ahead of the Verified-by-Provek button"
    )
    assert re.search(r"canClaimVerified\s*&&", s), (
        "the Verified-by-Provek CopyButton is not conditioned on canClaimVerified"
    )


def test_share_actions_is_called_with_the_effective_not_the_stored_status():
    """The gate above is only honest if it is fed `effectiveStatus(...)`, the same recomputation
    `tests/test_stale_on_the_surface.py` already holds the rest of this page to - not the raw
    `p.status`, which stays "verified" forever once a record lapses (ABI-15-5)."""
    s = src()
    assert re.search(r"<ShareActions[^>]*status=\{effectiveStatus\(p\.status,\s*p\.valid_until\)\}", s), (
        "ShareActions is not called with effectiveStatus(p.status, p.valid_until) as its status prop"
    )
