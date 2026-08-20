# Provek

**Evidence, not claims.** A verification layer that measures, per business operation, how much of a
company actually runs without a human in the loop — and publishes the evidence behind every number,
including what could not be measured.

🔗 **[provek.dev](https://provek.dev)** · [Public registry](https://provek.dev/#/registry) · [Method](https://provek.dev/#/method)

---

## The problem

Anyone can write "AI-powered" on a landing page. Nobody can currently tell that apart from a company
where machines really do the work. That is not a marketing problem — a competitor can always claim
more loudly. It is a verification problem.

Provek is an [ERC-8004](https://eips.ethereum.org/EIPS/eip-8004) **validator**: the standard supplies
identity and transport, the methodology is ours, and it is published in full so a third party can
recompute any verdict from the same inputs.

## What a verdict looks like

Real output, from the live registry — not an example:

```json
{
  "subject_id": "git:whiteknightonhorse/APIbase",
  "status": "verified",
  "projection": 80,
  "verifier_affiliation": "same_owner",
  "verified": {
    "operations": [
      { "operation": "development_initiation", "level": "L4", "measured": true,
        "confidence": "inferred",
        "limiters_applied": ["O1:mixed_classes->inferred"] },
      { "operation": "deployment", "level": "check_did_not_run", "measured": false,
        "confidence": null, "limiters_applied": [] }
    ]
  }
}
```

Three things in that fragment are the whole product:

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

Eight subjects, all the operator's own systems, all marked affiliated. **Three are verified; five
are unreadable** — they are private repositories, and a verdict on a source no third party can read
would not be reproducible, which under this project's own standard disqualifies it.

The registry is not padded. A registry of trust that invented entries would be doing the exact thing
it exists to detect, so it stays this size until real subjects grant a mandate.

## Reproduce a verdict yourself

The pipeline reads **public sources with no credential at all** — that is what makes a verdict
checkable by anyone, rather than by whoever holds a token.

```bash
git clone https://github.com/whiteknightonhorse/provek && cd provek
python3 -m pytest -q          # 169 tests
python3 scripts/cohort.py     # re-emits public/registry + public/passports
```

Artefacts land in `public/`. The site reads exactly those files — there is no second content path,
because a page that could drift from the machine record would stop being worth trusting.

## How the rules are kept

Every load-bearing rule in `enforced_by.yaml` names the gate and the test that enforce it — 29 of
them. Rules that live only in prose are the ones that quietly stop being true, so a rule without a
machine behind it is treated as unenforced.

The design record is in the open, including its mistakes:

- [`DECISIONS.md`](DECISIONS.md) — every ratified decision and why
- [`docs/adr/`](docs/adr/) — architecture decision records
- [`evidence/`](evidence/) — kept runs, **including failing ones**: `RED-001`, `RED-002`, and
  `TAINTED-SUDO-CORPUS`, the artefacts produced by a pipeline that read its subjects through host
  privilege before the rule caught it. Deleting the evidence of a violation would be a second
  violation.

## Repository layout

```
src/abs_profile/    the ladder, evidence classes, identity binding, "not measured" as a state
src/collector/      evidence collection; secrets redacted before anything becomes an artefact
src/verify/         the control map and the scorer, with the weak-signal limiters
src/passport/       passport assembly; verified and self-reported stay separate branches
src/registry/       status lifecycle and the public registry
src/transport/      file transport and the ERC-8004 read adapter
web/                the public surface (Preact + Vite), reading the same artefacts
```

## Status

Phase 1, verification-first. Intake is not yet open — see [`docs/WHY_GET_VERIFIED.md`](docs/WHY_GET_VERIFIED.md)
for what verification offers and what it deliberately does not.

## Licence

Not yet declared, and that is a known gap rather than an oversight: the specification requires
CC BY 4.0 for the profile text and Apache-2.0 for schemas and test vectors, because openness without
a licence is legally undefined. Tracked and being fixed.
