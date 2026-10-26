"""T-0546 - the Documentation law stands in CLAUDE.md once and whole, and every surface it names exists.

FLEET-DOCS-LAW-1026 sections 1-3 are enforced by the task engine's `DOCS:` pre-flight and reviewer
clause (`~/taskloop/lib/docs-law.sh`), which live outside this tree: a clone cannot judge a card,
as it cannot judge a rollback (D-29). What a clone CAN judge is the law's own failure mode - a
document about documentation that went stale. Rename `docs/WHY_GET_VERIFIED.md` or a permanent
check and section 4 lies; this test turns that red.

WHAT IS NOT ASSERTED: the routes section 4 lists (`/registry/`, `/method/`, `/build/*`, ...) and
`/data/registry.json` are served paths, not files in this tree, and are not checked. Nor is the
wording of sections 1-3 beyond their opening labels; the engine owns their meaning.

No skipif: an unreadable CLAUDE.md is an assertion failure, never a skip.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HEADING = "# Documentation law (FLEET-DOCS-LAW-1026"
ORDER = (
    "1. Same card.",
    "2. Read before write.",
    "3. Proof.",
    "4. Surfaces of this project.",
    "Provek (whiteknightonhorse/provek",
)

# (token as written in section 4, glob from the root that must match at least one file)
SURFACES = (
    ("web/public/**", "web/public/*"),
    ("web/public/llms.txt", "web/public/llms.txt"),
    ("web/public/.well-known/agent-registration.json", "web/public/.well-known/agent-registration.json"),
    ("scripts/cohort.py", "scripts/cohort.py"),
    ("README.md", "README.md"),
    ("SPEC.md", "SPEC.md"),
    ("DECISIONS.md", "DECISIONS.md"),
    ("docs/**", "docs/*.md"),
    ("WHY_GET_VERIFIED", "docs/WHY_GET_VERIFIED.md"),
    ("INTAKE_OPERATIONS", "docs/INTAKE_OPERATIONS.md"),
    ("LIVENESS_OPERATIONS", "docs/LIVENESS_OPERATIONS.md"),
    ("ALERT_TRIAGE", "docs/ALERT_TRIAGE.md"),
    ("MEASUREMENT_*", "docs/MEASUREMENT_*.md"),
    ("adr/", "docs/adr/ADR-*.md"),
    ("PRODUCT.md", "PRODUCT.md"),
    ("DESIGN.md", "DESIGN.md"),
    ("SECURITY.md", "SECURITY.md"),
    ("provek.json", "provek.json"),
    ("integrations/*/README.md", "integrations/*/README.md"),
    ("test_readme_fragment_is_verbatim", "tests/test_readme_fragment_is_verbatim.py"),
    ("test_brief_copy_matches_passport_page", "tests/test_brief_copy_matches_passport_page.py"),
    ("test_apply_*", "tests/test_apply_*.py"),
    ("scripts/dated_promises.py", "scripts/dated_promises.py"),
    ("enforced_by.yaml", "enforced_by.yaml"),
    ("web/src", "web/src/pages/*.tsx"),
)


def _section(text: str) -> str:
    lines = text.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith(HEADING))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("#")), len(lines))
    return "\n".join(lines[start:end])


def check(root: Path, claude_md: Path) -> list[str]:
    """Violations, empty when the law stands once and whole and every named surface exists."""
    problems: list[str] = []
    text = claude_md.read_text(encoding="utf-8")
    n = sum(1 for ln in text.splitlines() if ln.startswith(HEADING))
    if n != 1:
        return [f"heading '{HEADING}' appears {n} times, expected exactly 1"]
    section = _section(text)
    pos = -1
    for label in ORDER:
        at = section.find(label, pos + 1)
        if at < 0:
            problems.append(f"section lacks '{label}' after offset {pos}")
        else:
            pos = at
    for token, pattern in SURFACES:
        if not re.search(re.escape(token) + r"(?![A-Za-z0-9_])", section):
            problems.append(f"section 4 no longer names '{token}'")
        if not list(root.glob(pattern)):
            problems.append(f"'{token}' is named but {pattern} matches nothing")
    return problems


def _mirror(dst: Path, skip: str | None = None) -> None:
    """Symlink every file the table's globs match under `dst`, except the one named `skip`."""
    for _, pattern in SURFACES:
        for f in ROOT.glob(pattern):
            rel = f.relative_to(ROOT)
            if skip and rel.as_posix() == skip:
                continue
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.symlink_to(f)


def _claude_copy(tmp_path: Path) -> Path:
    dst = tmp_path / "CLAUDE.md"
    shutil.copy2(ROOT / "CLAUDE.md", dst)
    return dst


def test_the_law_stands_once_and_every_surface_exists():
    claude = ROOT / "CLAUDE.md"
    assert claude.is_file(), "CLAUDE.md is unreadable"
    assert check(ROOT, claude) == []


def test_a_dropped_surface_token_turns_red(tmp_path):
    copy = _claude_copy(tmp_path)
    copy.write_text(copy.read_text(encoding="utf-8").replace("web/public/llms.txt", "web/public/x", 1),
                    encoding="utf-8")
    assert any("web/public/llms.txt" in p for p in check(ROOT, copy))


def test_a_duplicated_heading_turns_red(tmp_path):
    copy = _claude_copy(tmp_path)
    text = copy.read_text(encoding="utf-8")
    copy.write_text(text + "\n" + HEADING + ")\n", encoding="utf-8")
    assert any("expected exactly 1" in p for p in check(ROOT, copy))


def test_a_renamed_permanent_check_turns_red(tmp_path):
    copy = _claude_copy(tmp_path)
    copy.write_text(
        copy.read_text(encoding="utf-8").replace(
            "test_readme_fragment_is_verbatim", "test_readme_fragment_is_verbatim2", 1),
        encoding="utf-8",
    )
    assert any("test_readme_fragment_is_verbatim" in p for p in check(ROOT, copy))


def test_a_missing_surface_file_turns_red(tmp_path):
    root = tmp_path / "tree"
    root.mkdir()
    _mirror(root, skip="docs/ALERT_TRIAGE.md")
    problems = check(root, ROOT / "CLAUDE.md")
    assert problems and all("ALERT_TRIAGE" in p for p in problems)
