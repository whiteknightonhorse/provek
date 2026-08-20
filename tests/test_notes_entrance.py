"""LAW-NOTES-ENTRANCE - the way in to the notes exists exactly when the notes do.

WHY THIS EXISTS AS A GATE RATHER THAN AS CARE. The Method page carried a paragraph saying the
methodology's harder parts "are written up as notes on the method", linking to `/method/notes/`.
Zero notes were captured, `prerender.mjs` emits that route only inside `if (notes.length)`, and so
the built site shipped one dangling internal link and, worse, one present-tense claim that a body
of writing existed. Nothing caught it: the four LAW-NOTES-* modules all carry
`skipif(not sources())`, so at zero notes - the state the site was actually in - every one of them
skipped, and the ratchet still counted them among the armed.

That is invariant 1 in the shape of a test suite. "The notes are correct" and "there are no notes
to check" are two states of the world, and a suite that skips reports them identically.

SO THIS MODULE NEVER SKIPS. It asserts a BICONDITIONAL, which is what makes it able to fail from
either side:

  * zero notes captured  -> no surface may offer a way in (today's state, and the red run that
    found the defect is kept as `evidence/RED-006-notes-entrance-without-notes.txt`);
  * one or more captured -> the Method page MUST name the entrance, so the first capture cannot
    quietly publish a section nobody can reach.

The second half is the load-bearing one for the future. Without it the honest fix for the first -
delete the paragraph - would leave the entrance to be restored from somebody's memory on the day a
note lands, and a rule whose enforcement depends on remembering is L-7's docstring rule again.

WHAT THIS GATE CATCHES, STATED NARROWLY BECAUSE THE FIRST DRAFT OVERSTATED IT. The source checks
match a LITERAL `/method/notes/` in `.tsx` and `.mjs` markup. A computed href - `{"/method/" +
"notes/"}`, a template string, a constant imported from elsewhere - is NOT caught by them, and no
amount of regex will change that; a page can always construct a link the reader of its source
cannot see. The backstop for that case is
`test_the_built_site_has_no_link_that_it_did_not_emit`, which reads the EMITTED HTML, where every
href is a literal no matter how it was computed. That backstop needs a build, so
`.github/workflows/gates.yml` now builds the site and runs it - before that it skipped in CI and
this module was, in the only place gates do not depend on the pusher's discipline, one grep.

AND THE BACKSTOP IS STILL NOT TOTAL, WHICH IS SAID HERE RATHER THAN LEFT TO BE DISCOVERED. It reads
`href` attributes. A link built by JavaScript - an `onClick` that calls `pushState` - carries no
href and is invisible to it, as is an entrance placed in a channel that is not markup. What it does
cover is the whole of what this site emits today, which is static documents whose every link is an
attribute.
"""
from __future__ import annotations

import re

import pytest

from .notes_support import ROOT, sources

METHOD_TSX = ROOT / "web" / "src" / "pages" / "Method.tsx"
DIST = ROOT / "web" / "dist"
ENTRANCE = "/method/notes/"


def _strip_comments(src: str) -> str:
    """Source with its comments removed, and NOTHING ELSE removed.

    Comments must go: the paragraph was deleted and replaced by a comment EXPLAINING the deletion,
    and that comment names `/method/notes/`. Matching the raw file would read the explanation as
    the offence and hold this gate red forever, and a false red teaches walking past a gate exactly
    as a false green does (L-5).

    THE FIRST DRAFT STRIPPED COMMENTS WITH `/\\*.*?\\*/` AND SO COULD PRODUCE THE FALSE GREEN IT WAS
    GUARDING AGAINST. That pattern does not know what a string literal is: a `/*` inside one - a URL
    such as "http://x/*" - opens a match that runs to the next `*/` anywhere in the file, deleting
    every line between, real markup included. Defending against the false red had opened the
    opposite hole. Block comments are therefore only recognised at the START of a line, which is
    where this codebase writes them and where a string literal cannot put one.
    """
    src = re.sub(r"\{/\*.*?\*/\}", " ", src, flags=re.S)          # JSX comment blocks
    src = re.sub(r"^[ \t]*/\*.*?\*/", " ", src, flags=re.S | re.M)  # line-leading block comments
    src = re.sub(r"^[ \t]*(//|\*).*$", " ", src, flags=re.M)      # line comments and jsdoc bodies
    return src


def _method_source() -> str:
    return _strip_comments(METHOD_TSX.read_text(encoding="utf-8"))


