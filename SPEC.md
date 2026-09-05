# SPEC — Provek web surface

**Written in Phase 1 of the design methodology.** Product facts are taken from the project
specification (`SPEC_AI_Business_Incubator_v1.md` v1.3), not invented here. Where this document
adds something the specification does not contain, it is marked **NEW**.

---

## 1. What this is

A verification and reputation layer for businesses operated by AI agents. The single sentence the
product must earn:

> An outside party can determine, **from evidence rather than claims**, how much of a given
> business is actually run by machines.

The web surface exists to make that sentence usable by humans. Today the registry is a JSON file:
a machine can read it, a founder cannot.

## 2. Two audiences, not one

| audience | what they want | where they land |
|---|---|---|
| **Subject** — a team running an agent business | to be verified, and to have something to show their own customers | landing → apply |
| **Consumer of evidence** — a counterparty, a buyer, a lawyer | to check whether a specific business is what it claims | passport link → registry |

The consumer arrives by a **link from elsewhere** (an email, a footer badge, a due-diligence memo).
That makes the passport page, not the landing page, the load-bearing screen.

## 3. Screens

### 3.1 Passport (`/p/<subject-id>`) — the load-bearing one

Everything else links here. It is the page a lawyer will read a year from now.

Must show, in this order:
1. **subject identity** and the STRENGTH of its binding (`erc8004` strong, `git`/`dns` weak, with
   the reason: a domain expires and gets resold);
2. **projection 0–100** — and immediately beside it, never in a footnote, the disclaimer that the
   score measures autonomy and **not** reliability, decision quality, profitability, or the
   presence of an accountable party;
3. **per-operation table**: operation, level L0–L5 **or `not_measured` with its reason**,
   confidence (`measured` / `inferred`), and which limiters were applied;
4. **control map** with its own coverage: what was inspected, what was out of reach and why, and
   what an undiscovered path would look like;
5. **accountability block** — emergency stop, claims addressee, insurance, dispute path.
   Each field carries a value **or the reason none was established**, on the same three
   reasons as item 3. A measured *none* and an unchecked field are DIFFERENT statements and
   the artefact must say which one it is making. Visually adjacent to the score but visibly
   NOT part of it;

   > Until 2026-08-20 this item read "claims addressee (which may honestly be *none*)" and
   > granted the conclusion without the apparatus: item 3 demanded a reason two lines above
   > while item 5 awarded an "honest none" for a field nobody had to inspect. Three emitters
   > took the licence, and every passport issued under schema 1.0.0 claimed a completed check
   > that never ran. The asymmetry was in this document before it was in the code.
6. **provenance**: protocol version, profile version, evidence window, `valid_until`;
7. **affiliation disclosure** where `verifier_affiliation: same_owner`.

### 3.2 Registry (`/registry`) — the listing

A dense, searchable table. Columns: subject, status, autonomy, verifier, valid-until. Filterable by
subject. Density over decoration: this is a public evidence log, and an ornamented log does not
inspire trust. A trailing action column stays in the layout and empty (§4.2).

⚠️ **Corrected 2026-08-20.** This paragraph listed a `confidence` column and required the table to
be **sortable**. Neither exists: `Row` in `src/registry/public_registry.py` emits no `confidence`
field and `git log -S confidence -- src/registry/public_registry.py` finds no commit that ever put
one there, the live
`https://provek.dev/data/registry.json` carries none, and the page offers a filter over subject and
no sort at all. The demand is withdrawn rather than implemented, because implementing it would
require a decision nobody has taken: the master specification's `confidence` is a property of a
single **operation** (§6.1, `measured` / `inferred`), and a subject-level column would need a rule
for aggregating three operations — two or three of which are `not_measured` on every current row —
into one word. Inventing that rule to satisfy a sentence in this document is precisely the direction of
travel this project exists to detect. A registry `confidence` column, if it is wanted, is a
recorded decision first and a column second.

Must handle the **honest current state**: eight rows, all affiliated. See §6.

