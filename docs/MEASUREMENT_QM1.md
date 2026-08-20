# Q-M1 measurement - how many external AI businesses exist

**Status:** step 1 DONE (measured 2026-08-19), step 2 DONE (measured 2026-08-20).
**Go/no-go condition** per specification section 1.5.

## Step 1 - population upper bound: MEASURED

**50,275 identities** in the ERC-8004 Identity Registry on Ethereum mainnet
(`0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`).

Method: direct `ownerOf(id)` reads over JSON-RPC, doubling then binary search. 32 calls against a
ceiling of 40 declared before the run. This is a measurement, not a quotation: the press reports
"45,000+ agents", and we read the chain instead of repeating it.

Step 2 tightens it from a ceiling towards a count: **0 of the 100 sampled ids were absent**. That
does not license "every id has been minted" - 0 of 100 is consistent with an absent share up to
about 3.7% at 95%, so the honest reading is that 50,275 is within roughly 4% of the true identity
count, and no absences were observed.

## Step 2 - the filter per specification 2.7: MEASURED

**0 candidate identities.** From a sample of 100 identities, **0 of the 35 registration files that
could be read describes a business in its own right**, and **27 could not be read at all**.

**At the operator level: 8 hosts surfaced, 4 declared a probeable endpoint, and 3 of those served
a live artefact when probed; 1 is `not_measured`.** The other four hosts are `not_measured` too -
no registration file was obtained from them, so no endpoint could be extracted.

Those are two answers to two different questions, and the second exists because the first cannot
answer Q-M1 alone. A per-identity rule structurally cannot count a bulk-minted business: an
operator whose whole registry presence is ten thousand collection rows yields ten thousand rows
each correctly labelled "not a business in its own right", and therefore zero candidates, when the
honest answer for that operator is one. The first draft of this document published the per-identity
zero on its own. Fable refuted it, and the refutation held.

Run: `python3 scripts/measure_qm1_step2.py --collect`, then `--probe-operators`, then `--report`.
Sample and per-identity labels: [`evidence/QM1-002-sample.json`](../evidence/QM1-002-sample.json).
Operator probes: [`evidence/QM1-003-operators.json`](../evidence/QM1-003-operators.json). Output:
[`evidence/QM1-002.txt`](../evidence/QM1-002.txt). 145 external calls (137 collect + 4 + 4
re-probe) against a ceiling of 300
declared before the run.

### Method

100 ids, systematically sampled at `round(k * 50275 / 100)` for k = 1..100 - evenly spaced across
the whole id space, which is also the time axis, since agentIds are assigned incrementally. No
seed, so any reader reproduces the same sample from that one expression. The design aliases
against periodic structure, which is named here rather than left to be found: a mint run whose
*period* sat near the stride of 503 would be mis-weighted.

The runs actually observed are far **longer** than the stride - twenty consecutive sample points
resolve to one host, implying a contiguous block of roughly 9,500 ids, and the inline-persona
block implies another of several thousand. That is the safe case: systematic sampling weights a
run much longer than the stride in proportion to its size. This paragraph said "far shorter than
the stride" until the sample was checked against it, which is the same defect the document is
about - a justification that reads plausibly and is the opposite of the data underneath it.

For each id: read `tokenURI` (the *agentURI* of EIP-8004), resolve whatever it points at, and
classify the registration file by hand against 2.7. The hand labels are stored per id, with a
one-line reason each, so a reader can disagree with a specific row rather than with the total.

### What the instruments returned, and what the report judged

Two columns, because they differ and the difference is this project's founding distinction. The
report demotes four identities that answered **HTTP 200 with a single-page-app shell**: the
instrument received a body, and the body is not a registration file.

| state | instruments returned | report judged | meaning |
|---|---|---|---|
| `token_absent` | 0 | 0 | the chain answered: never minted or burned |
| `rpc_unreadable` | 0 | 0 | the chain did not answer |
| `no_registration` | 38 | 38 | the chain answered: the identity declares **no registration file** |
| `card_unreadable` | 23 | 27 | a file is declared and no registration file was obtained |
| `card_read` | 39 | 35 | a registration file was obtained and classified by hand |

The demotion runs towards *unreadable* and never towards *not a business*. A soft 404 counted as a
read file would have put four web-server error pages in front of a human to be classified as
businesses.

The 27: **20** point at `agents.exquisite.land`, which offers no TLS certificate - `openssl
s_client` reports `no peer certificate available`, and an independent network path off this host
fails identically. So the failure is on the subject's side of the wire rather than in our reader;
whether the file *exists* behind it is still unknown, and the row stays `unreadable` rather than
being promoted to a measured absence. The remaining seven are the four soft 404s, one 404, one
502, and one IPFS gateway timeout.

**The 404 and the 502 currently land in the same field, and that is a known defect of this
taxonomy.** A 404 is an authoritative absence; a 502 is a refusal to answer. Splitting them would
move one row and narrow the upper end of the band, and it is recorded here as owed work rather
than quietly kept - a state named for not-knowing must not hold a measured absence.

