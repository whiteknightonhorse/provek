"""AUD-006 (Fable, 2026-09-03): the scan blocking `git push` and `redact()` guarding evidence
artefacts used to carry their own, independently-typed copies of the secret patterns. Both listed
`gh[pous]_...`, `sk-ant-...`, a PEM header, and a lower-case hex key - the forms a STRANGER'S repo
might carry - and neither knew `cfat_...` (Cloudflare), `pk1_.../sk1_...` (Porkbun), `r8_...`
(Replicate), or a Telegram bot token, which are the forms THIS project's own `~/.env` carries. A
scan that reports "clean" on inputs it cannot parse is not clean, it is blind - it was passing
"1/7 secrets" on a class of secret it never looked at.

`src/collector/github.py` already claimed (in `src/collector/declaration.py`'s docstring) to be
"the one place secret patterns are defined (LAW #ONE-PLACE)". That claim was false the moment
`scripts/secret_scan.sh` grew its own `PATTERN=` string: two lists asserting they are one list is
the exact defect LAW #ONE-PLACE exists to forbid (see `tests/test_badge_palette_matches_index_css.py`
for the sibling case where two files must physically differ in language and a test - not a
comment - is what keeps them in step). This file is that test for the secret patterns: it reads
both sources and fails the moment one drifts from the other, and it proves the new forms are
actually caught, not merely declared.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from src.collector.github import SECRET_PATTERNS, redact

ROOT = Path(__file__).resolve().parents[1]
SCAN_SH = ROOT / "scripts" / "secret_scan.sh"

# Fake secrets ASSEMBLED AT RUNTIME from fragments, so no secret-shaped literal ever sits
# contiguous in this file's raw bytes - the same discipline as `tests/test_github_collector.py`'s
# `_GH`/`_ANT` and `tests/test_declaration.py`'s `_FAKE_TOKEN`. The gate that AUD-006 is about
# stays strict; the fixture bends.
_CF = "cfat" + "_" + ("x" * 25)
_PK = "pk1" + "_" + ("a1b2c3d4e5" * 3)
_SK = "sk1" + "_" + ("a1b2c3d4e5" * 3)
_R8 = "r8" + "_" + ("y" * 25)
_TG = ("1234567" + "89") + ":" + ("A" * 35)


def _bash_pattern() -> str:
    text = SCAN_SH.read_text(encoding="utf-8")
    m = re.search(r"^PATTERN='(.+)'$", text, re.MULTILINE)
    assert m, "scripts/secret_scan.sh: no PATTERN='...' line found"
    return m.group(1)


def test_secret_scan_sh_matches_SECRET_PATTERNS_exactly():
    """LAW #ONE-PLACE: the bash gate and the python redactor must name the SAME alternatives.

    Two independent lists are compared component-by-component, not string-equal end to end,
    because bash and python cannot share one literal (T-badge-palette's own reason) - but nothing
    stops the SET of alternatives from being asserted identical, and this is that assertion.
    """
    bash_alts = set(_bash_pattern().split("|"))
    py_alts = {p.pattern for p in SECRET_PATTERNS}
    assert bash_alts == py_alts, (
        f"secret_scan.sh and SECRET_PATTERNS have drifted.\n"
        f"only in secret_scan.sh: {bash_alts - py_alts}\n"
        f"only in SECRET_PATTERNS: {py_alts - bash_alts}")


def test_the_comparison_itself_can_fail():
    """A reader that always reports equal would pass the test above by accident."""
    assert {"a", "b"} != {"a"}, "sanity: set comparison itself is not broken"
    assert _bash_pattern() != "", "scripts/secret_scan.sh: PATTERN parsed as empty"


def _scan_blocks(fragment: str) -> bool:
    """Run the ACTUAL gate script's regex against one line, the way `git grep -nE` would."""
    proc = subprocess.run(
        ["grep", "-nE", _bash_pattern(), "-"],
        input=fragment, capture_output=True, text=True)
    return proc.returncode == 0


def test_cloudflare_token_is_redacted_and_caught():
    assert "<REDACTED>" in redact(f"CF_API_TOKEN={_CF}")
    assert _scan_blocks(f"CF_API_TOKEN={_CF}")


def test_porkbun_keys_are_redacted_and_caught():
    assert "<REDACTED>" in redact(f"PORKBUN_KEY={_PK}")
    assert "<REDACTED>" in redact(f"PORKBUN_SECRET={_SK}")
    assert _scan_blocks(f"PORKBUN_KEY={_PK}")
    assert _scan_blocks(f"PORKBUN_SECRET={_SK}")


def test_replicate_token_is_redacted_and_caught():
    assert "<REDACTED>" in redact(f"REPLICATE_API_TOKEN={_R8}")
    assert _scan_blocks(f"REPLICATE_API_TOKEN={_R8}")


def test_telegram_bot_token_is_redacted_and_caught():
    """AUD-006's sharpest example: this exact shape can appear in a subject's OWN declaration
    prose (a Telegram handle plus a stray colon-joined number) and used to sail through both
    `redact()` and the push gate."""
    assert "<REDACTED>" in redact(f"bot token {_TG} configured")
    assert _scan_blocks(f"bot token {_TG} configured")


def test_redaction_still_leaves_ordinary_text_alone():
    """The four new patterns must not turn into a net that catches ordinary prose - a redactor
    that erases everything destroys evidence along with secrets (same law as the existing
    `test_redaction_leaves_ordinary_text_alone` in tests/test_github_collector.py)."""
    t = "the r8 rocket launched at 12:34 near cfa headquarters, pk1 postcode, sk1-rated bunker"
    assert redact(t) == t
    assert not _scan_blocks(t)
