"""The phase-2 page announces a specification, never a capability.

D-16 narrows D-05's boundary - "nothing announces a feature that does not exist" - to permit ONE
page that describes phase 2. A narrowing defended in prose and left unarmed is the shape this
project has already paid for twice (L-7): the weak-signal limiters were a docstring note until they
became code, and the accountability defaults were a schema comment until a gate read the emitted
document. So the four rules of SPEC 3.5 are checked here, and they are checked over the EMITTED
HTML, because what a reader receives is the thing that has to hold (L-3).

The source-level half runs everywhere, including a checkout with no build. A gate that can only run
where `web/dist` happens to exist would be green on CI while the page said anything at all.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "web" / "dist" / "phase-2" / "index.html"
SRC = ROOT / "web" / "src" / "pages" / "Phase2.tsx"
APP = ROOT / "web" / "src" / "App.tsx"
PRERENDER = ROOT / "web" / "prerender.mjs"

REFUSAL_AT_THE_TOP = "Nothing on this page is in service"
REFUSAL_AT_THE_FOOT = "Nothing on this page is an offer"
NO_INTAKE = "no application for one is being taken"

#: The one link the page is allowed to offer, plus the address of its own source. Anything else is
#: a route out of a page whose entire content is a refusal.
PERMITTED_LINKS = {
    "/apply/",
    "https://github.com/whiteknightonhorse/provek/blob/main/SPEC.md",
}

#: A date, or any word that stands in for one. "Soon" is not on this list and must not be: it names
#: no date and commits to nothing. A quarter, a month or a year does, and adding one would turn a
#: description into a promise without changing a single verb.
#: `may` is deliberately absent from the month names. It is also the modal verb this page leans on
#: most - "the page may not invent one" - and a gate that fires on the refusal is a gate that gets
#: switched off. A written-out May would arrive with a year beside it in any real sentence, and the
#: year alternative catches that.
DATES = re.compile(
    r"\b(19|20)\d{2}\b"
    r"|\bQ[1-4]\b"
    r"|\b(january|february|march|april|june|july|august|september|october|november|december)\b"
    r"|\b(next|this) (year|quarter|month|week)\b"
    r"|\bby the end of\b|\bwithin (a )?(few )?(weeks|months|days)\b"
    r"|\bin the coming\b|\blaunch date\b|\btimeline\b|\broadmap\b|\beta\b",
    re.I,
)

#: The exact constraint list of specification 8.5, and the status each one MUST carry. The pairing
#: is the point of the section: 8.5 forbids presenting the evidenced as the enforced and puts that
#: obligation on the interface, so a row that loses its status word is the defect itself.
CONSTRAINTS: list[tuple[str, str]] = [
    ("Ceiling on the amount", "enforced"),
    ("Permitted on-chain recipient", "enforced"),
    ("Release of a milestone against a machine-checkable criterion", "enforced"),
    ("Timeout, and return of whatever was not committed", "enforced"),
    ("The money was spent on compute", "evidenced only"),
    ("The work was done well", "evidenced only"),
    ("The agent did not hand the task to a human", "evidenced only"),
]

STATUS = re.compile(r">(enforced|evidenced only)<")


def _main() -> str:
    """The page's own content, without the shell and without the bootstrap payload.

    The inlined `window.__PROVEK__` carries the whole registry, including every `valid_until` -
    real dates, belonging to a different statement. A date gate that read them would fire on the
    truth and get switched off.
    """
    html = PAGE.read_text(encoding="utf-8")
    body = html.split("<script>window.__PROVEK__", 1)[0]
    m = re.search(r"<main\b.*?</main>", body, re.S)
    assert m, "the emitted page has no <main>"
    return m.group(0)


def _text(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


emitted = pytest.mark.skipif(not PAGE.exists(), reason="site not built in this checkout")


# --- rule 1: the refusal is the first thing said, and the last ---------------------------------


@emitted
def test_the_page_refuses_at_the_top_and_again_at_the_foot():
    text = _text(_main())
    assert REFUSAL_AT_THE_TOP in text, "the page never says it is not in service"
    assert REFUSAL_AT_THE_FOOT in text, "the page never repeats the refusal at its foot"
    # A refusal four screens down is a refusal that was not given (the D-02 argument, applied to a
    # different claim). 700 characters is roughly the first screenful of this page's prose.
    assert text.index(REFUSAL_AT_THE_TOP) < 700, (
        f"the refusal starts {text.index(REFUSAL_AT_THE_TOP)} characters in")
    assert text.index(REFUSAL_AT_THE_FOOT) > len(text) - 900, "the closing refusal has drifted up"


@emitted
def test_the_page_says_no_application_is_being_taken():
    assert NO_INTAKE in _text(_main())


@emitted
def test_the_refusal_travels_in_the_title_and_the_description():
    """Most readers meet this page as a search result or a social card and never open it."""
    html = PAGE.read_text(encoding="utf-8")
    title = re.search(r"<title>([^<]*)</title>", html)
    desc = re.search(r'<meta name="description" content="([^"]*)"', html)
    assert title and "not in service" in title.group(1).lower(), title
    assert desc and "not in service" in desc.group(1).lower(), desc


# --- rule 2: no date, and no word standing in for one ------------------------------------------


@emitted
def test_the_emitted_page_names_no_date():
    hit = DATES.search(_text(_main()))
    assert hit is None, f"the page commits to a time: {hit.group(0)!r}"


def test_the_component_names_no_date():
    """Runs without a build, so the gate has teeth on CI as well as here."""
    hit = DATES.search(SRC.read_text(encoding="utf-8"))
    assert hit is None, f"the component commits to a time: {hit.group(0)!r}"


# --- rule 3: nothing on the page can be pressed, and nothing leads to a payment -----------------


@emitted
def test_the_page_carries_no_control_that_could_be_pressed():
    """A control that does nothing is still a promise: the only reason to render one is that
    pressing it will eventually do something. That is D-05's actual subject, and D-16 does not
    licence it - it licences a description."""
    main = _main()
    for tag in ("<button", "<form", "<input", "<select"):
        assert tag not in main, f"the phase-2 page renders a {tag}> control"


@emitted
def test_every_link_leads_to_one_of_the_two_permitted_destinations():
    links = set(re.findall(r'<a\b[^>]*href="([^"]+)"', _main()))
    assert links, "the page has no links at all, including the one to its own source"
    assert links <= PERMITTED_LINKS, f"unpermitted destination: {sorted(links - PERMITTED_LINKS)}"


def test_the_component_has_no_payment_path():
    """A-6 is a permanent non-goal, so this is checked as a word list rather than as a shape: the
    page discusses payment at length in order to refuse it, and it is the VERBS that would betray a
    change of mind."""
    src = SRC.read_text(encoding="utf-8").lower()
    for verb in ("stripe", "checkout", "add to cart", "pay now", "buy now",
                 "subscribe", "pricing", "price:", "credit card"):
        assert verb not in src, f"a payment path appeared on the phase-2 page: {verb!r}"


# --- rule 4: enforced and evidenced are never swapped or dropped -------------------------------


@emitted
def test_every_constraint_publishes_whether_it_is_enforced_or_only_evidenced():
    main = _main()
    for text, expected in CONSTRAINTS:
        i = main.find(text)
        assert i != -1, f"constraint missing from the page: {text!r}"
        found = STATUS.search(main, i)
        assert found, f"constraint carries no status: {text!r}"
        assert found.group(1) == expected, (
            f"{text!r} is published as {found.group(1)!r}, specification 8.5 says {expected!r}")


@emitted
def test_the_page_says_who_does_the_enforcing():
    """`enforced` with no agent reads as "enforced by Provek", which is the custodial claim A-6
    exists to refuse."""
    text = _text(_main())
    assert "enforced by the contract the parties deploy" in text
    assert "we are not a party to it" in text


# --- the reserved slots D-16 did NOT open ------------------------------------------------------


def test_d05_still_holds_everywhere_else():
    """D-16 narrows one boundary. The narrowing is worthless if nobody checks that it stayed narrow:
    "a rule written in more than one place survives its own repeal" has a mirror image, and this is
    it - a rule repealed in one place quietly repealing itself everywhere."""
    chrome = (ROOT / "web" / "src" / "components" / "Chrome.tsx").read_text(encoding="utf-8")
    assert 'aria-disabled="true"' in chrome, "the reserved corpus slot stopped being disabled"
    assert "/phase-2/" not in chrome, (
        "the phase-2 page reached the navigation - that is an announcement in the one place a "
        "reader reads on every screen, and D-05 still forbids it")
    landing = (ROOT / "web" / "src" / "pages" / "Landing.tsx").read_text(encoding="utf-8")
    assert "/phase-2/" not in landing, (
        "phase 2 is offered on the landing, where a subject decides - specification 4.6 requires "
        "the pitch to hold at zero funders")


def test_the_route_is_wired_and_titled_as_a_refusal():
    app = APP.read_text(encoding="utf-8")
    assert 'if (route === "/phase-2/") return <Phase2 />;' in app, "the route is not served"
    assert re.search(r'"/phase-2/":\s*"[^"]*not in service[^"]*"', app), "the title hides the refusal"
    assert '"/phase-2/"' in PRERENDER.read_text(encoding="utf-8"), (
        "the page is not prerendered, so it has no address for a crawler or an archive")


# --- the control: each planted defect is a shape this page could really take --------------------


def test_these_gates_would_fire():
    """A checker never exercised against a real failure is not evidence of anything."""
    assert DATES.search("available in Q3"), "the date gate misses a quarter"
    assert DATES.search("shipping in March"), "the date gate misses a month"
    assert DATES.search("live in 2027"), "the date gate misses a year"
    assert DATES.search("see the roadmap"), "the date gate misses a roadmap"
    assert DATES.search("within a few weeks"), "the date gate misses a horizon"
    assert not DATES.search("It is not in service and no date is given."), (
        "the date gate fires on the refusal itself, which would make it unsatisfiable")

    swapped = '<li>The work was done well<span>enforced</span></li>'
    m = STATUS.search(swapped, swapped.find("The work was done well"))
    assert m and m.group(1) != "evidenced only", "the enforced/evidenced gate would not notice a swap"

    dropped = '<li>The work was done well</li><li>next</li>'
    assert STATUS.search(dropped, 0) is None, "the gate would not notice a status going missing"

    assert not (PERMITTED_LINKS >= {"/checkout/"}), "the link allowlist would admit a payment route"
