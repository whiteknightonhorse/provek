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


# ── Binary admission is by evidence, not by name ──────────────────────────────────────────────
#
# The gate reads every tracked file as UTF-8 and refuses what it cannot read. Shipping the
# favicon rasters made that refuse the push, correctly: it could not check them. The fix admits
# binary formats — and the danger of any such fix is that it turns "I could not read this" into
# "this is fine", which is the exact shape this project keeps paying for.
#
# So admission is proven from the file's own first bytes. These tests exist to keep it that way:
# the second one fails if anyone ever relaxes the check to trust the suffix.

def test_a_real_png_is_admitted_because_its_bytes_say_so(tmp_path):
    from scripts.ratchet_language import proven_binary
    f = tmp_path / "mark.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
    assert proven_binary(f) is True


def test_cyrillic_prose_named_png_is_still_refused(tmp_path):
    """A suffix is a claim the file makes about itself. This gate does not take claims."""
    from scripts.ratchet_language import proven_binary
    f = tmp_path / "notes.png"
    # Cyrillic prose in cp1251, written as escapes rather than as letters. Spelling it out would
    # put Cyrillic into a tracked file and the English-only gate would catch THIS test — the same
    # self-capture the CYRILLIC pattern in the gate documents having already paid for once.
    f.write_bytes(b"\xfd\xf2\xee \xed\xe5 \xea\xe0\xf0\xf2\xe8\xed\xea\xe0")
    assert proven_binary(f) is False, (
        "a file was admitted on the strength of its extension; undecodable prose would now pass "
        "the English-only gate by being renamed")


def test_an_unknown_binary_format_is_not_admitted(tmp_path):
    from scripts.ratchet_language import proven_binary
    f = tmp_path / "blob.dat"
    f.write_bytes(b"\x00\x01\x02\x03")
    assert proven_binary(f) is False


def test_the_shipped_icons_are_what_they_claim(tmp_path):
    """The live artefacts, not a fixture: these are the files that made the gate refuse."""
    import pathlib

    from scripts.ratchet_language import ROOT, proven_binary
    for name in ("favicon.ico", "apple-touch-icon.png", "icon-192.png", "icon-512.png"):
        p = pathlib.Path(ROOT) / "web/public" / name
        assert p.is_file(), f"{name} is missing"
        assert proven_binary(p) is True, f"{name} does not match the format its name claims"
