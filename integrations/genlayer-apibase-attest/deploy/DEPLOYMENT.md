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

## Dispute contract

Two sibling contracts (T-GD-01, D-80), deployed by the dispatcher on 2026-11-09 (D3 session); this section is written from that
transcript only (`evidence/MEASURED-021-*`; reads in `evidence/MEASURED-022-*`; fields in `deployment.json`, `dispute_contract`).
Same network (Bradbury Phase 2, chain `4221`), same deployer/operator `0x2c111FCD3082083C9B287DD9DA5995f190968Ef9`, same
constructor arguments (the operator and `https://apibase.pro/r/`), same runner header (`# v0.3.0`, `babwp9t3…`).

| Contract | Address | Bytes | sha256 |
|---|---|---|---|
| `ApibaseReceiptDispute` | [`0xe4e75ac47bf8350Ff705a552b7453Cf7726eF893`](https://explorer-bradbury.genlayer.com/address/0xe4e75ac47bf8350Ff705a552b7453Cf7726eF893) | 12191 | `91e2fea2867b018e8f4c6b4899c93503d6b5195fbac1ea7c185813eab004f71c` |
| `ApibasePaymentDispute` | [`0x34e8335b70546fb37c9f2c06d472208b13b8f168`](https://explorer-bradbury.genlayer.com/address/0x34e8335b70546fb37c9f2c06d472208b13b8f168) | 15868 | `c041f51b26654cec30e5d2528d6482d9d7a1be8906c55490f561240d10a19651` |

**Deployed from** commit `9055f93` (`origin/main`, as the transcript states); both files are unchanged since `e25eb22`, and
`tests/fixtures/apibase_*_dispute.9055f93.py.txt` are byte copies pinned by `test_deployment_record_pins_the_deployed_file`.
All five transactions (two deploys, two `set_policy`, one `set_chain`) show ACCEPTED, MAJORITY_AGREE, FINISHED_WITH_RETURN
(hashes `0x`-stripped in `deployment.json`).

**Configured:** as of 2026-11-09T01:42Z, `set_policy("2026-11-04.3", "d1cb13c3fa7ac84fcac3762caba66d208e2d1f9e95f934f4913a82b287b9d4fb")` on both
(superseded below);
`set_chain("8453", "https://mainnet.base.org", USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, payee
`0x50EbDa9dA5dC19c302Ca059d7B9E06e264936480`)` on the payment contract only. `get_config` read back on both (2026-11-09T01:42:04Z)
matches. The policy was re-pinned on both contracts to `2026-11-09.1` (sha256 `0bb0d0c9aef195a349a48c44dc497b9620b3e4fee07989cf41b6931aeef1e3fb`,
`set_policy` transactions `15619d170e87e710d85984799f9529cd25c123c843d370da90a74142bdf142a3` on the receipt contract and
`7686e1adaae54147085b9a554e05fbefc5f6e31cf0433163d68cee36fe92ac03` on the payment contract, both FINISHED_WITH_RETURN, 2026-11-09T14:15:17Z;
`evidence/MEASURED-026-*`), and `get_config` read back on both at 2026-11-09T14:15:40Z shows it (`evidence/MEASURED-024-*`).

**Fees:** each of the five writes carries a quoted fee deposit of 0.100000000000010352 GEN; the charge is `not_measured`.

**Disputes:** 3 as of 2026-11-16, all end-to-end tests by the team with its own wallets (sources team-test and team-test-staged), not
customer disputes: `cf55bfa89b7c387c4f0c0b391e2bdb271cc5b0f162817b6d5073a90b5c65a2a5` on the receipt contract (receipt
`9dbc77f9fd66bcb8714cd064f5681005`, verdict RELEASE, reason `upstream_status_200`),
`be87ea2e4455ee0dbae14fe38ae5f711b699cc2897ec7597522b1bb276619cce` on the payment contract (verdict RELEASE, reason
`receipt_exists:9dbc77f9fd66bcb8714cd064f5681005`; payer and amount are empty in the record, as read) and
`cc9ed6e5c34cc9e869dff4122e6a84c63f5b7713a55977f0dcbde337251d2eda` on the payment contract (verdict REFUND, reason
`paid_without_receipt`, 500000 atomic = 0.50 USDC, 2026-11-10T04:41:20Z). The first two were read back with `get_dispute` in
`evidence/MEASURED-024-*`, the third in `evidence/MEASURED-029-*` (its write: `-028-*`).

The third dispute is staged (source team-test-staged): with the operator's consent the team sent 0.50 USDC from its wallet
`0x18d76291ec67eb0e90a44353a816fd89a5de6ea4` to the payee on Base on 2026-11-10 with no API call, made for this test, so that a
payment without a receipt existed (payment transaction `34e69f9c0721b3bb3d4d7a2c8fab1726c0fce08395ca53d7c6f404d712a5abc6`,
`0x`-stripped; pre-write captures in `evidence/MEASURED-030-*`). It is not a customer payment and not an APIbase failure. The REFUND
is booked and not paid out: APIbase's refund ledger holds it as row `d48a64cd` (`paid_without_receipt`, 0.500000, via
`genlayer_dispute`, status `internal`), because the payer is a team wallet, which APIbase records and does not pay out (APIbase
ruling GD-PAYOUT-1116, 2026-11-16; the rows were not re-read for this record: `check_did_not_run`). No refund transaction is
recorded: the receipt index shows no refund for the payment (2026-11-16T10:26:38Z) and no refunds document is published for the
dispute (HTTP 404, 2026-11-16T10:26:38Z), `evidence/MEASURED-031-*`. The receipt claim is still `nothing_qualified`, with 0 receipts
billed with an upstream status of 500 or more ever and 40023 receipts in the last 30 days, as of 2026-11-10T03:15Z
(`evidence/MEASURED-025-*`).

**`not_measured`:** a refund paid out on Base (the one REFUND is booked and not paid out); `confirm_refund` (v1.1, not
deployed); FINALIZED status of the four D4 transactions (two `set_policy`, two dispute writes), of the D4c dispute write and of the five D3 transactions;
per-transaction charges; a studionet integration run; a full byte comparison of the deployed code (the deploy receipts print the first
4993 bytes of each calldata, which equal the committed files').

**Read it yourself:** a raw `gen_call` of `get_config()` on `https://rpc-bradbury.genlayer.com` against either address returns the
JSON in `evidence/MEASURED-022-*`; `list_recent()` returns the last 200 dispute ids.

## Reproduce

Read the record (no account, no fee): a raw `gen_call` of `get_attestation("0954262009b2f224290261fb68e833acf11f4003c1d52ea31027f4a778e414ef")`
on `https://rpc-bradbury.genlayer.com` against the contract above returns the record in `evidence/MEASURED-019-*`.

## After merge (dispatcher)

- Update the mirror (D-85, never edited directly): after the change is on Provek `main`, one new commit on
  `whiteknightonhorse/apibase-genlayer-attest` whose tree is this directory and whose parent is the mirror's head, pushed as a
  fast-forward and never forced.
- Live site, nothing here changes it: `curl -sS https://provek.dev/ | grep -c 0x1bD4C0EBC9b365905d4EBC84b944d861499afe6E` expects `0`
  (the address is in GitHub docs only).
- GitHub main, one per file: `curl -sS https://raw.githubusercontent.com/whiteknightonhorse/provek/main/README.md | grep -c 0x1bD4C0EBC9b365905d4EBC84b944d861499afe6E`
  (expects 2 or more), the same for `integrations/genlayer-apibase-attest/README.md`, `.../deploy/DEPLOYMENT.md` and
  `.../deploy/deployment.json`.
- Superseded wording, expects `0`: `grep -rn "7572cAB5" README.md integrations docs` outside `deployment.json`'s
  `previous_deployments` and this file.
- Submission: paste `docs/submission/apibase-receipt-attestation-update.md` into the Portal project "APIbase Receipt Attestation".
