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

## Phase 7 — Bing Webmaster: the site is registered, ownership is NOT proven

`https://provek.dev/` is in the Bing Webmaster account and `GetUserSites` returns it with
`IsVerified: false`. That second half is the whole status: **every per-site call is refused until
ownership is proven**, so there is no sitemap submission, no URL submission and no quota reading
for this domain yet.

### What each call answered

| call | subject `provek.dev` | control `defycard.com` |
|---|---|---|
| `GetUserSites` | present, `IsVerified: false` | present, `IsVerified: true` |
| `VerifySite` | `false` — the check ran and returned a verdict | — |
| `GetUrlSubmissionQuota` | `ErrorCode 14 / NotAuthorized` | `DailyQuota 0`, `MonthlyQuota 1100` |
| `GetFeeds` | `ErrorCode 14 / NotAuthorized` | 4 feeds |
| `GetQueryStats` | `ErrorCode 14 / NotAuthorized` | **0 rows, call OK** |
| `GetLinkCounts` | `ErrorCode 14 / NotAuthorized` | **0 rows, call OK** |

The control column is not decoration. Three of these calls can answer `200` with an empty body, and
on a new site that is the truth — so a zero on the subject alone cannot be told apart from an
instrument that sees nothing here. Running each call a second time against an old, verified site
settles which it is. The quota numbers in that column are **`defycard.com`'s**, not this domain's;
this domain's quota is `unreadable` and is recorded as such rather than being filled in with the
neighbour's figure.

`GetQueryStats` returning **0 rows on a verified site with a healthy call** is the trap this
measurement was warned about, and it reproduced exactly: a zero there is a state of the source, not
a defect. `GetLinkCounts` reads 0 on that same verified site.

That second zero was worth the counter defect it exposed. The control column first read `1` there,
because the counter scored the wrapping dict rather than the `Links` array inside it — a fabricated
row in a table whose whole purpose is to prove the instrument can see. Once the subject becomes
readable, a zero on both sides now correctly reports `instrument_blind` instead of a false
`measured`.

### Why ownership cannot be proven from here

Bing accepts three proofs: an XML file at the site root, a `msvalidate.01` meta tag, or a CNAME.
The first two are publications and the third is DNS at Porkbun — and **this host can publish
neither**. It is the same missing channel that phase 6 recorded: the Pages project is direct
upload, so nothing here turns a commit into a live URL. The fourth route, importing an already
verified property from Google Search Console, only moves the same requirement: GSC verification is
itself a publication or a DNS record, behind an OAuth step that is the operator's by standing rule.

`VerifySite` returning `false` is a bare boolean and, on its own, cannot say *why* — an unpublished
file, a CNAME that does not exist and an edge that refused Bing's fetcher all collapse into it. The
verdict here rests on that boolean **together with** an independent reading: `GET
https://provek.dev/BingSiteAuth.xml` answers `404` to a browser agent. One instrument corroborates
the other; after a deploy, a lone `false` would no longer license the same conclusion.

`web/public/BingSiteAuth.xml` therefore exists but is not in force. That directory is copied into
the build verbatim — `favicon.svg` is byte-identical (698 B) in `web/public/` and at
`https://provek.dev/favicon.svg`, and a local `vite build` puts `BingSiteAuth.xml` in `dist/`
unchanged — so the file will take effect on the next deploy and not before. Until then
`https://provek.dev/BingSiteAuth.xml` answers `404`, which is recorded as `absent`, a reading taken
with a browser user agent for the reason in the next section.

The code in that file is the account-level `AuthenticationCode`, which Bing expects to be served
publicly at the site root; it is a claim of ownership, not a credential. The API key it belongs to
stays in `~/.env` and appears in no file here.

### The completion path, and who can walk it

1. operator deploys — `BingSiteAuth.xml` goes live;
2. `VerifySite` — an API call, so this step needs no browser. It is expected to turn `true`, and
   that is an expectation rather than a result: it holds only if the edge admits Bing's fetcher.
   The 403-to-non-browser-clients behaviour measured below applies to Bing's crawler as much as to
   ours, and whether verified bots are allowlisted here has **not** been measured;
3. `GetUserSites` → `IsVerified: true`, at which point the refused calls above start answering;
4. sitemap `https://provek.dev/sitemap.xml` submitted via `SubmitFeed`, then URLs, against a quota
   **read from `GetUrlSubmissionQuota`** rather than assumed.

Only step 1 needs the operator. Steps 2–4 are API calls, which is worth stating precisely because
the opposite assumption — that Bing verification needs a human in a portal — would have parked the
whole task on the operator's desk instead of on one deploy. What is *not* claimed is that the deploy
is sufficient; step 2 names the condition that has not been measured.

### The instrument, for the fourth time

The probe first read the live site with Python's default user agent and got `403` on **every** path
including the homepage, where a browser agent gets `200`. That `403` was one step from being
written into the log beside "verification file not published" — a statement about the site, built
out of a refusal aimed at the client. It is L-10's shape in a new costume, produced by an instrument
written *that same hour* to honour L-10. The fix is a browser user agent and a three-state verdict
where `absent` is reserved for `404` alone; `403` and `5xx` are `unreadable`.

Review then found the *same law* broken twice more inside the instrument written to honour it, which
is the part worth keeping:

- the live fetch read the first 4096 bytes and ruled on them. The homepage is ~16 kB with `</head>`
  at ~5 kB, so a `msvalidate.01` tag — which belongs at the end of `head` — sat outside the window,
  and `served_without_code` would have been a verdict about a page from a slice that could not have
  contained the answer. Today's reading was accidentally right, which L-10 calls the dangerous kind.
  The body is now read whole, and truncation is its own state rather than a silent absence;
- the row counter returned `1` for any payload that was not a list. `GetLinkCounts` answers with a
  dict wrapping a `Links` array, so an empty result scored `1`: the control could never read zero,
  the `instrument_blind` state was unreachable, and an empty subject would have published as
  `measured`. A counter that cannot return zero is not a counter. Shapes it cannot count are now
  `uncountable_shape`, which is neither zero nor one.

Three instances of one law in one file, none of them caught by the author. The transferable part is
not "set a user agent" but: **before recording an absence, establish that the instrument could have
seen a presence.**

The state capture lives outside this repository, at `~/orchestra/logs/bing_state.json`, written by
`~/orchestra/bing_probe.py`. It is outside deliberately: every `*.py` under `scripts/` must be bound
to an `ABI-*` requirement, and a Bing client answers to none of them. Binding one to get it past the
gate would be the rubber-stamp that ratchet exists to catch.

