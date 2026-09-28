# Provek Evidence Witness (GenLayer Intelligent Contract)

A reusable GenLayer Intelligent Contract, built beside — not inside — the
[Provek](https://provek.dev/) repository this directory lives in
(`integrations/genlayer-witness/` in `whiteknightonhorse/provek`). It gives a single
machine-checkable evidence claim (does a URL answer? does the artefact at a URL match a declared
hash?) a second, consensus-backed opinion, independent of Provek's own single-process check.

This file follows the operator's brief (`taskloop/briefs/GL-00-operator-task.txt`, section
"README") section by section. The governing design decisions this contract implements are recorded
in full in `taskloop/disputes/GL-00-genlayer-witness-design.ruling-1.md` / `...ruling-2.md` /
`...ruling-3.md`; `DECISIONS.md` D-63 and `docs/adr/ADR-0012-a-second-isolated-toolchain-is-admitted-without-merging-into-the-first.md`
record how this integration is wired into the rest of the repository's gates without merging into
it. This README does not repeat those documents' reasoning in full — it states the contract's
externally-visible behaviour, points at the source of record for each design choice, and gives the
commands to reproduce every claim made here.

## Directory layout

```
integrations/genlayer-witness/
  README.md                  — this file
  pyproject.toml             — pytest rootdir + the `integration` marker
  requirements.txt           — pinned versions, for human readers (CI's own hash-pinned set lives
                               in requirements/ci-genlayer.{in,txt} at the repository root, D-63)
  gltest.config.yaml         — network config for `gltest` (localnet, studionet)
  scripts/
    check_genvm_lint.py      — the actual lint gate (see "Known genvm-lint check warnings" below)
  contracts/
    provek_evidence_witness.py
  tests/
    direct/                  — `pytest tests/direct -v` (no network, no real GenVM)
    integration/              — `gltest --network studionet tests/integration -v -s` (real
                                consensus; not run at the door, not run in CI — dispatcher-only)
    fixtures/
      digest_golden.json     — one digest formula, two readers (this repository's 3.10
                               `tests/test_genlayer_witness_digest_matches_provek.py` reads
                               `src.witness.witness._digest`, this directory's 3.12 direct tests
                               read the contract's own `_url_reachable_digest`)
  deploy/
    README.md                — the Deployment record (Bradbury address, explorer, three live
                               records, three named SDK limitations) — see "How to deploy" below
    deployment.json           — the same record's real, measured fields
```

## 1. What is Provek Evidence Witness

`ProvekEvidenceWitness` is a GenLayer Intelligent Contract that accepts a request to check one of
exactly two machine-checkable criteria about a public URL — `url_reachable` (does the URL answer
with a 2xx status) and `artifact_hash` (does the bytes at the URL hash to a declared sha256) — and
publishes a structured, permanent PASS/FAIL result once GenLayer's leader/validator consensus has
agreed on it. Every check is requested by a single, fixed `operator` address set once at
construction (see "Why this is not part of Provek scoring" for why there is no permissionless
mode). Results are stored on-chain, immutably, and can be read back at any later time by
`get_result(witness_id)` or listed per subject by `list_by_subject(subject_id)`.