### The two absences, kept apart

| | n | |
|---|---|---|
| `unreadable` | 27 | we did not obtain the evidence |
| `nothing_qualified` | 73 | we obtained it and nothing there qualifies |

This separation is the load-bearing part of the measurement, and it is enforced by
`LAW-SURVEY-ABSENCE` with a test, not by care. Folding the 27 into the 73 would leave every total
correct and publish our own instrument failures as a fact about the market (L-22).

Consequently the rate is published as a **band**:

* **lower 0.00%** - every unreadable identity counted as not a candidate → **0** candidates
* **upper 27.00%** - every unreadable identity counted as a candidate → **13,574** candidates

The upper end is arithmetic rather than plausible: 20 of the 27 sit behind a single host,
`agents.exquisite.land`, whose name suggests but does **not** establish a relation to
`exquisites.es` - different registrable domains, different path schemes, and no evidence collected
either way. The link is deliberately not asserted, because it would be asserted in the convenient
direction: it is what would let us dismiss the upper end. It is stated because
a bound one is free to disbelieve is still a bound, and choosing the believable end is how a
measurement becomes an opinion.

Separately from the unreadable band, the **sampling error** on the lower rate is 0.00% to 3.70%
(Wilson, 95%), i.e. 0 to **1,860** identities. At a zero count the lower Wilson tail is
identically zero and carries no information; the upper tail is the whole content of the interval.
An earlier draft published only the lower tail and called it a "conservative floor", which
advertised a precision that a sample of 100 cannot buy.

### What the 35 readable files actually were

Not one described a business. In order of frequency: persona boilerplate with no service or
endpoint declared (12); user-profile stubs that are not EIP-8004 registration files at all (5);
self-declared test entries - *"only test ... please do not disturb"* (4); rows of NFT collections
of 10,000 and 6,666 pieces (5); an art-critic endpoint replicated across ~10,000 identities under
one operator (4); and single instances of a meme persona, a collectible, an empty record, a
trading agent declaring capability with `services[]` empty, and an agent declaring three services
whose own telemetry reports it dormant.

Several of these rows do declare service endpoints - FREAK #923 declares three services and four
skills, Signalbound #5655 declares twenty-two, the Normies rows two each. The per-identity label
rejects them as *rows of a collection*, not as *silent*: the business is the collection, and each
row's rationale in the sample file now says which operator it defers to. FREAK #923 is rejected on
its own telemetry rather than by analogy - the card declares `state: "Dormant"`, `sessions: 0`,
`messages: 0`, `last_contact: null`.

An earlier draft justified the collection rows by the precedent that excluded `realestate`. **That
was wrong and is withdrawn.** `realestate` was excluded for *overlapping a subject already
counted*; the dedup rule presumes the business is counted once somewhere. Here the collections
were assessed nowhere, so the rule deleted them instead of deduplicating them. Hence the operator
level below.

### The operator level - where the question actually lives

**The registry's unit is not the question's unit.** Q-M1 asks how many businesses exist; the
registry counts identities, and one operator can mint ten thousand. Of the 62 identities that
declare an agentURI, 25 carry the document inline, one is content-addressed, and the remaining 36
point at just **8 distinct hosts** - three of which account for 28 of the 36.

Four operators' cards declared an endpoint that could be probed. Each was probed once, so that "observable
result of activity" is measured rather than read off a card:

| operator | endpoint result | body | state |
|---|---|---|---|
| `api.normies.art` | HTTP 200 | 6,993 bytes | `live` |
| `exquisites.es` | HTTP 200 | 85,056 bytes | `live` |
| `signalbound.art` | HTTP 200 | 7,594 bytes | `live` |
| `api.freaks.one` | transport failure (curl 56) | no body obtained - **not** zero bytes | `not_measured` |

So **3 live, 0 answered without an artefact, 1 `not_measured`** of the four probed. These are the
candidates a per-identity count erases.

`exquisites.es` reads HTTP 200 here and read HTTP 400 in the first version of this probe. **That
400 was our own instrument**: the endpoint selector took the first entry in `capabilities`, which
declares `"method": "POST"` in the same object, and a GET against it was refused. A GET-able
capability was sitting in the same file. The selector now honours the declared method, and an
operator is never recorded as silent because we asked the wrong way. The three states above are
separated for exactly this reason - a refusal aimed at our request is not the subject's silence.

Beyond those four, **4 of the 8 hosts were never probed** - `ag0.xyz`, `agents.exquisite.land`,
`api.khorus.io`, `space-weather-agent-production.up.railway.app` - because no registration file
was ever obtained from them, so no endpoint could be extracted. They are `not_measured`, not
"no endpoint": the gap is ours. Printing "4 operators, 2 live" without this line would put a
denominator in front of a reader that looks like the whole set, which is the same absence collapse
the row-level accounting refuses, committed one level up.

