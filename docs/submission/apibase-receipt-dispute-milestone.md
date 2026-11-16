# APIbase Receipt Dispute: milestone text (Changes & Improvements)

Written from `integrations/genlayer-apibase-attest/deploy/deployment.json` (`dispute_contract`) and `evidence/MEASURED-021-*`,
`-022-*`, `-024-*` to `-026-*` and `-028-*` to `-031-*`. Only transcript and capture facts are stated. All three disputes are end-to-end tests the team ran with its own wallets (sources
`team-test` and `team-test-staged`); none is a customer dispute, and the text says so. The one REFUND is on a transfer the team staged for this test; APIbase booked it and did not pay it out, because the payer is a team wallet. The milestone is submitted only after the
v0.1 milestone is reviewed, with the paragraph below as merged on main.

## Changes & Improvements (limit 1000 characters)

Two dispute contracts run on GenLayer Bradbury Phase 2 (test GEN): ApibaseReceiptDispute 0xe4e75ac47bf8350Ff705a552b7453Cf7726eF893 (billed but upstream 5xx) and ApibasePaymentDispute 0x34e8335b70546fb37c9f2c06d472208b13b8f168 (USDC paid on Base, no receipt). Deployed 2026-11-09 from commit 9055f93; refund policy 2026-11-09.1 is pinned on both and copied into every record. Validators fetch independently and return REFUND or RELEASE; a verdict never pays, APIbase's capped worker does. 3 disputes resolved, all end-to-end tests by the team with its own wallets (no customer disputes yet): RELEASE on receipt 9dbc77f9fd66bcb8714cd064f5681005 (upstream 200), RELEASE from the payment contract (receipt exists), REFUND paid_without_receipt on a 0.50 USDC transfer the team staged for this test with no API call. APIbase booked that REFUND in its refund ledger and did not pay it out, since the payer is a team wallet. Not measured: a paid-out refund, FINALIZED status, per-transaction charges.

## Pages that carry the same fact

- `integrations/genlayer-apibase-attest/deploy/DEPLOYMENT.md` in `whiteknightonhorse/provek`
