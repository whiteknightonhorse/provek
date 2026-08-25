#!/usr/bin/env bash
# LAW-DEPLOY-LABEL-TRUE, second half - the label is read back OFF THE LIVE SITE, not off the tool.
#
# WHY THIS EXISTS. `scripts/deploy_label.py` decides what a deployment is called. Nothing proved
# that the thing now answering on provek.dev IS that deployment. `verify_live.sh` cannot close it
# by construction: it measures LIVENESS - eight addresses and the codes they must answer - and every
# one of those codes is answered just as well by last week's deployment. So the failure class
# "wrangler exited 0 and published nothing, or published somewhere else" reads GREEN end to end:
# `/api/apply` still returns 405 from the old upload, every page still returns 200, and the deploy
# log records a confirmation for an upload that never landed. That is this project's founding
# defect - a green light over an unmeasured fact - and D-26's claim that a wrangler regression would
# be caught was true of exactly one class of breakage until this file existed. Found by Fable.
#
# WHY BOTH HALVES ARE HERE AND NOT ONE IN THE DEPLOY SCRIPT. The name of the file is the only thing
# the writer and the reader must agree on, and a filename in two places is a rule written twice
# (L-2) - it would drift the first time either side was edited, and the drift would show up as a
# permanently red deploy or, worse, as a check reading an address nobody writes. One constant, two
# subcommands, and `tests/test_deploy_stamp.py` drives the round trip so the agreement is machine-
# checked rather than remembered.
#
# IT IS A SEPARATE SCRIPT RATHER THAN AN OPTIONAL FLAG ON `verify_live.sh` FOR ONE REASON: an
# optional check is a check that can be absent, and "the label was not compared" would then look
# exactly like "the label matched". The label is a required argument here; without it this script
# refuses to run rather than passing.
set -uo pipefail

# The one address both halves must agree on. Served from the upload root, so it is a plain static
# asset - it needs no Function, and therefore stays readable in exactly the degraded state
# (static-only upload) that it is partly there to detect.
LABEL_FILE="deploy-label.txt"
TIMEOUT_S=20

usage() {
  echo "usage: $0 stamp  <label> <directory>   # write the label into a built upload" >&2
  echo "       $0 verify <label> [base-url]    # read it back off the live site" >&2
}

# Same table as verify_live.sh, and for the same reason: `curl -w '%{http_code}'` prints 000 when no
# HTTP exchange happened at all, and read as a code that is "not 200" - the SAME red as a genuinely
# wrong answer. "The site answered wrongly" and "we could not ask" are two states, never one.
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

cmd="${1:-}"
label="${2:-}"

if [ -z "$cmd" ] || [ -z "$label" ]; then
  echo "REFUSED: no label was given, so there is nothing to write or to compare against." >&2
  echo "This is not a passing check with a missing argument - it is a check that did not run." >&2
  usage
  exit 64
fi

