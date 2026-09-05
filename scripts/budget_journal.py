"""T-76 (Fable ruling, 2026-09-05): the anonymous GitHub budget is MEASURED, not assumed.

WHAT THIS REPLACES. `~/orchestra/nightly_remeasure.sh` used to spend the anonymous budget on ten
subjects before ever asking GitHub what that budget was, and its cost journal
(`~/orchestra/logs/remeasure_cost.jsonl`) recorded `github_calls_assumed: 3 * n` - a number nobody
measured, carried over from `scripts/measure_qm2.py`'s three-subject pipeline and never re-checked
against this cohort's own calls. On 2026-09-05 the budget was already at `remaining=0` before
`cohort.py`'s first request - spent by a neighbour sharing this host's outbound address (CLAUDE.md,
"ten projects share this host"), not by the cohort - and all ten subjects paid for a 403 plus a
confirming `/rate_limit` read against a budget that was already empty. This module gives the
nightly chain a way to read that budget FIRST, wait for it ONCE if it is empty, and write down what
was actually spent instead of what a per-subject literal assumes.

These are pure functions on purpose: the values GitHub returns (`remaining`, `limit`, `reset`) are
plain integers, and a rule stated on them should be checkable without a live network call. The
network read itself (`curl https://api.github.com/rate_limit`) stays in
`~/orchestra/nightly_remeasure.sh`, which is not part of this repository and is not unit-tested by
it - the same arrangement this file's neighbours (`PYCOST`/`PYINV`, inline in that script) already
have. What moved IN here is the part that can be wrong independently of the network: the arithmetic.
"""
from __future__ import annotations

from datetime import datetime, timezone


def parse_core(rate_limit_body: dict | None) -> dict | None:
    """Pull `remaining`/`limit`/`reset` out of a `/rate_limit` response body.

    `None` in, `None` out - and `None` out for anything that is not a well-formed core block.
    The endpoint being unreadable is `rate_limit_endpoint_unreadable`, never a budget of zero:
    inventing a measurement the network did not provide is the exact defect `NotMeasured` exists
    to forbid elsewhere in this project (CLAUDE.md invariant 1), and a budget gate is not exempt.
    """
    if not isinstance(rate_limit_body, dict):
        return None
    core = (rate_limit_body.get("resources") or {}).get("core")
    if not isinstance(core, dict):
        return None
    if not all(k in core for k in ("remaining", "limit", "reset")):
        return None
    return {"remaining": core["remaining"], "limit": core["limit"], "reset": core["reset"]}


def wait_seconds_for(core: dict | None, now_epoch: int) -> int:
    """How long to wait, ONCE, before spending a budget already known to be empty.

    Bounded by the field it reads, not by a constant this file would have to keep honest:
    `reset` always falls inside the current hourly window, so this can never ask for more than an
    hour. Zero - no wait - when the budget already has room, when `reset` has already passed (a
    stale read), or when `/rate_limit` itself could not be read: an unreadable instrument is not
    treated as an empty budget, the same distinction `parse_core` draws.

    Callers are expected to check ONCE, wait this many seconds if positive, and re-check ONCE
    after - never loop here. A budget still empty the instant the window reopens (a neighbour
    spending it again as fast as this host does) is a fact worth reporting, not a reason to sleep
    a second hour unattended.
    """
    if core is None or core["remaining"] != 0:
        return 0
    return max(0, core["reset"] - now_epoch)


def build_cost_row(*, at: datetime, n_subjects: int, seconds: int,
                    before: dict | None, after: dict | None, waited_seconds: int) -> dict:
    """One line of `remeasure_cost.jsonl` - MEASURED, never assumed (T-76 ruling).

    `github_calls_measured` is the difference of two real `/rate_limit` reads taken immediately
    before and immediately after the cohort pass - never a per-subject literal. It is `None`, with
    a named reason in `github_calls_absent_reason`, exactly when that difference cannot be
    trusted:

    - `rate_limit_endpoint_unreadable` - either read failed, so there is nothing to difference.
    - `window_reset_during_run` - `limit` or `reset` moved between the two reads, meaning the
      hourly window rolled over mid-run. `after remaining - before remaining` would then either
      be negative or would silently count a fresh hour's budget that this run never spent -
      inventory 1's rule (a number whose origin cannot be audited is not published as one).

    This mirrors `skip_rate_limited` in `scripts/cohort.py`: an absence is recorded by name, never
    coerced into a number that happens to print.
    """
    reason: str | None = None
    measured: int | None = None
    if before is None or after is None:
        reason = "rate_limit_endpoint_unreadable"
    elif after["limit"] != before["limit"] or after["reset"] != before["reset"]:
        reason = "window_reset_during_run"
    else:
        measured = before["remaining"] - after["remaining"]

    reference = after or before
    return {
        "at": at.isoformat(timespec="seconds"),
        "subjects": n_subjects,
        "seconds": seconds,
        "seconds_per_subject": round(seconds / n_subjects, 2) if n_subjects else None,
        "github_calls_measured": measured,
        "github_calls_absent_reason": reason,
        "remaining_before": before["remaining"] if before else None,
        "remaining_after": after["remaining"] if after else None,
        "limit": reference["limit"] if reference else None,
        "reset_at": (datetime.fromtimestamp(reference["reset"], tz=timezone.utc)
                     .isoformat(timespec="seconds") if reference else None),
        "waited_seconds": waited_seconds,
    }