### 3.3 Landing (`/`) — for subjects

The only screen allowed air. Leads with the reason that works at zero funders: *a passport is an
artefact for **your** customers, not for ours.* Content comes from `docs/WHY_GET_VERIFIED.md`,
including its stated limits — those are a feature of the pitch, not a caveat to bury.

### 3.4 Apply (`/apply`) — intake

Repository URL and contact. **Without a mandate we do not touch production** — this must be stated
on the form, not in terms of service.

The **mandate choice** is on the form: read-only verification, or a request for an active-probing
mandate as well.

⚠️ **Withdrawn and restored on 2026-08-20, both within a day, and the second move is the narrower
one.** This section originally required "the mandate choice: passive verification only, or an
explicit mandate for active probing". The choice was removed in the morning (**D-21**) because no
prober existed to honour an active mandate — offering it would have asked a stranger to sign a
document nothing in this repository could act on, which is a false claim about US on the one page
where a visitor commits to something. That removal was recorded in `web/src/pages/Apply.tsx` and
`docs/INTAKE_OPERATIONS.md` but not here and not in `DECISIONS.md`, so the rule survived its own
repeal in the document that governs the form — L-2.

**The offer states the probe's cost in requests to the applicant's origin, and that number is the
one `src/prober/prober.py` spends** (`CALLS_PER_PROBE`, three today: a positive control, a negative
control and the attempt). Written here because the rule belongs to the document that governs the
form and not only to the form — which is the mistake the paragraph above records, made once already
on this same section. The offer said "one operation exists today" and nothing more: true in the
prober's unit of account, and the wrong unit for a page where a stranger decides what may touch
their production system. A claim too MODEST for its artefact is still a claim that does not match
it, and it is the direction nobody audits. `tests/test_apply_names_the_probe_cost.py` holds the
constant, this form — every screen of it, including the confirmation — and the same offer in
`docs/WHY_GET_VERIFIED.md` to one number: every quantity in that copy must be either the number the
prober spends or one declared in the gate, with the declaration quoting enough of its own sentence
to identify it, and the offer itself must state the count where the offer is made. What it compares
is **numerals in the text a visitor reads** — which is why what counts as that text is itself
guarded by instrument controls of its own: repeatedly, while this gate was being written, an
extractor silently dropped copy it was meant to read or admitted code it was not, and each time the
suite went green over a promise nobody could see or red over a status code. (No count is written
here, of the controls or of the failures. Four hand-typed numbers in this pair have already gone
stale against the artefact beside them, which is the defect the gate itself exists to catch; both
counts are one `grep` away in `tests/test_apply_names_the_probe_cost.py` and
`evidence/RED-019-an-offer-narrower-than-what-arrives.txt`.)

What it does **not** catch is unquantified vagueness — "a minimal probe", "barely touches your
server" — which states no number and so contradicts none. That is a deliberate boundary rather than
an oversight: a rule against adjectives would have no measured quantity under it. What keeps the
boundary honest is the presence rule, which requires the true count on the same screen, so vagueness
can stand beside the number but never instead of it.

T-2.12 built the prober, and the choice returned the same day under **D-23**, bounded twice over.
It names the ONE action the prober implements rather than "active probing" in general, because the
artefact is one action wide and the offer may not be wider. And it ASKS rather than grants: a
mandate is a legal object and not a checkbox, so the endpoint records `mandate_requested` beside a
`mandate_applied` that is constant `passive` — the hole D-21 actually closed, which stays closed.

### 3.5 Phase 2 (`/phase-2/`) — an announcement, and not an offer

⚠️ **Owed, not yet done: specification revision 1.4 renumbered the phase grid (§4, §4.0).** This
page and section describe what used to be called "phase 2" — Funding Tasks — which is now phase 3.
The page itself is reworked to the new grid last in the operator's phase-2 implementation cycle,
after every button on the site has been checked live, so that the rework is not undone by a later
finding; until then this section is read as describing the page as it stands, not as the target.

