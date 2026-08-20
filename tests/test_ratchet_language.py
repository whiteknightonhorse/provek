"""LAW-ENGLISH-ONLY-ON-GITHUB - the gate must actually catch non-English content."""
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rl", ROOT / "scripts" / "ratchet_language.py")
rl = importlib.util.module_from_spec(spec)
sys.modules["rl"] = rl
spec.loader.exec_module(rl)


def test_repository_is_english_only():
    """The whole tracked surface, excluding the named exemptions."""
    assert rl.check() == []


def test_the_gate_CATCHES_cyrillic():
    """A gate that cannot catch the thing it guards is decoration."""
    victim = ROOT / "src" / "_probe_lang.py"
    victim.write_text("# \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430\n", encoding="utf-8")
    import subprocess
    subprocess.run(["git", "add", str(victim)], cwd=ROOT, capture_output=True)
    try:
        problems = rl.check()
        assert any("_probe_lang" in p for p in problems), problems
    finally:
        subprocess.run(["git", "rm", "-f", "--quiet", str(victim)], cwd=ROOT, capture_output=True)
        victim.unlink(missing_ok=True)
    assert rl.check() == []


def test_exemptions_are_NAMED_not_silent():
    """A checker that silently skips what it does not understand reports success on it."""
    assert rl.EXEMPT_PATHS
    assert rl.EXEMPT_REASON
    assert "evidence/" in rl.EXEMPT_PATHS


def test_commit_messages_are_part_of_the_github_surface():
    """The rule covers what people read on GitHub, and that includes commit messages."""
    assert callable(rl.check_commit_messages)
