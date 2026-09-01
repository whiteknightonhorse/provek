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
from datetime import datetime, timedelta, timezone

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
    private: bool | None
    """None when the source did not answer: unknown, which is not the same as False."""
    head_sha: str | None
    signed_commit_share: Measurement
    distinct_authors: Measurement
    bot_author_share: Measurement       # share of commits from bot/app accounts
    workflow_runs: Measurement          # automated CI runs - a trace of INITIATION
    identity_window_closed: Measurement = field(default_factory=lambda: Measurement(value=None, absent=NotMeasured.UNREADABLE))
    """Was every non-bot commit attributed by the PLATFORM or by a signature?

    Closed, `distinct_authors` is a count. Open, it is a lower bound: behind one unattributed key
    there can be any number of people, and no `authors <= N` claim is provable. The ladder answers
    an open window with its floor rather than with a guess in either direction, and rather than
    with `not measured` -- which would reward a subject for injecting one anonymous commit."""
    unlinked_commit_share: Measurement = field(default_factory=lambda: Measurement(value=None, absent=NotMeasured.UNREADABLE))
    unlinked_key_count: Measurement = field(default_factory=lambda: Measurement(value=None, absent=NotMeasured.UNREADABLE))
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

    Public reads need no credential at all, and that much still holds. What does NOT still hold is
    the count this docstring claimed: "all three return 200... a full cohort costs 24 of the 60
    anonymous requests GitHub allows per hour." Re-measured 2026-08-24 against the live API (see
    evidence/RED-037-*): `whiteknightonhorse/gov-auction-report` now answers 404, not 200, and a
    404 short-circuits `collect_github` after the FIRST call - it never reaches the commits or runs
    endpoints - so the three subjects `measure_qm2.py` exercises cost 3 + 3 + 1 = 7 calls, not the
    flat 3-per-subject this docstring assumed. A collector that measures its own subjects can be
    as stale as any other measurement; this one had gone four days without being re-run against
    the sources it describes.

    The general claim survives the correction: reads are public, need no credential, and a scoped
    token remains optional. That is the strongest available form of ABI-5-3. A scoped read-only
    token would make the pipeline reproducible by anyone the operator chooses to grant one; no
    token makes it reproducible by anyone at all, which is what "a third party can recompute the
    verdict from the same inputs" actually asks for. The token remains an option purely to widen
    the rate limit for a cohort larger than the anonymous budget - never as the default, and never
    as a requirement.
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


EVIDENCE_WINDOW_DAYS = 30
"""ASSIGNED, and already published: every passport carries it as `evidence_window_days`.

Ratified 2026-08-25 by adopting the number the documents had been promising rather than choosing
a new one. The instrument was brought to the promise; the promise was not rewritten to match the
instrument."""

COMMITS_PER_PAGE = 100
"""Structural, not policy: the largest page the GitHub commits endpoint will return.

Named because the gate that refuses bare numbers at a comparison was right to refuse this one -
read as a literal, `len(batch) < 100` is indistinguishable from a threshold somebody chose, and
the day the API changes it, the short-page test silently stops detecting the end of the window."""

COMMIT_PAGE_CEILING = 10
"""ASSIGNED. A fuse, not a window: ten pages of commits inside 30 days and the read stops UNDERREAD.

Reaching it cannot help a subject. Flooding a window is something only the subject can do, and
doing it costs them closure - the refusal points down, which is the correct direction for a gate
to be wrong in."""

CLOSURE_MASS_FLOOR = 10
"""ASSIGNED. Fewer than ten non-bot commits in the window and closure grants no level.

Closure says every commit was attributed. Over two commits that is true and means nothing, and a
subject would climb the ladder by committing almost nothing - silence as a strategy. Below the
floor the ladder answers with the same floor it gives an OPEN window, so staying quiet is never
better than being read."""


