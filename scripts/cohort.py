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
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# The repository root, wherever this clone happens to live. It was the server's absolute path,
# which meant the pipeline only ran on one machine - a quiet contradiction of the anonymous
# channel's whole point, that any reader can recompute a verdict.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.identity import Binding, BindingKind
from src.abs_profile.ladder import SIGNED_SHARE_FOR_L4, SMALL_TEAM_FOR_L3, SOLE_AUTHOR, L
from src.abs_profile.measured import NotMeasured
from src.collector.declaration import apply_declaration
from src.collector.github import EVIDENCE_WINDOW_DAYS, RateLimited, access_channel, collect_github
from src.passport.passport import PROFILE_VERSION, PROTOCOL_VERSION, Provenance, build
from src.registry.public_registry import PublicRegistry, Row
from src.transport.file_transport import FileTransport
from src.verify.control_map import (
    GITHUB_DID_NOT_ANSWER,
    GITHUB_PARTIAL_READ,
    Capability,
    ControlMap,
    ControlPath,
    Surface,
    build_coverage,
)
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

# INCREMENTAL MODE, and it exists because of arithmetic, not taste. Scoring one subject costs three
# anonymous GitHub calls and the anonymous budget is 60 an hour, so a full pass over N subjects
# costs 3N. At today's eight that is 24 and a rebuild is cheap; at nineteen it is 57, which is one
# pass per hour -- and intake promises an applicant a registry entry within fifteen minutes. A
# design that only works while the registry is small is a design that breaks on success.
#
# So PROVEK_ONLY measures the named subjects and PRELOADS every other row from the registry that is
# already published, instead of re-deriving it. The rows carried forward are not re-asserted: they
# keep the valid_until they were issued with, and `to_machine` downgrades a verified row to stale
# once that passes. Carrying a row forward therefore cannot silently refresh it.
#
# A full pass still has to happen -- that is the daily refresh, run when the budget allows.
ONLY = [r.strip() for r in os.environ.get("PROVEK_ONLY", "").split(",") if r.strip()]
if ONLY:
    unknown = [r for r in ONLY if r not in AFFILIATION]
    if unknown:
        raise SystemExit(f"REFUSED: PROVEK_ONLY names subjects absent from data/subjects.json: "
                         f"{unknown}. A verdict may not be published for a subject the list does "
                         f"not carry -- that is where affiliation and provenance come from.")
    COHORT = ONLY

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

def previous_rows() -> dict:
    """The registry as it was last PUBLISHED - the only record of those verdicts.

    Read unconditionally now, because TWO callers need it: a one-subject run, which must not
    erase the rest, and a subject whose re-measure was cut short by our own exhausted budget,
    whose old row must stand rather than vanish.
    """
    from src.registry.public_registry import Status
    prev = out / "registry" / "registry.json"
    if not prev.is_file():
        return {}
    rows = {}
    for _r in json.loads(prev.read_text(encoding="utf-8"))["subjects"]:
        rows[_r["subject_id"]] = Row(
            _r["subject_id"], Status(_r["status"]), _r["projection"],
            _r["projection_absent_reason"], _r["protocol_version"],
            datetime.fromisoformat(_r["valid_until"]), _r["passport_ref"],
            verifier_affiliation=_r["verifier_affiliation"])
    return rows


PREVIOUS = previous_rows()
RATE_LIMITED: list[str] = []


def skip_rate_limited(subject_id: str, why: Exception) -> None:
    """Our budget ran out mid-subject. Publish NOTHING new about them.

    The previously published row is carried forward unchanged: it is stale, and it is TRUE. A row
    DELETED because we could not re-read it would report a measured subject as never measured; a
    row REBUILT from the partial read would report our spent budget as their silence. Both are
    worse than yesterday's answer.

    Staleness is not hidden by this. The row keeps its own `valid_until`, and the nightly
    re-measure fails its expiry invariant on a row that stops being refreshed - which is exactly
    the alarm that should fire if the budget stays exhausted.
    """
    print(f"{subject_id:<42} RATE-LIMITED - no passport issued: {why}")
    RATE_LIMITED.append(subject_id)
    prev = PREVIOUS.get(subject_id)
    if prev is not None:
        registry.upsert(prev)


if ONLY:
    for _sid, _row in PREVIOUS.items():
        if _sid.removeprefix("git:") in ONLY:
            continue                          # about to be re-measured; do not carry the old row
        registry.upsert(_row)
    print(f"carried forward: {len(registry._rows)} already-published row(s)")
