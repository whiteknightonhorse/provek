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
| `"verifier_affiliation": "same_owner"` | Every record discloses whether the verifier and the subject share an owner — re-derived at each re-measure, not a label set once and trusted forever. |

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
