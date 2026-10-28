# Deployment

Deployed by the dispatcher on 2026-10-28 (T-GLR-05 session); this record (T-GA-02) is written from the dispatcher's
transcripts only. `deployment.json` in this directory holds the measured fields this file summarizes; a value that no
transcript carries is written `not_measured`.

## Deployment record

**Network:** GenLayer Testnet Bradbury Phase 2, chain id `4221`, RPC `https://rpc-bradbury.genlayer.com`. Test GEN only; no
real money moved through GenLayer. GenLayer reset Bradbury on 2026-10-24; the contract was redeployed on 2026-10-28. The
earlier deployment (address prefix `0x7572cAB5…`, made 2026-10-20) died with the reset and is kept in `deployment.json` under
`previous_deployments` with every field it has no transcript for marked `not_measured`; its records were not carried over.
Toolchain: Bradbury Phase 2 runs the `py-genlayer:babwp9t3…` runner (contract header `# v0.3.0`, then
`# { "Depends": "py-genlayer:babwp9t37jw9g4j2bccgn14g6x7x9s1f7dsmh7emvz735pz4zxa0" }`, D-79).

**Contract:** [`0x1bD4C0EBC9b365905d4EBC84b944d861499afe6E`](https://explorer-bradbury.genlayer.com/address/0x1bD4C0EBC9b365905d4EBC84b944d861499afe6E),
deployed from commit `11474b4cfc94dada3a3e5301d19d1262713027ac` (`origin/main`) by
`0x2c111FCD3082083C9B287DD9DA5995f190968Ef9`, the operator. Constructor arguments: that operator and the receipt base URL
`https://apibase.pro/r/`. Contract bytes: 17706 bytes, sha256 `497d6d126c354632d53c3c1b4b56524032b7425a9d481b79272cbb430a70ce08`
(D-67: the deployed bytes are the committed file). The deploy transaction was ACCEPTED (later FINALIZED), validators in
MAJORITY_AGREE, execution result FINISHED_WITH_RETURN (its hash, `0x`-stripped for the secret-scan gate per GL-00 ruling-1, is
`deploy_tx` in `deployment.json`).

**Chain configuration:** `set_chain("8453", "https://mainnet.base.org", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")` was ACCEPTED
and FINALIZED (FINISHED_WITH_RETURN); `get_config` afterwards read chains `["8453"]`, the operator, and the receipt base URL.

**Fees (consensus v0.6):** every write carries a fee deposit, quoted at 0.100000000000010352 GEN per transaction; the unused
part is refunded at finalization. The node exposes no per-transaction gas, and no transcript isolates the charge of an attest
transaction, so `write_charged` and `deploy_charged` are `not_measured`.

**Studionet:** `not_measured`. No `gltest --network studionet tests/integration` run for this contract was supplied.

**One live record on Bradbury Phase 2, as of 2026-10-28** (read back with `list_by_receipt` and `get_attestation`; transcripts in
`evidence/MEASURED-017-*` and `evidence/MEASURED-019-*`, fields in `deployment.json`'s `live_records`):

| result | receipt id | observation | attest transaction |
|--------|------------|-------------|--------------------|
| PASS | `9dbc77f9fd66bcb8714cd064f5681005` (`myvariant.search`, 1000 atomic USDC, Base) | `payment_matches` | ACCEPTED, MAJORITY_AGREE, FINISHED_WITH_RETURN, 5/5 validators |

`attest_id` = `0954262009b2f224290261fb68e833acf11f4003c1d52ea31027f4a778e414ef`. The record names a real Base payment
transaction, the payer, the payee, and the receipt and response digests.

**What was tried and did not produce a record:** `attest` on `1203e946…36a8` (the repository's test-fixture id) ended
FINISHED_WITH_ERROR because `https://apibase.pro/r/1203e946….json` answered HTTP 404; no APIbase receipt exists for that id and
none was paid for to make one. No record was written. **No FAIL or NOT_FOUND record exists** on this deployment: `not_measured`.

**Known tooling limitations** on Bradbury Phase 2 (no contract code changed for any): (1) the `genlayer` CLI read path answers
"gen_call does not exist" on the default RPC, so reads were raw `gen_call`; (2) the CLI argument parser turns `8453` into a
number and a `0x…` string into an address, so `set_chain` was written with the `s#` string-argument rule; (3) no
per-transaction gas is available from the node.

## Reproduce

Read the record (no account, no fee): a raw `gen_call` of `get_attestation("0954262009b2f224290261fb68e833acf11f4003c1d52ea31027f4a778e414ef")`
on `https://rpc-bradbury.genlayer.com` against the contract above returns the record in `evidence/MEASURED-019-*`.

## After merge (dispatcher)

- Re-split the mirror (D-64, never edited directly): `git subtree split --prefix=integrations/genlayer-apibase-attest`; push to
  `whiteknightonhorse/apibase-genlayer-attest`; create the repository first if it does not exist.
- Live site, nothing here changes it: `curl -sS https://provek.dev/ | grep -c 0x1bD4C0EBC9b365905d4EBC84b944d861499afe6E` expects `0`
  (the address is in GitHub docs only).
- GitHub main, one per file: `curl -sS https://raw.githubusercontent.com/whiteknightonhorse/provek/main/README.md | grep -c 0x1bD4C0EBC9b365905d4EBC84b944d861499afe6E`
  (expects 2 or more), the same for `integrations/genlayer-apibase-attest/README.md`, `.../deploy/DEPLOYMENT.md` and
  `.../deploy/deployment.json`.
- Superseded wording, expects `0`: `grep -rn "7572cAB5" README.md integrations docs` outside `deployment.json`'s
  `previous_deployments` and this file.
- Submission: paste `docs/submission/apibase-receipt-attestation-update.md` into the Portal project "APIbase Receipt Attestation".
