"""Markdown negotiation (ABI content axis, Fable's ruling 2026-08-31).

WHAT THIS ENFORCES, in three layers.

1. `web/markdown.mjs` is a pure function of registry+passport data (`tests/... -> node markdown.mjs`
   below), the same testing shape `tests/test_discovery_maps_agree.py` uses for `discovery.mjs` -
   checked without paying for a full site build.

2. THE BUILT ARTEFACT, not the generator's stdout. Fable's own example of why this matters sits in
   `web/prerender.mjs`'s robots.txt comment: a build step wrote a hardcoded string into `dist/`
   AFTER `vite build` had already copied the real source there, so the source could be edited
   forever and the served file would never change. `web/dist/` is what `wrangler pages deploy`
   publishes, so the markdown siblings this project claims to serve are asserted to exist THERE,
   byte-for-byte what the generator produces from the data the tree currently holds - not merely
   that the generator function is capable of producing them somewhere. Skipped, not failed, when
   `web/dist` is absent (the same convention `tests/test_separation_single_reference.py` uses):
   `scripts/push.sh` builds the site (step 6) before it runs pytest (step 7), so the door always
   judges a built tree; a bare `pytest` in an unbuilt checkout is not the door.

3. THE MIDDLEWARE'S BEHAVIOUR, run rather than read (`tests/middleware_probe.mjs`, the same shape as
   `tests/intake_probe.mjs`): markdown only on `Accept: text/markdown`, the OLD response on every
   other request including the ordinary browser one with no Accept header at all (the control this
   task named explicitly), and the three existing Functions plus a JSON data file untouched even
   when a client sends the markdown header - proving the fallthrough is decided by route shape, not
   by a list of names that could go stale as routes are added.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
MARKDOWN_GEN = WEB / "markdown.mjs"
MIDDLEWARE = WEB / "functions" / "_middleware.js"
PROBE = ROOT / "tests" / "middleware_probe.mjs"
DATA_DIR = WEB / "public" / "data"
DIST = WEB / "dist"
SITE = "https://provek.dev"


def test_the_generator_and_the_middleware_both_exist() -> None:
    """A gate pointed at a moved file reports clean forever - L-16's shape."""
    for path in (MARKDOWN_GEN, MIDDLEWARE, PROBE):
        assert path.is_file(), f"{path} is missing."


# --- layer 1: the generator is a pure function of registry + passport data ----------------------

