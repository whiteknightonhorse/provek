"""LAW-METHOD-STATES-THE-CODED-RULES - /method/ carries the numbers the code runs (D-74), and the six
NotMeasured states appear on the page and in the note.

Reads the constants from the code and asserts the page text carries their values, so editing a
constant without the page (or the page without the constant) is red.
"""
import re
from pathlib import Path

from src.abs_profile.ladder import FEW_AUTHORS_FOR_L3, SIGNED_SHARE_FOR_L4
from src.abs_profile.measured import NotMeasured
from src.collector.github import COMMIT_PAGE_CEILING, COMMITS_PER_PAGE, EVIDENCE_WINDOW_DAYS

ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "web" / "src" / "pages" / "Method.tsx").read_text(encoding="utf-8")
NOTE = (ROOT / "web" / "notes" / "src" / "not-measured-is-not-zero.md").read_text(encoding="utf-8")


def _text(tsx: str) -> str:
    """Rendered-ish text: tags dropped, JSX whitespace collapsed, entities left alone."""
    no_comments = re.sub(r"\{/\*.*?\*/\}", " ", tsx, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", no_comments))


def _rules_section() -> str:
    t = _text(PAGE)
    assert "Rules as coded" in t, "the page has no 'Rules as coded' section"
    return t.split("Rules as coded")[1].split("Open items")[0]


def test_the_page_carries_the_values_of_the_constants():
    rules = _rules_section()
    assert f"at most {FEW_AUTHORS_FOR_L3} attributed identities" in rules
    assert f"at least {round(SIGNED_SHARE_FOR_L4 * 100)} % of commits signed" in rules
    assert f"last {EVIDENCE_WINDOW_DAYS} days" in rules
    ceiling = f"{COMMIT_PAGE_CEILING * COMMITS_PER_PAGE:,}".replace(",", " ")
    assert f"more than {ceiling} commits" in rules


def test_the_page_states_the_floor_the_unreachable_level_and_the_limiters():
    rules = _rules_section()
    for needle in ("L2: no evidence above L2", "L5 is unreachable", "O1:", "O2:",
                   "O3: implemented in the scorer, not exercised in production"):
        assert needle in rules, needle


def test_the_page_defines_the_runtime_trace_as_a_scheduled_run_in_the_window():
    """T-0570: O2 reads workflow runs started by `schedule` inside the window, not lifetime runs."""
    assert "a runtime trace is a workflow run started by schedule inside the window" in _rules_section()


def test_open_items_no_longer_lists_what_the_rules_section_closes():
    open_items = _text(PAGE).split("Open items")[1]
    for gone in ("the rules for L0, L1, L2 and L5", "the full list of limiters O1-O3",
                 "whether any level above L4 is reachable"):
        assert gone not in open_items, gone


def test_every_not_measured_state_is_on_the_page_and_in_the_note():
    for state in NotMeasured:
        assert state.value in PAGE, f"{state.value} missing from Method.tsx"
        assert state.value in NOTE, f"{state.value} missing from the note"


def test_the_note_title_and_body_agree_on_the_count():
    head, body = NOTE.split("\n---\n", 1)
    assert "Six Ways" in head and "Six states" in head
    assert "Four" not in head and "three reasons" not in body and "Three states, not a blank" not in body
