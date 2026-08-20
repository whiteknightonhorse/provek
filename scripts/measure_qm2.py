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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.identity import Binding, BindingKind
from src.abs_profile.ladder import L
from src.collector import github as gh
from src.passport.passport import Accountability, Provenance, build
from src.registry.public_registry import PublicRegistry
from src.transport.file_transport import FileTransport
from src.verify.control_map import Capability, ControlMap, ControlPath, Coverage, Surface
from src.verify.scorer import projection, score_operation

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

out = Path("/tmp/_qm2out")
transport, registry = FileTransport(out), PublicRegistry(out)

TOKEN_HOLDER: dict[str, str] = {}

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
    answer and it is what ships: all three calls this pipeline makes are PUBLIC reads that return
    200 with no credential, and a full cohort costs 24 of the 60 anonymous requests GitHub allows
    per hour. So the default channel holds nothing at all - reproducible by any reader, not merely
    by one the operator has chosen to grant. Raised to Fable as a strengthening of his ruling, not
    a departure from it.

    A token is honoured when present, purely to widen the rate limit for a larger cohort. It never
    changes what is measured, and the passport records which channel was used so that "anyone can
    recompute this" is a published fact rather than an assumption.
    """
    return os.environ.get("PROVEK_GITHUB_TOKEN", "").strip() or None


PROV = Provenance("1.0.0", "1.0.0", 30)
COV = Coverage([Surface.GITHUB], {"server": "runtime not presented"}, "CI secret")

rows = []
for full in SUBJECTS:
    _calls["n"] = 0
    t0, c0 = time.time(), time.process_time()
    r0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    ev = gh.collect_github(full, optional_token())
    b = Binding(BindingKind.GIT, full)
    cmap = ControlMap([ControlPath(Surface.GITHUB, Capability.IMPROVE_OR_FIX, True)], COV)
    lvl = L.L4 if (ev.distinct_authors.is_measured and ev.distinct_authors.value == 1) else L.L3
    scores = [score_operation("development_initiation", lvl,
                              (EvidenceClass.PLATFORM_OBSERVED,), cmap.implied_level_cap(),
                              weak_mixed_signal=True, runtime_trace=ev.has_runtime_trace),
              score_operation("deployment", None, ()),
              score_operation("treasury_control", None, ())]
    p = build(b, scores, cmap, projection(scores), PROV, Accountability(),
              verifier_affiliation="same_owner")
    transport.publish(b.as_subject_id(), p.to_machine(), p.to_machine()["verified"]["projection"])

    rows.append({"subject": full.split("/")[1],
                 "wall_s": round(time.time() - t0, 2),
                 "cpu_s": round(time.process_time() - c0, 3),
                 "api_calls": _calls["n"],
                 "rss_delta_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - r0})

print("=== Q-M2: cost of ONE verification pass ===")
print("%-28s %8s %8s %6s %10s" % ("subject", "wall s", "cpu s", "calls", "rss dKB"))
for r in rows:
    print("%-28s %8s %8s %6s %10s" % (r["subject"], r["wall_s"], r["cpu_s"],
                                      r["api_calls"], r["rss_delta_kb"]))

avg_wall = sum(r["wall_s"] for r in rows) / len(rows)
avg_cpu = sum(r["cpu_s"] for r in rows) / len(rows)
avg_calls = sum(r["api_calls"] for r in rows) / len(rows)
print()
print("average per pass: wall %.2f s | cpu %.3f s | api calls %.1f" % (avg_wall, avg_cpu, avg_calls))
print()
for freq, label in ((1, "daily"), (1 / 7, "weekly"), (1 / 30, "monthly")):
    per_month = 30 * freq
    print("at %-8s re-verification: %.0f passes/month -> %.1f cpu-s, %.0f api calls per project"
          % (label, per_month, per_month * avg_cpu, per_month * avg_calls))
print()
print("GitHub API budget: 5000 calls/hour for a token. At daily re-verification one project costs")
print("%.0f calls/month, so the token supports roughly %.0f projects before rate limits bind."
      % (30 * avg_calls, 5000 * 24 * 30 / max(1e-9, 30 * avg_calls)))
