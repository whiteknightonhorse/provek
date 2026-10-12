#!/usr/bin/env python3
"""Produces evidence/RED-064-the-witness-relay-gates-are-able-to-fail.txt.

T-PW-02-witness-relay-submit: `tests/test_witness_relay.py` (and the tracker pins in
`tests/test_witness_page.py`) claim to guard the operator-signed relay. Each plant below breaks one
claim in the REAL tree (never a tmp copy) and the named test must go red, then green again once the
plant is reverted:

  PLANT 1  witnessRelay.js: the per-client limit becomes `>` (a fourth request in the hour passes).
  PLANT 2  witnessRelay.js: the upstream error is returned without `sanitise` (key material can leak).
  PLANT 3  witnessRelay.js: the URL rule "no userinfo" is dropped (relay and contract disagree).
  PLANT 4  witnessRelay.js: the disabled check is skipped (a missing secret reaches createAccount).
  PLANT 5  witnessRelay.js: the key is appended to the upstream-failure log line.
  PLANT 6  witnessView.js: UNINITIALIZED is never "not indexed yet" (the tracker calls a fresh hash
           nonexistent - the A1.1 defect).

Each file is restored byte-for-byte before the next plant, and the restore is verified.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / "RED-064-the-witness-relay-gates-are-able-to-fail.txt"
HELPER = ROOT / "web" / "src" / "witnessView.js"
RELAY = ROOT / "web" / "functions" / "_lib" / "witnessRelay.js"
T = "tests/"


def run_test(node: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, "-m", "pytest", T + node, "-q", "-p", "no:cacheprovider"],
                       cwd=ROOT, capture_output=True, text=True, timeout=180, check=False)
    # The tests use a FAKE key; its shape is still 64 hex, which scripts/secret_scan.sh blocks by
    # pattern, so no 64-hex run (key or hash) is copied into the artefact.
    return p.returncode, re.sub(r"(0[xX])?[0-9a-fA-F]{64}", "<64-hex>", (p.stdout + p.stderr).strip())


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
    ("PLANT 1 - witnessRelay.js: the per-client limit uses `>` so a fourth request in the hour passes.",
     RELAY, "if (ipN >= LIMITS.per_ip_per_hour)", "if (ipN > LIMITS.per_ip_per_hour)",
     "test_witness_relay.py::test_the_fourth_request_from_one_client_in_an_hour_is_429_with_retry_after"),
    ("PLANT 2 - witnessRelay.js: the upstream error is returned without `sanitise`.",
     RELAY, "const message = sanitise(e, cfg.key);", "const message = String(e && e.message);",
     "test_witness_relay.py::test_an_upstream_failure_is_502_with_the_message_and_without_key_material"),
    ("PLANT 3 - witnessRelay.js: the `no userinfo` URL rule is dropped.",
     RELAY, 'if (netloc.includes("@")) return "evidence_url must not carry userinfo";', "",
     "test_witness_relay.py::test_every_url_rule_gives_the_contracts_own_answer_on_the_same_cases"),
    ("PLANT 4 - witnessRelay.js: the disabled check is skipped, so a missing secret reaches the signer.",
     RELAY, "if (!cfg.enabled) {\n    return json({ ok: false, error: `Submissions", "if (false) {\n    return json({ ok: false, error: `Submissions",
     "test_witness_relay.py::test_without_the_secret_health_says_disabled_and_post_is_503_and_nothing_is_derived"),
    ("PLANT 5 - witnessRelay.js: the key is appended to the upstream-failure log line.",
     RELAY, "console.error(`witness-submit upstream failure: ${message}`);",
     "console.error(`witness-submit upstream failure: ${message} ${cfg.key}`);",
     "test_witness_relay.py::test_the_source_never_writes_the_key_to_a_log_or_a_response"),
    ("PLANT 6 - witnessView.js: UNINITIALIZED is never 'not indexed yet', so a fresh hash is called nonexistent.",
     HELPER, 'notFound = waitedMs < NOT_INDEXED_GRACE_MS ? "not_indexed_yet" : "absent";', 'notFound = "absent";',
     "test_witness_page.py::test_a_just_submitted_hash_is_not_called_nonexistent_while_bradbury_has_not_indexed_it"),
]


def main() -> int:
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
    body = f"""# RED-064 - the witness relay gates are able to fail
#
# {evidence_stamp.tree_stamp()}
#
# Produced by evidence/RED-064-generator.py, checked in beside this file so every run below can be
# repeated rather than believed. Six plants against the real tree, each reverted and verified
# byte-identical before the next.

""" + "\n".join(parts)
    OUT.write_text(body, encoding="utf-8")
    sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
