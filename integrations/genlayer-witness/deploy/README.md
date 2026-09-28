# Deployment

Not deployed by T-GL-03-contract itself; deployment (Studionet, then Testnet Bradbury) was GL-05's
(dispatcher + operator) and GL-05b's (this record) job — see `PHASE2-RESUME.md`. `deployment.json`
in this directory holds the real, measured fields this file summarizes below.

## Deployment record

**Network:** GenLayer Testnet Bradbury, chain id `4221`, RPC `https://rpc-bradbury.genlayer.com`.

**Contract:** [`0x499eD0E23CbCdC8Fc7735709dca32bCb01638fd6`](https://explorer-bradbury.genlayer.com/address/0x499eD0E23CbCdC8Fc7735709dca32bCb01638fd6),
deployed from commit `5e28d5f933329c124c058996da28b2abd4da5d37` (`origin/main`) by
`0x2c111FCD3082083C9B287DD9DA5995f190968Ef9`. The deploy transaction was ACCEPTED, with validators
in AGREE and execution result FINISHED_WITH_RETURN (its hash, `0x`-stripped for the secret-scan
gate per GL-00 ruling-1, is `deploy_tx` in `deployment.json`).

**Studionet, before the Bradbury deploy:** `gltest --network studionet tests/integration -v -s` —
4 passed (consensus-path integration tests against a real network with real validators; see
`evidence/MEASURED-011-*`).

**Three live records on Bradbury** (all ACCEPTED, read back with `get_result`; full detail and
every transaction hash in `evidence/MEASURED-012-*` and `deployment.json`'s `live_records`):

| result | criterion       | evidence_url                                             | observation      |
|--------|-----------------|-----------------------------------------------------------|-------------------|
| PASS   | `artifact_hash` | the pinned `LICENSE` at the commit above                   | `status=200`      |
| PASS   | `url_reachable` | `https://provek.dev/`                                      | `status=200`      |
| FAIL   | `artifact_hash` | the same `LICENSE`, checked against a deliberately wrong digest | `sha256 mismatch` |

The third record shows the FAIL path on-chain, not merely asserted by a test — a real check of a
false claim, resolved the same way a true one is (`_judge`, one function for both).

**Three known SDK limitations** (`genlayer-py==0.18.0`, the latest release on PyPI at deploy time,
against Bradbury — worked around in the dispatcher's own operational script, **no contract code
changed** for any of them):

1. Bradbury emits transaction status `14` (`LEADER_REVEALING`), which `genlayer-py`'s own
   `TRANSACTION_STATUS_NUMBER_TO_NAME` map does not contain (`genlayer-js` already does). Treated as
   non-terminal while polling.
2. On testnet, a transaction receipt's `tx_data_decoded` field is `None`, so `gltest.utils.
   extract_contract_address` raises `TypeError`. The deployed contract's address was instead read
   from the deploy transaction's own `recipient` field.
3. `gen_call` on Bradbury returns `{"data": <hex>, "status": ...}`, where `genlayer-py==0.18.0`
   expects a bare hex string for a read result. The dispatcher's read helper unwraps `"data"`
   before decoding.

See `evidence/MEASURED-011-*` (studionet) and `evidence/MEASURED-012-*` (Bradbury) for the full,
transcript-sourced detail behind every line above.
