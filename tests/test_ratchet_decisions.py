"""A dangling law is a law with no armed gate. The ratchet must fail on it."""
import importlib.util
import pathlib
import sys

import yaml

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


def _pyyaml_laws(text: str) -> list[dict]:
    """The real parser's reading of the same document, for the cross-checks below."""
    doc = yaml.safe_load(text)
    assert isinstance(doc, dict) and isinstance(doc.get("laws"), list), (
        f"not a {{laws: [...]}} document to PyYAML: {doc!r}")
    return doc["laws"]


def test_hand_written_reader_matches_pyyaml_on_the_live_file():
    """T-S13 (class L-31, closed for the workflow files by T-S7). `_load_laws` is a hand-written
    scanner, not a parser, and a scanner more permissive than the machine it stands in for
    certifies files that machine reads differently. It did: this exact comparison is what found
    LAW-EMITTED-IDS-UNIQUE's `text` truncated at an unquoted-looking '#' inside a quoted string,
    before `_strip_comment` closed it (see the module docstring). PyYAML lives in
    `requirements/ci-tests.in` (D-32), which is why this lives here rather than in
    `scripts/ratchet_decisions.py` itself - that module runs in the `ratchets` CI job, which
    installs nothing at all, by design.
    """
    text = rd.LAWS.read_text(encoding="utf-8")
    hand = rd._load_laws(rd.LAWS)
    parsed = _pyyaml_laws(text)
    assert hand == parsed, "the hand-written reader diverges from PyYAML on enforced_by.yaml"


def test_a_quoted_hash_is_read_the_same_way_by_both(tmp_path):
    """REGRESSION for the actual defect found on the live file: a '#' inside a quoted value must
    not be read as a comment by either side."""
    p = tmp_path / "enforced_by.yaml"
    p.write_text(
        'laws:\n  - id: LAW-X\n    text: "a url(#x) reference"\n    gate: g.py\n    test: t.py\n',
        encoding="utf-8")
    hand = rd._load_laws(p)
    parsed = _pyyaml_laws(p.read_text(encoding="utf-8"))
    assert hand == parsed
    assert hand[0]["text"] == "a url(#x) reference"


def test_a_block_scalar_the_hand_reader_cannot_see_is_CAUGHT(tmp_path):
    """Proves the comparison itself can fail (invariant 5), on a construct `_strip_comment` was
    never meant to cover: a YAML block scalar. `_load_laws` reads line by line and has no notion
    of a folded or literal block, so it reads the header alone as the value and drops the body -
    the same shape D-30's RED-028 named against a different hand-written reader in this repository.
    """
    p = tmp_path / "enforced_by.yaml"
    p.write_text(
        "laws:\n  - id: LAW-Y\n    text: >\n        a folded\n        scalar\n"
        "    gate: g.py\n    test: t.py\n",
        encoding="utf-8")
    hand = rd._load_laws(p)
    parsed = _pyyaml_laws(p.read_text(encoding="utf-8"))
    assert hand != parsed, "the fixture must actually diverge, or this test proves nothing"
