# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Two audiences, both real, with a decided order of priority.

**Primary — the subject.** A team running a business operated by AI agents, who needs a verdict
they can show their own customers. They arrive at the landing page cold, sceptical, and already
tired of the phrase "AI-powered" being unfalsifiable. Their job: decide within a minute whether
this standard is real enough to submit to, then apply.

**Secondary — the consumer of evidence.** A counterparty, buyer, or lawyer checking whether a
specific business is what it claims. They arrive by a link from elsewhere — an email footer, a
badge, a due-diligence memo — and land on a passport, not on the landing page. They read one
document, once, possibly a year after it was issued.

Operator decision, 2026-08-20: **the landing page speaks to the subject first.** The registry is
that page's evidence that a standard exists, not its main event. This does not demote the passport:
the passport remains the load-bearing screen because it is where the secondary audience always
lands.

## Product Purpose

An outside party can determine, **from evidence rather than claims**, how much of a given business
is actually run by machines.

The system measures, per business operation, how little a human is required — on a ladder L0–L5 —
and publishes the evidence behind every level, including what could not be measured. It issues a
machine-readable passport and lists the verdict in a public registry.

Success is a verdict a third party can reproduce from the same inputs. If it were not reproducible,
this would be a brand rather than a standard.

## Positioning

An ERC-8004 **validator**: the standard supplies identity and transport, the methodology is ours.
The claim a neighbouring product could not truthfully copy is the methodology itself, published in
full — including its own limits, and including the record of every check that did not run.

The system is applied to itself. `provek` is row eight of its own registry, measured by the same
collector as everything else — and it only became measurable when the repository was opened, which
is the mechanism working rather than a courtesy.

## Operating Context

- Verdicts are produced by a Python pipeline on the operator's server; the web surface reads the
  artefacts it emits (`registry.json`, one JSON passport per subject). There is no second content
  path — a file in the repository is not what a reader receives.
- A passport is valid for 30 days and then lapses to `stale` by time, with no event. Readers may
  encounter an expired document.
- The evidence window is 30 days. Provenance (protocol version, profile version, window) travels
  with every verdict, because a verdict without its protocol version cannot be interpreted a year
  later.
- Historical passports are never silently recomputed under a new methodology.

## Capabilities and Constraints

**Works today:** identity binding with a stated strength, evidence collection from git and the
GitHub API, human-control map with mandatory coverage, scoring with three weak-signal limiters,
passport issuance, public registry, status lifecycle, liveness, mandate, two transports, an
ERC-8004 read adapter, and self-application over eight subjects.

The word **liveness** in that list was doing more work than the artefact until 2026-08-20: the
module existed, passed its tests and carried two laws, and no component had ever declared an
obligation into it. It now holds one — the commitment to re-issue the eight published rows before
they lapse — and a gate that goes red when the interval passes unmet (`LAW-REISSUE-OR-FINDING`,
`docs/LIVENESS_OPERATIONS.md`). One obligation is a small claim, which is why it is stated as one.

**Does not work yet, and the surface must not imply otherwise:** no active probing (the mandate
object and its fail-closed behaviour exist; the prober does not), no runtime comparison, no runtime
evidence collection. At least two of three operations on every current subject are `not_measured` —
on the four unreadable subjects it is all three — and the passport says which of the three absences
applies rather than scoring them zero. (This read "two of three on every current subject" until
2026-08-20; it holds for four of the eight. Counted from the emitted passports, as SPEC §6 is —
which also records why the original sentence cannot be dated from anything in this repository.)

**Vocabulary that must not drift:**

- **`not_measured` is a state of its own, never a zero.** It always carries one of three reasons:
  `nothing_qualified`, `check_did_not_run`, `unreadable`. A zero would mean "measured, and fully
  non-autonomous" — an entirely different claim about the world.
- **A level belongs to an operation, never to a company.** A single number for a whole company is
  a marketing number.
- **The score measures autonomy.** Not reliability, not decision quality, not profitability, not
  the presence of an accountable party.
