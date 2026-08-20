# Audit — phase 4 exit

Run against the merged winner (M base + L's slot) on the built artefact, not the source. Every
number below was measured in a browser on the served files.

## Health score

| # | Dimension | Score | Key finding |
|---|---|---|---|
| 1 | Accessibility | 4 / 4 | WCAG 2.2 AA met and measured in **both** themes; three defects found and fixed here |
| 2 | Performance | 3 / 4 | 342 KB, 8 requests, no animation — but 222 KB of React for five static routes |
| 3 | Theming | 4 / 4 | Zero hard-coded colours in components; the dark palette is authored, not inverted |
| 4 | Responsive | 4 / 4 | 20 of 20 route × width combinations with no horizontal overflow |
| 5 | Implementation integrity | 4 / 4 | Detector clean; one device carried through 8 instances rather than eight ideas |
| **Total** | | **19 / 20** | Excellent. Threshold was 3 on every axis. |

## Implementation integrity verdict — PASS

The bundled detector returns an empty finding list over `web/src`. Verified by hand beyond it:

- **Zero hard-coded colours** in any component. 109 token references, one palette file.
- **One device, eight instances.** The unfilled slot appears wherever absence appears — three
  ladder rails, four accountability rows, one projection — and nowhere else. It is not a motif
  applied to decorate; it is the same fact rendered the same way each time it occurs.
- **The page could not be swapped onto another product.** Its structure encodes this product's
  claims: a disclaimer adjacent to the score, an affiliation warning above the evidence, coverage
  stated before the detail, a control map that publishes what it could not reach.
- None of the category defaults are present: no icon-heading-text card grid, no hero metric, no
  eyebrow labels, no section numbering, no gradient text, no coloured left bar, no pills standing
  in for data, no emoji as icons.

## Defects found by this audit, and fixed

**[P1] The slot failed the non-text contrast floor.** `--c-slot` was set by eye at `#b3aea4` and
measured **2.19 : 1** against paper. WCAG 1.4.11 puts the floor for a non-text element that carries
information at 3 : 1. The mark that carries this product's entire argument was below the floor at
which a reader is guaranteed to see it. Now `#8d8677` — **3.58** on paper, **3.26** on the page
ground, **3.46** in dark. Measured, not judged.

**[P2] Touch targets under 44px.** The masthead call to action was 36px, the nav links 40px, the
wordmark 26px. All cleared WCAG 2.2 AA (24px), none cleared 2.5.5 AAA. Raised to 44 — this document
is read on phones in meetings.

**[P3] The reserved slot fell below 3 : 1** when the palette changed under it (2.92). An
`aria-disabled` control is exempt from 1.4.3, so this was not a violation; it is held above 3
anyway, because "legible but plainly inert" was the intent and 2.92 was drifting toward illegible.

## Open, deliberately

**[P2] 222 KB of JavaScript for five static routes.** Inherited from the clone. React is doing hash
routing and rendering four documents. Aliasing `preact/compat` would remove roughly 180 KB, and
prerendering would remove the rest of the cost for a first-time reader. Not a phase-4 change: it
alters the runtime, and the phase-4 contract was appearance.

**[CLOSED in phase 5] `prefers-reduced-motion` was a global 0.01ms kill.** Replaced before the
first transition was written, as this document required. Travel now goes and feedback stays:
animations are set to `none`, presses lose their 1px offset, and colour, border, outline and
shadow transitions survive. Verified by flipping the rule's condition in the CSSOM and reading
computed styles on both sides — under reduce, three animations resolve to `none` while
`transition-property` keeps the four colour properties.

**[CLOSED in phase 5] The landing page's empty right half.** Filled with the registry itself —
four real rows, real projections, the affiliation named. The page claims a standard exists and the
registry is the only thing that can show it does. A wall of logos would have been the substitution
this product exists to detect.

**[Stated exception] `Corpus`, the reserved phase-2 nav slot, sits at 3.41 : 1 light and 3.38 dark**
against a 4.5 floor. It is an inactive control marked `aria-disabled` and exempt under WCAG 1.4.3.
Recorded here so a later reader finds a decision rather than rediscovering a defect.

## What was measured, and how

| check | instrument | result |
|---|---|---|
| Text contrast, both themes | computed styles walked against the resolved background of each node | 0 failures except the stated exception |
| Non-text contrast | the slot's border colour against its surface, in both themes | 3.58 / 3.46 |
| Horizontal overflow | `scrollWidth` vs `clientWidth`, 5 routes × 4 widths | 20 of 20 clean |
| Touch targets | bounding boxes of every link, button and input | none under 24; none under 44 outside inline text links |
| Landmarks and semantics | one `main`, one `header`, one `footer`, two `nav`, one `h1` per route | clean |
| Labels and alt text | every input's `labels`/`aria-label`; every `img`'s `alt` | 0 unlabelled, 0 missing |
| Transfer weight | `performance.getEntriesByType('resource')` on the served build | 342 KB, 8 requests, 4 font files at 86 KB |
| Hard-coded colour | regex over every `.tsx` for hex and `rgb()` outside token references | 0 |

The font figure is what the browser fetches, not what sits on disk. On disk the build carries
780 KB of IBM Plex because every subset is installed; only the latin faces are ever requested.
Reporting the disk number would have overstated the cost by a factor of nine.

## Positive findings worth keeping

- The absence reason lives in the accessible name, not in a `title` attribute. A reason reachable
  only by mouse is not published.
- The registry stacks rather than scrolls below 640px, and drops no field when it does — including
  the affiliation marker, which is the one a small screen would be most tempted to hide.
- Focus moves to the top of a new route, because a hash swap leaves focus on a document that is
  gone.
- The filter count is announced live; it is the only thing that says how much of the registry a
  filter has hidden.

---

## Phase 5 addendum — what motion cost, and the instrument that nearly cost more

Re-measured after the motion pass: **CLS 0** across load and five route changes, **20 of 20**
route × width combinations without horizontal overflow, **zero** contrast failures in both themes
bar the stated `Corpus` exception, **no console errors**.

**Two defects found and fixed in this pass:**

**[P1] Route change scrolled the reader past the masthead.** Focusing the content container
scrolls it into view, which on a short page parks the reader below the header on a document they
have not started. Now `focus({ preventScroll: true })` with an explicit scroll to top — a new
route means the top of a new document, then focus at the start of its content.

**[P2] The paced reveal was written as an opacity fade.** A scroll-driven fade that fails to
complete leaves text permanently dimmed, below its contrast floor, in the section that lists what
this product refuses to claim. Rewritten as travel only: a reveal that fails to complete leaves an
item eight pixels low and fully legible. **The failure mode chooses the property.**

**THE INSTRUMENT, AND THE NEAR MISS.** Three separate measurements said the authored moment was
inert: `animation-timeline: view()` produced no progress, a minimal isolated control produced no
progress, and a bare IntersectionObserver never fired. I was one edit from concluding the technique
was broken and rewriting it a third time. The cause was `document.visibilityState === "hidden"` —
the measuring tab was not frontmost, and Chrome suspends scroll timelines, observer delivery and
CSS transitions while a document is hidden.

The same blindness produced a burst of false contrast failures the moment transitions were added:
every flagged element was an anchor whose colour transition could not advance, so its computed
colour belonged to the previous theme while its background belonged to the new one. Seven
fabricated failures, all of them the instrument.

Two consequences are now in the code rather than in this paragraph: contrast is scanned with
transitions and animations disabled, and the reveal carries a two-second release valve so a
document opened in a background tab can never sit permanently offset waiting for an observer that
will not speak.

---

## Phase 6 — deployed, and measured on the deployed artefact

Live at **https://provek.pages.dev**. Cloudflare Pages, project `provek`, production branch `main`.

⚠️ **How a commit becomes a live page, written down because this line used to imply an answer it
did not give.** The project is **direct upload**, not connected to the GitHub repository: publishing
is a manual `wrangler pages deploy` of a locally built `dist`, run by whoever holds the Cloudflare
credential. **A push to `main` publishes nothing.** Measured on 2026-08-20 rather than assumed: two
pushes produced no Cloudflare activity in fifteen minutes; `/commits/{sha}/check-runs` returns four
GitHub Actions runs and no Cloudflare app on the same commits; the repository's deployments list is
empty (HTTP 200 and empty, which is a reading, not a refusal); and the live bundle
`index-Bd67xZVW.js` does not match a fresh local build, so what is served descends from somebody's
working copy rather than from a commit.

Two consequences, and neither is fixed by this paragraph. **The gate chain guards `commit → push`
and nothing guards `build → publish`** — the emitted-artefact half of every web test reads
`web/dist`, which is not tracked, so it is skipped on CI and cannot see what is actually uploaded.
And **an agent working from this host cannot complete a task whose acceptance criterion is a live
URL.** The honest form of that is a BLOCKED report naming the missing channel, not a green tick over
a built directory: a file in `dist` is not what the consumer receives.

### Lighthouse on the deployed site, mobile profile

Repeat runs, because a single run here is not evidence. Every figure below comes from a run whose
`benchmarkIndex` was near 3000; runs that landed near 200 are excluded and the reason is in the
next section.

| screen | performance | accessibility | best practices | SEO | LCP | TBT | CLS |
|---|---|---|---|---|---|---|---|
| Landing (3 runs) | 98 / 100 / 100 | 100 | 100 | 100 | 1.4 s | 0 ms | 0.013 |
| Registry | 97 | 100 | — | — | 2.1 s | 0 ms | 0 |
| Passport (2 runs) | 98 / 95 | 100 | 100 | 100 | 2.1 s | 0 ms | 0 |

Desktop profile on the landing: **100 / 100 / 100 / 100**, FCP and LCP 0.4 s, 73 KiB over 7
requests, zero console errors.

**Threshold met: every axis at or above 90 on every screen.**

### The defect only the deployed measurement could produce

**[P1] CLS 0.126 on the passport, mobile.** Every local measurement had said 0. Attribution named
the footer, and the cause is exact: the skeleton reserved a summary's worth of height while a real
passport is a document's worth, so the footer sat high during the fetch and jumped when content
arrived. Locally the fetch always returned before the shift could happen — the defect needed a
throttled connection to exist at all.

A skeleton that reserves the wrong amount of space causes the shift it exists to prevent. Both
skeletons now reserve a viewport. Re-measured on the deployed site: **0**.

### The instrument, for the third time in two phases

`benchmarkIndex` is Lighthouse's own measurement of the machine it is running on. A healthy figure
here is around 3000. Across this phase it swung between **201 and 3022**, and the performance score
tracked it exactly:

| benchmarkIndex | total blocking time | performance |
|---|---|---|
| ~210 | 7,060 – 10,810 ms | 38 – 54 |
| ~2950 | 0 ms | 95 – 100 |

Ten seconds of blocking for a 51 kB bundle is not a physical possibility; it is a starved CPU with
a 4× throttle multiplier on top. The pattern that finally made it legible: **the first run in any
batch is starved** — the cold start of Chrome and `npx` competes with the measurement it is about
to take — and every run after it is clean.

The rule that follows is cheap and should be permanent: **read `benchmarkIndex` before reading the
score, and never report a single run.** Had the first number been reported, this phase would have
recorded a performance score of 46 for a site that measures 100.

PageSpeed Insights was the intended instrument precisely because it runs on hardware that is not
this one. Its keyless API now returns a per-day quota of zero, so the fallback was repeat local
runs with the machine's own benchmark attached to each.

### Deploy configuration, verified on the response rather than the file

| path | cache-control | why |
|---|---|---|
| `/assets/*` | `max-age=31536000, immutable` | the filename carries a content hash |
| `/index.html` | `max-age=0, must-revalidate` | it is how a reader reaches any new build |
| `/data/*` | `max-age=0, must-revalidate` | a passport expires by time; one behind a long cache would show a document the issuer has already superseded |

Also live on every response: `X-Content-Type-Options: nosniff`,
`Referrer-Policy: strict-origin-when-cross-origin`.

Hash routing means no SPA rewrite rule is needed and no deep link can 404 at the edge.

### Still open

**[CLOSED] The custom domain.** `provek.dev` and `www.provek.dev` are both **active**. DNS stays
at Porkbun rather than moving to Cloudflare: an `ALIAS` record at the apex and a `CNAME` on `www`,
both pointing at `provek.pages.dev`. The apex could not take a CNAME — the record type is
forbidden at a zone apex, where NS and SOA already live — and Porkbun's `ALIAS` resolves that by
answering with an A record while following the target internally.

Certificate issued by Google Trust Services, `CN=provek.dev`, valid from 2026-08-20. No CAA record
existed to obstruct it, which was checked before the records were written rather than after the
certificate failed.

`.dev` is in the HSTS preload list, so there is no HTTP fallback at any point: before the
certificate existed the domain was simply unreachable over TLS, and `http://` was never an option
a browser would take. The footer's claim to `provek.dev` is now true.

The `rel="canonical"` tag was deliberately added only after the domain resolved. Adding it earlier
would have pointed every crawler at a host that did not answer.

**Open Graph tags.** A passport is shared by link in due-diligence email, which is the one
distribution channel this product actually has. There are no `og:` tags, so those links unfurl as
a bare URL. Deliberately deferred: they would be static across all routes on a hash-routed SPA, and
a per-passport unfurl needs prerendering.

