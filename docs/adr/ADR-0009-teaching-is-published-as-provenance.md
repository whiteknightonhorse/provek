# ADR-0009 — Teaching is published as provenance, in a separate repository

**Status:** accepted, 2026-08-20. Ruled by Fable at the operator's request.

## Context

The operator asked to publish four working documents about building autonomous agents and
autonomous startups. Specification §10.4 anticipates exactly this:

> If the same party teaches people to pass its own verification, it is grading work it set itself.
> Accepted for the MVP: verification is free, so the payment conflict does not arise; teaching and
> verification are separated as components.

Two non-goals were raised against publication. §4.3 non-goal 6 forbids becoming a generic platform
of business services. Non-goal 4 forbids judging the desirability of autonomy — and a guide called
*how to build autonomous agents* asserts by existing that more autonomy is better.

## What the measurement showed, and what it corrected

The four documents were grepped for the vocabulary of this instrument. **Zero occurrences** of
verification, passport, or the product name in any of them. So §10.4's conflict is not present in
the content; it is a drift risk. The question is therefore not whether publication is forbidden but
what framing and what gate keep that measured zero true.

The non-goal-4 objection was **over-read**, and the correction matters: §2.1, decision A-5, makes
the ladder monotone — "a higher level is a higher score; L5 is the goal, not a red flag". What §2.2
and non-goal 4 require is that the *score* carry no desirability claim, with the disclaimer beside
it. "L0 is a state, not a failure" is a rendering rule for the measurement, not a vow that the
issuer has no view. An incubator is not agnostic about autonomy; its founding thesis is that
autonomous business is coming and needs verifying.

## Decision

**Publish as provenance. Do not publish as teaching.**

1. **A separate repository** — `provek-method` — not a section, not a subdomain. "Separated as
   components" means a boundary a third party can check, and the verification surface must never
   have hosted the teaching when verification becomes paid.
2. **One link, in prose, on the Method page.** No navigation entry: that would make the corpus a
   component *of* this surface, and DESIGN.md rule 4 forbids the retrofit anyway.
3. **Descriptive titles, never hortatory.** "How this instrument was built", not "how to build
   autonomous agents".
4. **A standing disclaimer** in the corpus: following these documents has no effect on any verdict.
   This is literally true — the scorer is deterministic code over measured quantities and "used our
   method" is not a field — which makes it the strongest separation available, and it already
   existed.
5. **Two machine gates, in both directions.** In the corpus, a CI check that fails if it names the
   instrument, run against a planted violation on every push, with the failing run kept. On the
   site, a test over the emitted HTML asserting a single occurrence, on Method, framed as
   provenance. Registered as `LAW-TEACHING-IS-SEPARATE`.
6. **Documents published as quoted artefacts**, each with the sha256 of its original. Not rewritten
   into tutorials: rewriting changes the genre from "what we did" to "what you should do", and only
   the first is free of the conflict.

## Explicitly not decided

An actual course. That is a different product, it would face non-goal 6 on the merits, and it gets
its own ADR if it is ever wanted.

## Consequence for the paid transition

When verification becomes paid, §10.4's triad activates — payer separation, published methodology
(already satisfied by A-8), random re-audit. The teaching separation will already be structural, so
nothing is rebuilt under pressure. The conflict is also narrower than it first appears: teaching
someone to *be* autonomous legitimately changes the measured state; teaching someone to *appear*
autonomous is what the gate forbids and what random re-audit is for.
