#!/usr/bin/env bash
# T-H1 - the check that reads the LIVE site after a deployment, including the one address the
# previous check could not see.
#
# WHAT IT REPLACED, AND WHY THAT WAS NOT A COSMETIC GAP. The deploy script's own verification
# walked five static addresses and printed "DEPLOY CONFIRMED" when all five answered 200. What is
# recorded, and it is all that is claimed here: one confirmation in the operator's deploy log
# ("DEPLOY CONFIRMED on 6a4ab10", 2026-08-20), and `GET https://provek.dev/api/apply` answering 404
# on 2026-08-21 and again on 2026-08-24 - after that confirmation and with no deployment recorded
# between. `wrangler pages deploy` reads Functions from `functions/` RELATIVE TO THE WORKING
# DIRECTORY (wrangler 4.86.0, `pages deploy` has no --functions-directory flag), and the deploy ran
# from the repository root while the handler lives in `web/functions/api/apply.js`. So the
# deployment shipped static files only, the live `/apply/` form offered a submission that could not
# succeed on any input, and the check that was supposed to notice printed a confirmation over it.
# A green light over an unmeasured address is this project's own founding defect - a claim stronger
# than the artefact - sitting inside the instrument that is supposed to catch it.
#
# The first draft of this paragraph said the check "said DEPLOY CONFIRMED five times over" and tied
# the two 404 readings to "both of those confirmations". Neither number has an artefact behind it:
# the log holds one. Counting in a comment that indicts an uncounted claim is the same defect one
# level up, and Fable found it here before it was pushed.
#
# THE PROBE IS A GET AND MUST STAY ONE. `onRequestPost` writes a durable KV record and pages the
# operator on Telegram; a POST used as a health check would manufacture an applicant nobody applied
# for. `onRequestGet` answers 405 - "this endpoint accepts a submission, not a reading" - so the
# effect-free reading and the proof of publication are the same request:
#
#     405  the Function is published and routed
#     404  static assets only, no Function - the exact failure this file exists to catch
#
# WHY IT LIVES IN THE REPOSITORY AND NOT IN THE DEPLOY SCRIPT. The deploy script is on the
# operator's host, outside every gate and every clone; a check kept there is a check no reader can
# audit and no test can exercise. This one is judged by tests/test_verify_live_reads_the_function.py
# against a stub origin, so the red case is proved rather than asserted.
set -uo pipefail

BASE="${1:-${PROVEK_BASE_URL:-https://provek.dev}}"
TIMEOUT_S=20

# Address -> the code that means "this address is alive". `/api/apply` is the only one whose
# healthy answer is not 200, and that is the point of it.
CHECKS=(
  "/:200"
  "/apply/:200"
  "/registry/:200"
  "/method/:200"
  "/phase-2/:200"
  "/api/apply:405"
)

# A NUMBER IS NOT A REASON (L-23), and this is where the refusal of the instrument would otherwise
# be laundered into a finding: `curl -w '%{http_code}'` prints `000` when no HTTP exchange happened
# at all. Read as a code, `000` is "not 200" - which is the SAME red as a genuinely broken page,
# and the operator would go looking at Cloudflare for a fault that is in this host's network.
# Invariant 1: "the site answered wrongly" and "we could not ask" are two states, never one.
curl_reason() {
  case "$1" in
    6)  echo "the host name did not resolve" ;;
    7)  echo "the connection was refused" ;;
    28) echo "no answer within ${TIMEOUT_S}s" ;;
    35) echo "the TLS handshake failed - the host may serve no certificate at all" ;;
    60) echo "the certificate did not verify" ;;
    *)  echo "curl exit ${1}, which this script has no name for - look it up before believing it" ;;
  esac
}

echo "== live reading of ${BASE} (GET only; a POST here would create an intake record) =="

failed=0
unreadable=0
for entry in "${CHECKS[@]}"; do
  path="${entry%:*}"
  want="${entry##*:}"

  code=$(curl -sS -o /dev/null -w '%{http_code}' -m "$TIMEOUT_S" "${BASE}${path}" 2>/dev/null)
  rc=$?

  if [ "$rc" != "0" ]; then
    printf '  %-12s UNREADABLE   %s\n' "$path" "$(curl_reason "$rc")"
    unreadable=$((unreadable + 1))
    failed=$((failed + 1))
    continue
  fi

  if [ "$code" = "$want" ]; then
    printf '  %-12s %s          expected %s\n' "$path" "$code" "$want"
    continue
  fi

  printf '  %-12s %s          EXPECTED %s\n' "$path" "$code" "$want"
  # The named diagnosis for the one failure whose cause is already known. Everything else is
  # reported as an unexpected code rather than explained by a guess.
  if [ "$path" = "/api/apply" ] && [ "$code" = "404" ]; then
    echo "               ^ the Pages Function is NOT published: this deployment shipped"
    echo "                 web/dist and nothing else, so the intake form on /apply/ cannot"
    echo "                 succeed on any input. Deploy from web/ so that web/functions/ is"
    echo "                 in wrangler's working directory."
  fi
  failed=$((failed + 1))
done

if [ "$unreadable" != "0" ]; then
  echo "LIVE READING INCOMPLETE: ${unreadable} address(es) could not be read at all."
  echo "That is not a verdict about the site - it is the absence of one, and it is red for"
  echo "exactly that reason: an unmeasured address must never pass as a measured one."
  exit 1
fi

if [ "$failed" != "0" ]; then
  echo "LIVE READING RED: ${failed} address(es) did not answer as they must."
  exit 1
fi

echo "LIVE READING GREEN: all ${#CHECKS[@]} addresses answered as they must, /api/apply included."
