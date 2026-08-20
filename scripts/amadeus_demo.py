#!/usr/bin/env python3
"""T-2.16 - run the Amadeus auditor demo and write down what it showed (ABI-31-4, ABI-5-3).

WHAT THIS IS. The one command behind the demo: it runs the Provek Auditor agent that lives on the
Amadeus Protocol SDK (`demo/amadeus/auditor.mjs`), classifies what the agent gathered with
`src/amadeus/demo_audit.py`, and leaves both the raw artefact and a readable summary under
`evidence/`. The agent gathers, this script decides, and the decision is taken from recorded
quantities by code (invariant 2).

WHY THE RUN IS HERE AND NOT IN THE TEST SUITE. It reaches the network, and a networked test has
two failure modes that look identical - the subject changed, or this host has no route out - whose
usual repair is a `skipif` that turns the test into decoration (L-16). So the suite exercises
`judge()` through injected artefacts and never skips, and the live run is taken here, deliberately,
where a run that found something is an artefact rather than a build status. Same division as
`scripts/probe_self.py`.

WHAT IT COSTS THE SUBJECT: three GET requests to a public RPC that needs no credential, which is
also what makes the demo reproducible by a third party (ABI-5-3) - anyone can repeat it, including
Amadeus. Nothing is written to the chain; see the sentinel the agent records for why.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.amadeus.demo_audit import DemoVerdict, judge  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo" / "amadeus"
AGENT = DEMO / "auditor.mjs"
DEFAULT_STEM = ROOT / "evidence" / "AMADEUS-DEMO-001"
NODE_TIMEOUT_S = 180


def _shown(path: Path) -> str:
    """A path as a reader should see it: repo-relative when it is inside the repo, absolute when
    it is not.

    THE BARE `relative_to` THIS REPLACES CRASHED ON EVERY RELATIVE `--out`, which is the form the
    README documents. The files were written, then the process died with a traceback and exit 1 -
    the SAME code as `not_demonstrated`. So "the demo ran and showed nothing" and "the runner
    threw" were one number, in the script whose entire subject is keeping those apart. Found by
    running the documented command instead of the convenient one.
    """
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def _install(where: Path) -> int:
    """Install the pinned SDK. `npm ci` when there is a lockfile, because the demo's claim to be
    reproducible is a claim about the exact dependency tree, not about whatever resolves today."""
    cmd = ["npm", "ci"] if (where / "package-lock.json").exists() else ["npm", "install"]
    print(f"$ {' '.join(cmd)}  (in {_shown(where)})")
    return subprocess.run(cmd, cwd=where, check=False).returncode


def run_agent(install: bool) -> tuple[dict | None, str]:
    """Run the agent and return its artefact, or `(None, why not)`.

    A MISSING INSTRUMENT IS A RED, NEVER A SKIP. If node or the SDK is absent this returns a
    reason and the caller exits non-zero; it does not quietly report a demo that showed nothing,
    because "we could not run it" and "it ran and showed nothing" are the two states this whole
    repository exists to keep apart.
    """
    if shutil.which("node") is None:
        return None, "node is not on PATH, so the agent could not be started"
    if not AGENT.exists():
        return None, f"{_shown(AGENT)} is missing"
    if install and _install(DEMO) != 0:
        return None, "the SDK could not be installed, so the agent could not be started"
    if not (DEMO / "node_modules" / "@amadeus-protocol" / "sdk").exists():
        return None, ("@amadeus-protocol/sdk is not installed - re-run with --install, or "
                      "`npm ci` in demo/amadeus")
    try:
        done = subprocess.run(["node", str(AGENT)], cwd=DEMO, capture_output=True,
                              text=True, timeout=NODE_TIMEOUT_S, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"the agent could not be run: {type(exc).__name__}: {exc}"
    if done.returncode != 0:
        return None, f"the agent exited {done.returncode}: {done.stderr.strip()[:400]}"
    try:
        return json.loads(done.stdout), ""
    except ValueError as exc:
        return None, f"the agent's output was not JSON ({exc}); first bytes: {done.stdout[:200]!r}"


def summary(artefact: dict, judgement, taken_at: datetime) -> str:
    """The readable half of the artefact. Written for a person - Amadeus is meant to be able to
    read this without running anything - so every absence appears as a sentence, not a blank."""
    sdk = artefact.get("sdk", {})
    net = artefact.get("network", {})
    payload = artefact.get("payload", {})
    write = artefact.get("onchain_write", {})
    lines = [
        "T-2.16 - PROVEK AUDITOR AGENT ON THE AMADEUS PROTOCOL SDK",
        f"taken at        : {taken_at.isoformat()}",
        f"verdict         : {judgement.verdict.value.upper()}",
        f"sdk             : {sdk.get('package')}@{sdk.get('pinned_version')} "
        f"(reports {sdk.get('reported_version')})",
        f"network         : {net.get('name')} via {net.get('rpc_url')}",
        "",
        "READINGS  (a 200 is not a measurement; the shape is checked, and a body that is not this",
        "           chain's shape is UNREADABLE rather than a zero)",
    ]
    for r in judgement.readings:
        value = r.value.value if r.value.is_measured else f"absent:{r.value.absent.value}"
        lines.append(f"  {r.endpoint:<16} {r.state.value:<19} {value}")
        lines.append(f"  {'':<16} {r.detail}")
    lines += [
        "",
        f"SDK FINDING     : {judgement.sdk_finding.value}",
        "",
        "SELF-AUDIT      (ABI-31-4 - the subject of this demo is Provek itself)",
        f"  subject       : {artefact.get('self_audit', {}).get('subject_id')}",
        f"  projection    : {artefact.get('self_audit', {}).get('projection')}  (passed through "
        "from the passport, NOT recomputed by the agent)",
        f"  passport      : {artefact.get('self_audit', {}).get('path')}",
        f"  sha256        : {artefact.get('self_audit', {}).get('sha256')}",
        "",
        "VALIDATION PAYLOAD  (serialised with the SDK's own codec, so the record is TRANSPORTABLE",
        "                     on Amadeus rails - nothing was sent; see the on-chain write below)",
        f"  built         : {payload.get('built')}",
        f"  bytes         : {payload.get('byte_length')}",
        f"  sha256        : {payload.get('sha256')}",
        f"  base58        : {str(payload.get('base58'))[:64]}...",
        "",
        f"ON-CHAIN WRITE  : {write.get('state')} (not attempted)",
    ]
    lines += [f"  blocker       : {b}" for b in write.get("blockers", [])]
    lines += ["", "FINDINGS"]
    lines += [f"  - {f}" for f in judgement.findings] or ["  (none)"]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--install", action="store_true",
                    help="install the pinned SDK first (needed on a fresh clone)")
    ap.add_argument("--out", type=Path, default=DEFAULT_STEM,
                    help="path stem for the .json and .txt artefacts")
    ap.add_argument("--overwrite", action="store_true",
                    help="replace an artefact that is already on disk")
    args = ap.parse_args()

    # EVIDENCE IS NOT REWRITTEN BY ACCIDENT. `ratchet_language.py` exempts `evidence/` on the
    # stated ground that "historical run output is never rewritten", and this script's default
    # stem sat inside it silently replacing the shipped artefact on every run. Two rules, one of
    # them enforced. Refusing costs a flag; the alternative is a record whose provenance quietly
    # becomes "whenever somebody last ran this". Found by Fable.
    existing = [p for p in (args.out.with_suffix(".json"), args.out.with_suffix(".txt"))
                if p.exists()]
    if existing and not args.overwrite:
        names = ", ".join(_shown(p) for p in existing)
        print(f"REFUSED: {names} already exists. Pass --overwrite to replace it, or --out to "
              f"write a new stem. Nothing was run.", file=sys.stderr)
        return 2

    artefact, why_not = run_agent(args.install)
    if artefact is None:
        print(f"NOT RUN: {why_not}", file=sys.stderr)
        print("Nothing was written: an artefact recording a demo that never ran would be a "
              "record of a run that did not happen.", file=sys.stderr)
        return 2

    taken_at = datetime.now(timezone.utc)
    judgement = judge(artefact)
    # ONE CLOCK. The agent mints no timestamp; the stamp is applied here, once, so the artefact
    # cannot carry two times that disagree about when the same run happened.
    artefact["taken_at"] = taken_at.isoformat()
    artefact["verdict"] = judgement.verdict.value
    artefact["sdk_finding"] = judgement.sdk_finding.value
    artefact["findings"] = list(judgement.findings)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.with_suffix(".json").write_text(json.dumps(artefact, indent=2) + "\n", encoding="utf-8")
    text = summary(artefact, judgement, taken_at)
    args.out.with_suffix(".txt").write_text(text, encoding="utf-8")

    print(text)
    print(f"written to {_shown(args.out.with_suffix('.json'))} and "
          f"{_shown(args.out.with_suffix('.txt'))}")
    if judgement.verdict is not DemoVerdict.DEMONSTRATED:
        print(f"\n{judgement.verdict.value.upper()}: see FINDINGS above.", file=sys.stderr)
    return judgement.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
