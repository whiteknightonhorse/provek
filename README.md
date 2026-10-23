# Provek

[![gates](https://github.com/whiteknightonhorse/provek/actions/workflows/gates.yml/badge.svg)](https://github.com/whiteknightonhorse/provek/actions/workflows/gates.yml)
[![codeql](https://github.com/whiteknightonhorse/provek/actions/workflows/codeql.yml/badge.svg)](https://github.com/whiteknightonhorse/provek/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/whiteknightonhorse/provek/badge)](https://scorecard.dev/viewer/?uri=github.com/whiteknightonhorse/provek)

Each badge is a live run, not a picture — [what they assert](#what-the-badges-assert) is below.

**What it is.** A verification layer for businesses operated by AI agents. It measures, per
business operation, how much of a company runs without a human — and publishes the evidence
behind every number, including what could not be measured.

**Why.** Anyone can write "AI-powered" on a landing page; nobody can tell that apart from a
business machines actually run. Provek is an [ERC-8004](https://eips.ethereum.org/EIPS/eip-8004)
validator: the standard supplies identity and transport, the methodology is ours and is public, so
any third party can recompute a verdict from the same inputs — every read is anonymous and
credential-free.

**What it does.**

- Issues a machine-readable **passport** per subject: an `L0`–`L5` level per operation (never one
  number per company), evidence classed by forgery cost, and a self-declared accountability block
  that never enters the score.
- **Absence is a state, not a zero**: an unmeasured value carries its own reason
  (`check_did_not_run` is not `nothing_qualified` is not `unreadable`), never collapsed to zero.
- **Order channel.** A verified subject can declare where customers order from it. We probe that
  address ourselves before showing anything. The "Order" link appears only when the passport is
  `verified` **and** the declared address is `https` **and** our last anonymous check reached it —
  any one of those failing removes the link and shows the reason instead. How to get one:
  [provek.dev/method/#the-order-link](https://provek.dev/method/#the-order-link).
- Publishes a [registry](https://provek.dev/registry/) of verdicts; a verdict expires and lapses to
  `stale` on its own. Corrections are published in full, not quietly fixed — see the
  [corrections log](https://provek.dev/registry/corrections/).
- Takes [applications](https://provek.dev/apply/) — free, public repositories only, read-only
  unless a signed mandate says otherwise.

A later phase (a verified agent commissioning and witnessing paid work) is specified and not
built; [why](https://provek.dev/phase-2/) explains the boundary.

## What a verdict looks like

Below is `passport.verified.operations`, taken from
[`/data/passports/git_whiteknightonhorse_APIbase.json`](https://provek.dev/data/passports/git_whiteknightonhorse_APIbase.json) —
the complete array, extracted from that subtree and re-serialised with `json.dumps(..., indent=2)`.
It is one subtree of a passport, not a whole one: the rest carries `self_reported`,
`accountability` and provenance at `passport.*`, and coverage at `passport.verified.coverage`.
`tests/test_readme_fragment_is_verbatim.py` fails the build if this stops being an emitted
passport's operations array, entire and in order.

```json
[
  {
    "operation": "development_initiation",
    "level": "L2",
    "measured": true,
    "confidence": "inferred",
    "limiters_applied": [
      "O1:mixed_classes->inferred"
    ]
  },
  {
    "operation": "deployment",
    "level": "check_did_not_run",
    "measured": false,
    "confidence": null,
    "limiters_applied": []
  },
  {
    "operation": "treasury_control",
    "level": "check_did_not_run",
    "measured": false,
    "confidence": null,
    "limiters_applied": []
  }
]
```

Three things here are the whole product — two quoted above, and the third,
`"verifier_affiliation": "same_owner"`, one level up at `passport.verifier_affiliation`:

| | |
|---|---|
| `"level": "check_did_not_run"` | **Absence is a state, never a zero.** A verdict always says which reason applies; a zero would mean "measured, and fully non-autonomous", a different claim about the world. |
| `"confidence": "inferred"` | The published number is never stronger than the measurement behind it. |
| `"verifier_affiliation": "same_owner"` | Every record discloses whether the verifier and the subject share an owner — re-derived at each re-measure, not a label set once and trusted forever. The verifier's own GitHub owners are listed in `data/operator_owners.json`. |

## How it's built

Data flows left to right:

```
collector  ->  scorer  ->  passport  ->  registry  ->  web
src/collector  src/verify  src/passport  src/registry  web/ (Preact, prerendered)
anonymous      determin-   verified /    status rows,   static pages + a few
public reads,  istic code, self-reported valid_until    Cloudflare Functions
secrets        no LLM in   kept as                      (intake, badge, brief)
redacted       any verdict separate branches
```

`scripts/cohort.py` is the production emitter; `scripts/push.sh` is the only door outward and runs
every gate (secrets, scope, laws, language, lint, build, tests) before any push.

## Run it

The pipeline reads public sources with no credential at all, so any reader can recompute a verdict
— not only whoever holds a token.

```bash
git clone https://github.com/whiteknightonhorse/provek && cd provek
(cd web && npm ci && npm run build)                  # part of the suite judges the emitted site, not only the code
python3 -m pip install --upgrade pip                 # a stock pip mis-resolves pytest-cov's own
                                                       # coverage[toml] pin against our hash-pinned set
python3 -m pip install -r requirements/ci-tests.txt  # pinned test deps (PyYAML etc.), same set CI uses
python3 -m pytest -q                                 # the suite prints its own count
python3 scripts/cohort.py                            # re-emits public/registry + public/passports
```

## GenLayer Evidence Witness — live app

**What it does.** A web page, [https://provek.dev/witness/](https://provek.dev/witness/), for the
GenLayer Intelligent Contract described in this repository's witness integration
(`integrations/genlayer-witness/`). A visitor can look up the records the contract holds for a
subject, request a new check, and watch that request go through GenLayer consensus until it is
`FINALIZED` and a `PASS` or `FAIL` record exists. Two criteria exist: `url_reachable` (does the URL
answer) and `artifact_hash` (do the exact bytes at the URL hash to a declared sha256). It is not
Provek's own WitnessRecord pages under `/w/`; the nav and every heading say "GenLayer Evidence
Witness" so the two are never confused.

| | |
|---|---|
| Page | https://provek.dev/witness/ |
| Contract | `0x499eD0E23CbCdC8Fc7735709dca32bCb01638fd6` |
| Explorer | https://explorer-bradbury.genlayer.com/address/0x499eD0E23CbCdC8Fc7735709dca32bCb01638fd6 |
| Network | GenLayer testnet Bradbury (chain 4221), RPC `https://rpc-bradbury.genlayer.com` |
| Client library | `genlayer-js` 1.1.8, an exact pin in `web/package.json` and `web/package-lock.json` |

**Design: reads go straight to the chain, writes go through an operator relay.**

- *Reads* (look-up, supported criteria, transaction tracking) run in the visitor's browser against
  the Bradbury RPC, which allows browser origins, so no Provek server sits in between and nothing on
  the page is a stored copy: every record shown is an RPC answer received in that session.
- *Writes* need a relay. The contract's `witness(...)` accepts only the operator as caller
  (`only the operator may request a witness check`), so a visitor's wallet cannot submit. The page's
  "Request a check" form therefore posts to `/api/witness-submit` (a Cloudflare Pages Function,
  `web/functions/api/witness-submit.js`), which validates the request exactly as the contract does
  (a bad request is a `400` naming the field, never a wasted transaction), applies rate limits,
  signs with the operator key held as the Pages secret `GL_OPERATOR_KEY`, and answers `202` with
  `{tx_hash, explorer_url, track_url}`. The page then opens `/witness/?tx=<hash>` and follows the
  lifecycle by reading the chain. The relay only signs and sends; the verdict is produced by GenLayer
  validators, each fetching the evidence URL on its own, and is read back from the chain.
- *Limits*: 3 requests per client per hour and 50 per UTC day for the whole service (`429` with
  `Retry-After`). Counters live in the KV binding `WITNESS_RL`; they hold counts only, never a request
  body, and the client key is a keyed hash of the address under a per-day message, never the address.
  KV has no atomic increment, so the daily cap is exact to within a few simultaneous requests.
- *Failure modes*: no secret (or a malformed one) means `GET /api/witness-submit` reports
  `{"enabled": false, ...}`, `POST` answers `503`, and the page shows "submissions temporarily
  disabled" while the read path keeps working. An upstream failure is a `502` carrying the upstream
  message with any key material removed. The key is never logged and never present in a response.

**How a reviewer reproduces the whole workflow** (no wallet needed):

1. Open https://provek.dev/witness/. The supported criteria are read live from the contract.
2. Under "Look up records for a subject" the subject `git:whiteknightonhorse/provek` is pre-filled;
   the records it lists were written by earlier checks.
3. Under "Request a check" choose `url_reachable`, enter `https://provek.dev/` and submit. The page
   moves to `/witness/?tx=<hash>`.
4. Watch the observed lifecycle (for example `PENDING`, `PROPOSING`, `COMMITTING`, `REVEALING`,
   `ACCEPTED`) until `FINALIZED`. A just-submitted hash may show "not indexed yet" for up to a minute.
5. The matching record appears with `PASS`, its observation, evidence digest and a link to the
   transaction in the explorer.
6. For a `FAIL`: request `artifact_hash` for `https://provek.dev/` with an expected digest of 64
   zeros. The validators fetch the bytes, compute the real sha256, find it differs from the
   declaration, and the record reads `FAIL` with the digest they computed.
7. `UNDETERMINED` is a possible honest outcome (validators could not agree, typically because the
   URL was unavailable to them); the page says so and claims no record.

**Tests** (from the Provek repository root; no network, no real key):

```bash
(cd web && npm ci && npm run build)
python3 -m pytest tests/test_witness_relay.py tests/test_witness_page.py -q
./scripts/push.sh --gates-only
```

`tests/test_witness_relay.py` runs the relay under Node with a mocked `genlayer-js` client and a
fake key. It compares the relay's URL rules, case by case, with the contract's own `_validate_url`,
and asserts that the key appears in no response, header, log line or stored value.

**Deployment notes.**

- Create a KV namespace and put its id in the `WITNESS_RL` entry of `web/wrangler.toml` (the
  committed id is a placeholder).
- Set the secret `GL_OPERATOR_KEY` (hex private key of the contract's operator) on the Pages project
  from standard input, never on a command line, and never commit it.
- After deploying, `GET https://provek.dev/api/witness-submit` must report `enabled: true` and an
  `operator` address equal to the contract's `get_operator()`.
- The Workers runtime is not exercised by the tests; the first live submission after a deploy is the
  runtime check.

## Where the rest is

- [`SPEC.md`](SPEC.md) — what each screen and rule must be
- [`DECISIONS.md`](DECISIONS.md) and [`docs/adr/`](docs/adr/) — every ratified decision, mistakes kept
- [`enforced_by.yaml`](enforced_by.yaml) — each load-bearing rule, with the gate and test that arm it
- [`evidence/`](evidence/) — kept runs, **including failing ones** (`RED-001`, `RED-002`,
  `TAINTED-SUDO-CORPUS`) — deleting the evidence of a violation would be a second one
- [`docs/WHY_GET_VERIFIED.md`](docs/WHY_GET_VERIFIED.md) — what verification offers a subject

## What the badges assert

| badge | who runs it | what green means |
|---|---|---|
| `gates` | us, on GitHub Actions | the ratchets, the full test suite at ≥70% coverage, lint, and the secret scan all passed on this commit |
| `codeql` | GitHub's CodeQL engine | the analysis **completed** on both Python and TypeScript — not that it found nothing |
| OpenSSF Scorecard | the OpenSSF, from their own copy | supply-chain posture, scored and published by them, not by us |

`gates` is us grading our own homework; the other two are here because their queries and rubric are
not ours.

## Licence

Methodology prose (the ladder, the evidence taxonomy, `SPEC.md`, `DECISIONS.md`, `docs/`, this
file): **[CC BY 4.0](LICENSE-CC-BY-4.0)**. Code, schemas, tests (`src/`, `tests/`, `scripts/`,
`web/`): **[Apache-2.0](LICENSE-APACHE-2.0)**. Not licensed, deliberately: the accumulated evidence
corpus and the issuer's reputation — they do not travel with the text. See [`LICENSE`](LICENSE).
