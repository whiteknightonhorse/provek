#!/usr/bin/env python3
"""Produces evidence/RED-024-a-note-source-outlived-its-manifest-line.txt.

    python3 evidence/RED-024-generator.py --generator /tmp/before.py --out <artefact>
    python3 evidence/RED-024-generator.py --append --out <artefact>

The first run judges the pre-repair generator, recovered with `git -C ~/orchestra show <sha>:
notes_gen.py`; the second judges the one in place now and appends its verdict to the same file. The
artefact is therefore two runs of ONE tool over two versions of its subject, not a run and a
paragraph about a run.

T-C7 - prove what a kill between the source write and the manifest write leaves behind.

WHAT IS UNDER TEST. `notes_gen.py` publishes each method note as TWO artefacts that the readers
pin to each other: the prose at `web/notes/src/<slug>.md` and one line of
`web/notes/manifest.json`. `loadNotes()` in `web/notes/emit.mjs` throws when it meets a source
whose slug the manifest does not hold, and `tests/test_notes_freshness.py` refuses both directions
of the same mismatch. So the pair is a transaction, and until this harness existed nothing had ever
measured whether the generator writes it as one.

HOW A KILL IS SIMULATED, AND WHY THIS IS STRONGER THAN KILLING ONCE. Every primitive that can
change a byte under `web/notes/` is wrapped, and after each call the READER-VISIBLE state - the
`*.md` files and the manifest - is copied out. Each copy is, byte for byte, the tree a kill at that
instant would leave; replaying all of them covers every kill point instead of the one a single
`SIGKILL` happens to hit. Phase two then does send a real `SIGKILL` at the worst point the replay
found, because a simulation that has never been confirmed against the thing it simulates is a
model, not a measurement.

TORN WRITES ARE A KILL POINT TOO. `Path.write_text` is not atomic: a kill inside it leaves a
truncated file. Every non-atomic mutation of a reader-visible path therefore also gets replayed
with the file cut in half. A publish built only out of `os.replace` has no such state, and that is
part of what this measures rather than something it assumes.

NO MODEL IS CALLED. The plan and the prose are read back out of the note this repository already
carries and handed to `build()` through the same three seams a model would answer on, so
`measure()`, `measure_links()`, `check_addresses()` and the whole assembly path run FOR REAL
against real prose. What is stubbed is the drafting; what is measured is the writing.

THIS FILE IS IN THE REPOSITORY AND ITS SUBJECT IS NOT, WHICH IS DELIBERATE BOTH WAYS. `notes_gen.py`
stays outside for D-17's reason: every `*.py` under `scripts/` must be bound to an `ABI-*`
requirement, the specification carries no requirement about page generation, and binding one anyway
is the rubber stamp `scripts/ratchet_scope.py` exists to refuse. The harness comes INSIDE anyway,
in one copy rather than two, because a checker kept in both places is a rule written twice (L-2) and
the pair drifts the first time either moves. The cost is named, not hidden, and it is the same cost
D-17 already accepted: FROM A CLONE THIS CANNOT RUN. It exits 2 and says so, rather than reporting
a clean sweep over a generator it never found.

EXIT CODES
    0  no kill point leaves a tree on which `loadNotes()` throws
    1  at least one does - the tree is red at some instant of the capture
    2  the harness could not run to a verdict (missing note, missing node, missing repo)
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys

ORCHESTRA = pathlib.Path.home() / "orchestra"
"""Where the generator and its topic list live. Absent in a clone - see the note above."""

REAL_REPO = pathlib.Path(__file__).resolve().parents[1]
SCRATCH = pathlib.Path("/tmp/pv-notes-kill-window")
REPO = SCRATCH / "repo"
SNAPS = SCRATCH / "snapshots"

SEED_NOTE = "not-measured-is-not-zero"
SECOND_SLUG = "kill-window-second-note"

FRONT_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


class Bail(Exception):
    """The harness cannot reach a verdict. Never confused with a red verdict."""


def stranded() -> list[str]:
    """Files under `web/notes/` that the capture put there and no reader will ever enumerate.

    STRANDED IS DEFINED AGAINST THE COMMITTED SHAPE, not against a list of suffixes this harness
    happens to expect. Anything present in the scratch tree that the repository does not carry at
    the same path - and that is neither the manifest nor a `src/*.md` - was left by the run. Naming
    the leftovers by pattern would have found `.staged` and `.tmp` because those are the two the
    author already knew about, which is the shape of a fixture built from one example of a defect.
    """
    notes = REPO / "web" / "notes"
    if not notes.exists():
        return []
    out = []
    for f in sorted(notes.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(notes)
        if str(rel) == "manifest.json" or (rel.parent.name == "src" and f.suffix == ".md"):
            continue
        if (REAL_REPO / "web" / "notes" / rel).exists():
            continue  # committed beside the notes, e.g. emit.mjs - not something a kill left
        out.append(str(rel))
    return out


# --- the scratch tree ----------------------------------------------------------------------------

def build_scratch() -> None:
    """A full copy of the repository, minus the three directories nothing here reads.

    The copy is what gets written into: a harness that measures a generator by letting it write to
    the real tree has already changed the thing it was measuring.
    """
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH)
    SCRATCH.mkdir(parents=True)
    SNAPS.mkdir()
    r = subprocess.run(
        ["rsync", "-a", "--exclude", ".git", "--exclude", "node_modules", "--exclude", "dist",
         f"{REAL_REPO}/", f"{REPO}/"],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise Bail(f"rsync of the repository failed: {r.stderr.strip()[:300]}")
    # The capture starts from NO notes, because that is the state in which the window is widest:
    # a source lands with no line anywhere that could already have covered it.
    src = REPO / "web" / "notes" / "src"
    for f in src.glob("*.md"):
        f.unlink()
    (REPO / "web" / "notes" / "manifest.json").write_text('{\n  "notes": {}\n}\n', encoding="utf-8")


def reset_tree() -> None:
    """Rewind the scratch tree to the state a capture starts from: no notes, an empty manifest."""
    src = REPO / "web" / "notes" / "src"
    if not src.exists():
        raise Bail(f"{src} does not exist - phase one has not built the scratch tree")
    for f in list(src.iterdir()):
        f.unlink()
    (REPO / "web" / "notes" / "manifest.json").write_text('{\n  "notes": {}\n}\n', encoding="utf-8")


def sha256_of(p: pathlib.Path) -> str:
    import hashlib  # noqa: PLC0415 - one call, in the reporting path only
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def scratch_topics(real_topics: pathlib.Path) -> pathlib.Path:
    """The seed topic, and a second copy of it under another slug.

    TWO notes, not one, and the second is the point. The manifest is written once at the END of
    `main()`, so the window the task names is not "between two adjacent statements" - it is "for as
    long as every remaining note takes to draft". A single-topic run measures the narrow reading of
    the defect and would report the wide one as absent.
    """
    spec = json.loads(real_topics.read_text(encoding="utf-8"))
    seed = next((t for t in spec["topics"] if t["slug"] == SEED_NOTE), None)
    if seed is None:
        raise Bail(f"{real_topics}: no topic with slug {SEED_NOTE!r}")
    second = copy.deepcopy(seed)
    second["slug"] = SECOND_SLUG
    out = SCRATCH / "topics.json"
    out.write_text(json.dumps({"topics": [seed, second]}, indent=2), encoding="utf-8")
    return out


# --- the drafting seams, answered from prose that already exists ----------------------------------

def reconstruct(note: pathlib.Path) -> tuple[dict, str, list[dict]]:
    """(front matter, lead paragraph, sections) taken back out of a captured note.

    `build()` reassembles a body as lead + `## heading` + prose + optional figure marker, so the
    same note read back through this function and handed to the stubs reassembles byte for byte -
    which is what lets `measure()` run for real instead of against prose written to pass it.
    """
    m = FRONT_RE.match(note.read_text(encoding="utf-8"))
    if not m:
        raise Bail(f"{note}: no front matter, nothing to reconstruct from")
    front = json.loads(m.group(1))
    blocks = m.group(2).strip().split("\n\n")
    if not blocks or blocks[0].startswith("#"):
        raise Bail(f"{note}: does not open on a lead paragraph")
    lead, sections, cur = blocks[0], [], None
    for b in blocks[1:]:
        if b.startswith("## "):
            cur = {"heading": b[3:].strip(), "parts": [], "figure": None}
            sections.append(cur)
        elif cur is None:
            raise Bail(f"{note}: a block sits before the first heading")
        elif b.startswith("{{figure:"):
            cur["figure"] = b[len("{{figure:"):-len("}}")]
        else:
            cur["parts"].append(b)
    if not sections:
        raise Bail(f"{note}: no H2 sections")
    return front, lead, sections


def install_drafting_stubs(gen, front: dict, lead: str, sections: list[dict]) -> None:
    prose = {s["heading"]: "\n\n".join(s["parts"]) for s in sections}

    def plan_note(topic, keys, faq_rows, material):  # noqa: ARG001 - the seam's signature
        return {
            "title": front["title"],
            "h1": front["h1"],
            "description": front["description"],
            "lead_brief": "replayed from a captured note; no model was asked",
            "sections": [{"heading": s["heading"], "purpose": "replayed", "must_cover": [],
                          "target_chars": len(prose[s["heading"]]), "figure": s["figure"]}
                         for s in sections],
            "faq": [],
        }

    def write_section(sec, topic, material, prior, retry_note=""):  # noqa: ARG001 - the seam
        return prose[sec["heading"]]

    def ask(model, prompt, step, timeout=900):  # noqa: ARG001 - the seam
        if step == "lead":
            return lead
        raise Bail(f"the replay reached an unstubbed model call: {step!r}")

    gen.plan_note = plan_note
    gen.write_section = write_section
    gen.ask = ask


# --- the filesystem, watched ----------------------------------------------------------------------

class Watch:
    """Every mutation of a reader-visible path, and the tree it leaves behind.

    ATOMIC vs TORN-ABLE is recorded per mutation and is half the verdict. `os.replace` publishes a
    path in one syscall; `Path.write_text` opens, truncates and writes, so a kill inside it leaves a
    file that exists and is not what it claims to be - a state no ordering of writes can rescue and
    only an atomic publish can remove.
    """

    def __init__(self, src_dir: pathlib.Path, manifest: pathlib.Path):
        self.src_dir, self.manifest = src_dir, manifest
        self.events: list[dict] = []
        self.states: list[dict] = []
        self._last_visible: dict | None = None

    def visible(self, path: pathlib.Path) -> bool:
        p = pathlib.Path(path)
        return p == self.manifest or (p.parent == self.src_dir and p.name.endswith(".md"))

    def snapshot(self) -> dict:
        """The reader-visible pair, plus EVERY leftover a kill can strand under `web/notes/`.

        The first draft listed leftovers in `web/notes/src/` only, so a kill between the manifest's
        temporary write and its rename - which strands `web/notes/.manifest.json.tmp` one directory
        up - had no column that could show it. A report whose shape cannot express a state is not
        reporting that the state is absent; it is not looking. Found by Fable.
        """
        md = {}
        if self.src_dir.exists():
            for f in sorted(self.src_dir.glob("*.md")):
                md[f.name] = f.read_text(encoding="utf-8")
        man = self.manifest.read_text(encoding="utf-8") if self.manifest.exists() else None
        return {"md": md, "manifest": man, "hidden": stranded()}

    def record(self, primitive: str, target: pathlib.Path) -> None:
        """ONE numbering for everything, and the summary table is printed from this same list.

        The first draft numbered the summary over visible mutations and the kill-point rows over all
        of them, so an artefact meant to be read as a sequence carried two sequences using the same
        word. That is the defect this repository keeps failing builds over, in the file that reports
        the defect. Every mutation under `web/notes/` is recorded and numbered here; `visible` is a
        column, never a second index.
        """
        snap = self.snapshot()
        self.events.append({"n": len(self.events) + 1, "primitive": primitive,
                            "target": str(target), "visible": self.visible(target),
                            "atomic": primitive in ("os.replace", "os.rename")})
        key = (json.dumps(snap["md"], sort_keys=True), snap["manifest"])
        if self._last_visible != key:
            self._last_visible = key
            self.states.append(dict(self.events[-1], snap=snap))

    def install(self) -> None:
        watch = self
        real_write_text = pathlib.Path.write_text
        real_replace, real_rename, real_unlink = os.replace, os.rename, pathlib.Path.unlink
        # UNINSTALLED THE MOMENT THE CAPTURE ENDS. The replay below rewrites the same two paths to
        # materialise each kill point; leaving the hooks armed would let the harness's own writes
        # append to the list of events it is reporting on, which is an instrument measuring itself.
        self._restore = lambda: (
            setattr(pathlib.Path, "write_text", real_write_text),
            setattr(pathlib.Path, "unlink", real_unlink),
            setattr(os, "replace", real_replace),
            setattr(os, "rename", real_rename))

        def write_text(self, data, *a, **kw):
            out = real_write_text(self, data, *a, **kw)
            watch.record("Path.write_text", self)
            return out

        def replace(a, b, **kw):
            out = real_replace(a, b, **kw)
            watch.record("os.replace", pathlib.Path(b))
            return out

        def rename(a, b, **kw):
            out = real_rename(a, b, **kw)
            watch.record("os.rename", pathlib.Path(b))
            return out

        def unlink(self, *a, **kw):
            out = real_unlink(self, *a, **kw)
            watch.record("Path.unlink", self)
            return out

        pathlib.Path.write_text = write_text
        pathlib.Path.unlink = unlink
        os.replace, os.rename = replace, rename

    def uninstall(self) -> None:
        self._restore()


# --- judging one tree -------------------------------------------------------------------------------

LOADNOTES = """
import {loadNotes} from "%s/web/notes/emit.mjs";
try { const n = loadNotes(); console.log("OK " + n.length); }
catch (e) { console.log("THROW " + e.message); }
"""


def materialise(snap: dict) -> None:
    """Put the scratch tree into exactly the state a snapshot describes, leftovers included.

    `hidden` names are relative to `web/notes/`, not to `src/`, because a kill can strand a file in
    either directory - the staged prose below and the manifest's temporary file above it. Writing
    them all into `src/` was this function's bug for exactly as long as the snapshot could only hold
    one of the two.
    """
    notes = REPO / "web" / "notes"
    src = notes / "src"
    for f in list(src.glob("*.md")):
        f.unlink()
    for name in stranded():
        (notes / name).unlink()
    for name, text in snap["md"].items():
        (src / name).write_text(text, encoding="utf-8")
    for name in snap["hidden"]:
        (notes / name).write_text("(stranded content elided by the replay)\n", encoding="utf-8")
    man = notes / "manifest.json"
    if snap["manifest"] is None:
        man.unlink(missing_ok=True)
    else:
        man.write_text(snap["manifest"], encoding="utf-8")


# The one test in the freshness module that refuses a manifest line whose note is not on disk -
# which is the exact state the repaired publish order leaves behind for two syscalls. It is named
# rather than counted because a summary line cannot say WHICH gate walked past a tree.
PAIR_GATE = "test_the_manifest_holds_nothing_that_is_not_a_note"

OUTCOME = re.compile(r"::(\w+)\s+(PASSED|FAILED|ERROR|SKIPPED)")


def pins(text: str | None) -> set[str] | None:
    """The slugs a manifest pins, or None when the manifest cannot be read AT ALL.

    AN UNPARSEABLE MANIFEST IS NOT AN EMPTY MANIFEST. Returning an empty set for a file torn in half
    would report "pins nothing" for a tree whose manifest is wreckage, and the two states are
    exactly the pair invariant 1 exists to keep apart. The first version of this report had no such
    distinction and simply crashed on `json.loads` of a torn file - which at least did not lie, but
    it took the whole run down with it and left a STALE artefact on disk under a fresh timestamp.
    """
    if text is None:
        return None
    try:
        return set(json.loads(text)["notes"])
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def judge(snap: dict) -> tuple[str, dict]:
    """(loadNotes verdict, per-test outcomes) for one materialised tree.

    THE FIRST DRAFT OF THIS FUNCTION COMMITTED THIS PROJECT'S FOUNDING DEFECT. It returned pytest's
    summary line, and the caller decided the tree was clean with `if "failed" in fresh`. So a run
    that printed `4 skipped` - the whole module DISARMED by its own `skipif`, having judged nothing -
    was counted as a gate that had looked and found nothing wrong. That is a refusal returned as a
    zero, in the artefact whose subject is refusals returned as zeroes. Found by Fable, against the
    very kill point the report then under-counted.

    So the outcomes come back per test and NOT collapsed: `passed` is a gate that ran and held,
    `failed` is a gate that ran and refused, `skipped` is `check_did_not_run` and is neither.
    """
    materialise(snap)
    r = subprocess.run(["node", "--input-type=module", "-e", LOADNOTES % REPO],
                       capture_output=True, text=True, cwd=REPO)
    if r.returncode != 0:
        raise Bail(f"node could not run loadNotes: {(r.stderr or r.stdout).strip()[:300]}")
    load = r.stdout.strip()
    t = subprocess.run([sys.executable, "-m", "pytest", "tests/test_notes_freshness.py",
                        "-v", "--tb=no", "-p", "no:randomly"],
                       capture_output=True, text=True, cwd=REPO)
    outcomes = dict(OUTCOME.findall(t.stdout))
    if not outcomes:
        raise Bail(f"pytest reported no test outcomes at all: {t.stdout.strip()[-400:]}")
    return load, outcomes


def fresh_line(outcomes: dict) -> str:
    """One line naming the three states apart, with the pair gate always spelled out."""
    n = {s: sum(1 for v in outcomes.values() if v == s) for s in ("PASSED", "FAILED", "SKIPPED")}
    pair = outcomes.get(PAIR_GATE, "ABSENT")
    return (f"{n['PASSED']} passed, {n['FAILED']} failed, {n['SKIPPED']} did not run"
            f"  |  {PAIR_GATE}: {pair}")


def torn(prev: dict, target: pathlib.Path) -> dict | None:
    """`prev` with `target` cut in half - the tree a kill INSIDE a non-atomic write leaves."""
    name = pathlib.Path(target).name
    src = REPO / "web" / "notes" / "src"
    snap = copy.deepcopy(prev)
    if pathlib.Path(target).parent == src:
        full = (SCRATCH / "final_md" / name)
        if not full.exists():
            return None
        snap["md"][name] = full.read_text(encoding="utf-8")[: len(full.read_text(encoding="utf-8")) // 2]
    else:
        full = SCRATCH / "final_manifest.json"
        if not full.exists():
            return None
        snap["manifest"] = full.read_text(encoding="utf-8")[: len(full.read_text(encoding="utf-8")) // 2]
    return snap


# --- phase two: an actual SIGKILL --------------------------------------------------------------------

def hard_kill_child(stop_after: int, generator: pathlib.Path) -> str:
    """Re-enter this file in a child that SIGKILLs itself after the Nth recorded mutation.

    The replay above is a claim about what a kill leaves. This is the kill. They are compared, and a
    disagreement is the harness being wrong rather than the generator being right.
    """
    r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve()),
                        "--child-kill-after", str(stop_after),
                        "--generator", str(generator)],
                       capture_output=True, text=True)
    if r.returncode != -signal.SIGKILL:
        return f"child did not die by SIGKILL (rc={r.returncode}): {(r.stderr or '').strip()[-300:]}"
    return ""


# --- the run -------------------------------------------------------------------------------------------

def load_generator(path: pathlib.Path):
    """Import the generator UNDER TEST, which is not always the one on disk beside this file.

    A red run is only evidence if it can be produced again. `--generator` takes any copy - in
    particular `git show <sha>:notes_gen.py` from `~/orchestra`'s history - so the run that proves
    the defect can be re-taken against the same bytes after the repair has landed, instead of being
    a paragraph asserting what the old code used to do.
    """
    import importlib.util  # noqa: PLC0415 - only this path needs it
    if not path.exists():
        raise Bail(f"no generator at {path}")
    spec = importlib.util.spec_from_file_location("notes_gen_under_test", path)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    return gen


def run_capture(kill_after: int | None, generator: pathlib.Path,
                refuse: bool = False) -> Watch:
    gen = load_generator(generator)

    src_dir = REPO / "web" / "notes" / "src"
    manifest = REPO / "web" / "notes" / "manifest.json"
    gen.REPO = REPO
    gen.SRC_DIR = src_dir
    gen.MANIFEST = manifest
    gen.TOPICS = scratch_topics(ORCHESTRA / "notes_topics.json")
    gen.LOG = SCRATCH / "notes_gen.jsonl"
    # `read_excerpt` resolves `@orchestra/...` against the generator's own directory. A copy under
    # /tmp - which is how the pre-repair version is replayed - would resolve those to nothing, so
    # the seam is pointed back at the real orchestra dir. Otherwise `--generator` would silently
    # change what the capture READS, not just how it writes, and the two runs being compared would
    # differ in more than the one thing under test.
    gen.HERE = ORCHESTRA

    seed = REAL_REPO / "web" / "notes" / "src" / f"{SEED_NOTE}.md"
    if not seed.exists():
        raise Bail(f"no captured note at {seed}: nothing to replay a capture from")
    front, lead, sections = reconstruct(seed)
    install_drafting_stubs(gen, front, lead, sections)
    if refuse:
        # An UNREPAIRABLE miss: `Miss.block` is None, so `repair()` returns it untouched and
        # `build()` raises `Refusal`. This is the shape of every miss that is a property of the
        # whole note - a body outside its size band, an unspent link - rather than of one paragraph.
        gen.measure = lambda body, keys: [gen.Miss("forced by the harness: an unrepairable miss")]

    watch = Watch(src_dir, manifest)
    if kill_after is not None:
        real_record = watch.record

        def record_then_maybe_die(primitive, target):
            real_record(primitive, target)
            if len(watch.events) >= kill_after:
                sys.stdout.flush()
                os.kill(os.getpid(), signal.SIGKILL)

        watch.record = record_then_maybe_die
    watch.install()

    sys.argv = ["notes_gen.py"]
    try:
        rc = gen.main()
    finally:
        watch.uninstall()
    if refuse and rc == 0:
        raise Bail("the capture was forced to measure red and still exited 0")
    if not refuse and rc != 0:
        raise Bail(f"the replayed capture itself went red (rc={rc}); see {gen.LOG}")
    return watch


def refusal_leaves_nothing(generator: pathlib.Path) -> list[str]:
    """PHASE THREE. A capture that measures RED must strand no half-published note either.

    `build()` stages the prose as its last act, after `measure()`, so a refusal should never reach
    the staging line at all - but "should" is the word this project treats as unmeasured. The
    capture is forced red and the tree is then read for leftovers, because a repair that closes the
    kill window while leaving a refusal to litter the same directory has moved the defect rather
    than removed it.
    """
    reset_tree()
    tmp = REPO / "web" / "notes" / ".manifest.json.tmp"
    tmp.unlink(missing_ok=True)
    watch = run_capture(None, generator, refuse=True)
    snap = watch.snapshot()
    rows = [
        "PHASE THREE - A CAPTURE THAT MEASURES RED LEAVES NOTHING BEHIND",
        "  both topics forced to an unrepairable miss, so build() raises Refusal before it stages",
        f"      sources on disk : {', '.join(sorted(snap['md'])) or '(no source)'}",
        f"      manifest pins   : {', '.join(sorted(pins(snap['manifest']) or [])) or '(nothing)'}",
        f"      stranded files  : {', '.join(snap['hidden']) or '(none)'}",
        "",
    ]
    if snap["md"] or snap["hidden"] or pins(snap["manifest"]):
        rows.append("  RED: a refused capture left something in the tree.")
    else:
        rows.append("  GREEN: a refused capture publishes nothing and stages nothing.")
    rows.append("")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="", help="header line for the captured report")
    ap.add_argument("--out", help="write the report here as well as to stdout")
    ap.add_argument("--append", action="store_true",
                    help="append to --out instead of replacing it, to keep two runs in one artefact")
    ap.add_argument("--generator", default=str(ORCHESTRA / "notes_gen.py"),
                    help="the notes_gen.py under test; defaults to ~/orchestra/notes_gen.py")
    ap.add_argument("--child-kill-after", type=int,
                    help="internal: run the capture and SIGKILL after the Nth recorded mutation")
    args = ap.parse_args()
    generator = pathlib.Path(args.generator).resolve()
    if not ORCHESTRA.is_dir():
        print(f"NOT MEASURED: {ORCHESTRA} is absent, so the generator this judges is not on this "
              f"host. This is a clone, and D-17 names that cost: the capture cannot be re-run from "
              f"one. Reporting no kill points here would be a green over a check that did not run.",
              file=sys.stderr)
        return 2

    if args.child_kill_after is not None:
        # The child works in the tree phase one built, rewound to the state the capture starts from.
        reset_tree()
        run_capture(args.child_kill_after, generator)
        return 3  # unreachable: the process is killed before main() returns

    build_scratch()
    watch = run_capture(None, generator)

    # Keep the finished artefacts, so a torn-write state can be cut from the real bytes.
    (SCRATCH / "final_md").mkdir(exist_ok=True)
    for f in (REPO / "web" / "notes" / "src").glob("*.md"):
        shutil.copy(f, SCRATCH / "final_md" / f.name)
    shutil.copy(REPO / "web" / "notes" / "manifest.json", SCRATCH / "final_manifest.json")

    out: list[str] = []
    if args.label:
        out += [args.label, ""]
    out += [
        f"COMMAND: python3 {pathlib.Path(__file__).name}",
        f"GENERATOR UNDER TEST: {generator}  sha256 {sha256_of(generator)}",
        f"REPLAYED FROM: web/notes/src/{SEED_NOTE}.md, captured prose, no model called",
        f"TOPICS IN THE RUN: {SEED_NOTE}, {SECOND_SLUG}",
        "",
        "EVERY MUTATION UNDER web/notes/, IN ONE NUMBERING",
        "  a kill can land after any of these, and inside any that is not atomic.",
        "  SEEN is a path a reader enumerates: web/notes/src/*.md, or the manifest.",
        "",
    ]
    for e in watch.events:
        rel = str(pathlib.Path(e["target"]).relative_to(REPO))
        out.append(f"  {e['n']:>2}. {'SEEN  ' if e['visible'] else 'hidden'} "
                   f"{'ATOMIC    ' if e['atomic'] else 'TORN-ABLE '} {e['primitive']:<16} {rel}")
    visible = [e for e in watch.events if e["visible"]]
    non_atomic = [e for e in visible if not e["atomic"]]
    out += [
        "",
        f"  {len(watch.events)} mutations, {len(visible)} of them on a path a reader enumerates,",
        f"  {len(non_atomic)} of those non-atomic and therefore able to leave a torn file",
        "",
        "WHAT EACH KILL POINT LEAVES, JUDGED BY THE TWO READERS OF THE PAIR",
        "",
    ]

    throws: list[str] = []
    reds: list[str] = []
    unjudged: list[str] = []

    def account(where: str, snap: dict, load: str, outcomes: dict) -> None:
        """Sort one kill point into the THREE states its gates can be in, never two.

        A pair is one-sided when the manifest pins a slug with no source, or a source has no line.
        When that holds and the gate that exists to refuse it did NOT RUN, the tree is not clean -
        it is unjudged, and it is recorded as its own state. Collapsing it into "green" is what this
        report did before Fable read it.
        """
        if load.startswith("THROW"):
            throws.append(f"{where}: {load[6:]}")
        pinned = pins(snap["manifest"])
        held = {n[: -len(".md")] for n in snap["md"]}
        if any(v in ("FAILED", "ERROR") for v in outcomes.values()):
            reds.append(f"{where}: {fresh_line(outcomes)}")
        elif pinned is None:
            unjudged.append(f"{where}: the manifest cannot be read at all and "
                            f"{PAIR_GATE} is {outcomes.get(PAIR_GATE, 'ABSENT')}")
        elif pinned != held:
            unjudged.append(f"{where}: pair is one-sided ({sorted(pinned ^ held)}) and "
                            f"{PAIR_GATE} is {outcomes.get(PAIR_GATE, 'ABSENT')}")

    prev = {"md": {}, "manifest": '{\n  "notes": {}\n}\n', "hidden": []}
    for st in watch.states:
        rel = str(pathlib.Path(st["target"]).relative_to(REPO))
        load, outcomes = judge(st["snap"])
        held = ", ".join(sorted(st["snap"]["md"])) or "(no source)"
        seen = pins(st["snap"]["manifest"])
        pinned = ("(no manifest)" if st["snap"]["manifest"] is None
                  else "(UNREADABLE - the file is there and is not JSON)" if seen is None
                  else ", ".join(sorted(seen)) or "(nothing)")
        out += [
            f"  kill after mutation {st['n']} - {st['primitive']} {rel}",
            f"      sources on disk : {held}",
            f"      manifest pins   : {pinned}",
            f"      stranded files  : {', '.join(st['snap']['hidden']) or '(none)'}",
            f"      loadNotes()     : {load}",
            f"      freshness gate  : {fresh_line(outcomes)}",
            "",
        ]
        account(f"after mutation {st['n']} ({rel})", st["snap"], load, outcomes)
        if not st["atomic"]:
            cut = torn(prev, pathlib.Path(st["target"]))
            if cut is not None:
                tload, toutcomes = judge(cut)
                out += [
                    f"  kill INSIDE mutation {st['n']} - {rel} half written",
                    f"      loadNotes()     : {tload}",
                    f"      freshness gate  : {fresh_line(toutcomes)}",
                    "",
                ]
                account(f"inside mutation {st['n']} ({rel}, torn)", cut, tload, toutcomes)
        prev = st["snap"]

    worst = watch.states[0]["n"] if watch.states else 1
    if throws:
        worst = int(re.search(r"mutation (\d+)", throws[0]).group(1))
    problem = hard_kill_child(worst, generator)
    if problem:
        out += ["PHASE TWO - A REAL SIGKILL", f"  NOT MEASURED: {problem}", ""]
    else:
        killed = Watch(REPO / "web" / "notes" / "src", REPO / "web" / "notes" / "manifest.json")
        snap = killed.snapshot()
        load, outcomes = judge(snap)
        out += [
            "PHASE TWO - A REAL SIGKILL, NOT A REPLAY OF ONE",
            f"  the capture was re-run in a child killed by SIGKILL after mutation {worst}",
            f"      sources on disk : {', '.join(sorted(snap['md'])) or '(no source)'}",
            f"      stranded files  : {', '.join(snap['hidden']) or '(none)'}",
            f"      loadNotes()     : {load}",
            f"      freshness gate  : {fresh_line(outcomes)}",
            "",
        ]
        if load.startswith("THROW") and not throws:
            throws.append(f"real SIGKILL after mutation {worst}: {load[6:]}")

    phase3 = refusal_leaves_nothing(generator)
    out += phase3
    if any(r.strip().startswith("RED:") for r in phase3):
        throws.append("a refused capture left files in the tree (phase three)")

    out += ["VERDICT", ""]
    if throws:
        out.append(f"  RED. {len(throws)} kill point(s) leave a tree on which loadNotes() throws,")
        out.append("  which is a build that fails on the moment the process died:")
        out += [f"    - {t}" for t in throws]
    else:
        out.append("  GREEN on the criterion T-C7 states: no kill point, and no torn write, leaves")
        out.append("  a tree on which loadNotes() throws.")
    if reds:
        out += ["", f"  RESIDUAL, REFUSED: {len(reds)} kill point(s) leave a tree the freshness gate",
                "  refuses even though the build loads it:"]
        out += [f"    - {r}" for r in reds]
    else:
        out += ["", "  No kill point leaves the freshness gate red."]
    if unjudged:
        out += ["", f"  RESIDUAL, NOT MEASURED: {len(unjudged)} kill point(s) leave a MISMATCHED pair",
                "  that no gate looked at. This is not a pass - it is check_did_not_run, and it is",
                "  counted apart from both green and red for that reason:"]
        out += [f"    - {u}" for u in unjudged]
    else:
        out += ["", "  Every mismatched pair a kill can leave was actually judged by the pair gate."]

    text = "\n".join(out) + "\n"
    print(text)
    if args.out:
        out_path = pathlib.Path(args.out)
        if args.append:
            with out_path.open("a", encoding="utf-8") as fh:
                fh.write("\n\n" + "=" * 98 + "\n\n" + text)
        else:
            out_path.write_text(text, encoding="utf-8")
    return 1 if throws else 0


if __name__ == "__main__":
    raise SystemExit(main())
