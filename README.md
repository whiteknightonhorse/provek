# Provek

[![gates](https://github.com/whiteknightonhorse/provek/actions/workflows/gates.yml/badge.svg)](https://github.com/whiteknightonhorse/provek/actions/workflows/gates.yml)
[![codeql](https://github.com/whiteknightonhorse/provek/actions/workflows/codeql.yml/badge.svg)](https://github.com/whiteknightonhorse/provek/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/whiteknightonhorse/provek/badge)](https://scorecard.dev/viewer/?uri=github.com/whiteknightonhorse/provek)

*Each of these is a live run, not a picture — click one and read the run it came from.
[What they do and do not assert](#what-the-badges-assert) is stated below, because a badge is a
claim like any other.*

**Evidence, not claims.** A verification layer that measures, per business operation, how much of a
company actually runs without a human in the loop — and publishes the evidence behind every number,
including what could not be measured.

🔗 **[provek.dev](https://provek.dev)** · [Public registry](https://provek.dev/registry/) · [Method](https://provek.dev/method/)

---

## The problem

Anyone can write "AI-powered" on a landing page. Nobody can currently tell that apart from a company
where machines really do the work. That is not a marketing problem — a competitor can always claim
more loudly. It is a verification problem.

Provek is an [ERC-8004](https://eips.ethereum.org/EIPS/eip-8004) **validator**: the standard supplies
identity and transport, the methodology is ours, and it is published in full so a third party can
recompute any verdict from the same inputs.

## What a verdict looks like

Below is `passport.verified.operations`, taken from
[`/data/passports/git_whiteknightonhorse_APIbase.json`](https://provek.dev/data/passports/git_whiteknightonhorse_APIbase.json).
It is the complete array — all three operations, nothing dropped, nothing reshaped and nothing
reordered — extracted from that subtree and re-serialised with `json.dumps(..., indent=2)`. In the
served file the same array sits three levels deeper, attached to its `"operations":` key and
followed by a comma; those are the differences, and they are the whole of them. It is one subtree
of a passport, not a whole one: the rest carries `self_reported`, `accountability` and provenance
at `passport.*`, and coverage at `passport.verified.coverage`.

```json
[
  {
    "operation": "development_initiation",
    "level": "L4",
    "measured": true,
    "confidence": "inferred",
    "limiters_applied": [
      "O1:mixed_classes->inferred"
    ]
  },
  {
    "operation": "deployment",
    "level": "check_did_not_run",
    "measured": false,
    "confidence": null,
    "limiters_applied": []
  },
  {
    "operation": "treasury_control",
    "level": "check_did_not_run",
    "measured": false,
    "confidence": null,
    "limiters_applied": []
  }
]
```

> This block used to be introduced as *"Real output, from the live registry — not an example"*, and
> it was neither. It came from a passport rather than the registry, and its shape existed in no
> artefact: `status` and `verifier_affiliation` sit at `passport.*` while `operations` sits two
> levels down, and the fragment spliced the two levels flat and then dropped the third operation.
> Every value in it was true. A reader who pasted the path into `jq` would have got nothing, on the
> page that invites them to recompute the verdict themselves.
> `tests/test_readme_fragment_is_verbatim.py` now fails the build if this block stops being an
> emitted passport's operations array, entire and in order — the red run that proves it can fail is
> kept as `evidence/RED-008-readme-fragment-not-verbatim.txt`.

Three things here are the whole product — two of them quoted above, and the third,
`"verifier_affiliation": "same_owner"`, one level up at `passport.verifier_affiliation`:

| | |
|---|---|
| `"level": "check_did_not_run"` | **Absence is a state, never a zero.** Three reasons exist — `nothing_qualified`, `check_did_not_run`, `unreadable` — and a verdict always says which. A zero would mean "measured, and fully non-autonomous", an entirely different claim about the world. |
| `"confidence": "inferred"` | The published number is never stronger than the measurement behind it. |
| `"verifier_affiliation": "same_owner"` | Every record discloses whether the verifier and the subject share an owner. Today all of them do. |

## How it measures

**A level belongs to an operation, never to a company.** A single number for a whole company is a
marketing number.

```
L0  a human performs the operation
L1  a human performs it, tools assist
L2  a machine proposes, a human approves each time
L3  a machine acts, a human approves exceptions
L4  a machine acts, a human is notified
L5  a machine acts, no human is in the path
```

Evidence is classed by **forgery cost** — `self_reported`, `platform_observed`,
`third_party_attested`, `cryptographically_bound` — and a level built from mixed classes is marked
`inferred`, not `measured`.

A **human control map** accompanies every verdict. It can prove that a control path *exists*; it can
never prove that none was missed, so it publishes what it inspected and what it could not reach.

## What the score does *not* measure

Stated here for the same reason it is stated on every page of the site: reliability, decision
quality, profitability, and the presence of an accountable party. Accountability is recorded in a
separate block that deliberately does not affect the score — an empty control map yields maximum
autonomy *and* an honest "no addressee", and a reader deserves both truths side by side.

## Current state, honestly

Eight subjects, all the operator's own systems, all marked affiliated. **4 are verified; 4 are
unreadable** — those are private repositories, and a verdict on a source no third party can read
would not be reproducible, which under this project's own standard disqualifies it. The count moves
as repositories open or close; it is read from the emitted registry, not asserted here.

The registry is not padded. A registry of trust that invented entries would be doing the exact thing
it exists to detect, so it stays this size until real subjects grant a mandate.

## Reproduce a verdict yourself

The pipeline reads **public sources with no credential at all** — that is what makes a verdict
checkable by anyone, rather than by whoever holds a token.

```bash
git clone https://github.com/whiteknightonhorse/provek && cd provek
python3 -m pytest -q          # the suite prints its own count
python3 scripts/cohort.py     # re-emits public/registry + public/passports
```

Artefacts land in `public/`. The site reads exactly those files — there is no second content path,
because a page that could drift from the machine record would stop being worth trusting.

## How the rules are kept

Every load-bearing rule in `enforced_by.yaml` names the gate and the test that enforce it. Rules
that live only in prose are the ones that quietly stop being true, so a rule without a machine
behind it is treated as unenforced.

This paragraph used to end "— 31 of them", and the file had grown to 41 by the time anyone
re-read the sentence. A count copied into prose is a second copy of a fact whose first copy keeps
moving (L-2), and it decays into a claim the artefact no longer supports — on the page describing
how this project refuses to let that happen. The number is not restored here in a computed form
either: it would be one more place to keep true for no reader who needs it, and `enforced_by.yaml`
is in the repository for anyone who wants to count.

The design record is in the open, including its mistakes:

- [`DECISIONS.md`](DECISIONS.md) — every ratified decision and why
- [`docs/adr/`](docs/adr/) — architecture decision records
- [`evidence/`](evidence/) — kept runs, **including failing ones**: `RED-001`, `RED-002`, and
  `TAINTED-SUDO-CORPUS`, the artefacts produced by a pipeline that read its subjects through host
  privilege before the rule caught it. Deleting the evidence of a violation would be a second
  violation.

## What the badges assert

Three badges sit at the top of this file. Each is fetched live from the service that ran the check,
so it goes red when the check does — and a reader who wants the underlying run is one click away.

| badge | who runs it | what green means |
|---|---|---|
| `gates` | us, on GitHub Actions | the ratchets, the full test suite at ≥70% coverage, ruff, and the secret scan all passed on this commit |
| `codeql` | GitHub's CodeQL engine | the `security-and-quality` analysis **completed** on both Python and TypeScript — *not* that it found nothing; findings live in the Security tab |
| OpenSSF Scorecard | the OpenSSF, from their own copy | supply-chain posture scored against their rubric, published by them at [scorecard.dev](https://scorecard.dev/viewer/?uri=github.com/whiteknightonhorse/provek) |

**`gates` is us grading our own homework.** Every rule in it was written by the same hands as the
code it judges, which makes it useful and not independent. That is the whole reason the other two
are here: their queries and their rubric are not ours.

**The Scorecard number is low, and it is real.** It is not pinned, not cached and not chosen — it
is whatever the OpenSSF last computed. Several checks score zero because this repository has not
adopted the practice they measure; raising the number by tuning the run rather than by changing
the repository would be the exact defect this project exists to detect.

One detail in that report is worth naming, because it is this project's own vocabulary appearing in
someone else's tool: Scorecard reports `-1` for a check that **could not run**, distinct from `0`
for one that ran and found nothing. `nothing_qualified` and `check_did_not_run` are different
states of the world in their rubric as they are in [ours](SPEC.md).

**Badges that were considered and rejected**, so that their absence is a decision rather than an
oversight: Snyk (its badge answers `200` with the word *monitored* — no scan stands behind it),
Dependabot (a real service, but no badge that reports a run), Codecov (needs an account credential
this project does not hold; coverage is already gated at 70% inside `gates`), Sigstore/SLSA
provenance (nothing to attest — this repository publishes no release artefacts, which Scorecard
independently confirms with `-1` on `Signed-Releases` and `Packaging`), and the OpenSSF Best
Practices badge (a self-assessed questionnaire, which is `self_reported` under our own taxonomy and
therefore not evidence). `tests/test_readme_badges.py` fails the build if a badge without a run
behind it is ever pasted in here.

## Repository layout

```
src/abs_profile/    the ladder, evidence classes, identity binding, "not measured" as a state
src/collector/      evidence collection; secrets redacted before anything becomes an artefact
src/verify/         the control map and the scorer, with the weak-signal limiters
src/passport/       passport assembly; verified and self-reported stay separate branches
src/registry/       status lifecycle and the public registry
src/transport/      file transport and the ERC-8004 read adapter
web/                the public surface (Preact + Vite), prerendered to static HTML
web/functions/      the intake endpoint, writing to KV and announcing to the operator
```

## Status

Phase 1, verification-first. **Intake is open** at
[provek.dev/apply](https://provek.dev/apply/) — free, public repositories only, and the passport
says what it could not measure. See [`docs/WHY_GET_VERIFIED.md`](docs/WHY_GET_VERIFIED.md) for what
verification offers and what it deliberately does not.

## Licence

Two, because there are two different kinds of thing here.

- **The profile text** — the ladder, the evidence taxonomy, the absence vocabulary, and the
  methodology prose in `SPEC.md`, `DECISIONS.md`, `docs/` and this file — is
  **[CC BY 4.0](LICENSE-CC-BY-4.0)**. Quote it, adapt it, build on it; say where it came from.
- **The schemas, implementation and test vectors** — `src/`, `tests/`, `scripts/`,
  `requirements/`, `web/` — are **[Apache-2.0](LICENSE-APACHE-2.0)**. Run it, change it, ship it.

A profile that asks others to adopt a vocabulary must let them quote it; an implementation that
asks to be recomputed must let them run it. Different permissions, so different licences — and
openness without a licence is legally undefined, which is why the specification names both.

**Not licensed, deliberately:** the accumulated corpus of evidence and the reputation of the
issuer. They do not travel with the text. Copying the profile gives you the method; it does not
give you the record of what has been measured.

See [`LICENSE`](LICENSE).
