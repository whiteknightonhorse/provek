"""LAW-NOTES-CEILING - the corpus stands at the step the last control-paired reading has opened.

The precedent this work was modelled on gates its publishing rate on indexation health from Google
Search Console: 5-10 pages a day, then 30, then 50, each step unlocked by a measured reading. We
have no Search Console. The instrument that could answer the same question here is Bing Webmaster.

WHAT CHANGED ON 2026-08-21 (D-24). Until that day this docstring said Bing answers `ErrorCode 14 /
NotAuthorized` to every per-site call because ownership verification was unfinished. It is
finished: `provek.dev` is a verified property and the per-site calls answer.

WHAT THIS DOCSTRING THEN SAID FOR THREE DAYS, AND WHY IT WAS FALSE (T-B10, D-34). It said there was
no indexation reading because `GetQueryStats` and `GetLinkCounts` "return zero for this property,
and they return zero for an old verified control site as well", so the zero described what those
calls can see rather than whether anyone had found us - filed by the snapshot as `instrument_blind`.
The instrument was never blind. Measured 2026-08-24 20:33 UTC, one key, one code path, the two
sites side by side: `GetQueryStats` reads **64 rows / 402 impressions** at the control and 0 here;
`GetRankAndTrafficStats` reads **985 impressions / 29 clicks** at the control and 0 here (the rows
are in `~/orchestra/evidence/MEASURED-B10-the-control-pair.txt`; the T-B10 brief reports that this
pair also matches the operator's snapshot of the Bing web cabinet, which nothing on this host can
see, so that corroboration is the brief's rather than a reading taken here); `GetCrawlStats` reads 6 rows
there and 0 here. Every one of those zeros is `nothing_qualified` with `control_proven_capable:
true`: the calls are proven able to see the quantity, and no row qualified for their reports here.
That is NOT the same as "Bing has not crawled this site", which the first draft of this docstring
asserted - the same snapshot carries `sitemap_accepted.url_count: 13`, which Bing could not report
without having fetched and parsed the file. What a zero row count establishes is a zero row count.

SO THE READING EXISTED AND WAS ZERO, WHICH THE OLD CONDITION COULD NOT TELL FROM SUCCESS. The
condition was written as "an indexation reading exists", on the assumption that a reading would
carry indexation to gate a rate on. Read literally it was met the moment the probe answered, and
meeting it would have released a publishing rate at the exact moment the measurement said the
pages already published had reached nobody. T-B10 refused to rewrite it - an agent that repairs a
release condition it has just made satisfiable is fitting the measurement to the verdict - and
referred it. THIS FILE IS THAT REFERRAL ANSWERED, by Fable's ruling of 2026-08-24 and the
operator's task on top of it, and the answer is D-35: an existence test becomes a LADDER, and each
step is bought by observing the next link of the chain publication -> crawl -> index -> impressions.

  3 -> 7   a crawl row for this site, against a control that proves the call can report one;
  7 -> 15  the original D-18 condition unchanged - an impressions row - paired the same way;
  above   an operator's decision at live impressions, deliberately not automatic.

THE NUMBERS 7 AND 15 ARE ASSIGNED. There is no reading behind either, exactly as there was none
behind 3 on 2026-08-20, and this is stated as loudly as D-18 states its own bounds because a ladder
looks more measured than a flat number while being measured in only one of its two halves: WHICH
step is open is read from an instrument, HOW FAR a step carries is a choice.

THE CEILING TODAY IS THE FLOOR, AND FOR A BETTER REASON THAN BEFORE. Not "we cannot see" but "we
can see, the control returns six crawl rows, and none qualified for this site" - `nothing_qualified`
with `control_proven_capable: true`, in `web/notes/reach.json`. Two notes stand, so nothing presses
against it either way. What has NOT changed is the trap this file was written against: "the
property is verified" reads like the condition and is only part of it, and a rate lifted on that
part would be a publishing schedule justified by a gate we walked halfway through.

A rate gated on an instrument that does not exist is not a gate (L-4). A ceiling that lives in a
sentence is a promise rather than a gate - so the ladder lives in `web/notes/emit.mjs`, the reading
lives beside it as data a clone can read, and the fourth note fails the build.

WHAT MAY RAISE IT, named so that it cannot be raised by mood: a control-paired reading, taken from
the verified `provek.dev` property, in which the counter the next step names returns rows for THIS
site while a control property proves the same call able to return them. Not a date, not the passage
of time, not the operator's or this agent's judgement that three feels thin - and not an edit to a
number here, which is what `test_the_ladder_in_this_file_is_the_ladder_in_the_build` exists to stop.

HOW TO MAKE THIS FILE FAIL: delete the `control_proven_capable` branch from `stepState` in
`web/notes/emit.mjs` and give the reading a zero control with rows for the subject. The red run,
with nine other mutations and the closed-step refusal, is kept as
`evidence/RED-036-a-ladder-that-climbed-on-a-control-that-had-said-nothing.txt`.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from .notes_support import ROOT, SRC, emitted, sources

EMIT = ROOT / "web" / "notes" / "emit.mjs"
REACH = ROOT / "web" / "notes" / "reach.json"

LADDER: list[tuple[int, str | None]] = [(3, None), (7, "crawl_stats"), (15, "query_stats")]
"""THIS FILE'S COPY OF THE RULE, and it is a copy on purpose.

