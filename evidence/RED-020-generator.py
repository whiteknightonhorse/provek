#!/usr/bin/env python3
"""Produces evidence/RED-020-deploy-confirmed-over-a-dead-intake.txt.

    python3 evidence/RED-020-generator.py            # writes the artefact beside this file
    python3 evidence/RED-020-generator.py --check    # runs everything, writes nothing

WHAT IT ESTABLISHES. That `tests/test_verify_live_reads_the_function.py` CAN fail (invariant 5),
in each of the six directions the new deploy check is filed under. The subject is a shell script,
which is the shape a gate is least often proved over: nothing in a `.sh` fails a build by itself,
and the check it replaces - five `curl`s inside the operator's deploy script, outside every clone -
printed DEPLOY CONFIRMED on 2026-08-20 over an intake that read 404 on 2026-08-21 and on 2026-08-24
with no deployment recorded in between.

MUTATION 1 IS THE DEFECT ITSELF, restored verbatim: delete `/api/apply` from the address list and
the script becomes the five-address check that shipped the failure. If the suite stayed green under
that, it would be a suite that could not have caught what T-H1 found.

WHAT IT REFUSES TO WRITE THE ARTEFACT OVER, each inherited from RED-017/018 because each caught a
real draft there:
  * a mutation whose anchor is not unique, or which leaves the file unchanged - an edit that did
    not land is a transcript about the pristine script;
  * a mutation that does not turn the suite red - a gate unarmed against the edit it is filed under
    is the whole subject;
  * a pytest that did not RUN: only exit 1 is a suite that ran and failed. Any other nonzero is an
    instrument that asserted nothing, and reading it as "red" would be invariant 1 inside the tool
    kept to defend invariant 1;
  * a mutation that killed the INSTRUMENT CONTROL - see CONTROL below;
  * two mutations with the same failure set, which would mean one of them proves nothing the other
    did not (the transposition RED-013 was corrected for);
  * a script not restored byte for byte, or a suite not green again afterwards.

It writes the file itself rather than being redirected into it: a shell truncates its target before
Python starts, so every refusal above would empty the committed artefact on its way to declining to
replace it (the defect RED-017's generator shipped and names).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "scripts" / "verify_live.sh"
ARTEFACT = ROOT / "evidence" / "RED-020-deploy-confirmed-over-a-dead-intake.txt"
SUITE = "tests/test_verify_live_reads_the_function.py"

CONTROL = "test_the_probe_never_writes"
"""THE TEST THAT PROVES THE SCRIPT STILL RAN AND STILL REACHED AN ORIGIN.

It reads the stub's method log and requires exactly `{GET}`. No mutation below is ABOUT the method,
so its red would mean the script had stopped working rather than stopped checking - and a suite
that fails because the subject no longer executes establishes nothing about what the subject
asserts. A test cannot be both the control for a mutation and the property it removes."""

PREVIOUS_CHECK = """\
echo "== сверка ЖИВОГО сайта, а не отчёта =="
sleep 8
fail=0
for u in / /apply/ /registry/ /method/ /phase-2/; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 20 "https://provek.dev$u")
  printf '  %-12s %s\\n' "$u" "$code"
  [ "$code" = "200" ] || fail=1
done
if [ "$fail" = "1" ]; then
  echo "ДЕПЛОЙ НЕ ПОДТВЕРЖДЁН: не все адреса отдают 200"
  exit 1
fi
echo "ДЕПЛОЙ ПОДТВЕРЖДЁН на $SHA\""""
"""THE CHECK THAT WAS REPLACED, KEPT VERBATIM BECAUSE THE EDIT DESTROYED THE ONLY COPY.

`~/orchestra/` is not a git repository and the deploy script had no backup, so overwriting it left
the causal claim in this file resting on a second-hand log line. A verifier that erases the artefact
it is arguing from has done to itself what it audits others for. Six addresses cost two lines here;
the missing sixth let its one confirmation stand over a dead endpoint from 2026-08-20 to
2026-08-24."""

