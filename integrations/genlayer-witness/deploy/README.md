# Deployment

Not deployed by T-GL-03-contract itself; deployment (Studionet, then Testnet Bradbury) was GL-05's
(dispatcher + operator) and GL-05b's (this record) job — see `PHASE2-RESUME.md`. `deployment.json`
in this directory holds the real, measured fields this file summarizes below.

## Deployment record

**Network:** GenLayer Testnet Bradbury Phase 2, chain id `4221`, RPC `https://rpc-bradbury.genlayer.com`. GenLayer reset Bradbury on 2026-10-24; the witness contract was redeployed on 2026-10-28. The pre-reset deployment (address, deploy transaction, its three records) is kept in `deployment.json` under `previous_deployments`; its records were not carried over. Toolchain: Bradbury Phase 2 runs the `py-genlayer:babwp9t3…` runner (contract header `# v0.3.0`, then `# { "Depends": "py-genlayer:babwp9t37jw9g4j2bccgn14g6x7x9s1f7dsmh7emvz735pz4zxa0" }`); the documentation's `1jb45…` runner id fails there (every deploy FINISHED_WITH_ERROR), so the contract carries the babwp header (D-79).

**Contract:** [`0x99C23e1794ed35b429161fBEB00967D0c81DC491`](https://scan.bradbury.genlayer.com/address/0x99C23e1794ed35b429161fBEB00967D0c81DC491),
deployed from commit `11474b4cfc94dada3a3e5301d19d1262713027ac` (`origin/main`) by
`0x2c111FCD3082083C9B287DD9DA5995f190968Ef9`. The deploy transaction was ACCEPTED (later FINALIZED), with
validators in MAJORITY_AGREE (5/5) and execution result FINISHED_WITH_RETURN (its hash, `0x`-stripped for the
secret-scan gate per GL-00 ruling-1, is `deploy_tx` in `deployment.json`).

**Fees (consensus v0.6):** every write carries a fee deposit, quoted by the SDK's estimate. Quoted 0.100000000000010352 GEN per
transaction (deploy and `witness` write alike); the unused part is refunded at finalization, and all 10 transactions of the
2026-10-28 session netted 0.001056359060011646 GEN (0.0000984 GEN for the first `witness` write). The node exposes no per-transaction
gas, so no gas figure is recorded. Fields: `fees` in `deployment.json`.

**Studionet, before the pre-reset Bradbury deploy:** `gltest --network studionet tests/integration -v -s` —
4 passed (consensus-path integration tests against a real network with real validators; see
`evidence/MEASURED-011-*`).

**Three records on Bradbury Phase 2, as of 2026-10-28** (all FINALIZED, read back with `get_result`; full detail and
every transaction hash in `evidence/MEASURED-017-*`, `evidence/MEASURED-018-*` and `deployment.json`'s `live_records`):

| result | criterion       | evidence_url                                             | observation      |
|--------|-----------------|-----------------------------------------------------------|-------------------|
| PASS   | `artifact_hash` | the pinned `LICENSE` at the commit above                   | `status=200`      |
| PASS   | `url_reachable` | `https://provek.dev/`                                      | `status=200`      |
| FAIL   | `artifact_hash` | the same `LICENSE`, checked against a deliberately wrong digest | `sha256 mismatch` |

The third record shows the FAIL path on-chain, not merely asserted by a test — a real check of a
false claim, resolved the same way a true one is (`_judge`, one function for both).

**Three known tooling limitations** on Bradbury Phase 2 (no contract code changed for any of them):

1. The `genlayer` CLI read path answers "gen_call does not exist" on the network's default RPC. Reads were captured as raw
   `gen_call` on `https://rpc-bradbury.genlayer.com`, which is why the page and the relay read through `deployment.json`'s
   `rpc_url` and not the SDK preset URL (`web/src/witnessChainConfig.js`).
2. The CLI argument parser turns an empty string and 64 zeros into the number 0; the retried writes used the `s#` string-argument
   rule (two earlier attempts FINISHED_WITH_ERROR and wrote no record).
3. `eth_getTransactionByHash` returns null for consensus transaction ids on this RPC, so per-transaction gas is not available.

The three limitations of the pre-reset deployment (`genlayer-py==0.18.0`) are kept in `previous_deployments`.

See `evidence/MEASURED-017-*` and `evidence/MEASURED-018-*` (Bradbury Phase 2), `evidence/MEASURED-011-*` (studionet) and
`evidence/MEASURED-012-*` (pre-reset Bradbury) for the full, transcript-sourced detail behind every line above.
