"""Evidence collection through the GitHub API - BY THE SAME CHANNEL an external subject would use.

FABLE RULING 2026-08-19, and it is load-bearing: reading a subject through host privileges (sudo)
is FORBIDDEN. A methodology that only works where we are root is not reproducible by a third party
and violates ABI-5-3. Access is ANONYMOUS: these are public reads, and a reader who holds nothing
at all can repeat them. A granted token is accepted only to widen the rate limit for a large
cohort. Self-application is thereby a rehearsal of the real protocol rather than a privileged
shortcut - and a stricter one than the original ruling asked for, because it removes the credential
rather than scoping it.

REDACTION IS MANDATORY (same ruling): discovered secrets never enter evidence artefacts. The same
code will be needed for external subjects, so it is written here now, not "later".
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field

from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.measured import Measurement, NotMeasured

API = "https://api.github.com"

SECRET_PATTERNS = (
    re.compile(r"gh[pous]_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-ant-[A-Za-z0-9_-]{30,}"),
    re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    re.compile(r"0x[0-9a-f]{64}"),
)


def redact(text: str) -> str:
    """Strip secrets BEFORE the text becomes an artefact.

    Redaction lives here rather than at the output: an artefact from which a secret is removed
    later has already sat in memory, in a log, and possibly in a dump.
    """
    for p in SECRET_PATTERNS:
        text = p.sub("<REDACTED>", text)
    return text


@dataclass(frozen=True)
class GitHubEvidence:
    full_name: str
    read: bool = field(default=True, kw_only=True)
    """Did the subject's source answer THIS reader?

    A repository that returns 404 to an anonymous request has not "qualified nothing" - it has
    refused. The distinction is the founding one: `nothing_qualified` says we looked at what was
    there and none of it counted; `unreadable` says the source did not answer us. Conflating them
    told readers that five subjects had been examined and found wanting, when in truth they could
    not be examined by anyone without a credential."""
    private: bool
    head_sha: str | None
    signed_commit_share: Measurement
    distinct_authors: Measurement
    bot_author_share: Measurement       # share of commits from bot/app accounts
    workflow_runs: Measurement          # automated CI runs - a trace of INITIATION
    evidence_class: EvidenceClass = EvidenceClass.PLATFORM_OBSERVED
    notes: list[str] = field(default_factory=list)

    @property
    def has_runtime_trace(self) -> bool:
        """Is there a runtime trace of initiation (limiter O2 from the Fable ruling).

        CI runs are NOT proof that a business is autonomous, but they are an observable trace that
        something starts without a human at the keyboard. Without such a trace, a weak signal has
        no right to justify L3 or above.
        """
        return self.workflow_runs.is_measured and self.workflow_runs.value > 0


ANONYMOUS = "anonymous"
GRANTED = "granted_token"


def access_channel(token: str | None) -> str:
    """Which channel this evidence came through - and it is published, not assumed.

    "Reproducible by anyone" and "reproducible by someone holding a credential" are different
    claims, and this project does not let a reader guess which one they are being offered.
    """
    return GRANTED if token else ANONYMOUS


def _rate_limit_exhausted(token: str | None) -> bool:
    """Ask GitHub whether OUR budget is the reason, instead of inferring it from a status code."""
    code, body = _api("/rate_limit", token)
    if code != 200 or not isinstance(body, dict):
        return False
    core = ((body.get("resources") or {}).get("core") or {})
    return core.get("remaining") == 0


def _api(path: str, token: str | None = None) -> tuple[int, object]:
    """ANONYMOUS BY DEFAULT (2026-08-20).

    The three calls this collector makes are public reads, and public reads need no credential at
    all: measured, all three return 200 unauthenticated, and a full cohort costs 24 of the 60
    anonymous requests GitHub allows per hour.

    That is the strongest available form of ABI-5-3. A scoped read-only token would make the
    pipeline reproducible by anyone the operator chooses to grant one; no token makes it
    reproducible by anyone at all, which is what "a third party can recompute the verdict from the
    same inputs" actually asks for. The token remains an option purely to widen the rate limit for
    a cohort larger than the anonymous budget - never as the default, and never as a requirement.
    """
    headers = ["-H", "Accept: application/vnd.github+json"]
    if token:
        headers = ["-H", f"Authorization: Bearer {token}", *headers]
    p = subprocess.run(
        ["curl", "-s", "-w", "\n%{http_code}", *headers, f"{API}{path}"],
        capture_output=True, text=True, timeout=60)
    raw = p.stdout.rsplit("\n", 1)
    if len(raw) != 2:
        return 0, None
    body, code = raw
    try:
        return int(code), json.loads(body)
    except Exception:
        return int(code) if code.isdigit() else 0, None


def collect_github(full_name: str, token: str | None = None) -> GitHubEvidence:
    """Gather evidence about a repository. Unreachability yields NotMeasured, never zeros."""
    notes: list[str] = []
    def unread() -> Measurement:
        return Measurement(absent=NotMeasured.UNREADABLE)


    code, repo = _api(f"/repos/{full_name}", token)
    # NEW-4 (Fable): GitHub also returns 403 for DMCA-blocked and access-blocked repositories.
    # Treating every 403 as our exhausted budget would abort the whole cohort announcing a fact
    # about us when the truth was one subject refusing - misattribution in the opposite direction
    # from the one this guard exists to prevent. Only a 403 that comes with an exhausted rate-limit
    # header is ours; any other 403 is the subject's refusal and yields `unreadable` below.
    if code == 429 or (code == 403 and _rate_limit_exhausted(token)):
        # Exhausting a rate limit is OUR budget running out, not the subject's source refusing to
        # answer. Emitting evidence here would publish a fact about us as a fact about them.
        raise SystemExit(
            f"GitHub rate limit reached while reading {full_name} (HTTP {code}).\n"
            "Anonymous access allows 60 requests an hour and this cohort costs three per subject.\n"
            "Wait for the window to reset, or set PROVEK_GITHUB_TOKEN to widen the limit - the\n"
            "token changes the budget, never the evidence."
        )
    if code != 200 or not isinstance(repo, dict):
        notes.append(redact(f"repository not read, HTTP {code}"))
        return GitHubEvidence(full_name, False, None, unread(), unread(), unread(), unread(),
                              notes=notes, read=False)

    code, commits = _api(f"/repos/{full_name}/commits?per_page=50", token)
    if code != 200 or not isinstance(commits, list) or not commits:
        signed = authors = bots = unread()
        head = None
        notes.append(redact(f"commit history not read, HTTP {code}"))
    else:
        head = commits[0].get("sha")
        verified = sum(1 for c in commits
                       if (c.get("commit") or {}).get("verification", {}).get("verified"))
        logins, botn = set(), 0
        for c in commits:
            a = c.get("author") or {}
            login = a.get("login") or ((c.get("commit") or {}).get("author") or {}).get("email", "?")
            logins.add(login)
            if a.get("type") == "Bot" or str(login).endswith("[bot]"):
                botn += 1
        signed = Measurement(value=round(verified / len(commits), 3))
        authors = Measurement(value=len(logins))
        bots = Measurement(value=round(botn / len(commits), 3))

    code, runs = _api(f"/repos/{full_name}/actions/runs?per_page=1", token)
    if code == 200 and isinstance(runs, dict):
        wf = Measurement(value=int(runs.get("total_count", 0)))
    else:
        wf = unread()
        notes.append(f"CI runs not read, HTTP {code}")

    return GitHubEvidence(full_name, bool(repo.get("private")), head,
                          signed, authors, bots, wf, notes=notes)