LIVE_READING = """\
$ ./scripts/verify_live.sh                                    # 2026-08-24T01:23Z, before the fix
== live reading of https://provek.dev (GET only; a POST here would create an intake record) ==
  /            200          expected 200
  /apply/      200          expected 200
  /registry/   200          expected 200
  /method/     200          expected 200
  /phase-2/    200          expected 200
  /api/apply   404          EXPECTED 405
               ^ the Pages Function is NOT published: this deployment shipped
                 web/dist and nothing else, so the intake form on /apply/ cannot
                 succeed on any input. Deploy from web/ so that web/functions/ is
                 in wrangler's working directory.
LIVE READING RED: 1 address(es) did not answer as they must.
$ echo $?
1"""
"""A RECORDED READING, NOT A RE-TAKEN ONE, and the distinction is the reason it sits in a constant.

It is the live state of provek.dev at the moment the address was first read by this script, and it
cannot be reproduced after the deployment it caused: re-running the command today reads 405. The
generator therefore does not pretend to take it again - a network reading embedded in a
deterministic artefact would be a measurement whose truth depends on the day the reader runs it."""

# (name, why it matters, anchor, replacement, marker that must appear afterwards)
MUTATIONS = [
    (
        "THE DEFECT ITSELF - the five-address check restored",
        "The address list loses /api/apply, which is exactly the check that shipped: five static "
        "pages answering 200 while the endpoint behind the only button on the site answered 404.",
        '  "/api/apply:405"\n',
        "",
        None,
    ),
    (
        "404 accepted as the healthy answer",
        "The address is walked, and the dead state is what the script calls alive. A check can name "
        "an address and still be blind to it if it expects the failure.",
        '"/api/apply:405"',
        '"/api/apply:404"',
        '"/api/apply:404"',
    ),
    (
        "red, with the cause unnamed",
        "The run goes red and says only that a code was not the expected one. The operator is left "
        "to guess between a broken function, a routing change and a deploy that shipped no function "
        "at all - which is L-23, a number offered where a reason is owed.",
        '  if [ "$path" = "/api/apply" ] && [ "$code" = "404" ]; then',
        '  if false; then',
        "if false; then",
    ),
    (
        "the instrument's refusal wearing an HTTP code",
        "The curl exit status stops being consulted, so `%{http_code}` prints 000 for a request that "
        "never happened and the run reports it as a code that merely was not 200. 'The site answered "
        "wrongly' and 'we could not ask' become one line: invariant 1.",
        '  if [ "$rc" != "0" ]; then',
        '  if [ "$rc" = "-1" ]; then',
        'if [ "$rc" = "-1" ]; then',
    ),
    (
        "a list carried but never walked",
        "Only the first address is read. The remaining five are still printed in the source for a "
        "reader to be reassured by, which is the difference between a check and a declaration.",
        '  want="${entry##*:}"\n',
        '  want="${entry##*:}"\n  [ "$path" = "/" ] || continue\n',
        '[ "$path" = "/" ] || continue',
    ),
    (
        "a gate you can walk past",
        "Every address is read, every failure is printed, and the script exits 0 anyway. This is the "
        "shape push.sh was written after: a check whose finding does not stop anything is a check "
        "that manufactures confidence.",
        'echo "LIVE READING RED: ${failed} address(es) did not answer as they must."\n  exit 1',
        'echo "LIVE READING RED: ${failed} address(es) did not answer as they must."\n  exit 0',
        'did not answer as they must."\n  exit 0',
    ),
]


def run_suite() -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", SUITE, "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    return p.returncode, p.stdout + p.stderr


def failed_tests(output: str) -> set[str]:
    """Test names from pytest's FAILED lines. An empty set from a red run is itself a refusal."""
    return set(re.findall(r"^FAILED [^:]+::([\w\[\]/.\-]+)", output, re.MULTILINE))


def die(msg: str) -> None:
    sys.stderr.write(f"REFUSING TO WRITE THE ARTEFACT: {msg}\n")
    raise SystemExit(2)


