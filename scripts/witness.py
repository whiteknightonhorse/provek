#!/usr/bin/env python3
"""WitnessRecord v0 intake and publication (spec 4.2-bis point 4).

RUN BY THE OPERATOR (or their agent), ON A JOINT REQUEST FROM BOTH PARTIES - never on this
project's own initiative (A-9: active checks run only when someone with standing asked). This is
a CLI, not a public web form: the specification asks for a JOINT request, and a public POST
endpoint has no way to tell "both parties actually asked" from "one party typed two email
addresses". Fable's ruling on this exact question (design circle, 2026-09-02): the CLI IS the
accepted v0 realisation - a public form with fake authentication would be WORSE than the CLI, it
would launder A-9 rather than satisfy it. `--customer-contact`, `--subject-contact` and
`--joint-intent-evidence` are all REQUIRED - the third exists because Fable's ruling attached one
condition: the private record must also say HOW jointness was established (e.g. "customer email
of 2026-09-02, subject email of 2026-09-01"), so a future audit can distinguish a genuinely joint
request from an operator's own mistake.

WHAT GETS PUBLISHED, AND WHAT DOES NOT. `public/witness/<id>.json` and its mirror under
`web/public/data/witness/` carry ONLY the seven fields spec 4.2-bis point 4 names - see
`src.witness.witness.WitnessRecord.to_machine`. The two contacts and the joint-intent evidence
given on the command line go to a PRIVATE file - see `private_request_root`'s own docstring for
where, and for the defect this project shipped and then fixed before running a single real record.

AN UNSUPPORTED CRITERION WRITES NOTHING. `run_witness` raises before `publish_record` is ever
called - this script's exit code is the whole story on that path: nonzero and silent is correct,
not a bug to paper over.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.witness.witness import UnsupportedCriterion, WitnessRecord, run_witness  # noqa: E402


def private_request_root() -> Path:
    """Where the two contacts and the joint-intent evidence actually live - OUTSIDE the git tree
    entirely, never merely gitignored inside it.

    THE DEFECT THIS REPLACES (Fable's review, 2026-09-02). The first version of this script wrote
    those fields to `public/witness/_requests/<id>.json` - a path INSIDE `~/incubator`, the
    repository `push.sh` pushes to a PUBLIC GitHub remote. "Never mirrored to the served tree,
    never read by the site" was true and irrelevant: `push.sh`'s clean-tree gate means the first
    real WitnessRecord either blocks every subsequent push (an untracked file sitting in a
    directory the door treats as part of the tree) or gets committed and published to the public
    repository - the exact leak this module's own docstring promised did not happen. A `.gitignore`
    entry over that same path would still leave the data one `git add -f` or a careless glob away
    from the same outcome; living somewhere the repository's own tooling never walks is the
    stronger guarantee, not a stricter rule over the weaker location.

    `$HOME/.provek_witness_requests` by default - a sibling of `~/incubator`, never a descendant of
    it, so no rebase, no `git clean -fdx`, and no future contributor cloning this repository ever
    touches it. Overridable (tests point this at a `tmp_path`) but never defaulted to anywhere
    under `ROOT`.
    """
    return Path.home() / ".provek_witness_requests"


def publish_record(record: WitnessRecord, *, customer_contact: str, subject_contact: str,
                   joint_intent_evidence: str, public_root: Path,
                   private_root: Path | None = None) -> dict:
    """Write the published record under `public_root`, and the private request record under
    `private_root` (default: `private_request_root()`, OUTSIDE any git tree - see its docstring).

    Both roots are parameters - not module-level constants - so a test can point them at temporary
    directories and assert on real files without touching the live trees. Returns every path
    written, for the caller (or a test) to inspect.
    """
    private_root = private_root if private_root is not None else private_request_root()

    emitted = public_root / "public" / "witness"
    served = public_root / "web" / "public" / "data" / "witness"
    emitted_by_subject = emitted / "by_subject"
    private_requests = private_root  # the whole directory is private-only; no further nesting
    emitted.mkdir(parents=True, exist_ok=True)
    emitted_by_subject.mkdir(parents=True, exist_ok=True)
    served.mkdir(parents=True, exist_ok=True)
    private_requests.mkdir(parents=True, exist_ok=True)

    payload = json.dumps({"witness": record.to_machine()}, indent=2) + "\n"
    emitted_path = emitted / f"{record.witness_id}.json"
    served_path = served / f"{record.witness_id}.json"
    emitted_path.write_text(payload, encoding="utf-8")
    served_path.write_text(payload, encoding="utf-8")

    # Per-subject index, so `src.witness.witness.load_task_history` can find every record for a
    # subject without scanning the whole directory on every re-measure. This stays under
    # `public_root` - it is a fact about WHICH records exist, not about who asked for them, and
    # `scripts/cohort.py` reads it directly.
    slug = record.subject_id.replace(":", "_").replace("/", "_")
    idx_path = emitted_by_subject / f"{slug}.json"
    ids = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else []
    ids.append(record.witness_id)
    idx_path.write_text(json.dumps(ids, indent=2) + "\n", encoding="utf-8")

    request_path = private_requests / f"{record.witness_id}.json"
    request_path.write_text(json.dumps({
        "witness_id": record.witness_id,
        "customer_contact": customer_contact,
        "subject_contact": subject_contact,
        # Fable's condition on ruling the CLI an acceptable "joint request" realisation: the
        # private record must say HOW jointness was established, not only who the two parties
        # were - so a later audit can tell a genuinely joint request from an operator's mistake.
        "joint_intent_evidence": joint_intent_evidence,
    }, indent=2) + "\n", encoding="utf-8")

    return {"emitted": emitted_path, "served": served_path, "index": idx_path,
            "request": request_path}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subject", required=True, help="subject_id, e.g. git:owner/repo")
    ap.add_argument("--criterion-type", required=True, choices=["url_reachable", "artifact_hash"])
    ap.add_argument("--url", required=True)
    ap.add_argument("--sha256", help="required for artifact_hash")
    ap.add_argument("--customer-contact", required=True,
                    help="how the customer who asked for this can be reached - kept private, "
                         "never published")
    ap.add_argument("--subject-contact", required=True,
                    help="how the subject who agreed to this can be reached - kept private, "
                         "never published")
    ap.add_argument("--joint-intent-evidence", required=True,
                    help="how you established that BOTH parties actually asked for this - e.g. "
                         "'customer email of 2026-09-02, subject email of 2026-09-01' - kept "
                         "private, never published")
    args = ap.parse_args(argv)

    criterion: dict = {"type": args.criterion_type, "url": args.url}
    if args.criterion_type == "artifact_hash":
        if not args.sha256:
            ap.error("--sha256 is required for artifact_hash")
        criterion["sha256"] = args.sha256

    try:
        record = run_witness(args.subject, criterion)
    except UnsupportedCriterion as e:
        print(f"REFUSED, no record created: {e}", file=sys.stderr)
        return 1

    paths = publish_record(record, customer_contact=args.customer_contact,
                           subject_contact=args.subject_contact,
                           joint_intent_evidence=args.joint_intent_evidence, public_root=ROOT)
    print(f"{record.result} {record.witness_id} {args.subject} -> /w/{record.witness_id}/")
    print(f"  emitted: {paths['emitted']}")
    print(f"  served:  {paths['served']}")
    print(f"  private request record: {paths['request']}")
    print("  NEXT STEP: git add public/witness web/public/data/witness, then ./scripts/push.sh "
         "- publishing a record does not commit it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
