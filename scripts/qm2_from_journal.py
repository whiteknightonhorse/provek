"""QM2 from the nightly's own cost journal (T-0578).

`measure_qm2.py` prices one pass by running it; the nightly writes what a real night cost to
`~/orchestra/logs/remeasure_cost.jsonl`. This prints calls per subject per night from the rows
that carry a MEASURED count, and the anonymous capacity (60 calls/hour) that count implies.
Rows with `github_calls_measured: null` are not zeros and are not averaged in; with none, the
answer is `not_measured`.

    python3 scripts/qm2_from_journal.py [path/to/remeasure_cost.jsonl]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ANONYMOUS_PER_HOUR = 60
DEFAULT_JOURNAL = Path.home() / "orchestra" / "logs" / "remeasure_cost.jsonl"


def report(lines: list[str]) -> str:
    """Counter rows (they carry `github_calls_rate_limit_delta`, written from T-0578 on) are the
    measurement. Older rows inferred the count from two `/rate_limit` reads, before T-0570 added
    one call per subject; they are listed apart and never enter the capacity figure."""
    rows = [json.loads(ln) for ln in lines if ln.strip()]
    measured = [r for r in rows
                if r.get("github_calls_measured") is not None and r.get("subjects")]
    counted = [r for r in measured if "github_calls_rate_limit_delta" in r]
    inferred = [r for r in measured if "github_calls_rate_limit_delta" not in r]
    out = [f"journal rows: {len(rows)}; counted nights: {len(counted)}; "
           f"earlier nights inferred from /rate_limit: {len(inferred)}"]
    if inferred:
        per = [r["github_calls_measured"] / r["subjects"] for r in inferred]
        out.append(f"earlier (not counted, before T-0570's extra call): "
                   f"{min(per):.2f}..{max(per):.2f} calls per subject")
    if not counted:
        out.append("not_measured: 0 counted nights")
        return "\n".join(out)
    per_night = []
    for r in counted:
        per = r["github_calls_measured"] / r["subjects"]
        per_night.append(per)
        out.append(f"{r['at']}  subjects={r['subjects']}  calls={r['github_calls_measured']}"
                   f"  calls_per_subject={per:.2f}")
    worst = max(per_night)
    out.append(f"max calls per subject: {worst:.2f}")
    out.append(f"anonymous capacity at {ANONYMOUS_PER_HOUR}/h: "
               f"{int(ANONYMOUS_PER_HOUR // worst)} subjects per hour")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT_JOURNAL
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        print(f"not_measured: journal unreadable: {e.strerror}")
        return 1
    print(report(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
