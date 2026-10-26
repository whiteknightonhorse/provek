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
where Provek's gates check it (D-66, beside D-63 for the first contract). The same directory is published, with its
history, as `whiteknightonhorse/apibase-genlayer-attest` — a read-only mirror made with
`git subtree split` (the procedure is D-64's). The mirror is never edited directly: every change enters Provek and is
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

## ApibaseReceiptAttest — contract reference

The contract file keeps short docstrings (gas, see the last paragraph of this section). The text below is the original
documentation from commit `774a184`, verbatim.

### Narrative

```text
APIbase Receipt Attest — a GenLayer Intelligent Contract.

WHAT THIS IS. A consensus-backed check that an APIbase paid-call receipt tells the truth about the
money. APIbase publishes, for each paid tool call, a small JSON receipt (`apibase-receipt/1`, see
README.md) that names a payer, a payee, an amount of USDC and the Base transaction that moved it.
Anyone may ask this contract about a receipt id (`attest(receipt_id)`); the leader fetches the
receipt from `receipt_base_url`, asks the configured Base JSON-RPC for that transaction's receipt,
and reports whether the chain holds a USDC `Transfer(payer -> payee, amount)` inside it. Validators
repeat both fetches themselves and agree only if they saw the same thing. The verdict is written
to storage as an `Attestation` nobody can edit afterwards.

WHAT THIS IS NOT. There is no LLM anywhere in this contract. It never makes a paid call to APIbase
and never spends anything: it reads one static JSON document and asks a chain node for one
transaction receipt. It does not attest that the tool's response was good, only that the payment
the receipt claims is the payment on the chain; `response_sha256` is carried into the record so a
holder of the response can check it themselves, nothing more. v0 covers ONE rail (`x402-base`) and
BILLED calls only (`billed is true`); an MPP/Tempo receipt, or a call that was not billed, is
refused with a named reason rather than attested as something it is not.

TRUST ASSUMPTION, STATED. The chain is reached through ONE JSON-RPC URL per chain id, held in
storage and updatable by the operator alone (`set_chain`). Every validator asks that same URL, so
the contract proves "the configured node says so", not "the chain says so": an operator who points
`rpc_url` at a node that lies can make the contract attest a transfer that did not happen. The
URL is public (`get_chain`) so the assumption is auditable; removing it would mean validators each
choosing their own node, which is a different and later design.

WHY A CUSTOM VALIDATOR, NOT `strict_eq`. `strict_eq` compares the leader's whole output to the
validator's byte for byte. The receipt observation carries fields that can legitimately differ
between two honest nodes reading the same chain (a log list that includes unrelated contracts'
events, RPC extras) and, worse, it cannot distinguish "the validator saw something different" from
"the validator could not see anything". `_judge` below is the one deterministic function leader
and validator both call, so the verdict rule lives in exactly one place; the validator agrees iff
`_judge` gives the same answer on its own fetches, the receipt body hashes match, and the matched
transfer tuple is the same.

CONSENSUS SEMANTICS, NAMED EXPLICITLY. Three different outcomes must not be confused
(CLAUDE.md invariant 1: a missing measurement is never a pass, and never silently a fail):

* `FAIL` means the instrument worked and the claim is false: the transaction exists but reverted
  (`tx_reverted`), or it succeeded and holds no matching USDC transfer (`no_matching_transfer`).
* `NOT_FOUND` means the node answered and does not know the transaction (`tx_not_found`). It is
  recorded, not hidden: a payment that the configured node cannot see is evidence of its own.
* A revert (no record) means there is nothing to attest: the receipt is not readable at APIbase,
  or it is a shape this v0 contract refuses (`unsupported rail`, `not billed`, `chain not
  configured`, `malformed receipt`). Nobody is told "the payment is false" about a receipt that was
  never in scope.

Separately, a validator whose OWN fetch raises returns `False` without constructing any verdict:
"nobody could check" must not be turned into "the claim is false", and GenVM rotates the leader.

FIELD NAME NOTE. `genlayer.gl.nondet.web.Response` has `status`, not `status_code` (the same
finding as the witness contract next door; running its direct tests against the pinned SDK is
what showed it). This contract uses `response.status`.
```

### Storage

```text
See the module docstring. Storage: `operator` (fixed at construction), `receipt_base_url`
(receipts live at `{receipt_base_url}{receipt_id}.json`), `chains` (chain id -> `ChainConfig`,
operator-updatable), `records` (attest_id -> `Attestation`, append-only), `index`
(receipt_id -> JSON list of attest_ids; a list inside a `TreeMap` is kept as a JSON string, the
same workaround the witness contract uses).
```

### `set_chain`

```text
Operator-only: configure (or replace) the JSON-RPC endpoint and USDC address for a
chain id. `usdc` is stored lowercased.
```

### `attest`

```text
Request one consensus-backed attestation. PERMISSIONLESS: any sender may ask, and the
question has one answer per receipt, so who asks adds nothing. Reverts before consensus for
a malformed `receipt_id` or a duplicate `attest_id`; after consensus for the cases the
module docstring lists. Returns the `attest_id`.
```

### `get_attestation`

```text
The published record for `attest_id`; reverts for an unknown id — a missing record is a
caller error to surface, not an empty value to fabricate.
```

### `list_by_receipt`

```text
JSON list of every `attest_id` published for `receipt_id`, in request order, or `"[]"`.
```

### `get_chain`

```text
The configured endpoint and USDC address for `chain_id`; reverts for an unknown chain.
```

### `get_config`

```text
JSON: operator, receipt_base_url, configured chain ids (sorted).
```

### Deployed code is the file

The deployed bytes are the committed file bytes at the deploy commit, verifiable with `sha256sum
integrations/genlayer-apibase-attest/contracts/apibase_receipt_attest.py` at that commit against the code shown by the
explorer. The Bradbury per-transaction gas cap is 16 777 216 (measured 2026-10-20) and gas is about 778 per byte, so
every contract file in this repo is kept at or under 19 000 bytes and the deploy gate is `eth_estimateGas` <= 16 000 000
with the exact deploy arguments. `tests/direct/test_apibase_receipt_attest.py` holds the size ceiling, the docs-only AST
comparison against `774a184`, and the docstring limits.
