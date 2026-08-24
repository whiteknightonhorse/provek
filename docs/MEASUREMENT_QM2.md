# Q-M2 measurement - the cost of continuously verifying one project

**Status:** MEASURED for MVP scope. **First measured:** 2026-08-19. **Re-measured:** 2026-08-24
(`python3 scripts/measure_qm2.py`, live against the same three subjects - see below for why the
2026-08-19 numbers no longer held).
**Go/no-go condition** per specification section 1.5; the risk it tests is ABI-29-5.

## The risk being tested

Verification is a RECURRING cost; a fee is charged once. If cost per project per month exceeds
what anyone will pay, the model INVERTS at scale: the more customers, the worse the position. That
is not a pricing detail, it is a question of whether the business exists.

## Result (as measured 2026-08-24; re-run the script to check this is still current)

One full verification pass over three real repositories - not a uniform per-subject shape, because
one of the three now answers 404 to an anonymous reader and short-circuits after its first call
(`whiteknightonhorse/gov-auction-report`, reproduced in `evidence/RED-037-*`):

| subject | read | wall s | CPU s | API calls | RSS delta |
|---|---|---|---|---|---|
| gov-auction-report | **404, unreadable** | 0.70 | 0.001 | 1 | ~0.06 MB |
| mcp-protocol-tester | 200 | 3.08 | 0.005 | 3 | ~1.57 MB |
| AIpush | 200 | 2.84 | 0.004 | 3 | ~0 MB |
| **total for the pass** | 2 of 3 read | - | - | **7** | - |
| **average per subject** | - | 2.21 s | 0.003 s | 2.3 | under 1.6 MB (max) |

External API calls were **3 flat per subject** and **all three answered 200** as of 2026-08-19.
Neither statement is true today: a cohort pass now costs **7** calls, not 3 per subject, because
the unreadable subject stops after one call instead of three. Whether this holds for YOUR read of
"today" depends on whether `whiteknightonhorse/gov-auction-report` is still 404 - check with
`curl -s -o /dev/null -w '%{http_code}' https://api.github.com/repos/whiteknightonhorse/gov-auction-report`
rather than trusting this table past the date above.

Projected to re-verification frequency, per project (from the 2026-08-24 average of 2.3 calls and
0.003 CPU-s per subject):

| frequency | passes/month | CPU/month | API calls/month |
|---|---|---|---|
| daily | 30 | 0.1 s | 70 |
| weekly | 4 | negligible | 10 |
| monthly | 1 | negligible | 2 |

**One GitHub token (5,000 calls/hour) supports roughly 51,000 projects at daily re-verification
before rate limits bind**, at the 2026-08-24 measured rate.

## Verdict on the inversion risk: REFUTED for MVP scope

Compute cost is not the constraint and will not become one at any plausible MVP scale. The wall
clock is network latency, not work: ~2.2 s per project (2026-08-24 average, above) with
concurrency 1 is on the order of 39,000 projects per day of throughput, which is far beyond
anything the go/no-go thresholds contemplate.

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
