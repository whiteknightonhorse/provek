"""T-IN-06 - the slug rule is one rule written four times, and the four are compared byte for byte.

`web/src/slug.js` is the source. `brief.js`, `badge/[id].js` and `api/apply/[id].js` are Pages
Functions and mirror it rather than import across the bundle boundary. A rule written four times
drifts: before this task three copies said `^[A-Za-z0-9_-]+$` while `slugOf` (web/discovery.mjs)
kept the `.`, so a repository named `a.b` had a passport page and no brief or badge.

Asserted against the source TEXT of the `const SLUG = ...;` line, because the Functions are not
importable for this constant. The behaviour of the rule is run, not read, in
`tests/test_dotted_slug_reaches_its_brief.py`.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ROOT / "web" / "src" / "slug.js",
    ROOT / "web" / "functions" / "p" / "[id]" / "brief.js",
    ROOT / "web" / "functions" / "badge" / "[id].js",
    ROOT / "web" / "functions" / "api" / "apply" / "[id].js",
]


def slug_lines(path: Path) -> list[str]:
    return re.findall(r"^const SLUG = .*;$", path.read_text(encoding="utf-8"), re.M)


def test_each_source_defines_the_rule_exactly_once() -> None:
    for path in SOURCES:
        assert len(slug_lines(path)) == 1, f"{path} must hold exactly one `const SLUG = ...;` line"


def test_the_four_copies_are_byte_identical() -> None:
    lines = {str(p.relative_to(ROOT)): slug_lines(p)[0] for p in SOURCES}
    assert len(set(lines.values())) == 1, f"the slug rule has drifted between its copies: {lines}"


def test_the_rule_is_the_one_the_task_set() -> None:
    assert slug_lines(SOURCES[0])[0] == r"const SLUG = /^(?!.*\.\.)[A-Za-z0-9_][A-Za-z0-9_.-]*$/;"
