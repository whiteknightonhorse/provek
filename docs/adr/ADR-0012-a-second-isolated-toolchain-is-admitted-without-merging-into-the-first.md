# ADR-0012 — A second, isolated toolchain is admitted into this repository's gates, never merged into the first

**Status:** accepted, 2026-09-28. Ruled by Fable, in response to the operator's brief
`taskloop/briefs/GL-00-operator-task.txt` and the design disputes
`taskloop/disputes/GL-00-genlayer-witness-design.ruling-2.md` / `...ruling-3.md`. Full ruling kept
there; this document is the architectural decision in the form the rest of this project's ADRs
take, not a second telling of the whole ruling. Extends ADR-0002 (transport independence is
machine-checked) to a second boundary: a whole external dependency graph, not one import.

## Context

`integrations/genlayer-witness/` (T-GL-02/03) is a GenLayer Intelligent Contract — a genuinely
separate, reusable verification primitive this repository hosts but does not depend on. Its own
SDK (`genlayer-py`, `genlayer-test`, `genvm-linter`) requires Python >= 3.12; this repository's own
interpreter, every gate, and every requirement set predating this one are Python 3.10. Two
questions follow from that mismatch, and this ADR is the answer to both: how does a second
interpreter enter a gate system built around one, and what stops the contract it tests from
becoming a second, unaudited entry point into `main`.

## Decision

**One interpreter per concern, not one interpreter for the repository.** `~/orchestra/glenv`
(T-GL-02) is a Python 3.12 venv built and used OUTSIDE this repository's own tree, exactly the way
`~/.provek_witness_requests` already keeps D-52's request log outside it. `.github/workflows/gates.yml`
gains one job, `genlayer`, running on `actions/setup-python@...python-version: "3.12"` — a second,
parallel toolchain, not a repository-wide version bump. No other job's Python version changes.

**The same pinned-and-hashed discipline D-30 established, compiled by a different tool for the
reason D-30's own argument implies.** `pip-compile`, which produced `ci-tests.txt`/`ci-lint.txt`/
`ci-shipped.txt` under this repository's 3.10, cannot resolve `requirements/ci-genlayer.in` at all —
the packages in it declare `requires_python: ">=3.12"` and refuse the environment outright.
`requirements/ci-genlayer.txt` is compiled by `uv pip compile --generate-hashes` under Python 3.12
instead (see that file's own `.in` sibling for the exact command and for the resolver override its
compilation needs, GL-harness-notes.md §7a). D-30's own guarantee — every install line names a
committed, hash-checked set, checked mechanically by `scripts/verify_pip_pins.py` regardless of
which tool produced the file — holds unchanged; only the tool that produced this one file differs,
named rather than left to look like an inconsistency.

**The anticipated cross-file version conflict was checked and did not occur.** Ruling-2 named a
real risk: `verify_pip_pins.py` requires one version of `pytest` across every pinned set, and
`genlayer-test` might have forced a different one. It does not: `genlayer-test==0.29.2` declares a
bare, unconstrained `pytest` dependency — the same way this repository's own `ci-tests.in` names
`pytest` with no version pin — so both compilations independently resolved the same current release
(`pytest==9.1.1`, identical hash, a universal wheel). `verify_pip_pins.py` was run against the real
tree with `ci-genlayer.txt` in place and reports clean with no changes to its own code: there was
nothing to except. If a future bump ever does force a real divergence, ruling-2's fallback —an
interpreter-keyed exception in `verify_pip_pins.py`, its own red run, a line here— is the ordered
answer; it was not built speculatively for a conflict that was checked and found absent.

**Isolation is the same machine guarantee ADR-0002 already holds, applied to a new boundary.**
`tests/test_genlayer_witness_is_isolated.py` is an AST import scan — not a grep, for the reason
ADR-0002's own "Why AST and not grep" section gives — over every module under `src/` and
`scripts/`, asserting none imports `integrations`. `ratchet_scope.SCAN` now walks `integrations/`
too, so every file the contract adds is bound to an ABI requirement the same as everything else
(`requirements/ABI_MAP.yaml`) — an unbound file there fails the build exactly as one would under
`src/`. Neither direction is symmetric with ADR-0011's two-way vocabulary gate: `integrations/` is
not forbidden from mentioning Provek (its own module docstring does, honestly, since it exists
*because of* `src/witness/witness.py`'s schema) — only `src/`/`scripts/` reaching INTO it is
forbidden, because that is the direction that would let a change to an experimental, isolated
contract silently move Provek's own scoring.

**A linter with no baseline is not made to lie about a named false positive.** `genvm-lint check`
has no allowlist mechanism; two of its warnings on this contract are confirmed false positives
(this directory's own README.md) that this project decided to keep rather than route around by
changing a call convention the design ruling specifies. `scripts/check_genvm_lint.py` is the one
place that "these two, exactly, and nothing else" interpretation lives, run identically by
`gates.yml`'s `genlayer` job and `scripts/push.sh`'s door step 9 (L-2) — the same shape this
project already uses for `mypy`'s advisory exit-code interpretation, applied to a gate that DOES
block rather than one that is advisory.

## Instrument control

`tests/test_genlayer_witness_is_isolated.py` and `tests/test_genlayer_witness_digest_matches_provek.py`
each carry their own "this check is able to fail" test, and `evidence/RED-055-*`/`RED-056-*` are
the kept red runs: a planted import from `src/` into `integrations/`, and a planted change to
`src.witness.witness._digest`'s own field separator, each shown to turn the relevant test red and
green again on revert.
