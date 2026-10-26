"""Regenerate every Provek icon from the one source, web/public/brand/provek-mark.svg.

    python3 scripts/build_brand_icons.py

Writes web/public/{favicon.svg,favicon.ico,apple-touch-icon.png,icon-192.png,icon-512.png}.
The agent-registration.json `image` is apple-touch-icon.png, so it follows this script too.
No SVG library is needed: the source is restricted to <rect> and <path> with absolute
M/L/H/V/A/Z commands (circular arcs), which is all the mark uses; anything else raises.
"""
from __future__ import annotations

import math
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "web" / "public"
SOURCE = PUBLIC / "brand" / "provek-mark.svg"
SS = 4  # supersampling factor
TOKEN = re.compile(r"([MLHVAZ])|(-?\d*\.?\d+)")


def _hex(value: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError(f"fill must be #rrggbb, got {value!r}")
    return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]


def _arc(p0, r, large, sweep, p1, steps=64):
    """Flatten an SVG circular arc (rx == ry, no rotation) from p0 to p1."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = (x0 - x1) / 2, (y0 - y1) / 2
    d2 = dx * dx + dy * dy
    r = max(r, math.sqrt(d2))
    k = math.sqrt(max(0.0, (r * r - d2) / d2)) * (-1 if large == sweep else 1)
    cx, cy = (x0 + x1) / 2 + k * dy, (y0 + y1) / 2 - k * dx
    a0 = math.atan2(y0 - cy, x0 - cx)
    da = (math.atan2(y1 - cy, x1 - cx) - a0) % (2 * math.pi)
    if sweep == 0:
        da -= 2 * math.pi if da else 0
    return [(cx + r * math.cos(a0 + da * i / steps), cy + r * math.sin(a0 + da * i / steps)) for i in range(1, steps + 1)]


def _subpaths(d: str):
    tokens = [m.group(1) or float(m.group(2)) for m in TOKEN.finditer(d)]
    i, cur, cmd, poly, out = 0, (0.0, 0.0), None, [], []
    def num(n):
        nonlocal i
        vals = tokens[i : i + n]
        i += n
        return vals
    while i < len(tokens):
        if isinstance(tokens[i], str):
            cmd = tokens[i]
            i += 1
        if cmd == "M":
            if poly:
                out.append(poly)
            cur = tuple(num(2))
            poly = [cur]
        elif cmd == "L":
            cur = tuple(num(2))
            poly.append(cur)
        elif cmd == "H":
            cur = (num(1)[0], cur[1])
            poly.append(cur)
        elif cmd == "V":
            cur = (cur[0], num(1)[0])
            poly.append(cur)
        elif cmd == "A":
            r, _, _, large, sweep, x, y = num(7)
            poly += _arc(cur, r, int(large), int(sweep), (x, y))
            cur = (x, y)
        elif cmd == "Z":
            out.append(poly)
            poly = []
        else:
            raise ValueError(f"unsupported path command {cmd!r}")
    if poly:
        out.append(poly)
    return out


def render(size: int) -> Image.Image:
    root = ET.parse(SOURCE).getroot()
    vb = [float(v) for v in root.get("viewBox").split()]
    n = size * SS
    scale = n / vb[2]
    img = Image.new("RGB", (n, n), (0, 0, 0))
    for el in root:
        tag = el.tag.rsplit("}", 1)[-1]
        colour = _hex(el.get("fill"))
        mask = Image.new("L", (n, n), 0)
        if tag == "rect":
            x, y = float(el.get("x", 0)), float(el.get("y", 0))
            w, h = float(el.get("width")), float(el.get("height"))
            ImageDraw.Draw(mask).rectangle([x * scale, y * scale, (x + w) * scale - 1, (y + h) * scale - 1], fill=255)
        elif tag == "path":
            for sub in _subpaths(el.get("d")):
                part = Image.new("L", (n, n), 0)
                ImageDraw.Draw(part).polygon([(px * scale, py * scale) for px, py in sub], fill=255)
                mask = ImageChops.difference(mask, part)  # even-odd
        else:
            raise ValueError(f"unsupported element {tag!r}")
        img.paste(Image.new("RGB", (n, n), colour), mask=mask)
    return img.resize((size, size), Image.LANCZOS)


def main() -> int:
    shutil.copyfile(SOURCE, PUBLIC / "favicon.svg")
    render(180).save(PUBLIC / "apple-touch-icon.png", optimize=True)
    for size in (192, 512):
        render(size).convert("RGBA").save(PUBLIC / f"icon-{size}.png", optimize=True)
    render(48).convert("RGBA").save(PUBLIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
