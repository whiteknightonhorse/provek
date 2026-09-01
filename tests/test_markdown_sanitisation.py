"""The derived-markdown converter takes partly UNTRUSTED input, and has since 2026-08-31.

The accountability block renders four fields read from a SUBJECT'S OWN `provek.json`. Those fields
reach the prerendered page, and the page is what this converter reads. Until then its only input
was our own markup, and a single-pass tag strip was merely fragile; afterwards it is a question a
stranger gets to ask.

Removing `<script>` from `<scr<script>ipt>` in one pass RECONSTRUCTS the tag it just removed. That
is the whole of CodeQL's "incomplete multi-character sanitization", and it is why the strip repeats
until the text stops changing.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

PROBE = Path(__file__).parent / "sanitisation_probe.mjs"


@pytest.fixture(scope="module")
def out():
    if shutil.which("node") is None:
        pytest.skip("node is not on PATH")
    r = subprocess.run(["node", str(PROBE)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_a_reconstructed_script_tag_does_not_survive(out):
    """What must not survive is a COMPLETE tag - the thing a markdown reader could actually parse
    back into markup. `<scr` is a bare fragment: there is no closing `>`, so no tag can ever form
    from it, and this case's input is our own site markup, not a stranger's declaration. Demanding
    the fragment itself vanish was checking for a shape that was never dangerous."""
    md = out["reconstructed"]
    assert "<script" not in md.lower(), md


def test_a_reconstructed_comment_opener_does_not_survive(out):
    assert "<!--" not in out["comment"], out["comment"]


def test_nested_svg_leaves_no_open_tag(out):
    md = out["nested_svg"]
    assert "<svg" not in md.lower(), md
    assert "</svg>" not in md.lower(), md


def test_escaped_script_from_a_subject_declaration_stays_escaped(out):
    """THE REAL PATH: a subject's own `provek.json` holds this, React escapes it into the page,
    and this converter must never hand a live tag back from what arrived as entities."""
    md = out["escaped_from_a_declaration"]
    assert "<script" not in md.lower(), md
    assert "&lt;script&gt;" in md and "&lt;/script&gt;" in md, md


def test_escaped_img_from_a_subject_declaration_stays_escaped(out):
    md = out["escaped_img"]
    assert "<img" not in md.lower(), md
    assert "&lt;img" in md and "&gt;" in md, md


def test_a_tag_reconstructed_across_strip_categories_does_not_survive(out):
    """D-43, code-scanning alerts #76/#77. `strip()` chains four DIFFERENT regexes (comment,
    script/style/template, svg, sr-only) inside one loop rather than four separate ones, because
    they interact: removing `<script>y</script>` from `x<!<script>y</script>--z-->w` turns
    `<!` + `--z-->` into a freshly reconstructed `<!--z-->` - a comment the comment regex, having
    already run earlier in the SAME pass, will not see again until the loop repeats. Verified by
    hand: a copy of this chain with the surrounding loop deleted returns `<!--z-->w` for this input;
    the shipped, looped `strip()` returns `w`."""
    md = out["cross_category_reconstruction"]
    assert "<!--" not in md, md
    assert "<script" not in md.lower(), md


def test_the_probe_still_carries_the_words_around_the_attack(out):
    """THE CONTROL. A converter that answered "" to everything would pass every test above."""
    assert "before" in out["reconstructed"] and "after" in out["reconstructed"]
    assert "x" in out["nested_svg"] and "y" in out["nested_svg"]
    assert "x" in out["cross_category_reconstruction"] and "w" in out["cross_category_reconstruction"]
