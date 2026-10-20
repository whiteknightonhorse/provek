# APIbase Receipt Attest — a GenLayer Intelligent Contract

Validators attest that an APIbase paid-call receipt matches the USDC transfer on Base.

**What it is.** `ApibaseReceiptAttest` (`contracts/apibase_receipt_attest.py`) reads one public JSON
receipt published by APIbase for a paid tool call, asks a configured Base JSON-RPC node for the
transaction that receipt names, and records `PASS`, `FAIL` or `NOT_FOUND`. GenLayer's leader/validator
consensus replaces a single process's word with several independent fetches.

**What it is not.** There is no LLM in it. It never makes a paid call and never spends anything. It
does not judge the tool's response, only that the payment the receipt claims is the payment on the
chain. It covers one rail and billed calls only (see *v0 limits*). It does not take part in Provek's
scoring and shares no code with `src/`.

**The use case, in three sentences.** An agent pays APIbase for a tool call and gets a receipt that
says who paid whom, how much, and in which Base transaction. Anyone — the agent, its operator, an
auditor — can ask the contract about that receipt id, with no account and no permission. The answer is
a consensus-backed record that the receipt and the chain agree, or that they do not.

**Where this code lives.** The source of record is `integrations/genlayer-apibase-attest/` in
[`whiteknightonhorse/provek`](https://github.com/whiteknightonhorse/provek/tree/main/integrations/genlayer-apibase-attest),
where Provek's gates check it (D-66, beside D-63 for the first contract). The same directory is to be
published, with its history, as `whiteknightonhorse/apibase-genlayer-attest` — a read-only mirror made
with `git subtree split`, created by the follow-up task T-GA-02 and not by the one that wrote this
file (the procedure is D-64's). The mirror is never edited directly: every change enters Provek and is
re-split. Paths such as `DECISIONS.md`, `docs/adr/` and `evidence/RED-*` refer to the root of the Provek
repository.

## The receipt: `apibase-receipt/1`

The contract fetches `{receipt_base_url}{receipt_id}.json`. `receipt_id` is 32–64 lowercase hex
characters. The document, as the contract reads it (a concrete instance, with a real transaction hash, is
`tests/fixtures/receipt_pass.json`; the repository secret scan excludes that one fixtures directory
because a transaction hash has the shape of a raw key):

```json
{
  "schema": "apibase-receipt/1",
  "rail": "x402-base",
  "chain_id": 8453,
  "payment_tx": "0x<64 hex characters>",
  "payer": "0x688130810f0bede38742b66e7a443274c01d4213",
  "payee": "0x781dfd3f2687f8e5656313b2179fdefdf99d339d",
  "asset": "USDC",
  "amount_atomic": "1000000",
  "billed": true,
  "tool": "example.tool",
  "upstream_status": 200,
  "response_sha256": "<64 hex characters>"
}
```

Validation is strict: `schema` must be exactly `apibase-receipt/1`; `chain_id` and `upstream_status`
integers; `payment_tx` `0x` plus 64 hex; `payer` and `payee` `0x` plus 40 hex (stored lowercased);
`asset` exactly `USDC`; `amount_atomic` a decimal string (USDC has six decimals, so `1000000` is 1 USDC);
`billed` a boolean; `response_sha256` 64 hex. The first key that fails is named in the revert.
Receipts publish payer, payee, amount, transaction and the SHA-256 of the response — never the response.

## The judge

One function, `_judge`, is called by the leader, by every validator and by `attest()` after
consensus. `transfers` are the `Transfer(address,address,uint256)` logs emitted by the configured
chain's USDC contract inside the transaction; amounts are compared as integers.

| Observation | Outcome | Record `result` / `observation` |
|---|---|---|
| Receipt fetch failed, or HTTP status ≠ 200, or the RPC answered with an error | revert `receipt <id> is not readable at APIbase (http=<n>)` | none |
| Receipt malformed | revert `… not attestable by this contract: malformed receipt: <key>` | none |
| `rail` ≠ `x402-base` | revert `… unsupported rail <rail>` | none |
| `billed` is not true | revert `… not billed` | none |
| `chain_id` not configured | revert `… chain <id> not configured` | none |
| Node returns `null` for the transaction | recorded | `NOT_FOUND` / `tx_not_found` |
| Transaction status ≠ 1 | recorded | `FAIL` / `tx_reverted` |
| A transfer equals `[payer, payee, amount]` | recorded | `PASS` / `payment_matches` |
| Transaction succeeded, no such transfer | recorded | `FAIL` / `no_matching_transfer` |

A validator agrees iff `_judge` gives the same answer on its own fetches, the receipt body hashes
(`receipt_sha256`) are equal, and the matched transfer is the same. A validator whose own fetch raises
votes `False` and no verdict is made: nobody could check is not the same as the claim being false
(CLAUDE.md invariant 1, named in the contract's docstring). `NOT_FOUND`, `FAIL` and a revert are three
different things on purpose.

## Interface

- `__init__(operator, receipt_base_url)`; the URL must be http(s) and end in `/`.
- `set_chain(chain_id, rpc_url, usdc)` — operator only; `usdc` is stored lowercased.
- `attest(receipt_id) -> attest_id` — **permissionless** (D-66). `attest_id` is
  `sha256(json([receipt_id, checked_at, sender]))`; the same sender asking in the same block time reverts as a duplicate.
- Views: `get_attestation(attest_id)`, `list_by_receipt(receipt_id)` (JSON list, `[]` default),
  `get_chain(chain_id)`, `get_config()` (JSON: operator, receipt base URL, configured chain ids).
- The record (`Attestation`) carries `receipt_id`, `receipt_sha256`, `rail`, `chain_id`, `payment_tx`,
  `payer`, `payee`, `amount_atomic`, `tool`, `upstream_status`, `billed`, `response_sha256`, `result`,
  `observation`, `checked_at`, `requester`.

## Commands

Run from this directory, with the isolated Python 3.12 toolchain of D-63 (the door uses `~/orchestra/glenv`):

```
python3 scripts/check_genvm_lint.py          # genvm-lint check, with the four named E010 warnings
python3 -m pytest tests/direct -v            # direct-mode tests: mocks only, no network
gltest --network studionet tests/integration # live; skipped unless ATTEST_CONTRACT and APIBASE_RECEIPT_ID are set
```

`genvm-lint check` itself has no allowlist, so `scripts/check_genvm_lint.py` runs it with `--json` and
demands that the warning set be exactly the four known false positives: the linter's reachability check
does not recognise the `import genlayer.gl.vm as glvm; glvm.run_nondet_unsafe(...)` alias form, so each
of the two closures reports its `gl.nondet.web.get` and `gl.nondet.web.post` as E010. Any other shape is red.

`tests/fixtures/rpc_receipt_real_base_usdc.json` is a real `eth_getTransactionReceipt` answer from
`https://mainnet.base.org` (transaction `0xa7055e5e…bf58`, block 52589696): two logs, one of them a USDC
transfer of 1 USDC; `test_parse_transfers_golden_vector` parses it.

## v0 limits

- **One rail**: `x402-base`. An MPP/Tempo receipt is refused (`unsupported rail`), not attested.
- **Billed calls only**: `billed: false` is refused (`not billed`).
- **One asset**: USDC, at the address configured per chain.
- **Receipts are fetched, not signed**: the contract trusts neither the receipt nor the chain alone; it
  checks that they agree. A receipt APIbase never published is `not readable`.
- **It attests payment, not service**: `response_sha256` and `upstream_status` are copied into the
  record for whoever holds the response; the contract does not see it.

## The RPC trust assumption

Every validator asks the same JSON-RPC URL, held in storage per chain id and replaceable by the
operator alone with `set_chain`. The contract therefore proves "the configured node says so". An
operator who points a chain at a node that lies can make it attest a transfer that did not happen.
The URL is public (`get_chain`), which makes the assumption auditable; letting each validator choose its
own node would remove it and is a different, later design. At deployment the Base endpoint is
`https://mainnet.base.org`.
