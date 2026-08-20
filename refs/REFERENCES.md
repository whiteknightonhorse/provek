# Reference capture — Phase 2

Captured 2026-08-20 by driving a real browser, not from memory. Where a reference could not be
reached, the substitution is recorded rather than papered over.

---

## R1. Qualys SSL Labs — SSL Server Test report

`https://www.ssllabs.com/ssltest/analyze.html?d=github.com`

**Why this one.** The closest structural analogue that exists to our passport: a graded verdict, the
dimensions it is made of, and explicit statements about what could not be established.

### Observed structure

1. Breadcrumb, then `SSL Report: github.com (140.82.113.4)` — **subject identity carries its
   technical locator right next to the human name**.
2. Immediately under the title: `Assessed on: Wed, 19 Aug 2026 12:12:37 UTC | Clear cache`.
   **Provenance is the second thing on the page**, not a footer.
3. **Summary block**: a large letter grade (`A+`) in a filled square on the left, and on the right a
   horizontal bar chart of four sub-dimensions — Certificate, Protocol Support, Key Exchange,
   Cipher Strength — each scored on a 0–100 axis with visible gridlines.
4. Below the summary, a stack of **full-width status strips**, one finding per strip:
   - green for a positive finding (`This server supports TLS 1.3`),
   - **amber for a negative one** (`This server does not support PQC key exchange`),
   - each with a `MORE INFO »` link.
   The negative finding is not hidden, not collapsed, and not styled as an error — it sits in the
   same rhythm as the positive ones.
5. Detail sections: an icon, a blue heading, then a **two-column label/value table**. Label column
   is fixed and narrow; value column flexible. Row separators are 1px hairlines; rows are compact.
6. Secondary detail (fingerprints, pins, CAA records) renders as **smaller grey lines beneath the
   primary value inside the same cell** — no nested cards, no accordions.
7. Positive values are rendered as **green text** (`Yes`, `Trusted`), not as badges.

### What we take

The hierarchy verdict → what it is made of → what could not be established. Provenance high on the
page. The status-strip pattern for findings, including negative ones stated plainly. Two-column
dense tables with sub-detail inside the cell. Green as text colour, not as a pill.

### What we deliberately do not take

The 2010s chrome: bevelled panels, the red masthead, centred page column at a fixed 1200px. We keep
the information design, not the era.

---

## R2. OpenSSF Scorecard — report viewer

`https://scorecard.dev/viewer/?uri=github.com/ossf/scorecard`

**Why this one.** The closest analogue by subject matter: it scores a project on verifiable signals,
shows every check with its evidence, and publishes the methodology.

### Observed structure

1. Header band, then the subject line: an icon and `github.com/ossf/scorecard`.
2. **Aggregate score `9.0` inside a ring** on the left of the identity.
3. Directly under the identity, a four-line provenance block in small caps labels:
   `API URL`, `COMMIT` (full sha), `GENERATED AT` (ISO timestamp), `SCORECARD VERSION: v5.5.0`.
   A `SORT:` control sits at the right of the same block.
4. Then a **flat list of check rows**, each row:
   - left rail: status icon, the numeric score, and a **coloured underline bar** whose colour
     encodes the outcome;
   - check name in bold, followed by a **severity chip** (`CRITICAL` red, `HIGH` red, `MEDIUM`
     amber, `LOW` yellow);
   - a one-line plain-language description of what the check determines;
   - an expand chevron on the right.
5. **THE FINDING THAT MATTERS MOST TO US.** The last row, `Branch-Protection`, shows **`?` instead
   of a number**, with a neutral grey underline — a check that could not be evaluated. Meanwhile
   `Vulnerabilities` shows a **measured `0`** with a red icon and a red underline.
   The two are visually distinct: an unmeasurable check does not look like a failing one.

### What we take

This is decision D-03 already solved by someone else, in production, in a product people trust:
`not_measured` gets its own glyph and its own neutral colour, and sits in the same list as scored
items rather than being filtered out. We take the row anatomy wholesale — rail with score and
colour bar, name, severity chip, one-line description, expand — and the provenance block under the
identity.

### What we do not take

The purple masthead and the card-with-rounded-corners container. Our severity chips will encode
evidence class and confidence, not danger.

---

## R3. NVD Vulnerability Search — dense public log

`https://nvd.nist.gov/vuln/search`

**⚠️ SUBSTITUTION, RECORDED HONESTLY.** The planned third reference was `crt.sh` (Certificate
Transparency log search). It returned **502 Bad Gateway** on both attempted queries at the time of
capture. Describing it from memory would be inventing a fact, which the methodology forbids, so a
reference of the same class was captured instead. If crt.sh returns, it is worth a second look for
table density specifically.

### Observed structure

1. Search field with an adjacent icon button, then `Advanced`, `Reset`, `Show Statistics`.
2. A results bar: `Items per page: 25`, `1–25 of 380851`, and first/prev/next/last controls.
   **The total count is stated plainly** — the log does not hide its size.
3. Table columns: `Identifier` (a link), `CISA Kev Info` (icon only), `Published Date`, `CNA`,
   `Description` (long, wrapping, two to three lines).
4. Row separators are hairlines; row height is driven by the wrapping description rather than fixed.
5. **Skeleton state observed live**: before data arrived, each cell rendered as a grey rounded
   block sized roughly to its expected content, with the column headers already in place. The
   header row does not shimmer; only the cells do.

### What we take

Plain statement of the total. Pagination controls including first/last. A description column
allowed to wrap and drive row height, rather than truncating evidence to fit a grid. The skeleton
pattern with headers already present — it keeps the page from reflowing when data lands.

### What we do not take

The government-portal masthead, and the search-first layout: our registry is small and browsable,
so the table comes first and search filters it.

---

## Consolidated: what the clone must contain

| element | source |
|---|---|
| verdict block: big number + dimension bars | R1 |
| provenance directly under identity | R1 + R2 |
| check/operation row: rail, score, colour bar, name, chip, description, expand | R2 |
| **`?` glyph and neutral colour for unmeasured, distinct from a measured zero** | R2 |
| finding strips, negative ones stated in the same rhythm as positive | R1 |
| two-column dense label/value tables with sub-detail inside the cell | R1 |
| total count stated plainly, pagination with first/last | R3 |
| description column wraps and drives row height | R3 |
| skeleton with headers already present | R3 |

None of the three uses a card inside a card. None uses a gradient. All three state what they could
not determine. That is the aesthetic we are borrowing, and it is not an aesthetic — it is a habit.