case "$cmd" in
  stamp)
    dir="${3:-}"
    if [ -z "$dir" ] || [ ! -d "$dir" ]; then
      echo "REFUSED: '$dir' is not a directory, so the label cannot be placed in the upload." >&2
      exit 64
    fi
    printf '%s\n' "$label" > "$dir/$LABEL_FILE" || {
      echo "REFUSED: could not write $dir/$LABEL_FILE - the upload would go out unlabelled." >&2
      exit 1; }
    echo "STAMPED: $dir/$LABEL_FILE = $label"
    ;;

  verify)
    base="${3:-${PROVEK_BASE_URL:-https://provek.dev}}"
    url="${base}/${LABEL_FILE}"
    # ONE REQUEST, BECAUSE THE BODY AND THE CODE MUST COME FROM THE SAME EXCHANGE.
    #
    # The first version of this took two: `--fail-with-body` for the text, then a second curl with
    # `-w '%{http_code}'` for the code. Three defects, all found by Fable. The second curl's exit
    # status was never read, so a transport that died between the two printed `000`, and `000` is
    # not 200 - the refusal of the instrument would have been announced as "LABEL NOT PUBLISHED",
    # a verdict about the site, three lines under the comment at the top of this file explaining
    # why `000` must never be read as a code. Worse, the two answers could come from two different
    # deployments, so a switch in that window would have produced a mismatch report quoting a body
    # from one upload against a code from another - a red on a chimera. And a body fetched at 404
    # would have been compared as if it were a label.
    #
    # `-w '\n%{http_code}'` puts the code on its own last line of the same response, so there is
    # one exchange, one exit status, and no window.
    # A WINDOW FOR PROPAGATION, AND ONLY THAT. Measured 2026-08-25: this check read the old
    # label, printed WRONG DEPLOYMENT IS LIVE, and the edge served the new one seconds later. The
    # deployment was in Production in `wrangler pages deployment list` the whole time. A false red
    # costs exactly what a false green costs -- it teaches the next reader that this gate is noise
    # and to push past it -- so the read is retried for a bounded window before any verdict.
    #
    # The window is bounded and STATED IN THE FAILURE, so a real mismatch is still a mismatch and
    # nobody has to guess whether it was given time. Retries happen only while the answer is a
    # readable 200 carrying the WRONG label: an unreadable address and a non-200 stay immediately
    # red, because those are not "not yet", they are "not measured" and "in trouble".
    # Overridable so the suite does not pay the window on every run: the wrong-label test asserts
    # the REFUSAL, and making it wait sixty real seconds to do so is how a suite becomes something
    # people skip. Production leaves both unset and gets the full window.
    PROPAGATION_TRIES="${DEPLOY_LABEL_TRIES:-10}"
    PROPAGATION_SLEEP_S="${DEPLOY_LABEL_SLEEP_S:-6}"
    attempt=0
    while : ; do
    attempt=$((attempt + 1))
    answer=$(curl -sS -m "$TIMEOUT_S" -w '\n%{http_code}' "$url" 2>/dev/null)
    rc=$?
    if [ "$rc" != "0" ]; then
      echo "UNREADABLE: $url could not be read at all - $(curl_reason "$rc")."
      echo "That is NOT a statement about which deployment is live. It is the absence of one, and"
      echo "it is red for that reason: an unmeasured address must never pass as a measured one."
      exit 1
    fi
    code="${answer##*$'\n'}"
    body="${answer%$'\n'*}"
    if [ "$code" != "200" ]; then
      # 404 and 5xx are different faults and the text says which was seen rather than guessing.
      # A 404 is the failure this file was written for; a 5xx is a live origin in trouble, and
      # telling an operator "no label is published" about a 503 would send them to the wrong place.
      echo "LABEL NOT CONFIRMED: $url answered $code, not 200."
      if [ "$code" = "404" ]; then
        echo "There is no label at that address, so the upload that is live is NOT the one this"
        echo "run built. The commonest cause is a publish that reported success and landed nowhere."
      else
        echo "The address is served but did not answer with the label, so WHICH deployment is live"
        echo "is unmeasured - which is neither a confirmation nor a mismatch."
      fi
      exit 1
    fi
    live=$(printf '%s' "$body" | tr -d '\r\n')
    if [ "$live" != "$label" ]; then
      if [ "$attempt" -lt "$PROPAGATION_TRIES" ]; then
        sleep "$PROPAGATION_SLEEP_S"
        continue
      fi
      # THE COUNT REPORTED IS THE ONE PERFORMED, not the one configured. Written the other way
      # first, and its own test could not tell the two apart: disabling the retry entirely left
      # the message still claiming three reads over sixty seconds while it had read once. An error
      # text that overstates what it did is the defect this repository exists to name, and it had
      # got into the sentence whose whole job is to be believed.
      waited=$(( (attempt - 1) * PROPAGATION_SLEEP_S ))
      echo "WRONG DEPLOYMENT IS LIVE: $url says '$live', this run published '$label'."
      echo "Read $attempt time(s) over ${waited}s, so this is not the edge catching up."
      echo "The tool reported success over an upload that did not become the live one."
      exit 1
    fi
    if [ "$attempt" -gt 1 ]; then
      echo "(the edge served the previous label for $(( (attempt - 1) * PROPAGATION_SLEEP_S ))s first)"
    fi
    echo "LABEL CONFIRMED: $url says '$live', which is what this run published."
    break
    done
    ;;

  *)
    echo "REFUSED: unknown subcommand '$cmd'." >&2
    usage
    exit 64
    ;;
esac
