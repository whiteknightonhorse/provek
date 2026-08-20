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
from pathlib import Path

from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.measured import Measurement, NotMeasured


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


def collect(remote: str, *, keep: bool = False) -> RepoEvidence:
    """Gather evidence. A read failure yields NotMeasured - never a zero, never a raised error."""
    notes: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="incub_"))
    try:
        rc, out = _run(["git", "clone", "--depth", "50", "--quiet", remote, str(tmp / "r")])
        if rc != 0:
            notes.append(f"clone failed: {out.strip()[:200]}")
            return RepoEvidence(remote, None,
                                Measurement(absent=NotMeasured.UNREADABLE),
                                Measurement(absent=NotMeasured.UNREADABLE),
                                None, notes=notes)
        r = tmp / "r"
        rc, head = _run(["git", "rev-parse", "HEAD"], cwd=r)
        head_sha = head.strip() if rc == 0 else None

        rc, log = _run(["git", "log", "--format=%G? %ae", "-n", "50"], cwd=r)
        if rc != 0 or not log.strip():
            signed = Measurement(absent=NotMeasured.UNREADABLE)
            authors = Measurement(absent=NotMeasured.UNREADABLE)
        else:
            rows = [ln.split(None, 1) for ln in log.strip().splitlines() if ln.strip()]
            good = sum(1 for r_ in rows if r_ and r_[0] in ("G", "U"))
            signed = Measurement(value=round(good / len(rows), 3))
            authors = Measurement(value=len({r_[1] for r_ in rows if len(r_) > 1}))

        return RepoEvidence(remote, head_sha, signed, authors, tree_digest(r), notes=notes)
    finally:
        if not keep:
            shutil.rmtree(tmp, ignore_errors=True)   # disk budget, section 5.5