It is deployed on **GenLayer Testnet Bradbury** (chain id `4221`) at
[`0x499eD0E23CbCdC8Fc7735709dca32bCb01638fd6`](https://explorer-bradbury.genlayer.com/address/0x499eD0E23CbCdC8Fc7735709dca32bCb01638fd6) —
see "How to deploy" and `deploy/README.md` for the full, measured record.

## 2. Why it exists

Provek's own witness mechanism (`src/witness/witness.py`, `WitnessRecord` v0) runs an anonymous,
credential-free HTTP GET from a single untrusted process (this repository's own CI/cron host) and
publishes whatever that one process happened to observe — reproducible in principle (anyone can
repeat the same GET), but backed, in practice, by exactly one observer. `ProvekEvidenceWitness`
adds a second, structurally different guarantee over the same two criterion types: GenLayer's
leader/validator equivalence principle requires multiple independent validators, running on
different infrastructure, to each fetch the evidence themselves and agree with the leader's
verdict before any result is written to chain-verified state (see "How GenLayer consensus is
used"). It is a *reusable verification primitive*, published for GenLayer's own Intelligent
Contracts showcase, not a component Provek's pipeline calls — see "Why this is not part of Provek
scoring".

**Why no LLM.** Both criteria resolve entirely from bytes already on the wire — an HTTP status
code, a sha256 of a response body. There is no judgement call here an LLM's reasoning would add
evidence for; using one would only add latency and a second, unauditable source of disagreement
between leader and validators. GenVM's own equivalence-principle guidance treats a custom
leader/validator function pair as the general mechanism and LLM-prompt-based comparison as a
convenience layer for cases that need one to tolerate non-identical outputs — this contract is
exactly the case that does not, because `_judge` below is a pure, deterministic function of bytes
already observed.

## 3. Input format

```python
witness(subject_id: str, criterion: str, evidence_url: str, expected: str) -> str
```

A `@gl.public.write` method, callable only by the fixed `operator` address (reverts otherwise —
see "Why this is not part of Provek scoring"). Returns the new record's `witness_id`. Arguments are
four flat strings, not a dict — this keeps `genlayer write --args`/calldata plumbing simple; the
correspondence to Provek's own dict-shaped criterion is in the table below.

| Argument       | Constraint                                                                 | Provek `WitnessRecord.criterion` field |
|----------------|-----------------------------------------------------------------------------|-----------------------------------------|
| `subject_id`   | non-empty string, ≤ 256 characters                                          | `subject_id` (top-level, not part of the criterion dict) |
| `criterion`    | exactly `"url_reachable"` or `"artifact_hash"` — the same two names as `src.witness.witness.SUPPORTED_CRITERIA` | `criterion["type"]` |
| `evidence_url` | http(s) URL, ≤ 2048 characters, no whitespace/control characters, a host, no userinfo | `criterion["url"]` |
| `expected`     | `""` for `url_reachable`; a 64-character hex sha256 (`strip().lower()`'d) for `artifact_hash` | `criterion["sha256"]` (`artifact_hash` only; `url_reachable` has no equivalent field) |

All four constraints above, plus a duplicate `witness_id` (records are immutable — a repeat
request is a caller error, not a re-check), are rejected by a deterministic `revert` — the
transaction is rolled back, no record is written, and no consensus round runs at all. This is a
different outcome from a PASS/FAIL: a revert means the request itself was malformed, never that a
claim was checked and found false. See `tests/direct/test_provek_evidence_witness.py`'s revert
tests for every one of these shapes exercised individually.

## 4. Output format

```python
get_result(witness_id: str) -> WitnessResult   # @gl.public.view, raises if witness_id is unknown
list_by_subject(subject_id: str) -> str         # JSON array of witness_ids, request order, "[]" if none
supported_criteria() -> list[str]               # ["artifact_hash", "url_reachable"]
```

`WitnessResult` fields:

| Field             | Meaning                                                                                     |
|-------------------|-----------------------------------------------------------------------------------------------|
| `subject_id`      | echoed from the request                                                                       |
| `criterion`       | echoed from the request                                                                       |
| `evidence_url`    | echoed from the request                                                                       |
| `expected`        | echoed from the request (normalized: `strip().lower()`'d for `artifact_hash`)                 |
| `result`          | `"PASS"` or `"FAIL"` — never a third value; see "How validators verify the result"           |
| `evidence_digest` | see below — not always a hash of fetched bytes                                                |
| `checked_at`      | the requesting transaction's own datetime, `gl.message_raw["datetime"]` — **not**
              `datetime.now()`, which is equally deterministic on GenVM but is the exact temporal pattern `genvm-lint` flags, and the field is named explicitly here rather than left to a reader's guess |
| `observation`     | a short human string — `"status=200"`, `"sha256 mismatch"`, `"unreachable"`, `"too_large"` — the one field that keeps the nuance a bare PASS/FAIL would lose (see "How GenLayer consensus is used" on 403/429/5xx) |

**`evidence_digest`, by criterion and outcome.** For `artifact_hash`, when the fetch succeeded
(`fetch == "ok"`): the sha256 of the bytes actually fetched — the same value whether the result was
PASS or FAIL, so a third party who fetches the same bytes reaches the identical published digest
either way, exactly `src.witness.witness._check_artifact_hash`'s own choice. For `url_reachable`:
`sha256("url_reachable|" + url + "|" + result + "|" + checked_at)` — byte-for-byte
`src.witness.witness._digest("url_reachable", url, result, checked_at)`, proven equal by a shared
golden vector (`tests/fixtures/digest_golden.json`, read by both this contract's direct tests and
this repository's own `tests/test_genlayer_witness_digest_matches_provek.py`, D-63 §3). For
`artifact_hash` when the fetch itself failed (`fetch` is `"error"` or `"too_large"`): a **named
departure** from Provek's own formula. Provek's `_check_artifact_hash` hashes
`"artifact_hash|url|unreachable|" + str(e) + "|checked_at"`, where `str(e)` is the caught
exception's own message; inside a GenVM nondet block the original exception does not survive the
boundary (`leader_fn` catches it and returns a plain observation dict), so a **fixed token** — the
literal string `"error"` or `"too_large"` — stands in for `str(e)`. This is a deliberate,
documented substitution, not an oversight (see the contract's own `_unreachable_digest` docstring).

**Correspondence to Provek's `WitnessRecord`** (`src/witness/witness.py`) — the schema this
contract's result could, in a later and separately-decided step, become one input to (no such
bridge exists today; see "Why this is not part of Provek scoring"):

| `WitnessResult` (this contract)                | `WitnessRecord` (Provek)              | Relationship |
|-------------------------------------------------|-----------------------------------------|--------------|
| `witness_id` (the `witness()` return value, the key in `records`) | `witness_id`         | Provek's is a random `uuid4`; this contract's is `sha256(json.dumps([subject_id, criterion, evidence_url, expected, checked_at, sender], sort_keys=True))` — **deterministic**, because on-chain code has no source of randomness a validator could reproduce |
| `subject_id`                                     | `subject_id`                            | identical |
| `criterion` (flat string)                        | `criterion` (dict: `type`, `url`, `sha256`?) | this contract's four flat request args together carry the same information the dict holds — see the input table above |
| `result`                                         | `result`                                | identical `"PASS"`/`"FAIL"` vocabulary |
| `evidence_digest`                                | `evidence_digest`                       | same formula for `artifact_hash` PASS/FAIL-with-bytes and for `url_reachable`; named departure for `artifact_hash` FAIL-without-bytes (above) |
| `checked_at`                                     | `checked_at`                            | Provek uses `datetime.now(timezone.utc).isoformat()`; this contract uses the requesting transaction's own `gl.message_raw["datetime"]` — both are "the moment this check ran", read from a different clock |
| `observation`                                    | *(no equivalent field)*                 | new here — Provek's schema (spec 4.2-bis point 4) has no field for this; adding it was a deliberate choice to keep the nuance a bare PASS/FAIL loses, not an extension of Provek's own published schema |
| *(no equivalent field)*                          | `witnessed_fee_paid`                    | Provek's is always `False` in v0; this contract has no payable method and no fee concept of any kind — not even a placeholder field |

## 5. How GenLayer consensus is used

`witness()` performs all deterministic validation (input shape, operator check, duplicate check)
*before* entering GenVM's non-deterministic block — so a malformed request reverts without ever
reaching consensus. The actual evidence fetch runs inside
`glvm.run_nondet_unsafe(leader_fn, validator_fn)`
(`import genlayer.gl.vm as glvm`, matching the alias form GenLayer's own boilerplate
`contracts/PatternTest.py` uses — see `taskloop/disputes/GL-00-genlayer-witness-design.ruling-2.md`
§2 "Why not `strict_eq`" for why this alias form was chosen over the fully-dotted
`gl.vm.run_nondet_unsafe`).

The **leader** calls `gl.nondet.web.get(evidence_url)` once, from its own infrastructure, and
normalizes the response into a plain dict of primitives (`url`, `status`, `body_sha256`, `bytes`,
`fetch`) — never raising: any exception from the fetch itself (DNS failure, connection refused,
timeout) is caught and turned into `fetch="error"`, a normal observation, not a crash. This
observation, unchanged, becomes the value consensus agrees or disagrees on.

**403/429/5xx is an observation, not a failure to observe**, named explicitly because it is a
deliberate departure from this project's own usual "the server declined to say" treatment
(`tasks/lessons.md` L-11, which this project applies elsewhere by collapsing 403/429/5xx into an
undetermined state rather than a hard failure): `_judge` turns a non-2xx status into a normal
`FAIL` with `observation="status=NNN"`, the same "everything that did not confirm is a FAIL" rule
`src/witness/witness.py:154` applies. It cannot collapse into "undetermined" here, because the
result has to be one of exactly two `Result` values written to consensus-agreed on-chain storage —
`observation` is where the nuance (`"status=429"`, not a bare `FAIL`) survives instead of being
lost. A genuinely undetermined outcome — nobody could observe the URL at all — is a different path
entirely; see the next section.

## 6. How validators verify the result

Every validator independently runs `validator_fn(leader_result)` against the leader's proposed
observation. The verdict itself — PASS or FAIL — is computed by one function, `_judge(criterion,
expected, observation)`, called identically by the leader (to shape its own return value's
downstream use) and by every validator; this keeps the actual PASS/FAIL rule living in exactly one
place, checked by the golden-vector and criterion-coverage tests in
`tests/direct/test_provek_evidence_witness.py`. `validator_fn`'s own job is narrower: decide
whether it **agrees** the leader reached the right verdict, by fetching the same URL itself and
comparing.

**Why a custom validator, not `strict_eq`.** `strict_eq` can only ask "is the validator's output
byte-identical to the leader's" — it cannot distinguish "the validator observed something
different" from "the validator could not observe anything at all", and it cannot reject a
malformed leader result before comparing it. A custom `leader_fn`/`validator_fn` pair is GenVM's
own documented "recommended for most contracts" mechanism, and is what this contract uses instead.

`validator_fn` returns `False` (disagree) if: the leader's result is not a well-formed `Return`: if
the observation is not a dict with the expected keys and a recognized `fetch` state; if the
validator's own `gl.nondet.web.get(evidence_url)` call raises an exception; or if the validator's
own independently-computed verdict (via the same `_judge`) disagrees with the leader's, or — for
`artifact_hash` — if the validator's own fetched `body_sha256` differs from the leader's even when
both reached the same PASS/FAIL verdict (catches a leader that guessed the right verdict from the
wrong bytes).

**The validator's own fetch failing is "undetermined", never "the claim is false".** If the
validator's own `gl.nondet.web.get` call raises, `validator_fn` returns `False` without
constructing any `FAIL` — this is GenVM's documented behaviour for a `run_nondet_unsafe` call: an
uncaught exception inside a validator closure is also treated as *Disagree*, and this contract
names that explicitly rather than leaving it implicit (see the contract's own docstring at that
line). When enough validators disagree this way, GenVM rotates leaders; if the round as a whole
cannot reach agreement, the transaction goes **`UNDETERMINED`** and no `WitnessResult` is ever
written — a state Provek's own `WitnessRecord` schema has no equivalent for, because Provek's
single-process checker has no consensus round to fail to reach. `tests/integration/test_provek_evidence_witness_live.py::test_url_reachable_goes_undetermined_against_an_unreachable_url`
exercises exactly this path against a real, unresolvable `.invalid` host on Studionet.

## 7. Why this is not part of Provek scoring

`ProvekEvidenceWitness` does not compute a Provek Score, does not implement any part of Provek's
scoring methodology, and is not imported by, called from, or wired into `src/pipeline.py` or any
cohort re-measure — `tests/test_genlayer_witness_is_isolated.py` AST-scans every module under
`src/` and `scripts/` and asserts none of them imports anything from `integrations/`, the same
mechanism `ADR-0002` already uses to keep `src/scorer` free of transport imports, extended to this
second boundary (D-63 §2, `ADR-0012`). The reverse direction is not forbidden: this contract's own
module docstring names Provek and `src/witness/witness.py`'s schema by name, because it exists
*because of* that schema — only `src/`/`scripts/` reaching *into* `integrations/` would let an
experimental, isolated contract silently move Provek's own scoring, which is the direction this
isolation actually guards against.

It is a separate, reusable verification *primitive* that could, in a later and separately-decided
step, become one input to a `WitnessRecord` — no such bridge exists yet, and none is added here
(see "Limitations" below). `witness()` is also restricted to a single fixed `operator` address, the
same "checks run only by joint request, never on this contract's own initiative" discipline
`src/witness/witness.py`'s own docstring calls A-9 — there is no permissionless mode in this
version, so this contract cannot be pointed at arbitrary subjects by anyone but the address that
deployed it.

## 8. How to run direct tests

No network, no real GenVM WASM boundary — `genlayer-test`'s direct-mode harness runs the contract
in-process against a Python 3.12 interpreter, with `gl.nondet.web.get` calls answered from
`direct_vm.mock_web()` mocks (every test in `tests/direct/` uses one). This is the tier
`scripts/push.sh`'s door step `9/9` and `.github/workflows/gates.yml`'s `genlayer` job both run.

```
~/orchestra/glenv/bin/python3 -m pytest tests/direct -v
~/orchestra/glenv/bin/python3 scripts/check_genvm_lint.py
```

Both commands need the isolated Python 3.12 venv at `~/orchestra/glenv` (this repository's own
interpreter is 3.10 — see `GL-harness-notes.md`), and
`~/.cache/gltest-direct/genvm-universal-v0.2.16.tar.xz` pre-populated in the direct-mode SDK cache
(the auto-downloader 404s on every fresh host against the current `genvm` release, for any project,
not something specific to this one — checked against the committed digest
`genvm-universal-v0.2.16.sha256`, D-63 §4).

`scripts/check_genvm_lint.py` — not a bare `genvm-lint check contracts/provek_evidence_witness.py`
— is the actual gate: `genvm-lint` has no baseline/allowlist mechanism, so any surviving warning
makes a bare invocation exit 1 permanently, including the two confirmed false positives named
below. The script asks the narrower, honest question a CI status can actually answer: is the
warning set *exactly* the two named, understood false positives, and did SDK-semantic validation
pass — any other shape (a third warning, a moved line, a changed message) is a real failure. See
"Known `genvm-lint check` warnings" below for what the two warnings are and why they are false
positives.

## 9. How to run integration tests

Real leader, real validators, real `gl.nondet.web.get` — against a real GenLayer network. **Not**
run at the door, **not** run in CI (see "Limitations"): they need a funded account on a real
network, which this repository's own automated gates never hold.

```
cd integrations/genlayer-witness
gltest --network studionet tests/integration -v -s
```

Marked with the `integration` pytest marker (registered in `pyproject.toml`), so a bare `pytest`
run of this directory never picks these up by accident. `tests/integration/fixtures.py`'s
`deploy_provek_evidence_witness` deploys a fresh contract instance per test (via
`gltest.get_contract_factory("ProvekEvidenceWitness").deploy(...)`, resolved by class name, not
file stem), so `witness()`'s duplicate-id and operator-only checks never collide across tests in
the same run. Last run against Studionet: 4 passed (see `evidence/MEASURED-011-*` and
`deploy/README.md`).

## 10. How to deploy

**Studionet** (hosted, built-in faucet, used for the integration test tier above): `gltest`'s own
`get_contract_factory(...).deploy(args=[...])` — see `tests/integration/fixtures.py` — deploys
fresh against whatever network `gltest --network <name>` names; no separate deploy step is needed
for Studionet beyond running the integration tests themselves.

**Testnet Bradbury** (the canonical deployment target — a public explorer, unlike Studionet, whose
own state is not proven stable across resets): deployment needs a funded account and its private
key, held outside this repository (`~/orchestra/gl/key.hex`, never committed, never read by any
automated gate — GL-00 ruling-2 §"Сети"/"Секреты"). This repository's tests and gates make **no
GenLayer network call of any kind** and never read that key; only the dispatcher, operating
outside the automated door, performs a live deployment. The dispatcher's actual deploy path uses
`genlayer_py.create_client(chain=testnet_bradbury, account=...)` directly —
`client.deploy_contract(code=..., args=[CalldataAddress(acct.address)])` followed by
`client.wait_for_transaction_receipt(tx, status=TransactionStatus.ACCEPTED, ...)` — rather than the
`genlayer` CLI form (`genlayer deploy --contract ... --rpc ...`) the boilerplate documentation
otherwise leads with; this was a workaround for `gltest.utils.extract_contract_address` raising
`TypeError` against a testnet receipt with `tx_data_decoded == None` (limitation 2, below), not a
change to the contract's deploy semantics. **No contract code was written, or needs to be written,
specifically to support this deploy path** — it is a difference in which client library the
dispatcher's own operational script uses.

**The real, measured Bradbury deployment** — network, chain id, RPC, contract address, explorer
URL, deploy transaction, the three live PASS/PASS/FAIL records, and the three SDK workarounds
needed to reach them — is recorded in `deploy/README.md` ("Deployment record") and
`deploy/deployment.json`, both written by GL-05b directly from the dispatcher's own transcripts.
This section does not repeat that record; see it for the full, current detail. In short: **network**
GenLayer Testnet Bradbury, chain id `4221`, RPC `https://rpc-bradbury.genlayer.com`; **contract**
[`0x499eD0E23CbCdC8Fc7735709dca32bCb01638fd6`](https://explorer-bradbury.genlayer.com/address/0x499eD0E23CbCdC8Fc7735709dca32bCb01638fd6);
**deploy tx** ACCEPTED, validators AGREE, execution FINISHED_WITH_RETURN, from commit
`5e28d5f933329c124c058996da28b2abd4da5d37`.

## 11. Example request/result

Taken verbatim from the live Bradbury deployment's first record (`deploy/deployment.json`,
`live_records[0]`; full transaction detail in `evidence/MEASURED-012-*`).

**Request** (`witness()`, sent by the operator):

```python
contract.witness(
    args=[
        "git:whiteknightonhorse/provek",   # subject_id
        "artifact_hash",                    # criterion
        "https://raw.githubusercontent.com/whiteknightonhorse/provek/5e28d5f933329c124c058996da28b2abd4da5d37/LICENSE",  # evidence_url
        "c61e9a12ff00f711d1d42a15430de1f7191c369adcc20cab7d33e7c1cbcf8660",  # expected
    ]
).transact()
```

**Result** (`get_result(witness_id)`, read back after the transaction reached `ACCEPTED`):

```json
{
  "subject_id": "git:whiteknightonhorse/provek",
  "criterion": "artifact_hash",
  "evidence_url": "https://raw.githubusercontent.com/whiteknightonhorse/provek/5e28d5f933329c124c058996da28b2abd4da5d37/LICENSE",
  "expected": "c61e9a12ff00f711d1d42a15430de1f7191c369adcc20cab7d33e7c1cbcf8660",
  "result": "PASS",
  "evidence_digest": "c61e9a12ff00f711d1d42a15430de1f7191c369adcc20cab7d33e7c1cbcf8660",
  "checked_at": "2026-09-28T06:51:33Z",
  "observation": "status=200"
}
```

`witness_id`: `0645571a8dea1e2601e441eb3c451b3eb6ab60f2f1c5af68c70129c03ae13453`. Transaction status:
`ACCEPTED` (tx hash, `0x`-stripped for the secret-scan gate per GL-00 ruling-1:
`45388e3b02dba0295c5960a7aabefadf4175198a1d71b90008689772dfd68c7a`). See `deploy/deployment.json`
for the other two live records (a second PASS on `url_reachable` against `https://provek.dev/`,
and a FAIL on the same LICENSE artefact checked against a deliberately wrong digest — the FAIL path
shown on-chain, not merely asserted by a test).

## Known `genvm-lint check` warnings (named, not suppressed)

Two warnings survive `genvm-lint check contracts/provek_evidence_witness.py`, both the same code:

```
E010: gl.nondet.* call in 'ProvekEvidenceWitness.witness.<locals>.leader_fn' not reachable from equivalence principle block
E010: gl.nondet.* call in 'ProvekEvidenceWitness.witness.<locals>.validator_fn' not reachable from equivalence principle block
```

**Both are false positives, confirmed by reading `genvm_linter`'s own source
(`genvm_linter/lint/safety.py:366-372`, `genvm-linter==0.11.0`, the pinned version in
`~/orchestra/glenv`).** The E010 reachability check recognizes a fixed, literal list of dotted
call names as "equivalence principle blocks" — `gl.vm.run_nondet`, `gl.vm.run_nondet_unsafe`,
`gl.eq_principle.strict_eq`, and a few older-version aliases. It does NOT recognize
`glvm.run_nondet_unsafe(...)` — the form this contract uses, via `import genlayer.gl.vm as glvm`,
matching the GenLayer boilerplate's own `contracts/PatternTest.py` convention for accessing
`glvm.Return`/`glvm.run_nondet_unsafe` directly (see this file's own module docstring and
GL-facts.md F1). Because the linter's pattern-matcher sees the call as `glvm.run_nondet_unsafe`
rather than `gl.vm.run_nondet_unsafe`, it does not add it to the set of recognized "safe contexts
for nondet" (`safety.py`'s own docstring at that line), and so it reports the `gl.nondet.web.get(...)`
call textually inside `leader_fn`/`validator_fn` as unreachable from any such block — even though
both closures ARE, in fact, the exact `leader_fn`/`validator_fn` pair passed to
`glvm.run_nondet_unsafe(leader_fn, validator_fn)` two lines below their definitions.

This is named rather than worked around by switching the call site to the fully-dotted
`gl.vm.run_nondet_unsafe(...)` form (which WOULD silence it) because ruling-2 §2 of the design
dispute specifies the aliased form explicitly, matching `PatternTest.py`; changing the call
convention to satisfy a linter false positive was judged the wrong trade against following the
ruling. If a future `genvm-linter` release recognizes import aliases, this note becomes stale and
should be removed along with a re-run of `genvm-lint check`.

No other warnings survive. The three "Bare Python exception" warnings GL-harness-notes observed
in the boilerplate's own `football_bets.py` do not apply here: every deterministic revert path in
this contract raises `glvm.UserError(...)`, not a bare `Exception`/`ValueError`.

## Limitations (named, not hidden)

- **Studionet's own state is not proven stable across resets.** The contract address recorded
  there (`evidence/MEASURED-011-*`) is dated and marked as such; **Testnet Bradbury is the
  canonical address** for any external reference to this contract (`deploy/README.md`).
- **Integration tests are not run in CI, and not run at the door.** `tests/integration/` needs a
  funded account on a real network — a resource this repository's automated gates deliberately
  never hold (`GL-00 ruling-2 §"Сети"/"Секреты"`). They are run manually, by the dispatcher, against
  Studionet; see "How to run integration tests" above and `evidence/MEASURED-011-*` for the last
  recorded run.
- **No bridge writes this contract's on-chain results back into Provek's own `WitnessRecord`
  storage.** The field correspondence table above describes how the two schemas *could* line up;
  building the adapter that actually reads a `WitnessResult` off-chain and constructs a
  `WitnessRecord` from it is a separate, deliberately deferred task, named in `DECISIONS.md` D-63
  rather than built speculatively here.
- **A third criterion type — a command with a deterministic exit — is not implemented.** The
  operator's brief and Provek's own specification (spec 4.2-bis point 4) name it as a possible
  third machine-checkable criterion; `src/witness/witness.py`'s own module docstring already
  explains why it is not built there (arbitrary code execution triggered by a request from outside
  the host is a different order of decision than an SSRF-guarded GET), and the same reasoning holds
  here — `SUPPORTED_CRITERIA` in this contract is deliberately the same two names as Provek's own,
  not a superset.
- **Three known `genlayer-py==0.18.0` SDK limitations against Bradbury**, all worked around in the
  dispatcher's own operational script with **no contract code changed** — transaction status `14`
  (`LEADER_REVEALING`) missing from the SDK's status-name map, `gltest.utils.extract_contract_address`
  failing against a testnet receipt's `tx_data_decoded == None`, and `gen_call` on Bradbury
  returning `{"data": <hex>, ...}` where the SDK expects a bare hex string. Full detail in
  `deploy/README.md`'s "Deployment record" section.
