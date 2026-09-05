"""LAW-TEMPLATE-NAMES-NO-INSTRUMENT (ADR-0011, D-57) - the two-direction gate that replaces a
second repository for AI agent templates.

Direction 1: an artefact under templates/<slug>/ never names this instrument (the vocabulary a
template is about a THIRD PARTY's business agent, never about Provek). Direction 2: no file under
src/ or scripts/ references the templates/ path, so the scorer's inputs stay what they have always
been - evidence read from the subject's own repository.

Phase 0 ships this gate against ZERO real templates (templates/SCHEMA.md, D-18's precedent). Control
before trust (CLAUDE.md invariant 5): both directions are proven able to fail, against a planted
fixture, before either is trusted against the real (currently empty) tree.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "templates_vocabulary"

FORBIDDEN = [
    r"provek",
    r"passport",
    r"registry",
    r"verif\w*",
    r"\bL[0-5]\b",
    r"autonomy level",
    r"projection",
    r"evidence window",
    r"\bscore\b",
]
VOCAB_PATTERN = re.compile("|".join(FORBIDDEN), re.IGNORECASE)
TEMPLATES_PATH_PATTERN = re.compile(r"""['"](\.\./)?templates/""")


def _artefact_files(templates_root: Path) -> list[Path]:
    """SKILL.md and references/ under every slug directory - never README.md/SCHEMA.md/LICENSE
    at the templates/ root, which are the instrument's own contract about templates and are
    allowed to name it, the same way the repository's root LICENSE names src/ without being code.
    """
    if not templates_root.exists():
        return []
    files: list[Path] = []
    for slug_dir in sorted(p for p in templates_root.iterdir() if p.is_dir()):
        skill = slug_dir / "SKILL.md"
        if skill.exists():
            files.append(skill)
        refs = slug_dir / "references"
        if refs.exists():
            files.extend(f for f in sorted(refs.rglob("*")) if f.is_file())
    return files


def find_instrument_vocabulary(templates_root: Path) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for f in _artefact_files(templates_root):
        text = f.read_text(encoding="utf-8")
        found = sorted({m.group(0).lower() for m in VOCAB_PATTERN.finditer(text)})
        if found:
            hits[str(f.relative_to(templates_root))] = found
    return hits


def find_templates_path_references(*bases: Path) -> list[str]:
    hits = []
    for base in bases:
        if not base.exists():
            continue
        for f in sorted(base.rglob("*")):
            if f.is_file() and f.suffix in (".py", ".sh", ".mjs"):
                text = f.read_text(encoding="utf-8", errors="replace")
                if TEMPLATES_PATH_PATTERN.search(text):
                    hits.append(str(f))
    return hits


# --- control: the checker must be shown catching a real violation before it is trusted -------

def test_the_vocabulary_checker_catches_a_planted_violation():
    hits = find_instrument_vocabulary(FIXTURES / "bad")
    assert hits, "a planted 'Provek' / 'passport' mention in the bad fixture was not caught"


def test_the_vocabulary_checker_passes_a_clean_fixture():
    hits = find_instrument_vocabulary(FIXTURES / "good")
    assert not hits, f"a violation-free fixture was flagged: {hits}"


def test_the_templates_path_checker_catches_a_planted_violation(tmp_path):
    planted_src = tmp_path / "src"
    planted_src.mkdir()
    (planted_src / "leak.py").write_text(
        "TEMPLATES_DIR = 'templates/customer-support-agent'\n", encoding="utf-8"
    )
    hits = find_templates_path_references(planted_src)
    assert hits, "a planted reference to the templates/ path in src/ was not caught"


def test_the_templates_path_checker_passes_a_clean_fixture(tmp_path):
    planted_src = tmp_path / "src"
    planted_src.mkdir()
    (planted_src / "clean.py").write_text("VALUE = 'unrelated'\n", encoding="utf-8")
    assert find_templates_path_references(planted_src) == []


# --- the real tree ------------------------------------------------------------------------

def test_no_real_template_names_the_instrument():
    """Phase 0 ships zero templates (templates/SCHEMA.md); this stays armed as templates land."""
    hits = find_instrument_vocabulary(TEMPLATES)
    assert not hits, f"template(s) name the instrument: {hits}"


def test_no_source_file_references_the_templates_path():
    hits = find_templates_path_references(ROOT / "src", ROOT / "scripts")
    assert not hits, f"instrument code references the templates/ path: {hits}"