def test_method_offers_the_entrance_exactly_when_notes_exist() -> None:
    n = len(sources())
    offers = ENTRANCE in _method_source()
    if n == 0:
        assert not offers, (
            f"Method.tsx links {ENTRANCE} while no note is captured. `prerender.mjs` emits that "
            "route only when at least one note exists, so this is a link to a 404 AND a page "
            "claiming a body of writing that is not there."
        )
    else:
        assert offers, (
            f"{n} note(s) captured and Method.tsx does not name {ENTRANCE}. The notes are reachable "
            "from one sentence of prose and from nowhere else (SPEC 3.6, ADR-0009 keeps them out of "
            "the navigation), so without that sentence they are published and unreachable."
        )


def test_no_surface_anywhere_offers_an_entrance_that_is_not_built() -> None:
    """The same rule over every component, not just the one that broke.

    Restricting this to `Method.tsx` would be L-6: a checker that inspects one file reports success
    on every other. If some future page links the notes, it is caught here.
    """
    if sources():
        pytest.skip("notes are captured; the entrance is permitted and is asserted above")
    offenders = []
    for f in sorted((ROOT / "web" / "src").rglob("*.tsx")):
        body = _strip_comments(f.read_text(encoding="utf-8"))
        # THE ROUTER'S HAND-OFF IS EXCUSED BY ITS CONSTRUCTION, NOT BY ITS FILENAME. `App.tsx`
        # names this prefix to REFUSE to handle it - `if (href.startsWith("/method/notes/")) return;`
        # sends the click to the server instead of the router. Excusing the whole file (the first
        # draft did) would have let a genuine `<a href="/method/notes/">` sit green inside 297 lines
        # that do render anchors. Only that one construction is removed; anything else in the same
        # file is still an offence.
        body = re.sub(r'startsWith\(\s*"' + re.escape(ENTRANCE) + r'"\s*\)', " ", body)
        if ENTRANCE in body:
            offenders.append(f.relative_to(ROOT).as_posix())

    # THE EMITTERS ARE CHECKED FOR AN ANCHOR, NOT FOR THE STRING. `prerender.mjs` prints the
    # shipped markup and the sitemap and was outside the first draft's reach entirely (L-12: a
    # checker that reads one part of the tree reports success on the rest). It cannot be scanned
    # the same way, because it legitimately CONTAINS this route - it is the code that builds it,
    # inside `if (notes.length)`. Flagging the bare string here would be a permanent false red on
    # correct code, so what is looked for is an anchor: route construction is the job, a link to a
    # route that was not emitted is the defect.
    for f in sorted((ROOT / "web").glob("*.mjs")):
        if re.search(r'href=[\\"\']*' + re.escape(ENTRANCE), _strip_comments(f.read_text(encoding="utf-8"))):
            offenders.append(f.relative_to(ROOT).as_posix())

    assert not offenders, f"no note is captured, yet these offer a way in: {offenders}"


def test_the_built_site_has_no_link_that_it_did_not_emit() -> None:
    """L-3, over the artefact: every internal href on every emitted page resolves to something
    emitted. This is the general form of the defect - the notes entrance was one instance - and it
    is the check that would have caught it without knowing anything about notes."""
    if not DIST.exists():
        pytest.skip("site not built in this checkout")
    routes, files = set(), set()
    for p in DIST.rglob("*"):
        if not p.is_file():
            continue
        files.add(p.relative_to(DIST).as_posix())
        if p.name == "index.html":
            r = p.parent.relative_to(DIST).as_posix()
            routes.add("/" if r == "." else f"/{r}/")
    dangling = set()
    # EVERY 404.html TOO, not just the routed documents - it is the page a reader receives for any
    # address that does not exist, and a broken link on it is a broken link.
    for p in sorted([*DIST.rglob("index.html"), *DIST.glob("404.html")]):
        r = p.parent.relative_to(DIST).as_posix()
        page = "/" if r == "." else f"/{r}/"
        # THE QUERY AND THE FRAGMENT ARE STRIPPED AFTER MATCHING, NOT INSIDE THE CHARACTER CLASS.
        # `href="(/[^"#?]*)"` required the quote to come straight after the path, so any href
        # carrying `?` or `#` - `/method/notes/?src=m` - matched NOTHING AT ALL and passed unseen.
        # A pattern meant to ignore the query was instead ignoring the link, which is the false
        # green this whole module exists to prevent, sitting inside its own backstop.
        for raw in set(re.findall(r'href="(/[^"]*)"', p.read_text(encoding="utf-8"))):
            href = raw.split("#", 1)[0].split("?", 1)[0]
            if not href:
                continue          # a bare "#fragment" target names no address to resolve
            if href not in routes and href.lstrip("/") not in files:
                dangling.add((page, href))
    assert not dangling, f"emitted pages link to addresses the build did not produce: {sorted(dangling)}"
