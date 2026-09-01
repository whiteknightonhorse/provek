"""Q-M2 measurement: the cost of continuously verifying one project.

WHY THIS DECIDES THE BUSINESS MODEL (ABI-5-5, ABI-29-5). Verification is a RECURRING cost while a
fee is charged once. If the cost per project per month exceeds what anyone will pay, the model
INVERTS at scale: the more customers, the worse the position. Measuring this before pricing is the
difference between a business and a hope.

WHAT IS MEASURED: wall time, CPU time, peak RSS, and the number of external calls for one full
pass over one subject. What is NOT measured: the price of an API call in money - that depends on a
plan we have not chosen, and inventing it would be exactly the guessed constant this project
forbids.
"""
import os
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# A BARE ASSIGNMENT DOES NOT BELONG ABOVE THESE IMPORTS. Hoisting the repository root into a
# constant here is the obvious tidy-up and it turns the whole import block red: ruff exempts
# `sys.path` manipulation from E402 and nothing else, so one extra statement makes every import
# below it a violation. The root is therefore derived where it is used, further down.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.identity import Binding, BindingKind
from src.abs_profile.ladder import L
from src.abs_profile.measured import NotMeasured
from src.collector import github as gh
from src.collector.declaration import apply_declaration
from src.passport.passport import (
    PROFILE_VERSION,
    PROTOCOL_VERSION,
    Passport,
    Provenance,
    build,
)
from src.registry.public_registry import PublicRegistry, Row
from src.transport.file_transport import FileTransport
from src.verify.control_map import Capability, ControlMap, ControlPath, Surface, build_coverage
from src.verify.scorer import Confidence, OperationScore, projection, score_operation

SUBJECTS = ["whiteknightonhorse/gov-auction-report",
            "whiteknightonhorse/mcp-protocol-tester",
            "whiteknightonhorse/AIpush"]

# Count external calls without touching the collector: wrap its one network primitive.
_calls = {"n": 0}
_orig = gh._api


def counting_api(path, token):
    _calls["n"] += 1
    return _orig(path, token)


gh._api = counting_api

# THE OUTPUT ROOT IS THE PROJECT'S, NOT THE HOST'S SHARED /tmp (T-S6).
#
# This read `Path("/tmp/_qm2out")`, and it is not a scratch path: `FileTransport` and
# `PublicRegistry` write the passports and the registry of this measurement underneath it. `/tmp`
# here is mode 1777 and shared with nine other projects, so whoever creates `_qm2out` first owns
# it - and a neighbour who created it as a symlink would receive our output, or hand us theirs to
# read back as a measurement. A permission refusal is visible; a successful read of somebody
# else's artefact is not, and that is what makes a fixed name in a world-writable directory
# different in kind from a temporary directory. `tempfile.mkdtemp()` stays fine and is used
# elsewhere in this tree: it creates a 0700 directory under an UNPREDICTABLE name, which is the
# property that was missing here.
out = Path(__file__).resolve().parents[1] / ".state" / "qm2"
transport, registry = FileTransport(out), PublicRegistry(out)

def optional_token() -> str | None:
    """A credential is NOT required, and that is the point.

    THE VIOLATION THIS REPLACES (Fable, V1). Until 2026-08-20 both emitters opened with:

        subprocess.run(["sudo", "grep", "-ohE", "gh[pous]_[A-Za-z0-9_]+",
                        "/home/audiobook2/.claude/gh.env"], ...)

    - a regex over token shapes, run as root, against a NEIGHBOURING project's private file.
    Master spec 10.2 and ADR-0006 forbid it: a subject is read through the same channel an external
    subject would grant, because a methodology that reads its subject as root cannot be reproduced
    by a third party (ABI-5-3). Every passport published before that date descends from it, and
    they are kept under `evidence/TAINTED-SUDO-CORPUS/` rather than deleted.

    Fable ruled the remedy was a hand-issued scoped read-only token. Measurement found a stricter
    answer and it is what ships: every call this pipeline makes is a PUBLIC read that returns 200
    with no credential - that much still holds. What does NOT still hold is the count first
    written here: "all three calls... return 200... a full cohort costs 24 of the 60 anonymous
    requests." Re-measured 2026-08-24 against the live API (same correction as `_api` in
    src/collector/github.py; see evidence/RED-037-*): `whiteknightonhorse/gov-auction-report` now
    answers 404, not 200, and a 404 short-circuits `collect_github` after the FIRST call - so the
    three subjects in SUBJECTS above cost 3 + 3 + 1 = 7 calls per pass, not the flat 3-per-subject
    this docstring assumed. So the default channel holds nothing at all - reproducible by any
    reader, not merely by one the operator has chosen to grant. Raised to Fable as a strengthening
    of his ruling, not a departure from it.

    A token is honoured when present, purely to widen the rate limit for a larger cohort. It never
    changes what is measured, and the passport records which channel was used so that "anyone can
    recompute this" is a published fact rather than an assumption.
    """
    return os.environ.get("PROVEK_GITHUB_TOKEN", "").strip() or None


# PROTOCOL_VERSION and PROFILE_VERSION imported, not written as literals (LAW #ONE-PLACE, Fable,
# 2026-09-01) - this line stamped "1.0.0" / "1.0.0" on every passport this script emits, a stale
# value: `scripts/cohort.py` had already moved to profile 1.1.0. `src/passport/passport.py` is the
# canonical source now, and all three emitters read from it.
PROV = Provenance(PROTOCOL_VERSION, PROFILE_VERSION, 30)
COV = build_coverage(github_inspected=True)

