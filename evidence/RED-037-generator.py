#!/usr/bin/env python3
"""Produces evidence/RED-037-an-unread-subject-scored-anyway.txt.

THE SUBJECT. `scripts/measure_qm2.py`'s scoring branch (the line this repairs) tested whether
`ev.distinct_authors` happened to be measured, not whether `ev.read` was true. Those are different
questions with the same answer whenever a subject the collector never reached leaves every field
unmeasured - which it always does. `whiteknightonhorse/gov-auction-report` answers 404 to an
anonymous reader (measured live below, not assumed), and the old branch scored it `level: L2`
(after the weak-signal cap), `measured: true`, `projection: 40` regardless - a level and a number
for a subject nothing was read from.

WHY THE NUMBER IS A SILENT SHIFT, NOT JUST A WRONG ONE. `evidence/TAINTED-SUDO-CORPUS/
git_whiteknightonhorse_gov-auction-report.json` is the passport this same subject carried before
2026-08-20, when the pipeline read it as `sole_author -> L4 -> projection: 80` through the
now-forbidden sudo channel (Fable, V1). The anonymous channel that replaced it cannot see this
repository at all - it 404s - and the honest reading of that is `unreadable`, not a smaller number.
The old branch produced a smaller number anyway: 80 (privileged, real) silently became 40
(anonymous, fabricated), on the same subject, with nothing in either artefact saying the second
reading came from a source that never answered.

TWO PARTS, both against the REAL live API - no stub stands in for whether GitHub answers this
subject, because that is exactly the fact in dispute.

  1. THE OLD SCRIPT, READ BACK FROM HISTORY. `scripts/measure_qm2.py` as it stood at commit
     eb0c6cb8 (HEAD immediately before the T-S8 repair) is fetched with `git show` - not retyped -
     written to a temporary sibling file so its own `sys.path` arithmetic still resolves, and run
     for real. Its own state directory (`.state/qm2/`) is inspected afterwards for exactly the
     defect this file exists to document.
  2. THE FIXED SCRIPT, RUN THE SAME WAY, over the same live subject, immediately after. The
     permanent regression suite (`tests/test_qm2_unreadable_subject.py`) is then run so this
     artefact also proves the CI gate that stops this defect from shipping again is armed and
     green.

WHAT THIS FILE DOES NOT DO. It does not touch `~/orchestra`, does not deploy anything, and writes
one temporary file which it removes in a `finally`; if it dies between writing and removing that
file, the file is named `zz-red037-*` so the wreckage is identifiable per CLAUDE.md's rollback
procedure rather than mistaken for work in progress.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "RED-037-an-unread-subject-scored-anyway.txt"
OLD_PIN = "eb0c6cb8a0cec4e17179fbcbb09f15c320a720a3"   # HEAD immediately before the T-S8 repair
SUBJECT = "whiteknightonhorse/gov-auction-report"
SLUG = "git_whiteknightonhorse_gov-auction-report.json"
STATE = ROOT / ".state" / "qm2" / SLUG
TAINTED = ROOT / "evidence" / "TAINTED-SUDO-CORPUS" / SLUG
TEMP_OLD_SCRIPT = ROOT / "scripts" / "zz-red037-old-measure-qm2.py"
SUITE = "tests/test_qm2_unreadable_subject.py"


def run(cmd: list[str], timeout: int = 120) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False)
    return p.returncode, p.stdout + p.stderr


def read_dev_op(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    ops = doc["passport"]["verified"]["operations"]
    dev = next(o for o in ops if o["operation"] == "development_initiation")
    return {"projection": doc["projection"], "development_initiation": dev}


def live_status(full_name: str) -> int:
    rc, out = run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                  f"https://api.github.com/repos/{full_name}"], timeout=30)
    if rc != 0:
        raise SystemExit(f"REFUSED: curl toward {full_name} exited {rc} - not a 200/404 we can read")
    return int(out.strip())


def original_from_history() -> str:
    """The pre-repair script, fetched rather than retyped (RED-033's rule, same reason)."""
    done = subprocess.run(["git", "show", f"{OLD_PIN}:scripts/measure_qm2.py"],
                          cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
    if done.returncode != 0:
        raise SystemExit(f"REFUSED: could not read scripts/measure_qm2.py from {OLD_PIN}: "
                         f"{done.stderr}")
    if "if not ev.read" in done.stdout:
        raise SystemExit(f"REFUSED: {OLD_PIN} already carries the fix - this is not the pre-repair "
                         "commit this file claims to pin")
    return done.stdout


def main() -> int:
    live_code = live_status(SUBJECT)
    if live_code != 404:
        print(f"REFUSED: {SUBJECT} answers {live_code} live, not 404 - this fixture needs a "
              "subject the anonymous API currently refuses, and this one no longer is it.")
        return 1

    current_source = (ROOT / "scripts" / "measure_qm2.py").read_text(encoding="utf-8")
    if "if not ev.read" not in current_source:
        print("REFUSED: the working tree's scripts/measure_qm2.py does not carry the fix - "
              "nothing to contrast against history.")
        return 1

    old_source = original_from_history()

    if TEMP_OLD_SCRIPT.exists():
        print(f"REFUSED: {TEMP_OLD_SCRIPT} already exists - clean up before running this.")
        return 1

    old_result = new_result = None
    try:
        TEMP_OLD_SCRIPT.write_text(old_source, encoding="utf-8")

        old_rc, old_out = run([sys.executable, str(TEMP_OLD_SCRIPT)])
        if old_rc != 0:
            print(f"REFUSED: the pre-repair script exited {old_rc}.\n{old_out}")
            return 1
        old_result = read_dev_op(STATE)

        new_rc, new_out = run([sys.executable, str(ROOT / "scripts" / "measure_qm2.py")])
        if new_rc != 0:
            print(f"REFUSED: the fixed script exited {new_rc}.\n{new_out}")
            return 1
        new_result = read_dev_op(STATE)
    finally:
        TEMP_OLD_SCRIPT.unlink(missing_ok=True)

    if TEMP_OLD_SCRIPT.exists():
        print(f"REFUSED: {TEMP_OLD_SCRIPT} was not removed.")
        return 1

    old_dev = old_result["development_initiation"]
    if not (old_dev["measured"] is True and old_result["projection"] == 40):
        print(f"REFUSED: the pre-repair script did not reproduce the defect this file documents "
              f"(got {old_result}); the artefact would be describing a run that did not happen.")
        return 1

    new_dev = new_result["development_initiation"]
    if not (new_dev["measured"] is False and new_dev["level"] == "unreadable"
            and new_result["projection"] is None):
        print(f"REFUSED: the fixed script did not refuse (got {new_result}) - the repair does not "
              "hold on the live subject.")
        return 1

    suite_rc, suite_out = run([sys.executable, "-m", "pytest", SUITE, "-q"])
    if suite_rc != 0:
        print(f"REFUSED: {SUITE} is not green after the repair.\n{suite_out}")
        return 1

    tainted = json.loads(TAINTED.read_text(encoding="utf-8")) if TAINTED.exists() else None
    tainted_line = (
        f"evidence/TAINTED-SUDO-CORPUS/{SLUG} (issued {tainted['passport']['issued_at']}, "
        f"pre-2026-08-20 sudo channel): level={tainted['passport']['verified']['operations'][0]['level']}"
        f" projection={tainted['projection']}"
    ) if tainted else "evidence/TAINTED-SUDO-CORPUS/... not present in this checkout"

    body = f"""RED-037 - an unread subject scored anyway

DATE (UTC)     : 2026-08-24
SUBJECT        : scripts/measure_qm2.py, development_initiation scoring for {SUBJECT}
TASK           : T-S8
PRODUCED       : evidence/RED-037-generator.py, checked in beside this file so the runs below
                 can be repeated rather than believed.
LIVE CHECK     : GET https://api.github.com/repos/{SUBJECT} -> HTTP {live_code} (measured just now,
                 not assumed - this file refuses to write itself if the subject stops 404ing)

{'=' * 100}
THE SILENT SHIFT NAMED
{'=' * 100}

Before the anonymous channel (Fable, V1, 2026-08-20), this exact subject was read through a
now-forbidden sudo channel and scored genuinely - sole author, verified commits, and a runtime
trace justified L4:

  {tainted_line}

After 2026-08-20 the anonymous channel cannot see this repository at all: it answers 404, measured
above. The honest consequence is `unreadable` - the repository the anonymous method used to read
under privilege has become one it cannot reach at all through the reproducible channel. The
pre-repair code did not say that. It silently produced a SMALLER but still-affirmative number:

  before repair (this run)  : development_initiation = {json.dumps(old_dev)}
                              projection = {old_result['projection']}
  after repair  (this run)  : development_initiation = {json.dumps(new_dev)}
                              projection = {new_result['projection']}

80 -> 40 is not two measurements of the same thing getting more precise. It is a privileged real
reading (80) followed by an anonymous fabricated one (40) that never disclosed it was reading
nothing, on a subject a reproducible reader cannot see at all.

{'=' * 100}
PART ONE - the pre-repair script (git show {OLD_PIN}), run for real
{'=' * 100}

--- `python3 scripts/measure_qm2.py` at {OLD_PIN} ---   exit=0

{old_out.strip()}

--- .state/qm2/{SLUG} after that run ---

{json.dumps(old_result, indent=2)}

{'=' * 100}
PART TWO - the fixed script, run the same way over the same live subject
{'=' * 100}

--- `python3 scripts/measure_qm2.py` (working tree) ---   exit=0

{new_out.strip()}

--- .state/qm2/{SLUG} after that run ---

{json.dumps(new_result, indent=2)}

{'=' * 100}
THE PERMANENT GATE, GREEN
{'=' * 100}

--- `python -m pytest {SUITE} -q` ---   exit=0

{suite_out.strip()}
"""
    OUT.write_text(body, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
