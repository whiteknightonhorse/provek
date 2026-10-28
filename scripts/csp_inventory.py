#!/usr/bin/env python3
"""List what the built pages load, so the Content-Security-Policy in web/public/_headers is
measured rather than guessed (T-0579). Walks web/dist/**/*.html and web/src.

    python3 scripts/csp_inventory.py [dist_dir]

Prints one JSON document. `origins` is the part a policy must cover; the rest is evidence.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "web" / "dist"
SRC = ROOT / "web" / "src"
# Script types the browser never executes: data blocks (JSON-LD, a future JSON bootstrap).
DATA_TYPES = {"application/ld+json", "application/json"}


def _origin(url: str) -> str | None:
    u = urlparse(url)
    return f"{u.scheme}://{u.netloc}" if u.scheme in ("http", "https") and u.netloc else None


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[dict] = []
        self.inline: list[dict] = []
        self.styles: list[str] = []
        self.inline_style_attrs = 0
        self.style_tags = 0
        self.imgs: list[str] = []
        self.frames: list[str] = []
        self.forms: list[str] = []
        self._buf: list[str] | None = None
        self._type = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "style" in a:
            self.inline_style_attrs += 1
        if tag == "script":
            if a.get("src"):
                self.scripts.append({"src": a["src"], "type": a.get("type", "")})
            else:
                self._buf, self._type = [], a.get("type", "")
        elif tag == "style":
            self.style_tags += 1
        elif tag == "link" and "stylesheet" in (a.get("rel") or "") and a.get("href"):
            self.styles.append(a["href"])
        elif tag == "img" and a.get("src"):
            self.imgs.append(a["src"])
        elif tag == "iframe" and a.get("src"):
            self.frames.append(a["src"])
        elif tag == "form":
            self.forms.append(a.get("action", ""))

    def handle_data(self, data):
        if self._buf is not None:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._buf is not None:
            body = "".join(self._buf)
            digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
            self.inline.append({"type": self._type or "text/javascript", "sha256": digest, "bytes": len(body)})
            self._buf = None


def inventory(dist: Path = DIST, src: Path = SRC) -> dict:
    pages = sorted(dist.rglob("*.html"))
    scripts, styles, imgs, frames = set(), set(), set(), set()
    inline_exec, inline_data = {}, {}
    style_attr_pages, style_tag_pages = 0, 0
    forms = set()
    for p in pages:
        pg = _Page()
        pg.feed(p.read_text(encoding="utf-8"))
        scripts |= {s["src"] for s in pg.scripts}
        styles |= set(pg.styles)
        imgs |= set(pg.imgs)
        frames |= set(pg.frames)
        forms |= set(pg.forms)
        style_attr_pages += bool(pg.inline_style_attrs)
        style_tag_pages += bool(pg.style_tags)
        for s in pg.inline:
            d = inline_data if s["type"] in DATA_TYPES else inline_exec
            k = s["type"] + " " + s["sha256"]
            d[k] = d.get(k, 0) + 1
    src_hosts, src_frames, src_connect = set(), set(), set()
    for f in sorted(src.rglob("*")):
        if f.suffix in (".ts", ".tsx", ".js", ".jsx") and f.is_file():
            t = f.read_text(encoding="utf-8")
            src_hosts |= set(re.findall(r"https://[A-Za-z0-9.-]+", t))
            src_frames |= set(re.findall(r"<iframe[^>]*?src=\{`(https://[A-Za-z0-9.-]+)", t, re.S))
            # The chain read path: `RPC_URL = "https://..."` in witnessChainConfig.js.
            src_connect |= set(re.findall(r'RPC_URL\s*=\s*"(https://[A-Za-z0-9.-]+)"', t))
    img_src = {o for i in imgs if (o := _origin(i))}
    scripts_origins = {o for s in scripts if (o := _origin(s))}
    needs = {
        "script-src": sorted(scripts_origins),
        "img-src": sorted(img_src),
        "frame-src": sorted(src_frames | {o for i in frames if (o := _origin(i))}),
        # The beacon script reports to cloudflareinsights.com (its documented endpoint).
        "connect-src": sorted(src_connect | ({"https://cloudflareinsights.com"} if scripts_origins else set())),
    }
    return {
        "html_pages": len(pages),
        "script_src": sorted(scripts),
        "inline_scripts_executable": inline_exec,
        "inline_scripts_data_blocks": inline_data,
        "stylesheets": sorted(styles),
        "pages_with_style_attribute": style_attr_pages,
        "pages_with_style_element": style_tag_pages,
        "img_count": len(imgs),
        "img_origins": sorted(img_src) or ["(same-origin only)"],
        "iframes": sorted(frames),
        "form_actions": sorted(forms),
        "src_https_hosts": sorted(src_hosts),
        "needs": needs,
        "inline_script_needs_unsafe_inline": bool(inline_exec),
        "inline_style_needs_unsafe_inline": bool(style_attr_pages or style_tag_pages),
    }


if __name__ == "__main__":
    print(json.dumps(inventory(Path(sys.argv[1]) if len(sys.argv) > 1 else DIST), indent=2))