now = datetime.now(timezone.utc)
# PROFILE 1.1.0: the evidence window became the window that was published, and identity
# resolution became the platform's job rather than ours. A passport must say which ruleset read
# it, or a corrected document is indistinguishable from a changed subject.
#
# PROTOCOL_VERSION and PROFILE_VERSION imported, not written here as literals (LAW #ONE-PLACE,
# Fable, 2026-09-01) - this line used to be the one place that had the right value, while
# `src/pipeline.py` and `scripts/measure_qm2.py` each carried a different, stale one.
PROV = Provenance(PROTOCOL_VERSION, PROFILE_VERSION, EVIDENCE_WINDOW_DAYS)
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
        # PUBLISHED SO THE CLOSURE CAN BE RECOMPUTED, not just the count that came out of it.
        # Without these a reader sees `distinct_authors: 1` and cannot tell a genuinely
        # sole-authored repository from one whose commits nothing vouches for.
        "identity_window_closed": m(ev.identity_window_closed),
        "unlinked_commit_share": m(ev.unlinked_commit_share),
        "unlinked_key_count": m(ev.unlinked_key_count),
        "head_sha": ev.head_sha,
    }


def cohort_development_initiation_level(distinct_authors, signed_commit_share,
                                          identity_window_closed) -> L | None:
    """Level for "development initiation" - the COHORT's own procedure.

    Deliberately not `src.pipeline._observed_level` - see `SMALL_TEAM_FOR_L3`'s docstring for why
    two procedures exist at all (the cohort does not weigh signatures for L3, so it needs a wider
    band - <=3 instead of <=2 - to reach the same conclusion from less).

    DEFECT FIXED HERE (Fable, 2026-08-31, not a new ratification). Until this fix, `SOLE_AUTHOR`
    alone reached L4 in this function while `pipeline.verify` additionally required
    `SIGNED_SHARE_FOR_L4` - the rule actually published on provek.dev. A cohort computed from LESS
    evidence (no signature weighing) was handing out a STRONGER verdict than the pipeline computed
    from MORE evidence, for identical inputs: APIbase (signed_commit_share=0.0, distinct_authors=1)
    scored L4 here and L3 in `pipeline.verify`. The ratified compensation for "the cohort does not
    weigh signatures" is `SMALL_TEAM_FOR_L3`'s wider band - it widens what reaches L3. Nothing
    ratified widening what reaches L4; that requirement was silently dropped and is reinstated
    below, so the two procedures now agree at the one rung where they must.

    SIGNED_COMMIT_SHARE NOT MEASURED (ABI-33-4: inability to measure never yields a NEGATIVE
    verdict, chosen deliberately over the alternative reading). The old code required BOTH
    `distinct_authors` and `signed_commit_share` to be measured before assigning ANY level, so an
    unmeasured signature share withheld even the L3 verdict a sole author already supports without
    any signature evidence at all - more punitive than the absence requires. Here, only the CLAIM
    TO L4 needs the signature: a sole author whose signature share is unmeasured falls through to
    the L3 (or L2) rung that distinct_authors alone can support, rather than being withheld
    outright. A rung that needs no signature evidence should not be denied for the absence of one.
    """
    if not distinct_authors.is_measured:
        return None
    # PLATFORM CLOSURE (Fable, 2026-08-25) - unchanged by this fix. The author count is only an
    # author COUNT when every non-bot commit in the window was attributed by the platform or by a
    # signature; otherwise it is a LOWER BOUND, and the floor - not "not measured" - is the honest
    # answer to an open window (see the fuller note this replaced, in git history at this line).
    if not (identity_window_closed.is_measured and identity_window_closed.value):
        return L.L2
    if (distinct_authors.value == SOLE_AUTHOR
            and signed_commit_share.is_measured
            and signed_commit_share.value >= SIGNED_SHARE_FOR_L4):
        return L.L4
    if distinct_authors.value <= SMALL_TEAM_FOR_L3:
        return L.L3
    return L.L2


def publishable_source(ev) -> bool:
    """May this subject's evidence enter a PUBLISHED verdict?

    Two conditions, and they are different facts. `ev.read` says the source answered us. `private`
    says it would not answer anyone without a credential - and evidence only we can reach is not
    evidence a third party can recompute (ABI-5-3). Either failing means the same thing for
    publication and different things for the record, which is why both are kept.
    """
    return bool(ev.read) and ev.private is not True


