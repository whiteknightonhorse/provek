"""Withdraw a published subject: one edit to data/subjects.json that the next cohort run honours.

    python3 scripts/withdraw_subject.py owner/name --reason "..." --by operator|subject

Moves the row from `subjects` to `withdrawn` with the time, and prints what is still to be done.
It touches nothing else: the row and passport files leave the published surface when
`scripts/cohort.py` next runs (T-IN-07, D-72). Refuses a repository that is not a subject and a
second withdrawal of one already withdrawn. It makes no network call and deletes no file.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY = ("operator", "subject")

NEXT_STEPS = """\
withdrawn: {repo}
next steps (the chain docs/LIVENESS_OPERATIONS.md names):
  python3 scripts/cohort.py          # drops the row, removes the two passport files
  (cd web && npm run build)          # the page, the badge and the summary leave the build
  git add data public web/public/data && git commit -m "withdraw {repo}"
  ./scripts/push.sh                  # the only door outward
  ~/orchestra/deploy.sh              # the operator's step; a push publishes nothing
"""


def withdraw(doc: dict, repo: str, reason: str, by: str, at: str) -> dict:
    """Return `doc` with `repo` moved to `withdrawn`. Raises SystemExit on a refusal."""
    if by not in BY:
        raise SystemExit(f"--by must be one of {BY}, not {by!r}")
    if not reason.strip():
        raise SystemExit("--reason is required: a withdrawal without a sentence cannot be explained")
    withdrawn = doc.get("withdrawn")
    if withdrawn is None:
        raise SystemExit("data/subjects.json has no `withdrawn` list; refusing to invent one")
    if any(w["repo"] == repo for w in withdrawn):
        raise SystemExit(f"REFUSED: {repo} is already withdrawn")
    if not any(s["repo"] == repo for s in doc["subjects"]):
        raise SystemExit(f"REFUSED: {repo} is not a subject in data/subjects.json")
    doc["subjects"] = [s for s in doc["subjects"] if s["repo"] != repo]
    withdrawn.append({"repo": repo, "at": at, "reason": reason.strip(), "by": by})
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("repo", help="owner/name, exactly as listed in data/subjects.json")
    ap.add_argument("--reason", required=True)
    ap.add_argument("--by", required=True, choices=BY)
    ap.add_argument("--file", type=Path, default=ROOT / "data" / "subjects.json",
                    help="subjects file (default: the repository's own)")
    a = ap.parse_args(argv)
    doc = json.loads(a.file.read_text(encoding="utf-8"))
    at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    withdraw(doc, a.repo, a.reason, a.by, at)
    a.file.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(NEXT_STEPS.format(repo=a.repo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
