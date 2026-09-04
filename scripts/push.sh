#!/usr/bin/env bash
# The single door outward. A gate that does not STOP is not a gate.
#
# THIS SCRIPT WAS WRITTEN AFTER A REAL MISS: the first push succeeded while the ratchet was RED,
# because the checks sat in a chain without `set -e` - a failure printed to the log and execution
# carried on. A gate you can walk past is worse than no gate: it manufactures a false sense of
# safety.
#
# Order: secrets -> scope -> laws -> language -> lint -> site -> tests -> reproduce -> push.
# This line had already drifted once - it still read "... -> language -> tests" after ruff was
# added below, which is the same header-outlives-its-list defect that let the door and CI diverge
# in the first place, sitting three lines above the comment explaining that defect. The list that
# is actually compared against CI is `CI_GATES` in tests/test_door_matches_ci.py; this sentence is
# a reader's convenience and is not what enforces anything.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "1/8 secrets";  ./scripts/secret_scan.sh
echo "2/8 scope";    python3 scripts/ratchet_scope.py
echo "3/8 laws";     python3 scripts/ratchet_decisions.py
echo "4/8 language"; python3 scripts/ratchet_language.py
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
echo "5/8 lint";     python3 -m ruff check src tests scripts

# THE SAME DIVERGENCE, TWICE MORE, FOUND BY WRITING THE TWO LISTS OUT SIDE BY SIDE.
#
# Adding ruff above closed the instance that had turned `main` red four times and left the
# mechanism untouched, so `tests/test_door_matches_ci.py` now compares the two lists as a gate.
# It immediately named two more steps CI can fail on that never existed here:
#
#   THE SITE WAS NEVER BUILT. The `shipped` job builds it, because the assertions that sweep the
#   emitted pages are the only ones that judge what a reader receives (L-3). Here they read
#   whatever `web/dist` happened to be lying on this host - yesterday's output, or none at all, in
#   which case they SKIPPED and were counted as passing. That is L-16 at the door: present, not
#   armed. It costs 2.1s measured, and `web/dist/` is ignored, so the tree stays clean.
#
#   COVERAGE WAS NOT ENFORCED. CI requires 70%; this ran a bare `pytest`, so a commit could drop
#   coverage and go out clean through here. Coverage measured 89% on 2026-08-20, so the threshold
#   is slack the door can carry rather than a number chosen to be survivable.
#
# Step 7 needs `pytest-cov`, which CI installs and a fresh clone of this host does not have. If it
# is missing pytest rejects the flags and the step fails loudly - a missing instrument is a red,
# never a silently unenforced threshold, which is the whole reason the floor is stated as a flag
# here rather than read off a report afterwards.
#
# It also needs `node`, since T-A2-2: tests/test_intake_survives_a_failed_writeback.py RUNS the
# intake endpoint rather than reading it, and reports a missing node as a red rather than a skip.
# NODE'S VERSION IS A DIVERGENCE NOTHING COMPARES. CI pins 22 through `actions/setup-node`; this
# runs whatever the host has, v20.20.2 measured on 2026-08-21. The door/arbiter gate matches
# commands, not toolchains, so it is blind to this by construction - the workflow comment's "a
# version nothing here declares" is now true of the door instead. The probe's floor is NOT
# measured: it needs a global `crypto.randomUUID`, which arrived unflagged in Node 19, so the first
# draft of this line calling it harmless "while the probe uses nothing newer than Node 18" named a
# version on which it would not have run at all. What IS measured is both ends - 20.20.2 here, 22
# in CI - and the divergence is named rather than left for the day it stops being harmless. Found
# by Fable.
#
# The door builds with the `node_modules` already on this host while CI installs from the lockfile
# with `npm ci`. That difference is named rather than closed: a clean install at every push costs
# more than the drift it would catch. If `node_modules` is absent the build fails loudly, which is
# the correct reading - a missing instrument is a red, never a skip.
echo "6/8 site";     ( cd web && npm run build >/dev/null )
echo "7/8 tests";    python3 -m pytest tests -q --cov=src --cov-fail-under=70 | tail -3

# MYPY IS NOT HERE, AND THAT IS THE MEASURED ANSWER RATHER THAN AN OVERSIGHT.
# It runs in CI with its findings suppressed, so it cannot turn `main` red and the door omitting it
# creates no asymmetry. Its advisory state expires on 2026-10-15; when it becomes blocking, the
# comparison above fails until mypy is added here, in that same commit.

# T-63: A GREEN "7/8 tests" ABOVE DOES NOT MEAN A READER'S FIRST RUN WORKS.
#
# It proves the suite passes in THIS host's own already-provisioned interpreter - the exact
# blindness AUD-011 named once already (a fix "verified on a fresh clone" that ran somewhere the
# dependency it was checking for was already installed). tests/test_reproduce_readme.py clones this
# tree into a scratch directory and a genuinely fresh virtualenv and runs README.md's own "## Run
# it" commands there, unmodified - catching exactly the class of defect that instrument was blind
# to: a `pip install` that only works because this host's pip had already been upgraded for some
# other reason. It skips under the bare "7/8 tests" run above (see its own docstring for why -
# unguarded it would clone and run the ENTIRE suite, including itself, without a floor) and is
# armed here instead, the same PROVEK_REPRODUCE_README=1 gates.yml's `reproduce` job sets.
echo "8/8 reproduce"; PROVEK_REPRODUCE_README=1 python3 -m pytest tests/test_reproduce_readme.py -q

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
# T-S11: this used to read `git status --porcelain` straight into a variable, and an empty result
# is also what git prints when it warned on stderr and left a subtree out of stdout entirely - the
# same hole D-33 closed in publishable_tree.py, here at the door itself. clean_tree_gate.sh keeps
# UNREADABLE apart from DIRTY and apart from CLEAN; its red run is fixture-tested, not asserted.
./scripts/clean_tree_gate.sh

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
