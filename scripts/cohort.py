"""Cohort B5: passports for the operator's production systems (T-2.13, ABI-18-3, ABI-31-4).

SELECTION FOLLOWS SPEC 2.7, not "every repository". A subject is an entity with an observable
result of activity and at least one business operation. Forks of awesome-lists are NOT subjects:
they have no business operation, they are link catalogues. Padding the cohort with them would be
exactly the behaviour this product exists to expose.

Every passport carries verifier_affiliation=same_owner - without it the first registry entries
would read as INDEPENDENT verifications.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# The repository root, wherever this clone happens to live. It was the server's absolute path,
# which meant the pipeline only ran on one machine - a quiet contradiction of the anonymous
# channel's whole point, that any reader can recompute a verdict.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.identity import Binding, BindingKind
from src.abs_profile.ladder import SMALL_TEAM_FOR_L3, SOLE_AUTHOR, L
from src.abs_profile.measured import NotMeasured
from src.collector.github import access_channel, collect_github
from src.passport.passport import Accountability, Provenance, build
from src.registry.public_registry import PublicRegistry, Row
from src.transport.file_transport import FileTransport
from src.verify.control_map import Capability, ControlMap, ControlPath, Coverage, Surface
from src.verify.scorer import Confidence, OperationScore, projection, score_operation


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
    written here, copied from measure_qm2.py's three-subject pipeline rather than measured
    against this script's own eight-member COHORT below: "all three calls... return 200... a
    full cohort costs 24 of the 60 anonymous requests." Re-measured 2026-08-24 against the live
    API (same correction as `_api` in src/collector/github.py; see evidence/RED-037-*):
    `whiteknightonhorse/gov-auction-report` - a member of COHORT below - now answers 404, not
    200, and a 404 short-circuits `collect_github` after the FIRST call, breaking the flat
    3-per-subject assumption here too. What that costs THIS script's own eight-subject pass is
    `not_measured`: only the three-subject run in measure_qm2.py was re-run live on 2026-08-24
    (3 + 3 + 1 = 7 calls there), and this file's own total has not been separately re-checked. So
    the default channel holds nothing at all - reproducible by any reader, not merely by one the
    operator has chosen to grant. Raised to Fable as a strengthening of his ruling, not a
    departure from it.

    A token is honoured when present, purely to widen the rate limit for a larger cohort. It never
    changes what is PUBLISHED - that sentence was false when first written and is now enforced by
    the `publishable` rule below, which treats a private subject as unreadable whatever channel we
    hold. The passport records which channel was used, so "anyone can recompute this" is a
    published fact rather than an assumption.
    """
    return os.environ.get("PROVEK_GITHUB_TOKEN", "").strip() or None


# THE LIST LIVES IN data/subjects.json, not here. It was a literal in this file, which meant a
# subject could only be added by editing the program that measures subjects -- and intake has to
# add one without a human opening an editor. Read, never defaulted: a missing file is a refusal,
# because an empty cohort would publish a registry of nothing and read as "we verify no one".
_SUBJECTS = json.loads((Path(__file__).resolve().parents[1] / "data" / "subjects.json")
                        .read_text(encoding="utf-8"))["subjects"]
if not _SUBJECTS:
    raise SystemExit("data/subjects.json lists no subjects; refusing to publish an empty registry")
COHORT = [s["repo"] for s in _SUBJECTS]
AFFILIATION = {s["repo"]: s["affiliation"] for s in _SUBJECTS}

tok = optional_token()

# A TOKEN MAY NOT BUILD A PUBLISHED ARTEFACT. The token was meant to widen the request budget, and
# the docstring of optional_token says it "changes the budget, never the evidence". Measured
# 2026-08-25: that is false of the WRITTEN DOCUMENT. Run with a credential, the passport of a
# PRIVATE subject stops saying `unreadable` and starts carrying values -- signed_commit_share,
# distinct_authors, workflow_runs, head_sha -- that no anonymous reader can recompute. The
# projection stays withheld and the channel is stamped honestly, so nothing lies; but the artefact
# now depends on WHO built it, and every page of this site promises a verdict reproducible by a
# third party from the same inputs.
#
# So the refusal is here, at the point of writing, not in a note asking the operator to remember.
# For diagnostics, copy this script elsewhere and point its output at a scratch directory: the
# limit belongs to what gets PUBLISHED, not to what may be measured.
if tok:
    raise SystemExit(
        "REFUSED: PROVEK_GITHUB_TOKEN is set. A credentialed run writes passports an anonymous "
        "reader cannot reproduce, and reproducibility is the claim this registry makes. Unset it "
        "and wait for the anonymous window if the budget is exhausted.")

