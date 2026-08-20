#!/usr/bin/env bash
# Secret scan before push. It blocks; it does not warn.
#
# TRAP THIS SCRIPT WAS REWRITTEN OVER: a pipeline's exit status belongs to its LAST command. The
# first version ended in `| head -5`, which always returns 0, so the gate fired ALWAYS and blocked
# a clean tree. A false red is as harmful as a false green: it teaches people to bypass the gate.
# Hence the output is collected into a VARIABLE and the decision is made on its emptiness.
set -u
PATTERN='gh[pous]_[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9_-]{30,}|BEGIN [A-Z ]*PRIVATE KEY|0x[0-9a-f]{64}'
hits=$(git grep -nE "$PATTERN" -- . 2>/dev/null || true)
if [ -n "$hits" ]; then
  echo "X SECRET SCAN: findings, push blocked" >&2
  echo "$hits" | head -20 >&2
  exit 1
fi
echo "secret scan: clean"
