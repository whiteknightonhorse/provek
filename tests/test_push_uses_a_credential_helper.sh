#!/usr/bin/env bash
# T-0571: push.sh and sync_main.sh authenticate with the tenant's own PROVEK_GITHUB_TOKEN through a
# credential helper passed to ONE git command. No set-url, no URL carrying the token, no
# .git/config write, no privilege escalation. A stub `git` on PATH records argv, so the test can
# fail: restoring the old splice makes the set-url assertions red.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAKE="fixture-token-not-a-secret"
URL="https://github.com/whiteknightonhorse/provek.git"
fail=0
check() { if [ "$1" = ok ]; then echo "ok   - $2"; else echo "FAIL - $2"; fail=1; fi; }

W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
mkdir -p "$W/bin" "$W/repo/scripts"
cat > "$W/bin/git" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$STUB_LOG"
if [ "$1" = "remote" ] && [ "$2" = "get-url" ]; then echo "${STUB_URL}"; exit 0; fi
if [ "$1" = "rev-parse" ]; then echo 0000000000000000000000000000000000000001; exit 0; fi
exit 0
EOF
chmod +x "$W/bin/git"
printf '[remote "origin"]\n\turl = %s\n' "$URL" > "$W/repo/config"

# the push step of push.sh: everything from the T-0571 block to the end of the file
sed -n '/^TOKEN_VAR=/,$p' "$ROOT/scripts/push.sh" > "$W/push_tail.sh"
cp "$ROOT/scripts/sync_main.sh" "$W/repo/scripts/sync_main.sh"

run_push() { (cd "$W/repo" && env "${@:2}" STUB_LOG="$W/log" STUB_URL="$1" PATH="$W/bin:$PATH" bash "$W/push_tail.sh"); }

# 1. token set: helper passed, push issued, no set-url, URL untouched, token not in argv
: > "$W/log"
out=$(run_push "$URL" PROVEK_GITHUB_TOKEN="$FAKE" 2>&1); rc=$?
[ $rc -eq 0 ] && check ok "push exits 0 with a token" || check no "push exits 0 with a token ($rc: $out)"
grep -q 'credential.helper=!f()' "$W/log" && grep -q ' push -q origin main' "$W/log" && check ok "helper passed to the push" || check no "helper passed to the push"
grep -q 'set-url' "$W/log" && check no "no set-url call" || check ok "no set-url call"
grep -q "$FAKE" "$W/log" && check no "token value not in argv" || check ok "token value not in argv"
grep -q 'x-access-token@\|x-access-token:' "$W/log" && check no "no token URL in argv" || check ok "no token URL in argv"

# 2. missing token: exit 1, the sentence, git never called for push
: > "$W/log"
out=$(run_push "$URL" -u PROVEK_GITHUB_TOKEN 2>&1); rc=$?
[ $rc -ne 0 ] && echo "$out" | grep -q "a push needs the tenant's own token" && check ok "missing token refused with the sentence" || check no "missing token refused with the sentence ($rc: $out)"
grep -q ' push ' "$W/log" && check no "no push without a token" || check ok "no push without a token"

# 3. remote URL changed behind the push: REFUSED
out=$(run_push "https://x-access-token:abc@github.com/whiteknightonhorse/provek.git" PROVEK_GITHUB_TOKEN="$FAKE" 2>&1); rc=$?
[ $rc -ne 0 ] && echo "$out" | grep -q 'REFUSED: remote URL changed' && check ok "changed remote URL refused" || check no "changed remote URL refused ($rc: $out)"

# 4. sync_main.sh: same door for the fetch
: > "$W/log"
out=$(cd "$W/repo" && env STUB_LOG="$W/log" STUB_URL="$URL" PATH="$W/bin:$PATH" PROVEK_GITHUB_TOKEN="$FAKE" bash scripts/sync_main.sh 2>&1); rc=$?
[ $rc -eq 0 ] && check ok "sync_main exits 0 with a token" || check no "sync_main exits 0 ($rc: $out)"
grep -q 'credential.helper=!f()' "$W/log" && grep -q ' fetch -q origin main' "$W/log" && check ok "helper passed to the fetch" || check no "helper passed to the fetch"
grep -q 'set-url' "$W/log" && check no "sync_main: no set-url call" || check ok "sync_main: no set-url call"
: > "$W/log"
out=$(cd "$W/repo" && env -u PROVEK_GITHUB_TOKEN STUB_LOG="$W/log" STUB_URL="$URL" PATH="$W/bin:$PATH" bash scripts/sync_main.sh 2>&1); rc=$?
[ $rc -eq 1 ] && echo "$out" | grep -q 'PROVEK_GITHUB_TOKEN not set' && check ok "sync_main refuses without a token" || check no "sync_main refuses without a token ($rc)"

# 5. nothing wrote the token into the fixture's git config
if ! grep -q "x-access-token" "$W/repo/config"; then check ok "fixture config never contains x-access-token"; else check no "fixture config contains x-access-token"; fi

# 6. neither script contains a privilege escalation word
grep -nE '(^|[^A-Za-z0-9_./-])sudo([[:space:]]|$)' "$ROOT/scripts/push.sh" "$ROOT/scripts/sync_main.sh" >/dev/null && check no "no sudo in push.sh / sync_main.sh" || check ok "no sudo in push.sh / sync_main.sh"

exit $fail
