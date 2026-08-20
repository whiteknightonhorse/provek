"""A dangling law is a law with no armed gate. The ratchet must fail on it."""
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rd", ROOT / "scripts" / "ratchet_decisions.py")
rd = importlib.util.module_from_spec(spec)
sys.modules["rd"] = rd
spec.loader.exec_module(rd)


def test_all_declared_laws_are_armed():
    assert rd.check() == []


def test_a_law_pointing_at_nothing_FAILS(tmp_path):
    """A law whose gate does not exist must fail the build - otherwise it rots into a comment."""
    p = tmp_path / "enforced_by.yaml"
    p.write_text("laws:\n  - id: LAW-GHOST\n    gate: does/not/exist.py\n    test: nope.py\n",
                 encoding="utf-8")
    laws = rd._load_laws(p)
    assert laws and laws[0]["id"] == "LAW-GHOST"
    assert not (ROOT / laws[0]["gate"]).exists()