One page describes phase 2, and it is the only place on the surface that does. Four rules bind it,
and each one is a rule because breaking it would manufacture exactly the defect the product exists
to detect — a claim stronger than the artefact behind it:

1. it states, on the face of the page and again at its foot, that **nothing described is in service**
   and that **no application for it is being taken**;
2. it carries **no date, and no word standing in for one**. Nothing and nobody has committed to a
   date, so the page may not invent one;
3. it carries **no payment control**, in this phase or a later one (A-6, §4.1);
4. **every sentence on it traces to §4.1, to rules 1–3 above, or to the phase-1 screen it
   describes** (§3.1–3.4). A sentence that does not is not on the page.

   > Rule 4 first read "every sentence traces to §4.1", and the page it governs broke it on the day
   > both were written: the step "you ask to be verified, a passport is issued" is phase 1, and the
   > refusals are rules 1–2 of this section. Fable's objection is the one that matters here — a rule
   > tolerantly broken at birth teaches the next editor to reinterpret gates rather than obey them,
   > which is L-7 arriving from the other direction. The rule is widened to what it always meant.

It is reached from Method rather than from the landing. The landing's argument is built to hold at
zero funders — that is the point of it (specification §4.6) — and offering a future second side
there as a reason to apply would reintroduce the dependency the specification deliberately removed.

This page is a narrow exception to D-05, whose boundary otherwise stands: every reserved slot in the
layout stays empty, disabled and unannounced. Describing a phase is not the same act as offering a
capability, and the difference is recorded in D-16.

### 3.6 Method notes (`/method/notes/<slug>/`) — the methodology at length

The Method page states the ladder, the evidence classes and the three absences in a paragraph each.
A note takes one of them and writes it out: what the term measures, what it cannot, and which of
this repository's files settles the question. Reached from one sentence of prose on Method, with no
navigation entry.

**How many notes stand is not stated here, on purpose.** This section specifies the surface:
`/method/notes/` is emitted exactly when `web/notes/src/` holds a captured note, and the sentence on
Method that leads to it is written under that same condition — `LAW-NOTES-ENTRANCE` fails the build
if the two diverge in either direction. A count belongs to the index the surface renders, the one
copy of it that cannot drift from the artefact (§3.6 item 6 fixes the ceiling it may climb to, not
how many currently sit under it); this document does not keep a second copy that could go stale
between a capture and a reader. A specification is allowed to precede its instances; a page telling a
reader that writing exists when none has landed is not, which is the distinction §4 already draws for
phase 2.

**The genre is the constraint, and it is not a matter of taste.** ADR-0009 ruled that teaching and
verification stay separated as components: a surface written in the normative voice — *how to build
autonomous agents*, *how to score higher* — puts the institution's opinion where a reader cannot
tell it from the instrument's measurement, and an examiner coaching candidates grades work it set
itself. A note is descriptive or it is not published. Concretely, and each of these is a test rather
than an intention:

1. **every claim carries an address** — a section of this document, a decision, a law in
   `tasks/lessons.md`, a line of ERC-8004, or an emitted artefact. An address that does not resolve
   fails the build, so an untraceable sentence cannot reach the surface at all;
2. **no second-person imperative and no instruction vocabulary** — the boundary ADR-0009 draws, in
   machine form;
3. **no heading begins "How to"** — 35% of the question rows in the keyword capture do, and the
   largest measured one is *how to build an ai agent*. The demand is real and this surface may not
   serve it;
4. **a keyword is a row `seo/keywords.csv` returned**, carried with the demand state the base
   recorded, and never with a number where the instrument refused (D-17, §2.9). Zero to three per
   note; a note with none records why, because most of this subject has no measured demand at all;
5. **a figure is computed from an artefact at build time** — never drawn and then checked. Zero to
   three, and a note with none says why. No photograph and no generated image: neither carries a
   fact, and an ornament on a page about evidence is the failure this product exists to find;
