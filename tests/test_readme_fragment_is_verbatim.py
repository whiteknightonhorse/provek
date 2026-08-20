"""The README's sample verdict is a quotation, and this is the gate that keeps it one.

WHY THIS TEST EXISTS. `README.md` showed a JSON block introduced as "Real output, from the live
registry - not an example". It was neither. The values were real, but they came from a passport
rather than the registry, and the SHAPE existed in no artefact anywhere: `status` and
`verifier_affiliation` live at `passport.*`, `operations` lives at `passport.verified.operations`,
and the fragment spliced the two levels into one flat object and then dropped the third operation
without saying so. Nobody lied; a true thing was pasted into a shape that was never emitted, on the
page whose next section invites the reader to recompute the verdict for themselves. A reader who
followed that invitation with `jq` would have found none of those paths.

That is this repository's founding defect - a claim one notch stronger than the artefact behind it -
sitting in the first code block of its own front page. Correcting the words alone would have left
the mechanism, because nothing at all read that block. So the block is now a quotation with a
machine behind it: a rule in prose is a rule that quietly stops being true (L-2), and this file is
what stops the paste from drifting from the emit a second time.

WHAT IS ASSERTED. The fenced `json` block under "What a verdict looks like" parses, and it is the
`passport.verified.operations` array of THE PASSPORT THE README NAMES - deep-equal, so a dropped
operation, a reordered array, a changed level or an invented key is red. The subject is not free:
the paragraph above the block links to one passport by filename, and the test resolves that link
and compares against that file. An earlier version of this test accepted a match against any of the
eight emitted passports, and Fable refuted it with the state that leaves green - swap the block for
another subject's array, leave the link pointing at APIbase, and the README attributes a quotation
to a file that does not contain it while four tests pass. A gate that permits the defect it names
is decoration.

It is additionally the canonical `json.dumps(..., indent=2)` rendering of that subtree, which is
what lets the README describe the difference from the shipped bytes exactly.

WHAT IS NOT ASSERTED, deliberately. That the live site currently serves this. The test reads
`public/passports/`, not the network. A test that fails when Cloudflare is slow teaches people to
skip the suite, which is L-4 from its other edge - a false red bypasses a gate exactly as a false
green does.

That local-equals-served link is checked by NO GATE. The first draft of this docstring said it was
"checked elsewhere (LAW-MEASURE-SHIPPED)", and that law binds `src/collector/divergence.py`, which
compares an audit SUBJECT's repository digest against its deployment - a different quantity
entirely. Citing it here was the fake anchor L-8 refuses, written into the docstring of a test
about claims that outrun their artefact. What is true is smaller: the identity was measured BY HAND
on 2026-08-20, when `https://provek.dev/data/passports/git_whiteknightonhorse_APIbase.json` was
fetched with a browser user agent and compared equal to the file on disk. One reading, by a person,
on one day.

HOW TO MAKE IT FAIL, which is the only reason to trust it: delete the `treasury_control` operation
from the block in README, or change `"confidence": "inferred"` to `"measured"`, or re-indent the
block to four spaces, or repoint the link at another subject's passport while leaving the block
alone. The red run for the first of those is kept as
`evidence/RED-008-readme-fragment-not-verbatim.txt`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
PASSPORTS = ROOT / "public" / "passports"

HEADING = "## What a verdict looks like"
FENCE = re.compile(r"```json\n(?P<body>.*?)\n```", re.DOTALL)
# The passport the paragraph above the block links to, e.g. /data/passports/git_..._APIbase.json
LINKED = re.compile(r"/data/passports/(?P<name>[A-Za-z0-9_.-]+\.json)")


def _section() -> str:
    """Everything from the 'What a verdict looks like' heading to the next heading."""
    text = README.read_text(encoding="utf-8")
    start = text.find(HEADING)
    assert start != -1, (
        f"{README.name} has no {HEADING!r} section. If the section was renamed, this gate stopped "
        "guarding anything - rename it here in the same commit rather than deleting the test."
    )
    end = text.find("\n## ", start + len(HEADING))
    return text[start:] if end == -1 else text[start:end]


def _fragment() -> str:
    """The first ```json block after the 'What a verdict looks like' heading."""
    match = FENCE.search(_section())
    assert match is not None, f"no fenced json block follows {HEADING!r} in {README.name}"
    return match.group("body")


def _linked_passport() -> Path:
    """The passport file the README's own prose attributes the block to."""
    names = LINKED.findall(_section())
    assert names, (
        f"the {HEADING!r} section names no passport under /data/passports/. The block is presented "
        "as a quotation, and a quotation without an attribution cannot be checked against its "
        "source - restore the link rather than relaxing this gate."
    )
    assert len(set(names)) == 1, (
        f"the {HEADING!r} section links to more than one passport {sorted(set(names))}, so which "
        "one the block is quoted from is ambiguous."
    )
    path = PASSPORTS / names[0]
    assert path.is_file(), (
        f"{README.name} attributes the fragment to {names[0]}, which does not exist under "
        f"{PASSPORTS}. Either the cohort changed and the README was not re-copied, or the link is "
        "wrong; both are the drift this gate exists to catch."
    )
    return path


def _summarise(ops: list) -> str:
    """operation=level pairs - the names alone are identical across subjects, the levels are not."""
    return ", ".join(
        f"{op.get('operation')}={op.get('level')}" if isinstance(op, dict) else repr(op)
        for op in ops
    )


def _emitted_operation_arrays() -> list[tuple[str, list]]:
    """(filename, passport.verified.operations) for every emitted passport that has one."""
    out = []
    for path in sorted(PASSPORTS.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        ops = doc.get("passport", {}).get("verified", {}).get("operations")
        if isinstance(ops, list):
            out.append((path.name, ops))
    return out


def test_there_are_passports_to_compare_against() -> None:
    """An empty corpus would make every other test here vacuously green - L-16.

    A suite conditioned on its own subject cannot speak about the subject's absence, so the empty
    set is asserted against rather than skipped over.
    """
    assert _emitted_operation_arrays(), (
        f"no emitted passport under {PASSPORTS} carries passport.verified.operations. The README "
        "fragment claims to be quoted from one, so with none present the claim is unbacked and "
        "this is red rather than skipped."
    )


def test_fragment_is_valid_json() -> None:
    parsed = json.loads(_fragment())
    assert isinstance(parsed, list), (
        "the README fragment is introduced as the `passport.verified.operations` ARRAY; a JSON "
        f"object here means the block was reshaped again, got {type(parsed).__name__}"
    )


def test_fragment_is_the_operations_array_of_the_passport_the_readme_names() -> None:
    """The content is THAT passport's operations array, entire and in order."""
    parsed = json.loads(_fragment())
    source = _linked_passport()
    doc = json.loads(source.read_text(encoding="utf-8"))
    ops = doc.get("passport", {}).get("verified", {}).get("operations")
    assert isinstance(ops, list), (
        f"{source.name} carries no passport.verified.operations array, so the README's quotation "
        "has no source to be checked against."
    )
    if ops == parsed:
        return
    pytest.fail(
        "the README fragment under 'What a verdict looks like' is not the "
        f"passport.verified.operations of {source.name}, which is the file the README links to.\n"
        f"  README shows {len(parsed)}: {_summarise(parsed)}\n"
        f"  {source.name} has {len(ops)}: {_summarise(ops)}\n"
        "Re-copy the block from that passport, or repoint the link at the passport it really came "
        "from. Editing this test to match the README instead would be the rubber stamp the "
        "ratchets exist to refuse."
    )


def test_fragment_is_the_canonical_rendering_of_that_array() -> None:
    """Form as well as content: README says the only change is the outdent, so prove it."""
    parsed = json.loads(_fragment())
    canonical = json.dumps(parsed, indent=2)
    assert _fragment() == canonical, (
        "the README fragment parses to an emitted operations array but is not its canonical "
        "`json.dumps(..., indent=2)` rendering, so the README's claim that indentation is the only "
        "difference from the shipped bytes is no longer true. Replace the block with:\n\n"
        + canonical
    )
