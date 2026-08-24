#!/usr/bin/env python3
"""Produces `evidence/RED-025-a-red-note-had-nothing-between-it-and-the-live-site.txt`.

WHAT IS UNDER TEST, AND WHY THE SUBJECT IS NOT IN THIS REPOSITORY. The scheduled publication cycle
(`~/orchestra/notes_cron.py`) and the note capture it drives (`~/orchestra/notes_gen.py`) live
outside the repository by D-17 and D-19: every `*.py` under `scripts/` must be bound to an `ABI-*`
requirement, no requirement in the master specification covers scheduled publication or page
generation, and binding one anyway to get past `scripts/ratchet_scope.py` is the rubber stamp that
ratchet exists to catch. The evidence lives HERE, by the precedent RED-024 set: a red run kept only
on the host that produced it is insurance nobody else can reach.

THE DEFECT, STATED AS THE THING THAT COULD HAVE HAPPENED. The cycle ran host, capture, build,
sitemap, tree, deploy. `scripts/publishable_tree.py` asks whether the tree is CLEAN of work no gate
has judged - never whether the gates PASS - and it lists `web/notes/src/` and
`web/notes/manifest.json` as the cycle's own output, correctly, because the cycle writes them. So a
captured note that FAILS `tests/test_notes.py` was publishable by construction: every guard between
it and provek.dev was reading a different question. On 2026-08-24 the 05:22 capture produced exactly
such a note, and the only thing that stopped it was that another task's uncommitted files were lying
in the tree that morning, which made `step_tree` refuse for an unrelated reason.

THE INPUT IS NOT INVENTED. `~/orchestra/quarantine/20260824T063401Z/` holds the two notes that
scheduled cycle actually captured that day - one that fails the placement gate and one that passes
it. Both are used below, and the failing one is the fixture the task asks for: a knowingly red note,
written by a model rather than by the harness that judges it.

WHAT THIS FILE DOES TO THE WORKING TREE, AND WHAT IT PROMISES ABOUT IT. It puts those notes into
`web/notes/src/`, adds their manifest lines, and for one run writes a deliberately failing test into
`tests/`. Every one of those is removed again in a `finally`, the manifest is restored from bytes
captured before anything was written, and the run ENDS by comparing `git status --porcelain` and the
manifest's sha256 against the baseline it opened with. If they differ, the artefact is NOT written:
a red run that changed the tree it was measuring is not evidence of anything.

Usage:  python3 evidence/RED-025-generator.py [--out PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[1]
ORCHESTRA = pathlib.Path.home() / "orchestra"
QUARANTINE = ORCHESTRA / "quarantine" / "20260824T063401Z"
SRC_DIR = REPO / "web" / "notes" / "src"
MANIFEST = REPO / "web" / "notes" / "manifest.json"
SCRATCH = ORCHESTRA / ".red025-scratch"      # OUTSIDE the repository: the closing control
                                             # asserts this run leaves the tree untouched,
                                             # and a scratch directory inside it would be
                                             # the first thing to break that assertion
FIXTURE_TEST = REPO / "tests" / "test_zzz_red025_unrelated_red.py"
FIXTURE_SCOPE = REPO / "scripts" / "zzz_red025_unbound_module.py"

RED_NOTE = "autonomy-levels-l0-l5"
GREEN_NOTE = "what-erc-8004-provides-and-what-it-does-not"
FRONT_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


class Bail(Exception):
    """A precondition this harness will not paper over."""


# --- reporting ------------------------------------------------------------------------------------

BLOCKS: list[tuple[str, str]] = []


def block(heading: str, body: str) -> None:
    """Record a block and echo it, FLUSHED.

    Unflushed, this file's own diagnosis goes wrong: stdout is block-buffered when piped and stderr
    is not, so a `Bail` raised after a block is printed arrives in the stream ABOVE the block it
    followed. One run of this harness failed that way and the reason was lost to a `tail -4` that
    showed prose where the refusal should have been. An evidence generator that cannot be debugged
    from its own transcript is the shape it exists to catch.
    """
    BLOCKS.append((heading, body.rstrip()))
    print(f"\n===== {heading} =====", flush=True)
    print(body.rstrip()[:2000], flush=True)


def run(cmd: list[str], cwd: pathlib.Path = REPO, timeout: int = 900) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr).strip()


def gates() -> tuple[int, str]:
    return run(["/usr/bin/env", "bash", str(REPO / "scripts" / "push.sh"), "--gates-only"])


def gates_verdict(rc: int, out: str) -> str:
    """The last few lines of a gate run - the summary a reader needs, not 600 lines of pytest."""
    lines = [ln for ln in out.splitlines() if ln.strip()]
    keep = [ln for ln in lines if ln.startswith(("FAILED", "ERROR")) or " passed" in ln
            or " failed" in ln or ln.startswith("TREE GREEN")]
    return f"exit {rc}\n" + "\n".join(keep[-6:] if keep else lines[-4:])


def porcelain() -> str:
    rc, out = run(["git", "status", "--porcelain"])
    if rc != 0:
        raise Bail("git status could not be read, so no statement about the tree can be made")
    return out


# --- the fixture ----------------------------------------------------------------------------------

def note_parts(slug: str) -> tuple[dict, str]:
    path = QUARANTINE / f"{slug}.md"
    if not path.exists():
        raise Bail(f"{path} is missing: the fixture is a real capture and cannot be reconstructed")
    m = FRONT_RE.match(path.read_text(encoding="utf-8"))
    if not m:
        raise Bail(f"{path}: no front matter")
    return json.loads(m.group(1)), m.group(2).strip()


def install_note(slug: str) -> None:
    """Publish the quarantined note into the tree the way `notes_gen.publish()` would have."""
    front, body = note_parts(slug)
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    doc["notes"][slug] = {"body_sha256": hashlib.sha256(body.encode()).hexdigest(),
                          "date_published": "2026-08-24", "date_modified": "2026-08-24"}
    MANIFEST.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(QUARANTINE / f"{slug}.md", SRC_DIR / f"{slug}.md")


def write_fixture_test(count: int = 1) -> None:
    """`count` reds that are not the capture's, and they fail where the prose says they do.

    `count = 2` is A3e's fixture and the number is load-bearing. The module is named `test_zzz_*`
    so it sorts AFTER `tests/test_notes.py`, which puts the corpus test's `FAILED` line first of
    three and therefore first over the edge of `scripts/push.sh`'s `| tail -3`. Two unrelated reds
    are the fewest that will push it off, and pushing it off is the whole measurement.
    """
    bodies = "".join(
        f"def test_this_red_belongs_to_somebody_else{'' if i == 0 else f'_{i}'}():\n"
        f"    measured = 0\n"
        f"    assert measured == 1, 'RED-025 fixture: a red the scheduled capture did not cause'\n"
        f"\n\n" for i in range(count)).rstrip("\n") + "\n"
    FIXTURE_TEST.write_text(
        '"""Deliberately failing tests, written by evidence/RED-025-generator.py and removed by\n'
        'it. They stand for any red in this repository that has nothing to do with the note the\n'
        'publication cycle captured that morning."""\n\n\n' + bodies,
        encoding="utf-8")


