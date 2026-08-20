"""A badge in README is a claim, and this is the gate that makes it falsifiable.

WHY THIS TEST EXISTS. A status badge is the cheapest false claim on the internet: shields.io will
serve `build | passing` in the project's own colours to anybody who types the words into a URL, and
nothing anywhere checks that a build exists. This repository is built to detect claims stronger than
the artefact behind them, so a decorative badge in its own README would be the worst available
defect - the tool failing on itself, in public, at the very top of the page.

So the rule is mechanical rather than a matter of taste:

  1. every badge image is wrapped in a link, because a claim a reader cannot follow to its run is
     not checkable;
  2. every GitHub Actions badge names a workflow file that EXISTS in this repository, and links to
     that same workflow's run list - a badge for a deleted workflow keeps rendering the last colour
     it had;
  3. the static-label endpoint `img.shields.io/badge/...` is banned outright. That is the one that
     takes its text from the URL. Note the near-miss: the OpenSSF badge redirects THROUGH shields,
     but the URL written here is the OpenSSF's own API, so the number comes from them.

WHAT IT DOES NOT CHECK. Whether a badge is currently green. That is a network fact about a service,
and a test that fails when GitHub is slow teaches people to skip the suite (L-4's other edge: a
false red bypasses a gate exactly as a false green does). The runs behind these badges were read
from the Actions API and the OpenSSF API before they were written in, and that measurement is
recorded in the commit that added them.

HOW TO MAKE IT FAIL, which is the only reason to trust it: paste
`![build](https://img.shields.io/badge/build-passing-brightgreen)` into README, or delete
`.github/workflows/codeql.yml` while its badge stays.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
WORKFLOWS = ROOT / ".github" / "workflows"

# ![alt](image_url) optionally wrapped in [ ... ](target). The leading `[` group tells the two apart.
BADGE = re.compile(r"(\[)?!\[(?P<alt>[^\]]*)\]\((?P<img>[^)\s]+)\)(?:\]\((?P<href>[^)\s]+)\))?")

ACTIONS_BADGE = re.compile(
    r"https://github\.com/(?P<repo>[^/]+/[^/]+)/actions/workflows/(?P<wf>[^/]+\.yml)/badge\.svg"
)

STATIC_LABEL_ENDPOINT = "img.shields.io/badge/"


def _badges() -> list[re.Match]:
    return list(BADGE.finditer(README.read_text(encoding="utf-8")))


def test_readme_actually_carries_badges():
    """Guards the guard: if the badges vanish, every check below would pass vacuously."""
    assert _badges(), "README carries no badges at all - the rest of this file would be a no-op"


def test_every_badge_is_a_link_to_its_report():
    for m in _badges():
        assert m.group("href"), (
            f"badge {m.group('alt')!r} is an image with no link: a claim whose evidence "
            f"the reader cannot open"
        )


def test_no_static_label_badges():
    """The endpoint whose text is whatever you typed into the URL."""
    for m in _badges():
        assert STATIC_LABEL_ENDPOINT not in m.group("img"), (
            f"badge {m.group('alt')!r} uses {STATIC_LABEL_ENDPOINT} - that endpoint renders the "
            f"words in its own URL and no run stands behind it"
        )


def test_every_actions_badge_names_a_workflow_that_exists():
    seen = 0
    for m in _badges():
        hit = ACTIONS_BADGE.fullmatch(m.group("img"))
        if not hit:
            continue
        seen += 1
        wf = WORKFLOWS / hit.group("wf")
        assert wf.exists(), (
            f"badge {m.group('alt')!r} points at {hit.group('wf')}, which is not in "
            f".github/workflows - a badge for a workflow that does not exist keeps rendering "
            f"the last colour it ever had"
        )
    assert seen, "no GitHub Actions badge found - this repository's own CI is unrepresented"


def test_every_actions_badge_links_to_that_same_workflows_runs():
    """A badge for `gates` linking to `codeql`'s runs sends the reader to the wrong evidence."""
    for m in _badges():
        hit = ACTIONS_BADGE.fullmatch(m.group("img"))
        if not hit:
            continue
        expected = f"https://github.com/{hit.group('repo')}/actions/workflows/{hit.group('wf')}"
        assert m.group("href") == expected, (
            f"badge for {hit.group('wf')} links to {m.group('href')} instead of {expected}"
        )


def test_the_badges_are_explained_where_the_reader_can_find_it():
    """A green tick with no statement of what it covers is read as covering everything."""
    text = README.read_text(encoding="utf-8")
    assert "## What the badges assert" in text, (
        "the badge section is gone; three green ticks with nothing saying what they mean read as "
        "a claim about the whole repository"
    )
    assert "#what-the-badges-assert" in text, "the badges no longer link to their own explanation"
