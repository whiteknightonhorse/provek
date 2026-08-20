#!/usr/bin/env bash
# The single door outward. A gate that does not STOP is not a gate.
#
# THIS SCRIPT WAS WRITTEN AFTER A REAL MISS: the first push succeeded while the ratchet was RED,
# because the checks sat in a chain without `set -e` - a failure printed to the log and execution
# carried on. A gate you can walk past is worse than no gate: it manufactures a false sense of
# safety.
#
# Order: secrets -> scope -> laws -> language -> tests -> and only then push.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "1/6 secrets";  ./scripts/secret_scan.sh
echo "2/6 scope";    python3 scripts/ratchet_scope.py
echo "3/6 laws";     python3 scripts/ratchet_decisions.py
echo "4/6 language"; python3 scripts/ratchet_language.py
# LINT IS HERE BECAUSE ITS ABSENCE WAS MEASURED, NOT BECAUSE IT IS TIDY.
#
# `gates.yml` opens "THE SAME GATES AS scripts/push.sh". It was not true: CI ran ruff and this
# script never had. So a commit could pass every gate at the door and land red on main, and one
# did - the commit that added the note tests carried five ruff violations, went out clean through
# here, and turned `lint and types` red on `main` where the next reader sees a failing badge over a
# repository whose subject is gates that hold.
#
# The divergence is the defect, not the five violations. Two gate lists that claim to be one list
# are a rule written in more than one place (L-2), and this one had already survived its own
# repeal: the header asserting the lists were identical stayed correct-sounding while they drifted.
echo "5/6 lint";     python3 -m ruff check src tests scripts
echo "6/6 tests";    python3 -m pytest tests -q | tail -1

# Gates-only mode. The orchestra must judge the tree after EVERY task, not just before a push,
# and a second copy of the gate list would drift from this one the first time the list changed.
# One definition, two callers.
if [ "${1:-}" = "--gates-only" ]; then echo "TREE GREEN (gates only, nothing pushed)"; exit 0; fi

# THE GATES ABOVE JUDGED THE WORKING TREE. WHAT GOES OUT IS THE COMMIT.
#
# Those are two different artefacts, and every check above reads files from disk - tracked or not.
# A tree carrying an untracked `tests/test_x.py` alongside a COMMITTED law that names it passes all
# five gates here and publishes a repository whose own ratchet is red in any clone: the law is
# dangling, because the file proving it never left this host. That state existed in this tree
# while T-E1 was being written - four LAW-NOTES-* entries staged against gate and test files that
# were still untracked.
#
# This is L-3 turned on the door itself. The project's rule is that a file in the repository is not
# what the consumer receives; here, a file on this host is not what the clone receives. Refusing a
# dirty tree is the cheap version - it makes the tree and the commit the same artefact, so the
# gates that ran above are the gates that apply to what is pushed.
DIRTY=$(git status --porcelain)
if [ -n "$DIRTY" ]; then
  echo "REFUSED: the working tree is not clean, so the gates above did not judge what would be pushed." >&2
  echo "$DIRTY" >&2
  exit 1
fi

# AND THE COMMIT THE GATES JUDGED MUST BE THE COMMIT THE PUSH SENDS.
# A clean tree equals HEAD; the command below pushes `main`. On another branch, or in a detached
# HEAD, those are two different commits and the check above would have proved nothing about the one
# going out. Cheap to state, and it is the difference between the claim this block makes and what
# it actually measures.
if [ "$(git rev-parse HEAD)" != "$(git rev-parse main)" ]; then
  echo "REFUSED: HEAD is not main, so the gates judged a commit other than the one being pushed." >&2
  exit 1
fi

TOK=$(sudo grep -ohE 'gh[pous]_[A-Za-z0-9_]+' /home/audiobook2/.claude/gh.env | head -1)
if [ -z "$TOK" ]; then echo "no token" >&2; exit 1; fi
trap 'git remote set-url origin "https://github.com/whiteknightonhorse/provek.git" 2>/dev/null; unset TOK' EXIT
git remote set-url origin "https://x-access-token:${TOK}@github.com/whiteknightonhorse/provek.git"
git push -q origin main
echo "PUSH DONE, token removed from the remote config"