6. **the corpus is capped at a ladder step, and every step is bought by a control-paired reading**
   (D-35). Three notes stand until Bing Webmaster reports a crawl row for this site beside a control
   property proving the same call able to report one; seven until it reports an impressions row the
   same way; above fifteen is an operator's decision rather than an automatic consequence. The
   precedent for this work gates its publishing rate on Search Console; we have none, and a rate
   gated on an absent instrument is not a gate (L-4). **The numbers 7 and 15 are assigned and carry
   no reading**, exactly as 3 did: what is measured is which step is open, not how far it carries;
7. **what drafted the prose is disclosed on the face of the page.** A note is planned by
   `claude-sonnet-5` and written by `claude-haiku-4-5`, then captured once and committed — the build
   calls no model. Measuring how much of somebody else's business runs without a human, while
   publishing machine-drafted prose in silence, would be this product's own defect wearing its
   colours.

**A note that turns out to be wrong is corrected in public.** The correction is a dated block on the
page, the claim it replaces stays legible, and `dateModified` moves because the text moved — the
manifest pins each body by hash so a rebuild cannot manufacture freshness. A note withdrawn is
marked superseded and keeps its URL. Passports are never silently recomputed (PRODUCT.md); prose
published from the same surface gets the same treatment.

### 3.7 Build (`/build/`, `/build/<slug>/`) — AI agent templates — NEW

Ruled by Fable, `docs/adr/ADR-0011-templates-are-a-machine-addressed-artefact-gated-from-the-instrument.md`,
recorded as D-57. Not an incubator, not a course: a static library of instructions a reader's own
coding agent turns into a running business agent, for one business operation at a time.