Two copies of a rule survive each other's repeal (L-2). This one has two by necessity - the build
must refuse before it writes, and the test must refuse in CI where the build has not run - so they
are compared instead of trusted, in both directions: the numbers below are matched against the
literal in `emit.mjs`, and the ceiling this file computes from the reading is matched against the
one node computes from the same reading.
"""

FLOOR = LADDER[0][0]


# --- the same rule, computed here, from the same file the build reads ----------------------------

def _reading() -> dict:
    """The reading, or a NAMED absence. A missing file is not an empty reading and not a zero: it
    is nobody having measured, and the three are kept apart here for the reason invariant 1 gives."""
    if not REACH.exists():
        return {"state": "check_did_not_run", "chain": {}}
    try:
        doc = json.loads(REACH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"state": "unreadable", "chain": {}}
    if doc.get("subject") != "https://provek.dev/" or not isinstance(doc.get("chain"), dict):
        return {"state": "unreadable", "chain": {}}
    return {"state": "measured", "chain": doc["chain"]}


def _step_state(chain: dict, counter: str) -> tuple[bool, str]:
    c = chain.get(counter)
    if c is None:
        return False, "check_did_not_run"
    if c.get("control_proven_capable") is not True:
        return False, "capability_unproven"
    if not isinstance(c.get("count"), int) or isinstance(c.get("count"), bool):
        return False, "unreadable"
    if c["count"] == 0:
        return False, "nothing_qualified"
    return True, "measured"


def ceiling_from(reading: dict) -> int:
    ceiling = FLOOR
    if reading["state"] != "measured":
        return ceiling
    for rung, counter in LADDER[1:]:
        assert counter is not None
        opened, _ = _step_state(reading["chain"], counter)
        if not opened:
            break
        ceiling = rung
    return ceiling


CEILING = ceiling_from(_reading())


# --- the two copies, held against each other -----------------------------------------------------

def test_the_ladder_in_this_file_is_the_ladder_in_the_build() -> None:
    """The watchdog. It reads the literal out of `emit.mjs` rather than a number, because the thing
    an editor reaches for when a fourth note is wanted is the ladder, and a ladder is four numbers
    and two counter names rather than one integer."""
    text = EMIT.read_text(encoding="utf-8")
    m = re.search(r"export const NOTE_LADDER = \[(.*?)\];", text, re.S)
    assert m, "web/notes/emit.mjs no longer declares NOTE_LADDER"
    rungs = re.findall(r"\{\s*ceiling:\s*(\d+),\s*opens_on:\s*(null|\"[a-z_]+\")", m.group(1))
    built = [(int(c), None if o == "null" else o.strip('"')) for c, o in rungs]
    assert built == LADDER, (
        f"web/notes/emit.mjs and this test no longer agree on the ladder: {built} vs {LADDER}")


def _node(script: str) -> object:
    """Ask the GATE. A missing `node` is a RED here and never a skip - an unrunnable check is
    `not_measured`, and reporting it as a pass is the defect this repository is about."""
    node = shutil.which("node")
    assert node, "node is not on this host, so this gate could not run - that is red, not a skip"
    out = subprocess.run([node, "--input-type=module", "-e", script],
                         cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, f"the build's ladder did not evaluate:\n{out.stderr}"
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_the_build_computes_the_same_ceiling_from_the_same_reading() -> None:
    """The stronger half of the watchdog: not that the two files carry the same numbers, but that
    two independent implementations of the rule return the same answer over the reading in this
    tree."""
    built = _node(
        "import {NOTE_CEILING, NOTE_STEP} from './web/notes/emit.mjs';"
        "console.log(JSON.stringify({c: NOTE_CEILING, r: NOTE_STEP.reading}));")
    assert built["c"] == CEILING, (
        f"the build enforces {built['c']} and this test enforces {CEILING} over the same reading")
    assert built["r"] == _reading()["state"], (
        f"the build files the reading as {built['r']}, this test as {_reading()['state']}")


# --- what the ladder does with each shape of reading ---------------------------------------------

def _counter(count: int | None, proven: bool | None) -> dict:
    return {"count": count, "control_proven_capable": proven, "control_count": 6}


CASES = [
    ("a crawl row against a proven control opens the first step",
     {"crawl_stats": _counter(6, True)}, 7),
    ("and no further, because the step above it has nothing",
     {"crawl_stats": _counter(6, True), "query_stats": _counter(0, True)}, 7),
    ("both links read, both open",
     {"crawl_stats": _counter(6, True), "query_stats": _counter(3, True)}, 15),
    ("THE DEFECT T-B10 REMOVED FROM THE PROBE: rows for us, silence at the control",
     {"crawl_stats": _counter(6, False)}, 3),
    ("a zero on both sides is not a closed step, it is an undecided one - and it stays shut",
     {"crawl_stats": _counter(0, False)}, 3),
    ("the call sees and nothing qualified: shut, and for the honest reason",
     {"crawl_stats": _counter(0, True)}, 3),
    ("a counter absent from the reading cannot open anything",
     {}, 3),
    ("an impressions row may not skip the crawl rung it arrived without",
     {"query_stats": _counter(9, True)}, 3),
    ("a count that is not a number is unreadable, never zero",
     {"crawl_stats": _counter(None, True)}, 3),
]


READINGS = [{"state": "measured", "chain": chain} for _, chain, _ in CASES] + [
    # The two silences, over a chain that WOULD open the first step if anyone had read it. A ladder
    # that climbed here would be treating "nobody measured" as a measurement - invariant 1 broken by
    # the gate that enforces it - and the two silences stay two facts rather than one.
    {"state": "check_did_not_run", "chain": {"crawl_stats": _counter(6, True)}},
    {"state": "unreadable", "chain": {"crawl_stats": _counter(6, True)}},
]
EXPECTED = [c[2] for c in CASES] + [FLOOR, FLOOR]
WHY = [c[0] for c in CASES] + [
    "a reading nobody took is not a closed step and not an open one",
    "a reading that did not parse may not be climbed either",
]


@pytest.fixture(scope="module")
def gate_answers() -> list[int]:
    """THE SAME CASES PUT TO THE GATE ITSELF. Without this the table below would judge the copy of
    the rule in this file and leave `emit.mjs` - the thing that actually refuses the fourth note -
    unmeasured, which is L-3 committed by the test suite: a template checked instead of an artefact.
    One node process for all of them, because the point is coverage, not isolation."""
    answers = _node(
        "import {ceilingFrom} from './web/notes/emit.mjs';"
        f"const cases = {json.dumps(READINGS)};"
        "console.log(JSON.stringify(cases.map((r) => ceilingFrom(r).ceiling)));")
    assert isinstance(answers, list) and len(answers) == len(READINGS)
    return answers


@pytest.mark.parametrize("i", range(len(READINGS)), ids=[w[:48] for w in WHY])
def test_the_ladder_climbs_only_on_a_control_paired_row(i: int, gate_answers: list[int]) -> None:
    assert ceiling_from(READINGS[i]) == EXPECTED[i], f"this file's copy: {WHY[i]}"
    assert gate_answers[i] == EXPECTED[i], f"web/notes/emit.mjs: {WHY[i]}"


def test_a_reading_about_another_property_decides_nothing_here(tmp_path: Path) -> None:
    """`reach.json` is a COPIED file, and the one thing a copy can get wrong while every number in
    it is right is which site it is a copy of. The control property has 64 query rows and 6 crawl
    rows; a build that read those as ours would climb the whole ladder on somebody else's traffic."""
    doc = json.loads(REACH.read_text(encoding="utf-8"))
    doc["subject"] = doc["control"]
    for name in doc["chain"]:
        doc["chain"][name]["count"] = 9   # rows, so only the subject check can hold the step shut
    p = tmp_path / "reach.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    got = _node(
        "import {readReach, ceilingFrom} from './web/notes/emit.mjs';"
        f"const r = readReach({json.dumps(str(p))});"
        "console.log(JSON.stringify({s: r.state, c: ceilingFrom(r).ceiling}));")
    assert got["s"] == "unreadable", f"a reading of another property was filed as {got['s']}"
    assert got["c"] == FLOOR


