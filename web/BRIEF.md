# Design brief — Provek web surface

Written by `/impeccable shape` after `init`. This is the contract the three phase-4 variants are
judged against. It states intent, never CSS.

## 1. Job and audience

The landing page speaks to the **subject** — a team running an agent business, arriving cold and
already tired of "AI-powered" being unfalsifiable. Visitor mode: **Persuade**. They must decide in
under a minute whether this standard is real enough to submit to.

The passport speaks to the **consumer of evidence** — a counterparty or lawyer who arrived by a
link from elsewhere and will read one document, once, possibly a year after issue. Visitor mode:
**Read**. It is the load-bearing screen and the one every variant is compared on.

The registry serves both and is mode **Operate**: scan, filter, leave with a link.

## 2. Outcome and proof

Primary action for the subject: request verification. Primary outcome for the consumer: understand
what a number does and does not claim, and see what was not measured without hunting for it.

The proof available is small and must not be inflated: eight passports, all the operator's own
systems, all affiliated, two of three operations unmeasured on every one. Two measured answers
exist and are worth showing: 50,275 on-chain identities, 0.006 CPU-seconds per verification.

## 3. Structural thesis (shared by all three variants)

**Coverage is legible before the text is read.** A reader should see how much of a passport was
actually measured from across the room. Today that fact is only reachable by reading each row.

This is the one structural idea every variant must implement, because it is the product's argument
made visible rather than argued. Variants differ in how far they take it.

## 4. Scope and boundaries

**In scope:** typography, spacing, colour, components, states, and — for L only — grid and identity.

**Untouched by all variants:** the copy's factual claims, the data path, the route table, the
information architecture of the passport (order of blocks is specified), and the reserved phase-2
slots, which stay disabled and unannounced.

**Anti-goals, in the product's own terms:**

- No emblem, mark, or wordmark invented to look established. An emblem earned before a method is
  the substitution this product exists to detect.
- No decorative charts. A bar that restates the number beside it is not evidence, and a bar that
  implies precision we do not have is worse.
- No gradient-on-dark "AI product" idiom. The category signal we want is *registry*, not *startup*.
- Nothing that makes `not_measured` quieter than a measured value. Lighter ink, smaller type, or a
  neutral dash for absence is an argument by typography for dismissing the fact.
- No motion that runs before the reader asks for it on the passport. It is a document.

## 5. States and ranges

Real ranges, from the emitted artefacts:

| thing | min | typical | max seen |
|---|---|---|---|
| registry rows | 0 (filtered) | 8 | designed to hold hundreds |
| subject identifier | 12 chars | ~35 | 240 tested, must wrap |
| operations per passport | 3 | 3 | open-ended |
| unmeasured operations | 0 | 2 of 3 | 3 of 3 |
| out-of-reach surfaces | 0 | 3 | open-ended |

Material states, all already built and all to be carried forward: loading (shaped like what is
coming), empty-by-filter, missing passport, unreadable passport, unknown route, expired passport
(`stale`), long identifier, and a passport whose every field is unmeasured.

## 6. Interaction and layout

Hierarchy on the passport: identity → affiliation warning → projection with its disclaimer →
per-operation ladder → accountability → identity binding → control-map coverage → self-reported.
That order is specified and does not change.

Responsive: four breakpoints are already proven at 360 / 768 / 1280 / 1920. The registry collapses
from table to stack below 640 and drops no field when it does.

Keyboard: skip link, focus moved to the top of a new route, live count on filter. Established in
phase 3 and inherited.

## 7. The three variants

| | scope | thesis |
|---|---|---|
| **S** small | type scale, spacing, contrast. System font stack, no new dependency. | The cheapest possible improvement. Proves how much of the gap is rhythm rather than identity. |
| **M** medium | + palette with dark mode, component set, evidence-class treatment, state design. | A standards body with a real system. IBM Plex, because it was drawn for technical documents. |
| **L** large | + own typographic pairing, asymmetric grid, one visual device. | **The unfilled slot.** A measured fact is set solid; an unmeasured one keeps its empty slot visible with a rule where the value would be, so the shape of what is missing is the page's texture. |

Layout skeleton stays recognisable in all three. The winner may be a hybrid.

## 8. Constraints a builder must not invent

- WCAG 2.2 AA, measured against **both** grounds, not white alone.
- Fonts are self-hosted. No external font request, no CDN.
- No new runtime dependency beyond fonts; the bundle is 222 kB and should not grow materially.
- Dark mode, where a variant offers it, must be a real palette rather than an inversion.
- Every number on screen must exist in the emitted artefact. Nothing is computed for display.
