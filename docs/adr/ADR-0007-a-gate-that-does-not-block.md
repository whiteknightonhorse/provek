# ADR-0007. A gate that does not stop is not a gate

**Date:** 2026-08-19. **Status:** accepted. **Basis:** our own miss, not someone else's review.

## What happened
The first push to GitHub succeeded while the ratchet was RED. The checks sat in a chain without
`set -e`: the failure printed to the log and execution carried on. The gate existed, reported, and
held nothing back.

## The second miss of the same day
The secret scan ended in `| head -5`. A pipeline's exit status belongs to its LAST command, and
`head` always returns 0 - so the scan fired ALWAYS and blocked a clean tree. A false red is as
harmful as a false green: it teaches people to bypass the gate.

## The third: the ratchet looked only at `*.py`
Shell scripts were outside supervision entirely. Extending it to `.sh` immediately found an
unmapped `run_budgeted.sh`. A checker that inspects one shape reports success on every other.

## Decision
The single door outward is `scripts/push.sh` with `set -euo pipefail`: secrets -> scope -> laws ->
language -> tests -> push. The token is placed into the remote for the duration and removed in a
`trap ... EXIT`.

## Proof, not assertion
`evidence/RED-002-push-gate.txt`: a planted unmapped module - the push was STOPPED.
A gate whose firing has never been shown remains a promise.
