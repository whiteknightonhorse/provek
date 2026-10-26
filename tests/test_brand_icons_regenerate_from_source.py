"""Every shipped icon is the render of web/public/brand/provek-mark.svg, and nothing else.

Edit the SVG, run `python3 scripts/build_brand_icons.py`; a hand-edited raster, or an SVG changed
without regenerating, fails here.
"""
from PIL import Image, ImageChops

from scripts import build_brand_icons as b

PUBLIC = b.PUBLIC


def _same(a: Image.Image, c: Image.Image, tol: int = 0) -> bool:
    diff = ImageChops.difference(a.convert("RGBA"), c.convert("RGBA"))
    return max(hi for _, hi in diff.getextrema()) <= tol


def test_favicon_svg_is_the_source_byte_for_byte():
    assert (PUBLIC / "favicon.svg").read_bytes() == b.SOURCE.read_bytes()


def test_rasters_are_renders_of_the_source():
    for name, size in (("apple-touch-icon.png", 180), ("icon-192.png", 192), ("icon-512.png", 512)):
        assert _same(Image.open(PUBLIC / name), b.render(size)), f"{name} is stale against the SVG"


def test_favicon_ico_carries_16_32_48_of_the_source():
    ico = Image.open(PUBLIC / "favicon.ico")
    assert ico.ico.sizes() == {(16, 16), (32, 32), (48, 48)}
    for s in (16, 32, 48):
        assert _same(ico.ico.getimage((s, s)), b.render(48).resize((s, s), Image.LANCZOS), tol=24), f"{s}px entry is stale"


def test_the_mark_uses_exactly_three_colours():
    svg = b.SOURCE.read_text()
    assert sorted(set(__import__("re").findall(r'fill="(#[0-9a-f]{6})"', svg))) == ["#0f1115", "#4ade80", "#e8e6df"]