def test_an_absent_reading_is_not_an_empty_one(tmp_path: Path) -> None:
    """The two ways to have no reading, asked of the gate rather than of this file's copy."""
    absent = tmp_path / "nothing.json"
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    got = _node(
        "import {readReach, ceilingFrom} from './web/notes/emit.mjs';"
        f"const a = readReach({json.dumps(str(absent))});"
        f"const b = readReach({json.dumps(str(broken))});"
        "console.log(JSON.stringify({a: a.state, b: b.state, ca: ceilingFrom(a).ceiling, "
        "cb: ceilingFrom(b).ceiling}));")
    assert got["a"] == "check_did_not_run", "a reading nobody took was filed as something else"
    assert got["b"] == "unreadable", "a reading that did not parse was filed as something else"
    assert (got["ca"], got["cb"]) == (FLOOR, FLOOR)


def test_the_reading_in_this_tree_is_control_paired_at_all() -> None:
    """INSTRUMENT CONTROL for every case above. A `reach.json` in which nothing is control-paired
    would make the ladder unopenable for a reason nobody chose, and every assertion here would
    still pass. This is the one that would die."""
    reading = _reading()
    assert reading["state"] == "measured", f"the reading is {reading['state']}"
    proven = [k for k, v in reading["chain"].items() if v.get("control_proven_capable") is True]
    assert proven, ("no counter in web/notes/reach.json is proven capable, so the ladder is a wall "
                    "held shut by an unproven instrument rather than by a measurement")


# --- what is actually in the tree ----------------------------------------------------------------

def test_no_more_notes_exist_than_the_ceiling_allows() -> None:
    if not SRC.exists():
        pytest.skip("no method notes in this checkout")
    files = sorted(SRC.glob("*.md"))
    assert len(files) <= CEILING, (
        f"{len(files)} note sources, ceiling is {CEILING}. Raising it requires a control-paired "
        f"reading in web/notes/reach.json opening the next step, not an edit to this number.")


def test_the_emitted_site_carries_no_more_notes_than_were_captured() -> None:
    pages = emitted()
    if not pages:
        pytest.skip("site not built in this checkout")
    assert len(pages) == len(sources()) <= CEILING