def authors_and_bot_commits(commits: list[dict]) -> tuple[set[str], int, set[str], int]:
    """Attributed authors, bot commits, and the keys nothing vouches for.

    IDENTITY IS RESOLVED BY THE PLATFORM OR BY CRYPTOGRAPHY, NEVER BY US. A commit GitHub
    attributes to a login is attributed: linking an address to an account requires proving you
    control the address, and the attribution is then visible to any anonymous reader. A signed
    commit is attributed by the signature. A commit with neither carries only the name and address
    its author typed into their own `git config` -- written by the side being measured, which is
    exactly what a key may not be. Merging such commits into an identity would encode a guess;
    splitting them encodes a different guess. They are counted apart instead, and the count they
    produce is a LOWER BOUND rather than a number (Fable, 2026-08-25).

    Split out of `collect_github` so it can be judged without a network: the rule it carries was
    ratified separately (ladder.SOLE_AUTHOR, 2026-08-25), and a ratified rule that only a live API
    call can exercise is a rule nothing guards.

    BOTS ARE COUNTED, BUT NOT AS AUTHORS. `distinct_authors` feeds SOLE_AUTHOR, whose docstring
    calls it the strongest signal that no HUMAN ROTA is behind the commits. A dependency bot's
    commit is not evidence of a human rota, so counting it there made the signal assert people on
    the strength of commits no person wrote - and cost a subject a level for becoming MORE
    automated, which is the one thing this ladder exists to reward.

    The test is the PLATFORM's classification, never the name. Renaming an account
    `something-bot` opens no hole: GitHub types such an account `User`, and the `[bot]` suffix
    cannot be typed into a user login at all - square brackets are not legal there, and the
    platform synthesises that suffix for Apps alone.
    """
    logins: set[str] = set()
    bot_commits = 0
    unlinked_keys: set[str] = set()
    unlinked_commits = 0
    for c in commits:
        a = c.get("author") or {}
        login = a.get("login")
        cm = (c.get("commit") or {}).get("author") or {}
        signed = bool(((c.get("commit") or {}).get("verification") or {}).get("verified"))
        if a.get("type") == "Bot" or str(login or "").endswith("[bot]"):
            bot_commits += 1        # bot_author_share still measures every one of them
            continue
        if login:
            logins.add(login)       # the PLATFORM attributed this commit to an account
        elif signed:
            logins.add(cm.get("email", "?"))   # cryptography attributed it instead
        else:
            # NEITHER the platform nor a signature vouches for who wrote this. The e-mail is
            # whatever the author's `git config` said, which the measured side writes itself.
            unlinked_keys.add(cm.get("email", "?"))
            unlinked_commits += 1
    return logins, bot_commits, unlinked_keys, unlinked_commits


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
        # `private` was hardcoded False here (Fable, B2). For a repository that answered 404 to
        # this reader, "private: false" is not a weaker claim - it is the OPPOSITE of the truth,
        # and it travelled downstream into the passport's self-reported block under a heading that
        # says "claimed by the subject". The subject claimed nothing; the template did. That is
        # invariant 1 and R4's shape at once, and it is refutable by anyone who opens the URL.
        return GitHubEvidence(full_name, None, None, unread(), unread(), unread(), unread(),
                              notes=notes, read=False)
    # Defaults before the branch. A source that did not answer leaves these UNREADABLE rather
    # than undefined: an exception here would read as a crash, not as an absent measurement.
    closed = unread()
    unlinked_share = unread()
    unlinked_key_count = unread()

    # THE WINDOW IS TIME, AND IT IS THE TIME WE PUBLISH. Until 2026-08-25 this read the last 50
    # commits by COUNT while every passport declared `evidence_window_days: 30`. Those are
    # different quantities, and the difference is not academic: a count window is EVACUATED BY THE
    # ACTIVITY OF THE SUBJECT BEING MEASURED. Our own repository demonstrated it - roughly fifty
    # commits in one day pushed an unattributed commit from the day before past position 50, and
    # the instrument reported a closed identity window that a 30-day reading shows open.
    #
    # A time window cannot be evacuated by working harder; it can only be waited out in real time,
    # and the dates are public, so waiting it out is visible to any reader. Between two unratified
    # numbers the PUBLISHED one wins: 30 days is a promise made in every issued document, 50 was a
    # literal in a URL that promised nothing (Fable, 2026-08-25).
    since = (datetime.now(timezone.utc) - timedelta(days=EVIDENCE_WINDOW_DAYS)).isoformat()
    commits: list[dict] = []
    window_fully_read = False
    code = 0
    for page in range(1, COMMIT_PAGE_CEILING + 1):
        code, batch = _api(
            f"/repos/{full_name}/commits"
            f"?per_page={COMMITS_PER_PAGE}&since={since}&page={page}", token)
        if code != 200 or not isinstance(batch, list):
            break
        commits.extend(batch)
        if len(batch) < COMMITS_PER_PAGE:
            window_fully_read = True     # a short page means the window is exhausted
            break
    else:
        # The ceiling was reached with pages still coming. UNDERREAD is not the same finding as
        # OPEN: open means a counter-example was seen, underread means the instrument never
        # finished looking. They publish apart and weigh the same at the gate, because closure is
        # a claim about EVERY commit in the window and a partial read cannot make it.
        notes.append(f"window not fully read: stopped at the {COMMIT_PAGE_CEILING}-page ceiling")

    if code != 200:
        # THE SOURCE REFUSED. Nothing about the subject is known from here.
        signed = authors = bots = unread()
        head = None
        notes.append(redact(f"commit history not read, HTTP {code}"))
    elif not commits:
        # THE SOURCE ANSWERED AND THE WINDOW IS EMPTY. These are different worlds and collapsing
        # them was a defect I introduced with the time window: a repository whose last commit
        # predates the window had its silence reported as "we could not read it", which is a
        # statement about US wearing a statement about THEM. The read succeeded; there was simply
        # nothing inside the thirty days.
        #
        # NO_EVIDENCE_IN_WINDOW (Fable, 2026-09-01 - the fourth reason this docstring used to say
        # LAW-NOT-MEASURED had no room for). `nothing_qualified` was filed here as "the declared
        # reason closest to this" and it was closest, not correct: it reads as "the check ran and
        # examined candidates, none of which qualified", while what happened here is that the
        # window itself was empty. Two subjects (AIpush, mcp-protocol-tester) published the
        # imprecise reading all the way to the live registry, where `projection()`'s precedence
        # then picked `check_did_not_run` from their two always-unattempted operations over this
        # one - so a check that ran ended up reported as one that never did. Fixed at the source.
        signed = authors = bots = Measurement(value=None, absent=NotMeasured.NO_EVIDENCE_IN_WINDOW)
        head = None
        notes.append(f"no commits inside the {EVIDENCE_WINDOW_DAYS}-day evidence window")
    else:
        head = commits[0].get("sha")
        verified = sum(1 for c in commits
                       if (c.get("commit") or {}).get("verification", {}).get("verified"))
        logins, botn, unlinked_keys, unlinked_n = authors_and_bot_commits(commits)
        signed = Measurement(value=round(verified / len(commits), 3))
        authors = Measurement(value=len(logins))
        bots = Measurement(value=round(botn / len(commits), 3))
        # The window is CLOSED when every non-bot commit was attributed by the platform or by a
        # signature. Open, the author count cannot be an upper bound: any number of people can
        # stand behind one unattributed key.
        non_bot = len(commits) - botn
        # Closure needs all three: nothing unattributed, the whole window actually read, and
        # enough commits for the claim to mean anything. Closure over two commits is a vacuum
        # truth - true, and evidence of nothing.
        closed = Measurement(value=(unlinked_n == 0 and window_fully_read
                                    and non_bot >= CLOSURE_MASS_FLOOR))
        unlinked_share = Measurement(value=round(unlinked_n / len(commits), 3))
        unlinked_key_count = Measurement(value=len(unlinked_keys))

    code, runs = _api(f"/repos/{full_name}/actions/runs?per_page=1", token)
    if code == 200 and isinstance(runs, dict):
        total_runs = int(runs.get("total_count", 0))
        if total_runs:
            wf = Measurement(value=total_runs)
        else:
            # APPARATUS_ABSENT (Fable, 2026-09-01). This endpoint carries no `since` filter - it
            # is not a windowed read - so `total_count: 0` is not "none in the last thirty days",
            # it is "none have ever existed". Measured on `cryptocardhub-public`. Publishing that
            # as a measured `value: 0` would let a structural fact about the subject's platform
            # choice (no CI configured at all) travel through the same slot as a genuine zero-run
            # count, exactly the "zero conflated with absence" shape LAW-NOT-MEASURED exists to
            # forbid. The trait "how many CI runs" does not apply to a subject with no apparatus.
            wf = Measurement(absent=NotMeasured.APPARATUS_ABSENT)
    else:
        wf = unread()
        notes.append(f"CI runs not read, HTTP {code}")

    return GitHubEvidence(full_name, bool(repo.get("private")), head,
                          signed, authors, bots, wf, notes=notes,
                          identity_window_closed=closed,
                          unlinked_commit_share=unlinked_share,
                          unlinked_key_count=unlinked_key_count)
