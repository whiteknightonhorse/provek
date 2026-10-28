#!/usr/bin/env bash
# The single door outward. A gate that does not STOP is not a gate.
#
# THIS SCRIPT WAS WRITTEN AFTER A REAL MISS: the first push succeeded while the ratchet was RED,
# because the checks sat in a chain without `set -e` - a failure printed to the log and execution
# carried on. A gate you can walk past is worse than no gate: it manufactures a false sense of
# safety.
#
# Order: secrets -> scope -> laws -> language -> lint -> site -> tests -> reproduce -> genlayer ->
# push. This line had already drifted once - it still read "... -> language -> tests" after ruff
# was added below, which is the same header-outlives-its-list defect that let the door and CI
# diverge in the first place, sitting three lines above the comment explaining that defect. The
# list that is actually compared against CI is `CI_GATES` in tests/test_door_matches_ci.py; this
# sentence is a reader's convenience and is not what enforces anything.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "1/9 secrets";  ./scripts/secret_scan.sh
echo "2/9 scope";    python3 scripts/ratchet_scope.py
echo "3/9 laws";     python3 scripts/ratchet_decisions.py
echo "4/9 language"; python3 scripts/ratchet_language.py
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
echo "5/9 lint";     python3 -m ruff check src tests scripts
if [ ! -x ~/orchestra/lintenv/bin/python ]; then
  echo "REFUSED: ~/orchestra/lintenv (the hash-pinned lint venv built from requirements/ci-lint.txt, T-MY-02) is missing - a missing venv is RED, not skip." >&2
  exit 1
fi
~/orchestra/lintenv/bin/python scripts/check_mypy_ceiling.py

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
echo "6/9 site";     ( cd web && npm run build >/dev/null )
echo "7/9 tests";    python3 -m pytest tests -q --cov=src --cov-fail-under=70 | tail -3

# MYPY IS HERE SINCE T-MY-02, in step 5 above, through the same program CI runs
# (scripts/check_mypy_ceiling.py): it goes red when the advisory backlog grows past the D-65
# ceiling or when mypy does not run. The advisory state still expires on 2026-12-14 (D-65).
#
# THE INSTRUMENT IS ~/orchestra/lintenv, NOT ~/.local. The host's user-site carried mypy 2.3.1
# against a `mypy==2.4.0` pin (measured 2026-10-19); a shared user-site is not an instrument. The
# venv is built from the hashed file with CI's own command, and the script refuses a mypy that is
# not the pin. When the pin moves, rebuild it:
#   python3 -m venv ~/orchestra/lintenv && ~/orchestra/lintenv/bin/pip install --quiet \
#     --require-hashes --only-binary=:all: -r requirements/ci-lint.txt

# T-63: A GREEN "7/9 tests" ABOVE DOES NOT MEAN A READER'S FIRST RUN WORKS.
#
# It proves the suite passes in THIS host's own already-provisioned interpreter - the exact
# blindness AUD-011 named once already (a fix "verified on a fresh clone" that ran somewhere the
# dependency it was checking for was already installed). tests/test_reproduce_readme.py clones this
# tree into a scratch directory and a genuinely fresh virtualenv and runs README.md's own "## Run
# it" commands there, unmodified - catching exactly the class of defect that instrument was blind
# to: a `pip install` that only works because this host's pip had already been upgraded for some
# other reason. It skips under the bare "7/9 tests" run above (see its own docstring for why -
# unguarded it would clone and run the ENTIRE suite, including itself, without a floor) and is
# armed here instead, the same PROVEK_REPRODUCE_README=1 gates.yml's `reproduce` job sets.
echo "8/9 reproduce"; PROVEK_REPRODUCE_README=1 python3 -m pytest tests/test_reproduce_readme.py -q

# T-GL-04. `integrations/genlayer-witness/` needs Python >= 3.12 (D-63) - this repository's own
# interpreter is 3.10, so this step alone reaches outside it, into the isolated venv T-GL-02 built
# for exactly this. A MISSING VENV IS RED, NOT SKIP: silently skipping the one step nothing else
# here can cover would be invariant 1's own mistake, aimed at this door.
echo "9/9 genlayer"
# T-GLR-04. The venv is `glenv-babwp`, not the T-GL-02 `glenv` it replaces: that one holds the
# genlayer-test 0.29.2 harness, which cannot load the py-genlayer runner Bradbury Phase 2 executes
# (`babwp9t37j...`, header `# v0.3.0`). Build it from the committed, hash-pinned closure:
#   python3.12 -m venv ~/orchestra/glenv-babwp && ~/orchestra/glenv-babwp/bin/pip install --quiet \
#     --require-hashes --only-binary=:all: --no-deps -r requirements/ci-genlayer.txt
GLENV="${GLENV:-$HOME/orchestra/glenv-babwp}"
if [ ! -x "$GLENV/bin/python3" ]; then
  echo "REFUSED: $GLENV (the isolated Python 3.12 venv built from requirements/ci-genlayer.txt) is" >&2
  echo "missing or not executable - a missing venv is RED, not skip." >&2
  exit 1
