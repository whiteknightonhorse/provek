# Template schema

Normative. `tests/test_templates_never_name_the_instrument.py` and `tests/test_template_was_run.py`
enforce the parts of this file that are machine-checkable; the rest binds a human author. Shape
follows the Agent Skills specification (agentskills.io): a directory named for its `name`, a
`SKILL.md` with YAML frontmatter, optional `references/` loaded on demand.

## Frontmatter

```yaml
---
name: customer-support-agent            # = directory name, <=64 chars, kebab-case
description: <what it builds, for whom, when to use - <=1024 chars, keyword-bearing>
license: Apache-2.0
compatibility: Any coding agent that can create files and run shell commands (Claude Code, Codex, Cursor)
metadata:
  template_schema: "1"
  business_operation: "<one line: the single business operation this agent runs>"
  for: "<one line: who this is for>"
  human_remains_for: "<one line: what stays with a human - shown on the template's card>"
  requires: "<one line: accounts, APIs, credentials needed - shown on the template's card>"
  derived_from: "<source URL and its licence, if adapted from a public project - optional>"
  keys: "<a row from seo/keywords.csv, with its demand_state - optional, never a bare number>"
---
```

All frontmatter values are strings. `name` must equal the directory name. `metadata.derived_from`
is required when a template is adapted from an identified external project (attribution is not
optional for those) and omitted otherwise — never invented.

## Body — fixed section order, `##` headings

```
## What to build
## Architecture
## Workflow
## Tools and APIs
## Credentials
## Memory
## Decision points
## Where a human stays in the loop
## Security
## Tests
## Deployment
## Commercial use
## Attribution
```

`## Credentials` states that secrets are never written into code, are asked of the user, and are
kept in `.env`. `## Tests` states the tests the coding agent's build must pass before it may report
the work done — CLAUDE.md invariant 5 applied to a third party's build, not just this one's.
`## Attribution` is present (even if only "no external source" for an original template) and
carries the licence and URL of any adapted source.

Budget: the body stays under roughly 5000 tokens and under 500 lines, per the Agent Skills
specification's progressive-disclosure design; material beyond that moves to `references/`, one
directory level deep, loaded by the coding agent only when the body points to it.

## The two directions of `LAW-TEMPLATE-NAMES-NO-INSTRUMENT`

**Direction 1 — the artefact never names the instrument.** Neither the frontmatter nor the body of
a `SKILL.md`, nor any file under its `references/`, may contain (case-insensitive):

* `provek`
* `passport`
* `registry`
* the stem `verif` (`verify`, `verified`, `verification`, …)
* a level token matching `\bL[0-5]\b`
* `autonomy level`
* `projection`
* `evidence window`
* `score`

A template describes a third party's business agent; none of the above is a fact about that agent.
Where a template needs to say "a human approves before this sends", it says exactly that, in plain
language, never in the vocabulary of this project's own ladder.

**Direction 2 — the instrument never reads the artefact.** No file under `src/` or `scripts/` may
reference the `templates/` path. The scorer's inputs stay what they always were: evidence read from
the subject's own repository, never from this directory.

A planted violation of each direction is kept in `tests/fixtures/` and must turn the relevant test
red — CLAUDE.md invariant 5: a test that cannot fail proves nothing.

## The witnessed dry run — `LAW-TEMPLATE-WAS-RUN`

A template's page is emitted only if `evidence/TEMPLATE-RUN-<slug>.json` exists and its
`body_sha256` matches the current `SKILL.md` body. Record shape:

```json
{
  "slug": "customer-support-agent",
  "body_sha256": "<sha256 of the SKILL.md body at run time>",
  "run_at": "2026-09-05T00:00:00Z",
  "tool": "claude-code",
  "model": "<model id>",
  "outcome": "scaffold produced; N of N template tests passed",
  "transcript_sha256": "<sha256 of the recorded transcript>",
  "notes": "<free text>"
}
```

Three states, never collapsed into one another: **no record** (never published), **hash mismatch**
(the current body is a later revision than the one that was run — the page says so rather than
showing a stale dry run as fresh, per CLAUDE.md invariant 1), and **matching record** (publishable).
A failed dry run is a red result and is not published; it is not retried into silence.
