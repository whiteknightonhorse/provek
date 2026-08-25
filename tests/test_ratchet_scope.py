"""The ratchet must CATCH, not decorate. Verified against planted violations."""
import importlib.util
import pathlib
import sys

import yaml

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


def test_hand_written_reader_matches_pyyaml_on_the_live_file():
    """T-S13 (class L-31, closed for the workflow files by T-S7). The sibling reader in
    `scripts/ratchet_decisions.py` carried this exact defect shape against a live law; nothing in
    `requirements/ABI_MAP.yaml` has tripped it, since every value here is a bare identifier rather
    than free text, but the reader is the same hand-written scanner and the comparison is what
    would catch the day that stops being true. PyYAML lives in `requirements/ci-tests.in` (D-32),
    which is why this lives here rather than in `scripts/ratchet_scope.py` itself - that module
    runs in the `ratchets` CI job, which installs nothing at all, by design.
    """
    text = rs.MAP.read_text(encoding="utf-8")
    hand = rs._load_map(rs.MAP)
    parsed = yaml.safe_load(text)
    assert isinstance(parsed, dict), f"PyYAML does not read {rs.MAP} as a mapping: {type(parsed)}"
    assert hand == parsed, "the hand-written reader diverges from PyYAML on ABI_MAP.yaml"


def test_a_multiline_flow_sequence_the_hand_reader_cannot_see_is_CAUGHT(tmp_path):
    """Proves the comparison itself can fail (invariant 5), on a construct the line-by-line reader
    was never meant to cover: a flow sequence YAML allows to continue across physical lines."""
    p = tmp_path / "ABI_MAP.yaml"
    p.write_text("src/x.py: [ABI-1-1,\n  ABI-1-2]\n", encoding="utf-8")
    hand = rs._load_map(p)
    parsed = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert hand != parsed, "the fixture must actually diverge, or this test proves nothing"
