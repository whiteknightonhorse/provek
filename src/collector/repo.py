"""T-2.3 - passive evidence from a public repository (ABI-5-1, ABI-5-2).

BOUNDARIES SET BY THE SPECIFICATION:
  * read-only - we never write to the subject's systems;
  * MVP takes only PUBLIC repositories of THIRD PARTIES (section 10.2). The operator's own
    systems are not third parties (identity predicate) and are read by the same channel an
    external subject would use - never through host privileges;
  * clone `--depth`, and the working copy is DELETED after the audit - a couple of large foreign
    repositories would eat the entire 10 GB disk budget. Only evidence artefacts persist.

WHAT IS NOT DONE HERE. No conclusion about autonomy - that belongs to the scorer. The collector
only GATHERS, and honestly reports what it failed to gather: `unreadable`, never a zero.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.measured import Measurement, NotMeasured
from src.collector.github import EVIDENCE_WINDOW_DAYS


@dataclass(frozen=True)
class RepoEvidence:
    """What was gathered. Every field carries its own forgeability class."""
    remote: str
    head_sha: str | None
    signed_commit_share: Measurement
    distinct_authors: Measurement
    tree_digest: str | None
    evidence_class: EvidenceClass = EvidenceClass.PLATFORM_OBSERVED
    notes: list[str] = field(default_factory=list)


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def tree_digest(root: Path) -> str:
    """Digest of the tree CONTENT - the thing comparable to a deployed artefact (T-2.4).

    Computed over sorted paths and file hashes; `.git` is excluded because we care about the
    shipped code, not the history.
    """
    h = hashlib.sha256()
    for f in sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts):
        h.update(f.relative_to(root).as_posix().encode())
        h.update(hashlib.sha256(f.read_bytes()).digest())
    return h.hexdigest()


CLONE_DEPTH_CEILING = 500
"""ASSIGNED. A fuse against the disk budget (CLAUDE.md: 10 GB shared by ten projects), not the
evidence window - the window is TIME (`EVIDENCE_WINDOW_DAYS`, imported from `src.collector.github`,
LAW #ONE-PLACE, so this module cannot carry a second, disagreeing number of its own).

Until the fix for AUD-002 (2026-09-03) this constant WAS the window: `--depth 50` and `git log -n
50` read the last fifty commits BY COUNT while every passport declared `evidence_window_days: 30` -
exactly the errata already published against `collect_github` on 2026-08-25 for the API reader, and
still alive here because this collector was never brought in line with it. A count window is
EVACUATED BY THE ACTIVITY OF THE SUBJECT BEING MEASURED; a time window cannot be. A plain git clone
has no `since=` filter to page against the way the GitHub API does, so the ceiling here is a depth
generous enough that an ordinary repository's real 30-day history fits inside it, with an explicit
underread note - mirroring `COMMIT_PAGE_CEILING` in github.py - when it does not."""


def collect(remote: str, *, keep: bool = False, now: datetime | None = None) -> RepoEvidence:
    """Gather evidence. A read failure yields NotMeasured - never a zero, never a raised error."""
    now = now or datetime.now(timezone.utc)
    notes: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="incub_"))
    try:
        rc, out = _run(["git", "clone", "--depth", str(CLONE_DEPTH_CEILING), "--quiet",
                       remote, str(tmp / "r")])
        if rc != 0:
            notes.append(f"clone failed: {out.strip()[:200]}")
            return RepoEvidence(remote, None,
                                Measurement(absent=NotMeasured.UNREADABLE),
                                Measurement(absent=NotMeasured.UNREADABLE),
                                None, notes=notes)
        r = tmp / "r"
        rc, head = _run(["git", "rev-parse", "HEAD"], cwd=r)
        head_sha = head.strip() if rc == 0 else None

        cutoff = now - timedelta(days=EVIDENCE_WINDOW_DAYS)
        rc, log = _run(["git", "log", f"--since={cutoff.isoformat()}", "--format=%G? %ae"], cwd=r)
        if rc != 0:
            signed = Measurement(absent=NotMeasured.UNREADABLE)
            authors = Measurement(absent=NotMeasured.UNREADABLE)
        elif not log.strip():
            # THE CLONE ANSWERED AND THE WINDOW IS EMPTY - not the same claim as UNREADABLE. Mirrors
            # `NO_EVIDENCE_IN_WINDOW` in github.py (Fable, 2026-09-01): a repository whose last
            # commit predates the window is not a repository that refused to answer.
            signed = Measurement(value=None, absent=NotMeasured.NO_EVIDENCE_IN_WINDOW)
            authors = Measurement(value=None, absent=NotMeasured.NO_EVIDENCE_IN_WINDOW)
            notes.append(f"no commits inside the {EVIDENCE_WINDOW_DAYS}-day evidence window")
        else:
            rows = [ln.split(None, 1) for ln in log.strip().splitlines() if ln.strip()]
            good = sum(1 for r_ in rows if r_ and r_[0] in ("G", "U"))
            signed = Measurement(value=round(good / len(rows), 3))
            authors = Measurement(value=len({r_[1] for r_ in rows if len(r_) > 1}))

            # UNDERREAD, NOT SILENTLY TRUSTED. `--depth` bounds what this clone can see AT ALL, so a
            # `--since` filter run against a truncated history cannot tell "nothing older exists"
            # from "older commits exist but the shallow boundary hid them" - only the age of that
            # boundary's own oldest commit can.
            rc2, oldest_out = _run(["git", "log", "--format=%cI"], cwd=r)
            oldest_lines = [ln for ln in oldest_out.strip().splitlines() if ln.strip()]
            if rc2 == 0 and oldest_lines and datetime.fromisoformat(oldest_lines[-1]) >= cutoff:
                notes.append(
                    f"window not fully read: shallow clone (depth {CLONE_DEPTH_CEILING}) reached "
                    f"its boundary before the {EVIDENCE_WINDOW_DAYS}-day cutoff")

        return RepoEvidence(remote, head_sha, signed, authors, tree_digest(r), notes=notes)
    finally:
        if not keep:
            shutil.rmtree(tmp, ignore_errors=True)   # disk budget, section 5.5
