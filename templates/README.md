# Templates

An **AI agent template** is a specification, addressed to a coding agent (Claude Code, Codex,
Cursor or similar), that makes it build a business agent running one real business operation —
support, lead generation, back-office, research, content, finance. It is not documentation about
this instrument, and it is not a course. Ruled by Fable, 2026-09-05, `docs/adr/ADR-0011-templates-are-a-machine-addressed-artefact-gated-from-the-instrument.md`;
this file is the working README for that ruling, not a second source of truth for it.

**No template exists in this directory yet.** This phase (Phase 0) ships the contract, the licence and
the gates a template must pass before it may be published; the first template lands in the next
phase. A specification is allowed to precede its instances (D-18 already set this precedent for
the method notes corpus); a page claiming a template exists when none has landed would not be.

## Admission — a template is added only if all four hold

1. It produces an agent that runs **one business operation** end-to-end — never "a company"; this
   project measures per operation.
2. Its human-in-the-loop points are nameable and few, and are stated on the template itself.
3. It builds on a proven public source with a compatible licence, or on an architecture this fleet
   has actually run — never invented from scratch to fill a category.
4. **It has passed a witnessed dry run** — see below. A template with no run record cannot be
   published; the build refuses it.

v1 admits six templates in this order: `customer-support-agent`, `lead-generation-agent`,
`ecommerce-operations-agent`, `market-research-agent`, `content-production-agent`,
`finance-operations-agent`. Each is built in a later phase, with its own dry run. A backlog
(recruiting, SEO, legal research, business analyst, executive assistant, shopping assistant) is
not shown anywhere on the public surface — a backlog is not a promise.

## The gate: a template never names this instrument, and this instrument never reads a template

ADR-0011's central decision. A template is a specification about a *third party's* business agent;
it must never mention Provek, its passport, its registry, its verification vocabulary or its
autonomy ladder — teaching someone to *appear* autonomous to an examiner that then grades its own
teaching is exactly the conflict ADR-0009 already refused for the method corpus, applied here in
the other direction. Machine-checked, in both directions:

* **Direction 1.** No file under `templates/<slug>/SKILL.md` or `templates/<slug>/references/`
  contains (case-insensitive) `provek`, `passport`, `registry`, the stem `verif`, `L0`-`L5` as a
  level token, `autonomy level`, `projection`, `evidence window`, or `score`. Enforced by
  `tests/test_templates_never_name_the_instrument.py`, law `LAW-TEMPLATE-NAMES-NO-INSTRUMENT`.
* **Direction 2.** No file under `src/` or `scripts/` references the `templates/` path. Same law,
  second assertion, same test file.

This README and `SCHEMA.md` are documents *about* the template system, not templates themselves,
and are outside the scanned set — they may name the instrument because they are the instrument's
own contract, the same way `LICENSE` at the repository root names `src/` without being source code.

## Publication requires a witnessed dry run

Before a template's page is emitted, it is run once against a fresh temporary directory with a
real coding agent, and the outcome is recorded at `evidence/TEMPLATE-RUN-<slug>.json`, keyed to the
sha256 of the `SKILL.md` body at run time. A template with no record, or whose current body no
longer matches the recorded hash, is not published — enforced by
`tests/test_template_was_run.py`, law `LAW-TEMPLATE-WAS-RUN`. See `SCHEMA.md` for the record shape.

## Extraction, if verification becomes paid

`templates/` stays in this repository while verification is free. ADR-0011 records the condition
under which it moves: if verification becomes paid, `templates/` is extracted into its own
repository (subtree, history kept) **before** the first paid passport is issued — the same
boundary ADR-0009 drew for the method corpus, arriving here on the mirror trigger.

## Licence

`templates/LICENSE` — Apache License 2.0, covering everything under this directory. Compatible
with `anthropics/commerce-agents` (Apache-2.0), which one v1 template adapts directly with
attribution carried in its `metadata.derived_from` field; a source under MIT folds in without
conflict. This is a third, independent licensing surface from the repository root's split between
CC BY 4.0 (the profile prose) and Apache-2.0 (`src/`, `tests/`, `web/`) — `templates/` is its own
Apache-2.0 grant because a template is code-shaped (an instruction set for a coding agent), not
methodology prose, and because it may be extracted into a standalone repository later and needs to
carry its own terms when it travels.

## One template, one directory

```
templates/
  LICENSE                      Apache-2.0, full text
  README.md                    this file
  SCHEMA.md                    the frontmatter and body contract, normative
  <slug>/
    SKILL.md                   the artefact: frontmatter + instructions to a coding agent
    references/                optional, one level deep, loaded by the agent on demand
```

See `SCHEMA.md` for the exact contract a `SKILL.md` must satisfy.
