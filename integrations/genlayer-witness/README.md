# Provek Evidence Witness (GenLayer Intelligent Contract) — skeleton

**This is a skeleton README, written by T-GL-03-contract.** The full eleven-section operator
document (what it is, why it exists, input/output format, how consensus works, how validators
verify, why it is not Provek scoring, how to run each test tier, how to deploy, an example
request/result, the WitnessRecord field-correspondence table, and named limitations) is GL-06's
job. This file exists now only to satisfy this task's own acceptance criterion: every `genvm-lint`
warning that survives must be named here, with a reason, rather than silently suppressed.

See the contract's own module docstring (`contracts/provek_evidence_witness.py`) for the design
rationale in full; see
`~/taskloop/disputes/GL-00-genlayer-witness-design.ruling-2.md` and `...ruling-3.md` for the
governing decisions this contract implements.

## Directory layout

```
integrations/genlayer-witness/
  README.md                  — this file (skeleton; GL-06 completes it)
  pyproject.toml             — pytest rootdir + the `integration` marker
  requirements.txt           — pinned versions, for human readers (CI's own pins live in
                               requirements/ci-genlayer.{in,txt} at the repository root, GL-04)
  gltest.config.yaml         — network config for `gltest` (localnet, studionet)
  contracts/
    provek_evidence_witness.py
  tests/
    direct/                  — `pytest tests/direct -v` (no network, no real GenVM)
    integration/             — `gltest --network studionet tests/integration -v -s` (real
                               consensus; not run at the door, not run in CI — dispatcher-only)
    fixtures/
      digest_golden.json     — one digest formula, two readers (this repo's 3.10 `tests/` reads
                               `src.witness.witness._digest`, this directory's 3.12 direct tests
                               read the contract's own `_url_reachable_digest`)
  deploy/
    README.md                — Deployment record (Bradbury address, explorer, three live records,
                               three named SDK limitations); see GL-05/GL-05b
    deployment.json           — the same record's real, measured fields (GL-05b)
```

## Running the tests written so far

```
~/orchestra/glenv/bin/python3 -m pytest tests/direct -v
~/orchestra/glenv/bin/genvm-lint check contracts/provek_evidence_witness.py
```

Both commands need the isolated Python 3.12 venv at `~/orchestra/glenv` (this repository's own
Python is 3.10 — see `GL-harness-notes.md`), and `~/.cache/gltest-direct/genvm-universal-v0.2.16.tar.xz`
pre-populated in the direct-mode SDK cache (GL-harness-notes.md §7b: the auto-downloader 404s on
every fresh host against the current `genvm` release, for any project, not something specific to
this one).

`tests/integration/` needs a live network and a funded account and is not run by this task — see
`tests/integration/test_provek_evidence_witness_live.py`'s own module docstring for the exact
command, and GL-05/GL-05b for who actually runs it.

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
