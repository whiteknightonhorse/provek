# A Provek Auditor agent on the Amadeus Protocol SDK

This is the T-2.16 demo: an auditor agent built on [`@amadeus-protocol/sdk`][sdk] that packages
Provek's **own** audit into a validation record serialised with the SDK's codec, anchored at a
chain height read through the SDK.

Provek is a validator, not a registry. The methodology is ours; the transport is somebody else's.
The same validation record is already published over a file transport — and an ERC-8004 adapter
exists but **refuses** to publish, by design, until there is a deployed validator contract and gas
(`src/transport/erc8004.py` raises rather than silently doing nothing). The point of this demo is
that the record is **transportable on Amadeus rails too**, without the methodology learning
anything about them.

Said plainly, so the demo is not read as more than it is: **nothing is written to the chain and no
scoring runs here.** The agent reads the already-published passport, hashes it, anchors it at a
height it read through the SDK, and encodes the result with the SDK's codec. Claiming it "runs an
audit on-chain" would be the kind of overclaim this product exists to detect.

## Run it

```sh
# On a fresh clone, writing your own copy of the artefact rather than replacing the shipped one:
python3 scripts/amadeus_demo.py --install --out evidence/MY-AMADEUS-RUN

# Or replace the committed artefact deliberately:
python3 scripts/amadeus_demo.py --overwrite
```

`--install` is only needed the first time. The runner **refuses to overwrite an artefact that is
already on disk** unless you say so — the shipped `evidence/AMADEUS-DEMO-001.*` is a record of a
particular run, and a record that is silently replaced on every invocation has no provenance.

Three anonymous GETs against the public mainnet RPC — no credential, no key, nothing written to
the chain — so anyone can repeat it, including Amadeus. The run writes a `.json` (raw) and a `.txt`
(readable) at the chosen stem, and exits non-zero unless the run actually demonstrated something.

Two halves, deliberately: `auditor.mjs` uses the SDK and **gathers**; `src/amadeus/demo_audit.py`
**decides**. PASS/FAIL is taken by deterministic code from a measured quantity, and the law lives
where the test suite can reach it — `tests/test_amadeus_demo.py` covers it with injected artefacts,
opens no socket, and never skips.

## What the demo found, and it is not about us

**No schema is applied to a success body.** `ChainAPI.getTip()` is
`return this.client.get('/api/chain/tip')`; the `validate()` calls in that file guard *input*
arguments. Being precise about what the client *does* check, because it is not nothing:
`handleResponse()` inspects a 2xx body for an application-level `error` envelope — throwing 404 on
`error:"not_found"`, 400 on any other non-`ok` value, and stripping `error:"ok"` — and throws if
the body will not parse as JSON. A document that carries no `error` key at all falls through to
`return data` and reaches the caller as the chain tip, where `entry.header.height` reads
`undefined` — which one arithmetic step later is a zero.

This is not hypothetical. On **2026-08-20 at ~23:07Z** three consecutive requests to
`mainnet-rpc.ama.one` for `/api/chain/tip`, `/api/chain/stats` and `/api/chain/kpi` each returned
HTTP 200 carrying a CKAN `package_search` response from `ckan.opendata.swiss` — the Swiss open
government data portal. A later re-probe of 24 samples found no recurrence, so the window was
transient.

That reading, and an explicit list of what it does **not** establish, is
[`evidence/AMADEUS-RPC-ANOMALY-001.txt`](../../evidence/AMADEUS-RPC-ANOMALY-001.txt). The short
version, because the finding must not be read as stronger than its artefact:

- **It was not an instrumented capture.** Only the leading ~400 characters of each body were kept,
  as terminal output. Response headers, including content-type, were never read — an earlier draft
  of this file asserted "same content-type", and that claim has been removed rather than softened.
- **Where the misroute happened was not established.** Both addresses were Cloudflare. Edge, CDN,
  or somewhere on path — this demo does not know, and does not claim Amadeus's infrastructure was
  at fault.
- **The control below therefore serves a reduced reconstruction**, not the captured bytes. What it
  reproduces is the SDK's behaviour, which does not depend on which foreign document arrives — and
  that behaviour, not the incident, is what the finding rests on.

So the agent runs an **instrument control**: a local socket answers 200 with a body that is
plainly not chain state, the SDK is pointed at it, and whether the SDK notices is recorded.
Current result — `accepts_unvalidated_response`. The control is able to fail in the direction
that matters: if a future SDK validates its responses it flips to `validates_response` and the
finding above is retired, in code, without anybody editing this paragraph.

The suggestion this demo carries to Amadeus is small and cheap: the SDK already depends on
`effect`, whose `Schema` is used on inputs. Applying it to responses would turn a misrouted 200
into a thrown error instead of a silent `undefined`.

## What the demo does not do

**It does not write to the chain**, and that is a recorded state, not a gap — the artefact carries
`onchain_write.state = check_did_not_run` with two named blockers: this agent is never given a
signing key (by operator decision, only a public address would ever reach a file), and a write
costs AMA the project does not hold. A blocked step that leaves no sentinel is how "cannot"
becomes "forgot". Lifting either blocker is a decision for a person, which is why this demo will
not quietly start writing when one of them lifts.

**It does not recompute the score.** The projection is passed through from the passport, because a
second implementation of the score in JavaScript would be a second methodology.

**It is not a verdict about Amadeus.** The demo's verdict says whether *the demo* showed what it
claims to show, and each state has its own exit code so a script cannot confuse them:

| verdict | exit | meaning |
|---|---|---|
| `demonstrated` | 0 | the SDK was seen talking to the live chain, the control ran, the record was built |
| `not_demonstrated` | 1 | the run was honest and showed nothing — an unreachable RPC looks like this |
| `defect` | 3 | our artefact is malformed: our bug, not a finding about anyone else |
| — | 2 | the demo never started (node or the SDK missing, or an artefact already on disk) |

"Their RPC was down" and "we shipped a broken demo" do not share a code. A run whose instrument
control could not be set up is `not_demonstrated`, never `demonstrated` — the finding above is the
control's, and a run that failed to establish it must not exit 0 still carrying the claim.

## Naming

"Amadeus" here is **Amadeus Protocol** (`ama.one`), the settlement layer for AI agents — not
Amadeus the travel-technology company (`amadeus.com`, `amadeus4dev` on GitHub), whose unrelated
SDKs dominate a search for the name.

## Provenance

`@amadeus-protocol/sdk@1.2.0`, MIT, pinned in `package.json` and locked in `package-lock.json`.
Tarball integrity as published:
`sha512-4SWs2PsZGXRiX7PlaNpIw1cowRi0h6JwlCvkg1EoFSWlgw6FgwqiR7Xz4vu5HNo3uyyVRDGqupWGegTYdwlGvw==`
— verified against the downloaded tarball before any of this was written.

[sdk]: https://www.npmjs.com/package/@amadeus-protocol/sdk