def main() -> int:
    write = "--check" not in sys.argv
    pristine = SRC.read_text(encoding="utf-8")

    rc, out = run_suite()
    if rc != 0:
        die(f"the suite is not green before any mutation - there is nothing to prove.\n{out}")
    baseline = out.strip().splitlines()[-1]

    sections: list[str] = []
    seen_failures: dict[frozenset[str], str] = {}
    try:
        for i, (name, why, anchor, repl, marker) in enumerate(MUTATIONS, start=1):
            if pristine.count(anchor) != 1:
                die(f"mutation {i} ({name}): its anchor appears {pristine.count(anchor)} times, not once")
            broken = pristine.replace(anchor, repl, 1)
            if broken == pristine:
                die(f"mutation {i} ({name}): the edit did not change the file")
            if marker and marker not in broken:
                die(f"mutation {i} ({name}): the marker is absent afterwards - the edit did not land")
            SRC.write_text(broken, encoding="utf-8")

            rc, out = run_suite()
            if rc == 0:
                die(f"mutation {i} ({name}): the suite stayed GREEN - it is not armed against this")
            if rc != 1:
                die(f"mutation {i} ({name}): pytest exited {rc}, which is an instrument that did not "
                    f"run rather than a suite that failed.\n{out}")
            fails = failed_tests(out)
            if not fails:
                die(f"mutation {i} ({name}): red with no FAILED line parsed - the harness cannot read "
                    f"its own instrument.\n{out}")
            if CONTROL in fails:
                die(f"mutation {i} ({name}): it killed the control {CONTROL}, so the script stopped "
                    f"running rather than stopped checking")
            key = frozenset(fails)
            if key in seen_failures:
                die(f"mutation {i} ({name}): identical failure set to {seen_failures[key]} - one of "
                    f"the two proves nothing the other does not")
            seen_failures[key] = name

            sections.append(
                f"----- MUTATION {i}: {name} -----\n\n"
                f"WHY IT MATTERS. {why}\n\n"
                f"  {anchor.strip() or '(the line above, deleted)'}\n"
                f"    ->  {repl.strip() or '(deleted)'}\n\n"
                f"FAILED: {', '.join(sorted(fails))}\n\n"
                f"{out.strip()}\n")
    finally:
        SRC.write_text(pristine, encoding="utf-8")

    if SRC.read_text(encoding="utf-8") != pristine:
        die("the script was not restored byte for byte")
    rc, out = run_suite()
    if rc != 0:
        die(f"the suite is not green again after the restore.\n{out}")

    body = (
        "RED-020 - the deploy check, proved able to go red on a dead intake\n\n"
        "DATE (UTC): 2026-08-24\n"
        "SUBJECT   : scripts/verify_live.sh, judged by " + SUITE + "\n\n"
        "WHY THIS FILE EXISTS. Invariant 5: a test must be ABLE to fail, and the red run is the\n"
        "only proof of it. The check this one replaces read five static addresses and printed\n"
        "DEPLOY CONFIRMED; the address the site's only call to action depends on was not among\n"
        "them, and answered 404 through every confirmation it printed.\n\n"
        "THE CHECK THAT PRINTED THE CONFIRMATION, kept here because the edit that replaced it\n"
        "destroyed the only copy - ~/orchestra is not a git repository and held no backup:\n\n"
        + "\n".join("    " + line for line in PREVIOUS_CHECK.splitlines()) + "\n\n"
        "THE DEFECT, MEASURED ON THE LIVE SITE BEFORE THE FIX:\n\n"
        + "\n".join("    " + line for line in LIVE_READING.splitlines()) + "\n\n"
        "Five green lines and one red one. The check above reads only the five.\n\n"
        "BASELINE (pristine script): " + baseline + "\n"
        "CONTROL (must stay green under every mutation): " + CONTROL + "\n\n"
        "COMMAND: python3 evidence/RED-020-generator.py\n\n"
        + "\n".join(sections)
        + "\n----- RESTORED -----\n\n" + out.strip() + "\n"
    )

    if write:
        ARTEFACT.write_text(body, encoding="utf-8")
        print(f"wrote {ARTEFACT.relative_to(ROOT)} - {len(MUTATIONS)} mutations, all red, control held")
    else:
        print(f"--check: {len(MUTATIONS)} mutations, all red, control held, script restored")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