**Status as of 2026-09-05: this surface is built and live at `/build/`.** `templates/` carries the
contract, the licence and the gates below (Phase 0); all six v1 templates are admitted under them
and emitted: `customer-support-agent` (Phase 1); `lead-generation-agent`,
`ecommerce-operations-agent`, `market-research-agent` (Phase 2); `content-production-agent`,
`finance-operations-agent` (Phase 3, which also added a real three-question FAQ, in each
template's own words, to every template page — item 8 below). D-18 already set the precedent that
a specification may precede its instances — describing the target was not the same act as
offering it, exactly as §3.5 draws that line for phase 2, and Phase 0 shipped that description
against zero real templates on purpose.

1. **`/build/`** — one screen before a grid of admitted templates: an H1 stating the page is a
   library to copy from, not a service that builds for the reader; a three-step explanation with a
   tool selector (Claude Code / Codex / Cursor / Other) whose copied text is identical across
   tools; the grid itself, one bordered block per template naming its business operation, its
   human-in-the-loop point, what it needs, its dry-run date, a Copy control and a link to its page;
   and a closing "what follows" block stating, as facts with their conditions, what happens after
   an agent is built — never a promise of a verified outcome.
2. **`/build/<slug>/`** — one template, in progressive disclosure: the card's facts above the
   fold; a short description of what it does and what the reader gets; the artefact's own sections
   rendered as closed `<details>` blocks; the full `SKILL.md` text in a `<pre>`, plus the same
   bytes served raw at `/build/<slug>/SKILL.md` for a coding agent to fetch directly.
3. **The gate, in both directions (ADR-0011).** A template names no vocabulary of this instrument
   (`provek`, `passport`, `registry`, `verif*`, a level token, `autonomy level`, `projection`,
   `evidence window`, `score`); no file under `src/` or `scripts/` names the `templates/` path.
   Law `LAW-TEMPLATE-NAMES-NO-INSTRUMENT`, `templates/SCHEMA.md`.
4. **Publication requires a witnessed dry run** — `evidence/TEMPLATE-RUN-<slug>.json`, keyed to the
   `SKILL.md` body's sha256. No record: unpublished. A stale record: the page says the dry run
   predates the current revision, never presented as fresh. Law `LAW-TEMPLATE-WAS-RUN`.
5. **The funnel strip** — one component, fixed text, on every template page and on the index: that
   requesting verification is independent of this page, may return any level including
   *not measured*, and links to `/apply/` exactly once per page. No other route from a template to
   verification exists; no counters, no tiers, no "verified" wording anywhere under `/build/`.
6. **Machine channels.** Every `SKILL.md` is reachable raw, at its own URL, with an
   `Accept: text/markdown` sibling like every other page (§3.6's convention); `llms.txt` and
   `llms-full.txt` gain a *Templates* section generated from the emitted set, never typed by hand.
7. **Reuse, not a second design language.** The Copy control is one component
   (`web/src/components/CopyButton.tsx`), shared with the passport page rather than duplicated;
   zero new colours, fonts or ornament beyond `DESIGN.md`'s existing tokens.
8. **A real FAQ, and structured data that matches it.** Every template page carries a visible
   three-question `Questions` block — `What does a human still do?`, `What do I need before I
   start?`, `What happens after it runs?` — answered in that template's own words, authored in
   `templates/faq.json` (kept outside every `SKILL.md`, so an answer can be revised without
   invalidating that template's witnessed dry run). The same three answers are mirrored into a
   `FAQPage` JSON-LD block alongside the page's `TechArticle`; `tests/test_build_jsonld_validates.py`
   checks every emitted block parses as valid JSON and carries the fields its `@type` requires.

## 4. Phase 3 — Funding Tasks — deferred by A-10, specified in full

<!-- PHASE3-NOTE-START -->
Specification revision 1.4 (2026-09-02) renumbered the phase grid: Funding Tasks (specification
§8 in full) moved from "phase 2" to phase 3, with none of §8's own norms changed — only the
moment they take effect. "Phase 2" now names the Provider Catalog (§4.0 below, specification
§4.2-bis), not this section.
<!-- PHASE3-NOTE-END -->

### 4.0 Phase 2 — Provider Catalog (specification §4.2-bis) — NEW, revision 1.4

The section this heading used to hold — §8, Funding Tasks — is now phase 3 (§4.1 below). The phase
that actually ships next is the **Provider Catalog**: a subject holding a current `verified`
passport gets an outward "Order ↗" link to its own order-intake page (specification §4.2-bis).
The incubator is never a party to the order, never holds funds, and never routes anything — the
button's predicate (`verified` ∧ declared ∧ reachable) is code, not copy, and is designed and built
in full in the phase-2 implementation cycle (the operator's own five-step plan for it). This subsection
exists so §4.1's derivation below is read against the renumbering rather than against the phase
grid it superseded; the Catalog's own detailed page design is not duplicated here.

### 4.1 What a funding task is, and what it is not

Taken from specification **v1.4**, §8 and §4.2. This subsection exists because a page now states
these things in public (§3.5), and a public statement whose only address is a document on the
operator's laptop is a claim the reader cannot check — which is the shape this product exists to
reject.

<!-- PHASE3-NOTE-START -->
Specification revision 1.4 (2026-09-02) renumbered the phase grid: Funding Tasks (specification
§8 in full) moved from "phase 2" to phase 3, with none of §8's own norms changed — only the
moment they take effect. "Phase 2" now names the Provider Catalog (§4.0 below, specification
§4.2-bis), not this section.
<!-- PHASE3-NOTE-END -->

⚠️ **Re-derived for revision 1.4, and the same gap remains for whatever comes after it.** The
source document is not in this repository and no test can read it, so a v1.5 that changes §8 again
would leave this subsection quietly wrong and every check green — the phase-3-note markers above
are checked byte-for-byte against each other by `scripts/ratchet_phase3_note.py`, which catches one
copy going stale against the other, but neither copy is checked against the laptop-only master
document itself. Saying so is the honest half; the other half is a rule with a human behind it
rather than a machine — **an edit to specification §8 requires this subsection to be re-derived**,
and that belongs on the operator's checklist. Naming an unarmed rule as unarmed is the practice of
`tasks/lessons.md` L-8: a law with a fake anchor is worse than an honest note.

**Deferred, not cancelled.** Decision A-10: projects first, because the registry is useful without
the second side and the second side is not useful without the registry (§4.2-bis, phase 2).
Specification §8 defines phase 3 anyway, so that it will not have to be designed twice.

**What it is.** A funding task is a **contract for services — procurement**. Not a grant, not a
donation, not a pre-payment for a share, not an investment contract (§8.1). The funder is a
**customer** and takes delivery of the result (A-2); a share of revenue is excluded permanently, not
deferred (A-3). The terms `investment`, `investor`, `equity` and `secondary market` are forbidden in
the product — and §8.1 records in the same breath that the prohibition is not itself a legal
argument, because classification follows substance rather than vocabulary.

**Money.** The incubator holds and routes no funds: no escrow, no treasury, no keys (A-6, §4.3
non-goal 1). The customer pays the agent **directly**. The milestone contract is **deployed by the
parties themselves** from a template the incubator publishes, and the incubator holds no
administrative key to it — deploying it and holding keys would return the custodial risk A-6
removed through the back door, and "we are only infrastructure" would stop being true (§8.2). A
commission on transfers is excluded forever (§11.4). The phase-2 revenue stream is a fixed fee for
the witnessing itself (§11.4, and §5 below).

**Conditions of creation.** A draft missing `acceptance_criteria`, `failure_criteria`, `timeout`,
`milestones` or `cap` never becomes a task — the policy gate refuses it, and that is a condition of
creation rather than a recommendation (§8.2; on `rejected`, see the lifecycle note below). **One task, one principal:** financing out of the commingled funds of an agent acting for
several principals is forbidden in phase 2.0, and the gate follows `funder → delegation → principal`
rather than stopping at the funder (§8.2, §8.6).

**Lifecycle** (§8.3):

```
draft → policy_check → funded → executing
policy_check → rejected            (a condition of creation is missing, §8.2)
executing → milestone_released → executing        (partial release)
executing → completed              (every acceptance criterion met)
executing → failed                 (a failure criterion fired)
executing → timed_out              (the timeout expired — BY TIME, with no event)
failed | timed_out → settled       (the uncommitted remainder returned by code)
```

The parenthesised conditions are §8.3's own and are reproduced rather than summarised: the page
shows them, and §3.5 rule 4 requires the page's every sentence to have an address here.

Terminal: `completed`, `settled`, `rejected`. **There is no cancellation by the funder** (A-4); all
three exits from `executing` are performed by the contract rather than decided by a person. An
undefined transition is impossible, not undocumented.

**The arrow into `rejected` is a ratified erratum, not a reconstruction anymore.** Specification
revision 1.3's §8.3 listed `rejected` as terminal while its diagram showed nothing reaching it, and
§8.2 says a task missing a condition of creation *is not created at all* — which could not both be
true and leave it sitting in a terminal state. Revision 1.4 resolves this in the specification
itself, not only on this page: a **draft** is refused at `policy_check` and never becomes a funded
task, which satisfies both sentences, and the diagram above now carries the arrow as a norm rather
than as this page's own interpretation (`DECISIONS.md` D-45).

**Enforced against evidenced** (§8.5) — "the most frequent place where such products lie", and §8.5
puts the obligation on the interface: UI and documents must show the status of every constraint.
`enforced` means the deployed contract **carries the constraint out itself**; `evidenced` means it
can be shown and argued, and nothing more. Neither word promises a contract free of defects, and the
surface may not upgrade `enforced` into a guarantee of impossibility: §8.5 says "enforced by the
contract" and spends the word *impossible* only on the state machine (§8.3). The template has not
been through the lawyer's review §8.2 requires.

| constraint | status |
|---|---|
| ceiling on the amount | **enforced** by the contract |
| permitted on-chain recipient | **enforced** |
| release of a milestone against a machine-checkable criterion | **enforced** |
| timeout and return of the uncommitted remainder | **enforced** |
| "the money was spent on compute" | **evidenced only** |
| "the work was done well" | **evidenced only** |
| "the agent did not hand the task to a human" | **evidenced only**, probabilistic |

**Unresolved, and published as unresolved.** Only machine-checkable acceptance criteria are
admitted, so a dispute about quality is not admitted into such a task — it is never created, and an
observer holding no money cannot be an arbiter (§8.5). Witnessing creates **reliance exposure**: a
party relies on our statement at the moment funds move, and both that and the milestone-contract
template are marked as requiring a lawyer's review before phase 2 (§8.2, §8.5). "The agent did not
hand this task to a human" is not verifiable at reasonable cost (T1, §1.4) and is published as a
probabilistic signal, never as a verdict.

### 4.2 It must fit without a redesign — NEW

The operator's explicit requirement, now satisfied one phase earlier than it was written for.
Phase 3 (Funding Tasks, 47 requirements, specification §8) is deferred by decision A-10, not
cancelled; phase 2 (Provider Catalog, specification §4.2-bis) is the phase that fills the slots
named below, and this section is corrected rather than left to read as if phase 2 still meant
Funding Tasks:

* the registry row's **trailing action column**, empty in phase 1, is filled in phase 2 by an
  "Order ↗" link for `verified`+reachable subjects (§4.2-bis point 3) — not by "commission work",
  which stays a phase-3 concern and is not designed here;
* the passport page's **task history section**, hidden while empty rather than absent from the
  layout, is filled in phase 2 by WitnessRecord entries (§4.2-bis point 4, the D-05 slot), before
  any phase-3 funding-task history exists to share it;
* navigation reserves a slot for **corpus access** (revenue stream 3).

**Never, in any phase: a "pay" button.** Money does not flow through us (decision A-6, a
permanent non-goal, strengthened rather than loosened by §4.2-bis). A customer pays a provider
directly; in phase 3, a funder pays the agent directly and the milestone contract is deployed by
the parties. An interface that implies otherwise would promise what the architecture refuses to do.

## 5. How the product makes money — and what that means for the layout — NEW

From specification §11.4. A commission on transfers is excluded forever.

| stream | surfaces where it lives |
|---|---|
| paid verification | apply flow (later; free at first) |
| fixed fee for witnessing execution | phase 2, task history |
| **corporate access to the evidence corpus** | a reserved nav slot; the registry is its shop window |
| **regulatory dossier** | a passport export action |

Streams 3 and 4 are the real business, and both are **accumulating assets**. The registry page is
therefore not a directory — it is the visible surface of the asset being accumulated. It should
read that way even at eight rows.

## 6. Data — real, and honestly scarce

**Eight records exist. All are the operator's own systems, all carry `same_owner`.**

The master specification's first cohort is eleven. The three that are not here are named
in [`docs/COHORT_EXCLUSIONS.md`](docs/COHORT_EXCLUSIONS.md) with the §2.7 condition each
one fails, because a registry that silently holds eight where its own specification says
eleven has made an unexplained choice.

⚠️ **Corrected 2026-08-20.** This table listed a projection for all eight. It stopped being true
when the pipeline moved to an anonymous channel: **four** of the eight subjects are private
repositories and return 404 to a reader holding no credential, so their verdicts were never
reproducible by a third party. (This correction said "five" until it was itself re-counted on
2026-08-20 — against anonymous GitHub, which answers 404 for exactly four of the eight, and against
the emitted registry, which carries exactly four `unreadable` rows. A miscount inside a paragraph
correcting a miscount is the shape worth naming, not hiding.) The numbers below are now read from the emitted registry rather
than asserted here, because a specification that describes an artefact it has stopped matching is
the drift this project exists to catch.

| subject | state | why |
|---|---|---|
| AIpush, APIbase, mcp-protocol-tester, provek | verified, projection 40–80 | public, readable anonymously |
| AI-Property-Sales-Platform, audiobook-shorts-series, cryptocardhub-defycard, gov-auction-report | **unverified, `unreadable`** | private repositories; no anonymous reader can recompute the verdict |

**At least** two of three operations on every subject are `not_measured` — runtime evidence is not
collected yet, and the passport says so. On the four unreadable subjects it is all three, and the
three are not all absent for the same reason: `development_initiation` is `unreadable` there,
because a repository that returns 404 to an anonymous reader cannot be read at all, while
`deployment` and `treasury_control` are `check_did_not_run` on those subjects exactly as they are
on the public four. Two absences with different causes must not be summed into one word — that is
invariant 1 in prose rather than in a field.

⚠️ **Corrected 2026-08-20.** This read "two of three operations on every subject". It is true of
four of the eight; the four private subjects carry three `not_measured` operations each — counted
from the emitted passports, the same reading that produced the table above. The sentence was
presumably written against the credentialed pipeline, but that is not reconstructible from this
repository: the oldest commit carrying emitted passports already shows `unreadable` on the private
four, so no tracked state ever matched the claim, and no reader can check when it did.

**We will not invent additional companies to fill the table.** Rule 6 of the design methodology
forbids inventing facts about the product, and fabricated entries in a trust registry are the worst
possible instance of it. Instead the **near-empty state is a designed state**, because it will be
real for months: it must explain what the registry is, why it is small, and how to be in it —
without apologising.

## 7. What we may honestly claim, and what would be a lie

From specification §1.4, §3 and the unimplementable register.

**True:** we measure autonomy per operation from evidence; we publish our own coverage; we hold
ourselves to the same protocol and our own passport shows our own gaps.

**A lie if stated:** that we prove a human did not write the code (unverifiable at reasonable cost
— published as a probabilistic signal, never a verdict); that a control map proves no undiscovered
path exists (impossible in principle); that a verified badge means safe, reliable, or profitable.

The interface must make the second list impossible to read into it.

## 8. Design direction

* **Tone:** strict instrument. Closer to SSL Labs than to a marketing page. The landing is the only
  screen with air.
* **Density:** dense on registry and passport; comfortable on landing and apply.
* **Themes:** both, **light by default** — the passport is opened from an email by lawyers and
  buyers, not only by developers at night.
* **Brand:** none yet. Typography and palette come in Phase 4 as three variants.
* **Accessibility:** WCAG AA in both themes, visible focus everywhere, full keyboard flow.

## 9. References (Phase 2 clone targets)

| reference | what we take |
|---|---|
| **SSL Labs SSL Server Test** | the hierarchy verdict → what it is made of → what could not be tested; caveats beside the grade, not in a footnote |
| **OpenSSF Scorecard** | check → result → evidence link; failed and inapplicable checks shown alongside passed ones; public methodology as an asset |
| **crt.sh** | density and instant search of a public log; nothing ornamented |

**Anti-example:** startup directory showcases (Product Hunt and kin) — big logos, vote counts,
gradients. They sell attention; we sell evidence, and borrowing their language would make eight
records look like advertising.

## 10. Forbidden (from the methodology, plus ours)

Inter/Geist by default everywhere; purple-blue or neon gradients as identity; card inside card
inside card; grey text on colour below AA; emoji instead of icons; `shadow-2xl` everywhere; 16px
radius on everything; the stock hero of centred headline plus two buttons plus a framed screenshot.

**Ours, additionally:** any element that presents `not_measured` as a zero; any badge that reads as
a safety rating; any pay button; any fabricated registry entry.

## 11. Technical

Preact (through `preact/compat`, so the source still imports from `react`) + TypeScript + Vite +
Tailwind — the runtime is Preact, and `web/vite.config.ts` is what settles it. Deploy to
Cloudflare Pages via Wrangler, domain
**provek.dev**. The site is static and reads `registry.json` and passport JSON produced by the
validator — the same artefacts machines consume, so the human surface can never drift from the
machine one.

Repository layout follows the methodology: `/web` working app, `/web-1.0` frozen clone, `/refs`
reference captures. The existing Python validator under `src/` is untouched.