TWIN = "autonomy-levels-l0-l5-second-offender"


def install_twin() -> None:
    """A SECOND note that breaks the same rule, so one test failure covers two offenders.

    This is the fixture for the defect Fable found in the first fix: the placement gate is one
    unparametrised function looping over the corpus, so it fails once whether one note offends or
    two. Title, h1 and description are altered - they still do not carry the primary key, which is
    the point - so that the twin is a second OFFENDER rather than a duplicate of the first, and no
    uniqueness rule fires instead of the one under test.
    """
    front, body = note_parts(RED_NOTE)
    front = json.loads(json.dumps(front))
    front["slug"] = TWIN
    front["title"] = "A second reading of the same ladder - Provek"
    front["h1"] = "A second reading of the same ladder"
    front["description"] = front["description"].replace("Describes how", "Restates how")
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    doc["notes"][TWIN] = {"body_sha256": hashlib.sha256(body.encode()).hexdigest(),
                          "date_published": "2026-08-24", "date_modified": "2026-08-24"}
    MANIFEST.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    (SRC_DIR / f"{TWIN}.md").write_text(
        "---\n" + json.dumps(front, indent=2, ensure_ascii=False) + "\n---\n\n" + body + "\n",
        encoding="utf-8")


def restore_tree(manifest_bytes: bytes) -> None:
    (SRC_DIR / f"{TWIN}.md").unlink(missing_ok=True)
    for slug in (RED_NOTE, GREEN_NOTE):
        (SRC_DIR / f"{slug}.md").unlink(missing_ok=True)
    MANIFEST.write_bytes(manifest_bytes)
    FIXTURE_TEST.unlink(missing_ok=True)
    FIXTURE_SCOPE.unlink(missing_ok=True)


# --- loading the subjects -------------------------------------------------------------------------

