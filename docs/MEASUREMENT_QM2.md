# Q-M2 measurement - the cost of continuously verifying one project

**Status:** MEASURED for MVP scope. **Date:** 2026-08-19.
**Go/no-go condition** per specification section 1.5; the risk it tests is ABI-29-5.

## The risk being tested

Verification is a RECURRING cost; a fee is charged once. If cost per project per month exceeds
what anyone will pay, the model INVERTS at scale: the more customers, the worse the position. That
is not a pricing detail, it is a question of whether the business exists.

## Result

One full verification pass over one subject, averaged over three real repositories:

| | measured |
|---|---|
| wall clock | 3.02 s |
| CPU | **0.006 s** |
| external API calls | **3** |
| peak RSS delta | under 1.5 MB |

Projected to re-verification frequency, per project:

| frequency | passes/month | CPU/month | API calls/month |
|---|---|---|---|
| daily | 30 | 0.2 s | 90 |
| weekly | 4 | negligible | 13 |
| monthly | 1 | negligible | 3 |

**One GitHub token (5,000 calls/hour) supports roughly 40,000 projects at daily re-verification
before rate limits bind.**

## Verdict on the inversion risk: REFUTED for MVP scope

Compute cost is not the constraint and will not become one at any plausible MVP scale. The wall
clock is network latency, not work: 3 s per project with concurrency 1 is about 28,000 projects
per day of throughput, which is far beyond anything the go/no-go thresholds contemplate.

This removes the ABI-29-5 inversion from the risk register **for the MVP's passive verification**,
and it means the revenue model does not have to carry the verification cost. That is a genuine
simplification of the economics, not a hopeful reading.

## What this does NOT cover - stated so the number is not over-read

* **Active probing by mandate** is not measured here. It touches a live third-party system and its
  cost is bounded by the mandate, not by us.
* **Runtime evidence** is not measured: the MVP does not receive it, which is exactly why two of
  three operations come back `not_measured`. Adding it adds cost.
* **Large repositories.** The three subjects are small-to-medium. The collector reads the API
  rather than cloning, so size affects little - but this is an inference, not a measurement.
* **Money.** The price of an API call is not stated because it depends on a plan we have not
  chosen. Inventing it would be the guessed constant this project forbids.

## Consequence for pricing (deferred, not decided)

Since verification is effectively free at MVP scope, a per-verification fee is not required to
cover cost. Whether to charge at all - and for what - stays an operator decision. The measurement
removes a constraint; it does not choose a business model.
