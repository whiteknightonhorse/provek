#!/usr/bin/env bash
# Run work INSIDE the declared resource budget. Everything heavy goes through here.
#
# CONCURRENCY = 1 (hard). One claude/node session takes 300-500 MB; three in parallel would break
# the 1.5 GB cap and repeat the neighbours' OOM. Serialised with flock, not with hope.
#
# DEFERRAL IS A NAMED FINDING, NOT SILENCE: if the slot is busy we PRINT it. Silent deferral is
# indistinguishable from idleness.
set -u
LOCK=/tmp/incubator.slot.lock
exec 9>"$LOCK"
if ! flock -n 9; then
  echo "DEFERRED: the slot is held by another run (concurrency=1). This is a finding, not silence." >&2
  exit 75   # EX_TEMPFAIL - distinct from a real error
fi
exec systemd-run --user --scope --slice=incubator.slice --quiet "$@"
