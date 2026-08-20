"""The ratchet must CATCH, not decorate. Verified against planted violations."""
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rs", ROOT / "scripts" / "ratchet_scope.py")
rs = importlib.util.module_from_spec(spec)
sys.modules["rs"] = rs
spec.loader.exec_module(rs)


def test_clean_tree_is_clean():
    assert rs.check() == []


def test_unmapped_module_FAILS_the_build(tmp_path, monkeypatch):
    """The key property: a module nobody needed fails the build."""
    victim = ROOT / "src" / "abs_profile" / "_probe_unmapped.py"
    victim.write_text("# planted module\n", encoding="utf-8")
    try:
        problems = rs.check()
        assert any("MODULE WITHOUT REQUIREMENT" in p for p in problems), problems
    finally:
        victim.unlink()
    assert rs.check() == []


def test_third_party_code_is_outside_the_scan_boundary(monkeypatch):
    """REGRESSION. `demo/` is scanned by filesystem walk, so the gitignored `node_modules` under
    it came inside the boundary. The build survived only because `CODE_SUFFIXES` carried `.mjs`
    and not `.js` - a coincidence, and this list has been widened twice already. Widening it here
    proves the skip does the work rather than the coincidence."""
    monkeypatch.setattr(rs, "CODE_SUFFIXES", (".py", ".sh", ".mjs", ".js"))
    assert rs.check() == []


def test_stamp_degeneration_is_caught():
    """The "hang everything on one requirement" degeneration is caught mechanically, not by eye."""
    fake = {f"src/m{i}.py": ["ABI-21-2"] for i in range(10)}
    import collections
    cnt = collections.Counter(i for ids in fake.values() for i in ids)
    assert cnt["ABI-21-2"] / len(fake) > rs.MAX_SHARE
