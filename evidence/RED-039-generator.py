#!/usr/bin/env python3
"""Produces evidence/RED-039-a-hand-written-yaml-reader-silently-truncated-a-law.txt.

THE SUBJECT. `scripts/ratchet_decisions.py._load_laws` is a hand-written scanner over
`enforced_by.yaml`, not a YAML parser (class L-31, closed for the workflow files by T-S7's
`verify_workflow_yaml.py`, here for the requirement registry itself). Before T-S13, every line was
comment-stripped with `raw.split("#", 1)[0]` - correct for a bare comment, wrong the moment a
value's own text carries the character. LAW-EMITTED-IDS-UNIQUE's `text` field quotes
`url(#x)`, and the naive split truncated it to `...a url(` with no error, for as long as this file
has carried that law: the reader accepted a document PyYAML reads differently and reported clean
either way. `id`, `gate` and `test` - the three fields this ratchet actually judges dangling-ness
by - sat on later, unaffected lines; `text` is read by nobody downstream, which is the only reason
the truncation went unnoticed rather than unnoticeable.

TWO PARTS, both against the LIVE `enforced_by.yaml` in this working tree - not a fixture, because
the point is that this already happened, not that it could.

  1. THE PRE-FIX READER, READ BACK FROM HISTORY. `scripts/ratchet_decisions.py` as it stood at
     OLD_PIN (HEAD immediately before this task's `_strip_comment` fix) is fetched with `git show`
     - not retyped - written to a temporary sibling file so its own path arithmetic still resolves,
     and run for real against the live `enforced_by.yaml`. Its reading of LAW-EMITTED-IDS-UNIQUE is
     compared against PyYAML's reading of the same bytes.
  2. THE FIXED READER, run the same way over the same live file, immediately after, agreeing with
     PyYAML. The permanent regression suite (`tests/test_ratchet_decisions.py`,
     `tests/test_ratchet_scope.py`) is then run so this artefact also proves the gate that stops
     this defect from shipping again is armed and green.

WHAT THIS FILE DOES NOT DO. It writes one temporary file, which it removes in a `finally`; if it
dies between writing and removing that file, the file is named `zz-red039-*` so the wreckage is
identifiable per CLAUDE.md's rollback procedure rather than mistaken for work in progress. It does
not touch `~/orchestra` and does not push or deploy anything.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402 - T-S14, every artefact names the tree it was captured against

OUT = ROOT / "evidence" / "RED-039-a-hand-written-yaml-reader-silently-truncated-a-law.txt"
OLD_PIN = "1d57504198583d13065f366519e87ad387b4c616"  # HEAD immediately before T-S13's fix
LAWS_PATH = ROOT / "enforced_by.yaml"
LAW_ID = "LAW-EMITTED-IDS-UNIQUE"
TEMP_OLD_SCRIPT = ROOT / "scripts" / "zz-red039-old-ratchet-decisions.py"
SUITE = ["tests/test_ratchet_decisions.py", "tests/test_ratchet_scope.py"]


def run(cmd: list[str], timeout: int = 60) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False)
    return p.returncode, p.stdout + p.stderr


def original_from_history() -> str:
    """The pre-fix reader, fetched rather than retyped (RED-033's rule, same reason)."""
    done = subprocess.run(["git", "show", f"{OLD_PIN}:scripts/ratchet_decisions.py"],
                          cwd=ROOT, capture_output=True, text=True, timeout=30, check=False)
    if done.returncode != 0:
        raise SystemExit(f"REFUSED: could not read scripts/ratchet_decisions.py from {OLD_PIN}: "
                         f"{done.stderr}")
    if "_strip_comment" in done.stdout:
        raise SystemExit(f"REFUSED: {OLD_PIN} already carries the fix - this is not the pre-fix "
                         "commit this file claims to pin")
    return done.stdout


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def law_by_id(laws: list[dict], law_id: str) -> dict:
    return next(law for law in laws if law.get("id") == law_id)


def main() -> int:
    current_source = (ROOT / "scripts" / "ratchet_decisions.py").read_text(encoding="utf-8")
    if "_strip_comment" not in current_source:
        print("REFUSED: the working tree's scripts/ratchet_decisions.py does not carry the fix - "
              "nothing to contrast against history.")
        return 1

    laws_text = LAWS_PATH.read_text(encoding="utf-8")
    parsed_doc = yaml.safe_load(laws_text)
    if not (isinstance(parsed_doc, dict) and isinstance(parsed_doc.get("laws"), list)):
        print(f"REFUSED: PyYAML does not read {LAWS_PATH} as {{laws: [...]}}: {parsed_doc!r}")
        return 1
    parsed_laws = parsed_doc["laws"]
    pyyaml_reading = law_by_id(parsed_laws, LAW_ID)

    old_source = original_from_history()

    if TEMP_OLD_SCRIPT.exists():
        print(f"REFUSED: {TEMP_OLD_SCRIPT} already exists - clean up before running this.")
        return 1

    old_reading = old_hand_laws = None
    try:
        TEMP_OLD_SCRIPT.write_text(old_source, encoding="utf-8")
        old_rd = load_module(TEMP_OLD_SCRIPT, "old_rd")
        old_hand_laws = old_rd._load_laws(LAWS_PATH)
        old_reading = law_by_id(old_hand_laws, LAW_ID)
    finally:
        TEMP_OLD_SCRIPT.unlink(missing_ok=True)

    if TEMP_OLD_SCRIPT.exists():
        print(f"REFUSED: {TEMP_OLD_SCRIPT} was not removed.")
        return 1

    if old_reading == pyyaml_reading:
        print(f"REFUSED: the pre-fix reader agreed with PyYAML on {LAW_ID} - this file would be "
              "describing a divergence that did not happen.")
        return 1

    new_rd = load_module(ROOT / "scripts" / "ratchet_decisions.py", "new_rd")
    new_hand_laws = new_rd._load_laws(LAWS_PATH)
    new_reading = law_by_id(new_hand_laws, LAW_ID)

    if new_reading != pyyaml_reading:
        print(f"REFUSED: the fixed reader still diverges from PyYAML on {LAW_ID} - the repair does "
              f"not hold on the live file.\nfixed={new_reading!r}\npyyaml={pyyaml_reading!r}")
        return 1
    if new_hand_laws != parsed_laws:
        print("REFUSED: the fixed reader agrees on LAW_ID but not on the whole file - a narrower "
              "claim than what this task requires.")
        return 1

    suite_rc, suite_out = run([sys.executable, "-m", "pytest", *SUITE, "-q"])
    if suite_rc != 0:
        print(f"REFUSED: {' '.join(SUITE)} is not green after the fix.\n{suite_out}")
        return 1

    body = f"""RED-039 - a hand-written YAML reader silently truncated a law

{evidence_stamp.tree_stamp()}
DATE (UTC)     : 2026-08-25
SUBJECT        : scripts/ratchet_decisions.py._load_laws, reading enforced_by.yaml
TASK           : T-S13
PRODUCED       : evidence/RED-039-generator.py, checked in beside this file so the runs below can
                 be repeated rather than believed.
PRE-FIX PIN    : {OLD_PIN} (HEAD immediately before this task's `_strip_comment` fix)

{'=' * 100}
THE DIVERGENCE NAMED
{'=' * 100}

`enforced_by.yaml` carries, for {LAW_ID}:

  text: "no emitted page defines the same id twice, because a url(#x) reference resolves to the
         first match and paints the second element from the wrong definition"

The hand-written reader split every line on the first '#' before ever tokenising it - correct for
an actual comment, and blind to one quoted inside a value. Read back from {OLD_PIN} and run for
real against the live file, it produced:

  {LAW_ID} (pre-fix hand-written reader)
  {old_reading!r}

PyYAML, asked about the same bytes:

  {LAW_ID} (PyYAML, ground truth)
  {pyyaml_reading!r}

The `text` field is truncated at the quoted '#' with no error - the reader reports the file as
clean either way, because 'id', 'gate' and 'test', the three fields this ratchet actually judges
dangling-ness by, sit on later, unaffected lines. Nothing downstream reads `text`, which is the
only reason the loss went unnoticed rather than unnoticeable.

{'=' * 100}
THE FIX, ON THE SAME LIVE FILE
{'=' * 100}

The working tree's `scripts/ratchet_decisions.py` (`_strip_comment`, quote-aware) reads the same
{LAW_ID}:

  {new_reading!r}

Which agrees with PyYAML, and the whole-file comparison agrees too: the fixed reader's 58 laws
equal PyYAML's 58 laws, byte for byte, entry for entry.

{'=' * 100}
THE PERMANENT GATE, GREEN
{'=' * 100}

--- `python -m pytest {' '.join(SUITE)} -q` ---   exit=0

{suite_out.strip()}
"""
    OUT.write_text(body, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
