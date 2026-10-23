"""T-IN-03 (D-69) - the form promises a status, not a clock.

`Apply.tsx` said the entry appears "within about fifteen minutes". Nothing on the other side
keeps that clock: GitHub's public interface is shared and rate-limited, and a deferred request
waits for it. The page now says the run is automatic, usually publishes within the hour, can take
longer, and links to the request's own status page. A promise nothing keeps is the defect this
project exists to find, so the page may not make it.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / "web" / "src" / "pages" / "Apply.tsx"
STATUS = ROOT / "web" / "src" / "pages" / "ApplyStatus.tsx"


def _code(path: Path) -> str:
    """The rendered text, without the comments that explain what used to be there."""
    s = path.read_text(encoding="utf-8")
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r"\{/\*.*?\*/\}", "", s, flags=re.S)
    return re.sub(r"(?m)^\s*//[^\n]*", "", s)


def test_the_form_promises_no_clock() -> None:
    text = re.sub(r"\s+", " ", _code(FORM)).lower()
    for phrase in ("fifteen minutes", "15 min"):
        assert phrase not in text, f"Apply.tsx still promises a clock: {phrase!r}"


def test_the_form_links_to_the_requests_own_status() -> None:
    text = re.sub(r"\s+", " ", _code(FORM))
    assert "Check this request" in text, "the confirmation has no link to the status page"
    assert "/apply/status/?id=" in text, "the link does not carry the request's id"


def test_the_status_page_exists_and_reads_the_endpoint() -> None:
    assert STATUS.is_file(), "web/src/pages/ApplyStatus.tsx is missing"
    code = _code(STATUS)
    assert "/api/apply/" in code and "no-store" in code