def reads_completed(ev) -> bool:
    """Did the reads THIS VERDICT RESTS ON actually finish?

    Deliberately not `publishable_source`, which answers a different question - may this evidence
    enter a published verdict. A subject can pass that while the reads feeding the level never
    landed: the repository answers 200, the commits page does not, and the passport then prints
    "Inspected: github" three sections away from three measurements saying the source was never
    read. Both claims sit on one page and only one can be true.

    Coverage reports the READING. Scoring keeps its own rule, and this function does not touch it:
    `Coverage` feeds no ceiling and no level (measured 2026-09-01 - zero references to coverage in
    the scorer). Saying so matters because we are a subject in our own registry, and a change that
    moved our own number would need a different kind of scrutiny than one that cannot.
    """
    return publishable_source(ev) and not any(
        m.absent is NotMeasured.UNREADABLE
        for m in (ev.distinct_authors, ev.signed_commit_share, ev.identity_window_closed))

print("%-42s %-7s %-9s %-6s %s" % ("subject", "level", "projection", "CI", "limiters"))
print("-" * 96)

for full in COHORT:
    try:
        ev = collect_github(full, tok)
    except RateLimited as e:
        skip_rate_limited(f"git:{full}", e)
        continue
    binding = Binding(BindingKind.GIT, full)

    # THE MAP REPORTS WHAT WAS ACTUALLY INSPECTED (Fable, B2). It used to stamp the same coverage
    # onto every subject, so a passport whose source could not be read still said "Inspected:
    # github" and carried a control-map ceiling of L5 - two claims about one source, on one page,
    # in direct contradiction, three sections apart.
    #
    # `build_coverage` (LAW #ONE-PLACE, Fable, 2026-09-01) replaces the coverage dict this used to
    # hand-roll per branch: it and `scripts/measure_qm2.py`'s COV and `src/pipeline.py`'s default
    # each carried their own copy of "deployment": "collector not implemented", drifted in wording
    # and, in two of the four call sites, missing the `deployment` key outright.
    publishable = publishable_source(ev)
    coverage = build_coverage(
        github_inspected=reads_completed(ev),
        github_absent_reason=(GITHUB_DID_NOT_ANSWER if not publishable else GITHUB_PARTIAL_READ))
    paths = [ControlPath(Surface.GITHUB, Capability.IMPROVE_OR_FIX, recorded=True)] if publishable else []
    cmap = ControlMap(paths=paths, coverage=coverage)

    lvl = cohort_development_initiation_level(
        ev.distinct_authors, ev.signed_commit_share, ev.identity_window_closed)

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
    # `publishable` was already computed above, for `build_coverage` - same finding, one call.
    observed = (EvidenceClass.PLATFORM_OBSERVED,) if publishable else ()
    # `absent_reason=ev.distinct_authors.absent` (Fable, 2026-09-01): `lvl` is None exactly when
    # `ev.distinct_authors` is unmeasured (see `cohort_development_initiation_level` above), and
    # the collector already knows WHY - `no_evidence_in_window` for an empty thirty-day read,
    # `unreadable` if the commit history itself refused to answer even though the repository did
    # not. `score_operation` cannot see the collector's Measurement, only the boolean fact that the
    # level came back None, and its own guess (`nothing_qualified`) was publishing the wrong one:
    # AIpush and mcp-protocol-tester were genuinely read with an empty evidence window, and the
    # guess let `check_did_not_run` from the two always-unattempted operations below win the
    # registry's headline reason instead. Harmless when `lvl` is a real level - the scorer only
    # consults this in the branch where the level is absent.
    dev = (score_operation("development_initiation", lvl, observed, cmap.implied_level_cap(),
                           weak_mixed_signal=True, runtime_trace=ev.has_runtime_trace,
                           absent_reason=ev.distinct_authors.absent)
           if publishable else
           OperationScore("development_initiation", NotMeasured.UNREADABLE, (), Confidence.MEASURED))
    scores = [dev,
              score_operation("deployment", None, ()),
              score_operation("treasury_control", None, ())]
    proj = projection(scores)
    # PHASE 2 - the subject's own `provek.json`, pinned to `ev.head_sha` (already measured above;
    # never a second `/commits` call). Reads through `raw.githubusercontent.com`, which spends no
    # `api.github.com` budget, so this runs for every subject regardless of `publishable` - the
    # four-world mapper already turns an unreachable or absent declaration into an honest state.
    base_claims = {"source": "github", "private": ev.private} if ev.read else {"source": "github"}
    try:
        accountability, claims = apply_declaration(full, ev.head_sha, base_claims)
    except RateLimited as e:
        # Nothing is written before this point in the loop body - the passport is emitted below
        # and the row upserted after it - so `continue` here leaves no half-issued document.
        skip_rate_limited(f"git:{full}", e)
        continue
    p = build(binding, scores, cmap, proj, PROV, accountability,
              # A self-reported block states what the SUBJECT said. When the source never
              # answered, the subject said nothing, and an omitted key is the honest rendering of
              # that - a `false` here was the template speaking in the subject's name.
              now=now,
              claims=claims,
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

# THE README FRAGMENT IS EMITTED, NOT PASTED - the same defect as the mirror above, one artefact
# further out. `public/passports/<name>.json` had THREE homes: the emitted file, the served tree
# (fixed above), and a fenced block in README.md that a human re-copied by hand. On 2026-08-25 the
# nightly re-measure raised APIbase from L2 to L4 and nobody re-copied, so
# `test_readme_fragment_is_verbatim` went red - correctly - and `scripts/push.sh` refused under
# `set -euo pipefail`. The chain `cohort && commit && push && deploy` stopped at step three, which
# is exactly what a gate is for. The cost was that FIVE DAYS of nightly re-measures never reached
# the site: the live registry served `generated_at: 2026-08-25` while the tree held 2026-08-30, and
# nothing said so.
#
# Writing `L4` into README by hand would fix today and rearm the trap for the next time a passport
# moves. The gate is right; the hand-copy is the defect. So the block is emitted here, from the
# passport THE README ITSELF NAMES, and the test stays exactly as it is - it now judges this
# writer instead of a human's memory.
#
# The section and the link are located with the SAME rules the test applies (heading to next `## `,
# the one `/data/passports/<name>.json` link, the first ```json fence). Deliberately no new
# `<!-- BEGIN -->` markers: a second way of finding the same block is a second thing to keep in
# sync, and the whole point here is that one place decides.
readme = Path(__file__).resolve().parents[1] / "README.md"
_HEADING = "## What a verdict looks like"
_text = readme.read_text(encoding="utf-8")
_start = _text.find(_HEADING)
if _start == -1:
    # Loud, not silent. A renamed section means this writer stopped writing anything, and a silent
    # no-op here would put us back to a hand-copied block with a gate nobody notices passing.
    raise SystemExit(f"cohort: README has no {_HEADING!r} section - the fragment writer has no target")
_end = _text.find("\n## ", _start + len(_HEADING))
_end = len(_text) if _end == -1 else _end
_section = _text[_start:_end]

_names = re.findall(r"/data/passports/([A-Za-z0-9_.-]+\.json)", _section)
if len(set(_names)) != 1:
    raise SystemExit(f"cohort: the {_HEADING!r} section names {sorted(set(_names))} passports, "
                     "so which one the block quotes is ambiguous - the fragment is not written")
_src = out / "passports" / _names[0]
if not _src.is_file():
    raise SystemExit(f"cohort: README attributes the fragment to {_names[0]}, which this run did "
                     "not emit - the cohort changed and the link was not repointed")

_ops = json.loads(_src.read_text(encoding="utf-8"))["passport"]["verified"]["operations"]
# `json.dumps(..., indent=2)` with its default ensure_ascii, because that is the exact call the
# canonical-rendering test makes. Two spellings of "canonical" would be the same divergence again.
_canonical = json.dumps(_ops, indent=2)

_fence = re.search(r"```json\n(.*?)\n```", _section, re.DOTALL)
if _fence is None:
    raise SystemExit(f"cohort: no fenced json block follows {_HEADING!r} - nothing to write into")

if _fence.group(1) == _canonical:
    print("README fragment: already the operations array of %s" % _names[0])
else:
    _new_section = _section[:_fence.start(1)] + _canonical + _section[_fence.end(1):]
    _tmp = readme.with_suffix(".md.tmp")
    _tmp.write_text(_text[:_start] + _new_section + _text[_end:], encoding="utf-8")
    os.replace(_tmp, readme)          # an interrupted write must not leave a truncated README
    print("README fragment: re-emitted from %s (%d operation(s))" % (_names[0], len(_ops)))


# A RATE-LIMITED COHORT IS AN ALARM, NOT A FOOTNOTE.
# The nightly re-measure invokes this as `cohort.py || fail`, so a non-zero exit stops the run
# BEFORE it commits, pushes or deploys, and sends the operator a message. Deliberate: a run that
# could not read part of the cohort must not publish as though it had. Artefacts for the subjects
# that WERE read stay in the working tree for the next successful run to carry.
if RATE_LIMITED:
    raise SystemExit(
        "rate_limited: " + ", ".join(RATE_LIMITED) + "\n"
        "Our budget ran out mid-cohort. No passport was issued for these subjects, and their "
        "previously published rows were carried forward unchanged. Nothing here is a finding "
        "about them.")
