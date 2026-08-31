"""`web/functions/_lib/copy.js` copies operation labels, descriptions and absence-reason text out
of `web/src/pages/Passport.tsx` and `web/src/components/Measured.tsx`, because the brief page
(`web/functions/p/[id]/brief.js`) is a Cloudflare Pages Function and cannot import a `.tsx` module
into its bundle. Each copied string is asserted to still be a VERBATIM substring of the file it was
copied from - a wording change on the full passport page that is not carried into the brief page
would otherwise produce two summaries of one subject that quietly disagree, which is invariant 1 in
its copy-editing form.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COPY_JS = ROOT / "web" / "functions" / "_lib" / "copy.js"
PASSPORT_TSX = ROOT / "web" / "src" / "pages" / "Passport.tsx"
MEASURED_TSX = ROOT / "web" / "src" / "components" / "Measured.tsx"


def _js_string_map(js: str, export_name: str) -> dict[str, str]:
    i = js.index(f"export const {export_name} =")
    open_brace = js.index("{", i)
    depth, end = 0, None
    for j in range(open_brace, len(js)):
        if js[j] == "{":
            depth += 1
        elif js[j] == "}":
            depth -= 1
            if depth == 0:
                end = j
                break
    assert end is not None, f"{export_name}: no matching closing brace"
    body = js[open_brace:end]
    out: dict[str, str] = {}
    for m in re.finditer(r'(\w+):\s*\n?\s*"([^"]*(?:"\s*\+\s*"[^"]*)*)"', body):
        out[m.group(1)] = m.group(2).replace('" +\n    "', "").replace('" + "', "")
    return out


def test_op_labels_are_verbatim_copies():
    labels = _js_string_map(COPY_JS.read_text(encoding="utf-8"), "OP_LABEL")
    assert labels, "OP_LABEL parsed to nothing"
    passport_src = PASSPORT_TSX.read_text(encoding="utf-8")
    for key, text in labels.items():
        assert f'"{text}"' in passport_src, (
            f"OP_LABEL[{key!r}] = {text!r} is not a verbatim string in Passport.tsx any more")


def test_op_descriptions_are_verbatim_copies():
    descs = _js_string_map(COPY_JS.read_text(encoding="utf-8"), "OP_DESC")
    assert descs, "OP_DESC parsed to nothing"
    passport_src = PASSPORT_TSX.read_text(encoding="utf-8")
    # Passport.tsx's own strings sometimes wrap across lines; normalise whitespace on both sides
    # rather than requiring the exact line-break position to match too.
    normalised_src = re.sub(r"\s+", " ", passport_src)
    for key, text in descs.items():
        needle = re.sub(r"\s+", " ", text)
        assert needle in normalised_src, (
            f"OP_DESC[{key!r}] is not a substring of Passport.tsx any more (copy drifted)")


def test_reason_text_is_a_verbatim_copy():
    reasons = _js_string_map(COPY_JS.read_text(encoding="utf-8"), "REASON_TEXT")
    assert reasons, "REASON_TEXT parsed to nothing"
    measured_src = MEASURED_TSX.read_text(encoding="utf-8")
    for key, text in reasons.items():
        assert f'"{text}"' in measured_src, (
            f"REASON_TEXT[{key!r}] = {text!r} is not a verbatim string in Measured.tsx any more")


def test_the_operation_keys_match_what_a_real_passport_carries():
    """The floor under the copy: if a passport ever names an operation neither map recognises,
    the brief page falls back to the raw key (per its own code) rather than silently mislabelling
    it - but the three operations this project currently scores must all be covered."""
    labels = _js_string_map(COPY_JS.read_text(encoding="utf-8"), "OP_LABEL")
    descs = _js_string_map(COPY_JS.read_text(encoding="utf-8"), "OP_DESC")
    expected = {"development_initiation", "deployment", "treasury_control"}
    assert expected <= labels.keys()
    assert expected <= descs.keys()
