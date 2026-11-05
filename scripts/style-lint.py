#!/usr/bin/env python3
"""style-lint.py — deterministic house-style gate for NEW guides (T-0395).

Usage: style-lint.py [--json] PAGE.html [PAGE.html ...]
Exit 0 = GREEN, 1 = RED (reasons on stderr). Same semantics as check-page-claims.py:
RED blocks the release of the page. The rules are style/house-rules.md; this file enforces
the machine-checkable ones. Scope: article prose only. Chrome (NOCLAIMSCAN regions) and
<script>/<style>/<svg>/<pre>/<table>/<figure> are not linted.

Thresholds (env override): STYLE_MAX_PASSIVE_RATIO (0.20), STYLE_MAX_AVG_SENTENCE_WORDS (22),
STYLE_MAX_FILLER (2), STYLE_MAX_EM_DASH_PER_PARAGRAPH (1).
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
from pathlib import Path

MAX_PASSIVE_RATIO = float(os.environ.get("STYLE_MAX_PASSIVE_RATIO", "0.20"))
MAX_AVG_SENTENCE_WORDS = float(os.environ.get("STYLE_MAX_AVG_SENTENCE_WORDS", "22"))
MAX_FILLER = int(os.environ.get("STYLE_MAX_FILLER", "2"))
MAX_EM_DASH = int(os.environ.get("STYLE_MAX_EM_DASH_PER_PARAGRAPH", "1"))

# (label, regex). Kept in sync with style/house-rules.md by a unit test.
BANNED = [
    ("delve", r"\bdelv(?:e|es|ed|ing)\b"),
    ("tapestry", r"\btapestr(?:y|ies)\b"),
    ("landscape", r"\blandscapes?\b"),
    ("realm", r"\brealms?\b"),
    ("leverage", r"\bleverag(?:e|es|ed|ing)\b"),
    ("seamless", r"\bseamless(?:ly)?\b"),
    ("robust", r"\brobust(?:ness)?\b"),
    ("cutting-edge", r"\bcutting[- ]edge\b"),
    ("game-changer", r"\bgame[- ]changers?\b"),
    ("in today's fast-paced", r"\bin today's fast[- ]paced\b"),
    ("it's worth noting", r"\bit(?:'s| is) worth noting\b"),
    ("it is important to note", r"\bit is important to note\b"),
    ("in conclusion", r"\bin conclusion\b"),
    ("unlock", r"\bunlock(?:s|ed|ing)?\b"),
    ("navigate the", r"\bnavigat(?:e|es|ed|ing) the\b"),
    ("elevate", r"\belevat(?:e|es|ed|ing)\b"),
    ("embark", r"\bembark(?:s|ed|ing)?\b"),
    ("whether you're ... or", r"\bwhether you(?:'re| are)\b[^.?!]{0,100}?\bor\b"),
    ("let's dive in", r"\blet's dive in\b"),
    ("dive into", r"\bdive (?:in|into)\b"),
    ("in the world of", r"\bin the world of\b"),
    ("are you looking", r"\bare you looking\b"),
]
FILLER = r"\b(?:very|actually|really|unfortunately|basically|essentially|simply)\b"
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⬆↔-↪️]")
IRREGULAR = ("built|made|done|run|sent|given|known|shown|seen|taken|written|chosen|paid|held|"
             "set|put|kept|found|used|bought|sold|told|left|lost|drawn|driven|broken|stored")
PASSIVE = re.compile(
    r"\b(?:is|are|was|were|be|been|being|gets?|got)\s+(?:\w+ly\s+)?(?:\w{3,}ed|" + IRREGULAR + r")\b",
    re.IGNORECASE)

NOCLAIMSCAN = re.compile(r"<!--\s*NOCLAIMSCAN\s*-->.*?<!--\s*/NOCLAIMSCAN\s*-->", re.DOTALL)
SKIP_BLOCKS = re.compile(r"<(script|style|svg|pre|table|figure)\b.*?</\1>", re.DOTALL | re.IGNORECASE)
BLOCK = re.compile(r"<(p|li|h[1-6])\b[^>]*>(.*?)</\1>", re.DOTALL | re.IGNORECASE)
FACT_TOKEN = re.compile(r"<<FACT:[A-Za-z0-9_]+>>")


def _text(fragment: str) -> str:
    t = re.sub(r"<[^>]+>", "", fragment)
    t = html.unescape(FACT_TOKEN.sub("", t)).replace("’", "'")
    return re.sub(r"\s+", " ", t).strip()


def extract_blocks(page: str) -> list[tuple[str, str]]:
    """[(tag, plain text)] for the article prose, in document order."""
    page = SKIP_BLOCKS.sub(" ", NOCLAIMSCAN.sub(" ", page))
    return [(m.group(1).lower(), t) for m in BLOCK.finditer(page) if (t := _text(m.group(2)))]


def split_sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def lint_blocks(blocks: list[tuple[str, str]], min_words: int = 0) -> dict:
    reasons: list[str] = []
    body = [(tag, t) for tag, t in blocks if tag in ("p", "li")]
    sentences = [s for _, t in body for s in split_sentences(t)]
    full = " ".join(t for _, t in blocks)

    for label, rx in BANNED:
        hits = re.findall(rx, full, flags=re.IGNORECASE)
        if hits:
            reasons.append(f"banned phrase '{label}' x{len(hits)}")
    if EMOJI.search(full):
        reasons.append("emoji present")
    if "!" in full:
        reasons.append(f"exclamation mark x{full.count('!')}")
    filler = re.findall(FILLER, full, flags=re.IGNORECASE)
    if len(filler) > MAX_FILLER:
        reasons.append(f"filler words x{len(filler)} (max {MAX_FILLER}): {sorted(set(w.lower() for w in filler))}")
    for i, (_, t) in enumerate(body):
        n = t.count("—")
        if n > MAX_EM_DASH:
            reasons.append(f"paragraph {i} has {n} em dashes (max {MAX_EM_DASH})")
    after_h2 = False
    for tag, t in blocks:
        if tag == "h2":
            after_h2 = True
            continue
        if after_h2 and tag in ("p", "li"):
            sents = split_sentences(t)
            if sents and sents[0].endswith("?"):
                reasons.append(f"rhetorical question opens a section: '{sents[0][:60]}'")
        after_h2 = False

    passive = sum(1 for s in sentences if PASSIVE.search(s))
    ratio = passive / len(sentences) if sentences else 0.0
    if ratio > MAX_PASSIVE_RATIO:
        reasons.append(f"passive-voice ratio {ratio:.2f} > {MAX_PASSIVE_RATIO}")
    words = sum(len(s.split()) for s in sentences)
    avg = words / len(sentences) if sentences else 0.0
    if avg > MAX_AVG_SENTENCE_WORDS:
        reasons.append(f"average sentence length {avg:.1f} words > {MAX_AVG_SENTENCE_WORDS}")
    if min_words > 0 and words < min_words:
        reasons.append(f"body words {words} < {min_words}")
    return {"green": not reasons, "reasons": reasons, "sentences": len(sentences),
            "passive_ratio": round(ratio, 3), "avg_sentence_words": round(avg, 1), "words": words}


def lint_page(page: str, min_words: int = 0) -> dict:
    return lint_blocks(extract_blocks(page), min_words)


def main(argv: list[str]) -> int:
    argv = list(argv)
    min_words = 0
    if "--min-words" in argv:
        i = argv.index("--min-words")
        try:
            min_words = int(argv[i + 1])
        except (IndexError, ValueError):
            print("usage: --min-words N (integer)", file=sys.stderr)
            return 2
        del argv[i:i + 2]
    as_json = "--json" in argv
    paths = [a for a in argv if not a.startswith("--")]
    if not paths:
        print("usage: style-lint.py [--json] [--min-words N] PAGE.html ...", file=sys.stderr)
        return 2
    rc = 0
    results = {}
    for p in paths:
        res = lint_page(Path(p).read_text(encoding="utf-8"), min_words)
        results[p] = res
        if not res["green"]:
            rc = 1
            if not as_json:
                print(f"RED {p}: " + "; ".join(res["reasons"]), file=sys.stderr)
        elif not as_json:
            print(f"GREEN {p} (passive {res['passive_ratio']}, avg {res['avg_sentence_words']} words, "
                  f"body {res['words']} words)")
    if as_json:
        print(json.dumps(results, indent=2))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
