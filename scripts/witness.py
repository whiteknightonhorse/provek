#!/usr/bin/env python3
"""WitnessRecord v0 intake and publication (spec 4.2-bis point 4).

RUN BY THE OPERATOR (or their agent), ON A JOINT REQUEST FROM BOTH PARTIES - never on this
project's own initiative (A-9: active checks run only when someone with standing asked). This is
a CLI, not a public web form: the specification asks for a JOINT request, and a public POST
endpoint has no way to tell "both parties actually asked" from "one party typed two email
addresses" - inventing an authentication protocol for that was not specified and is not decided
here. See DECISIONS.md D-49 and this session's own report to the operator/Fable, which names this
as an interpretation rather than a ratified design. `--customer-contact` and `--subject-contact`
are REQUIRED, so whoever runs this has to have both in hand before a check can run at all.

WHAT GETS PUBLISHED, AND WHAT DOES NOT. `public/witness/<id>.json` and its mirror under
`web/public/data/witness/` carry ONLY the seven fields spec 4.2-bis point 4 names - see
`src.witness.witness.WitnessRecord.to_machine`. The two contacts given on the command line go to
`public/witness/_requests/<id>.json`, which is NEVER mirrored to the served tree and NEVER read by
the site or by `scripts/cohort.py`: it exists so a later question about "who asked for this" has an
answer, the same reason `web/functions/api/apply.js`'s KV record exists, kept out of the public
artefact for the same reason a subject's contact address is not published anywhere else on this
site.

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


def publish_record(record: WitnessRecord, *, customer_contact: str, subject_contact: str,
                   root: Path) -> dict:
    """Write the published record to both trees and the private request file, under `root`.

    `root` is a parameter - not a module-level constant - so a test can point this at a temporary
    directory and assert on real files without touching the live `public/witness/` tree. Returns
    the three paths written, for the caller (or a test) to inspect.
    """
    emitted = root / "public" / "witness"
    served = root / "web" / "public" / "data" / "witness"
    (emitted / "_requests").mkdir(parents=True, exist_ok=True)
    (emitted / "by_subject").mkdir(parents=True, exist_ok=True)
    served.mkdir(parents=True, exist_ok=True)

    payload = json.dumps({"witness": record.to_machine()}, indent=2) + "\n"
    emitted_path = emitted / f"{record.witness_id}.json"
    served_path = served / f"{record.witness_id}.json"
    emitted_path.write_text(payload, encoding="utf-8")
    served_path.write_text(payload, encoding="utf-8")

    # Per-subject index, so `src.witness.witness.load_task_history` can find every record for a
    # subject without scanning the whole directory on every re-measure.
    slug = record.subject_id.replace(":", "_").replace("/", "_")
    idx_path = emitted / "by_subject" / f"{slug}.json"
    ids = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else []
    ids.append(record.witness_id)
    idx_path.write_text(json.dumps(ids, indent=2) + "\n", encoding="utf-8")

    request_path = emitted / "_requests" / f"{record.witness_id}.json"
    request_path.write_text(json.dumps({
        "witness_id": record.witness_id,
        "customer_contact": customer_contact,
        "subject_contact": subject_contact,
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
                           subject_contact=args.subject_contact, root=ROOT)
    print(f"{record.result} {record.witness_id} {args.subject} -> /w/{record.witness_id}/")
    print(f"  emitted: {paths['emitted']}")
    print(f"  served:  {paths['served']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
