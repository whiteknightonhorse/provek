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

echo "1/5 secrets";  ./scripts/secret_scan.sh
echo "2/5 scope";    python3 scripts/ratchet_scope.py
echo "3/5 laws";     python3 scripts/ratchet_decisions.py
echo "4/5 language"; python3 scripts/ratchet_language.py
echo "5/5 tests";    python3 -m pytest tests -q | tail -1

TOK=$(sudo grep -ohE 'gh[pous]_[A-Za-z0-9_]+' /home/audiobook2/.claude/gh.env | head -1)
if [ -z "$TOK" ]; then echo "no token" >&2; exit 1; fi
trap 'git remote set-url origin "https://github.com/whiteknightonhorse/provek.git" 2>/dev/null; unset TOK' EXIT
git remote set-url origin "https://x-access-token:${TOK}@github.com/whiteknightonhorse/provek.git"
git push -q origin main
echo "PUSH DONE, token removed from the remote config"
