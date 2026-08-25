"""LAW-EVIDENCE-STAMPED-TREE, the enforcing half. The ratchet must CATCH, not decorate -
verified against a planted violation, the same discipline `tests/test_ratchet_scope.py` and
`tests/test_ratchet_decisions.py` hold their own subjects to.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("re_", ROOT / "scripts" / "ratchet_evidence.py")
re_ = importlib.util.module_from_spec(spec)
sys.modules["re_"] = re_
spec.loader.exec_module(re_)

sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp as es  # noqa: E402


def test_live_evidence_directory_is_clean():
    assert re_.check() == []


def test_an_unstamped_file_FAILS_the_build():
    """The key property: a new file dropped into evidence/ with no stamp, and not legacy-listed,
    must make the build red rather than pass by default."""
    victim = ROOT / "evidence" / "_probe_unstamped.txt"
    victim.write_text("no provenance line anywhere in this file\n", encoding="utf-8")
    try:
        problems = re_.check()
        assert any("_probe_unstamped.txt" in p and "no 'tree:" in p for p in problems), problems
    finally:
        victim.unlink()
    assert re_.check() == []


def test_a_stamped_file_PASSES():
    victim = ROOT / "evidence" / "_probe_stamped.txt"
    victim.write_text(f"# a fixture\n{es.tree_stamp()}\n", encoding="utf-8")
    try:
        problems = re_.check()
        assert not any("_probe_stamped.txt" in p for p in problems), problems
    finally:
        victim.unlink()


def test_a_stamp_past_the_header_window_does_not_count():
    """The stamp must be in the header, not "anywhere in the file" - a 600-line red-run transcript could
    otherwise contain the literal string `tree:` deep inside quoted tool output and pass by
    accident."""
    victim = ROOT / "evidence" / "_probe_late_stamp.txt"
    body = "\n".join(f"filler line {i}" for i in range(re_.HEADER_LINES + 5))
    victim.write_text(f"{body}\n{es.tree_stamp()}\n", encoding="utf-8")
    try:
        problems = re_.check()
        assert any("_probe_late_stamp.txt" in p for p in problems), problems
    finally:
        victim.unlink()


def test_legacy_files_are_exempt_even_though_none_of_them_are_stamped():
    legacy = re_._legacy()
    assert legacy, "the legacy list must not be empty on this tree"
    sampled = list(legacy)[:5]
    for name in sampled:
        path = ROOT / "evidence" / name
        assert path.exists(), f"{name} is named in the legacy list but is not in evidence/"
    problems = re_.check()
    assert not any(name in p for name in sampled for p in problems)


def test_generator_scripts_are_not_themselves_required_to_carry_a_stamp():
    """`*-generator.py` is code that PRODUCES an artefact, not the artefact - the requirement
    binds what a reader receives as evidence, not the tool that made it (mirrors ratchet_scope's
    own separation between code and its output)."""
    a_generator = ROOT / "evidence" / "RED-039-generator.py"
    assert a_generator.exists()
    assert a_generator.name not in re_._legacy()
    problems = re_.check()
    assert not any("RED-039-generator.py" in p for p in problems)


def test_directories_under_evidence_are_skipped_not_flagged():
    problems = re_.check()
    assert not any("__pycache__" in p for p in problems)
    assert not any("TAINTED-SUDO-CORPUS" in p for p in problems)


def test_legacy_list_is_named_not_a_pattern():
    """CLAUDE.md's `.gitignore` doctrine: no templated exemption. Every legacy entry must be a
    literal filename that exists today, not a glob."""
    for name in re_._legacy():
        assert "*" not in name and "?" not in name, f"{name} looks like a pattern, not a filename"
