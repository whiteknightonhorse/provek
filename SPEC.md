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

A dense, searchable table. Columns: subject, status, projection, confidence, valid-until,
affiliation. Sortable and filterable. Density over decoration: this is a public evidence log, and
an ornamented log does not inspire trust.

Must handle the **honest current state**: eight rows, all affiliated. See §6.

### 3.3 Landing (`/`) — for subjects

The only screen allowed air. Leads with the reason that works at zero funders: *a passport is an
artefact for **your** customers, not for ours.* Content comes from `docs/WHY_GET_VERIFIED.md`,
including its stated limits — those are a feature of the pitch, not a caveat to bury.

### 3.4 Apply (`/apply`) — intake

Repository URL, contact, and the mandate choice: passive verification only, or an explicit mandate
for active probing. **Without a mandate we do not touch production** — this must be stated on the
form, not in terms of service.

## 4. Phase 2 must fit without a redesign — NEW

The operator's explicit requirement. Phase 2 (Funding Tasks, 47 requirements, specification §8)
is deferred by decision A-10, not cancelled. The layout must have a place for it from day one:

* the registry row gets a **trailing action column**, empty in phase 1. In phase 2 it holds
  "commission work" for listed subjects;
* the passport page gets a **task history section**, hidden while empty rather than absent from
  the layout;
* navigation reserves a slot for **corpus access** (revenue stream 3).

**Never, in either phase: a "pay" button.** Money does not flow through us (decision A-6, a
permanent non-goal). A funder pays the agent directly and the milestone contract is deployed by
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

| subject | projection | why |
|---|---|---|
| AI-Property-Sales-Platform, audiobook-shorts-series, gov-auction-report, APIbase | 80 | runtime trace present (CI runs) |
| AIpush, cryptocardhub-defycard, mcp-protocol-tester, provek | 40 | zero CI runs → limiter O2 capped the level at L2 |

Two of three operations on every subject are `not_measured` — runtime evidence is not collected
yet, and the passport says so.

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

React + TypeScript + Vite + Tailwind. Deploy to Cloudflare Pages via Wrangler, domain
**provek.dev**. The site is static and reads `registry.json` and passport JSON produced by the
validator — the same artefacts machines consume, so the human surface can never drift from the
machine one.

Repository layout follows the methodology: `/web` working app, `/web-1.0` frozen clone, `/refs`
reference captures. The existing Python validator under `src/` is untouched.