fi
# The two GenVM-bundle consumers (gltest's direct harness, genvm-linter) are told the version, so
# neither asks GitHub for "latest" (see gates.yml's matching step for the full account).
export GENVM_VERSION=v0.6.0-rc10 GENVM_ALLOW_PRERELEASE=1
# Same cache-priming as gates.yml - guarded, since this host needs the 310 MB bundle once, not on
# every push.
GENVM_TARBALL=~/.cache/gltest-direct/bundles-v2/genvm-universal-v0.6.0-rc10.tar.xz
if [ ! -f "$GENVM_TARBALL" ]; then
  mkdir -p ~/.cache/gltest-direct/bundles-v2
  curl -fsSL -o "$GENVM_TARBALL" \
    https://github.com/genlayerlabs/genvm-manager/releases/download/v0.6.0-rc10/genvm-universal.tar.xz
fi
# THE DOOR'S OWN CACHE OUTLIVES ANY SINGLE PUSH, SO THE GUARD ABOVE IS BLIND TO IT GOING STALE.
#
# The existence check above only proves A file is sitting there under that name - not that it is
# still the asset this project pinned. A release ASSET, unlike a tag, is a fourth movable pointer
# this file's own header did not count (see gates.yml's matching step for the full argument): the
# same tag can serve a re-uploaded or truncated asset under an unchanged name, and an existence
# check alone would trust it silently, forever. Checked against the one committed digest (D-79)
# every time this step runs, cached copy or fresh download alike - not only on the branch that
# just downloaded it.
want="$(cat integrations/genlayer-witness/genvm-universal-v0.6.0-rc10.sha256)"
got="$(sha256sum "$GENVM_TARBALL" | cut -d' ' -f1)"
if [ "$got" != "$want" ]; then
  echo "REFUSED: $GENVM_TARBALL sha256 mismatch (got $got, want $want, D-79) - a moved or" >&2
  echo "truncated release asset is RED here, never silently trusted." >&2
  exit 1
fi
mkdir -p ~/.cache/genvm-linter
cp "$GENVM_TARBALL" ~/.cache/genvm-linter/genvm-universal-genlayerlabs-genvm-manager-v0.6.0-rc10.tar.xz
# T-GA-01 (D-66): two contracts, one toolchain, one loop. The directory list is the same text in
# gates.yml's `genlayer` job; `tests/test_door_matches_ci.py` holds the steps, this loop is the list.
for d in integrations/genlayer-witness integrations/genlayer-apibase-attest; do
  ( cd "$d" \
    && "$GLENV/bin/python3" scripts/check_genvm_lint.py \
    && "$GLENV/bin/python3" -m pytest tests/direct -q \
    && "$GLENV/bin/python3" -m pytest --collect-only -q tests/integration )
done

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

# T-0571 (audit P5-08, P2-11): this door used to read a token with a root grep out of a NEIGHBOUR
# tenant's credential file, splice it into the remote URL and rely on an EXIT trap to put the URL
# back. Two measured defects: a privileged read of another tenant's secret, and a trap that a
# SIGKILL (intake's run() timeout) skips - which left the token in .git/config. Now the tenant
# pushes with its OWN token, handed to git by a credential helper for this one command: nothing is
# written to .git/config, there is no trap to rely on, and the remote URL is checked afterwards
# instead of restored.
TOKEN_VAR="PROVEK_GITHUB_TOKEN"
if [ -z "${PROVEK_GITHUB_TOKEN:-}" ]; then
  echo "PROVEK_GITHUB_TOKEN not set; push refused - a push needs the tenant's own token" >&2
  exit 1
fi
git -c credential.helper= \
    -c 'credential.helper=!f(){ printf "username=x-access-token\npassword=%s\n" "$PROVEK_GITHUB_TOKEN"; }; f' \
    push -q origin main
[ "$(git remote get-url origin)" = "https://github.com/whiteknightonhorse/provek.git" ] || { echo "REFUSED: remote URL changed" >&2; exit 1; }
echo "PUSH DONE"
