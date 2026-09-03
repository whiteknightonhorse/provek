#!/usr/bin/env bash
# Secret scan before push. It blocks; it does not warn.
#
# TRAP THIS SCRIPT WAS REWRITTEN OVER: a pipeline's exit status belongs to its LAST command. The
# first version ended in `| head -5`, which always returns 0, so the gate fired ALWAYS and blocked
# a clean tree. A false red is as harmful as a false green: it teaches people to bypass the gate.
# Hence the output is collected into a VARIABLE and the decision is made on its emptiness.
set -u
# AUD-006: kept identical, character for character, to SECRET_PATTERNS in src/collector/github.py
# (LAW #ONE-PLACE, enforced by tests/test_secret_scan_one_place.py - a comment saying "identical"
# is exactly the claim that drifts unless something reads both files and compares them).
PATTERN='gh[pous]_[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9_-]{30,}|BEGIN [A-Z ]*PRIVATE KEY|0x[0-9a-f]{64}|cfat_[A-Za-z0-9_-]{20,}|[ps]k1_[A-Za-z0-9]{20,}|r8_[A-Za-z0-9]{20,}|[0-9]{8,10}:[A-Za-z0-9_-]{35}'
hits=$(git grep -nE "$PATTERN" -- . 2>/dev/null || true)
if [ -n "$hits" ]; then
  echo "X SECRET SCAN: findings, push blocked" >&2
  echo "$hits" | head -20 >&2
  exit 1
fi
echo "secret scan: clean"