def score_subject(ev: gh.GitHubEvidence, cmap: ControlMap) -> OperationScore:
    """The `development_initiation` score for one subject's evidence.

    `ev.read` is the COLLECTOR's own finding - the subject answered us, or it did not - and it is
    not optional input to this decision, it is the first thing this function must ask (T-S8,
    Fable). The line this replaces asked a different question ("is `distinct_authors`
    measured?") and got the same answer for two different reasons: a subject with two committers
    and a subject that returned 404 both leave `distinct_authors` unmeasured, and the `else`
    branch could not tell them apart. It fell back to `L.L3` for both, so
    `whiteknightonhorse/gov-auction-report` - which answers 404 to an anonymous reader, reproduced
    in evidence/RED-037-* - was scored `level: L2` (after the weak-signal cap), `measured: true`,
    `projection: 40`. A subject the collector never read cannot ALSO be scored: that is the
    scorer manufacturing a number invariant 1 says only a collector may withhold or grant.
    """
    if not ev.read:
        return OperationScore("development_initiation", NotMeasured.UNREADABLE, (),
                              Confidence.MEASURED)
    lvl = L.L4 if (ev.distinct_authors.is_measured and ev.distinct_authors.value == 1) else L.L3
    return score_operation("development_initiation", lvl,
                           (EvidenceClass.PLATFORM_OBSERVED,), cmap.implied_level_cap(),
                           weak_mixed_signal=True, runtime_trace=ev.has_runtime_trace)


def registry_row(subject_id: str, p: Passport, ref: str) -> Row:
    """The registry row one measured subject would produce - pulled out of the loop for the same
    reason `score_subject` was (T-S8): a test can check it against a built passport with no
    network call, instead of only being exercisable by running the whole script live.
    """
    m = p.to_machine()
    return Row(subject_id=subject_id, status=p.status,
              projection=m["verified"]["projection"],
              absent_reason=m["verified"]["projection_absent_reason"],
              protocol_version=PROV.protocol_version, valid_until=p.valid_until,
              passport_ref=ref, verifier_affiliation="same_owner")


if __name__ == "__main__":
    rows = []
    for full in SUBJECTS:
        _calls["n"] = 0
        t0, c0 = time.time(), time.process_time()
        r0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        ev = gh.collect_github(full, optional_token())
        b = Binding(BindingKind.GIT, full)
        cmap = ControlMap([ControlPath(Surface.GITHUB, Capability.IMPROVE_OR_FIX, True)], COV)
        scores = [score_subject(ev, cmap),
                  score_operation("deployment", None, ()),
                  score_operation("treasury_control", None, ())]
        # PHASE 2 - same mapper as `src/pipeline.py` and `scripts/cohort.py` (LAW #ONE-PLACE),
        # pinned to `ev.head_sha` already measured above.
        accountability, claims = apply_declaration(full, ev.head_sha, None)
        p = build(b, scores, cmap, projection(scores), PROV, accountability,
                  claims=claims, verifier_affiliation="same_owner")
        ref = transport.publish(b.as_subject_id(), p.to_machine(),
                                p.to_machine()["verified"]["projection"])
        # A REAL PASS PUBLISHES TO THE REGISTRY, NOT ONLY THE PASSPORT (T-S10). Building a passport
        # and never upserting it into the registry undercounts "one full verification pass" by the
        # one step production's `pipeline.verify()` always takes after `transport.publish`. Timed
        # inside the loop, same as everything else here, so the number this script reports is the
        # per-project cost a continuously-running verifier actually pays.
        registry.upsert(registry_row(b.as_subject_id(), p, ref))
        registry.write(datetime.now(timezone.utc))

        rows.append({"subject": full.split("/")[1],
                     "read": ev.read,
                     "wall_s": round(time.time() - t0, 2),
                     "cpu_s": round(time.process_time() - c0, 3),
                     "api_calls": _calls["n"],
                     "rss_delta_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - r0})

    print("=== Q-M2: cost of ONE verification pass ===")
    print("%-28s %-5s %8s %8s %6s %10s" % ("subject", "read", "wall s", "cpu s", "calls", "rss dKB"))
    for r in rows:
        print("%-28s %-5s %8s %8s %6s %10s" % (r["subject"], r["read"], r["wall_s"], r["cpu_s"],
                                              r["api_calls"], r["rss_delta_kb"]))

    avg_wall = sum(r["wall_s"] for r in rows) / len(rows)
    avg_cpu = sum(r["cpu_s"] for r in rows) / len(rows)
    avg_calls = sum(r["api_calls"] for r in rows) / len(rows)
    print()
    print("average per pass: wall %.2f s | cpu %.3f s | api calls %.1f"
          % (avg_wall, avg_cpu, avg_calls))
    print()
    for freq, label in ((1, "daily"), (1 / 7, "weekly"), (1 / 30, "monthly")):
        per_month = 30 * freq
        print("at %-8s re-verification: %.0f passes/month -> %.1f cpu-s, %.0f api calls per project"
              % (label, per_month, per_month * avg_cpu, per_month * avg_calls))
    print()
    print("GitHub API budget: 5000 calls/hour for a token. At daily re-verification one project costs")
    print("%.0f calls/month, so the token supports roughly %.0f projects before rate limits bind."
          % (30 * avg_calls, 5000 * 24 * 30 / max(1e-9, 30 * avg_calls)))
