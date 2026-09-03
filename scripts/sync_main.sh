#!/usr/bin/env bash
# AUD-003 (Fable, 2026-09-03). Two systems write to `origin/main` under opposite ownership models:
# `.github/workflows/dependabot-auto-merge.yml` merges patch/minor bumps straight into
# `origin/main` with no human and no visit to this host, while `scripts/push.sh` pushes this
# server's `main` assuming it already IS the tip - it never fetches first. The first auto-merged
# dependabot PR makes both halves of that assumption false at once: the next `push.sh` gets a
# non-fast-forward rejection (a stopped, alerted night per `nightly_remeasure.sh`'s own `fail()`),
# and the bump that auto-merged never reaches the live site regardless, because the site is built
# from THIS tree, not from GitHub's copy of it.
#
# THE MODEL CHOSEN (one of the two the finding named): the server pulls before it measures, rather
# than dependabot's automation being switched off. This script is that pull, run once at the start
# of the nightly chain, before `cohort.py` takes a single reading - "before the measurement" is
# load-bearing, not a preference: pulling AFTER would let a night's passports be re-measured off a
# tree that is about to change under them.
#
# WHY A TOKEN IS NEEDED TO EVEN LOOK. Measured directly on this host: an anonymous
# `git ls-remote https://github.com/.../provek.git` gets a 200 on the `GET info/refs` half of the
# smart-HTTP exchange and a 401 on the following `POST git-upload-pack` - GitHub declines the
# actual object negotiation without credentials from this network, for a repository that is
# otherwise public. `push.sh` already carries the fix for the write side (a token spliced into the
# remote URL only for the duration of the push, then removed); this is the same splice for the
# read side, so a fetch is not a second, unexplained hole next to a solved one.
#
# NOT INVOKED FOR A NON-GITHUB REMOTE (tests use a local `file://` origin, which needs no auth and
# must not be made to depend on this host's token file to stay green).
#
# THREE OUTCOMES, NAMED SEPARATELY, never collapsed (the class LAW-NOT-MEASURED and
# `clean_tree_gate.sh` already hold elsewhere in this door): already level, a clean fast-forward,
# or a genuine divergence. The last one is a NAMED RED, not a guessed merge - a real divergence
# between this server's `main` and GitHub's means someone or something wrote to one side outside
# this script's own model, and resolving that by picking a side automatically would publish a
# choice nobody made.
#
# Bound to ABI-32-1 (the door outward governs what `main` becomes) and ABI-16-5 (a refusal is a
# named state, not a swallowed exit code). See tests/test_sync_main_ff.py for the mutation control:
# RED reproduces the exact non-fast-forward push AUD-003 measured, GREEN shows this script closing
# it before that push ever runs.
set -euo pipefail
cd "$(dirname "$0")/.."

REMOTE="${SYNC_MAIN_REMOTE:-origin}"
BRANCH="${SYNC_MAIN_BRANCH:-main}"

url="$(git remote get-url "$REMOTE")"
if [[ "$url" == https://github.com/* ]]; then
  TOK=$(sudo grep -ohE 'gh[pous]_[A-Za-z0-9_]+' /home/audiobook2/.claude/gh.env | head -1)
  if [ -z "$TOK" ]; then echo "sync_main: no token, cannot even read $REMOTE from this host (AUD-003)" >&2; exit 1; fi
  trap 'git remote set-url "$REMOTE" "$url" 2>/dev/null; unset TOK' EXIT
  git remote set-url "$REMOTE" "https://x-access-token:${TOK}@${url#https://}"
fi

git fetch -q "$REMOTE" "$BRANCH"

local_head="$(git rev-parse HEAD)"
remote_head="$(git rev-parse "$REMOTE/$BRANCH")"

if [ "$local_head" = "$remote_head" ]; then
  echo "sync_main: HEAD already matches $REMOTE/$BRANCH ($local_head)"
  exit 0
fi

if git merge-base --is-ancestor HEAD "$REMOTE/$BRANCH"; then
  echo "sync_main: $REMOTE/$BRANCH is ahead of HEAD - fast-forwarding before tonight's measurement"
  git merge --ff-only "$REMOTE/$BRANCH"
  echo "sync_main: fast-forwarded to $(git rev-parse HEAD)"
  exit 0
fi

echo "sync_main: HEAD ($local_head) and $REMOTE/$BRANCH ($remote_head) have DIVERGED - not a fast-forward, refusing to guess which side wins" >&2
exit 1
