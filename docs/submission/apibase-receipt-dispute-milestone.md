# APIbase Receipt Dispute: milestone text (Changes & Improvements)

Written from `integrations/genlayer-apibase-attest/deploy/deployment.json` (`dispute_contract`) and `evidence/MEASURED-021-*`,
`-022-*`, `-024-*`, `-025-*` and `-026-*`. Only transcript and capture facts are stated. Both disputes are end-to-end tests the team ran with its own wallets (source
`team-test`); none is a customer dispute, and the text says so. No REFUND verdict as of 2026-11-09. The milestone is submitted only after the
v0.1 milestone is reviewed, with the paragraph below as merged on main.

## Changes & Improvements (limit 1000 characters)

Two dispute contracts now run on GenLayer Bradbury Phase 2 (test GEN): ApibaseReceiptDispute 0xe4e75ac47bf8350Ff705a552b7453Cf7726eF893 (billed but upstream 5xx) and ApibasePaymentDispute 0x34e8335b70546fb37c9f2c06d472208b13b8f168 (USDC paid on Base, no receipt). Deployed 2026-11-09 from commit 9055f93; refund policy 2026-11-09.1, which names both addresses, is pinned on both and copied into every record. Validators fetch independently and return REFUND or RELEASE; a verdict never pays, APIbase's capped worker does. 2 disputes resolved, both end-to-end tests by the team with its own wallets (no customer disputes yet): RELEASE on receipt 9dbc77f9fd66bcb8714cd064f5681005 (upstream 200) and RELEASE from the payment contract (receipt exists). No REFUND verdict by 2026-11-09: as of 2026-11-10 no receipt has ever been billed with an upstream 5xx (40023 receipts in the last 30 days), since APIbase does not bill a failed call. Not measured: FINALIZED status and per-transaction charges.

## Pages that carry the same fact

- `integrations/genlayer-apibase-attest/deploy/DEPLOYMENT.md` in `whiteknightonhorse/provek`
