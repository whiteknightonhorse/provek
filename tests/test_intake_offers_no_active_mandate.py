"""D-21 in machine form: the intake cannot record an active probing mandate.

WHY THIS TEST EXISTS. The active-mandate option was removed from `/apply/` on 2026-08-20 because no
prober exists to honour it, and offering it would ask a stranger to grant access to a live system
that nothing here can use. The removal was written into the form, into a comment, and into
`docs/INTAKE_OPERATIONS.md` - and the ENDPOINT went on accepting it. `apply.js` read

    const mandate = body.mandate === "active" ? "active" : "passive";

which honours "active" for every client that is not the form. A `curl` POST could grant a probing
mandate over production and have it validated, written durably to KV, and announced to the operator
as though a person had agreed to it. Removing a control from a page removes the OFFER, not the
capability; the form is not the boundary.

So this is L-2 with the copies counted properly. Three copies of the repeal were prose and one was
executable, and the executable one is the copy that mattered - it was found only because the
decision entry was refuted against the file it cited as its own evidence. A rule with no machine
behind it is treated as unenforced in this repository, and until this file existed, D-21 had none.

WHAT IS ASSERTED. With comments stripped - the prose here quotes the old line on purpose, and a
checker that reads its own explanation is the false red L-4 warns of - the endpoint assigns
`mandate` a constant `"passive"`, and the QUOTED token `"active"` appears nowhere in either the
endpoint's code or the form's code. Reintroducing the ternary, or adding a radio input that sends
"active", is red.

Two edges on the stripper, both put there after Fable found them rather than by foresight. Line
comments are matched as `(?<!:)//`, because a plain `//` swallows the tail of every URL - the
Telegram endpoint and the form's placeholder both contain one, and a ternary sharing a line with a
URL would have been invisible. And the token is matched quoted, because a bare substring test also
fires on `interactive`, on a Tailwind `active:` variant and on `activeElement`: a gate that goes red
for a word which grants nothing is how a suite gets skipped.

WHAT IS NOT ASSERTED. That the DEPLOYED endpoint behaves this way. `/api/apply` is a Cloudflare
Pages Function republished by `wrangler pages deploy`, which needs a credential this host does not
hold (L-9, D-19), so the served function changes only when the operator deploys. This test reads
the repository. The gap between the two is real, is named in D-21, and is not something a test here
can close - claiming otherwise would be the fake anchor L-8 refuses.

HOW TO MAKE IT FAIL: restore the ternary in `apply.js`, or add `mandate: "active"` to the form's
submit body. The red run is kept as `evidence/RED-009-intake-accepts-active-mandate.txt`.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = ROOT / "web" / "functions" / "api" / "apply.js"
FORM = ROOT / "web" / "src" / "pages" / "Apply.tsx"

BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
# `(?<!:)` keeps the URL in `https://api.telegram.org/...` out of the stripper's mouth. Without it
# everything after the `//` of a URL is treated as a comment and stops being scanned, so a line
# holding a URL AND a reinstated mandate ternary would pass green - L-6, a checker that inspects
# one syntax and reports success on every other.
LINE_COMMENT = re.compile(r"(?<!:)//[^\n]*")
JSX_COMMENT = re.compile(r"\{\s*/\*.*?\*/\s*\}", re.DOTALL)
# The quoted token only. A bare `"active" in code` also fires on `interactive`, on a Tailwind
# `active:` variant and on `document.activeElement`, none of which grant anything - and a gate that
# reddens for a word that means nothing here teaches people to skip the suite (L-4's other edge).
ACTIVE_TOKEN = re.compile(r"""['"`]active['"`]""")


def _code(path: Path) -> str:
    """Source with comments removed, so the gate never reads its own explanation."""
    text = path.read_text(encoding="utf-8")
    text = JSX_COMMENT.sub("", text)
    text = BLOCK_COMMENT.sub("", text)
    return LINE_COMMENT.sub("", text)


def test_the_files_this_gate_guards_still_exist() -> None:
    """A gate pointed at a moved file reports clean forever - L-16's shape."""
    for path in (ENDPOINT, FORM):
        assert path.is_file(), (
            f"{path} is missing. This gate enforces D-21 against it; if the intake moved, move "
            "this test in the same commit rather than letting it pass over nothing."
        )


def test_endpoint_assigns_passive_unconditionally() -> None:
    code = _code(ENDPOINT)
    assert re.search(r'\bconst\s+mandate\s*=\s*"passive"\s*;', code), (
        "web/functions/api/apply.js no longer assigns `mandate` the constant \"passive\". D-21 "
        "withdraws the active probing mandate from the INTAKE, not merely from the form - the "
        "previous version made exactly this mistake with "
        '`body.mandate === "active" ? "active" : "passive"`, which honours "active" for any client '
        "that is not the form."
    )


def test_no_active_mandate_anywhere_in_the_intake() -> None:
    for path in (ENDPOINT, FORM):
        code = _code(path)
        found = ACTIVE_TOKEN.findall(code)
        assert not found, (
            f"the quoted token {found[0]} appears in the code of {path.relative_to(ROOT)} "
            "(comments were stripped before this check). No prober exists to honour an active "
            "probing mandate, so the intake may not accept, send or store one until T-2.12 - see "
            "D-21."
        )
