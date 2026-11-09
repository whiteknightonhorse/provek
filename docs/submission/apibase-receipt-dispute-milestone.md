# APIbase Receipt Dispute: milestone text (Changes & Improvements)

Written from `integrations/genlayer-apibase-attest/deploy/deployment.json` (`dispute_contract`) and `evidence/MEASURED-021-*`,
`-022-*`. Only transcript facts are stated. The dispatcher fills the `<...>` placeholders from `~/taskloop/briefs/GD-disputes.md`
at submission time. **The milestone is submitted only with at least 2 real disputes resolved** (T-GD-02, Fable ruling
GENLAYER-DISPUTE-1102). Disputes the team runs with its own MCP-Heartbeat wallets are end-to-end tests (source `team-test` in the
ledger) and the text says so; they are never presented as customer disputes.

## Changes & Improvements (limit 1000 characters)

Two dispute contracts now run on GenLayer Bradbury Phase 2 (test GEN): ApibaseReceiptDispute 0xe4e75ac47bf8350Ff705a552b7453Cf7726eF893 (billed but upstream 5xx) and ApibasePaymentDispute 0x34e8335b70546fb37c9f2c06d472208b13b8f168 (USDC paid on Base, no receipt). Deployed 2026-11-09 from commit 9055f93, refund policy 2026-11-04.3 pinned, five transactions ACCEPTED by 5/5 validators. Validators fetch independently and return REFUND or RELEASE; a verdict never pays, APIbase's capped worker does. <N real disputes: REFUND n, RELEASE m>, resolved end to end; refund <refund tx>. Where the dispute was an end-to-end test by the team with its own wallets, it is labelled so. Not measured: FINALIZED status and per-transaction charges.

## Pages that carry the same fact

- `integrations/genlayer-apibase-attest/deploy/DEPLOYMENT.md` in `whiteknightonhorse/provek`
