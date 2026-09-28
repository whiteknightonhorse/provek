"""LAW-X-ACCOUNT-LINK - every emitted page names the same X account, twice.

T-PX-01-x-account-link (PROVEK-x-link-0928.ruling-1.md, points 1-3): `twitter:site` is a single
static line in `web/index.html`, outside `prerender.mjs`'s per-page rewrite list (`head()` in
`web/prerender.mjs` rewrites only `og:url`, `og:title`, `og:description`, both `twitter:*` title
and description twins - `twitter:site` names the account, not the page, so it is absent from that
list on purpose). The footer link lives in `Footer()` (`web/src/components/Chrome.tsx`), which
`Shell` wraps around every route rendered by both `renderRoute` and `renderStatic`
(`web/src/entry-server.tsx`) - the same component tree the 404 document and every `/method/notes/`
page go through, not a special case for either.

WHY THIS IS A SWEEP, NOT A SPOT CHECK ON `/`. A static meta line and a shared footer component
survive on the page they were written on without any test; what a test buys here is proof that
`prerender.mjs`'s per-page head rewrite and the 404 document's canonical/`og:url` stripping
(`web/prerender.mjs:544-545`) do not also strip or shadow `twitter:site`, and that no route
renders outside `Shell` and silently drops the footer. Both failure modes are per-page, so the
check has to be too - a single page passing proves nothing about the other twelve.

WHAT IS NOT ASSERTED. That the account exists, that `x.com` is reachable, or that `rel="me"`
round-trips through X's own verification - none of that is observable from the built tree.
"""
from __future__ import annotations

from .notes_support import DIST

TWITTER_SITE = '<meta name="twitter:site" content="@provek_dev" />'
X_HREF = 'href="https://x.com/provek_dev"'


def emitted_pages() -> dict[str, str]:
    return {
        str(p.relative_to(DIST)): p.read_text(encoding="utf-8")
        for p in sorted([*DIST.rglob("*.html")])
    }


def test_the_sweep_has_something_to_read():
    """A build that emitted nothing must not report every page as clean (invariant 1: zero pages
    and zero missing-tag pages are the same green unless something separates them)."""
    pages = emitted_pages()
    assert pages, (
        f"no emitted pages under {DIST} - the site was not built, so this sweep measured nothing. "
        f"That is 'check_did_not_run', not a clean result."
    )


def test_every_emitted_page_names_the_x_account_in_the_head_and_the_footer():
    missing_meta = []
    missing_link = []
    for name, html in emitted_pages().items():
        if TWITTER_SITE not in html:
            missing_meta.append(name)
        if X_HREF not in html:
            missing_link.append(name)
    assert not missing_meta, (
        f'pages missing `{TWITTER_SITE}` in <head>: {sorted(missing_meta)}'
    )
    assert not missing_link, (
        f'pages missing the footer link `{X_HREF}`: {sorted(missing_link)}'
    )
