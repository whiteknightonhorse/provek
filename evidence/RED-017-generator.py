#!/usr/bin/env python3
"""Produces evidence/RED-017-nothing-was-saved-about-a-saved-record.txt.

    python3 evidence/RED-017-generator.py            # writes the artefact beside this file
    python3 evidence/RED-017-generator.py --check    # runs everything, writes nothing

IT WRITES THE FILE ITSELF rather than being redirected into it, and the reason is a defect the
first version shipped: the documented invocation was `... > evidence/RED-017-....txt`, and a shell
truncates its target before Python starts. So every refusal below - the ones this docstring is
mostly about - would have emptied the committed artefact on its way to refusing to write it, which
is the opposite of what "refuses to write" means. The output is assembled in full, written to a
temporary name and moved into place, so a refusal leaves the previous artefact untouched. Found by
Fable.

WHY IT IS CHECKED IN. The artefact claims that nine mutations of the intake endpoint each turn
LAW-INTAKE-SAVED-MEANS-SAVED red, and L-26 is the standing rule that a red run is evidence only
because it is the output of the command printed above it - which nobody can establish without the
command. The first version of this generator was a scratch file, deleted after use, and the
artefact still claimed in the present tense that "the generator refuses to write this file" if a
control fails: machinery asserted about a program the repository did not contain, in the artefact
kept to detect exactly that. Found by Fable.

WHERE IT LIVES, AND THE HOLE THAT ALLOWS IT. `scripts/` is scanned by `scripts/ratchet_scope.py`,
which would demand an `ABI-*` binding for a one-shot evidence generator - and inventing one is the
rubber stamp that ratchet's own docstring names as its degeneration (L-12, D-17). The ratchet scans
`src`, `scripts` and `demo`, so `evidence/` is outside its supervision; this file sits there
deliberately and the hole is named rather than papered over. The alternative taken elsewhere -
keeping the tool outside the repository - would make a committed artefact unreproducible by its
reader, which is the property L-26 asks for.

WHAT IT REFUSES TO WRITE THE ARTEFACT OVER, which has to be code rather than a sentence:
  * a mutation whose anchor is not unique, or whose marker does not appear in the file afterwards -
    an edit that did not land is a transcript about the pristine endpoint;
  * a mutation that does not turn the suite red - a gate unarmed against the edit it is filed under
    is the whole subject;
  * a pytest that did not RUN. Any nonzero exit was read as "red" in the first version, which is
    invariant 1 inside the instrument: a usage error, an internal error and a collection failure
    all exit nonzero and assert nothing. Only exit 1 is a suite that ran and failed;
  * a mutation that kills the suite's INSTRUMENT CONTROL. One of these was an `if (false) {` left
    facing a `catch`: the module stopped parsing, every scenario died, and eight tests went red
    under a heading claiming a property had been removed. A file that does not parse fails every
    test whatever the gate asserts, so that red established nothing;
  * two mutations with the same failure set - the transposition RED-013 was corrected for;
  * a restored endpoint that is not byte for byte the original, or that is not green.

The diff blocks in the output are printed from the same strings that perform the edits, so the
prose and the edit cannot disagree.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402 - T-S14, every artefact names the tree it was captured against

SRC = ROOT / "web" / "functions" / "api" / "apply.js"
ARTEFACT = ROOT / "evidence" / "RED-017-nothing-was-saved-about-a-saved-record.txt"
SUITE = "tests/test_intake_survives_a_failed_writeback.py"

# The one test that can only pass if the endpoint is still executing: a submission with an invalid
# repository URL, refusable by nothing but the endpoint's own validation.
CONTROL = "test_the_probe_is_exercising_the_real_endpoint"

WRITEBACK = """  try {
    await env.INTAKE.put(key, JSON.stringify({ ...record, delivered }));
  } catch (refusal) {"""

FIRST_PUT = "  await env.INTAKE.put(key, JSON.stringify({ ...record, delivered: null }));"

SENTINEL_OPEN = """    try {
      await env.INTAKE.put("""

NOTICE_CATCH = """    } catch {
      delivered = false;
    }"""

MUTATIONS = [
    (
        "1-writeback-uncaught",
        "THE DEFECT ITSELF, restored: the write-back leaves the `try` and is uncaught again. The "
        "`if (false)` keeps the sentinel block that follows syntactically attached, so what the "
        "mutation removes is the guard and nothing else.",
        WRITEBACK,
        "  await env.INTAKE.put(key, JSON.stringify({ ...record, delivered }));"
        "  // MUTATION: uncaught again\n  if (false) { const refusal = null;",
    ),
    (
        "2-catch-everything",
        "THE OPPOSITE ERROR, and the reason the gate asserts a biconditional: the DURABLE write is "
        "swallowed as well, which is what `wrap it in a try/catch` produces when it is aimed one "
        "line too high. Every assertion killed by mutation 1 passes here. What dies is the other "
        "direction - nothing is stored, so `Nothing was saved` is TRUE, and the endpoint confirms "
        "a submission that does not exist. Nobody sweeps for a record that was never written.",
        FIRST_PUT,
        "  try {  // MUTATION: the durable write is swallowed too\n" + FIRST_PUT +
        "\n  } catch { /* MUTATION */ }",
    ),
    (
        "3-no-sentinel",
        "THE FIX'S OWN DEFECT, which is what the first draft of this change shipped: the refusal "
        "is caught, the applicant is answered honestly, and nothing durable records that it "
        "happened - so `delivered: null` means both `told the truth` and `told that nothing was "
        "saved`, in the one field the operator's sweep acts on. Found by Fable. The sentinel is "
        "still computed and is handed to a call that stores nothing, because a mutation that "
        "deleted the block would change what the file PARSES to rather than what it does.",
        SENTINEL_OPEN,
        "    try {\n      await Promise.resolve(  // MUTATION: the sentinel is never stored",
    ),
    (
        "4-catch-only-what-a-stub-throws",
        "A CATCH NARROWED TO THE FAILURE SHAPE A TEST IS LIKELY TO THROW. It is green against a "
        "probe that only ever raises a 429 - which is what this suite did until Fable applied this "
        "exact mutation and watched it pass - and it restores the 500-over-a-durable-record defect "
        "for every other KV failure.",
        "  } catch (refusal) {",
        '  } catch (refusal) {  // MUTATION: only the shape the stub throws\n'
        '    if (!String(refusal).includes("429")) throw refusal;',
    ),
    (
        "5-delivery-outcome-is-a-constant",
        "THE VALUE THE OPERATOR ACTS ON, FROZEN. `delivered` stops following the notice and is "
        "always true, so every applicant is told the operator was notified and every sentinel "
        "records it. This was GREEN until Fable applied it: the probe's Telegram stub took an `ok` "
        "argument that was only ever passed `true`, a control that could not go false, in the "
        "suite whose subject is claims that outrun their measurement.",
        "      delivered = r.ok;",
        "      delivered = true;  // MUTATION: the delivery outcome is no longer measured",
    ),
    (
        "6-unreachable-telegram-reads-as-delivered",
        "THE SAME VALUE, ONE BRANCH OVER. Telegram REFUSING a message and Telegram being "
        "unreachable are two outcomes, and the repair for mutation 5 covered only the first: no "
        "scenario made the notice fetch throw, so the `catch` beside it was dead code in every "
        "run. Green until Fable applied it, and the state it produces is the worst the sweep can "
        "carry - every submission recorded as announced, in the field the whole habit keys on.",
        NOTICE_CATCH,
        "    } catch {\n      delivered = true;  // MUTATION: an unreachable notice reads as sent\n    }",
    ),
    (
        "7-write-back-stores-a-constant",
        "THE ONE WRITE WHOSE PURPOSE IS CARRYING THE OUTCOME INTO THE STORE, carrying a constant. "
        "Every notice scenario refused the write-back and the only successful write-back sent no "
        "notice, so this line was never watched storing a measured `true`. Green until Fable "
        "combined the two: it flags every notified applicant as unseen in the operator's sweep.",
        "    await env.INTAKE.put(key, JSON.stringify({ ...record, delivered }));",
        "    await env.INTAKE.put(key, JSON.stringify({ ...record, delivered: false }));"
        "  // MUTATION: constant",
    ),
    (
        "8-refusal-reason-is-a-constant",
        "THE SENTINEL'S ACCOUNT OF WHY, replaced by a plausible sentence. The operations note tells "
        "the operator that a documented same-key 429 is a known cost and anything else is a "
        "finding; under this mutation every 429 reads as the finding. Green until Fable applied "
        "it, because the reason was asserted for truthiness and pinned only in the scenario whose "
        "real value the constant happens to match.",
        "          reason: String((refusal && refusal.message) || refusal),",
        '          reason: "KV unavailable",  // MUTATION: not what the store said',
    ),
    (
        "9-sentinel-under-one-shared-key",
        "THE SENTINEL ROUTING BACK INTO THE LIMIT IT EXISTS TO AVOID. One constant key means "
        "concurrent refusals overwrite each other's marks and a second refusal inside a second is "
        "refused by the same-key rule itself. Green until Fable applied it: the gate compared the "
        "sentinel's `of` field to the record's key and never the key it was stored under.",
        "        `writeback-refused:${received_at}:${id}`,",
        '        "writeback-refused:always-the-same-key",  // MUTATION: one key for all refusals',
    ),
]

HEADER = """# RED-017 - the intake telling an applicant that nothing was saved, about a record that was saved
#
# Produced by evidence/RED-017-generator.py, checked in beside this file so the runs below can be
# repeated rather than believed. It establishes that the gate landing with T-A2-2 CAN fail
# (invariant 5) in each of the directions it holds. Each mutation is applied to
# web/functions/api/apply.js from a pristine copy, grepped back out to prove it landed, run with
# its output captured separately, and the endpoint restored and compared byte for byte before the
# next one - because a single redirected stream is how RED-013 came to carry one mutation's output
# under another's heading (L-26).
#
# FIVE OF THESE NINE WERE GREEN WHEN THEY WERE FIRST APPLIED. That is the honest summary of this
# file: the gate was written, believed, and then refuted and repaired over three rounds, and 5 to 9 are
# the false greens Fable produced against it - a delivery outcome frozen to a constant, an
# unreachable Telegram reading as a delivered notice, a write-back storing a constant, a refusal
# reason that is not what the store said, and every sentinel sharing one key. Each is a value the
# operator's sweep acts on, and each passed a suite that already RAN the endpoint. A gate that runs
# the code is still a gate about the shapes it runs.
#
# WHAT THE GENERATOR REFUSES TO WRITE THIS FILE OVER, each of which caught a real draft:
#
#   * a mutation that does not go red, or whose marker does not appear in the file afterwards;
#   * a pytest that did not RUN - only exit 1 is a suite that ran and failed, and reading any
#     nonzero exit as "red" was invariant 1 inside the instrument;
#   * a mutation that kills the suite's INSTRUMENT CONTROL. Mutation 3 was first written as an
#     `if (false) {` facing a `catch`: the module stopped parsing, every scenario died, and eight
#     tests went red under a heading claiming the sentinel had been removed. A red produced by a
#     file that does not parse says nothing about any property;
#   * two mutations with the same failure set - the transposition RED-013 was corrected for;
#   * an endpoint that is not restored byte for byte, or that is not green afterwards.
#
# The diff blocks are printed from the strings that perform the edits. Written by hand, one of them
# was already wrong: it showed a mutated line without the `// MUTATION` marker the grep under it
# proved was there. Nothing was invented and the run was real, and the prose still described an
# edit other than the one performed, which is L-26's second half inside the artefact kept to defend
# against L-26. Found by Fable.
#
# The gate is tests/test_intake_survives_a_failed_writeback.py, and it RUNS the endpoint under Node
# with a stubbed KV binding (tests/intake_probe.mjs) rather than matching patterns against its
# source. That is the point of it: a source scan can see that a `try` is written and can never see
# what the handler answers.
#
# Everything below each `$` line is verbatim output of the command shown.
#
"""

BAR = "# " + "=" * 92


def pytest_run() -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "pytest", SUITE, "-q"],
                          cwd=ROOT, capture_output=True, text=True)


def main(argv: list[str]) -> int:
    pristine = SRC.read_text(encoding="utf-8")
    _title, _rest = HEADER.split("\n", 1)
    stamped_header = f"{_title}\n# {evidence_stamp.tree_stamp()}\n{_rest}"
    out, seen = [stamped_header], {}
    try:
        for n, (name, prose, old, new) in enumerate(MUTATIONS, start=1):
            if pristine.count(old) != 1:
                raise SystemExit(f"{name}: anchor found {pristine.count(old)} times in {SRC.name}")
            SRC.write_text(pristine.replace(old, new), encoding="utf-8")
            grep = subprocess.run(["grep", "-n", "MUTATION", str(SRC)],
                                  capture_output=True, text=True)
            run = pytest_run()
            SRC.write_text(pristine, encoding="utf-8")
            if SRC.read_text(encoding="utf-8") != pristine:
                raise SystemExit(f"{name}: the endpoint was NOT restored; stopping")

            if not grep.stdout.strip():
                raise SystemExit(f"{name}: no MUTATION marker in the file - the edit did not land, "
                                 "so the run below is a transcript of the pristine endpoint")
            if run.returncode == 0:
                raise SystemExit(f"{name} did NOT go red: the gate is unarmed against it")
            if run.returncode != 1:
                raise SystemExit(
                    f"{name}: pytest exited {run.returncode}, which is not a suite that ran and "
                    "failed. A red must be an assertion, never an instrument that did not run")
            if CONTROL in run.stdout:
                raise SystemExit(
                    f"{name} killed the instrument control ({CONTROL}): the endpoint stopped "
                    "running at all, so this red is about a broken file and not about a property")
            failed = tuple(sorted(ln for ln in run.stdout.splitlines() if ln.startswith("FAILED ")))
            if failed in seen:
                raise SystemExit(f"{name} and {seen[failed]} produce the SAME failure set")
            seen[failed] = name

            diff = "\n".join(f"# - {ln}" for ln in old.split("\n"))
            diff += "\n" + "\n".join(f"# + {ln}" for ln in new.split("\n"))
            out.append(
                f"{BAR}\n# RED {n}.\n# {prose}\n#\n{diff}\n#\n"
                "# $ grep -n 'MUTATION' web/functions/api/apply.js\n"
                + "".join(f"# {ln}\n" for ln in grep.stdout.splitlines())
                + f"#\n# $ python3 -m pytest {SUITE} -q\n" + run.stdout + run.stderr + "\n")
    finally:
        SRC.write_text(pristine, encoding="utf-8")

    green = pytest_run()
    if green.returncode != 0:
        raise SystemExit("the restored endpoint is not green; the reds above prove nothing")
    out.append(f"{BAR}\n# GREEN, on the restored endpoint, so the reds above are known to be the "
               "mutations' doing\n# and not a suite that fails on everything.\n#\n"
               f"# $ python3 -m pytest {SUITE} -q\n" + green.stdout + green.stderr)

    if "--check" in argv:
        print(f"{len(MUTATIONS)} mutations, all red, all distinct; nothing written")
        return 0
    # Written whole and moved into place: a redirection would truncate the artefact before any of
    # the refusals above could decline to replace it.
    tmp = ARTEFACT.with_suffix(".txt.new")
    tmp.write_text("".join(out), encoding="utf-8")
    tmp.replace(ARTEFACT)
    print(f"{ARTEFACT.relative_to(ROOT)}: {len(MUTATIONS)} mutations, all red, all distinct")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