**The operator count in the population is `not_measured`**, and that is a state rather than a gap.
A sample of identities is not a sample of operators: estimating how many distinct operators exist
from it is a species-richness problem, and multiplying 8 by the stride is not an estimator of it -
that would be the very mistake this document exists to avoid, committed one level up. Nor is the
host count a bound in either direction, since one company may serve several hosts and one host may
serve several companies. It is a count of hosts, and it is published because the *concentration*
is legible in it.

The next measurement is therefore an operator-level enumeration - grouping agentURI hosts across
the whole registry rather than a sample - and it is named here as owed, not implied as done.

**And `live` means reachable, not active.** The probe establishes that a server returns bytes at a
declared endpoint. §2.7 asks for an *observable result of activity*, which is a stronger thing: a
static metadata page about a collectible is reachable and is not evidence that anything operates.
So the three live operators are themselves a **ceiling**, exactly as the identity-level number is,
and for the same reason - the condition that would settle it is not remotely readable. The column
reads `live` rather than `active` because the measurement supports the first and not the second.

### What these numbers are, and what they are not

They are counts of **candidates for intake**: at the identity level, identities whose public
registration file describes a business operation with an observable result; at the operator level,
distinct operators whose declared endpoint was probed.

It is **not** the count of subjects qualifying under 2.7. That section requires all of an
observable result of activity, at least one 2.3 operation at level **≥ L3**, and an identity that
survives redeploy. A registration file speaks to the first; an ERC-8004 identity satisfies the
third by construction. **No public artefact carries the second**, and no remote read can establish
it - the autonomy level of an operation is `not_measured` for all 100 rows and is settled at the
mandate stage, with the subject's cooperation. So this is a **ceiling** on 2.7 qualification, and
a ceiling can refute a market but can never on its own confirm one.

### The go/no-go, computed rather than argued

`src/governance/thresholds.py` was run at both ends of the band, with `mandates_granted` and the
clock left as `not_measured` because they are:

| end | candidates | verdict | reason |
|---|---|---|---|
| lower | 0 | `REVISIT` | below 10, but growth has not been measured - a young market is not a dead one |
| upper | 13,574 | `NOT_MEASURED` | mandates granted were not measured |

Neither end is `GO` and neither is `STOP`. **The width of the band therefore does not bind the
decision**, and narrowing it - chasing 27 unreadable files - would change nothing.

What *does* bind differs by end, and saying "the mandate stage" for both was wrong: below
`CANDIDATES_REVISIT` the mandate gate is never reached at all.

* at the **lower** end, what binds is a second-window **growth measurement**;
* at the **upper** end, what binds is the unmeasured **mandate and clock** inputs.

The threshold code's own words for the lower end are the correct reading of a zero here: the 2.7
definition is deliberately strict and the market is young, so a terminal stop would kill the
project for being early. A terminal stop requires the absence of growth over a second window,
which has not been run.

Note also that the lower-end row is fragile to sampling error alone: at the Wilson upper tail
(~1,860) the verdict crosses to `NOT_MEASURED` on mandates. GO and STOP are unaffected either way,
which is why the decision does not turn on it.

### What step 1 already told us, and what step 2 did to it

Step 1 observed that any filter rate above 0.06% clears the threshold of 30, and reframed the risk
as *"the danger is not 'no market', it is 'the market is agents, not businesses'"*.

**That risk is now measured, and the framing was right.** Not one of the 35 registration files
that could be read describes a business standing on its own: the registry at this date is
populated by collectibles, test mints and persona records. 2.7 was written to separate agents from
businesses, and applied per-identity to a stranger population it admitted nothing at all.

But "zero businesses in the registry" would be the overclaim, and it is the one this document had
to be argued out of. The same sample surfaced four operators running collections behind those
rows, two of them serving a live artefact on demand. The market visible here is **thin and
concentrated**, not absent - and it is counted in operators, which nobody has yet counted.

## Material finding, outside Q-M1

**The Validation Registry is NOT DEPLOYED.** The `erc-8004/erc-8004-contracts` repository lists
Identity and Reputation registry addresses across many chains, and states that the Validation
Registry portion "is still under active update" with no addresses given.

This is the registry our architecture publishes into (ADR-0001). Consequences, stated plainly:

* the degraded mode described in the specification is not hypothetical - it is the CURRENT state:
  distribution through the standard is unavailable, the methodology and our own status registry
  are not;
* T-2.15b (on-chain publication) has **no target to write to** and cannot be scheduled yet;
* the decision to keep the adapter thin and the methodology transport-independent was not
  over-caution. It is what makes this finding an inconvenience rather than a redesign.

## Second material finding, from step 2

**A registration file does not have to be a file, or resolve, or be a registration file.** Of 100
identities: 38 declare nothing, 20 point at a host with no certificate, four answer HTTP 200 with
an HTML shell, and five store a user-profile stub inline where a pointer belongs. The standard's
identity layer is deployed and populated; the artefact layer behind it is largely absent or
broken.

For a validator this is not a disappointment, it is the market. A binding that resolves to
nothing is precisely the claim-stronger-than-artefact this project measures - and the ERC-8004
adapter's insistence that an unreachable registry yields `not_measured` with a reason, rather than
a zero, is now doing work against real data rather than a hypothetical.
