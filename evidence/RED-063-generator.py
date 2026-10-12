#!/usr/bin/env python3
"""Produces evidence/RED-063-the-witness-page-gates-are-able-to-fail.txt.

T-PW-01-witness-page-read-path: `tests/test_witness_page.py` proves three things about
`/witness/`. Each plant below breaks exactly one of them in the REAL tree (never a tmp copy) and the
named test must go red, then green again once the plant is reverted:

  PLANT 1 (helper)   web/src/witnessView.js: `succeeded` stops requiring FINISHED_WITH_RETURN, i.e.
                     consensus status alone is taken for execution success - the confusion the
                     order names ("Accepted/Finalized != execution success").
  PLANT 2 (artefact) web/dist/witness/index.html: the contract address is removed from the
                     emitted page.
  PLANT 3 (artefact) web/dist/witness/index.html: a real witness id from deployment.json is written
                     into the static html - a record the reader's browser never read.

Each file is restored byte-for-byte before the next plant, and the restore is verified.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / "RED-063-the-witness-page-gates-are-able-to-fail.txt"
HELPER = ROOT / "web" / "src" / "witnessView.js"
PAGE = ROOT / "web" / "dist" / "witness" / "index.html"
DEPLOY = json.loads((ROOT / "integrations" / "genlayer-witness" / "deploy" / "deployment.json").read_text())
T = "tests/test_witness_page.py::"


def run_test(node: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, "-m", "pytest", T + node, "-q", "-p", "no:cacheprovider"],
                       cwd=ROOT, capture_output=True, text=True, timeout=180, check=False)
    return p.returncode, (p.stdout + p.stderr).strip()


def plant(path: Path, old: str, new: str, node: str):
    original = path.read_bytes()
    text = original.decode("utf-8")
    if old not in text:
        raise RuntimeError(f"REFUSED: {old!r} is not present in {path} - nothing to plant.")
    rc_before, out_before = run_test(node)
    if rc_before != 0:
        raise RuntimeError(f"REFUSED: {node} is not green before the plant.\n{out_before}")
    try:
        path.write_bytes(text.replace(old, new).encode("utf-8"))
        rc_red, out_red = run_test(node)
    finally:
        path.write_bytes(original)
    if path.read_bytes() != original:
        raise RuntimeError(f"REFUSED: {path} was not restored.")
    if rc_red == 0:
        raise RuntimeError(f"REFUSED: the plant did not turn {node} red.\n{out_red}")
    rc_after, out_after = run_test(node)
    if rc_after != 0:
        raise RuntimeError(f"REFUSED: {node} is not green after the revert.\n{out_after}")
    return rc_before, out_before, rc_red, out_red, rc_after, out_after


PLANTS = [
    ("PLANT 1 - web/src/witnessView.js: `succeeded` ignores the execution result "
     "(consensus status alone counts as success).",
     HELPER, 'const succeeded = settled && exec === "FINISHED_WITH_RETURN";', "const succeeded = settled;",
     "test_accepted_with_a_failed_execution_is_not_success"),
    ("PLANT 2 - web/dist/witness/index.html: the contract address is removed from the emitted page.",
     PAGE, DEPLOY["contract_address"], "", "test_the_emitted_page_names_the_contract_network_and_explorer"),
    ("PLANT 3 - web/dist/witness/index.html: a real witness id is written into the static html.",
     PAGE, "</main>", f"<p>{DEPLOY['live_records'][0]['witness_id']}</p></main>",
     "test_the_emitted_page_carries_no_record_value"),
]


def main() -> int:
    if not PAGE.is_file():
        print(f"REFUSED: {PAGE} is absent - run `npm run build` in web/ first.")
        return 1
    parts = []
    for title, path, old, new, node in PLANTS:
        try:
            b, bo, r, ro, a, ao = plant(path, old, new, node)
        except RuntimeError as e:
            print(str(e))
            return 1
        parts.append(f"""{"=" * 100}
{title}
SUBJECT: {T}{node}
{"=" * 100}

--- before the plant, exit {b} ---
{bo}

--- with the plant in place, exit {r} ---
{ro}

--- plant reverted, exit {a} ---
{ao}
""")
    body = f"""# RED-063 - the /witness/ page gates are able to fail
#
# {evidence_stamp.tree_stamp()}
#
# Produced by evidence/RED-063-generator.py, checked in beside this file so every run below can be
# repeated rather than believed. Three plants against the real tree, each reverted and verified
# byte-identical before the next.

""" + "\n".join(parts)
    OUT.write_text(body, encoding="utf-8")
    sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
