"""LAW-PHASE-THREE-NOTE-SYNCED. The ratchet must CATCH the two copies drifting apart, not decorate
agreement that already holds - the same discipline `tests/test_ratchet_staged_media.py` holds its
own subject to. Mutations run against the LIVE `SPEC.md` and are restored byte-for-byte in a
`finally`, per this project's own rule against leaving the tree damaged longer than an assertion
needs it.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rp3", ROOT / "scripts" / "ratchet_phase3_note.py")
rp3 = importlib.util.module_from_spec(spec)
sys.modules["rp3"] = rp3
spec.loader.exec_module(rp3)


def test_live_tree_is_clean():
    """SPEC.md carries at least two identical copies of the note today."""
    assert rp3.check() == []


def test_corrupting_one_copy_fails_the_build():
    """Changing a single word inside the SECOND marked copy must turn the build red - this is the
    mutation the operator's brief asked to be run before this phase closes."""
    original = rp3.SPEC.read_text(encoding="utf-8")
    try:
        blocks = rp3._blocks(original)
        assert len(blocks) >= 2, "fixture assumption: the live file carries at least two copies"
        # Corrupt only the SECOND occurrence of the note's text, leaving the first untouched -
        # a naive "does the phrase appear somewhere" check would still pass this.
        target = blocks[1]
        corrupted_inner = target.replace("Provider Catalog", "Contractor Marketplace", 1)
        assert corrupted_inner != target, "fixture assumption: the replaced phrase is present"
        first_end = original.find(rp3.END) + len(rp3.END)
        second_start = original.find(rp3.START, first_end)
        second_end = original.find(rp3.END, second_start)
        mutated = (
            original[: second_start + len(rp3.START)]
            + corrupted_inner
            + original[second_end:]
        )
        assert mutated != original
        rp3.SPEC.write_text(mutated, encoding="utf-8")
        problems = rp3.check()
        assert any("drifted apart" in p for p in problems), problems
    finally:
        rp3.SPEC.write_text(original, encoding="utf-8")
    assert rp3.check() == []


def test_deleting_down_to_one_copy_fails_the_build():
    """A note reduced to a single surviving copy - by deleting the other outright rather than
    editing it - must also be caught: the requirement is "at least two", not "no disagreement
    among however many remain"."""
    original = rp3.SPEC.read_text(encoding="utf-8")
    try:
        first_start = original.find(rp3.START)
        first_end = original.find(rp3.END, first_start) + len(rp3.END)
        second_start = original.find(rp3.START, first_end)
        second_end = original.find(rp3.END, second_start) + len(rp3.END)
        assert -1 not in (first_start, second_start)
        mutated = original[:second_start] + original[second_end:]
        assert len(rp3._blocks(mutated)) == 1
        rp3.SPEC.write_text(mutated, encoding="utf-8")
        problems = rp3.check()
        assert any("need at least 2" in p for p in problems), problems
    finally:
        rp3.SPEC.write_text(original, encoding="utf-8")
    assert rp3.check() == []