out = Path(__file__).resolve().parents[1] / "public"
transport = FileTransport(out / "passports")
registry = PublicRegistry(out / "registry")
now = datetime.now(timezone.utc)
PROV = Provenance("1.0.0", "1.0.0", 30)
SITE = "https://provek.dev"


def observations(ev) -> dict:
    """The measured quantities a level was actually built from.

    The site says it "publishes the evidence behind every number" and it did not: the passport
    carried verdicts, limiters and coverage, and never the observations underneath. Fable offered
    two honest exits - weaken the sentence, or make it true. This is the second, because the
    collector already holds these and withholding them was a choice nobody had made deliberately.

    Every value keeps its own absence state; none of them collapses to a zero.
    """
    def m(x):
        return {"value": x.value, "measured": x.is_measured,
                "absent_reason": None if x.is_measured else x.absent.value}
    return {
        "signed_commit_share": m(ev.signed_commit_share),
        "distinct_authors": m(ev.distinct_authors),
        "bot_author_share": m(ev.bot_author_share),
        "workflow_runs": m(ev.workflow_runs),
        "head_sha": ev.head_sha,
    }


def publishable_source(ev) -> bool:
    """May this subject's evidence enter a PUBLISHED verdict?

    Two conditions, and they are different facts. `ev.read` says the source answered us. `private`
    says it would not answer anyone without a credential - and evidence only we can reach is not
    evidence a third party can recompute (ABI-5-3). Either failing means the same thing for
    publication and different things for the record, which is why both are kept.
    """
    return bool(ev.read) and ev.private is not True

print("%-42s %-7s %-9s %-6s %s" % ("subject", "level", "projection", "CI", "limiters"))
print("-" * 96)

