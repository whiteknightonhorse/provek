# ADR-0011 — Templates are a machine-addressed artefact, gated from the instrument in both directions

**Status:** accepted, 2026-09-05. Ruled by Fable, in response to the operator's brief
`briefs/ai-agent-incubator.md` (885 lines, sha256 `faad64ade...`) and the executor's dispute
`taskloop/disputes/70-ai-agent-incubator-page.q-1.md`. Full ruling kept at
`taskloop/disputes/70-ai-agent-incubator-page.ruling-1.md`; this document is its architectural
decision, in the form the rest of the project's ADRs take, not a second telling of the whole ruling.

## Context

The brief asks for a page of "AI Agent Templates" — copy-a-template-into-your-coding-agent, with a
funnel toward this project's own verification. ADR-0009 closed with exactly this contingency:

> An actual course… gets its own ADR if it is ever wanted.

This is that clause firing. ADR-0009 separated *documents about this instrument*, written for a
human reader, from the instrument itself, by publishing them in a **separate repository** with a
vocabulary gate. A template is a different genre: it is addressed to a *machine* (the reader's own
coding agent), and it is *about a third party's business agent*, not about Provek. Specification
§10.4 names the conflict this whole family of decisions manages: "if the same party teaches people
to pass its own verification, it is grading work it set itself." ADR-0009 already drew the line
that matters here — *teaching someone to be autonomous legitimately changes the measured state;
teaching someone to appear autonomous is what the gate forbids.*

## Decision

Templates live **in this repository**, under `templates/<slug>/SKILL.md`, in the Agent Skills
shape (agentskills.io: frontmatter with `name`/`description`/`license`/`compatibility`/`metadata`,
optional `references/`, progressive disclosure). They are **not** moved to a second repository the
way the method corpus was. Instead, the separation is enforced as a **two-direction machine gate**,
vocabulary-based rather than geography-based:

1. **Direction 1 — the artefact never names the instrument.** No file under `templates/<slug>/`
   may contain (case-insensitive) `provek`, `passport`, `registry`, the stem `verif`, a level token
   `\bL[0-5]\b`, `autonomy level`, `projection`, `evidence window`, or `score`. A planted violation
   must turn the check red; the red run is kept under `evidence/`.
2. **Direction 2 — the instrument never reads the artefact.** No file under `src/` or `scripts/`
   references the `templates/` path. The scorer's inputs remain what they have always been:
   evidence read from the subject's own repository.

Both directions are registered as one law, `LAW-TEMPLATE-NAMES-NO-INSTRUMENT`, enforced by
`tests/test_templates_never_name_the_instrument.py` (§ full contract: `templates/SCHEMA.md`).

**Why not a second repository (rejected option c).** A second repository buys ADR-0009 one thing:
"the verification surface must never have hosted the teaching when verification becomes paid." That
same guarantee is bought here, without the cost of a live network dependency at build time (D-18's
own reasoning: a build that depends on a network and a token is not reproducible from a clone), by
naming the extraction condition now instead of paying for it today:

**Extraction condition.** If verification becomes paid, `templates/` is extracted into its own
repository (subtree, history kept) **before the first paid passport is issued.** This is the same
trigger ADR-0009's own closing section names for the teaching/verification conflict generally.

**Publication gate.** A template is emitted on the public surface only after a **witnessed dry
run** — run once against a fresh directory with a real coding agent, recorded at
`evidence/TEMPLATE-RUN-<slug>.json`, keyed to the sha256 of the `SKILL.md` body at run time. Three
states, never collapsed: no record (unpublished), hash mismatch (the page says the dry run predates
the current revision, rather than presenting it as fresh — CLAUDE.md invariant 1), matching record
(publishable). Registered as `LAW-TEMPLATE-WAS-RUN`, enforced by `tests/test_template_was_run.py`.

## What this surface explicitly does not become, and why

| brief's proposal | ruling | ground |
|---|---|---|
| **Agent Clinic** — score the reader's own agent on the L0–L5 ladder and coach it upward | refused, on this surface, permanently | a level outside the passport breaks invariants 2 and 6; coaching toward a verdict this same instrument later issues is exactly §10.4's conflict; no backend exists for it (concurrency 1) |
| **Teardowns** with a hand-written "Before: L1 → After: L4" | not in v1 | a hand-written level is a self-issued verdict (invariant 2); later, only if the level is computed at build time from a real, linked passport |
| **Build Logs** with dated level claims | not in v1, same reason as Teardowns | as above |
| a second **Showcase** table | not built — `/registry/` already is this | a second table with softer entry criteria is badge inflation by construction (2026-09-02 competitor capture, antipattern №1) |
| **Free / Builder Program / Incubator tiers**, announced | not announced | D-05, D-16: no reserved slot is offered before it exists |
| usage **counters** ("1,247 agents built…") | none | brief's own condition ("only if measured") cannot be met in v1; no WitnessRecord-class mechanism exists for this surface yet |

## Naming (brief §2)