def load_module(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_cron(path: pathlib.Path, name: str, deploy_stub: pathlib.Path,
              topics: pathlib.Path | None = None):
    """`notes_cron.py` with its JOURNAL and its DOOR pointed at the harness, and nothing else moved.

    What is re-pointed is data paths and one script path, all of them module constants: the journal,
    the state file, the lock, the topic list, the park directory, and `DEPLOY`. What is NOT
    re-pointed is every path the claim is about - `REPO`, `MANIFEST`, `SRC_DIR`, `GATES` and
    `TREE_GATE` all still address the real repository, so the gates that run are the real gates over
    the real tree.

    `DEPLOY` is a stub for two reasons and the second is the important one. It makes "the deploy was
    reached" a fact on disk rather than an inference from a journal that would not contain the line;
    and it means the mutation run below - which removes the gate and lets a red note through - stops
    at a marker file instead of publishing that note to provek.dev.
    """
    cron = load_module(path, name)
    cron.LOG = SCRATCH / f"{name}.jsonl"
    cron.STATE = SCRATCH / f"{name}.state.json"
    cron.LOCK = SCRATCH / f"{name}.lock"
    cron.PARKED = SCRATCH / "parked"
    cron.DEPLOY = deploy_stub
    # NOTHING LEAVES THIS HOST FROM HERE. `step_bing` is downstream of the deploy, so the mutation
    # run - the one that deliberately removes the gate - reaches it whenever the novelty read comes
    # back `not_measured`, which is one failed HTTPS request away on any run. A harness that submits
    # a URL to a search engine depending on the weather is not a harness. The refusal is a named
    # transport error, which `step_bing` turns into `Blocked`, so the cycle's own handling of a
    # refusing instrument is what runs rather than a stub of the step.
    cron.bing_call = lambda *_a, **_k: {"state": "transport_error", "payload": None,
                                        "message": "RED-025 harness: no submission may leave this host"}
    if topics is not None:
        cron.TOPICS = topics
    return cron


def mutate(path: pathlib.Path, old: str, new: str, dest: pathlib.Path) -> str:
    """Write `path` to `dest` with exactly one substitution, and prove the substitution happened.

    A mutation that did not apply produces a run identical to the unmutated one, under a heading
    claiming a property was removed - which is a false green wearing a red's clothes, and this
    project has already paid for it twice (L-21, L-26). So the count is checked and the diff of the
    edit is returned for the artefact to carry.
    """
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise Bail(f"the mutation anchor appears {text.count(old)} times in {path}, not once")
    dest.write_text(text.replace(old, new), encoding="utf-8")
    return f"--- {path}\n-{old.strip()}\n+{new.strip() or '(removed)'}"


# --- PART A: the cycle ------------------------------------------------------------------------------

def part_a(manifest_bytes: bytes) -> None:
    stub = SCRATCH / "deploy_stub.sh"
    marker = SCRATCH / "DEPLOY_WAS_REACHED"
    stub.write_text(f'#!/usr/bin/env bash\necho "stub deploy" > "{marker}"\nexit 0\n',
                    encoding="utf-8")
    stub.chmod(0o755)

    # --- A1: the defect, on the tree as the cycle would have left it ------------------------------
    install_note(RED_NOTE)
    rc_g, out_g = gates()
    rc_t, out_t = run([sys.executable, str(REPO / "scripts" / "publishable_tree.py"),
                       "--root", str(REPO)])
    block("RUN A1 - THE DEFECT: the gates refuse the note and the cycle's only guard waves it through",
          f"The tree now holds `web/notes/src/{RED_NOTE}.md` and its manifest line, exactly as the\n"
          f"05:22 capture left them on 2026-08-24. Two instruments read the same tree:\n\n"
          f"$ ./scripts/push.sh --gates-only\n{gates_verdict(rc_g, out_g)}\n\n"
          f"$ python3 scripts/publishable_tree.py --root .\nexit {rc_t}\n{out_t[-300:]}\n\n"
          f"The repository says the tree is red. The one check the publication cycle ran before\n"
          f"`deploy.sh` says it is publishable, and it is not wrong - `web/notes/src/` is the\n"
          f"cycle's own output and the question it asks is about foreign work. Between those two\n"
          f"readings there was nothing at all.")
    if rc_g == 0:
        raise Bail("the gates pass the fixture note; the fixture is not red and proves nothing")
    if rc_t != 0:
        raise Bail(f"publishable_tree exited {rc_t}: the tree carries foreign work, so this run "
                   f"cannot show that the tree gate would have passed the note")

    # --- A2: the fix, at the step ------------------------------------------------------------------
    cron = load_cron(ORCHESTRA / "notes_cron.py", "cron_a2", stub)
    raised, journal_lines = None, []
    try:
        cron.step_gates([RED_NOTE])
    except Exception as e:                                     # noqa: BLE001 - the class is the result
        raised = f"{type(e).__name__}: {e}"
    journal_lines = read_journal(cron.LOG)
    parked = sorted((SCRATCH / "parked").glob(f"{RED_NOTE}.*.md"))
    note_gone = not (SRC_DIR / f"{RED_NOTE}.md").exists()
    manifest_now = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    front, body = note_parts(RED_NOTE)
    block("RUN A2 - THE FIX: step_gates parks the capture and ends the cycle RED",
          f"`step_gates([{RED_NOTE!r}])` against the same tree, with the real `scripts/push.sh` and\n"
          f"the real repository:\n\n{chr(10).join(journal_lines)}\n\n"
          f"raised: {raised}\n"
          f"note removed from web/notes/src/: {note_gone}\n"
          f"parked copies: {[p.name for p in parked]}\n"
          f"parked sha256 == the note's sha256: "
          f"{bool(parked) and hashlib.sha256(parked[0].read_bytes()).hexdigest() == hashlib.sha256((QUARANTINE / (RED_NOTE + '.md')).read_bytes()).hexdigest()}\n"
          f"manifest back to its pre-fixture bytes: "
          f"{manifest_now == hashlib.sha256(manifest_bytes).hexdigest()}\n"
          f"reason file beside it (first lines; the whole gate output follows them in the file):\n"
          f"{chr(10).join(parked[0].with_suffix('.reason.txt').read_text(encoding='utf-8').splitlines()[:8]) if parked else '(none)'}\n\n"
          f"The second gate reading is what convicts the note: the same tree passes without it.\n"
          f"Nothing was deleted - the capture is fourteen minutes of model calls and the only\n"
          f"record of what a model wrote when the rule was broken.")
    if raised is None:
        raise Bail("step_gates returned instead of raising on a tree the gates refuse")
    if not note_gone or not parked:
        raise Bail("step_gates did not park the capture it convicted")

    # --- A3: attribution - a red that is NOT the capture's ----------------------------------------
    restore_tree(manifest_bytes)
    install_note(GREEN_NOTE)
    write_fixture_test()
    # THE FIXTURE FAILS AT `pytest` AND NOT AT `ruff`, AND THE FIRST DRAFT FAILED AT RUFF. It was
    # written as a bare `assert False`, which bugbear's B011 refuses, so the gate stopped at step
    # 5/7 and never reached the suite - under a paragraph saying the tree held "a test file that
    # fails on purpose" and that both readings "name the same failing test". Both readings were red
    # and the mechanism under test behaved identically, so nothing here would have gone wrong; the
    # SENTENCE was about a run that had not happened. Verified before rewriting:
    #   $ ruff check --stdin-filename tests/... -   ->  B011 Do not `assert False`

    cron3 = load_cron(ORCHESTRA / "notes_cron.py", "cron_a3", stub)
    raised3 = None
    try:
        cron3.step_gates([GREEN_NOTE])
    except Exception as e:                                     # noqa: BLE001
        raised3 = f"{type(e).__name__}: {e}"
    back = SRC_DIR / f"{GREEN_NOTE}.md"
    same = back.exists() and back.read_bytes() == (QUARANTINE / f"{GREEN_NOTE}.md").read_bytes()
    left_parked = sorted((SCRATCH / "parked").glob(f"{GREEN_NOTE}.*"))
    block("RUN A3 - ATTRIBUTION: a red that is not the capture's does not cost the capture",
          f"The tree now holds a note that PASSES the placement gate and a test file that fails on\n"
          f"purpose. A gate step that assumed the capture was to blame would park a good note over\n"
          f"somebody else's red test, and write a journal line that reads as an attribution\n"
          f"nothing measured.\n\n{chr(10).join(read_journal(cron3.LOG))}\n\n"
          f"raised: {raised3}\n"
          f"the note is back in the tree byte for byte: {same}\n"
          f"parked copies left behind: {[p.name for p in left_parked]}\n\n"
          f"Both readings are red and both name the same failing test - the fixture's, never the\n"
          f"note's - and that is the whole of the attribution:\n"
          f"the capture is exonerated by measurement rather than by a rule about which files are\n"
          f"whose. The cycle is RED either way; what the second reading decides is what happens to\n"
          f"the note.")
    if raised3 is None or not same or left_parked:
        raise Bail("the exoneration path did not restore the capture cleanly")

    # --- A3b: a red with TWO causes ---------------------------------------------------------------
    restore_tree(manifest_bytes)
    install_note(RED_NOTE)
    write_fixture_test()
    cron3b = load_cron(ORCHESTRA / "notes_cron.py", "cron_a3b", stub)
    raised3b = None
    try:
        cron3b.step_gates([RED_NOTE])
    except Exception as e:                                     # noqa: BLE001
        raised3b = f"{type(e).__name__}: {e}"
    gone3b = not (SRC_DIR / f"{RED_NOTE}.md").exists()
    # The newest only: A2 parked this same slug earlier in this run, and listing the whole glob
    # reads as though this branch had parked twice.
    parked3b = sorted((SCRATCH / "parked").glob(f"{RED_NOTE}.*.md"))[-1:]
    block("RUN A3b - a red with TWO causes does not acquit the capture",
          f"The tree holds the note that fails the placement gate AND the unrelated failing test.\n"
          f"Both readings are red, so a step that compared exit codes would restore the note - and\n"
          f"leave it in the manifest, where it is never recaptured and every later cycle wedges on\n"
          f"`captured=[]` under a journal line denying it had anything to do with the red. The\n"
          f"morning that produced this task was one failing test away from that state.\n\n"
          f"{chr(10).join(read_journal(cron3b.LOG))}\n\n"
          f"raised: {raised3b}\n"
          f"note still out of the tree: {gone3b}\n"
          f"parked by this run: {[q.name for q in parked3b]}\n\n"
          f"Two failures with the capture, one without: the difference is what the capture added,\n"
          f"and the tree being red for another reason as well acquits nobody. The comparison rides\n"
          f"the COUNT rather than the printed ids, because `scripts/push.sh` ends its test step with\n"
          f"`| tail -3` and a third failure would push an id off the end - two readings could then\n"
          f"print the same two names while differing by one test, and a set comparison would call\n"
          f"that an exoneration.")
    if raised3b is None or not gone3b or not parked3b:
        raise Bail("A3b: a capture that adds a failure to an already-red tree was not held")

    # --- A3d: both causes inside ONE test ---------------------------------------------------------
    restore_tree(manifest_bytes)
    install_note(RED_NOTE)
    install_twin()
    cron3d = load_cron(ORCHESTRA / "notes_cron.py", "cron_a3d", stub)
    raised3d = None
    try:
        cron3d.step_gates([RED_NOTE])
    except Exception as e:                                     # noqa: BLE001
        raised3d = f"{type(e).__name__}: {e}"
    gone3d = not (SRC_DIR / f"{RED_NOTE}.md").exists()
    block("RUN A3d - two offenders, one failing test: an equal count is not an acquittal",
          f"The tree holds this cycle's capture AND a second note breaking the same rule. The\n"
          f"placement gate is one unparametrised function looping over the corpus, so it fails ONCE\n"
          f"either way: both readings print `1 failed` and name the same id.\n\n"
          f"{chr(10).join(read_journal(cron3d.LOG))}\n\n"
          f"raised: {raised3d}\n"
          f"note out of the tree: {gone3d}\n\n"
          f"A comparison of counts alone calls this 'the same tests fail without the capture' and\n"
          f"restores a guilty note - which then sits in the manifest, is never recaptured, and\n"
          f"wedges every later cycle on `captured=[]` under yesterday's journal line saying the red\n"
          f"was not this cycle's. It is the exit-code defect one level down: the code was blind to\n"
          f"two causes, then the count was blind to two causes inside one test. What separates this\n"
          f"from A3 is not the count but WHICH test fails - a module under `tests/test_notes*` judges\n"
          f"the corpus, and an equal count there establishes nothing about this capture.\n"
          f"Found by Fable, in the fix for the first blindness.")
    if raised3d is None or not gone3d:
        raise Bail("A3d: an equal count over a corpus-level test was read as an acquittal")

    # --- A3e: the corpus test's name truncated off the top -----------------------------------------
    restore_tree(manifest_bytes)
    install_note(RED_NOTE)
    install_twin()
    write_fixture_test(2)
    cron3e = load_cron(ORCHESTRA / "notes_cron.py", "cron_a3e", stub)
    raised3e = None
    try:
        cron3e.step_gates([RED_NOTE])
    except Exception as e:                                     # noqa: BLE001
        raised3e = f"{type(e).__name__}: {e}"
    gone3e = not (SRC_DIR / f"{RED_NOTE}.md").exists()
    block("RUN A3e - the name the acquittal turns on is the one the door truncated away",
          f"A3d's tree plus TWO unrelated failing tests. Three tests fail in both readings, and\n"
          f"`scripts/push.sh` ends its test step with `| tail -3`, so only the last two `FAILED`\n"
          f"lines survive. The corpus test sorts first and is the one that falls off.\n\n"
          f"{chr(10).join(read_journal(cron3e.LOG))}\n\n"
          f"raised: {raised3e}\n"
          f"note out of the tree: {gone3e}\n\n"
          f"A3d's fix reads the printed ids to find a corpus-level test among them. Here the ids do\n"
          f"not contain one - not because none failed, but because the door printed two names for a\n"
          f"reading that declares three. An empty classification then reads as 'no corpus test\n"
          f"failed', which is the acquittal A3d exists to prevent, reached by a different road. It\n"
          f"is the same blindness a third level down: the exit code was blind to two causes, the\n"
          f"count to two causes in one test, and the id set to a cause outside the tail. Neither a\n"
          f"race nor a changing tree is needed - both readings here are byte-identical.\n\n"
          f"What closes it is that the COUNT survives what truncates the names, so the count audits\n"
          f"them: fewer names than the count declares means the set is incomplete, and a\n"
          f"classification drawn from an incomplete set is unknowable rather than negative. Only\n"
          f"the equal-count path is guarded - where the capture strictly adds failures the count\n"
          f"convicts on its own and no name is load-bearing (A3b is that control, and still passes).")
    if raised3e is None or not gone3e:
        raise Bail("A3e: a corpus failure truncated out of the ids was read as an acquittal")
    FIXTURE_TEST.unlink(missing_ok=True)

    # --- A3c: a red the comparison cannot read at all ---------------------------------------------
    restore_tree(manifest_bytes)
    install_note(GREEN_NOTE)
    FIXTURE_SCOPE.write_text(
        '"""Written and removed by evidence/RED-025-generator.py. It is bound to no ABI-*\n'
        'requirement, so `scripts/ratchet_scope.py` refuses the tree at step 2 of 7 and the suite\n'
        'never runs - which is how a red arrives with no failing test to name."""\n\n\n'
        "def unused() -> None:\n    return None\n", encoding="utf-8")
    cron3c = load_cron(ORCHESTRA / "notes_cron.py", "cron_a3c", stub)
    raised3c = None
    try:
        cron3c.step_gates([GREEN_NOTE])
    except Exception as e:                                     # noqa: BLE001
        raised3c = f"{type(e).__name__}: {e}"
    gone3c = not (SRC_DIR / f"{GREEN_NOTE}.md").exists()
    block("RUN A3c - a red the comparison cannot read is a third state, not a verdict",
          f"The tree holds a note that PASSES the gates and a module in `scripts/` bound to no\n"
          f"`ABI-*` requirement, so the door refuses at step 2 of 7 and the suite never runs. There\n"
          f"is no failing test to count in either reading, so the counterfactual asks a question the\n"
          f"instrument cannot answer.\n\n{chr(10).join(read_journal(cron3c.LOG))}\n\n"
          f"raised: {raised3c}\n"
          f"note out of the tree: {gone3c}\n\n"
          f"The capture stays parked and the journal says why in the state's own name. That is a\n"
          f"CHOICE and it is recorded as one: parking is reversible from a copy this step verified\n"
          f"by sha256 before removing anything, and the alternative - restoring on an unmeasured\n"
          f"acquittal - is the wedge A3b describes, arrived at silently. Note that this branch\n"
          f"parks an innocent note, which is the price, and it is the reversible half of the trade.")
    if raised3c is None or not gone3c:
        raise Bail("A3c: an unmeasurable attribution did not hold the capture")
    FIXTURE_SCOPE.unlink(missing_ok=True)

    # --- A4 / A5: the cycle, with and without the step ---------------------------------------------
    restore_tree(manifest_bytes)
    install_note(RED_NOTE)
    topics = SCRATCH / "topics.json"
    real = json.loads((ORCHESTRA / "notes_topics.json").read_text(encoding="utf-8"))
    kept = [t for t in real["topics"] if t["slug"] in json.loads(MANIFEST.read_text())["notes"]]
    topics.write_text(json.dumps({"topics": kept}, indent=2), encoding="utf-8")

    marker.unlink(missing_ok=True)
    cron4 = load_cron(ORCHESTRA / "notes_cron.py", "cron_a4", stub, topics)
    rc4 = cron4.run_cycle({}, "harness", 0, 0, "harness")
    reached4 = marker.exists()
    steps4 = [json.loads(ln)["step"] for ln in cron4.LOG.read_text(encoding="utf-8").splitlines()]
    journal4 = read_journal(cron4.LOG)

    mutated = SCRATCH / "notes_cron_MUTATED.py"
    diff = mutate(ORCHESTRA / "notes_cron.py",
                  "        step_gates(cap[\"captured\"])",
                  "        pass  # MUTATION: the gate step removed",
                  mutated)
    marker.unlink(missing_ok=True)
    cron5 = load_cron(mutated, "cron_a5", stub, topics)
    cron5.HERE = ORCHESTRA
    rc5 = cron5.run_cycle({}, "harness", 0, 0, "harness")
    reached5 = marker.exists()
    steps5 = [json.loads(ln)["step"] for ln in cron5.LOG.read_text(encoding="utf-8").splitlines()]
    journal5 = read_journal(cron5.LOG)

    block("RUN A4 / MUTATION A5 - the whole cycle, with the step and without it",
          f"Both runs are `run_cycle()` over the SAME tree, the one holding the red note. `DEPLOY`\n"
          f"is a stub that writes a marker file, so 'the deploy was reached' is a fact on disk -\n"
          f"and so that the mutation stops at a marker instead of publishing the note.\n\n"
          f"A4, the file as it stands:\n{chr(10).join(journal4)}\n"
          f"  steps journalled : {steps4}\n"
          f"  exit code        : {rc4}   (1 = RED)\n"
          f"  deploy reached   : {reached4}\n\n"
          f"A5, the same file with one line removed:\n{diff}\n{chr(10).join(journal5)}\n"
          f"  steps journalled : {steps5}\n"
          f"  exit code        : {rc5}\n"
          f"  deploy reached   : {reached5}\n\n"
          f"The mutation is the measurement of the gate. Without that one call the cycle carries a\n"
          f"note the repository's own tests refuse all the way to the door of the publication\n"
          f"channel.\n\n"
          f"WHY A5's EXIT CODE IS ALSO 1, AND WHY THAT IS NOT THE GATE DOING ITS JOB. The mutated\n"
          f"run goes red at `published`, three steps AFTER the deploy: `DEPLOY` is a stub that\n"
          f"publishes nothing, so the URL the build made new does not answer 200 when the cycle\n"
          f"reads it back. Against the real `deploy.sh` that URL would have been live, `published`\n"
          f"would have been green, and the cycle would have gone on to submit the address of a page\n"
          f"failing this repository's own tests to Bing. Both exit codes are 1 and they mean\n"
          f"opposite things - which is exactly why the marker file is what this run measures and\n"
          f"the exit code is not. This paragraph is reasoning about a run that was deliberately not\n"
          f"made, and it is marked as such rather than presented as a reading.")
    if reached4 or rc4 != 1:
        raise Bail(f"A4: the cycle reached the deploy ({reached4}) or was not RED (rc={rc4})")
    if not reached5:
        raise Bail("A5: the mutation did not change the outcome, so A4 proves nothing about the gate")


def read_journal(path: pathlib.Path) -> list[str]:
    """The journal, with each line's `detail` shown by its VERDICT rather than by its first 150 characters.

    The first draft printed `detail[:150]`, and every gate line therefore opened on "1/7 secrets,
    secret scan: clean" - the head of a gate run, which is identical whether the run passed or
    failed. The artefact read as though the step had recorded nothing useful while the journal on
    disk held the failing test's name all along. A truncation that always shows the same characters
    is the same defect as a check that always returns the same answer.
    """
    if not path.exists():
        return ["(the step wrote no journal line at all)"]
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        r = json.loads(ln)
        detail = str(r.get("detail", ""))
        verdict = [x.strip() for x in detail.splitlines()
                   if x.startswith(("FAILED", "ERROR")) or " passed" in x or " failed" in x]
        shown = " | ".join(verdict) if verdict else detail[:150]
        out.append(f"  [{r['state']:24}] {r['step']:8} {shown[:400]}")
    return out


# --- PART B: the capture ----------------------------------------------------------------------------

def git_blob(sha: str, path: str = "notes_gen.py") -> bytes | None:
    """A revision's file as BYTES.

    `run()` strips its output, which is right for a log a human reads and wrong here by exactly one
    trailing newline - and a byte comparison against a provenance hash that is off by one byte
    reports "no committed revision produced this note", which is a finding rather than a bug in the
    reader. Nothing about the file is normalised on this path.
    """
    p = subprocess.run(["git", "show", f"{sha}:{path}"], cwd=str(ORCHESTRA),
                       capture_output=True, timeout=60)
    return p.stdout if p.returncode == 0 else None


def previous_generator() -> tuple[str, pathlib.Path]:
    """`notes_gen.py` as it stood before the placement rule was written, out of the history.

    RED-024 set this precedent and the reason holds here: a mutation is an edit somebody chose, and
    the state it claims to restore is a state that really existed and can be fetched instead of
    approximated. The commit is not named by hand either - it is the newest one whose blob does not
    define `measure_placement`, so the artefact cannot drift onto the wrong revision when this file
    is re-run after later commits.
    """
    rc, out = run(["git", "log", "--format=%H", "--", "notes_gen.py"], cwd=ORCHESTRA)
    if rc != 0:
        raise Bail("~/orchestra has no history for notes_gen.py; the 'before' state is unreachable")
    for sha in out.split():
        blob = git_blob(sha)
        if blob is not None and b"def measure_placement" not in blob:
            dest = SCRATCH / f"notes_gen_{sha[:7]}.py"
            dest.write_bytes(blob)
            return sha[:7], dest
    raise Bail("every revision of notes_gen.py already carries measure_placement")


def revision_with_blob(digest: str) -> str:
    """The short sha of the `notes_gen.py` revision whose blob hashes to `digest`, or a named miss.

    Never a bare "unknown": a provenance hash that matches no committed revision means the capture
    ran from a working copy that was never committed, which is a different fact from one this
    function failed to look up.
    """
    rc, out = run(["git", "log", "--format=%H", "--", "notes_gen.py"], cwd=ORCHESTRA)
    if rc != 0:
        return "(~/orchestra's history could not be read)"
    for sha in out.split():
        blob = git_blob(sha)
        if blob is not None and hashlib.sha256(blob).hexdigest() == digest:
            return sha[:7]
    return "(no committed revision: the capture ran from an uncommitted working copy)"


def real_topic(slug: str) -> dict:
    """The topic as `notes_topics.json` declares it - `measure_ordinals` reads its `subject`."""
    spec = json.loads((ORCHESTRA / "notes_topics.json").read_text(encoding="utf-8"))
    return next(t for t in spec["topics"] if t["slug"] == slug)


def tripwire(*_a, **_k):
    raise AssertionError("TRIPWIRE: a model call was attempted")


def canned_plan(front: dict, body: str) -> dict:
    """The plan the capture would have produced, taken back out of the note it produced.

    Every field the placement rule reads is the model's own output from that morning, not a string
    written here to fail a check: `title`, `h1` and `description` are lifted verbatim from the
    captured front matter, and the sections are its real headings.
    """
    return {"title": front["title"], "h1": front["h1"], "description": front["description"],
            "lead_brief": "", "faq": [],
            "sections": [{"heading": h, "purpose": "", "must_cover": [], "target_chars": 900,
                          "figure": None} for h in re.findall(r"^## (.+)$", body, re.M)]}


def capture_attempt(gen_path: pathlib.Path, name: str, slug: str) -> str:
    """Run `build()` with the drafting stubbed and every model call wired to a tripwire.

    What runs for real is everything that decides: `resolve_key`, `check_addresses`,
    `read_excerpt`, and the placement measurement. What is stubbed is the drafting - and the stub is
    a tripwire rather than canned prose, because the claim being measured is that the capture
    refuses BEFORE it spends a model call, and the only way to measure that is to make spending one
    an error.
    """
    gen = load_module(gen_path, name)
    gen.HERE = ORCHESTRA
    gen.TOPICS = ORCHESTRA / "notes_topics.json"
    gen.LOG = SCRATCH / f"{name}.jsonl"
    front, body = note_parts(slug)
    topic = next(t for t in json.loads(gen.TOPICS.read_text(encoding="utf-8"))["topics"]
                 if t["slug"] == slug)
    gen.plan_note = lambda *_a, **_k: canned_plan(front, body)
    gen.ask = tripwire
    gen.ask_json = tripwire
    try:
        gen.build(topic, gen.load_base())
    except Exception as e:                                     # noqa: BLE001 - the class is the result
        return f"{type(e).__name__}: {e}"
    return "no exception: the capture ran to the end"


def part_b() -> None:
    gen_path = ORCHESTRA / "notes_gen.py"
    gen = load_module(gen_path, "gen_read")
    gen.HERE = ORCHESTRA

    readings = []
    for slug in (RED_NOTE, GREEN_NOTE):
        front, body = note_parts(slug)
        misses = gen.measure_all(body, front["keys"], real_topic(slug),
                                 {k: front[k] for k in ("title", "h1", "description")})
        placement = [m for m in misses if "primary key" in m or "primary role" in m]
        readings.append(f"  {slug}\n"
                        f"    title       : {front['title']!r}\n"
                        f"    primary key : {gen.primary_key(front['keys'])}\n"
                        f"    placement misses: {len(placement)}\n"
                        + "".join(f"      - {str(m)[:110]}  [fatal={m.fatal}]\n" for m in placement))
    block("RUN B1 - the rule the tests held alone, measured at capture time",
          "`measure_all()` over the two notes that scheduled cycle really captured, with the fold\n"
          "imported from `tests/notes_support.py` - the gate's own reader, not a second copy:\n\n"
          + "\n".join(readings) +
          "\nOne fails in three places and one passes, so the check is not a ritual refusal: it\n"
          "discriminates between two bodies of prose a model wrote twenty minutes apart. The lead\n"
          "of the failing note DOES carry the key, which is why the miss is `fatal` - a paragraph\n"
          "rewriter cannot reach a title.")

    red = capture_attempt(gen_path, "gen_b2", RED_NOTE)
    green = capture_attempt(gen_path, "gen_b3", GREEN_NOTE)
    rfront, rbody = note_parts(RED_NOTE)
    sections = len(canned_plan(rfront, rbody)["sections"])
    block("RUN B2 - the refusal lands after the PLAN and before the prose, and the control proves it",
          f"`build()` with `plan_note` answered from the note's own captured front matter, and\n"
          f"`ask`/`ask_json` replaced by a tripwire that raises if a model call is attempted:\n\n"
          f"  {RED_NOTE}\n    -> {red}\n\n"
          f"  {GREEN_NOTE}\n    -> {green}\n\n"
          f"The control is the whole of the reading. A refusal on its own says nothing about WHEN\n"
          f"it happened; the green note reaching the tripwire says the capture goes on to write\n"
          f"prose when the placement is right, so the red note's refusal is attributable to the\n"
          f"placement and not to the harness.\n\n"
          f"ONE MODEL CALL IS STILL SPENT, AND AN EARLIER DRAFT OF THIS HEADING DENIED IT. The plan\n"
          f"is itself a call - `plan_note()` is `ask_json(claude-sonnet-5, ...)`, and the real run's\n"
          f"journal has it at 05:23:24 - and the placement rule cannot be read before it, because\n"
          f"the title it judges is what the plan produces. The refusal stands between the plan and\n"
          f"the prose. In this harness the plan is answered from the fixture, so the tripwire does\n"
          f"not see that call by construction: 'before the first model call' would have been a claim\n"
          f"about the harness's own shape. Found by Fable.\n\n"
          f"What the refusal saves is counted rather than described: the plan it stopped carries\n"
          f"{sections} sections, so the calls not made are {sections} prose calls plus the lead, plus the FAQ\n"
          f"answers, plus up to REPAIR_MAX (6) repair calls - on a note that could not have been\n"
          f"published by any of them.")
    if "Refusal" not in red or "TRIPWIRE" in red:
        raise Bail(f"B2: the red note did not refuse before a model call: {red}")
    if "TRIPWIRE" not in green:
        raise Bail(f"B2 control: the green note did not reach a model call: {green}")

    sha, before = previous_generator()
    before_red = capture_attempt(before, "gen_before", RED_NOTE)
    pinned = note_parts(RED_NOTE)[0]["provenance"]["generator_sha256"]
    pin_rev = revision_with_blob(pinned)
    block("RUN B3 - the same note through the generator as it stood before this commit",
          f"Not a mutation: `git show {sha}:notes_gen.py` out of `~/orchestra`'s own history. The\n"
          f"revision is chosen by a PROPERTY rather than by hand - the newest one whose blob does\n"
          f"not define `measure_placement` - so re-running this file after later commits cannot\n"
          f"quietly move the measurement onto the wrong code. Same tripwire:\n\n"
          f"  {RED_NOTE} -> {before_red}\n\n"
          f"The model call is reached. Before this commit nothing in the capture read the placement\n"
          f"rule at all, so a plan that put the primary key nowhere near the title bought six prose\n"
          f"calls, a lead, the FAQ answers and a published note.\n\n"
          f"WHAT THIS RUN IS NOT, AND THE DRAFT THAT SAID IT WAS. The first version of this\n"
          f"paragraph called {sha} 'the file that captured this note at 05:22'. It is not, and the\n"
          f"note says so itself: its `provenance.generator_sha256` is {pinned[:16]}..., which is the\n"
          f"blob of {pin_rev} - a revision committed at 05:31:56, nine minutes INTO a run that had\n"
          f"started at 05:22 and whose journal logs `write`, a step that revision no longer has.\n"
          f"`build()` hashes the generator by re-reading it from disk at the END of a fourteen-minute\n"
          f"capture, so a file edited mid-run is pinned by a note the previous code produced. That is\n"
          f"a provenance field claiming more than its artefact, in the project built to find those;\n"
          f"it is recorded in `~/orchestra/FINDINGS.md` and not fixed here, because it is a change to\n"
          f"what a published note's provenance MEANS and needs its own red run. Neither revision\n"
          f"carries the placement rule, so this measurement stands under either.")
    if "TRIPWIRE" not in before_red:
        raise Bail(f"B3: the pre-commit generator refused before a model call, so the rule already "
                   f"existed and this whole part measures nothing: {before_red}")

    m1 = SCRATCH / "notes_gen_MUT1.py"
    d1 = mutate(gen_path, "    if early:", "    if False:  # MUTATION: the early refusal disarmed", m1)
    m1_red = capture_attempt(m1, "gen_mut1", RED_NOTE)

    m2 = SCRATCH / "notes_gen_MUT2.py"
    d2 = mutate(gen_path, "            + measure_placement(keys, placement_fields(body, front)))",
                "            )  # MUTATION: placement removed from the assembled-body measurement", m2)
    gen2 = load_module(m2, "gen_mut2")
    gen2.HERE = ORCHESTRA
    front, body = note_parts(RED_NOTE)
    m2_misses = gen2.measure_all(body, front["keys"], real_topic(RED_NOTE),
                                 {k: front[k] for k in ("title", "h1", "description")})
    m2_placement = [m for m in m2_misses if "primary key" in m]
    block("MUTATIONS B4 / B5 - each copy of the rule killed on its own",
          f"The rule is read twice: once the moment the plan exists, and once over the assembled\n"
          f"body inside `measure_all()`. The first is an accelerator and the second is the one\n"
          f"nothing can be staged past, so each has to be shown to be armed by itself.\n\n"
          f"B4 - the early reading removed:\n{d1}\n"
          f"  {RED_NOTE} -> {m1_red}\n"
          f"  The tripwire fires: without that call the capture spends prose calls on a note that\n"
          f"  cannot be published. What this run does NOT show is the later refusal - the tripwire\n"
          f"  ends the capture at the first model call, so nothing here executes `measure_all`. That\n"
          f"  the second reading holds the same rule is B1's measurement (3 misses over this note)\n"
          f"  and B5's (removing it drops them to 0), not this one's.\n\n"
          f"B5 - the reading inside `measure_all` removed:\n{d2}\n"
          f"  placement misses over the same red note: {len(m2_placement)} (was 3)\n"
          f"  This mutation leaves the early reading standing, so it does not show a capture running\n"
          f"  to completion over a red note - B3 is where that state is measured, from the history\n"
          f"  rather than from an edit. What it does show is that the second reading is the one that\n"
          f"  carries the rule: with it removed the assembled body measures clean, and the only\n"
          f"  thing left between this note and `stage()` is an accelerator B4 has just killed.")
    if "TRIPWIRE" not in m1_red:
        raise Bail(f"B4: removing the early reading changed nothing, so it was never armed: {m1_red}")
    if m2_placement:
        raise Bail("B5: the mutation did not remove the placement reading")


# --- main -------------------------------------------------------------------------------------------

HEADER = """RED-025 - A NOTE THE REPOSITORY'S OWN GATES REFUSE HAD NOTHING BETWEEN IT AND THE LIVE SITE

Generated by `evidence/RED-025-generator.py`. Everything below a heading is verbatim output of the
run named in that heading; nothing is retyped. The subjects are `~/orchestra/notes_cron.py` and
`~/orchestra/notes_gen.py`, which are outside this repository by D-17 and D-19, and the fixture is
`~/orchestra/quarantine/20260824T063401Z/` - the two notes the scheduled cycle really captured on
2026-08-24, one of which fails `tests/test_notes.py` and one of which does not.

WHAT A READER SHOULD CHECK RATHER THAN TRUST. Every claim here is a mutation or a control, because a
red run proves a gate is armed against the mutation that produced it and against no other (L-26):

  * A1 shows two instruments disagreeing about one tree. Re-runnable by hand in ten seconds.
  * A2 and A3 are the two branches of the SAME red gate. They differ in what happens to the
    capture, and the difference is a second measurement rather than a rule about whose file it is.
  * A3b, A3d and A3e are one defect found three times, each inside the fix for the last: the exit
    code could not see two causes, then the test COUNT could not see two causes inside one test
    function, then the id SET could not see a cause the door's `| tail -3` had truncated away. Read
    them in that order; the third needs no race and no changing tree, and A3 remains the control
    that a capture which really is innocent still goes back into the tree.
  * A5 removes the gate call and the red note reaches the deploy door. A4 is worth nothing without
    it: a cycle that would have stopped anyway proves no gate.
  * B2's control is the green note reaching the tripwire. Without it, "refused before a model call"
    would be a claim about a code path nobody watched execute.
  * B3 is not a mutation at all - it is the generator's own previous revision, fetched from
    `~/orchestra`'s history, so the "before" state is the one that really existed.
  * B4 and B5 kill the two copies of the placement rule separately, because a rule read in two
    places can be armed in one and decorative in the other (L-21).

WHAT IS NOT ASSERTED HERE, AND THE LIST IS LONGER THAN THE FIRST DRAFT'S.

  * NOT that a red note can never reach the deploy. What is measured is that the note in the tree
    WHEN THE GATES RAN cannot. `step_gates` reads the tree once, and `deploy.sh` ships the tree as
    it stands several steps later, so a note written into `web/notes/src/` by a concurrent capture
    in between would pass `step_tree` by construction - both its halves are cycle-owned - and go
    out. Narrow, and it needs a second writer, but "cannot reach" is a universal and this is not
    one. Named in `~/orchestra/FINDINGS.md`. Found by Fable.
  * NOT that the fixture note is the only note that could fail these gates. The placement rule is
    one of several the suite holds, and `step_gates` is indifferent to which one goes red.
  * NOT that the deploy would have succeeded in A5. `DEPLOY` is a stub; what A5 measures is that
    the cycle REACHED it.
  * NOTHING at all about whether provek.dev currently serves a bad note. That is a reading of the
    origin, and this file reads a working tree.

RE-RUNNING IT NEEDS A COMMITTED TREE. A1's control is `scripts/publishable_tree.py`, which counts
any uncommitted file - including this generator and this artefact - as foreign work and refuses.
The instrument therefore declines to demonstrate a clean-tree property on a dirty tree, which is
correct of it and is why the generator is committed before the artefact it writes is regenerated.

HOW THIS FILE BEHAVED WHILE IT WAS BEING WRITTEN, WHICH BELONGS HERE RATHER THAN IN A COVER NOTE.
Re-running it should reproduce this artefact except for timestamps and pytest durations; two
consecutive runs of THIS revision did, compared with `git diff` against the committed copy. The
three-run comparison quoted here before was of the revision without A3e and is not evidence about
this one. A run of a still earlier revision exited without writing the artefact, and the cause was
lost because only the last four lines of its output were kept. It has not recurred and it is not
explained. What was fixed is the
reason it could not be diagnosed: the block printer now flushes, and a `Bail` prints on both
streams, because stdout is block-buffered when piped and stderr is not, so the refusal had been
arriving above the block it followed. An unexplained failure in the instrument is worth less than
an explained one and more than a silence, so it is written here rather than left out.
"""


def main() -> int:
    # PRINTED, NOT ONLY WRITTEN. The header goes into the artefact file, and a reader who has this
    # run's stdout but not the repository - which is the judge's situation on this host - would have
    # been told about limits they could not see. The brief for round two asserted the log contained
    # the artefact; it did not, and that was a claim about an artefact made without reading it.
    print(HEADER, flush=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "evidence" /
                                         "RED-025-a-red-note-had-nothing-between-it-and-the-live-site.txt"))
    args = ap.parse_args()

    if not QUARANTINE.exists():
        raise Bail(f"{QUARANTINE} is missing: this run's fixture is a real capture, and inventing "
                   f"a substitute would make the evidence weaker than the sentence describing it")
    state = ORCHESTRA / "logs" / "notes_cron.state.json"
    today = time.strftime("%Y-%m-%d", time.gmtime())
    if not state.exists() or json.loads(state.read_text(encoding="utf-8")).get("last_cycle_day") != today:
        raise Bail("the scheduled cycle has not yet run today, so it could fire into the tree while "
                   "this harness is holding a deliberately red note in it")

    base_porcelain = porcelain()
    manifest_bytes = MANIFEST.read_bytes()
    for slug in (RED_NOTE, GREEN_NOTE):
        if (SRC_DIR / f"{slug}.md").exists():
            raise Bail(f"{slug} is already in the tree; this harness would overwrite a real capture")
    SCRATCH.mkdir(parents=True, exist_ok=True)

    try:
        part_a(manifest_bytes)
        part_b()
    finally:
        restore_tree(manifest_bytes)
        shutil.rmtree(SCRATCH, ignore_errors=True)
        rc, out = gates()
        end_porcelain = porcelain()

    block("CLOSING CONTROL - the tree this run measured is the tree it leaves behind",
          f"The fixtures are removed, the manifest is restored from the bytes read before anything\n"
          f"was written, and the site is rebuilt by the gate run itself:\n\n"
          f"$ ./scripts/push.sh --gates-only\n{gates_verdict(rc, out)}\n\n"
          f"git status --porcelain, before and after:\n"
          f"  before: {base_porcelain.splitlines() or ['(clean)']}\n"
          f"  after : {end_porcelain.splitlines() or ['(clean)']}\n"
          f"  identical: {base_porcelain == end_porcelain}\n"
          f"  manifest sha256 unchanged: "
          f"{hashlib.sha256(MANIFEST.read_bytes()).hexdigest() == hashlib.sha256(manifest_bytes).hexdigest()}\n\n"
          f"A red run that changed the tree it was measuring is not evidence, so this is a\n"
          f"precondition of the artefact being written rather than a note at the end of it.")
    if base_porcelain != end_porcelain or rc != 0:
        raise Bail("the tree did not come back to what it was; the artefact is NOT written")

    bodies = [b for _, b in BLOCKS]
    if len(set(bodies)) != len(bodies):
        raise Bail("two blocks carry identical output - one of the runs did not happen (L-26)")

    text = HEADER + "\n" + "\n\n".join(
        f"{'=' * 98}\n{h}\n{'=' * 98}\n\n{b}" for h, b in BLOCKS) + "\n"
    pathlib.Path(args.out).write_text(text, encoding="utf-8")
    print(f"\nwritten: {args.out} ({len(text)} bytes, {len(BLOCKS)} blocks)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Bail as e:
        # On BOTH streams and after a flush: see `block()`. A refusal that lands where nobody looks
        # is the defect this repository is named for.
        sys.stdout.flush()
        print(f"\nBAIL: {e}", flush=True)
        print(f"BAIL: {e}", file=sys.stderr, flush=True)
        raise SystemExit(2)
