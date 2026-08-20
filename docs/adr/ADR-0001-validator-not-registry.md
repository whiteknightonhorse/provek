# ADR-0001. Built as an ERC-8004 VALIDATOR, not as our own registry

**Date:** 2026-08-19. **Status:** accepted. **Supersedes:** nothing (first decision).

## Decision
The core is the methodology: the L0-L5 ladder, PoAB, the control map, mandated active probing.
Publication goes through a transport layer; ERC-8004 is the primary identity binding and the
distribution channel. We do NOT build our own IDENTITY registry. We DO build a STATUS registry -
it is required by ABI-19-2.

## Why
Verified against the primary source (eips.ethereum.org/EIPS/eip-8004): the standard is in Draft,
it fixes the shape of a validator's answer (0-100), and it explicitly moves complex reputation
aggregation off-chain, leaving the validator's mechanisms to the validator. The standard is
TRANSPORT; the methodology is the part left unoccupied. A proprietary registry would be displaced
by the standard; a validator on the standard gains distribution from it.

## What protects us from the Draft status
`scorer` does not import transport (a machine guarantee, not a convention), the adapter is thin,
and a second transport exists to prove independence. If the standard does not finalise, what falls
is distribution, not the product.

## Cost
The standard lowers the barrier for competitors too. The moat stays in execution: the methodology,
the accumulated evidence corpus, and the reputation of the issuer.
