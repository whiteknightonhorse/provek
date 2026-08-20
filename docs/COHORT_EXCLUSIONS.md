# The first cohort: eleven systems named, eight measured

The specification's first cohort is **eleven of the operator's own systems** (§4, §5.2, ABI-31-4).
The registry holds eight. The delta is checkable by anyone who reads the specification, so it is
named here rather than left to be discovered.

Nothing is silently absent. That is the rule this project applies to measurements, and a cohort is
a measurement of a population.

## Included — eight

> **These are membership facts, not measurements.** Whether a candidate qualifies under §2.7 is
> decided from what the operator knows about his own systems; it is what admits a subject to the
> cohort, and it is not a verdict. Four of the rows below have passports stating that nothing about
> them could be measured, and both statements are true at once — one is why the subject was
> submitted, the other is what the method could establish once it was.

| subject | why it qualifies for submission under §2.7 |
|---|---|
| `AI-Property-Sales-Platform` | observable output (published listings), development initiation is machine-led, identity survives redeploy |
| `audiobook-shorts-series` | observable output (published audiobooks and shorts), automated production pipeline |
| `gov-auction-report` | observable output (a published report channel), scheduled autonomous runs |
| `cryptocardhub-defycard` | observable output (a live site with published articles), autonomous content pipeline |
| `APIbase` | observable output (a running API service), automated deployment |
| `AIpush` | observable output (a running service), machine-led development |
| `mcp-protocol-tester` | observable output (test artefacts), automated runs |
| `provek` | observable output (this verifier and its registry), machine-led development. Self-application is required by §5.2, not a courtesy |

Four of the eight publish a projection today. The other four are private repositories and are
recorded as `unverified` with reason `unreadable` — a measurement about their public posture, not a
judgement of it. The rule is in the passport: evidence only the verifier can reach is not evidence a
third party can recompute, so it does not enter a published verdict even though a credential exists
that would read it.

## Excluded — three, with the reason each fails §2.7

§2.7 requires **all** of: an observable result of activity · at least one §2.3 operation at level
≥ L3 · an identity that survives redeploy. An agent-as-a-function and a chat copilot are explicitly
not subjects, because they have no business operations.

| candidate | fails on | why |
|---|---|---|
| `game` — the video-generation channel pipeline | **no identity surviving redeploy** | It is a set of scripts and cron entries inside another project's home directory, with no repository of its own and no binding that outlives a reinstall. §2.8 requires an identity that cannot be trivially assumed by another party; a directory path is not one. |
| `polymarket` — the market-watching agent | **no observable result of activity** | It reads and reports; it produces no product, service, or stream of artefacts that a third party can observe. §2.7 calls this an agent-as-a-function and excludes it by name. |
| `realestate` — the listings research fleet | **overlaps an included subject** | Its published output is `AI-Property-Sales-Platform`, already row one. Counting the fleet and its product as two subjects would inflate the cohort by describing one business twice, which is the padding this registry refuses. |

## Why this list exists at all

A registry that quietly holds eight where its own specification says eleven has made an unexplained
choice, and an unexplained choice in a trust artefact is indistinguishable from a convenient one. A
reader who finds the number and not the reasons has to assume the worst; a reader who finds both can
disagree with the reasoning and say where.

Reviewed 2026-08-20. If a candidate's circumstances change — a repository of its own, a published
output — it is re-assessed against §2.7 rather than admitted by preference.
