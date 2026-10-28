# APIbase Receipt Attestation: project update

The project is already live on the Portal. This is the text for the project UPDATE, written from
`integrations/genlayer-apibase-attest/deploy/deployment.json` and `evidence/MEASURED-019-*`. Nothing here is a new claim: a
value the record does not carry is not stated.

Why the update: GenLayer reset the Bradbury testnet on 2026-10-24 and the earlier deployment died with it. The contract was
redeployed on Bradbury Phase 2 (chain 4221) on 2026-10-28 from Provek commit `11474b4` (runner `babwp`, header `# v0.3.0`),
`set_chain("8453", ...)` was accepted, and one live `attest` on a real APIbase receipt reached PASS. No FAIL or NOT_FOUND
record exists on the new deployment and no studionet integration run was supplied: both are `not_measured`.

## How-to step (replaces the explorer link)

Open https://explorer-bradbury.genlayer.com/address/0x1bD4C0EBC9b365905d4EBC84b944d861499afe6E (GenLayer Bradbury Phase 2, chain 4221). Call get_attestation with attest_id 0954262009b2f224290261fb68e833acf11f4003c1d52ea31027f4a778e414ef, or list_by_receipt with receipt id 9dbc77f9fd66bcb8714cd064f5681005.

## Expected verification outcome (358 characters, limit 500)

Contract 0x1bD4C0EBC9b365905d4EBC84b944d861499afe6E (redeployed 2026-10-28 after the testnet reset). get_attestation returns result PASS, observation payment_matches, rail x402-base, chain 8453, amount_atomic 1000, tool myvariant.search: the APIbase receipt matches the Base USDC transfer it names. Written by an ACCEPTED attest transaction (5/5 validators).

## Pages that carry the same fact

- https://apibase.pro/attest/ (APIbase's page; moves to the new address when the promotion goes live)
- `integrations/genlayer-apibase-attest/deploy/DEPLOYMENT.md` in `whiteknightonhorse/provek`