Nav label **Build**, route `/build/`, descriptive noun **AI agent templates**. "Incubator" is
rejected as the page name: zero measured demand for the word (`seo/keywords.csv`, 0 of 1418 rows),
and a direct collision with the product's own description ("Provek, AI Business Incubator") and
with the reserved `/phase-2/` phase vocabulary. "Builder Program" is rejected for the same reason
one level down — real demand exists for "ai agent builder" (649–1129 impressions) but the qualified
rows are vendor-navigational (OpenAI Agent Builder, Vertex AI Agent Builder, Copilot Studio), and
"Program" asserts a cohort and admission dates that do not exist (D-05, D-16). Both rejected names
are kept in reserve as the names of paid tiers that are not shown in v1.

## v1 templates (admitted by rule, not by list)

`customer-support-agent`, `lead-generation-agent`, `ecommerce-operations-agent`,
`market-research-agent`, `content-production-agent`, `finance-operations-agent` — each admitted
only if it (i) runs one business operation end-to-end, (ii) names its few human-in-the-loop points,
(iii) builds on a proven public source or an architecture this fleet has run, (iv) passes its
witnessed dry run. `templates/README.md` records the rule and the backlog (not shown publicly).

**2026-09-05 addendum (D-58).** "v1 admits six" above named the launch's scope, not a ceiling: the
admission mechanism in this section is the only gate, and a category is not admitted because it is
on a list, nor refused because it is off one. A seventh template, `youtube-channel-operations-agent`,
is admitted under the same four-part rule: (i) the operation is channel operations — taking a
finished video and its metadata through to an unlisted upload and a human's publish decision, which
does not overlap `content-production-agent`'s draft-and-fact-check operation; (ii) its
human-in-the-loop points are named (OAuth setup in a browser, first consent, the unlisted-to-public
decision, anything involving money); (iii) its source is the second branch of ground (iii) — three
of the operator's own live channel-operations codebases (game, cryptocardhub, realestate), read by
the dispatcher and supplied as `briefs/youtube-agent-facts.md` since this tenant has no access to
those projects' hosts, rather than an identified public repository; (iv) it passed its witnessed
dry run before publication. Video production and short-versus-long format rules are not part of
this template, for lack of a measured source at admission time. Full reasoning:
`taskloop/disputes/77-seventh-template-youtube-channel-agent.ruling-1.md`.

## Sources read for this decision, and what was not readable

Fetched and read: `anthropics/commerce-agents` (README, `plugins/commerce-builder`; Apache-2.0) —
its merchant agent is the direct source for `ecommerce-operations-agent`, with attribution carried
in that template's `metadata.derived_from`. The Agent Skills specification at agentskills.io, for
the directory/frontmatter/progressive-disclosure shape adopted above. `karpathy/llm-council` could
not be fetched this session (refused four times); the multi-model cross-examination pattern it is
recalled to use informs `market-research-agent`'s design, and the template's author re-reads the
actual repository before adapting it and cites it in `metadata.derived_from`.

**Not read, and not papered over.** Three files the brief names live only on the operator's laptop
and are unreachable from this host — confirmed by `find /` for all three exact names and for
`*Tempo*`, nothing found:

* `/Volumes/Disk D/projects/Tempo/docs/` — a file on AI agent fleets (original title in Russian)
* `/Volumes/Disk D/projects/Tempo/docs/` — a note on applying the Matt Pocock Skills architecture (original title in Russian)
* `/Volumes/Disk D/projects/Tempo/docs/UNIVERSALDESIGNPROMPT.md` — a design brief against AI-slop (original title partly in Russian)

Their exact original filenames are quoted in full in `taskloop/disputes/70-ai-agent-incubator-page.q-1.md`,
which sits outside this repository (the taskloop working directory, not the GitHub surface) and so
is not bound by this project's English-only rule the way this ADR is.

If the operator places readable copies under `~/briefs/`, a follow-up task re-reads them and amends
this decision by a dated addendum; until then, `DESIGN.md` and `SPEC.md` §10 are the binding
anti-slop reference for this surface, and this gap is a named `PARTIAL`, not a silent one, in the
final walk this task's brief requires (§9 of the ruling on disk).

## Explicitly not decided

Whether `templates/` should be marked in `robots.txt` / Content-Signal as input for AI systems —
an operator decision, not made here. A `provek.json` field letting a subject declare "started from
template X" so it can surface in `/registry/` — a schema decision for the operator, not this ADR.
A support channel beyond one per-template GitHub issue link and the existing `/apply/` form —
nothing beyond that exists to announce.

## Consequence

`SPEC.md` §3.7 specifies the surface this gate makes possible; `DECISIONS.md` D-57 records the
decision for this interface; `enforced_by.yaml` carries `LAW-TEMPLATE-NAMES-NO-INSTRUMENT` and
`LAW-TEMPLATE-WAS-RUN`. This phase (Phase 0) ships the contract, the licence and the two gates, with
`tests/fixtures/` proving each can fail, against **zero real templates** — the first lands in the
next phase, following D-18's precedent that a specification may precede its instances.
