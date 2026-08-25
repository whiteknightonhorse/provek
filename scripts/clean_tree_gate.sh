#!/usr/bin/env bash
# T-S11 - the door's own dirty-tree check must not read a warned `git status` as a clean tree.
#
# THE BUG THIS CLOSES. `scripts/push.sh` used to read `DIRTY=$(git status --porcelain)` straight
# into a variable and treat an empty result as clean. That is also what git prints when it could
# not enter a directory: it writes `warning: could not open directory 'sub/': Permission denied` to
# STDERR, EXITS 0, and leaves that subtree out of stdout - so `$DIRTY` came back empty over content
# nobody read, and the door would have pushed on the strength of a check that did not run
# (invariant 1: `check_did_not_run` is not `nothing_qualified`). D-33 closed the identical hole in
# `scripts/publishable_tree.py._porcelain`; this is the same repair for the door's own reading,
# tracked separately as T-S11 because D-33 named the other two readers rather than fixing them in
# passing - a finding closed in one place is not closed everywhere it recurs (CLAUDE.md's rollback
# section, `~/orchestra/orch.sh`'s `untracked_inventory`).
#
# THREE STATES, NOT TWO. CLEAN, DIRTY (named tracked/untracked paths) and UNREADABLE (git said it
# did not read the whole tree). The exit code carries which one. git's stderr is printed, never
# parsed: matching on today's wording would make this gate's coverage a list of warnings someone
# thought of, and the warning that hides an unread tree is by definition the one nobody thought of.
#
# STANDALONE RATHER THAN INLINE IN push.sh so it can be fixture-tested (`clean_tree_gate.sh <root>`)
# without running the rest of the door - secrets/ratchets/lint/build/tests/push are all upstream of
# this check and none of them belong in a test of THIS reading. See
# tests/test_clean_tree_gate_reads_git_stderr.py for the red run on a `chmod 000` fixture.
#
# Bound to ABI-32-1 (the door is the only way out) and ABI-16-5 (a refusal is a named state).
set -uo pipefail

ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"

CLEAN=0
DIRTY=1
UNREADABLE=2

ERRFILE=$(mktemp)
trap 'rm -f "$ERRFILE"' EXIT

STATUS_OUT=$(git -C "$ROOT" status --porcelain 2>"$ERRFILE")
STATUS_ERR=$(cat "$ERRFILE")

if [ -n "$STATUS_ERR" ]; then
  echo "UNREADABLE: git status wrote to stderr, so its report is not a reading of the whole tree - what follows is git's own sentence, not this gate's:" >&2
  echo "$STATUS_ERR" >&2
  exit "$UNREADABLE"
fi

if [ -n "$STATUS_OUT" ]; then
  echo "REFUSED: the working tree is not clean, so the gates above did not judge what would be pushed." >&2
  echo "$STATUS_OUT" >&2
  exit "$DIRTY"
fi

echo "CLEAN"
exit "$CLEAN"
