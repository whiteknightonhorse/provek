"""LAW-STAGED-MEDIA-LANDING-ONLY, the enforcing half of D-42. The ratchet must CATCH a violation,
not decorate one - the same discipline `tests/test_ratchet_evidence.py` holds its own subject to.

The load-bearing mutation test writes a real `<video>` tag into the LIVE `web/src/pages/Passport.tsx`
- an evidence surface D-42 says the exception cannot reach - runs the check, asserts it goes red,
and restores the file's exact original bytes in a `finally` before the test can complete either way.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rsm", ROOT / "scripts" / "ratchet_staged_media.py")
rsm = importlib.util.module_from_spec(spec)
sys.modules["rsm"] = rsm
spec.loader.exec_module(rsm)


def test_live_tree_is_clean():
    """No media asset exists yet (the boundary this task runs under forbids committing one), so
    the live tree must report clean today."""
    assert rsm.check() == []


def test_a_video_in_an_evidence_page_FAILS_the_build():
    """The key property: a <video> referencing web/public/media/ dropped into Passport.tsx - a
    named evidence surface - must turn the build red, not pass by default. Mutates the REAL file
    and restores it byte-for-byte in `finally`, per the task's own instruction not to leave the
    tree damaged longer than the assertion needs it."""
    victim = rsm.EVIDENCE_FILES[0]
    assert victim.name == "Passport.tsx"
    original = victim.read_text(encoding="utf-8")
    try:
        mutated = original + '\n<video src="/media/order-1.mp4" />\n'
        victim.write_text(mutated, encoding="utf-8")
        problems = rsm.check()
        assert any("Passport.tsx" in p and "predicate 4" in p for p in problems), problems
    finally:
        victim.write_text(original, encoding="utf-8")
    assert rsm.check() == []


def test_a_video_on_a_page_thats_neither_landing_nor_a_named_evidence_page_still_fails():
    """Apply.tsx is neither Landing.tsx nor one of the five named evidence surfaces, and must still
    be caught by the generic branch - the exception is scoped to Landing.tsx by inclusion, not to
    the five evidence files by exclusion."""
    victim = ROOT / "web" / "src" / "pages" / "Apply.tsx"
    assert victim not in rsm.EVIDENCE_FILES and victim != rsm.LANDING
    original = victim.read_text(encoding="utf-8")
    try:
        victim.write_text(original + '\n<img src="/media/still.png" />\n', encoding="utf-8")
        problems = rsm.check()
        assert any("Apply.tsx" in p and "outside Landing.tsx" in p for p in problems), problems
    finally:
        victim.write_text(original, encoding="utf-8")
    assert rsm.check() == []


def test_a_staged_video_on_landing_with_its_caption_passes():
    """The admitted case: Landing.tsx may carry a /media/ reference IF the staged-scene caption is
    also on the page - proving the gate does not simply ban every reference outright."""
    victim = rsm.LANDING
    original = victim.read_text(encoding="utf-8")
    try:
        addition = (
            '\n<video src="/media/order-1.mp4" />'
            '\n<p>Staged scene — an illustration, not a measurement.</p>\n'
        )
        victim.write_text(original + addition, encoding="utf-8")
        problems = rsm.check()
        assert not any("Landing.tsx" in p for p in problems), problems
    finally:
        victim.write_text(original, encoding="utf-8")
    assert rsm.check() == []


def test_a_video_on_landing_without_the_caption_fails(tmp_path, monkeypatch):
    """Predicate 3 has teeth: a /media/ reference with no staged-scene caption is refused.

    This used to append a <video> to the REAL Landing.tsx and expect a violation. That fixture
    expired the moment the feature shipped: once the live file carries the caption, an appended
    video inherits it, no violation is produced, and a test named for the caption-less case stops
    exercising it while still passing as long as nobody looks. It also wrote to a production source
    file mid-run, so a crash between the write and the restore left the tree corrupt.

    The tree is now BUILT, so the test measures the rule instead of the repository's contents.
    Every path the module derives - ROOT included, since it formats `relative_to(ROOT)` into the
    message - is redirected, or the synthetic file is not under the root the module reports against.
    """
    src = tmp_path / "web" / "src" / "pages"
    src.mkdir(parents=True)
    landing = src / "Landing.tsx"
    monkeypatch.setattr(rsm, "ROOT", tmp_path)
    monkeypatch.setattr(rsm, "WEB_SRC", tmp_path / "web" / "src")
    monkeypatch.setattr(rsm, "WEB_FUNCTIONS", tmp_path / "web" / "functions")
    monkeypatch.setattr(rsm, "LANDING", landing)
    monkeypatch.setattr(rsm, "EVIDENCE_FILES", ())

    landing.write_text('<video src="/media/order-1.mp4" />\n', encoding="utf-8")
    problems = rsm.check()
    assert any("Landing.tsx" in p and "predicate 3" in p for p in problems), problems

    # ... and the SAME file with the caption is accepted, so the assertion above is about the
    # caption and not merely about the presence of a media reference.
    landing.write_text(
        '<video src="/media/order-1.mp4" />\n' + rsm.STAGED_CAPTION + "\n", encoding="utf-8"
    )
    assert rsm.check() == []


def test_the_badge_embed_snippet_in_passport_is_not_a_false_positive():
    """Passport.tsx already contains a literal `<img src="${badgeUrl}">` string (a copy-paste
    snippet shown to the user, pointing at /badge/<slug>.svg) - the live-clean assertion above
    already proves this, but the intent is named here so a future edit to the regex is judged
    against it explicitly rather than only by an assertion elsewhere going red."""
    text = rsm.EVIDENCE_FILES[0].read_text(encoding="utf-8")
    assert "badgeUrl" in text
    assert not rsm.MEDIA_REF_RE.search(text)