- **Accountability is outside the score**, deliberately. An empty control map yields maximum
  autonomy and no addressee at once, and both truths are shown side by side.
- Evidence is classed by forgery cost: `self_reported`, `platform_observed`, `third_party_attested`,
  `cryptographically_bound`.

**Reserved and deliberately unannounced:** phase 2 (execution witnessing, task history) and revenue
streams 3 and 4 (corporate access to the evidence corpus, regulatory dossier export). The design
must have room for these from the start, but must not describe them as coming features.

## Brand Commitments

- Name: **Provek**. Domain `provek.dev`, registered.
- The entire public surface is **English-only** — code, docs, commit messages, interface.
- Voice: a standards body, not a startup. States its own limits before it is asked. Never
  apologises for the size of the registry, and never pads it.
- No logo or emblem exists, and none is required: an emblem earned before a method is exactly the
  substitution this product exists to detect.
- Colour, typography and motion are **decided and recorded** in `DESIGN.md`: IBM Plex, two
  authored palettes, and one visual device — the unfilled slot, a ruled blank where an
  unmeasured value would have gone.

## Evidence on Hand

Real, and honestly scarce.

- **Eight passports**, all of the operator's own systems, all marked `same_owner` — an affiliated
  rehearsal of the protocol, not independent verification, and marked as such on every row and
  every document.
- **4 verified, 4 unreadable.** The unreadable four are private repositories: they
  answer 404 to a reader holding no credential, and a verdict on a source no third party can read
  is not reproducible. That is a measurement about the subject's public posture, not a judgement of
  it, and it is the honest result of applying the method to ourselves. Exact numbers live in the
  emitted registry; repeating them here is how this section drifted once already.
- Three measured answers to open questions: the ERC-8004 identity population is **50,275**,
  measured on-chain; verification cost is **0.006 CPU-seconds** and three API calls; and the
  §2.7 filter over a 100-identity sample of that population returns **zero candidate identities**,
  with 27 of the 100 recorded as unreadable rather than counted against anyone, and **3 of the 8
  operators behind those identities reachable at a declared endpoint** when probed
  ([`docs/MEASUREMENT_QM1.md`](docs/MEASUREMENT_QM1.md)). Both numbers are published because a
  per-identity rule cannot count a business that mints ten thousand rows.
- 301 tests, 44 laws armed, four ratchets. The count is quoted because it moves; the claim that
  matters is that every load-bearing rule names the gate and the test enforcing it.

**Absences that must not be fabricated:** no customers, no testimonials, no third-party subjects,
no independent verifications, no pricing, no case studies, no press. The near-empty registry is a
**designed state** and will be real for months. It must explain what the registry is, why it is
small, and how to enter it — without apologising.

## Product Principles

1. **Publish the absence.** Every check that did not run says so, with its reason. A surface that
   renders an unmeasured field as a zero, a dash, or nothing at all has told the reader something
   false.
2. **State the limits before you are asked.** The disclaimer sits beside the score, never in a
   footnote. Affiliation is on the face of the record.
3. **One artefact, two readers.** The human page and the machine record are the same data. If they
   could drift, the machine record would stop being the thing we ask people to trust.
4. **Never pad the evidence.** A registry of trust that invents entries is doing the exact thing it
   exists to detect.
5. **Reproducibility over reputation.** Any claim the surface makes must be recomputable by a third
   party from the same inputs.

## Accessibility & Inclusion

WCAG 2.2 AA is a product requirement, not a preference: this is a document people read under
obligation — in due diligence, in a dispute, a year after issue — and legibility is part of the
claim to be a standard.

Two consequences that are specific to this product rather than generic:

- The `not_measured` marker carries the most easily dismissed fact on the page. It is held to the
  same contrast floor as ordinary text; rendering it in the lightest ink available would be an
  argument by typography for exactly the dismissal the state exists to prevent.
- No fact may be carried by colour alone, and no reason may be reachable only by hover. Both were
  found and fixed in phase 3: the absence reason had been sitting in a `title` attribute, which
  reaches a mouse and nothing else.
