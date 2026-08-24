#!/usr/bin/env python3
"""T-S1, second half - the workflow's `pip install` lines name a hash-checked set, and keep naming one.

`scripts/verify_action_pins.py` holds the same property one layer up: an action named by a movable
TAG runs code no gate here has ever seen. Three `pip install` lines in `gates.yml` were that defect
in another spelling - `pip install --quiet pytest pytest-cov` names two packages, installs ten, and
resolves the other eight fresh from PyPI on every run, with the same token the SHA-pinning was
performed to bound. D-30 records the decision to pin them.

WHY THIS EXISTS RATHER THAN THE PINNING BEING A ONE-TIME EDIT. The same reason its sibling exists,
stated in that file's own commit: A ONE-TIME EDIT DRIFTS BACK. Nothing in this repository could see
a `--require-hashes` line reverted to a bare `pip install`, and the check that comes closest reads
it as innocent by construction: `tests/test_door_matches_ci.py` classifies any line beginning
`pip install` as runner preparation, so the reverted line would be waved through as setup by the
very gate built to catch steps that slipped past the table. Scorecard would eventually raise a new
`PinnedDependenciesID` alert, days later, in somebody else's tab; this is the half that answers on
the push.

WHAT IS CHECKED AND WHAT IS NOT - the same split as the action pins, and for the same reason.

  * SHAPE, taken from this tree with no network: the install names `--require-hashes`, forbids
    source distributions, and points at a requirements file inside this repository; that file
    exists; every requirement in it carries a hash; and a package named by more than one file is
    pinned to one version in all of them.
  * TRUTH - that a `--hash=sha256:...` is the digest PyPI actually serves for that artefact - is
    NOT checked here and cannot be taken from this tree. It does not need to be: unlike a SHA
    beside a tag comment, this digest is not decoration a reviewer might believe. `pip` itself
    recomputes it at install time and REFUSES the artefact on a mismatch, which is the whole point
    of `--require-hashes`. So the enforcement of truth is the installer's, on every run, and what
    is left over for a gate is exactly the shape that installer never gets to see: whether the flag
    is still on the line at all.

THE THIRD STATE IS THE POINT, as everywhere else here. A requirements file that cannot be READ is
not a file with no unhashed lines. `_read` returns None for unreadable and the callers report that
as its own problem rather than folding it into the clean count - a checker that reads an I/O error
as "no violations found" is invariant 1 committed inside the instrument.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

# `pip install`, however it is spelled. A predicate that knew only the literal `pip install` would
# be satisfied by `python -m pip install`, which is the same act with a longer name.
PIP_INSTALL = re.compile(r"\b(?:pip3?|python3?(?:\.\d+)?\s+-m\s+pip)\s+install\b")

# `-r FILE` / `--requirement FILE` / `--requirement=FILE`.
REQ_FLAG = re.compile(r"(?:^|\s)(?:-r|--requirement)(?:[=\s]+)(\S+)")

# A requirement line in a compiled file: `name==version`, optionally trailing a `\` continuation.
PIN_LINE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==(\S+)")

# A YAML block scalar header: `|` or `>`, then an indentation indicator and a chomping indicator in
# either order, optionally behind an anchor or a tag. Reading only the bare `|` and `>` spellings
# left `run: |2` and `run: &a |` unrecognised - and unrecognised meant the body was skipped in
# SILENCE, so a `pip install` inside it was invisible to this gate while three inline lines kept the
# "measured NOTHING" guard quiet. A control that valid YAML blinds without a signal is a defect, not
# a limit. Found by Fable.
#
# THE TRAILING COMMENT IS PART OF THE HEADER, and leaving it out reopened the exact hole this regex
# was widened to close. `run: | # collect coverage` is ordinary YAML; it failed to match, so the
# body was skipped in silence again and `installs seen=0` was reported as clean. Found by Fable, in
# the round reviewing the repair that claimed this class was closed.
BLOCK_HEADER = re.compile(r"^(?:[&!]\S+\s+)*[|>](?:[0-9][+-]?|[+-][0-9]?)?(?:\s+#.*)?$")

REQUIRED_FLAGS = (
    # Without this, everything else here is decoration: pip only enforces the digests when asked.
    "--require-hashes",
    # `--generate-hashes` records sdist digests too, and hash-checking mode accepts an sdist. Building
    # one runs `setup.py`/PEP 517 in an isolated env whose build dependencies are fetched WITHOUT
    # hashes and are in no committed set - a hole that opens with no change to this tree, on the day
    # a project stops shipping a wheel for the runner's platform. Today every pin resolves to a
    # wheel, so this flag changes no outcome; it is here so that the day it would, the run REFUSES
    # rather than quietly widening. Found by Fable.
    "--only-binary=:all:",
)


def _lex(line: str):
    """`(index, char, is_syntax)` for every character, with quotes and backslashes resolved.

    `is_syntax` is True when bash would read the character as SYNTAX rather than as data - not
    inside quotes, and not escaped by a backslash.

    ONE LEXER, BECAUSE TWO COPIES DIVERGED AND BOTH WERE WRONG THE SAME WAY. `strip_comment` and
    `segments` each carried their own quote-tracking loop, and neither knew about `\\`. Inside
    double quotes bash reads `\\"` as a literal quote and stays INSIDE the string; the loops read it
    as a close followed by an open, so from that point their idea of quoted-ness was inverted
    against bash's - in both directions at once:

      * FALSE GREEN. `echo "\\"" ; pip install evilpkg  # --require-hashes -r requirements/...`
        looked like one quoted segment, so the `;` never split it and the `#` never cut it. Every
        flag was "found", in a comment, on a command bash never receives them on - one unpinned
        package installed under the workflow token, reported clean.
      * FALSE RED. `grep -r "\\"" logs && pip install --require-hashes ... -r requirements/...` is
        honest, and the same inversion swallowed the `&&`, so grep's `-r` was read as a second
        requirements reference pointing outside `requirements/`. A gate that reddens a correct line
        teaches people to route around it (L-5), which costs more than the miss it prevents.

    A rule written in two places survives its own repeal (L-2), and here it was one rule with two
    identical holes. Both findings are Fable's, in the round that reviewed the repair of the round
    before - which is the argument for this function existing rather than for a third loop.

    Each item is `(index, char, is_syntax, substitutable)`. `substitutable` is the weaker condition
    that a COMMAND SUBSTITUTION would still open here: bash expands `$(...)` and backticks inside
    double quotes as well as outside, and only single quotes suppress them. The two flags differ for
    exactly that case, and collapsing them would reopen the hole they were separated to close.
    """
    quote: str | None = None
    escaped = False
    for i, ch in enumerate(line):
        if escaped:
            escaped = False
            yield i, ch, False, False
        elif ch == "\\" and quote != "'":
            # Single quotes are literal in bash: a backslash inside them escapes nothing.
            escaped = True
            yield i, ch, False, False
        elif quote:
            if ch == quote:
                quote = None
            yield i, ch, False, quote != "'"
        elif ch in "'\"":
            quote = ch
            yield i, ch, False, ch != "'"
        else:
            yield i, ch, True, True


def unbalanced_quote(line: str) -> bool:
    """True if a quote is left open at the end of the line.

    Such a line is a broken command bash would refuse, and it is also the one input that makes this
    reader's output meaningless - everything after the stray quote is data, so no separator and no
    comment marker can be seen. Reported rather than parsed, because the alternative is a gate whose
    silence depends on a syntax error.
    """
    quote: str | None = None
    escaped = False
    for ch in line:
        if escaped:
            escaped = False
        elif ch == "\\" and quote != "'":
            escaped = True
        elif quote:
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
    return quote is not None


def strip_comment(line: str) -> str:
    """The command with any trailing shell comment removed.

    THE HOLE THIS CLOSES, AND IT WAS THE WHOLE GUARANTEE. Every check below looks for its flags as
    SUBSTRINGS, and bash discards a `#` comment that this reader was keeping. So

        pip install evilpkg  # --require-hashes --only-binary=:all: -r requirements/ci-tests.txt

    satisfied all three flags, resolved an `-r` pointing inside the tree, and reported no problem -
    while the runner installed one unpinned package with no requirements file at all, holding the
    token. The comment vouched for a command it had been removed from. That is the shape
    `test_door_matches_ci.executable_lines` was already burned by twice, arriving here by the same
    route: a substring test run against text that is not the command. Found by Fable.

    Quotes are tracked because a `#` inside them is data, not a comment, and cutting there would
    truncate a real command. Quoted text is otherwise KEPT, unlike the door's reader: `pip install
    "--require-hashes"` really does pass the flag to pip, so removing it would invent a false red.
    """
    out = []
    for i, ch, is_syntax, _ in _lex(line):
        if is_syntax and ch == "#" and (i == 0 or line[i - 1].isspace()):
            break
        out.append(ch)
    return "".join(out).strip()


def segments(line: str) -> list[str]:
    """The line split into the separate commands a shell would run.

    `pip install evilpkg && echo "--require-hashes -r requirements/ci-tests.txt"` is one line
    holding two commands, and only the second carries the flags. Judging the whole line lets any
    later command on it vouch for the install - the `echo` that announces a step it has disabled,
    which is the second lesson `executable_lines` records about itself. Each command is judged
    alone, so the flags must sit on the install itself.

    COMMAND SUBSTITUTION IS A COMMAND, and missing that was the eighth way past this gate.
    `echo $(pip install evilpkg) --require-hashes --only-binary=:all: -r requirements/ci-tests.txt`
    holds no `&&`, no `;` and no `|`, so it arrived here as ONE segment carrying every required
    flag - reported clean, while bash runs `pip install evilpkg` inside the substitution and the
    flags decorate the harmless `echo` around it. Precisely the vouching-by-neighbouring-text class
    this function was written to close, in the one spelling it did not split; `$(` is in
    `test_door_matches_ci.CHAINS` for the same reason, found there first. The boundaries `$(`, a
    backtick, `<(`, `>(` and the closing `)` therefore end a command here too. Found by Fable.
    """
    out: list[str] = []
    current: list[str] = []
    skip = -1
    for i, ch, is_syntax, substitutable in _lex(line):
        if i == skip:
            continue
        nxt = line[i + 1] if i + 1 < len(line) else ""
        if is_syntax and ch in "&|;":
            # `&&`, `||`, `|`, `;` all end a command; a lone `&` backgrounds it, which also ends it.
            out.append("".join(current))
            current = []
            if nxt == ch:
                skip = i + 1
        elif substitutable and (ch == "`" or (ch in "$<>" and nxt == "(") or ch == ")"):
            out.append("".join(current))
            current = []
            if nxt == "(":
                skip = i + 1
        else:
            current.append(ch)
    out.append("".join(current))
    return [s.strip() for s in out if s.strip()]


def _read(path: pathlib.Path) -> str | None:
    """The file's text, or None if it could not be read. None is a state, not an empty file."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def run_command_lines(workflow: str) -> list[str]:
    """The TEXT of every shell line written in a `run:` step of this workflow.

    Both spellings, because a checker that knew only one would be blind to the other: the inline
    `- run: pip install ...` and the block scalar `run: |` with its indented body. The block form is
    how a step grows a second line, so reading only the inline form would mean a pip install could
    be hidden from this gate by reformatting the step that holds it.

    WHAT IT EXECUTES IS A WIDER CLAIM THAN WHAT IT SAYS, and this returns the second. A step that
    runs `bash scripts/secret_scan.sh` - the `secrets` job does exactly that - could install
    packages from inside that script, and nothing here would see it. No such indirection exists in
    this tree today; the limit is written down rather than glossed, because a docstring claiming
    the stronger property is the defect this repository exists to catch. Found by Fable, against an
    earlier line here that claimed it.
    """
    lines: list[str] = []
    block_indent: int | None = None
    for raw in workflow.splitlines():
        stripped = raw.strip()
        indent = len(raw) - len(raw.lstrip())
        if block_indent is not None:
            # The block ends at the first non-blank line indented no further than the `run:` itself.
            if stripped and indent <= block_indent:
                block_indent = None
            else:
                if stripped:
                    lines.append(stripped)
                continue
        m = re.match(r"-?\s*run:\s*(.*)$", stripped)
        if not m:
            continue
        body = m.group(1).strip()
        if BLOCK_HEADER.match(body):
            block_indent = indent
        elif body:
            lines.append(body)

    # A TRAILING BACKSLASH CONTINUES THE COMMAND, and reading the physical lines separately turned
    # an honest install into a red one. Split for readability -
    #
    #     pip install --require-hashes --only-binary=:all: \
    #         -r requirements/ci-tests.txt
    #
    # - the first physical line carries both flags and no `-r`, so it was reported as installing
    # packages named on the command line. That is a false RED on correct work, and the three lines
    # D-30 pinned are exactly the candidates for being wrapped this way one day. A gate that
    # reddens the correct form teaches people to route around it (L-5). Found by Fable.
    joined: list[str] = []
    for line in lines:
        if joined and joined[-1].endswith("\\"):
            joined[-1] = joined[-1][:-1].rstrip() + " " + line
        else:
            joined.append(line)
    return [c for line in joined for c in segments(strip_comment(line))]


def pip_install_lines(workflow: str) -> list[str]:
    """The commands in `run:` steps that install Python packages."""
    return [ln for ln in run_command_lines(workflow) if PIP_INSTALL.search(ln)]


def line_problems(line: str) -> list[str]:
    """What is wrong with one `pip install` line, judged on shape alone."""
    problems = []
    if unbalanced_quote(line):
        # Refuse rather than guess. Past an unclosed quote every separator and every `#` is data, so
        # a verdict taken here would be a verdict about a string this reader cannot segment.
        return [f"`{line}` leaves a quote unclosed, so it cannot be read as a command at all"]
    for flag in REQUIRED_FLAGS:
        if flag not in line:
            problems.append(f"`{line}` does not pass {flag}")
    refs = REQ_FLAG.findall(line)
    if not refs:
        problems.append(
            f"`{line}` installs packages named on the command line rather than a committed "
            "requirements file, so what it resolves is not in this repository")
        return problems
    for ref in refs:
        # A URL or an absolute path is a requirements file this repository does not hold and no
        # reviewer sees. It satisfies every flag above while sourcing its contents from anywhere -
        # the hole `-r` opens that a flag check alone would wave through. Found by Fable.
        if "://" in ref or ref.startswith(("/", "-")) or ".." in ref:
            problems.append(f"`{line}` reads requirements from {ref}, which is not a path in this tree")
        elif not ref.startswith("requirements/"):
            problems.append(f"`{line}` reads requirements from {ref}, outside `requirements/`")
    return problems


def pins(requirements: str) -> dict[str, str]:
    """`{package: version}` for every pinned requirement in a compiled file."""
    out = {}
    for raw in requirements.splitlines():
        m = PIN_LINE.match(raw.strip())
        if m:
            out[m.group(1).lower()] = m.group(2).rstrip(" \\")
    return out


def unhashed(requirements: str) -> list[str]:
    """Requirements carrying no `--hash=`.

    The hashes sit on continuation lines after the `name==version`, so a requirement's block runs
    until the next requirement or a blank line. A pinned version with no digest under it is exactly
    what `--require-hashes` would reject at install time - caught here so it is a red review rather
    than a red build ten minutes later.
    """
    out, current, seen_hash = [], None, False
    for raw in requirements.splitlines() + [""]:
        line = raw.strip()
        if line.startswith("#"):
            continue
        m = PIN_LINE.match(line)
        if m:
            if current and not seen_hash:
                out.append(current)
            current, seen_hash = m.group(1), "--hash=" in line
        elif current is not None:
            if "--hash=" in line:
                seen_hash = True
            if not line:
                if not seen_hash:
                    out.append(current)
                current, seen_hash = None, False
    if current and not seen_hash:
        out.append(current)
    return out


def check(workflows: pathlib.Path = WORKFLOWS, root: pathlib.Path = ROOT) -> list[str]:
    """Every violation in the tree. An EMPTY list means clean; a missing instrument is a violation."""
    problems: list[str] = []
    if not workflows.is_dir():
        return [f"{workflows} is not a directory - the workflows are ABSENT, which is not the same "
                "fact as their pip lines being clean"]

    versions: dict[str, dict[str, str]] = {}
    installs = 0
    # BOTH EXTENSIONS. GitHub reads `*.yml` and `*.yaml` alike, so a checker that knew one would be
    # silent about a workflow saved under the other - and silent is the dangerous half: the three
    # inline installs here keep the "measured NOTHING" guard below quiet, so the gap would not even
    # announce itself as an empty measurement. Found by Fable.
    for wf in sorted([*workflows.glob("*.yml"), *workflows.glob("*.yaml")]):
        text = _read(wf)
        if text is None:
            problems.append(f"{wf.name} could not be READ, so its pip lines are unmeasured, not clean")
            continue
        for line in pip_install_lines(text):
            installs += 1
            problems += [f"{wf.name}: {p}" for p in line_problems(line)]
            for ref in REQ_FLAG.findall(line):
                if not ref.startswith("requirements/") or "://" in ref or ".." in ref:
                    continue        # already reported above; do not also read it
                req = root / ref
                body = _read(req)
                if body is None:
                    problems.append(
                        f"{wf.name}: `{line}` names {ref}, which does not exist or cannot be read")
                    continue
                versions[ref] = pins(body)
                if not versions[ref]:
                    problems.append(f"{ref} pins NOTHING - an empty set is not a hash-checked set")
                problems += [f"{ref}: {pkg} is pinned with NO hash" for pkg in unhashed(body)]

    # THE COST OF THREE FILES, MADE MECHANICAL. Separate sets per job is the right call - `shipped`
    # has no use for a coverage plugin - but it buys a way for two jobs to measure the same tree
    # with different instruments: a bump applied to one file and not its siblings leaves both green
    # and only one of them current. Named by Fable as the price the decision recorded without.
    for pkg in sorted({p for v in versions.values() for p in v}):
        holders = {f: v[pkg] for f, v in versions.items() if pkg in v}
        if len(set(holders.values())) > 1:
            spread = ", ".join(f"{f}={ver}" for f, ver in sorted(holders.items()))
            problems.append(f"{pkg} is pinned to DIFFERENT versions across the sets: {spread}")

    if installs == 0:
        # Nothing to check is not the same as everything checked out. If the workflows stop
        # installing Python packages this gate has become vacuous, and that should be seen.
        problems.append(
            "no `pip install` line was found in any workflow - this gate measured NOTHING, which is "
            "unknown rather than clean")
    return problems


def main() -> int:
    p = check()
    if p:
        sys.stderr.write("\nX T-S1-PIP-PINS:\n" + "".join(f"  - {x}\n" for x in p))
        return 1
    print("T-S1-PIP-PINS: clean (every pip install names a hash-checked set inside this tree)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
