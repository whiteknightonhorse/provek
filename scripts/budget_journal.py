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

import re
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


NEED_LOOKBACK_ROWS = 7
"""ASSIGNED (T-GHB-01, 2026-11-16). How many of the latest journal rows `night_need` looks at. Measured:
the call count moved by at most 2 between consecutive nights, 2026-10-27..2026-11-16, so a week
is long enough to hold the largest recent night and short enough to forget a cost long gone."""

NEED_MARGIN_CALLS = 3
"""ASSIGNED (T-GHB-01, 2026-11-16). Calls added on top of the largest recent count. Measured: the
count moved by at most 2 between consecutive nights, 2026-10-27..2026-11-16; three covers one
step more than the largest move seen."""


def night_need(rows: list[dict]) -> int | None:
    """Calls the coming night needs: the largest non-null `github_calls_measured` in the last
    `NEED_LOOKBACK_ROWS` journal rows plus `NEED_MARGIN_CALLS`. None when no row in the lookback has
    a number - an unmeasured need is not a need of zero, and the caller then keeps the old rule."""
    counts = [r.get("github_calls_measured") for r in rows[-NEED_LOOKBACK_ROWS:]]
    counts = [c for c in counts if isinstance(c, int)]
    return max(counts) + NEED_MARGIN_CALLS if counts else None


def wait_seconds_for(core: dict | None, now_epoch: int, need: int | None = None) -> int:
    """How long to wait, ONCE, before spending a budget too small for the night.

    `need is None` keeps the T-76 rule: wait only when `remaining == 0`. Given a need (T-GHB-01),
    wait when `remaining < need`. Bounded by the field it reads, not by a constant: `reset` always
    falls inside the current hourly window, so this can never ask for more than an hour. Zero - no
    wait - when the budget has room, when `reset` has already passed (a stale read), when
    `/rate_limit` could not be read (an unreadable instrument is not an empty budget, the same
    distinction `parse_core` draws), and when `need > limit`: no window can hold that night, a wait
    cannot help, and the run's own stop reports it.

    Callers check ONCE, wait this many seconds if positive, and re-check ONCE after - never loop
    here. A budget still short the instant the window reopens is a fact worth reporting, not a
    reason to sleep a second hour unattended.
    """
    if core is None:
        return 0
    if need is None:
        short = core["remaining"] == 0
    else:
        short = core["remaining"] < need <= core["limit"]
    return max(0, core["reset"] - now_epoch) if short else 0


def preflight(core: dict | None, rows: list[dict], now_epoch: int) -> dict:
    """Everything the nightly pre-flight prints, from one read and the journal (T-GHB-01).

    `window_opened` is `reset` minus the 3600 s window, as ISO UTC; None when the read failed.
    """
    need = night_need(rows)
    return {
        "wait": wait_seconds_for(core, now_epoch, need),
        "need": need,
        "remaining": core["remaining"] if core else None,
        "limit": core["limit"] if core else None,
        "window_opened": (datetime.fromtimestamp(core["reset"] - 3600, tz=timezone.utc)
                          .strftime("%Y-%m-%dT%H:%M:%SZ") if core else None),
    }


def parse_cost_line(text: str) -> int | None:
    """The LAST `COST github_calls=<n>` line `scripts/cohort.py` printed, or None when the run
    never got that far (T-0578). None is `not measured`, never 0: a cohort that died before the
    line made calls nobody counted."""
    found = re.findall(r"^COST github_calls=(\d+)\s*$", text, flags=re.MULTILINE)
    return int(found[-1]) if found else None


def build_cost_row(*, at: datetime, n_subjects: int, seconds: int,
                    before: dict | None, after: dict | None, waited_seconds: int,
                    counted: int | None = None, need: int | None = None) -> dict:
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

    T-0578: `counted` is the run's own call count (the `COST github_calls=N` line `cohort.py`
    prints from the counter in `_api`). When given it IS `github_calls_measured` and the reason is
    None - a counter inside the one door cannot straddle the hourly reset. The two `/rate_limit`
    reads stay in the row as a cross-check, and their difference is kept as
    `github_calls_rate_limit_delta` (None when it cannot be trusted).

    T-GHB-01: `reset_before`/`reset_after` keep the window each read belonged to (`reset_at`, the
    window of the read after the run, stays); `need` is what the pre-flight waited for, or None.
    """
    reason: str | None = None
    measured: int | None = None
    if before is None or after is None:
        reason = "rate_limit_endpoint_unreadable"
    elif after["limit"] != before["limit"] or after["reset"] != before["reset"]:
        reason = "window_reset_during_run"
    else:
        measured = before["remaining"] - after["remaining"]

    delta = measured
    if counted is not None:
        measured, reason = counted, None

    def _iso(core: dict | None) -> str | None:
        return (datetime.fromtimestamp(core["reset"], tz=timezone.utc).isoformat(timespec="seconds")
                if core else None)

    reference = after or before
    return {
        "at": at.isoformat(timespec="seconds"),
        "subjects": n_subjects,
        "seconds": seconds,
        "seconds_per_subject": round(seconds / n_subjects, 2) if n_subjects else None,
        "github_calls_measured": measured,
        "github_calls_absent_reason": reason,
        "github_calls_rate_limit_delta": delta,
        "remaining_before": before["remaining"] if before else None,
        "remaining_after": after["remaining"] if after else None,
        "limit": reference["limit"] if reference else None,
        "reset_at": (datetime.fromtimestamp(reference["reset"], tz=timezone.utc)
                     .isoformat(timespec="seconds") if reference else None),
        "waited_seconds": waited_seconds,
        # T-GHB-01: the window each read belonged to, and the need the pre-flight waited for.
        "reset_before": _iso(before),
        "reset_after": _iso(after),
        "need": need,
    }
