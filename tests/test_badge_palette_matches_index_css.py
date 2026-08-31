"""LAW-ONE-PLACE, for the one rule in this task that has to physically live in two places.

`web/functions/_lib/palette.js` copies the design tokens out of `web/src/index.css`, because a
Cloudflare Pages Function returns raw bytes and never loads that stylesheet - see the header of
`palette.js` for why a badge in particular cannot merely inherit a CSS custom property. This file
reads BOTH sources and fails the moment a value in one stops matching the other, rather than
trusting the header comment to keep them in step by itself.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_CSS = ROOT / "web" / "src" / "index.css"
PALETTE_JS = ROOT / "web" / "functions" / "_lib" / "palette.js"

# index.css names -> palette.js keys (see index.css's own `:root { --c-<name>: ... }` declarations).
TOKENS = {
    "ink": "ink", "ink-2": "ink2", "ink-3": "ink3",
    "line": "line", "line-2": "line2",
    "paper": "paper", "paper-2": "paper2",
    "pass": "pass", "warn": "warn", "fail": "fail", "unknown": "unknown",
    "slot": "slot",
}


def _block(css: str, start_marker: str) -> str:
    """The declarations between one `{` and its matching `}`, starting at `start_marker`."""
    i = css.index(start_marker)
    open_brace = css.index("{", i)
    depth = 0
    for j in range(open_brace, len(css)):
        if css[j] == "{":
            depth += 1
        elif css[j] == "}":
            depth -= 1
            if depth == 0:
                return css[open_brace:j]
    raise AssertionError(f"{start_marker}: no matching closing brace found")


def _read_tokens(block: str) -> dict[str, str]:
    return {m.group(1): m.group(2).lower()
            for m in re.finditer(r"--c-([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})", block)}


def _light_tokens() -> dict[str, str]:
    css = INDEX_CSS.read_text(encoding="utf-8")
    # The FIRST `:root { ... }` block in the file is the light palette (index.css's own ordering:
    # light first, dark inside the `prefers-color-scheme: dark` media query below it).
    return _read_tokens(_block(css, ":root {"))


def _dark_tokens() -> dict[str, str]:
    css = INDEX_CSS.read_text(encoding="utf-8")
    return _read_tokens(_block(css, '@media (prefers-color-scheme: dark)'))


def _js_object(js: str, export_name: str) -> dict[str, str]:
    body = _block(js, f"export const {export_name} =")
    return {m.group(1): m.group(2).lower()
            for m in re.finditer(r"(\w+):\s*\"(#[0-9a-fA-F]{6})\"", body)}


def test_light_palette_matches_index_css():
    css_tokens = _light_tokens()
    js_tokens = _js_object(PALETTE_JS.read_text(encoding="utf-8"), "LIGHT")
    for css_name, js_name in TOKENS.items():
        assert css_name in css_tokens, f"index.css light palette has no --c-{css_name}"
        assert js_name in js_tokens, f"palette.js LIGHT has no key {js_name!r}"
        assert css_tokens[css_name] == js_tokens[js_name], (
            f"{css_name}: index.css has {css_tokens[css_name]}, palette.js LIGHT.{js_name} "
            f"has {js_tokens[js_name]}")


def test_dark_palette_matches_index_css():
    css_tokens = _dark_tokens()
    js_tokens = _js_object(PALETTE_JS.read_text(encoding="utf-8"), "DARK")
    for css_name, js_name in TOKENS.items():
        assert css_name in css_tokens, f"index.css dark palette has no --c-{css_name}"
        assert js_name in js_tokens, f"palette.js DARK has no key {js_name!r}"
        assert css_tokens[css_name] == js_tokens[js_name], (
            f"{css_name}: index.css dark has {css_tokens[css_name]}, palette.js DARK.{js_name} "
            f"has {js_tokens[js_name]}")


def test_the_readers_themselves_can_fail():
    """A parser that always returns the same dict regardless of input would pass the two tests
    above by accident. Prove both readers respond to their own source changing."""
    assert _light_tokens() != _dark_tokens(), "light and dark read identically - the block finder is broken"
