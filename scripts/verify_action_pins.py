#!/usr/bin/env python3
"""T-S1 - every third-party action is pinned to a commit, and the tag beside it is the true one.

WHY A PIN AT ALL. `uses: actions/checkout@v4` names a TAG, and a tag is a movable pointer: the
action's owner may repoint it at any commit at any time, without our tree changing by a byte. This
repository is public and its CI holds a token, so "whatever that tag resolves to at run time"
is somebody else's code executing with our credentials. Code scanning called it
`PinnedDependenciesID` nineteen times; the name understates it, because this is not a freshness
problem but an authorisation one.

WHY THE PIN NEEDS ITS OWN CHECKER, WHICH IS THE LESS OBVIOUS HALF. A pin to the WRONG commit is
worse than no pin: `actions/checkout@<forty hex characters>  # v4.4.0` looks exactly like diligence
whether or not that SHA has ever been in `actions/checkout`, and the comment - the only part a
human reads - is free text nothing validates. Pinning therefore converts a visible weakness into an
invisible one unless something re-derives the pin from the action's own repository.

THE THREE STATES, WHICH IS WHY `git ls-remote` IS CALLED RATHER THAN TRUSTED (invariant 1). Asking
another host a question can fail, and a failed lookup must never read as a match:

    MATCH        - the tag exists in that repository and resolves to the SHA we pinned.
    MISMATCH     - it resolves to a DIFFERENT commit. The pin is a lie with a true-looking label.
    TAG_ABSENT   - the tag does not exist there at all.
    NOT_MEASURED - the lookup did not complete. Unknown, never clean, and never a match.

The verdict below is taken by code from those states, never from prose. `verify()` is pure and
takes the resolver as an argument, so the whole table is exercised by `tests/test_actions_pinned.py`
without a network - which is the only way the MISMATCH and NOT_MEASURED arms are ever SEEN to fire,
rather than being present and unwatched (L-16).

WHO RUNS THIS, STATED SO IT IS NOT MISTAKEN FOR AN ARMED GATE. `main()` is NOT wired into
`gates.yml` or `scripts/push.sh`. The SHAPE half is armed on every push, inside
`tests/test_actions_pinned.py`; this half needs a route out to GitHub, and a gate that reddens the
tree on a network blip is one that gets disabled by the first person it stops. Run it by hand when
a `uses:` line changes - which is the only moment its answer can have changed:

    python3 scripts/verify_action_pins.py

That is a deliberate ceiling, not an oversight, and it is the weaker half of this task: the tree
cannot tell a true pin from a false one on its own. If a pin is ever to be trusted without a human
remembering to run this, the honest fix is a CI step whose NOT_MEASURED is allowed to be red -
which is a decision about the cost of a flaky gate, not something to slip in here.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

SHA_RE = re.compile(r"^[0-9a-f]{40}$")

# `uses:` with an optional trailing `# tag ...` comment. The comment is captured because it is the
# claim being checked, not decoration. `.*?` rather than `\S+` for the tag: the first draft required
# the comment to be a SINGLE word, so `# v4.4.0 (pinned upstream)` failed to match - and a line that
# failed to match was silently skipped, which made the whole `uses:` invisible to this checker. See
# LOOKS_LIKE_USES below for the half that turns that class of miss into a red.
USES_RE = re.compile(
    r"^\s*(?:-\s*)?uses\s*:\s*(?P<ref>\S+?)\s*(?:#\s*(?P<tag>\S+)(?P<rest>.*?)\s*)?$")

# ANY line that mentions `uses` as a key, however it is written. The strict pattern above decides
# what a line MEANS; this one decides whether the line was our business at all, and the gap between
# them is reported rather than skipped.
#
# THE FALSE GREEN THIS PAIR EXISTS FOR, found by Fable in the first draft. `collect()` reported an
# unreadable DIRECTORY and an unreadable FILE, and then walked silently past an unreadable LINE - so
# `uses: github/codeql-action/init@main  # pinned upstream, see notes` matched nothing, was dropped
# on the floor, and every assertion downstream went green over a workflow running a moving branch.
# The door's own parser already names this shape and fixes it with `__unparsed__`
# (tests/test_door_matches_ci.py); this is the same repair, one file over. A checker that quietly
# walks past what it does not understand reports success on what it never examined.
LOOKS_LIKE_USES = re.compile(r"(?:^|[-{,\s])uses\s*:")

# Local actions (`./.github/actions/x`) and reusable workflows inside this repository are not
# pinned, deliberately: they ARE this tree, and a SHA would pin them to a past version of
# themselves. Anything reached over the network is in scope.
LOCAL_PREFIXES = ("./", "../")


class Pin:
    """One `uses:` line: what it names, what it is pinned to, and what it claims that pin is."""

    def __init__(self, workflow: str, line_no: int, action: str, ref: str, tag: str | None) -> None:
        self.workflow = workflow
        self.line_no = line_no
        self.action = action
        self.ref = ref
        self.tag = tag

    @property
    def repo(self) -> str:
        """`github/codeql-action/init` is served by the repository `github/codeql-action`."""
        parts = self.action.split("/")
        return "/".join(parts[:2])

    @property
    def is_pinned(self) -> bool:
        return bool(SHA_RE.match(self.ref))

    def __repr__(self) -> str:  # pragma: no cover - diagnostics only
        return f"{self.workflow}:{self.line_no} {self.action}@{self.ref[:12]} # {self.tag}"


def collect(workflows: pathlib.Path = WORKFLOWS) -> tuple[list[Pin], list[str]]:
    """Every `uses:` in every workflow, plus problems found while reading them.

    A directory that is absent or holds no workflow is reported as a PROBLEM rather than as an
    empty clean list. "No unpinned actions" and "we never found the workflows" are different facts,
    and a checker that returns `[]` for the second reports the tree it could not read as compliant.
    """
    problems: list[str] = []
    if not workflows.is_dir():
        return [], [f"{workflows} is not a directory - the workflows are UNREADABLE, not clean"]
    files = sorted(p for p in workflows.iterdir() if p.suffix in (".yml", ".yaml"))
    if not files:
        return [], [f"no workflow files in {workflows} - unreadable or empty, and both are reported"]

    pins: list[Pin] = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except OSError as exc:
            problems.append(f"{f.name}: could not be read ({exc}) - unreadable, not clean")
            continue
        for i, raw in enumerate(text.splitlines(), start=1):
            if raw.lstrip().startswith("#"):
                continue
            m = USES_RE.match(raw)
            if m is None:
                if LOOKS_LIKE_USES.search(raw.split("#", 1)[0]):
                    problems.append(
                        f"{f.name}:{i}: this line names `uses:` and this checker COULD NOT PARSE "
                        f"it - {raw.strip()!r}. Unreadable is reported, never skipped: a `uses:` "
                        "invisible to this gate is an action nothing here judges.")
                continue
            ref = m.group("ref")
            if ref.startswith(LOCAL_PREFIXES):
                continue
            action, _, at = ref.partition("@")
            if not at:
                problems.append(
                    f"{f.name}:{i}: `uses: {ref}` names no ref at all, so the runner takes the "
                    "default branch - the most movable pointer there is")
                continue
            pins.append(Pin(f.name, i, action, at, m.group("tag")))
    return pins, problems


def token_problems(text: str, name: str = "<workflow>") -> list[str]:
    """Jobs whose `GITHUB_TOKEN` is left at GitHub's default, which is wider than any job here needs.

    Workflow-level `permissions:` covers every job, so it is looked for first; otherwise each job
    must bound its own. The parse is line-based on purpose - the first draft used
    `text.partition("\\njobs:\\n")`, and Fable broke it with `jobs:  # five of them`: the partition
    found nothing, the job list came back empty, and the function returned "no unbounded jobs" for a
    workflow it had entirely failed to read. Annotating a key is ordinary YAML, and "I found no
    jobs" rendered as "every job is bounded" is invariant 1 turned on this checker.

    `write-all` is rejected rather than counted as a declaration. The property is that the token is
    BOUNDED, and a blanket write grant is the default this exists to replace - checking only that
    the key is PRESENT would let the fix be undone by editing the value, which is L-16's shape.
    Narrower `write` scopes are allowed at JOB level and are not second-guessed here: `codeql.yml`
    genuinely needs `security-events: write` to file its findings, and this checker has no way to
    know which job deserves what.
    """
    lines = text.split("\n")
    top_perm = next((ln for ln in lines if re.match(r"^permissions\s*:", ln)), None)
    if top_perm is not None and "write-all" in top_perm:
        return [f"{name}: workflow-level `permissions: write-all` is the broad default wearing a "
                "declaration; that is not a bound"]

    jobs_at = next((i for i, ln in enumerate(lines) if re.match(r"^jobs\s*:", ln)), None)
    if jobs_at is None:
        return [f"{name}: no top-level `jobs:` key found - the workflow is UNREADABLE to this "
                "checker, which is not the same fact as having no unbounded job"]
    if top_perm is not None:
        return []

    out: list[str] = []
    body = lines[jobs_at + 1:]
    for i, ln in enumerate(body):
        m = re.match(r"^  ([A-Za-z0-9_.-]+)\s*:", ln)
        if not m:
            continue
        job, block = m.group(1), []
        for nxt in body[i + 1:]:
            if nxt.strip() and not nxt.startswith("    "):
                break
            block.append(nxt)
        if not any(re.match(r"^    permissions\s*:", b) for b in block):
            out.append(f"{name}: job `{job}` runs on GitHub's DEFAULT token permissions - nothing "
                       "says what it is allowed to do, so it is allowed what the default allows")
    return out


def shape_problems(pins: list[Pin]) -> list[str]:
    """What can be judged from this tree alone: pinned to a SHA, and labelled with a tag."""
    out: list[str] = []
    for p in pins:
        if not p.is_pinned:
            out.append(
                f"{p.workflow}:{p.line_no}: `{p.action}@{p.ref}` is pinned to a MOVABLE ref. The "
                "owner of that action may repoint it at any commit, and our CI would run it with "
                "our token.")
        elif not p.tag:
            out.append(
                f"{p.workflow}:{p.line_no}: `{p.action}` is pinned to a SHA with no `# tag` "
                "comment. Nothing there tells a reader which version this is, so the pin can "
                "never be reviewed or deliberately moved.")
    return out


GITHUB = "https://github.com/"


def resolve_tags(repo: str, base: str = GITHUB) -> dict[str, str] | None:
    """Every tag in `repo` mapped to the COMMIT it points at, or None if the lookup failed.

    None is the third state and every caller treats it as one. Collapsing it into `{}` would report
    every pin as TAG_ABSENT, which accuses the action's owner of deleting a tag when the true fact
    is that we could not ask - it sends the next reader to investigate somebody else's repository
    over a broken route out of this one.

    Annotated tags are dereferenced through their `^{}` peel, because an action is pinned to a
    commit and the tag OBJECT's own sha is a different thing that would compare unequal and read as
    a MISMATCH - a false red on a correct pin, which teaches walking past this gate exactly as a
    false green would (L-5). `github/codeql-action`'s tags are annotated and `actions/checkout`'s
    are not, so both arms are live against the real pins in this tree.

    `base` is injectable so the failure arm can be driven from a test without a network, and
    `GIT_TERMINAL_PROMPT=0` is set because a git that stops to ask for a password is a gate that
    hangs rather than one that fails.
    """
    import os

    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "true"}
    try:
        out = subprocess.run(
            ["git", "ls-remote", f"{base}{repo}", "refs/tags/*"],
            capture_output=True, timeout=60, check=False, env=env)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None

    direct: dict[str, str] = {}
    peeled: dict[str, str] = {}
    for line in out.stdout.decode("utf-8", "replace").splitlines():
        if "\t" not in line:
            continue
        sha, ref = line.split("\t", 1)
        if not ref.startswith("refs/tags/"):
            continue
        name = ref[len("refs/tags/"):]
        if name.endswith("^{}"):
            peeled[name[:-3]] = sha
        else:
            direct[name] = sha
    return {**direct, **peeled}


def verify(pins: list[Pin], resolver) -> list[tuple[Pin, str, str]]:
    """(pin, state, detail) for every pin, where state is one of the four named in the docstring.

    Pure: the resolver is injected, so the MISMATCH and NOT_MEASURED arms can be driven from a test
    with no network. A gate whose failure path has never executed is a promise.
    """
    cache: dict[str, dict[str, str] | None] = {}
    results: list[tuple[Pin, str, str]] = []
    for p in pins:
        if not p.is_pinned or not p.tag:
            results.append((p, "NOT_MEASURED", "not pinned to a SHA with a tag; see shape_problems"))
            continue
        if p.repo not in cache:
            cache[p.repo] = resolver(p.repo)
        tags = cache[p.repo]
        if tags is None:
            results.append((p, "NOT_MEASURED", f"could not read the tags of {p.repo}"))
        elif p.tag not in tags:
            results.append((p, "TAG_ABSENT", f"{p.repo} has no tag {p.tag}"))
        elif tags[p.tag] != p.ref:
            results.append((p, "MISMATCH", f"{p.tag} is {tags[p.tag]}, pinned {p.ref}"))
        else:
            results.append((p, "MATCH", f"{p.tag} = {p.ref}"))
    return results


def main() -> int:
    pins, problems = collect()
    problems += shape_problems(pins)
    for f in sorted(WORKFLOWS.glob("*.yml")) if WORKFLOWS.is_dir() else []:
        problems += token_problems(f.read_text(encoding="utf-8"), f.name)

    if problems:
        sys.stderr.write("\nX T-S1 (shape):\n" + "".join(f"  - {x}\n" for x in problems))
        return 1

    results = verify(pins, resolve_tags)
    bad = [(p, s, d) for p, s, d in results if s != "MATCH"]
    for p, state, detail in results:
        print(f"  {state:<12} {p.workflow}:{p.line_no} {p.action}@{p.ref[:12]}  # {p.tag} - {detail}")
    if bad:
        # NOT_MEASURED is in here on purpose. A network that refused is not a repository that
        # agreed, and exiting 0 on it would make this gate green precisely when it is blind.
        sys.stderr.write(
            f"\nX T-S1: {len(bad)} of {len(results)} pins are not a confirmed MATCH.\n")
        return 1
    print(f"T-S1: clean ({len(results)} actions, every pin re-derived from the action's repository)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