for full in COHORT:
    ev = collect_github(full, tok)
    binding = Binding(BindingKind.GIT, full)

    # THE MAP REPORTS WHAT WAS ACTUALLY INSPECTED (Fable, B2). It used to stamp the same coverage
    # onto every subject, so a passport whose source could not be read still said "Inspected:
    # github" and carried a control-map ceiling of L5 - two claims about one source, on one page,
    # in direct contradiction, three sections apart.
    #
    # When nothing was read, nothing was inspected, and github moves to out_of_reach with the
    # reason. The map is then INVALID by its own rule, which is correct: a map without coverage
    # claims more than it knows, and the passport cannot stand on it.
    if publishable_source(ev):
        coverage = Coverage(
            inspected=[Surface.GITHUB],
            out_of_reach={"server": "runtime not presented by the subject",
                          "treasury": "outside MVP scope",
                          "database": "no access through the chosen channel"},
            unknown_shape="privileged access through a CI secret or account recovery")
        paths = [ControlPath(Surface.GITHUB, Capability.IMPROVE_OR_FIX, recorded=True)]
    else:
        coverage = Coverage(
            inspected=[],
            out_of_reach={"github": "the repository did not answer a reader holding no credential",
                          "server": "runtime not presented by the subject",
                          "treasury": "outside MVP scope",
                          "database": "no access through the chosen channel"},
            unknown_shape="privileged access through a CI secret or account recovery")
        paths = []
    cmap = ControlMap(paths=paths, coverage=coverage)

    lvl = None
    if ev.signed_commit_share.is_measured and ev.distinct_authors.is_measured:
        if ev.distinct_authors.value == SOLE_AUTHOR:
            lvl = L.L4
        elif ev.distinct_authors.value <= SMALL_TEAM_FOR_L3:
            lvl = L.L3
        else:
            lvl = L.L2

    # The evidence tuple is a CLAIM that platform-observed evidence exists. When the repository
    # did not answer, passing it anyway made the scorer say `nothing_qualified` - "we looked and
    # none of it counted" - about a source that had refused to speak to us. Pass what we actually
    # hold, and let the collector's own finding stand.
    # NEW-2 (Fable). `ev.read` alone is not the test. Run this with a token that can see the
    # operator's private repositories and all five of them return 200, read cleanly, and publish as
    # `verified` with projections - verdicts no anonymous reader could ever reproduce. That is the
    # sudo hole reopened in softer clothes: evidence reachable only through a privileged channel.
    #
    # THE RULE: evidence entering a published verdict must be anonymously reproducible. A private
    # subject is therefore unreadable FOR SCORING regardless of what we hold. The collector still
    # records honestly that it read - that is a fact about us - and the cohort refuses to publish
    # what only a credential could see, which is a fact about the verdict.
    publishable = publishable_source(ev)
    observed = (EvidenceClass.PLATFORM_OBSERVED,) if publishable else ()
    dev = (score_operation("development_initiation", lvl, observed, cmap.implied_level_cap(),
                           weak_mixed_signal=True, runtime_trace=ev.has_runtime_trace)
           if publishable else
           OperationScore("development_initiation", NotMeasured.UNREADABLE, (), Confidence.MEASURED))
    scores = [dev,
              score_operation("deployment", None, ()),
              score_operation("treasury_control", None, ())]
    proj = projection(scores)
    p = build(binding, scores, cmap, proj, PROV, Accountability(),
              # A self-reported block states what the SUBJECT said. When the source never
              # answered, the subject said nothing, and an omitted key is the honest rendering of
              # that - a `false` here was the template speaking in the subject's name.
              now=now,
              claims=({"source": "github", "private": ev.private} if ev.read
                      else {"source": "github"}),
              observations=observations(ev),
              # PER SUBJECT. `same_owner` on an applicant's passport would claim the verifier and
              # the subject are the same person, which is false and understates their verdict; the
              # self-mandate is ours and means nothing on a repository we do not own.
              mandate_ref=("self-mandate-0001" if AFFILIATION[full] == "same_owner" else None),
              verifier_affiliation=AFFILIATION[full],
              access_channel=access_channel(tok))
    m = p.to_machine()
    # The return value is deliberately dropped, and the call is not: publishing is the side effect
    # that puts the machine record where the row below points. The handle it returns was the
    # server-side path, and nothing has read it since `passport_ref` stopped being that path (see
    # the note under this line) - so binding it to a name was a reader that no longer exists.
    # CodeQL #9, `py/unused-global-variable`.
    transport.publish(binding.as_subject_id(), m, m["verified"]["projection"])
    # protocol_version, not SCHEMA_VERSION (Fable, R2). Those are different quantities that happen
    # to be version strings, and a fix of mine swapped one for the other because the names sit next
    # to each other: the registry then published protocol 2.0.0 for verdicts whose passports say
    # 1.0.0. Read it from the same Provenance object the passport uses, so the two cannot diverge
    # again.
    #
    # passport_ref was the server's filesystem path, published to the world (Fable, I4): useless to
    # a consumer, leaking our layout, and the registry's ONLY pointer to the document it lists. It
    # is now the URL of the machine record, which exists today and is fetchable.
    slug = binding.as_subject_id().replace(":", "_").replace("/", "_")
    # A subject nothing was measured on is NOT verified. The registry said `verified` for five
    # rows whose projection was null - a status asserting a completed verification beside a field
    # saying none happened, in the same row.
    # THE PASSPORT'S OWN STATUS, not a second computation of it. This line derived its own answer
    # from the projection and diverged the moment `_status` learned about invalid maps: the row
    # said `unverified` while the document it links to said `verification_in_progress`. That is
    # NEW-1 recurring, in the fix for NEW-1's sibling. One rule, one place, both artefacts reading
    # from it.
    registry.upsert(Row(binding.as_subject_id(), p.status,
                        m["verified"]["projection"], m["verified"]["projection_absent_reason"],
                        PROV.protocol_version, p.valid_until,
                        f"{SITE}/data/passports/{slug}.json",
                        verifier_affiliation=p.verifier_affiliation))

    op = m["verified"]["operations"][0]
    lim = ",".join(scores[0].limiters_applied) or "-"
    ci = ev.workflow_runs.value if ev.workflow_runs.is_measured else "n/a"
    print("%-42s %-7s %-9s %-6s %s" % (full.split("/")[1][:40], op["level"],
                                       m["verified"]["projection"], ci, lim))

written = registry.write(now)
print("\nregistry:", written)

# MIRROR TO WHAT IS ACTUALLY SERVED. This script wrote `public/`; the site and prerender.mjs read
# `web/public/data/`. Both trees are tracked, both are judged -- by DIFFERENT tests -- and nothing
# copied one to the other. A human did, by hand, every time. That is one artefact with two homes
# and no writer, which is the shape this project has paid for repeatedly; left alone it would have
# let intake publish verdicts into a file no reader is ever served.
served = Path(__file__).resolve().parents[1] / "web" / "public" / "data"
(served / "passports").mkdir(parents=True, exist_ok=True)
mirrored = 0
for src in sorted((out / "passports").glob("*.json")):
    (served / "passports" / src.name).write_bytes(src.read_bytes())
    mirrored += 1
(served / "registry.json").write_bytes((out / "registry" / "registry.json").read_bytes())
print(f"mirrored to served tree: registry.json + {mirrored} passport(s)")
