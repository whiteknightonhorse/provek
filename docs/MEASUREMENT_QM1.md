# Q-M1 measurement - how many external AI businesses exist

**Status:** step 1 DONE (measured), step 2 NOT DONE (named, not silently skipped).
**Date:** 2026-08-19. **Go/no-go condition** per specification section 1.5.

## Step 1 - population upper bound: MEASURED

**50,275 identities** in the ERC-8004 Identity Registry on Ethereum mainnet
(`0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`).

Method: direct `ownerOf(id)` reads over JSON-RPC, doubling then binary search. 32 calls against a
ceiling of 40 declared before the run. This is a measurement, not a quotation: the press reports
"45,000+ agents", and we read the chain instead of repeating it.

## Step 2 - the filter per specification 2.7: NOT DONE

**50,275 is NOT the answer to Q-M1.** An ERC-8004 identity is an agent record. A subject under our
definition needs an observable business operation - a chat function is not a business. The share
of the 50,275 that qualify is unmeasured.

What step 2 requires: read `tokenURI` for a sample, fetch the registration files, classify against
2.7, count manually for the first 100 and extrapolate. Cost: roughly 200-300 RPC and HTTP calls
plus manual classification.

**Reported as `not_measured`, with the reason - not as an estimate.** A number invented here would
propagate into the go/no-go decision, and the specification forbids exactly that.

## What step 1 already tells us

The go/no-go threshold is 30 external candidates, with a terminal stop below 10. The population
upper bound exceeds that by three orders of magnitude, so the binding question is entirely the
2.7 filter rate, not the size of the pond. Any filter rate above 0.06% clears the threshold.

That reframes the risk: the danger is not "no market", it is "the market is agents, not
businesses". Which is precisely what 2.7 was written to separate.

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
