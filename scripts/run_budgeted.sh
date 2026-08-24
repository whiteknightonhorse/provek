#!/usr/bin/env bash
# Run work INSIDE the declared resource budget. Everything heavy goes through here.
#
# CONCURRENCY = 1 (hard). One claude/node session takes 300-500 MB; three in parallel would break
# the 1.5 GB cap and repeat the neighbours' OOM. Serialised with flock, not with hope.
#
# THE LOCK IS NOT IN /tmp, AND THAT IS THE WHOLE POINT OF THIS FILE'S EXISTENCE.
#
# It was `LOCK=/tmp/incubator.slot.lock` until T-S6. `/tmp` on this host is mode 1777 and ten
# projects share it, so the path holding the project's only concurrency guarantee was one any
# neighbour could have created first - as a file with the wrong mode, or as a symlink pointing
# somewhere else entirely. Whoever creates the path owns it; the sticky bit stops others deleting
# it, not others getting there first. A permission error would at least be visible. The failure
# that is NOT visible is the one that matters here: the guarantee quietly ceasing to exist in
# exactly the circumstance it was written for. Measured before the move, and recorded in
# `evidence/MEASURED-002-the-shared-lock-this-project-was-relying-on.txt`: the old path was in
# fact still ours, so nothing had been lost yet - which is a fact about luck, not about design.
#
# The lock now lives beside the checkout that defines the project. It is derived from this
# script's own location rather than named as a constant, so a second checkout gets its own slot
# instead of silently contending with this one, and there is exactly one rendezvous point per
# project. `.state/` is gitignored, so it does not dirty the tree the door refuses to push.
#
# THE ONE HAZARD THIS TRADES FOR: an advisory lock lives on the INODE. Unlink the file while it is
# held and the next run creates a fresh inode and takes it, so two runs proceed. `git clean` is
# forbidden in this project without exception (CLAUDE.md), which is the same rule that protects the
# evidence corpus, and it is what keeps this trade sound.
#
# THREE OUTCOMES, NOT TWO. "The slot is busy" and "the lock could not be taken at all" are
# different facts and this script had been printing the first for both. A refusal wearing the face
# of contention is invariant 1 applied to the guarantee itself: it tells the caller to retry
# something that will never succeed, and it reports the concurrency limit as WORKING at the moment
# it has stopped existing. Red run: `evidence/RED-033-a-lock-that-was-never-taken-reported-as-contention.txt`.
#
#   exit 0  - the lock is held by us, the work runs
#   exit 75 - EX_TEMPFAIL, the slot is genuinely taken by another run. Retrying is meaningful.
#   exit 70 - EX_SOFTWARE, the guarantee could NOT be established. Retrying is not meaningful.
#
# DEFERRAL IS A NAMED FINDING, NOT SILENCE: if the slot is busy we PRINT it. Silent deferral is
# indistinguishable from idleness. So is a silent refusal, and that one is worse.
set -u

refuse() {
  echo "REFUSED: $* - concurrency=1 could NOT be established, so nothing was run." >&2
  echo "This is not a deferral: retrying will not help until the cause is repaired." >&2
  exit 70
}

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P) || \
  refuse "the project root could not be resolved from ${BASH_SOURCE[0]}"
STATE="$ROOT/.state"
LOCK="$STATE/slot.lock"

mkdir -p -m 700 "$STATE" || refuse "the state directory $STATE could not be created"

# `exec 9>` DOES NOT STOP THIS SHELL WHEN IT FAILS - measured, bash prints to stderr, returns 1 and
# carries on. The status is therefore read explicitly rather than trusted to end the script.
exec 9>"$LOCK"
opened=$?
[ "$opened" -eq 0 ] || refuse "the lock file $LOCK could not be opened for writing"

# AND A SUCCESSFUL flock IS NOT YET PROOF THAT WE LOCKED THE FILE WE NAMED.
#
# If descriptor 9 arrives already open - inherited from whatever invoked this script - then a
# failed `exec 9>` above leaves that INHERITED descriptor in place, `flock -n 9` locks the caller's
# unrelated file, and the work runs to completion, exit 0, with no lock on the slot at all. That
# was measured on the previous form of this script and it is the silent failure the exit codes
# above cannot help with, because it produces no error at all. `/proc/self/fd/9` resolves to the
# real target, so a lock path that is a SYMLINK to somewhere else is refused here too - which is
# the /tmp hijack in its precise form.
held=$(readlink -- /proc/self/fd/9 2>/dev/null) || held=""
[ "$held" = "$LOCK" ] || \
  refuse "descriptor 9 is open on '${held:-nothing}', not on the lock this script named ($LOCK)"

# flock -n: 0 = taken, 1 = would block, anything else = the instrument itself failed. A missing
# flock binary exits 127 here, and folding that into the deferral branch is what reported an
# uninstalled tool as a busy neighbour.
flock -n 9
rc=$?
case "$rc" in
  0) ;;
  1) echo "DEFERRED: the slot is held by another run (concurrency=1). This is a finding, not silence." >&2
     exit 75 ;;
  *) refuse "flock exited $rc, so the slot was never tested - this is not_measured, not 'free'" ;;
esac

exec systemd-run --user --scope --slice=incubator.slice --quiet "$@"