def _run_markdown_gen(data_dir: Path) -> dict:
    result = subprocess.run(
        ["node", str(MARKDOWN_GEN), str(data_dir), SITE],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"markdown.mjs failed: {result.stderr}"
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def live_markdown() -> dict:
    return _run_markdown_gen(DATA_DIR)


@pytest.fixture(scope="module")
def live_registry() -> dict:
    return json.loads((DATA_DIR / "registry.json").read_text(encoding="utf-8"))


def test_registry_markdown_names_every_subject_and_the_true_count(live_markdown, live_registry):
    md = live_markdown["registryMd"]
    assert md.startswith("# Provek registry\n"), "registry markdown carries no title"
    assert f"{live_registry['count']} records" in md, (
        "the markdown does not carry the registry's own count - a hand-typed number here would be "
        "exactly the drift this file exists to prevent"
    )
    for subject in live_registry["subjects"]:
        assert subject["subject_id"] in md, f"{subject['subject_id']} is missing from the registry markdown"


def test_passport_markdown_covers_every_passport_on_disk(live_markdown, live_registry):
    from_registry = {s["subject_id"] for s in live_registry["subjects"]}
    assert live_markdown["passportMd"], "no passport markdown was produced at all"
    produced_subject_ids = set()
    for slug, md in live_markdown["passportMd"].items():
        assert md.startswith("# Autonomy passport: "), f"{slug}: no title"
        assert "## Operations" in md, f"{slug}: no operations table"
        produced_subject_ids.add(md.split("\n", 1)[0].removeprefix("# Autonomy passport: "))
    assert produced_subject_ids == from_registry, (
        "passport markdown and the registry disagree on which subjects exist: "
        f"only in registry: {sorted(from_registry - produced_subject_ids)}, "
        f"only in markdown: {sorted(produced_subject_ids - from_registry)}"
    )


def test_a_bare_projection_never_appears_without_its_name(live_markdown):
    """`web/functions/badge/[id].js`'s own rule, over the same data: a number standing alone for a
    subject is the overclaim this project marks other subjects down for making about themselves."""
    for slug, md in live_markdown["passportMd"].items():
        assert "Projection: **" in md, f"{slug}: projection is not labelled"
        assert "not measured (" in md or "/100**" in md.split("Projection: **", 1)[1][:40], (
            f"{slug}: the projection value does not carry its unit or its absence reason"
        )


# --- layer 2: the SERVED artefact, not the generator's opinion of itself -------------------------

pytestmark_dist = pytest.mark.skipif(
    not DIST.exists(), reason="site not built in this checkout (npm run build was not run)")


@pytestmark_dist
def test_dist_carries_a_markdown_sibling_for_the_registry_page(live_markdown):
    served = (DIST / "registry" / "index.md").read_text(encoding="utf-8")
    assert served == live_markdown["registryMd"], (
        "web/dist/registry/index.md does not match what web/markdown.mjs produces from the data "
        "currently on disk - the artefact wrangler would publish has drifted from its own source, "
        "the exact shape of the robots.txt regression this gate exists to rule out for this file."
    )


@pytestmark_dist
def test_dist_carries_a_markdown_sibling_for_every_passport_page(live_markdown):
    missing = []
    mismatched = []
    for slug, expected in live_markdown["passportMd"].items():
        served_path = DIST / "p" / slug / "index.md"
        if not served_path.is_file():
            missing.append(slug)
            continue
        if served_path.read_text(encoding="utf-8") != expected:
            mismatched.append(slug)
    assert not missing, f"no markdown sibling built for: {missing}"
    assert not mismatched, f"built markdown sibling disagrees with the generator for: {mismatched}"


#: Routes whose markdown is BUILT FROM DATA, not derived from the rendered page. Everything else
#: gets its sibling from `html_to_markdown.mjs`, so this list is the whole of the exception.
DATA_BUILT = ("", "registry")

#: Losses this converter DECLARES rather than hides: the page chrome outside `<main>`, the sr-only
#: spans that duplicate what the eye reads, and inline SVG (two method notes draw charts whose axis
#: labels read as a word salad in prose order). Named here as well as in the converter because a
#: gate that widens silently until it passes measures nothing.
DECLARED_LOSSES = ("outside <main>", "sr-only spans", "inline <svg>")


def _derived_routes():
    for html in sorted(DIST.rglob("index.html")):
        rel = str(html.parent.relative_to(DIST)).replace(".", "")
        if rel in DATA_BUILT or rel.startswith("p/"):
            continue
        yield rel, html.parent


@pytestmark_dist
def test_every_page_route_has_a_markdown_sibling():
    """No page route may answer `Accept: text/markdown` with HTML.

    Ruling 2026-08-31, AMENDED 2026-09-01. The original rule forbade a sibling for the prose pages
    (`/`, `/method/`, `/apply/`, `/phase-2/`) because a generated one would have been a SECOND COPY
    of prose that only lives in TSX, and a second copy drifts. That objection dissolved when the
    sibling stopped being written and started being COMPUTED from the page's own rendered HTML: a
    projection cannot drift from its source, only a copy can. What stays forbidden is a hand-written
    builder for a prose route - held by `test_a_derived_sibling_is_exactly_what_the_converter_emits`
    below, which recomputes each one and compares bytes."""
    missing = [rel for rel, d in _derived_routes() if not (d / "index.md").exists()]
    assert not missing, (
        f"{len(missing)} page route(s) have no markdown sibling: {missing} - the scanner that "
        "measured this site as 'does not support Markdown for Agents' asked the ONE address that "
        "had none"
    )


@pytestmark_dist
def test_a_derived_sibling_is_exactly_what_the_converter_emits():
    """A derived sibling is a projection of its page, and this proves it byte for byte.

    This is what replaced "no sibling exists". Hand-editing one, or slipping a data-built renderer
    in for a prose route, changes the bytes and fails here - which is the second-copy risk the
    original rule was written against, now caught by measurement rather than by absence."""
    recompute = ROOT / "tests" / "recompute_derived_md.mjs"
    assert recompute.is_file(), f"{recompute} is missing - the instrument this gate reads through"
    for rel, d in _derived_routes():
        done = subprocess.run(["node", str(recompute), str(d)],
                              capture_output=True, text=True, timeout=30)
        assert done.returncode == 0, f"recompute failed for /{rel}/: {done.stderr}"
        assert done.stdout == (d / "index.md").read_text(encoding="utf-8"), (
            f"/{rel}/index.md is not what html_to_markdown.mjs produces from its own index.html - "
            "a derived sibling that was edited, or built by something else, is exactly the second "
            "copy this rule exists against"
        )


@pytestmark_dist
def test_a_derived_sibling_loses_no_visible_word():
    """FIDELITY. The converter's header promises it keeps what it does not recognise; this counts.

    Its first version selected `h*|p|li|summary|td|th` and dropped the rest while the header said
    the opposite - `/apply/` lost 76 visible words, the `<label>` and `<button>` text that says HOW
    to apply, which is that page's entire content for an agent. A promise in a comment is not a
    mechanism (LAW #ALLOWLIST-WHAT-YOU-INSPECT: a checker that skips what it does not recognise
    reports success on what it cannot handle)."""
    import re
    strip = lambda h: re.sub(r"<svg\b[^>]*>.*?</svg>", " ",
                     re.sub(r'<span[^>]*\bsr-only\b[^>]*>.*?</span>', " ",
                     re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", h, flags=re.S|re.I),
                     flags=re.S | re.I), flags=re.S | re.I)
    # Entities are stripped BEFORE tokenising, exactly as the converter's `decode` resolves them:
    # without this `&quot;` tokenises to the word "quot", which the markdown (holding a real quote
    # character) does not contain, and the gate reports a loss that never happened. Two instruments
    # measuring the same thing must agree on their world before either verdict means anything.
    words = lambda t: set(re.findall(
        r"[a-z0-9]{2,}",
        re.sub(r"&[a-z#0-9]+;", " ", re.sub(r"<[^>]+>", " ", t), flags=re.I).lower()))
    for rel, d in _derived_routes():
        html = (d / "index.html").read_text(encoding="utf-8")
        main = re.search(r"<main\b[^>]*>(.*?)</main>", html, re.S | re.I)
        source = words(strip(main.group(1) if main else html))
        lost = sorted(source - words((d / "index.md").read_text(encoding="utf-8")))
        assert not lost, (
            f"/{rel}/ drops {len(lost)} visible word(s) from its own page: {lost[:12]} - the only "
            f"losses this converter is allowed are the declared ones ({', '.join(DECLARED_LOSSES)})"
        )


# --- layer 3: the middleware's behaviour, run rather than read -----------------------------------

def _probe(scenario: str) -> dict:
    assert PROBE.is_file(), (
        f"{PROBE} is missing - the instrument this gate reads through is gone, so every assertion "
        "below would be about nothing."
    )
    try:
        done = subprocess.run(
            ["node", str(PROBE), scenario],
            cwd=ROOT, capture_output=True, timeout=30, check=False)
    except FileNotFoundError:
        raise AssertionError(
            "`node` is not on PATH, so the only gate that RUNS the middleware could not run. That "
            "is a missing instrument and a red, never a silent skip (L-16)."
        ) from None
    assert done.returncode == 0, (
        f"the probe exited {done.returncode} on scenario {scenario!r}:\n"
        f"{done.stderr.decode('utf-8', 'replace')}")
    return json.loads(done.stdout.decode("utf-8"))


def test_no_accept_header_gets_the_old_html_not_markdown():
    """THE CONTROL. An ordinary browser sends no Accept: text/markdown at all - if this scenario
    ever answered markdown, negotiation would be a substitution, not an addition."""
    r = _probe("no_header_gets_the_old_html")
    assert r["next_called"] == 1, "the middleware did not pass the ordinary request through"
    assert r["body"] == "ORDINARY-PIPELINE-RESPONSE"
    assert r["content_type"] != "text/markdown; charset=utf-8"


def test_explicit_html_accept_also_gets_the_old_html():
    r = _probe("html_accept_gets_the_old_html")
    assert r["next_called"] == 1
    assert r["body"] == "ORDINARY-PIPELINE-RESPONSE"


def test_markdown_accept_on_a_page_with_a_sibling_gets_markdown():
    r = _probe("markdown_accept_on_a_page_with_a_sibling")
    assert r["next_called"] == 0, "the middleware called through instead of answering markdown itself"
    assert r["status"] == 200
    assert r["content_type"] == "text/markdown; charset=utf-8"
    assert r["body"] == "# Provek registry\n\nfixture body\n"


def test_markdown_wins_when_the_client_offers_both():
    r = _probe("markdown_accept_wins_when_both_are_offered")
    assert r["content_type"] == "text/markdown; charset=utf-8"
    assert r["next_called"] == 0


def test_markdown_accept_on_a_page_with_no_sibling_falls_through_rather_than_404():
    """A page that plainly exists but has no generated sibling yet must keep answering its HTML -
    a 404 here would tell a markdown-reading client a real page does not exist."""
    r = _probe("markdown_accept_on_a_page_with_no_sibling")
    assert r["next_called"] == 1
    assert r["status"] == 200
    assert r["body"] == "ORDINARY-PIPELINE-RESPONSE"


@pytest.mark.parametrize("scenario", [
    "api_apply_untouched_even_with_markdown_accept",
    "badge_untouched_even_with_markdown_accept",
    "brief_untouched_even_with_markdown_accept",
    "registry_json_untouched_even_with_markdown_accept",
])
def test_existing_functions_and_data_are_never_intercepted(scenario):
    """The requirement's own warning: middleware in Cloudflare Pages intercepts EVERY request.
    Each of these paths ends in a literal segment, never `/`, so `markdownSiblingPath` refuses them
    by shape - checked here even against a client that explicitly asks for markdown, the one case
    that would expose a middleware intercepting by header alone instead of by route shape."""
    r = _probe(scenario)
    assert r["next_called"] == 1, f"{scenario}: the middleware intercepted a non-page route"
    assert r["body"] == "ORDINARY-PIPELINE-RESPONSE"
