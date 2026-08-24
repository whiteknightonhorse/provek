"""LAW-SLUG-JUDGED-BEFORE-FETCH.

`web/src/App.tsx` builds a passport request by interpolating a substring of `location.pathname`
into `/data/passports/<slug>.json`. `route.slice(3).replace(/\\/$/, "")` strips a TRAILING slash
and nothing else, so an inner `/` survived into the path.

The finding is not CodeQL's. The 2026-08-24 triage raised it against ITSELF while dismissing `#6`
and `#7` - two alerts on the frozen `web-1.0/` copy, whose fetch went through
`.replace(/[:/]/g, "_")` and therefore could not carry a separator at all. The live tree was a
superset of the code CodeQL objected to in the frozen one, and carried no alert. Absence of an
alert on the product path is `not_measured`, not `clean`, which is why this gate exists rather than
a note saying the scanner is happy.

WHAT IS ASSERTED, and by what instrument:

  * `tests/slug_probe.mjs` RUNS `web/src/slug.js` under Node - the same bytes the bundle ships -
    over an adversarial corpus, and the refusals are read off its answers rather than off the
    regular expression's text;
  * every slug the emitter can actually produce is ACCEPTED. Those are read from
    `web/public/data/registry.json` at run time, not listed here, so a subject whose identifier
    falls outside the character class turns this gate red instead of turning the site into a page
    of dead ends;
  * the guard is WIRED: `App.tsx` imports it and calls it, in the effect, before the template
    literal that builds the path.

WHAT IS NOT ASSERTED, named rather than implied, because a named blind spot is still a blind spot
(L-25) and the honest thing is to say which half is which:

  * that the DEPLOYED bundle enforces this. These tests read the repository and run one module out
    of it. `scripts/verify_live.sh` reads the origin, and it reads status codes, not behaviour;
  * that `useEffect` ordering in a real browser matches the source ordering asserted below. The
    wiring half IS a source assertion - `preact-render-to-string` does not run effects, so there is
    no render that would exercise the real path - and it is written to be specific about position
    rather than about presence, since "the file contains the string `isSafeSlug`" is satisfied by a
    call sitting after the fetch, or inside a comment, or in dead code (L-21);
  * that `^[A-Za-z0-9_-]+$` is the right rule for identifiers this project does not yet mint. It is
    the measured shape of the eight that exist.

The red runs are `evidence/RED-032-a-slug-that-walked-out-of-the-passport-directory.txt`.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "slug_probe.mjs"
APP = ROOT / "web" / "src" / "App.tsx"
REGISTRY = ROOT / "web" / "public" / "data" / "registry.json"

# Each entry is (slug, why it must be refused). The reasons are here because a corpus without them
# decays into a list nobody can extend: the next person needs to know what each case is standing in
# for, or they will add near-duplicates of the easy ones.
REFUSED = [
    ("git_x/../../etc/passwd", "traversal out of the passport directory, the plain form"),
    ("a/b", "an inner slash - the exact residue `replace(/\\/$/, \"\")` does not remove"),
    ("a%2Fb", "a percent-encoded slash, which some origins resolve before the path is matched"),
    ("..%2f..%2fetc", "traversal with the separator encoded, in case only a literal `/` is checked"),
    ("", "the empty slug: `/p//` would otherwise request the directory itself"),
    ("abc\n", "a trailing newline - accepted by the same pattern in Python's `re`, refused in JS"),
    ("a\nb", "an embedded newline, in case the anchors were relaxed to multiline"),
    ("registry.json", "a dot, which is what lets a slug name a file other than a passport"),
    ("a?cache=1", "a query string, which changes the request without changing the directory"),
    ("a#frag", "a fragment"),
    ("https://evil.example.com/x", "an absolute URL pasted into a path segment"),
    ("git x", "a space"),
    ("\\", "a backslash, which some servers normalise to a separator"),
]

# ACCEPTED and deliberately so. `__proto__` passes the character class, and that is safe HERE for a
# reason worth writing down rather than trusting: `App.tsx` uses the value as a computed key in an
# OBJECT LITERAL (`{...p, [key]: v}`), which defines an own property, where `obj.__proto__ = v`
# would walk the prototype. If that line is ever rewritten as an assignment, this comment is the
# thing that was relied on, and it will be wrong.
ACCEPTED_EXTRA = ["__proto__", "constructor", "a-b_C9", "A"]


def probe(slugs: list[str]) -> list[dict]:
    """Run the guard. A probe that could not run is a refusal, never an empty result."""
    try:
        done = subprocess.run(
            ["node", str(PROBE), json.dumps(slugs)],
            capture_output=True, text=True, timeout=60,
        )
    except FileNotFoundError:  # pragma: no cover - environment, not logic
        pytest.fail(
            "`node` is not on PATH, so the only gate that RUNS the slug guard could not run. "
            "That is a refusal of the instrument and it is reported as one: it is not evidence "
            "that the guard is correct, and it must not be read as a pass."
        )
    if done.returncode != 0:
        pytest.fail(
            f"slug_probe exited {done.returncode}, so nothing was measured.\n"
            f"stdout:\n{done.stdout}\nstderr:\n{done.stderr}"
        )
    return json.loads(done.stdout)


def real_slugs() -> list[str]:
    """The slugs the emitter can actually produce, derived the way `cohort.py` derives them.

    Read rather than listed: a hard-coded copy would keep passing on the day a new subject stops
    matching, which is the one day this assertion is for.
    """
    subjects = json.loads(REGISTRY.read_text())["subjects"]
    assert subjects, (
        "the registry carries no subjects, so the acceptance half of this gate would assert "
        "nothing at all - the empty set is a case, not a reason to skip (L-16)"
    )
    return [re.sub(r"[:/]", "_", s["subject_id"]) for s in subjects]


@pytest.mark.parametrize("slug", real_slugs())
def test_every_real_slug_is_accepted(slug: str) -> None:
    """The guard must not break the passports that exist.

    ONE NODE PER SUBJECT, and that is not cosmetic. A single test looping over the corpus reports
    the same one failure whether one subject broke or all eight did, and - measured, by the
    generator of RED-032 refusing to write its file - it makes weakenings of the rule
    indistinguishable from each other in the evidence. Distinct defects that kill the same test are
    exactly what L-26's transposition check is about.
    """
    row = probe([slug])[0]
    assert row["safe"], (
        f"the guard refuses {slug!r}, which is a REAL subject's slug. A rule that refuses the "
        f"artefact it protects turns every passport into a dead end."
    )


@pytest.mark.parametrize(("slug", "why"), REFUSED, ids=[repr(s) for s, _ in REFUSED])
def test_the_adversarial_slug_is_refused_and_never_reaches_a_url(slug: str, why: str) -> None:
    """The boolean is not the whole property; where the request WOULD have gone is the property.

    Both halves are asserted in the same node because they are one claim about one slug, and
    splitting them produced two tests that could only ever fail together - which is a failure set
    that cannot tell two mutations apart.
    """
    row = probe([slug])[0]
    assert row["slug"] == slug, "the probe answered about a different slug than it was asked"
    assert not row["safe"], f"the guard ACCEPTS {slug!r} - {why}"
    # The URL the probe reports is the one `App.tsx` interpolates. This is what would have been
    # requested had the guard said yes; it is recorded so the refusal is checkable against the
    # thing it prevents rather than against a bare `False`.
    assert row["url"] == f"/data/passports/{slug}.json"


def test_a_non_string_is_refused() -> None:
    """`RegExp.test` coerces, so a missing `typeof` check is a hole with no visible edit.

    `SLUG.test(null)` tests the STRING `"null"`, which is inside the character class - so a guard
    without the type check answers `true` for a value that is not a slug at all, and the caller
    goes on to request `/data/passports/null.json`. Kept separate from the corpus above because
    `null` has no Python spelling that round-trips through the URL assertion, and forcing it into
    that list would have meant weakening the assertion for every other case.
    """
    rows = probe([None, 1, [], {}])
    for row in rows:
        assert not row["safe"], (
            f"the guard accepts {row['slug']!r}, which is not a string. `RegExp.test` would have "
            f"coerced it and matched the coercion rather than the value."
        )


def test_the_probe_can_fail() -> None:
    """Instrument control (L-16, L-28).

    Every assertion above is a refusal, and a probe that answered `safe: false` unconditionally -
    because the import broke, because the module was emptied, because `isSafeSlug` was renamed -
    would satisfy all of them while measuring nothing. This is the reading that must be POSITIVE,
    and it is the one an inert probe cannot produce.
    """
    rows = probe(ACCEPTED_EXTRA)
    assert [r["slug"] for r in rows] == ACCEPTED_EXTRA
    assert all(r["safe"] for r in rows), (
        "the probe refuses slugs that are inside the character class, so it is not distinguishing "
        "anything and the refusals above are worth nothing"
    )


def test_the_guard_is_called_before_the_fetch() -> None:
    """The wiring half. A correct module nobody calls is an unarmed gate that reads as an armed one.

    Position, not presence: L-21 is the case where three repairs were written, documented, and
    never called, and `grep` found each of them at its own definition and nowhere else.
    """
    src = APP.read_text()
    assert 'from "./slug"' in src, "App.tsx does not import the guard at all"

    # The effect that fetches a passport, from the guard clause that opens it to the `fetch(`.
    effect = re.search(r"if \(!slugInRoute\) return;(.*?)fetch\(`/data/passports/", src, re.S)
    assert effect, (
        "could not find the passport effect in App.tsx. Either it was restructured - in which "
        "case this assertion must be rewritten rather than deleted - or the fetch no longer "
        "interpolates the slug, which would make the guard unnecessary and this test wrong."
    )
    assert "isSafeSlug(slugInRoute)" in effect.group(1), (
        "the passport fetch is reached without `isSafeSlug(slugInRoute)` between the effect's "
        "entry and the request. The guard exists and does not stand in front of anything."
    )


def test_an_invalid_slug_is_not_reported_as_a_missing_passport() -> None:
    """Invariant 1, at the point a reader sees it.

    `missing` is what the registry answered when we asked. A slug we refused was never asked
    about, and rendering "nothing has been issued under this identifier" over it would publish an
    absence nobody measured - the founding defect with the sign flipped. The two must be different
    states, and the fifth state must reach the renderer.
    """
    src = APP.read_text()
    assert '{ state: "invalid" }' in src, "the refusal does not have a state of its own"
    assert 'p.state === "invalid"' in src, (
        "nothing renders the `invalid` state, so a refused slug falls through to the skeleton and "
        "the reader waits for ever on a request that was never made"
    )
