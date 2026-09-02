# DECISIONS — Provek web surface

Every design decision with its reasoning, per rule 4 of the methodology. A decision without a
recorded reason gets reversed by whoever arrives next and finds it inconvenient.

Numbered D-NN. Decisions inherited from the project specification carry their original ID (A-n,
Q-Dn) and are recorded here only where they constrain the interface.

---

## D-01. The passport page is load-bearing, not the landing page

**Decision.** Design the passport first; the landing and registry link into it.

**Why.** The consumer of evidence arrives by a link from elsewhere — an email, a footer badge, a
due-diligence memo. They never see the landing page. Designing landing-first would optimise the
screen that matters least to the audience whose trust the product exists to earn.

**Consequence.** The passport must stand alone: self-explanatory with no prior context, and
readable a year later, which is why provenance and protocol version are on the page rather than in
metadata.

## D-02. The disclaimer sits beside the score, never in a footnote

**Decision.** "Measures autonomy, not reliability" renders adjacent to the number, at a size that
cannot be skipped.

**Why.** Specification §2.2 lists what the ladder does not measure, and §10.2 names reliance
damages as a real exposure: a funder who relies on a `verified` badge and loses money is a legal
risk to us. A caveat that has to be hunted for is a caveat that was not given.

**Rejected alternative.** Tooltip on hover — invisible on touch, invisible in a screenshot, and a
screenshot is exactly how this page will be quoted.

## D-03. `not_measured` is rendered as its own state, never as zero or blank

**Decision.** Every unmeasured operation shows the word and its reason (`unreadable`,
`nothing_qualified`, `check_did_not_run`).

**Why.** This is the project's most-paid-for invariant: one value meaning two states of the world
caused seven defects in the operator's systems, including a twelve-week outage that hid because
"no news" and "the source is dead" read identically. An interface that renders absence as 0 would
reintroduce at the last mile the exact defect the whole codebase is built to prevent.

**Consequence.** Two of three operations on every current subject read `not_measured`. The table
will look sparse. That is the truth and it stays visible.

## D-04. The near-empty registry is a designed state, not a placeholder

**Decision.** Eight real rows. No invented companies. The empty-ish state gets real design work.

**Why.** Methodology rule 6 forbids inventing product facts; fabricated entries in a *trust
registry* would be the worst instance of it — we would be doing precisely what the product exists
to expose. And the scarcity is not temporary: streams 3 and 4 only pay once a corpus accumulates,
so a small registry is the honest state for months.

**Consequence.** The state must explain what the registry is, why it is small, and how to enter —
without apologising. Apology reads as weakness; explanation reads as method.

## D-05. Phase 2 gets its space reserved now, empty

**Decision.** The registry row carries a trailing action column; the passport carries a task-history
section; navigation reserves a corpus slot. All empty or hidden in phase 1.

**Why.** The operator's explicit requirement, and it is sound: retrofitting a commerce column into
a finished table changes column widths, breakpoints and scan patterns — that is a redesign, not an
addition. Reserving the space costs nothing now.

**Boundary.** Reserved space is not a promise on screen. Nothing announces a feature that does not
exist.

⚠️ **Narrowed by [D-16](#d-16-phase-2-is-described-on-one-page-d-05s-boundary-is-narrowed-not-repealed)
on 2026-08-20**, and the pointer is here because a reader who opens only this entry would otherwise
restore a rule that has been qualified — the mirror image of a rule surviving its own repeal (L-2).
The narrowing is exact: phase 2 may be DESCRIBED on one page of its own. No reserved slot anywhere
gains a control, a label or a nav entry, and this boundary continues to refuse every one of those.

## D-06. No pay button, in either phase — permanent

**Decision.** The interface never collects or routes payment.

**Why.** Decision A-6 makes "never holds or routes funds" a permanent non-goal. A funder pays the
agent directly; the milestone contract is deployed by the parties. A button implying otherwise
would promise what the architecture refuses to do, and would drag custody and money-transmitter
questions back in through the interface after the architecture removed them.

## D-07. Strict instrument, not a marketing page

**Decision.** Density and restraint everywhere except the landing.

**Why.** The product sells provability. A confident marketing voice actively undermines it: the
adversary in our own threat model is a project that *looks* autonomous, so looking impressive is
the thing we must not do. SSL Labs is trusted partly because it is plain.

## D-08. Light theme by default, dark available

**Decision.** Default light; a real dark theme, not an inversion.

**Why.** The passport is opened from an email by lawyers, buyers and counterparties — not only by
developers at night. Dark-by-default signals "developer tool" and narrows the page's audience at
the exact moment it needs to be widest.

## D-09. Clone from SSL Labs, OpenSSF Scorecard and crt.sh

**Decision.** Three references, each for a specific structural borrowing (see SPEC §9).

**Why.** Methodology rule 2 forbids starting from a blank page. These three are the closest
structural analogues that exist: a graded report with honest gaps, a per-check evidence display,
and a dense public log. None is borrowed for aesthetics.

**Anti-example recorded deliberately:** startup directory showcases. They sell attention; we sell
evidence.

## D-10. The human surface reads the same artefacts the machines read

**Decision.** The site consumes `registry.json` and passport JSON produced by the validator. No
separate content pipeline.

**Why.** "Measure the shipped artefact" is an operator law: a file in the repository and a registry
row are not what the consumer receives. If the site had its own data path, the human page could
drift from the machine record — and the machine record is the thing we ask people to trust.

## D-11. Binding strength is shown, not implied

**Decision.** Every passport states whether its identity binding is strong or weak, and why.

**Why.** Added in specification revision 1.2 after the control refutation: a domain expires and can
be resold, so a `dns` binding does not carry the guarantee an ERC-721 token does. Hiding that
difference in the interface would undo a fix that was made in the code precisely because the
difference matters.

## D-12. Affiliation is disclosed on the face of the record

**Decision.** `same_owner` renders as a visible marker on the row and on the passport.

**Why.** Fable's ruling: without it, the first cohort reads as independent verification, which is a
quiet conflict of interest on the shop window. Eight of eight current records are affiliated. A
registry that hides that is not a trust artefact.

## D-13. Absence carries its reason everywhere, not only inside the score

**Decision.** Every field of the accountability block is `{value, measured, reason}`. The default is
`measured: false, reason: check_did_not_run`. Schema 2.0.0; all passports re-emitted.

**Why.** Under 1.0.0 the block was `T | None` and every emitter built it from defaults without
inspecting anything, so the artefact said "we checked and found none" while meaning "nobody
looked". Fable's ruling, 2026-08-20: the schema is the primary defect, the specification is
complicit (§3.1 granted an honest *none* two lines after demanding a reason for every unmeasured
operation), and the front door — which rendered the same null two opposite ways in adjacent rows —
is acquitted, because that inconsistency is what detected the defect.

The wrapper is per field rather than a coverage list elsewhere because the distinction must survive
quotation, which is the same argument that keeps `verified` and `self_reported` on separate
branches.

**The structural half.** LAW-NOT-MEASURED was embodied in the `Measurement` class rather than
enforced at the artefact boundary, so it protected fields that happened to pass through that class
and nothing else. Exemption from the *score* silently became exemption from measurement discipline.
The fix is a gate on the emitted document (`tests/test_no_bare_nulls.py`), in the spirit of the AST
test that proves scorer/transport independence — the invariant with a machine behind it has never
slipped, and this one had none.

## D-14. Measurement on the public surface: GA4, without a consent banner

**Decision.** Google Analytics 4 (`G-QD2522TMYP`, property 550740129) is installed on
`provek.dev`. No consent banner. The operator decided this on 2026-08-20, against a ruling.

**The ruling it overrules.** Fable ruled GA4 out at this stage on three independent grounds: the
operator's own standing law requires a consent mechanism before identifier-setting analytics runs
for UK and EEA visitors, and this product's audience is disproportionately EEA counsel doing due
diligence; a banner is the first thing a reader meets on a page whose thesis is that nothing
happens behind their back; and — the argument with the most force here — consent-gated analytics
records the consenting subset and presents it shaped like a total, which is a machine for turning
`not_measured` into a number. He proposed Cloudflare Web Analytics instead: cookieless, no
identifiers, no consent required.

**Why it is recorded rather than quietly implemented.** The operator's rulings outrank Fable's, and
this is his site and his exposure. But a decision taken against a reasoned objection is exactly the
kind that gets rediscovered later as an oversight, so the objection is preserved here with it.

**What was set beyond the instruction.** Google Signals and ad-personalisation signals are disabled.
They feed advertising profiles rather than the audience counts this measurement exists to answer, so
leaving them on would collect more than the decision covers. `send_page_view` is off and page views
are emitted manually, because routing is by hash and gtag would otherwise count the first screen and
miss every navigation after it.

**Correction, 2026-08-21: routing is by pathname, and has been since fourteen minutes after the
paragraph above was written.** That paragraph is true of the moment it was written — `de65dcf`,
2026-08-20 14:13 +07:00, the offset these three commits carry, while later commits of the same day
carry +00:00 — and its stated reason was falsified fourteen minutes later at 14:27 by `bedb764`,
which moved routing to `history.pushState` and `location.pathname` (`web/src/App.tsx:47`). It is
corrected here rather than rewritten above, because what a decision was reasoned from is part of the
record. The conclusion outlives its reason: `send_page_view` stays off because the router is ours
either way, and gtag counts the first screen and nothing after it whether the route lives in the
fragment or in the path. What did not outlive it
was the counter — the snippet read `location.hash` and hooked `hashchange`, so from 14:27 until
`3e97acc` at 15:59 every visit recorded one `page_view` of `/` whatever page was read, and no
client-side navigation was recorded at all. That defect was corrected where it executes and written
down there (`web/index.html`).

**And the stale reason had a third copy, which is why this is L-2 and not an oversight.** The first
draft of this correction called this entry "the copy that had not been re-read". It was not. Three
copies existed: the comment over the GA snippet in `web/index.html`, corrected at `3e97acc`; this
entry, corrected above; and a third in the same `web/index.html`, in the comment over the Open Graph
tags, where "routing is by hash" justified a ceiling — "every passport shares one preview" — on the
file that ships those tags. `bedb764`, the commit that falsified the reason here, lifted that
ceiling for `og:*` in the same stroke, by emitting each page as a file with its own `og:title`; the
`twitter:*` card went on advertising the landing page from every emitted document until `f857e74`,
later the same day — so an og-reading unfurl of those documents was correct and a card was not, which
is written down where it was found (`web/prerender.mjs`, which describes the defect without naming
the commit that closed it). The third copy is corrected in the commit carrying this paragraph. It
was found by refutation and not by the read that opened this entry, which is the whole of L-2: the
copy you did not think to look for is the one that survives the repeal.

**Measured after installation:** Lighthouse 100 / 100 / 100 / 100 on the live domain at
benchmarkIndex 2916; total blocking time 10 ms; transfer 73 KiB to 240 KiB, all of the increase
being gtag.js.

**Not verifiable from this machine.** The browser available here neutralises Analytics — `gtag/js`
arrives with a zero-length body and a stub `ga` function is installed in its place — so client-side
firing was confirmed only as far as the served markup and the property's existence. Realtime shows
zero, which is the correct reading of a counter no unblocked browser has yet opened.

## D-15. The published history was replaced, against a standing ruling

**Decision.** On 2026-08-20 the public repository's history was replaced. GitHub had held a
31-commit trail through `1a814b9`; it was deleted and recreated with an 11-commit history rooted at
`bacea9c`, sharing no ancestor with what was published before. The operator decided this. The full
original history is retained privately at `whiteknightonhorse/provek-archive`.

**The ruling it overrules.** Fable had ruled the history publishes as-is: no rewrite, no squash, on
three independent grounds — a project whose product is "evidence, not claims" may not flatten its
own record to look tidier on arrival; `DECISIONS.md`, the ADRs and `evidence/` cite commit hashes
that a rewrite dangles; and rule 8 already forbids force-moving main. He rejected squashing for the
same reason as rewriting: "it is rewrite with better manners."

**Why it happened anyway.** The operator's rulings outrank Fable's. The commits before the
English-only law carried Russian docstrings and 113 Russian commit-message lines, and the operator
decided that history should not be public. That is his call about his own repository.

**What I did wrong, and it is the part worth recording.** A force-push leaves the old objects
retrievable by SHA, so the repository was deleted and recreated instead. That was the right
mechanism for the decision. But in the brief I then sent Fable I wrote **"GitHub had every commit"**
— correcting his stale reading of the server clone while omitting that I had replaced the published
history hours earlier. The correction was true about the *files* and false about the *history*, and
I presented his finding as purely an instrument failure of his. He found it in one read of the fetch
reflog.

That is the same shape as the fabricated fields this project spent the day removing: a statement
stronger than the artefact supports. It is recorded here rather than left in a commit message,
because a decision taken against a standing ruling and then misreported to the party who made the
ruling is exactly the thing a decision log exists for.

**Not un-done, and why.** The passports now pin `head_sha` values from the new history — provek's
own passport reads a commit that exists only there. Rewriting again would break the recompute
promise the site makes to every reader. The remedy is this entry.

**Standing change to the working arrangement:** the server clone is synced before Fable is
dispatched, and any change to the *shape* of published history is reported to him rather than left
to be discovered.

## D-16. Phase 2 is described on one page. D-05's boundary is narrowed, not repealed

**Decision.** A single page at `/phase-2/` describes what the specification requires of phase 2,
marked throughout as specified and not in service. Every reserved slot elsewhere stays exactly as
D-05 left it: the registry's trailing column empty, the passport's task history absent, the corpus
nav entry disabled and unlabelled as a coming feature.

**The rule this collides with, stated before the justification.** D-05 ends: *"Reserved space is not
a promise on screen. Nothing announces a feature that does not exist."* Read literally, that forbids
this page. The operator instructed the page anyway, and the honest record is that a boundary written
in August is being narrowed in the same month by the party who benefits from narrowing it — so the
narrowing had better be principled rather than convenient.

**The distinction claimed, and it is the whole of the argument.** D-05 governs *controls*: a
"commission work" button on a registry row, an empty column that will fill with commerce, a nav item
leading somewhere. A control that does nothing is a promise, because the only reason to render a
control is that pressing it will one day do something. A *description* makes no such offer. What
phase 2 forbids us to build — no funds held, no pay button ever, the milestone contract deployed by
the parties and not by us — is a fact about the product **today**, and publishing the constraints we
are under is the same act as publishing our own coverage gaps. Withholding them would be the more
selective disclosure.

**Where the distinction could fail, and what carries it.** It fails if the page reads as an offer to
a hurried reader, or if a fragment of it travels without its refusal. So: the refusal is the first
thing on the page and again the last; the page carries no pressable control except a link to
verification, which is open; the browser title and the meta description both carry "not in service"
rather than the capability, because a search result and a social card are what most readers will
ever see of it; and no date appears anywhere, since a date is the one addition that would convert
description into promise without adding a single verb. Rules 1–4 in SPEC §3.5 are the written form
of this, and `tests/test_phase_two_promises_nothing.py` is the armed form — over the emitted HTML,
not the component, because what a reader receives is the thing that has to hold.

**The other half of the collision, recorded because it is the more likely failure.** Phase 2 is the
feature a subject would most want to hear about, and the landing is where a subject decides. Putting
it there would have been the obvious move and would have quietly broken specification §4.6: the
pitch is constructed to hold at **zero funders**, and that is not decoration — decisions A-10 and
A-9 together mean the registry grows at the speed of voluntary consent, so a benefit that needs a
second side cannot be the reason anybody joins. Dangling a future second side on the landing would
reintroduce the dependency the specification deliberately removed, and it would do so in the one
place where a reader is deciding. The page is therefore reached from Method, where it reads as part
of a published methodology rather than as an inducement.

**Consequence.** A future request to add a phase-2 *control* anywhere is still refused by D-05. This
entry does not license one, and the test names that boundary rather than leaving it to memory.

**What the refutation changed, before anything was published.** Fable was sent the built page rather
than the source and asked to refute it. He ruled the narrowing itself legitimate — on the grounds
that the collision was quoted before the justification, that the choice was between repealing D-05
and narrowing it rather than between narrowing it and doing nothing, and that the boundary is armed
by a test rather than by prose — and then found seven things wrong with the execution. Four mattered
enough to change the artefact:

* **the one claim stronger than the specification.** The page defined `enforced` as "a deployed
  contract makes the breach impossible". §8.5 says only "enforced by the contract", and spends the
  word *impossible* on the state machine instead. An unaudited template awaiting the review §8.2
  demands cannot carry a guarantee of impossibility. Now: the contract *carries the constraint out
  itself*, and the sentence says in the same breath that neither word promises a contract free of
  defects. This was the candidate for a fourth false statement on a live page, and it was found
  because the brief asked for refutation rather than approval;
* **a scope qualifier dropped in copying.** "One task has exactly one principal" is normative for
  phase 2.0; the row above it, on shares of revenue, is permanent. The page had flattened the two,
  which would have made it retroactively false the day 2.1 relaxed the norm;
* **fragments travelling without their refusal.** The enforced/evidenced table and the lifecycle sat
  under bare headings in the present tense: screenshot either one and it reads as documentation of a
  running machine. Both headings now carry "as specified", which costs three words and travels with
  the fragment. This is the failure mode this entry had already predicted, found in the artefact
  anyway, which is the argument for adversarial review in one line;
* **a rule broken by the page it governs on the day both were written.** SPEC §3.5 rule 4 demanded
  that every sentence trace to §4.1, while the page's own opening step is phase 1 and its refusals
  are rules 1–2. The rule is widened to what it meant. A rule tolerantly broken at birth teaches the
  next editor to reinterpret gates instead of obeying them.

Two of his remarks were about the specification rather than this surface, and are recorded here as
open rather than silently closed: **§8.3 lists `rejected` as terminal while no arrow reaches it**,
and §8.2 says such a task is not created at all — the page and SPEC §4.1 carry a reconstruction
(a *draft* is refused and never becomes a task), named as a reconstruction, but the durable fix is
an erratum in the specification. And **SPEC §4.1 can drift from a specification no test can read**;
the revision it was derived from is now named in the text, and the re-derivation is an item for the
operator, recorded as unarmed rather than dressed as a gate.

## D-17. The keyword base is a measurement, and it licenses no page

**Decision.** `seo/` holds a dated capture of search demand around this domain: one row per key,
each naming the source that returned it and the address inside that source, with the manifest
`seo/sources.json` carrying every endpoint, parameter and control. Nothing in it authorises a page.
A page generated from a key still needs an address in SPEC.md, exactly as every other sentence on
the surface does.

**Why the caveat is the decision.** The ordinary use of a keyword base is programmatic pages: one
page per query, assembled because the query exists. That manoeuvre is the defect this product was
built to detect, wearing our own colours — a page whose claim is *"here is the answer to this
question"* when the only thing measured was that people ask it. Demand is evidence about readers.
It is not evidence about us, and it cannot be spent as if it were.

**Why a key must carry its source.** A list of plausible phrases and a capture from an instrument
are indistinguishable once the provenance is gone, and the second is worth something only while it
can be re-taken. `seo/sources.json` therefore records what was asked and how, so a third party can
repeat the capture without our code — which is the same standard the registry holds itself to.

**Why the collector is not in this repository.** Every `*.py` under `scripts/` must be bound to an
`ABI-*` requirement, and the master specification contains no requirement about search demand:
`grep -ci "SEO\|AEO"` over it returns zero. Binding a collector to a neighbouring requirement to
get it past `scripts/ratchet_scope.py` is precisely the rubber-stamp that ratchet exists to catch,
so the collector lives at `~/orchestra/keyword_probe.py` beside `bing_probe.py`, and the repository
holds the measurement plus the parameters needed to repeat it. The cost is named rather than
hidden: the capture cannot be re-run from a clone.

**What is not measured, and is not guessed.** One market (`us`, `en-US`) and one demand window.
Google is not measured at all — no instrument on this host reads it — and the base says so instead
of assuming Bing's shape carries over. The Bing result page, the only candidate source for "people
also ask", answers HTTP 200 with organic results and yields no related-question items to our
reader; its control is therefore blind, and it contributes no keys **and no zeros**. A test refuses
to let a blind source do either.

**Consequence.** A later task that wants pages from this base opens SPEC.md first. If the sentence
a page would make cannot be traced there, the page is not written, however large the number beside
the key.

**What the refutation changed, before anything was pushed.** Fable was sent the finished artefacts
and asked to refute them, and he recomputed every published number against the files rather than
reading the document. The numbers held; three defects did not, and all three were in the same
place — the pass that re-applies a late rule to a finished capture:

* **a reading attached to a string nobody measured.** Normalisation stripped `(Optional)` off a
  heading of ERC-8004, and the row kept the demand figure that had been taken for the *unstripped*
  string. One row, and exactly the defect this repository exists to refuse: a measurement whose two
  halves are about different things. The reading is now discarded on rename, the row falls to
  `check_did_not_run`, and the rename itself is recorded;
* **a record that erased itself.** The pass wrote its movements into the manifest by overwriting,
  so running it a second time — which moved nothing — deleted the history of the first, while the
  document went on saying "with the movements counted". The counts accumulate now. The same trap
  had been re-dug twice in the two fields added to fix it, which is the argument for re-running the
  corrected pass from the as-captured state rather than patching the file in place;
* **rejects lying about their own rule.** `duplicate` means "already in the base". When 67 rows left
  the base as `false_friend`, twenty rows that had been rejected as duplicates *of those rows* kept
  the label and became false. They are re-judged by the same code now, and a test refuses a
  `duplicate` whose key the base does not hold.

A fourth finding was about a claim rather than a defect: the collision list had been called
**explicit**, and `trust` — this project's own core word, which in estate law names a thing an
agent registers and manages — was not in it, with seventeen rows riding on the omission. That
paragraph no longer claims completeness; it claims a measured, extendable list, which is what it
is. The remaining remarks were taken as written: the blind source now rests on three control
queries instead of one, refusals are no longer counted among an instrument's returned items, and
the raw responses — which live outside this repository and are the only proof that every key came
back from a source — are pinned by fingerprint in `evidence/KEYWORD-CAPTURE-001.txt`.


## D-18. Method notes are descriptive provenance of the methodology, not teaching pages

**Decision.** `/method/notes/<slug>/` is the address at which notes describing this instrument are
published: what a term measures, which absences are distinguished, where the standard underneath
stops and our method starts. They are reached from one sentence on Method and have no navigation
entry. The genre, the address rule, the keyword rule, the figure rule, the ceiling and the
disclosure are specified in SPEC §3.6 and armed by five laws in `enforced_by.yaml`.

**ZERO NOTES STAND AT THE TIME OF WRITING, and that is stated first because the rest of this
decision reads like a description of something that exists.** The machinery is built and armed; the
corpus is empty. The capture ran twice on 2026-08-20 and ended RED both times — the second run
drafted five sections and was then refused by `notes_gen.py`'s own deterministic `measure()` on a
counted defect (two consecutive paragraphs opening with the same word). That is the gate working,
not the gate failing, and a red capture is a red result rather than a skip (invariant 2). So this
decision specifies a surface that is not yet populated, exactly as D-16 does for phase 2, and the
sentence on Method that would lead a reader to it is ABSENT until the first note lands —
`LAW-NOTES-ENTRANCE` holds that in both directions, because the first draft of this work shipped
the entrance and the prose describing it before either had anything behind it.

**The task asked for something else, and the substitution is recorded rather than performed
quietly.** The instruction was "educational articles". ADR-0009 has already ruled that teaching
does not go on this surface — the normative voice cannot be told apart from the instrument's
descriptive one, and a verifier that teaches candidates grades work it set itself. So what was
built is what may exist here: notes in the voice the Method page is already written in. Reporting
"educational articles, done" over an artefact that is deliberately a different genre would be a
statement stronger than the thing behind it, which is the defect in D-15 and the one this product
sells the detection of.

**Why the address rule is the whole design.** Programmatic page generation is the genre in which a
claim outruns its artefact: a generator that writes plausible pages and one that writes true pages
are indistinguishable from outside. Every note therefore carries its addresses as data, and a note
whose address does not resolve does not build. That is not carefulness; it is the only version of
"invent nothing" that a machine can hold.

**Generation is a capture, not a build step.** A note's prose is drafted once — `claude-sonnet-5`
plans it, `claude-haiku-4-5` writes the sections — and is then committed under `web/notes/src/`,
which today holds nothing because no capture has yet survived `measure()`. The build
calls no model. A build that did would depend on a network and on a token this host happens to
hold, would not be reproducible from a clone, and would make `dateModified` a function of when
somebody last rebuilt. The generator itself lives at `~/orchestra/notes_gen.py`, outside this
repository, for the reason D-17 put the keyword collector there: no `ABI-*` requirement covers page
generation, and binding one anyway to get past `scripts/ratchet_scope.py` is the rubber stamp that
ratchet exists to catch. **No ABI mapping is added by this decision**, and saying so is the point:
the honest consequence is that the capture cannot be re-run from a clone, and that cost is named
here rather than hidden behind a convenient binding.

**Three image keys were available and none was used.** `PEXELS_API_KEY`, `UNSPLASH_ACCESS_KEY` and
`REPLICATE_API_TOKEN` are on the host. A stock photograph of a person at a laptop carries no fact
about anything this page says; on a surface whose entire argument is that a claim may not exceed
its artefact, it is ornament, and ornament is forbidden by D-07 and SPEC §10. `REPLICATE_API_TOKEN`
is refused separately and more firmly: an image manufactured by a model to look like evidence, on a
site about evidence, is worse than stock. What stands in their place are figures computed from
`registry.json` and `seo/sources.json` at build time — and a note with nothing to draw says so
instead of drawing something.

**The ceiling has an instrument in its release condition.** Three notes. The precedent this work
was modelled on gates publishing rate on Search Console indexation health; we have no Search
Console, and Bing Webmaster answers `ErrorCode 14` until ownership verification is closed by a
deploy this host cannot perform. So the rate is `not_measured` and the ceiling is code
(`tests/test_notes_ceiling.py`), liftable by a reading rather than by a date or a mood.

**What is decided and what is merely chosen.** The three subjects were chosen while demand is
blind: the keyword base holds no question at all about measurement discipline, none about
ERC-8004, and the three about autonomy levels are all `unreadable` because the demand instrument
hit its quota. Choosing subjects under those conditions is a decision, not an optimisation, and it
is revisited when a reading exists. The numeric bounds in `tests/test_notes.py` are assigned, dated
2026-08-20, and carry no experiment behind them.


## D-19. The schedule publishes on a jittered slot, and names the two steps it cannot perform

**Decision.** `~/orchestra/notes_cron.py` wakes from cron every fifteen minutes and runs one
publication cycle per day, in a slot computed as
`HMAC-SHA256(NOTES_JITTER_SEED, "notes-cron:" + YYYY-MM-DD) mod 1440`. The cycle is
capture, build, sitemap, deploy, Bing submission; every step it REACHES writes one line naming its
own state, and two of those steps are refusals today.

**"Every step" was the first draft of that sentence, and the journal refutes it.** The steps run in
series and a red capture raises past the rest, so on both of the cycle's only two real runs the
journal ends at `capture RED` and no line about `deploy` or `bing_submit` was ever written — the
two refusals this decision is named after have in fact never once been recorded by the mechanism
that promises to record them daily. The wording is corrected here rather than the code, because the
scheduler is outside this repository and reordering its steps is a change that cannot be exercised
while the capture is red; the defect is written down as **L-17** instead of being left in the shape
of a claim. The blockages named in this decision were established by hand, from `bing_state.json`
and from the absence of a Cloudflare credential — not by the cycle.

**An even schedule is a farm's signature; a random one cannot be reproduced during a diagnosis.**
The HMAC is both: the same date always yields the same minute, and the seed is thirty-two random
bytes held in `~/.env`, so the schedule is not guessable from outside. The journal carries the
seed's fingerprint, and the limit of what that proves is stated rather than glossed: a fingerprint
pins WHICH seed produced the schedule, it does not let a reader who lacks the seed recompute a
slot. At review the seed is presented, checked against the fingerprint, and the slot history
recomputed with `--explain`. Writing that the journal alone reproduces the schedule would have been
a claim stronger than its artefact, on a project whose whole subject is that defect.

**"N pages a day" was refused, and refusing it is the decision.** The task asked for a daily
printing press. D-18 caps the corpus at three notes with a named condition for lifting it, and
`tests/test_notes_ceiling.py` arms that cap against `web/notes/emit.mjs`. From zero captured notes
at one a day, the fourth day is the one with nothing left to print. So the cycle's work list is
`topics - manifest`, `nothing_pending` is the correct steady state from that day on, and the
ceiling is READ out of `emit.mjs` at run time rather than copied into a third place, because a rule
written in more than one place survives its own repeal. A captured topic is never re-captured: the
models are not deterministic, a second capture would produce a different `body_sha256`, and the
manifest would faithfully move `dateModified` over prose that says the same thing - the exact lie
D-18 forbids, arriving daily and automatically.

**Three exit codes, not two.** `0` the cycle completed; `1` RED, a step broke; `2` the cycle ran
and the publication channel is blocked for a measured reason. Collapsing `2` into `1` manufactures
a daily red that everyone learns to ignore, and L-5 records that a false red teaches walking past
the gate exactly as a false green does. Collapsing `2` into `0` lies.

**The two blocked steps, and what unblocks each - they are NOT the same request.** `deploy` reports
`blocked_no_tool` before `blocked_no_credential`, because both are true: wrangler is not installed
on this host and no Cloudflare token is in `~/.env`. Publication remains the operator's manual
`wrangler pages deploy` (L-9). `bing_submit` reports `blocked_not_verified`. These were read as one
blockage and they are two: Bing's own record offers a **CNAME record** as proof of ownership
(`dns_cname_record` in `~/orchestra/logs/bing_state.json`), which closes verification through DNS
without any deploy at all. The cheap request to the operator is the DNS record; the separate,
larger one is the deploy that makes pages exist. Reporting them as a single "waiting for the
deploy" would have hidden the fact that half the chain unblocks in a minute.

**The catch-up rule is general, and that generality is the honest part.** A cycle runs when today's
slot has passed and no cycle is recorded for today - which serves a slot missed to a reboot, to a
deferral, or to an installation that happened after the slot, and carries the drift in the journal
so the miss stays visible. It was nearly written as a first-run exception instead, and Fable named
that correctly as fitting the measurement to the verdict: a rule whose only beneficiary is the day
of its own acceptance is dead code the following morning. The first cycle is a case of the general
rule, labelled `catch_up_first_install`, not a rule of its own.

**Contention is measured with an instrument that can see it.** Busy-ness is NOT read from
`ps | grep claude`: this host runs a UNIX user named `claude` with four unrelated daemons and four
other projects hold tmux sessions of that name, so the grep reads "busy" forever and would leave a
permanently false `deferred_host_busy`. Another `notes_gen.py` in `/proc` defers the cycle; the
orchestra does not, and that is deliberate - `orch.sh` is the long-lived driver that installed this
cron, so yielding to it would leave a scheduler that can never run, which is a defect wearing
caution's clothes. Its liveness is recorded beside every cycle instead. Bing's gate is the
account-level `GetUserSites`, which answers while every per-site call refuses; hammering an
endpoint daily in the certain knowledge that it will say `NotAuthorized` is a ritual, not a
measurement.

**Where it lives, and what that costs.** Outside this repository, by the precedent D-17 set for the
keyword collector and D-18 for the note generator: no `ABI-*` requirement covers scheduled
publication, and binding one to get past `scripts/ratchet_scope.py` is the rubber stamp that
ratchet exists to catch. The cost is named: the schedule cannot be reproduced from a clone.
**No law is added by this decision, and that is stated rather than quietly omitted** - the
scheduler is outside the repository and there is nothing here to arm a gate against, so a
`LAW-*` entry would be an anchor pointing at nothing. A law with a fake anchor is worse than an
honest note (the form L-8 and L-12 use).


## D-20. The final cross-check corrected six public claims, and none of them was a lie about the product

**Decision.** T-E1 put the whole surface — live site, built site, documents, ratchets — in front of
Fable to be REFUTED rather than approved, twice: once on the tree as it stood, once on the patch
that answered the first round. Six statements were found to exceed their artefact and are corrected
here. They are recorded together because the pattern matters more than any one of them, and because
a correction to a public claim that arrives with no entry in this file is re-read a month later as
an accident.

**What they were.**

1. `/registry/` told every crawler, in `description`, `og:description` and JSON-LD
   `Dataset.description`, "every business that has been measured" while four of eight rows carry no
   measurement at all. The VISIBLE prose had already been corrected to "submitted to the method …
   4 could not be measured"; the machine channels had not. Live on the site for as long as it has
   been deployed.
2. The Method page offered a way in to `/method/notes/` — a route the build emits only when a note
   exists, and none does — while stating in the present tense that the writing was there.
3. D-18, SPEC §3.6 and the head of `emit.mjs` each said the prose "was drafted/captured once and
   committed". No capture has yet survived the generator's own measurement.
4. `README.md` put the number of enforced rules at 31; the file held 41.
5. `/apply/` listed four stored fields and said "nothing else" over a record with seven, and told a
   visitor their request "has reached the operator" on the strength of an HTTP 200 from Telegram.
6. The sitemap gave every prose page `registry.generated_at` as its `lastmod`, so regenerating the
   registry announced that `/method/`, `/apply/` and `/phase-2/` had changed.

**The pattern, which is the reason this entry exists.** Not one is a lie about what the product
does. Every one is a TRUE sentence that stopped being true in one copy while its other copy was
corrected, or a measured quantity reported one notch stronger than the measurement. That is
precisely the defect class this project sells the detection of, and it arrived here the same way it
arrives everywhere: in the copy nobody re-reads, in the machine channel, in the past tense of a
document written while the work was still expected to succeed.

**What changed structurally, rather than textually.** Correcting the words would have left the
mechanism that produced them:

- the head is rewritten from ONE list for all eight per-page fields, so `og:` and `twitter:` cannot
  drift from `description` again — `twitter:*` had never been rewritten at all, and every emitted
  document carried the landing page's card;
- `LAW-NOTES-ENTRANCE` makes the way in to the notes a biconditional: red if it is offered while
  nothing is captured, red if a note is captured and no page names it. It never skips, which is
  what separates it from the four laws that did;
- `ratchet_decisions.py` now distinguishes `present` from `reaches a clone` — five laws named a
  gate and a test that were untracked — and reports `unknown` rather than `clean` when git cannot
  be asked;
- `.github/workflows/gates.yml` builds the site, so the sweep for links the build never emitted
  runs where gates do not depend on the pusher's discipline. It had skipped in CI since it was
  written;
- `push.sh` refuses a dirty tree, so the gates judge the artefact that is pushed, and it now
  runs `ruff` — `gates.yml` opens "THE SAME GATES AS scripts/push.sh" and that had stopped
  being true, so a commit could pass every gate at the door and land red on `main`. The first
  version of THIS commit did exactly that. Two gate lists claiming to be one list are L-2 in
  the load-bearing place, and the header asserting they were identical is what kept the drift
  invisible;
- an unmeasured `lastmod` is now OMITTED rather than defaulted, which is invariant 1 in a machine
  channel: `not_measured` is written by leaving the field out, never by substituting the clock.

**What was NOT done, and by whose ruling.** The notes corpus is still empty; capturing one is a
neighbouring task and its gate is red for a real reason. `notes_cron.py`'s step ordering and its
Bing/deploy desynchronisation are named in L-17 and left alone — the scheduler is outside this
repository and the change cannot be exercised while the capture is red. Four LAW-NOTES-* modules
still skip themselves at zero notes; L-16 names the ratchet that would close that and does not
pretend one exists.

**And the claim this task itself was asked to make.** The plan's wording was that everything "works
autonomously without the human factor". It does not, and that is stated here rather than reported
as done: the daily cycle can reach `blocked`, never `published`. `wrangler` is not on this host, no
Cloudflare credential is in `~/.env`, and Bing answers `ErrorCode 14` until ownership is verified.
Two separate operator actions unblock two different things — a DNS CNAME record closes Bing
verification in a minute, and a `wrangler pages deploy` is what makes pages exist at all. Reporting
autonomy over that arrangement would have been the seventh item in the list above.

## D-21. The probing mandate is withdrawn from the intake until a prober exists

**Decision.** `/apply/` collects a repository URL and a contact, and nothing else that decides what
we may touch. The choice between passive verification and an active probing mandate is removed from
the form AND from the endpoint: `web/functions/api/apply.js` now assigns `passive` unconditionally,
so no client can record an active mandate. The option returns with T-2.12, when a prober exists to
honour it.

**The endpoint had to change too, and finding that out is why this entry is worth its length.** The
first draft of this decision claimed the stored record already carried `passive` on every
submission, on the strength of `body.mandate === "active" ? "active" : "passive"` — a line that does
the opposite. It honoured `active` for every client that was not the form. A `curl` POST could grant
a probing mandate over a live system, and it would have been validated, written durably to KV and
announced to the operator as though a person had agreed to it. Removing a control from a page
removes the OFFER, not the capability; the form is not the boundary. Fable refuted the draft against
the very file the draft cited as its own evidence — L-14's shape, a reading that stopped at the
field which agreed with it.

⚠️ **This lands in the repository, not yet on the live endpoint.** `/api/apply` runs as a Cloudflare
Pages Function and is republished by `wrangler pages deploy`, which needs a credential this host
does not hold (L-9, D-19). Until the operator deploys, the served endpoint still coerces in the old
direction, and an active mandate remains recordable in production. That is the state of the world
today rather than a claim about it.

**Armed, because a decision without a machine behind it is unenforced.**
`tests/test_intake_offers_no_active_mandate.py` fails the build if the endpoint stops assigning
`passive` unconditionally, or if the quoted token `"active"` reappears in the code of either the
endpoint or the form. It strips comments first, so this entry and the ones in the source can go on
quoting the old line. The red run is kept as `evidence/RED-009-intake-accepts-active-mandate.txt`.

The gate covers the one copy that executes. The four prose copies have no gate and are not pretended
to have one — a `LAW-*` naming them would be the fake anchor L-8 refuses, since no checker can tell
a withdrawn offer from a described one. What closes those is the count above, done again.

**Not covered, and named rather than left silent:** `web-1.0/` is the frozen rollback clone and its
`Apply.tsx` still carries the full active-mandate radio UI. The freeze is deliberate, so it is left
alone; but a rollback to that clone would re-offer the mandate with no prober behind it, and that is
a property of the rollback rather than a defect in it.

**Why.** No prober exists. Offering the mandate would ask a stranger to grant permission to touch
their production system, in the knowledge that nothing in this repository is capable of using the
permission — and it would do so on the single page where a visitor commits to something. That is a
claim stronger than its artefact pointed at the reader rather than at a subject, which makes it the
least excusable instance of the defect this product sells the detection of: the tool failing on
itself, in the one place a stranger acts on what it says.

**Why it is a decision and not a note.** The removal happened on 2026-08-20 and was written down
twice — a comment in `web/src/pages/Apply.tsx` and a paragraph in `docs/INTAKE_OPERATIONS.md` —
while `SPEC.md` §3.4 went on requiring "the mandate choice" on the form. The specification is the
document that governs the form, so for as long as that stood, the rule had been repealed in the
code and in the operations note while surviving intact in the copy that outranks both. That is L-2
exactly: *a rule written in more than one place survives its own repeal*.

**And the count went wrong twice, which is the part worth keeping.** The first draft found three
copies of the rule. Refuted, it found a fourth and said so — `apply.js`'s ternary, the only copy
that RAN, while `SPEC.md` §3.4 and the header of `Apply.tsx` were merely prose that had stopped
being true. Refuted again, it found a fifth: `docs/WHY_GET_VERIFIED.md` still asked a stranger for
an active mandate in the present tense, in the document that IS the offer. So five copies — four
prose, one executable — and the entry claiming "the copies were four, not three" was itself a
miscount, two lines above its own sentence about how prose is the easy half to find. The lesson
does not survive as a number. It survives as: **the copy you have not found is the reason to keep
counting**, and the search ends when a search finds nothing, not when the tally feels complete.

**What is unchanged.** The sentence the mandate existed to carry stays on the form: *without a
mandate we do not touch production*. Removing the control did not remove the promise, and the form
now states the read-only limit as a fact about today rather than as one branch of a choice. The
passport keeps its `mandate_ref` field: every record in the current cohort carries
`self-mandate-0001`, the operator's self-mandate under ADR-0006, because all eight subjects are the
operator's own systems. A subject verified without any mandate would carry the field with no
reference rather than no field at all — an absent mandate is a state with a name (invariant 1). The
first draft of this paragraph said the field was "null on every record"; it is null on none of
them, and the eight emitted passports say so.

**What this does not decide.** Whether active probing is built at all, and on what terms. T-2.12
owns that, and it requires a signed document before anything runs.

## D-22. The door and the arbiter are compared by a gate, and mypy's advisory state gets a date

**Decision.** `scripts/push.sh` runs every check `.github/workflows/gates.yml` can fail the build
on, and `tests/test_door_matches_ci.py` holds that correspondence as a table checked in both
directions. `mypy` stays advisory — with its three states separated, and with an expiry of
**2026-10-15** that goes red on its own.

**Why a table rather than another tool added to the door.** The ruff divergence was closed in D-20
by adding ruff to `push.sh`. That was the right repair and it addressed the instance: the header
asserting the two gate lists were identical stayed correct-sounding while nothing compared them, so
the next drift would have been just as invisible and would also have been discovered by a red
`main`. Writing the comparison out as a gate found two further divergences immediately, both older
than the ruff one:

- **the door never built the site.** The `shipped` job builds it because the sweep over emitted
  pages is the only check that judges what a reader receives (L-3). At the door those assertions
  read whatever `web/dist` happened to be on this host — a stale build, or none, in which case they
  skipped and were counted as passing. L-16 at the door: present, not armed. The build costs 2.1s
  measured and `web/dist/` is ignored, so the tree stays clean and `push.sh` still refuses a dirty
  one;
- **the door enforced no coverage floor.** CI requires 70%; `push.sh` ran a bare `pytest`, so a
  commit could drop coverage and go out clean. Measured 89% on 2026-08-20, so the threshold is
  slack the door can carry rather than a number picked to be survivable.

Neither had ever produced a red build. That is the argument for the table: they were found by the
check, not by the badge.

**Why mypy stays advisory, and why that is now a dated position rather than a standing one.** The
reasoning for suppressing its findings is unchanged — a gate that fails on day one gets disabled by
whoever meets it. What was wrong was the shape of the promise. `mypy ... || true` collapsed three
states into one, and the collapsed one was load-bearing: mypy failing to start printed exactly what
a clean baseline prints, and a clean baseline was the stated trigger for making the gate blocking.
The condition could not have been observed even if it had occurred. The step now fails on a clean
run (saying to make it blocking and add mypy to the door in the same commit), fails on exit ≥ 2 as
`not_measured`, and prints a count otherwise.

The reading is taken only in CI. mypy is absent from the audit host, so a local zero would be the
instrument's absence wearing the shape of a measurement — L-1, and L-11's sharper form.

**The baseline, and why it argues for a deadline.** 28 errors across 7 files on 2026-08-20, nearly
all `None` reaching a comparison or an attribute access. That is invariant 1's own defect class, in
`src/liveness/commitments.py` above all, which is the strongest available argument against letting
the advisory state stand indefinitely. The date is 56 days out, inside the sixty after which GitHub
disables a public repository's `schedule:`, because that schedule is what runs the deadline test in
the world where nobody pushes — L-19's arithmetic, applied to a different clock.

**What was NOT done, and named rather than left to be found.** The door builds with the
`node_modules` on this host while CI installs from the lockfile with `npm ci`; a clean install at
every push costs more than the drift it would catch, and the difference is recorded in `push.sh`
rather than closed. The comparison checks a declared correspondence, not semantics — it proves the
door runs `pytest` with the same coverage floor, not that the two runs see the same tree. The 28
type errors are not fixed here; this task bought them a deadline, not a repair. And the workflows
README table said "four jobs" while five were running, omitting `shipped` — the one job that judges
the shipped artefact, absent from the document listing what fails the build.

**A third instance of the same defect, found and deliberately left open.** `pyproject.toml` says of
the ruff rule families: "EXPANSION IS A DATED PROMISE, NOT AN INTENTION: after the front door lands,
add one family at a time … Recorded here so it cannot quietly become never." It names no date, and
nothing measures whether the front door has landed — the mypy promise exactly, one file over, in
the configuration of the gate this task was opened about, and carrying a sentence that claims the
opposite of what it does. It is named rather than closed because the two things it needs are the
operator's calls and not the executor's: whether "the front door has landed" is now true, and which
date each of `E5`, `UP`, `SIM`, `C4`, `BLE` gets. The mechanism to arm it exists in this commit and
the entry would be four lines. Recorded here so that leaving it is a decision with a name on it.

**The law's scope, corrected before it was ever true.** `LAW-DOOR-MATCHES-ARBITER` was first
written "no check can fail on main that the door did not run". Its test reads `gates.yml` alone,
and `codeql.yml` and `scorecard.yml` both trigger on push to `main` — so the law was broader than
its gate on the day it was ratified, in the commit closing a task about headers that outlive their
lists. The door cannot run CodeQL and should not pretend to: the achievable property is that **our
own** suite is mirrored at the door and the unmirrorable workflows are declared with the reason.
The law now says that, and the count of workflow files is asserted rather than left to the word
"three" in a README, so a fourth cannot arrive unnoticed.

**On how the remaining defects were found, which is the part worth keeping.** Three of the repairs
in `tests/test_door_matches_ci.py` were written, documented, and never called — dead helpers whose
docstrings described fixes the code did not perform, with the suite green throughout. Five more
false greens surfaced only when the repaired file was handed to Fable to *refute* rather than to
review: a printed excuse vouching for the step it skips, a reusable-workflow job, a commented job
id, a flow-mapping step, and a gate reached by command substitution. Every fix in this commit is
mutation-tested — the repair is removed and exactly one test must die — because a green suite
proved nothing about the three that were decorative. That practice is L-21.

## D-23. The prober exists, so the mandate option returns — one action wide, and asking rather than granting

**Decision.** `src/prober/` executes one active operation, `unauthenticated_access_attempt`: it
attempts to use a path the subject says is closed and reports whether the running system refuses it.
No request leaves the process without a mandate that permits that action, is in force, is not
revoked and has budget for the whole probe. The mandate choice returns to `/apply/` in the same
commit, naming that one action; the endpoint records `mandate_requested` beside a `mandate_applied`
that is the constant `passive` on every submission.

**The first version of this decision shipped the defect it exists to detect, and Fable refuted it.**
The loaded claim probed `GET /api/apply` expecting 405. `/api/apply` is a PUBLIC intake endpoint —
it accepts anonymous submissions, that is its whole purpose — so a 405 on GET is a method
restriction and not an access control, and the subject had never declared that path closed. The
action was called `unauthenticated_access_attempt` while the instance actually wired up was an
ordinary public read needing no mandate at all. That is L-13 in its purest form: the measurement
fitted to the acceptance criterion, invisible afterwards because everything around it reads as
principled. The tell had been sitting in `prober.py` since the first draft — `DECLINES_TO_SAY`
excludes 401 as *the clearest evidence a path is protected*, the whole classifier reasons about 401
and 403, and the shipped claim named 405, which is neither.

The claim is now `GET /.git/config`, expected to be refused, addressed to `web/wrangler.toml`'s
`pages_build_output_dir = "dist"` — the subject's own declaration that what is published is the
build output. Requesting another party's repository metadata is the canonical opening move of an
intruder and appears in their logs as exactly that, which is what makes it an act needing written
authorisation even though it fails.

**Retargeting the claim was not enough, and the second refutation is the one that changed the
design.** On a host whose catch-all is 404, `/.git/config` answering 404 is the same reading as a
misspelt path answering 404. The first repair still returned ENFORCED for it — crediting the
subject with a refusal never performed, on evidence a host that deployed nothing at all would
produce. L-11 says *404 is absence*, and the classifier was turning absence into a positive
finding, four lines below a constant whose docstring says so.

So the probe now takes a NEGATIVE control as well: a path on the same origin that cannot exist. If
the probed path answers as that one does, the state is `INDISTINGUISHABLE_FROM_ABSENT` and the
verdict is `not_measured` — L-10's third sibling, *the instrument cannot see the quantity*, which
is a complete reading of a question the answer does not settle. The same call catches the soft 404
that put four ERC-8004 identities in front of a human as businesses in Q-M1 (L-23): where unknown
paths answer 2xx, a 2xx on the probed path is not evidence of exposure either, and `NOT_ENFORCED`
must not be published. A probe costs three calls now, and the mandate is asked about all three.

**And the repair for that refutation carried the same defect one request further left, which the
third round found.** The new veto asked whether the negative control *answered* — so a control
coming back 403 counted as an answer, its status differed from the subject's 404, and the reading
was promoted to `ENFORCED`. But 403, 429 and 5xx are the server declining to say; a decline
establishes no catch-all at all. On an origin that refuses clients at its own discretion — which
this subject demonstrably is, and which is the fact the whole positive control exists for — one
unlucky call out of three would have credited it with a control never exercised. L-11 was armed on
one control and left unarmed on the other, in the commit that added the other. The condition is now
a named quantity, `catch_all_known`, and it vetoes in both directions: an unestablished catch-all
blocks the flattering `ENFORCED` and equally blocks the accusing `NOT_ENFORCED`, since a soft 404
cannot be ruled out either. Four mutations are kept in the red run, and two of them restore states
this component actually shipped between rounds — each of which passed every test that existed then.

**And the round after that found the same rule missing from its third site.** Both vetoes were
written inline at `ENFORCED` and at `NOT_ENFORCED`, and the fall-through to `DIVERGED` had neither —
so an origin that redirects every unknown path answered the probed path exactly as it answered a
path that had never existed, and that was published as a measured **FAIL**. A host which had
deployed nothing at all would have been accused of divergence: the mirror image of the sentence
`INDISTINGUISHABLE_FROM_ABSENT` exists to prevent, surviving two consecutive rounds of repairing
the identical defect in its two neighbours. The comparison is one named expression now,
`reading_matches_absence`, consulted by all three — two copies of a rule and a third place that
needed it is L-2 inside a single function, and writing it twice is what made the third invisible.

Two smaller things came with it. A `ControlClaim` could name a 2xx as the refusal it expected,
which would have turned an open path into a PASS with one field; the only thing standing against it
was a test pinning the single shipped instance, which is a rule enforced by inspecting one caller
(L-7). It is refused at construction now, 2xx and 3xx alike. And the `ProbeState` docstring counted
"three measurements and four statements" over eight members — the previous round's fix to that same
sentence changed a wrong number into one that did not add up.

**The red run itself was fabricated, and that is the worst defect in this task.** `RED-013` was
generated by one shell block that mutated, ran and restored four times with all output redirected
together, and the run recorded under RED 4 was in fact RED 3's — a different mutation's failures,
under a heading reading *"Everything below this line is verbatim tool output"*. The arming was real;
the artefact was not. Fable caught it by applying the recorded mutation and comparing the failures,
which is the only way it could have been caught, because the file looked exactly like an honest one.
This repository keeps red runs so that a reader can check a gate rather than trust it, so a
fabricated line in `evidence/` is worse than a missing file — it is the founding defect committed in
the artefact that exists to detect it, and it was produced by automation nobody was checking. Each
mutation is now run separately, captured to its own file, and joined afterwards; the four failure
sets are distinct, and that distinctness is stated in the file as its own control.

**The consequence is that the incubator's own probe returns `not_measured`, and it ships that way.**
provek.dev is a static site with no authenticated surface, so it has no path whose refusal differs
from its catch-all; the honest reading is that this question cannot be answered on this subject. A
green PASS was available by leaving the classifier as it was, which is exactly why it is worth
recording that it was not taken. `tests/test_prober.py` pins the three properties that made the
old claims indefensible — a claimed refusal may not be a success status, the probed path may not be
one the subject publishes for the public to call, and the claim must carry a negative control —
while the discrimination itself is made at runtime, where it belongs.

**Why the option could not return one commit earlier, and why it may return now.** D-21 removed it
because offering a stranger the chance to grant access to their production system, while nothing
here could use the permission, is a false claim about US on the single page where a visitor commits
to something. The condition was never "T-2.12 is finished"; it was "a signed mandate has something
to execute it". One probe satisfies that literally, and one probe is what shipped.

**Why the offer is one action wide.** The prober implements a single operation, so the form names
that operation. "An active probing mandate" in general would be the same defect at a smaller
scale — an offer sized to the ambition rather than to the artefact — and this project exists to
detect exactly that ratio. When the second action is built, the sentence grows by one clause.

**Why it asks rather than grants, which is the half that keeps D-21's finding intact.** The mandate
module opens "a mandate is a legal object, not a checkbox": it must state permitted actions, their
limits, what must not be affected, liability, an abort condition and how it is revoked. An HTTP
field carries none of that, so the radio records a QUESTION. The applied policy stays a constant in
code, which is precisely the property D-21 was written to establish after `body.mandate ===
"active" ? "active" : "passive"` turned out to honour `active` for every client that was not the
form. Returning the offer changes what we ask; it does not change what a request can authorise.

**The two fields exist because `apply.js` asked for them in writing.** Its own comment named the
collapse and deferred it: *"the moment a prober exists and the value can differ, the request's own
value has to be recorded beside the applied one rather than overwritten by it."* Until today
"asked for active, refused" and "asked for passive" were the same bytes in KV — invariant 1, in the
field that decides whether a human owes the applicant a document. An unrecognised value is a 400
rather than a coercion to `passive`: the safe-sounding default is what made the single field
meaningless in the first place.

**What the prober refuses to conclude, and it is the design.** The probe spends THREE calls, two of
them controls. The first is a request against a path the subject declares public, and its failure
is a veto, not a warning: `provek.dev` answers 200 to a browser's user agent and 403 to Python's default one,
so without the control a 403 read off a protected path would land in the set of refusals the
subject's claim named and publish ENFORCED — the subject credited with a control that was never
exercised, because the edge declined to talk to us (L-11). The veto is armed in both directions;
the case that would have flattered the subject is the one nobody checks. And because the probe
needs all three calls, a mandate with two left of its ceiling produces no probe at all rather than
part of one: the ceiling is the subject's protection and it is spent in whole probes.

**Three further corrections came out of the same refutation, and each was a claim outrunning its
artefact by a little.** *One*, the classifier filed two different facts under `ORIGIN_UNREADABLE` —
an origin that refuses our client, and a path that refuses us on an origin which answers everything
else. Those need different next actions, so `SUBJECT_DECLINED` is now its own state; invariant 1,
found inside the code written to honour invariant 1. *Two*, the hourly ceiling is enforced against
the count it is given, and nothing persists a count between runs, so what it bounds today is one
invocation rather than an hour. The runner names that in `CALLS_LAST_HOUR` instead of passing a
bare zero, and this entry no longer implies a limiter that exists. *Three*, `self_probe.is_live()`
carried a docstring saying the runner read it before spending a call; the runner never called it,
and `may_probe` already enforces the same condition. It is deleted rather than wired in — a second
implementation of a live rule is a copy that can drift from the one that runs (L-2), and a helper
whose only caller is the test asserting it is L-21's dead repair.

**The useful finding of this task was made beside the probe rather than by it, and it is attributed
that way everywhere it appears.** It came from the hand measurements taken while choosing what to
probe: **`GET https://provek.dev/api/apply`
answers 404**, where `web/functions/api/apply.js` claims 405. The same request to
`/api/nonexistent-xyz` returns the same static 404 page — the intake Pages Function is not deployed
at all. `~/orchestra/deploy.sh` publishes `web/dist` from the repository root while the functions
live at `web/functions`, which that directory does not contain. **So the form's only action has been
failing for every visitor who has ever pressed the button**, and four documents describe it as
working.

Nothing in this repository could have found that. Every gate reads files; the test guarding the
endpoint's behaviour says in its own docstring that it cannot speak about the deployed function;
the door builds the site and sweeps `web/dist`, which is exactly the directory the functions are
missing from. The gap between "the file says 405" and "the origin says 404" is the size of an
active probe, and closing it is the first thing this component did that reading a repository could
not. It is recorded as `evidence/PROBE-001.txt` and as L-25.

**It is named and not fixed — and the reason first written here was an assumption, which is the
part worth keeping.** That draft argued the fix was blocked on infrastructure: publishing the
functions needs the `INTAKE` KV binding and the two Telegram secrets to exist on the Pages project,
so a deploy would swap a loud 404 for a 503 from `if (!env.INTAKE)` — a different failure that looks
like progress. It reads like a technical reason and nothing had measured it. Asked directly, the
production project already carries **all three**: `kv_namespaces: ['INTAKE']` and `env_vars:
['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']` (`evidence/PROBE-001.txt`; binding values are never
printed, the names are the whole reading). So nothing infrastructural is missing. The only thing
wrong is the working directory the deploy command runs `wrangler` from — `web/functions` is found
when wrangler runs in `web/`, and `deploy.sh` runs it in the repository root.

That is L-14 committed inside the entry announcing a lesson about untested claims: a reason
constructed from what would plausibly be true, offered as evidence, and never asked of the system
that could answer it in one call. It cost nothing here because the deferral survives the
correction — `deploy.sh` lives outside this repository, it is the operator's publication channel,
and switching on a server-side endpoint that writes durable records and messages a human is more
than the site deploy this task is authorised to perform. But the deferral is now honest about its
size: **one line, in one file, on the operator's side**, not a blocked dependency.

**Adjacent, found in the same reading and recorded before it is lost.** `self-mandate-0001` has no
document anywhere in this repository. It is a bare string in `scripts/cohort.py` that eight
published passports point at as the authority under which their subjects were touched — a reference
with no referent, which is this project's subject defect in the field that says by what right we
acted. The active mandate is therefore a NEW one, `self-mandate-0002`, declared in
`src/prober/self_probe.py`: widening `0001` to cover active probing would have changed, retroactively,
what eight artefacts already in public say they were produced under. Writing the read mandate down
is a task of its own.

**Armed.** `LAW-PROBE-NEEDS-MANDATE` (`tests/test_prober.py`) asserts against the TRANSPORT and not
against the check: a recording `fetch` must hold nothing at all after each of the five denial
reasons, and the reasons are enumerated from the `Denial` enum so a sixth cannot arrive untested.
`LAW-PROBE-CONTROL-BEFORE-ABSENCE` (`tests/test_probe_control.py`) holds the veto.
`tests/test_intake_records_the_mandate_request.py` holds both halves of the intake rule. Every one
of the three was mutation-tested — the repair removed, the exact deaths recorded — because a green
suite proved nothing about three decorative helpers once already (L-21). The red runs are
`evidence/RED-013-prober-without-a-mandate.txt` and
`evidence/RED-014-intake-grants-what-it-was-asked.txt`.

**The self-mandate expires on 2026-11-18 and `tests/test_prober.py` goes red when it does.** That
red is correct behaviour rather than a defect to route around: a standing permission to send
unauthenticated requests at a live system should be renewed by somebody deliberately, and widening
the window to restore a green build would be the measurement fitted to the verdict (L-13).

## D-24. Bing ownership is closed by the published file, and it lifts nothing but itself

**Measured 2026-08-21.** `provek.dev` is a verified property in Bing Webmaster. `VerifySite`
returned `true`, and — because a call that reports on its own success is not evidence — the account
was re-read afterwards: `GetUserSites` shows `IsVerified: true` where it showed `false` eleven
minutes earlier. The sitemap is accepted, and "accepted" here is Bing's word rather than ours:
`GetFeeds` reports `Status: Success` with `UrlCount: 13`, a number Bing could not hold without
having fetched and parsed the file. Thirteen URLs were submitted against a quota **read** from
`GetUrlSubmissionQuota` (100 that day), and the daily remainder moved 87 → 74 across the send. The
snapshot is `~/orchestra/logs/bing_state.json`, taken after the verification rather than before it.

**What actually closed it was the deploy, and this withdraws a request to the operator.** D-19 and
the reasoning behind the notes ceiling both record Bing as answering `ErrorCode 14` until ownership
verification is closed, and D-19 offers the cheap way through: a **DNS CNAME record**, one line on
the operator's side. That request is withdrawn — not completed, withdrawn. `BingSiteAuth.xml` has
been reachable at the site root since the publication channel began working on 2026-08-20, and the
root file closed the verification with no DNS record and no operator action at all. The CNAME was
the cheapest path only while the site could not be published; it stopped being needed the moment
that changed, and a standing ask that no longer buys anything is a claim on somebody's attention
that our own records no longer support.

**It does not lift the notes ceiling, and the temptation to read it as though it did is the point.**
`LAW-NOTES-CEILING` releases on "an indexation reading from a verified Bing Webmaster property".
That condition has two halves and exactly one of them just became true. The reading itself does not
exist: `GetQueryStats` and `GetLinkCounts` now answer instead of refusing, and both return zero —
but so does `defycard.com`, an old and verified property, which means the zero is a statement about
what those calls can see here and not about whether anyone has found this site. The snapshot records
them as `instrument_blind` rather than as zero impressions, and three notes still stand. Reading
`is_verified: true` as the release condition would have raised a publishing rate on the strength of
a gate we had merely walked halfway through.

**Corrected 2026-08-24 by D-34; the paragraph above stands as written, because a decision is not
rewritten after the fact.** The sentence "but so does `defycard.com`, an old and verified property,
which means the zero is a statement about what those calls can see here" is false. It draws a
conclusion about the instrument from a control that returned zero, and a control that returns zero
has established nothing at all — the same call, on the same key, answers 64 rows at that control
three days later. What this decision CONCLUDES survives the correction: ownership still lifts
nothing but itself, and the notes ceiling still stands. Its reason does not survive, and the
difference matters, because the reason is what the next reader would have reused.

**The instrument was wrong in our own signature way, and the red run is kept.** `SubmitUrlBatch`
answers success with an empty body; the first version of `submit_urls` therefore wrote
`state: "accepted"` whenever the call did not raise, and funnelled every failure — including a
dropped connection, after which Bing may well be holding the URLs — into `submitted: 0` with
`count_state: "measured"`. A refusal of the instrument, published as a fact about the world, in the
client written to catch exactly that. The verdict is now computed from a quantity read twice: the
strongest word available is `received_quota_charged`, and it is deliberately not "accepted" or
"indexed", because the quota decrements on receipt and nothing in this API promises a crawl. An
unanswered call yields `sent: null` and `check_did_not_run`. Seven simulated worlds now produce six
distinct states; against the discarded version they produced two, and that run is kept at
`~/orchestra/logs/RED-bing-submit-states.txt` (`bing_states_check.py --prove-red`).

**Two things left unmeasured, named rather than rounded off.** Bing reports the sitemap's
`FileSize` as 2197 bytes; the file served from `https://provek.dev/sitemap.xml` is 1491 bytes to
every client we asked, including `bingbot`, and `web/dist/sitemap.xml` matches the served copy
exactly. The `UrlCount` agrees with ours at 13, so Bing parsed the document we published, but the
size disagreement has no explanation here and is recorded without one. And durability: the three
readings of `is_verified: true` span three minutes, which cannot distinguish a settled verification
from an optimistic flag that reverts on Bing's next independent fetch. The known revert mechanism is
guarded — the file is in `web/public/` and reaches `web/dist/`, so a deploy cannot silently drop it
— but the distinguishing measurement is a re-read after Bing's own re-crawl, and it has not happened
yet.


## D-25. The scheduler publishes through the same door a human uses, and only what the gates judged

**Context: the two blockages this schedule was built around have both lifted.** D-19 designed the
daily cycle when its last two steps could not succeed — no Cloudflare credential on the host, and
`provek.dev` unverified at Bing — and its whole selling point was that the shut channel would be
struck and NAMED daily. Ownership was verified on 2026-08-21 (D-24) and the credential is now in
`~/.env`. T-C5 asked what the cycle did with that, and the measured answer is nothing: `step_deploy`
looked for a `wrangler` binary in `web/node_modules/.bin`, in `/usr/local/bin` and on `PATH`, there
is none in any of the three on this host, and so every cycle would have stopped at
`blocked_no_tool` with the credential check below it as dead code. The channel did not open when
its preconditions did.

**Decision: `step_deploy` no longer contains a deploy command.** It calls `~/orchestra/deploy.sh`,
which is to the site what `scripts/push.sh` is to the repository. The copy that was there had never
executed once, and had rotted in three separate ways while nobody could see it: the token is pinned
to one IPv4 address and this host prefers IPv6, so the call needs `--dns-result-order=ipv4first` or
it fails as `10000 Authentication error` and reads like missing permissions; `wrangler pages deploy`
resolves `functions/` against the current working directory, so the wrong one publishes static
assets and a dead `/api/apply`; and the tool's own report is not evidence, which is why `deploy.sh`
ends by reading the live site through `scripts/verify_live.sh`. Three divergences in one unexecuted
copy is L-2 with the lid off — a rule written in two places, where the second copy was never run and
therefore never contradicted.

**Decision: the unattended publisher ships only a tree the gates judged — LAW-PUBLISH-JUDGED-TREE.**
`wrangler pages deploy` uploads the working tree, and this tree routinely carries work parked
between tasks; a stash restored "byte-identical" is the established habit here. On the morning this
was written, an unpushed T-A2-5 rewrite of the `/apply/` offer sat in the tree two hours before the
day's slot, with nobody at the keyboard. `push.sh` has refused a dirty tree since it was written and
states the reason — the gates judged the tree, so what leaves must be what they judged — and the
site had no equivalent because until this task the scheduler could not publish at all. **The hazard
is one this change creates rather than one it inherits, which is why the guard ships in the same
commit as the fix.**

The rule is deliberately not "refuse a dirty tree". The cycle dirties the tree itself — it writes a
note into `web/notes/src/` and rewrites the manifest — so that rule would refuse every cycle forever
and be deleted by the first agent it stopped. It is "refuse a tree dirty OUTSIDE the paths the cycle
writes", and those paths are listed once, in `scripts/publishable_tree.py`. The gate lives in the
REPOSITORY rather than beside the scheduler for the reason `deploy.sh` gives for moving its own live
check there: a check outside the repository is read by no reviewer and executed by no test.

**It has three outcomes, and the third is the load-bearing one.** `publishable`, `foreign work is
present`, and `git could not be asked`. Collapsing the third into the first publishes on the
strength of a check that did not run; collapsing it into the second manufactures a daily false red,
which teaches walking past a gate exactly as a false green does (L-5). `--commit-dirty=true` in
`deploy.sh` is not the same permission and is not evidence against this: there a human has just run
the gates and is choosing a known state, and the flag suppresses a warning about it. Under a cron
entry the same flag means "publish whatever is lying on disk", and the difference between those two
readings is the whole of this law.

**Decision: the Bing submission is downstream of a page that was read from the outside.** L-17
recorded, and left alone, that the cycle caught `Blocked` from the deploy inline and ran
`bing_submit` regardless — so a day with a working Bing channel and a failed deploy would submit the
URL of a page that does not exist. It was left alone because "the change cannot be exercised while
the capture is red", and the capture went green in T-C4, which is what makes this the moment to
close it rather than record it again. A blocked deploy now withholds the submission under its own
journal line, and what is submitted is not what the build produced but what a `GET` answered `200`
for on `https://provek.dev` after the deploy — the same law as `verify_live.sh`, applied to the
claim we make to a search engine.

**Decision: novelty is measured against the live sitemap, and a failed reading is not zero.** The
diff was against `sitemap_urls` in the state file, which L-17 names twice over: it was saved even on
cycles that published nothing, so a page built while the channel was shut spent its novelty on the
day it was BUILT and became `nothing_to_submit` forever after; and on the first cycle to reach that
step there was no previous value to diff against, so that cycle's own new page fell into the gap
between "no baseline" and "already seen" and would never have been submitted by anybody. The
baseline is now `https://provek.dev/sitemap.xml`, read before the deploy. What is published is a
measurable fact and the state field was a copy of it that could go stale (L-2); the field is gone
rather than kept in sync. When the read fails, novelty is `not_measured` — which is neither "no new
URLs" nor "all of them" — the deploy still happens, and the submission is withheld under
`withheld_novelty_not_measured`.

**What is NOT claimed.** The scheduler is still outside this repository (D-19) and still cannot be
exercised by a clone; only the tree gate it calls has moved inside, and that is one of its six steps.
The corpus ceiling is untouched at three (D-18), so this channel has two more captures of work in it
before `nothing_pending` becomes the permanent steady state — a schedule striking a channel that has
nothing to send is the state D-19 already calls correct, not a defect to be fixed later.


## D-26. A deployment is named by what was published, and `wrangler@4` stays unpinned

**The defect, and the reason its near-miss is not a defence.** `~/orchestra/deploy.sh` built
`web/` from the WORKING TREE and then labelled the result `git rev-parse --short HEAD`. Those are
two different artefacts the moment the tree is dirty, and the script said so about neither: it also
passed `--commit-dirty=true` unconditionally, so Cloudflare's own record could not separate a
deliberate dirty publication from a clean one either — the one field built to carry that fact was a
constant. `DEPLOY CONFIRMED on <sha>` was therefore true of a commit and false of the site, in the
operator's deploy log, which is the only record of what is live. The deploy of 2026-08-24 01:41
passed through the hole without falling in, because the work in progress happened to be parked in a
stash at that minute; D-25 records the opposite arrangement at 02:59 the same morning, an unstashed
`/apply/` rewrite in the tree two hours before the scheduler's slot. A hole closed by where the
work happened to be lying is not closed.

**Decision: a dirty tree is refused by default, and the refusal names the paths.** `push.sh` has
refused one since it was written, for the reason it states — the gates judged the tree, so what
leaves must be what they judged — and the site had no equivalent for the artefact a human deploys.
The check runs BEFORE `npm run build`, because the build reads the tree: the question is about the
input, asked before our own step touches anything.

**Decision: `--allow-dirty` grants publication and never the commit's name.** The operator can
publish an unjudged tree; the deployment is then labelled `dirty-<digest>` over a hash of the bytes
on disk, `commit_dirty` is measured rather than asserted, and the commit message states that the
base commit does not describe what was published. In the three fields the deployment record
carries, the short sha therefore never stands alone.
Without this half the flag would be the original defect with a nicer spelling, which is the whole
reason the permission and the label are two decisions and not one.

**Three outcomes, not two, and the third is load-bearing.** `labelled`, `refused — the tree is
dirty`, and `the tree could not be read`. Collapsing the third into the first publishes under a
name earned by a check that did not run; collapsing it into the second sends the operator hunting
for uncommitted work that may not exist. The policy lives in `scripts/deploy_label.py` rather than
beside the deploy script, for the reason `verify_live.sh` moved there: a check outside the
repository is read by no reviewer and executed by no test.

**What is NOT claimed, measured while writing this.** `git status` does not fail on a directory it
cannot read — it warns on stderr and exits 0 with that subtree missing from its output. So a tree
carrying an unreadable directory is reported clean by the shared reader and would be signed with a
commit's sha. The hole is in `publishable_tree._porcelain`, which the scheduler's gate depends on
too, so it is recorded as a finding rather than repaired by a neighbouring task. This gate refuses
every dirty path git REPORTS and does not claim git reported all of them.

**That limit was closed on 2026-08-24 by D-33, and this paragraph is left standing rather than
rewritten.** It is the record of what was known when this decision was ratified, and the finding it
names is the reason the repair exists at all; deleting it would leave D-33 looking like a
precaution nobody had measured a need for. What changed: the shared reader now returns its third
state whenever `git status` writes to stderr, so the sentence "this gate refuses every dirty path
git REPORTS" is unchanged and the sentence before it no longer describes the gate. The price of
that reading, and the class it still cannot see, are in D-33.

**Decision: `wrangler@4` is NOT pinned to an exact version.** The deploy runs `npx --yes
wrangler@4`, which floats across minor and patch releases. Pinning would freeze a tool that talks to
somebody else's API and holds our credential, and security updates to it are worth more than the
breakage a float can cause here — provided the breakage is caught by measurement rather than
prevented by a version number. That proviso is the whole decision, and the first draft of this
paragraph asserted it where it was not yet true.

**What the deploy actually measures, and the second class it did not.** The failure T-H1 found is
covered: the `functions/` directory resolved differently, the upload carries static assets and no
Pages Function, `scripts/verify_live.sh` reads `GET /api/apply` and requires 405, and a regression
answers 404 and exits nonzero. But `verify_live.sh` measures LIVENESS, not FRESHNESS — eight
addresses and the codes they must answer, every one of which is answered just as well by last
week's deployment. So the class "wrangler exited 0 and published nothing, or published somewhere
else" read GREEN end to end: the old upload keeps answering 405 and 200, and a confirmation went
into the operator's deploy log for an upload that never landed. A green light over an unmeasured
fact is this project's founding defect, and claiming that measurement covered a class it could not
see was that defect in a decision record. Found by Fable, before this was pushed.

**Consequence: the label is written into the upload and read back off the live site.**
`scripts/deploy_stamp.sh` puts it in the built directory and, after publication, requires
`https://provek.dev/deploy-label.txt` to equal what this run published — the only fact that
separates a fresh deployment from a working stale one. It distinguishes five answers, not two: the
name matches; a different name is live; a 404, meaning no label was published there at all; any
other code, meaning the address is served but which deployment is live went unmeasured; and the
address could not be read. The body and the status code come from ONE request, because two would
mean a verdict assembled from two different moments — the first draft took two and never read the
second one's exit status, so a transport that died in between would have announced `000` as a fact
about the site. It is read BEFORE `verify_live.sh`, so a green liveness reading can never be the
first thing the operator sees about somebody else's deployment. That is what makes the float above
a measured trade rather than a hopeful one.

**Consequence: the tree is measured again after the build.** Between the gate and the upload sits
`npm run build`, and in that window the tree can move: the build rewrites the tracked
`web/dist-ssr/` (byte-identical today — measured — but that is a property of the build, not a
guarantee), and `notes_cron` writes `web/notes/` on a schedule. "Concurrency = 1" is a budget rule,
not a machine guarantee. The label taken before the build must still describe the tree after it, or
the upload goes out under a name measured against different content; a mismatch is red and prints
both labels.

**What is still NOT measured, named rather than implied.** How Cloudflare's dashboard RENDERS a
deployment record is not something this repository has read. The three fields it accepts —
`--commit-hash`, `--commit-dirty`, `--commit-message` — are measured (`wrangler pages deploy
--help`, wrangler 4) and all three are now filled from a reading of the tree instead of the
constant `true` that used to be passed on every deploy. What that produces on screen is the
operator's to confirm, and the sentence "the short sha never stands alone" above is a claim about
those fields, not about a dashboard anybody here has looked at.

## D-27. The intake's POST half is deferred rather than assumed, and the probe is the operator's to run

**Decision.** No probe of `POST /api/apply` is taken from this repository or from the audit host.
The path stays `not_measured` with the reason `check_did_not_run` — the state
`docs/INTAKE_OPERATIONS.md` already records for it — and one move lifts it while fabricating
nothing: the retrospective sweep under *The habit*, which reads the namespace and is the operator's
to run. The only other thing that would answer the same questions is a real submission, which is
the operator's to decide and is not a probe taken here. This record is the deferral itself. It is
not a finding about the endpoint, and nothing in it says the POST path works.

**What IS measured, so the deferral covers a named half rather than the whole endpoint.**
`GET https://provek.dev/api/apply` answered **405** with the handler's own sentence — a string that
lives at `web/functions/api/apply.js:196` and that no edge default carries — read on 2026-08-24
under two different deployment labels, with `/api/nonexistent-xyz` → 404 and `/` → 200 as controls
so the code describes that path rather than the origin's mood (L-11). The dated table is in
`docs/INTAKE_OPERATIONS.md`. That places the handler in the published tree and says nothing about
the branch the intake depends on: a GET enters `onRequestGet` and returns without touching `env`,
so that `env.INTAKE` resolves at runtime (`apply.js:91` answers 503 if it does not), that the two
Telegram variables are readable by the Function, that the two writes to one key land rather than
meeting the documented one-write-per-second refusal, and that the `writeback-refused:` sentinel is
written when they do not — all four are untouched by every reading taken so far. Invariant 1 says
what that is: `check_did_not_run`, not a zero, and not a pass inherited from the 405.

**Why the only probe that would answer it is one this project will not run.** A VALID submission is
the only thing that reaches any of those four items; an invalid one is refused at validation
(`apply.js:38`–`80`) before the first `put` and settles none of them, and the endpoint has no dry
run. So the probe puts a durable record into the operator's production `INTAKE` namespace and wakes
them on their ops channel — an active operation with an effect on a live system, which is the class
D-23 refuses to perform without a mandate naming that action. Nothing here submits to a live intake
in order to turn a `not_measured` into a green line in a document: that is L-13 exactly, the
measurement fitted to the acceptance criterion, and it would be fitted on the endpoint the launch
depends on.

**The cheap way in is not ours to take, and the second candidate is itself unmeasured.** The sweep
under *The habit* answers both questions — whether anyone has ever submitted, and what the
`delivered` values are — in one `list`, with no notice sent and nothing fabricated. It runs on the
operator's laptop: `wrangler` is not installed on the audit host and the account is not reachable
from it, so it is the habit of a person and not a job this repository can schedule. The other
candidate is a preview deployment, and what a preview deployment BINDS has never been read —
`evidence/PROBE-001.txt` asked the Pages project for names and got `production kv_namespaces` and
`production env_vars`, a reading about production and about nothing else. If preview binds the
production namespace, a POST there IS the fabricated submission this decision refuses; if it binds
its own, it cannot answer the first item on the list. Which of those two holds is the reading that
has to come first, and it has not been taken.

**What the deferral costs, named rather than left for the reader to find.** If any of the four items
is broken, the first party to learn it is a real applicant whose submission fails — the person the
endpoint exists for. That cost is why `docs/INTAKE_OPERATIONS.md` puts the sweep BEFORE the link is
published rather than on a schedule after it: the deferral is bounded by an event already written
down, and its empty case is a reading in its own right, since zero records means the endpoint has
never once been exercised end to end.

**What this decision does not license.** No page, document or commit message here may describe the
intake's POST path as working, verified, or tested in production; the GET reading may be quoted for
what it is. And nothing reddens when the readings go stale. `scripts/verify_live.sh` does read the
live origin — it requires `GET /api/apply` to answer 405, calls a 404 there the failure it exists
to catch, and reports a transport refusal as UNREADABLE rather than as a code — but it is run by
`~/orchestra/deploy.sh`, not by the door and not by CI, so it judges a deployment at the moment one
is made and never the dated table in `docs/INTAKE_OPERATIONS.md` afterwards. Between deployments
the date beside the reading is the whole mechanism, which is prose — L-25's boundary, named in that
document in the same section. Rejected alternative: a gate that curls the origin. The argument
against it was that somebody else's network failure would paint the build red, and that argument
does not hold — a refusal is `check_did_not_run` and a measured 404 is the finding. It is a task
with its own red run and it is not taken here, which is why this paragraph names the gap instead of
implying a check exists.

**Numbering.** This number was held open for this record by the ruling of 2026-08-24, and the
paragraph below in D-28 is what kept the gap from reading as a deleted decision.

## D-28. A line in `evidence/` that goes stale is corrected BESIDE the artefact, never inside it

**Numbering.** D-27 was reserved by the ruling of 2026-08-24 for the deferral of the POST path and
stood empty when this record was written; taking the number here would have made two decisions
answer to one. It was written later the same day and is above. This paragraph also predicted that
the number would be taken "by the task that measures it" — what took it defers the measurement
instead, and that difference is D-23 rather than drift. The prediction is corrected here rather
than deleted, because a draft this file's own subject-matter proved wrong is evidence and not a
typo. The paragraph stays because it is the reason the numbering ran D-26, D-28, D-29 for the
hours in between.

**Decision.** `evidence/RED-020-*` keeps a sentence that was true when it was written and stopped
being true the next morning — "`~/orchestra` is not a git repository and held no backup", in three
places (`RED-020-deploy-confirmed-over-a-dead-intake.txt:12`, `RED-020-generator.py:72` and
`:241`). Neither file is edited. The correction is a dated sibling,
`evidence/RED-020-erratum-2026-08-24-the-frame-went-stale-not-the-fact.txt`, which quotes the three
lines, separates the fact that survived from the frame that rotted, and says plainly that a history
beginning at 04:32 on 2026-08-24 does not restore the copy destroyed before it.

**Why.** Three reasons, and none of them is that editing would be inconvenient. Invariant 5 keeps
the red run as an artefact, and an artefact edited afterwards is a recollection of a run rather
than the run. The `.txt` is OUTPUT of `RED-020-generator.py`: editing it by hand desynchronises an
artefact from its producer (L-26), and regenerating it re-runs six mutations through pytest and
overwrites red output captured at a different moment. And the precedent is already set — L-30's
correction could not go into the commit it belonged to and stands beside it, with the record left
wrong on purpose.

**Why it was not simply left alone.** The three lines are in the PRESENT TENSE about a live system.
A reader gets a claim about how `~/orchestra` is kept today, not a note about how it was kept on
2026-08-24 — the same class this project repaired in T-A2-5. The artefact stays; the claim gets
answered.

**The cost, named because it is real.** Nothing links line 12 to the erratum. A reader who opens
only the `.txt` reads the stale sentence and never learns the correction exists; what they get is a
directory listing where the two names sit adjacent, which is weaker than a footnote and is the
price of not rewriting evidence. The alternative — a pointer inside the artefact — is an edit to
the artefact, so there is no version of this decision that keeps both properties.

**Found by the hand that created it.** The staleness was reported in `~/orchestra/FINDINGS.md` by
the author of the commit that caused it, on the same day, with the fork explicitly left to a judge
on the stated ground that the hand which creates a divergence is a poor judge of how tolerable it
is. The judge answered on 2026-08-24 (ruling, item 5) and this records the execution of that
answer, not a fresh opinion.

## D-29. The rollback rule is prose here and code in `~/orchestra`, and no gate can close that gap

**The incident, 2026-08-24 06:34 UTC.** T-C7's own acceptance criterion required simulating a
process killed between writing a note source and writing its manifest line, so the tree was
deliberately put into that half-written state. The task did not close, the orchestra rolled the
tree back to the last good commit and marked it STUCK — and the reset returned the TRACKED half
(the manifest lines, and T-C7's edits to `tests/test_notes_freshness.py` and `web/notes/emit.mjs`)
while the UNTRACKED half, two `web/notes/src/*.md` sources, stayed exactly where it was. Orphaned
sources crash `loadNotes()`, so the gates read red AFTER the rollback, and the orchestra halted
deliberately rather than build on a tree it could not explain. The alarm was right; the state it
was alarming about was manufactured by the recovery.

**Decision.** The rollback procedure is written in `CLAUDE.md` — inventory the untracked paths
BEFORE the reset, take the difference after it, MOVE what appeared into quarantine, and re-run the
gates — and it is armed only where a program performs the rollback: `~/orchestra/orch.sh`, whose
recovery path now does exactly those steps and is committed there rather than living, as it did
until today, as an uncommitted edit on one host.

**Why there is no gate here, and why that is not resignation.** A check that fires when an agent
types `git reset --hard` would have to be triggered by the act it polices, which is L-19 exactly:
the tripwire measures whoever walks into it and is silent in the state it exists for. Every gate
this repository owns judges the TREE, and the tree after a bad rollback is indistinguishable from a
tree that was always broken — which is precisely why the incident cost an orchestra halt to
diagnose. Naming a `LAW-*` for this would be the fake anchor L-8 refuses.

**What the machine half was measured to do, and what it was not.** Its first version counted the
files it INTENDED to move: on a fixture carrying a Cyrillic filename — the shape of the file the
06:34 quarantine was itself given, whose name is the Russian word for "why" — it logged "2 files
carried out" while one file moved and the other stayed in the tree, because `git status
--porcelain` quotes non-ASCII names and no such path exists to move. That is
invariant 1 inside the repair: a refusal to resolve a name, returned as a count of files carried to
safety. Repaired before it was committed, and the run is kept as
`~/orchestra/evidence/RED-H7-a-quarantine-that-counted-what-it-did-not-move.txt`: the reading is
now NUL-delimited, the outcome is three counters (moved / vanished before the move / move REFUSED)
each exercised by a fixture, `mv`'s stderr is kept instead of discarded, and a missing
before-inventory is reported as unmeasured rather than read as "nothing appeared" — the latter
would have quarantined work that was lying in the tree before the task began.

**Still not measured, stated rather than implied.** The hop has never executed inside a live cycle.
The quarantine of 06:34 was made by hand, and what the red run above exercises is the shipped text
of `orch.sh` extracted at run time against a fixture, not a real failed task. Until a cycle takes
that branch, "the orchestra recovers from untracked damage" is a claim about a fixture.

**Two more machine halves under the same doctrine, 2026-08-24 (T-H8).** The gap this decision names
turned out to have two further instances, and both are repaired the same way — inside the program,
because a gate would again have to be triggered by the act it polices.

*Records are now committed by the hand that writes them.* The briefs, the judge's answers and the
plan edits are written by `orch.sh` and `plan.py`, but committing them was left to a hand that had
already moved on to the next task; the orchestra tree stood dirty after the run three times in one
day, the last time on twenty paths. The pinned revision contained zero occurrences of `git commit`.
It now has `orch_commit()`, called at seven points of record, with three outcomes named separately —
committed, nothing to commit, and REFUSED — because collapsing the last two would report a clean
tree where the commit did not happen. Kept as
`~/orchestra/evidence/RED-H8-b-records-written-by-a-hand-that-never-committed.txt`.

*A zero-byte answer from the judge is a refusal, not a verdict.* An empty answer file is
indistinguishable from a judgement, and the cost is not the missed call but the sentence put in the
judge's mouth: the flow reads on, finds no acceptance line, and logs "Fable said there is more to do
but returned no tasks" when Fable said nothing. `ask_fable()` now names the emptiness in the
journal, retries once, and on a second empty answer writes the refusal INTO the answer file and
returns a distinct code that both call sites branch on — the file itself can no longer consist of
nothing. Kept as `~/orchestra/evidence/RED-H8-a-zero-byte-answer-read-as-a-verdict.txt`.

**The task's own brief carried a measurement the journal contradicts, and that is the more useful
finding.** The brief asserted two zero-byte answers, at 07:10 and 11:59. The journal says
`ask_fable()` has run five times and every answer was non-empty (9416, 13015, 7311, 15966, 16751
bytes); that 11:59:51 was the QUESTION, answered at 12:10:44 with the 16751 bytes on which the
ledger accepted T-C7; and that exactly one genuine zero-byte file exists, from a Fable call made by
hand outside the function. The defect was real, the transcription was not, and "measured twice by
this instrument" would have been precisely the claim-stronger-than-artefact this project exists to
catch. The cause of the misreading was itself the defect one layer down: `> "$out"` truncates the
answer file when the call STARTS, so for the eleven minutes of a healthy call — up to forty by the
timeout — it reads zero bytes, spelling "in flight" and "instrument refused" identically. The answer
is now assembled beside the file and moved into place in one motion, so a reader mid-call sees the
previous verdict intact and an `.inflight` file saying why. RUN 3 of the red run measures exactly
this from inside the call.

**The instrument that nearly decided all of this returned a refusal as silence.** The first reading
of `logs/orchestra.log` reported that the string "Fable" did not occur in it at all, from which the
repair and this entry would have been built on "the function has never once run". It occurs 99
times. The journal is invalid UTF-8 from byte 18489, because `ask_fable` truncated its own log line
by BYTES and severed a Cyrillic character — every line naming Fable carries the break, since that
is the line being cut. Repaired to a character-wise cut; the existing journal is left alone, being
the record of the run. The bound is the useful part and took a second measurement to establish: the
orchestra does not go blind, because in the bare environment it actually runs in `grep` is GNU grep
3.7 and reads the file correctly. What went blind was the ANALYSIS — in this agent's shell `grep` is
a function wrapping ugrep, which on invalid UTF-8 exits 1 with empty stdout AND empty stderr, which
is character-for-character what "no matches" looks like. §2.9 turned on the tooling the audit itself
is performed with, and the only thing that caught it was measuring the same fact a second way.

**Limits, stated rather than implied.** Both halves are exercised against fixtures that extract the
shipped text of `orch.sh` at run time — not inside a live cycle, the same bound this decision
already records for the quarantine hop. And `orch.sh` was RUNNING while it was repaired: bash parses
a compound command whole, so the live process is playing out the pre-repair text and both halves
take effect at the next launch. The installation was done by rename rather than in-place edit for
that reason, and the live process was confirmed to still hold the old inode, marked `(deleted)`; an
in-place edit would have sent it to execute an arbitrary fragment of the new file at its old byte
offset.

**A fourth machine half, 2026-08-24 (T-H11): the submission mark now carries a measurement.** Twice
in that one day the orchestra marked a task submitted-unverified over work that had never been
planted, and both times the gates were honestly green — T-H4 at 05:01:20Z with the whole of its work
in `stash@{0}`, T-S1 at 11:24:28Z with its work in the index. Green gates and planted work are two
different claims: the gates judge the health of the TREE, and whether the work is IN that tree is a
question none of them asks. Both divergences existed at the second of the mark and cost one command
to see; the judge learned of them hours later, from a neighbouring task. The mark now goes into the
plan beside a measurement block naming five things taken at that second: which tree was read, how
many paths its porcelain reports, how deep its stash is, its local HEAD and the sha `origin/main`
answers with.

*It is a measurement and not a gate, and that is the same doctrine as above rather than a
concession.* A check that refused the mark on a dirty tree would be triggered by the very act it
polices, which is L-19 exactly — it would measure the hand and stay silent in the state it exists
for, the state where nobody marks anything. Nothing in the new path can withhold the mark: every
refusal of the instrument becomes a word in the line and the submission still goes in, exercised as
its own case in the red run.

*Four numbers rather than the two the task named, and the third was found by measuring rather than
by reasoning.* The task asked for a porcelain count and the remote sha. On the fixture both read
GREEN for T-H4 — `git stash` removes the work from porcelain, and the commit was already on the
remote — so those two alone would have been blind to one of the two incidents they were written
for, and blind in the most confident form available, a zero. Three shapes are now visible in one
field each: work in the index shows up as a non-zero porcelain count, work in the stash as a
non-zero stash depth, and work committed but never pushed leaves local HEAD and the remote sha
unequal. Kept as
`~/orchestra/evidence/RED-H11-green-gates-and-work-in-the-stash-read-the-same.txt`.

*Three shapes is not coverage, and this sentence exists because without it the one above reads as
though it were.* Unplanted work also takes forms none of the four fields sees, and the first
instance is this task itself: `orch.sh` passes `--tree "$ROOT"`, so every mark measures the
REPOSITORY, while T-H11's own work lay in `~/orchestra`, which has no origin at all — the line will
be green, true, and about a different tree, which is why the tree it measured is named in it. Also
blind: a commit on another local branch or in another worktree while `HEAD == main == remote`;
`skip-worktree` and `assume-unchanged`, under which porcelain says nothing about edits to a tracked
file; and a hand editing the plan file directly, which never reaches the ledger. None of these can
be closed by a gate, for the reason the original could not.

*It lives in `plan.py`, not in `orch.sh`, for the reason the commit moved in T-H8:* inside the call
that makes the record there is no interval in which somebody has to remember. The first draft of
this paragraph justified that with a fact the journal refutes. It said the plan's second permitted
hand — the executor's own claim form, which the law of the plan allows beside the orchestra's — had
been used on 2026-08-21 at 02:38. What `logs/orchestra.log:414` shows at that moment is the
ORCHESTRA's form, stamped 2026-08-21T02:38:38Z, written by an agent calling `plan.py submit` out of
band; the executor's form has never appeared in any plan or any journal, only in a docstring. The
conclusion survives on firmer ground than it was given — the out-of-band hand went through `submit`,
so a measurement in the ledger covers it and one in the orchestra would not — but the cost is worth
recording, because a justification stronger than its artefact, inside the entry written against that
very defect, is the worst instance this project has to offer. Found by Fable, refuting this change.
A limit falls out of the correction and is now written in the ledger too: a hand that edits the plan
file directly bypasses the ledger, and no measurement placed there can see it. `orch.sh` passes
`--tree "$ROOT"` rather than letting the ledger infer the tree from its working directory, because a
number measured off the wrong tree while looking like a measurement of the repository is worse than
no number at all.

*Limits, stated rather than implied.* The fixture drives the shipped `plan.py` as a subprocess
against a throwaway repository with a real origin, not a live cycle — the same bound the halves
above carry. Two things in it had to be repaired before it was kept, both of the kind it exists to
catch. It first SIMULATED the gates and had them call the T-S1 tree red, which would have refuted
the incident it reproduces; what the gates said is now quoted from `logs/orchestra.log`, where both
marks are preceded by the journal's own line saying the gates were green. Its narration was also
unfalsifiable: the paragraphs asserting a porcelain count of one and a stash depth of one were
constant strings that would have printed word for word
against a ledger writing no measurement at all, so the only non-zero exits were setup failures.
Every narrated number is now checked against the line the shipped ledger wrote, substituting the
pinned file takes the producer to exit 1 on ten failed expectations, and a control section inside
the artefact demonstrates the checks firing. Finally, until the orchestra is relaunched the running
process is playing out the pre-repair `orch.sh` and passes no `--tree` at all; the marks it makes
resolve the tree from the live process's working directory instead, which was confirmed to be the
repository. That the criterion is met by that route rather than by `--tree` is luck until the next
launch, and is recorded here rather than left to be discovered.

## D-30. The CI toolchain is pinned by hash, and a set that goes stale reddens `main` on purpose

**What was still unpinned after the actions were.** `ca539ec` replaced sixteen tag references with
commit shas and narrowed the workflow token to `contents: read`, on the argument that a tag is a
movable pointer and the code it resolves to runs on this tree with that token. Three lines in the
same file were the identical defect in another spelling: `pip install --quiet pytest pytest-cov`,
`pip install --quiet pytest`, and `pip install --quiet ruff mypy`. Between them they name five
package specifiers — four distinct packages — and install ten, eight and eight respectively: the
transitive closure is resolved fresh on every run,
from whatever PyPI serves at that minute, and it executes with the same token the sha-pinning was
performed to bound. Pinning half the supply chain and leaving the interpreter's half open is the
shape of defence this repository exists to name.

**Decision: each job installs a compiled, hash-checked set.** `requirements/ci-tests.txt`,
`ci-shipped.txt` and `ci-lint.txt` hold the full closure with a hash per artefact, compiled by
`pip-compile --generate-hashes` under the same Python 3.10 the jobs run, from committed `.in` files
that record the intent separately from the resolution. `--require-hashes` makes pip refuse anything
that does not match, which also closes the quieter case a version number alone leaves open: the
same version re-served as a different artefact.

**And `--only-binary=:all:` beside it, which is not tidiness.** `--generate-hashes` records the
digests of source distributions too, and hash-checking mode will accept one. Building an sdist runs
PEP 517 in an isolated environment whose build dependencies are fetched **without** hashes and
appear in no committed set — so the guarantee would end quietly, one layer below where it is
written, on the day some project stops shipping a wheel for the runner's platform. Every pin here
resolves to a wheel today, so the flag changes no outcome now; it is there so that when it would,
the run REFUSES instead of widening. Named by Fable, which also declined to call the branch closed
merely because it is currently asleep.

**Three files rather than one, deliberately — and the price, which the first draft omitted.**
`shipped` runs the dist-dependent assertions and has no use for a coverage plugin; `lint` shares
nothing with either. One shared file would install each job's dependencies on the other two jobs'
behalf, and the widest install would become the floor for all three. The cost is that `pytest`,
`tomli` and `typing-extensions` are each pinned in more than one file, so a bump applied to one and
not its siblings leaves two jobs measuring the same tree with different instruments, both green and
only one current. That is a fact about the tree, so it is not left to care: `verify_pip_pins.py`
fails on a package pinned to different versions across the sets.

**The update policy, which is the half worth writing down.** A hash set moves by a deliberate edit
— change the `.in`, re-run the `pip-compile` command recorded in its header, commit both files —
and never by CI upgrading itself. There is no scheduled refresh and no `--upgrade` anywhere in the
workflow. The consequence is intended and is stated here so that nobody repairs it in a hurry: **CI
that goes red because a set has gone stale is the ratchet working as designed, not a flake.** The
red is the notification that somebody else's release schedule has moved under this tree, and the
fix is to read what moved and decide, not to unpin the line that reported it. A hash set quietly
refreshed by a machine would restore precisely the property being removed here, while leaving the
`--require-hashes` flag in place to vouch for it.

**Why this does not repeal D-26's unpinned `wrangler@4`, though it looks like it.** That decision
floats a tool that talks to somebody else's API and holds our deploy credential, on the ground that
security updates to it are worth more than the breakage a float can cause — *provided the breakage
is caught by measurement*. The proviso is what separates the two cases. Wrangler's output is
measured after the fact by `scripts/verify_live.sh` reading the live site, so a bad float is caught
by an instrument that does not depend on the float. The three sets here ARE the instruments: a
floating pytest, ruff or mypy changes what the gates themselves report, and there is no outer check
that would catch it — a drift in the measuring tool arrives as a verdict about the tree.

*Float what is measured; pin what measures* is the short form, and it is a rule of thumb rather
than a law, because this very workflow does not obey it. `node-version: "22"` floats across minors
and runs the intake gate and the site build; `python-version: "3.10"` floats across patch releases
and is the interpreter every gate executes on; `ubuntu-latest` floats entirely. All three measure,
and none is pinned. They are named here rather than left for a reader to notice, because a maxim
that the file it is written in contradicts is the kind of rule that gets quoted at the next
decision and is not true of this one. What is claimed is narrower: **the three sets pinned here are
the tools whose drift arrives disguised as a finding about our own code**, and that is the class
this decision closes. The runner floats are a separate, unclosed exposure and belong in
`FINDINGS.md`, not in a sentence that implies they were handled. Found by Fable.

**mypy is the concrete case, not a hypothetical.** The `lint` step goes RED when mypy reports ZERO
errors, because that is the condition `.github/workflows/README.md` promised would end its advisory
state (D-22). Unpinned, a mypy release that got BETTER at nothing in particular could turn `main`
red on an afternoon when nobody touched this tree, and the reader would meet a red build whose
cause is not in the diff. Pinned, that transition can only be reached by a hand that moved the set.

**Measured before it was committed, on this host, under Python 3.10.12 — the jobs' own version.**
All three sets install under `--require-hashes --only-binary=:all:`; the pinned `ruff==0.16.4`
reports `All checks passed` on `src tests scripts`; the pinned `mypy==2.3.1` exits 1 with 40 errors,
which is the advisory branch and not the zero-error branch that would redden the step; the full
suite under the pinned `pytest==9.1.1` and `pytest-cov==7.1.0` is 642 passed, 1 skipped, coverage
92.87% against a floor of 70. A pinning commit that had never run the pinned tools would be
asserting compatibility rather than measuring it — so the transcript is kept, in
`evidence/GREEN-005-the-pinned-toolchain-was-run-before-it-was-committed.txt`, rather than the
numbers being recited here alone. The first draft of this paragraph recited them alone, and Fable
refused the change for it: the identical refusal, on the identical ground, that produced GREEN-004
one commit earlier (L-30).

**Armed by `LAW-CI-PIP-HASH-PINNED`, after the first draft argued no gate was possible.** That
argument said the property that matters — the set was moved by somebody who read what changed — is
a fact about an edit rather than about the tree, and filed the whole decision under L-8's honestly
gateless class. Half of it was true, and the half that was true was being used to carry the half
that was not. Whether a bump was WISE is unreadable by any checker and stays prose. Whether
`--require-hashes` is still on the line is a fact about the tree, readable offline, and able to go
red — and it needed arming for exactly the reason `test_actions_pinned.py` gives about its own
subject: **a one-time edit drifts back.** Worse here than there, because no other gate in this
repository could see it happen — `tests/test_door_matches_ci.py` classifies any step beginning
`pip install` as runner preparation, so the reverted line would be waved through as setup by the
gate built to catch steps that slipped the table. `scripts/verify_pip_pins.py` holds the shape:
the flags are present, the requirements file is a path inside this tree rather than a URL, it
exists, every pin in it carries a hash, and shared packages agree across the sets. The red run
where the reverted line is actually caught is
`evidence/RED-027-a-pinned-line-is-one-edit-from-unpinned.txt`. Refuted into existence by Fable.

**And then the gate itself was refuted, which is the part worth keeping in the record.** Its first
version could be walked past four ways, two of them found by Fable and two implied by those: a
trailing `#` comment, whose text the reader kept and bash discards, so
`pip install evilpkg  # --require-hashes ... -r requirements/ci-tests.txt` reported no problem
while the runner installed one unpinned package holding the token; the same trick with a later
`echo` on the line vouching for the install; and two block-scalar headers - `run: |2` and
`run: &a |` - that the hand-written reader did not recognise, so it skipped the body IN SILENCE and
reported clean over an empty measurement, with the vacuity guard held quiet by the three genuine
installs elsewhere in the file. A gate blinded without a signal is invariant 1 pointed at the
instrument. All four are captured before and after in
`evidence/RED-028-a-gate-that-could-be-walked-past-four-ways.txt`. The lesson is the one this
repository keeps paying for: **a substring test run against text that is not the command** — the
same shape `tests/test_door_matches_ci.py` was burned by twice before this, arriving by a third
route in the gate written with those two lessons in view.

**Then the repair was refuted, and that is where the record stops being flattering.** The next round
found three more ways past, TWO OF THEM INTRODUCED BY THE REPAIR. Its two new loops each tracked
quotes and neither knew about the backslash, so `\"` inverted their idea of quoting against bash's —
one blindness producing a false GREEN on an unpinned install hidden behind `echo "\"" ;` and a
false RED on an honest `grep -r "\"" logs && pip install --require-hashes ...`. The false red is the
more expensive of the two: a gate that reddens correct work teaches people to route around it (L-5).
The third was `run: | # collect coverage`, a block header carrying a comment — the silent-skip class
RED-028 had just declared closed. Captured in
`evidence/RED-029-the-repair-carried-the-same-defect-one-layer-down.txt`; the two loops are now one
`_lex`, because that was one rule written in two places with two identical holes (L-2).

**And an eighth, in the round after that — command substitution.** `echo $(pip install evilpkg)
--require-hashes ... -r requirements/ci-tests.txt` holds no `&&`, `;` or `|`, so the splitter handed
the whole line over as one command carrying every flag, while bash ran the install inside the
substitution. The same vouching class as before, in the spelling the splitter did not know — and not
an exotic one: `$(` was already in `tests/test_door_matches_ci.CHAINS`, put there when the trick was
found against the door. The lesson had landed in one gate and not the other. Three spellings are
closed (`$( )`, backticks, and a substitution inside double quotes, which is why the lexer now
answers "is this quoted" and "would a substitution open here" separately), together with a false RED
in the same round: an honest install wrapped over two lines with a trailing backslash was read as
two commands and reddened. See
`evidence/RED-030-the-eighth-way-past-and-the-honest-line-it-would-have-reddened.txt`.

**What is claimed about this gate, at the strength the artefacts support.** Eleven named bypasses are
closed and each has a test that fails without its fix. That is not a proof that an eighth does not
exist, and the honest expectation is that one does: this is a hand-written approximation of a shell
lexer inside a hand-written approximation of a YAML reader. What the law buys is not impossibility
but cost — the ORDINARY regression, somebody editing `--require-hashes` off a line, now fails the
build instead of passing unnoticed. THREE consecutive rounds of refutation landing on the INSTRUMENT
rather than on the change is worth recording as its own finding: the tool written to catch claims
stronger than their artefacts made one about itself each time, and each time what was wrong was a
closing sentence rather than a measurement. The previous draft of this paragraph expected an eighth
bypass to exist; it was found in the next round, which is the best argument available that the
qualifier is load-bearing and should not be edited out by whoever patches the ninth.

**What the gate does NOT check, since the split is the whole of its honesty.** That a
`--hash=sha256:...` is the digest PyPI really serves is not verified from this tree — and unlike a
sha beside a tag comment, it does not need to be. A wrong action pin looks exactly like a right one
and defeats review; a wrong hash is recomputed and REFUSED by pip on every install. Truth is
enforced by the installer at run time, and what is left for a gate is the one thing the installer
never sees: whether it was asked to enforce anything at all.

## D-31. The `web-1.0/` freeze is confirmed, and the road out of it is a revocation, not a cleanup

**Numbering.** This entry was commissioned as "D-30". By the time it was written that number was
held by the CI toolchain decision above, which was authored by the task that measured it and lands
in the same push. Renumbering another decision's record so that a brief's wording comes out right
would make the brief the authority over the file. The next free number is taken instead, and the
reason is written here rather than left to be reconstructed — the same device D-28 used for the
D-27 gap.

**Decision.** `web-1.0/` stays, and the freeze recorded in D-21 is confirmed as of 2026-08-24. A
task of that date proposed deleting the directory as dead and, to its credit, set its own stop
condition: if one tracked file still refers to `web-1.0`, the deletion is off and the reference is a
finding. Three were found. The stop condition fired on the task's own terms.

**The half of the proposal that held.** The build genuinely does not reach the directory.
`~/orchestra/deploy.sh` runs the build in `web/` and publishes `web/dist`; the string `web-1.0`
does not occur in it. `web/wrangler.toml` sets `pages_build_output_dir = "dist"` and names nothing
else. `grep -rn 'web-1\.0' .github/` is empty — no workflow refers to it.

**And the live site was distinguished by a FEATURE, not by a status code.**
`web-1.0/src/pages/Registry.tsx:28` still carries the withdrawn sentence "Every business that has
been measured", while `https://provek.dev/registry/` serves the corrected one computed by
`web/prerender.mjs`: "Every business submitted to the method… 8 records, of which 4 could not be
measured at all." A 200 would have proven only that the origin answers; the sentence proves which
tree the served bytes were built from. Control: `/` → 200, so the source was talking to us.

**The hole that no amount of grepping could close, and the measurement that did.** A build can be
configured in the Cloudflare dashboard, outside every file in this repository — and a setting that
does not live in the tree cannot be refuted by reading the tree. So it was measured rather than
argued: `GET /accounts/<omitted>/pages/projects` → HTTP 200, and the `provek` project reads
`source: null`, a `build_config` carrying `destination_dir` alone — no `build_command`, no
`root_dir` — and a latest deployment whose trigger type is `ad_hoc`. The Pages project is not
connected to a git repository at all: Cloudflare neither clones this repository nor builds it, so
there is no path by which any dashboard setting could reach `web-1.0/`. The account id is omitted
above on purpose, and so are the token's scopes; neither is needed to check the finding, and this
file is written to be read by strangers.

**The three anchors, by name, because "there are references" is not a measurement.**

1. `web/prerender.mjs:113-116` — a deliberate L-2 anchor recording that a third copy of the
   withdrawn sentence survives at `web-1.0/src/pages/Registry.tsx:28`. It is a comment and changes
   no build, but it is not incidental: L-2 is about knowing where every copy is, and this is the
   note that tells whoever rolls back to `web-1.0` what they restore along with the layout. The
   deletion task named `prerender.mjs` in its own stop condition and made no exception for comments.
2. `SPEC.md:436` — the repository layout: "`/web` working app, `/web-1.0` frozen clone, `/refs`
   reference captures." A speaking document of the project, not a stray mention.
3. `DECISIONS.md:667` (D-21) — where the freeze is called deliberate and the directory explicitly
   "left alone", with the mandate UI still standing in `web-1.0/Apply.tsx` named as a property of
   the rollback rather than a defect in it.

**The directory is also not dead.** `web-1.0/FROZEN.md` gives it a function: the phase-2 rollback
point of the design method, existing so that phases 3-5 — palette, type, states, motion — can be
compared against something rather than against a memory. Those phases are not done. A baseline is
useless the moment it is edited, which is why the same file says to edit `web/` instead; a baseline
is equally useless once deleted.

**Therefore the road out is a revocation, not a cleanup.** Removing the 28 files repeals three
recorded places at once, and this project reverses decisions by Fable's verdict or the operator's
ruling, never by the hand of the executor who finds them inconvenient. If the freeze is to end, it
ends as: the operator revokes it; a DECISIONS entry records the revocation and its reason; the
layout line at `SPEC.md` §11 is edited; and the L-2 anchor in `web/prerender.mjs` is removed in the
same change, because an anchor pointing at a path that no longer exists is worse than no anchor —
it is a rule surviving its own repeal, which is precisely what L-2 names. Only after those three is
deleting the files bookkeeping. **No document in this repository calls `web-1.0/` a directory to be
deleted, and none should.**

**The argument against the freeze, raised here rather than left for a critic.** Deletion would
*not* have been irreversible, and the first draft of this reasoning had that wrong. `FROZEN.md`
pins commit `82d8a29`, which does not contain `web-1.0` at all — in it the clone sat at `web/` —
and is held only by three stale remote-tracking refs that no longer exist on the remote. But
`web-1.0` entered the CURRENT published history in the first commit `bacea9c` and has not changed
since: `git diff --stat bacea9c HEAD -- web-1.0` is empty. The content is recoverable from public
history at any commit. So the freeze does not rest on "we could never get it back". It rests on the
recorded function and the three anchors, which is a weaker-sounding basis and the true one.

**Alerts `#6` and `#7` stand dismissed on this same basis, and that is now measured.** Read with
the token the door uses: both `state=dismissed`, `dismissed_reason: won't fix`, rules
`js/remote-property-injection` and `js/client-side-request-forgery`, each dismissal comment naming
`web-1.0/` as the frozen rollback point that the build excludes and the site never serves — and
each careful to say only that the frozen copy is not shipped, not that the live tree is clean.
`docs/ALERT_TRIAGE.md:26` carries the same basis in the same words. Worth recording that an earlier
attempt to read alert `#6` returned HTTP 401 against a control of 200 on the repository endpoint,
and was logged as `unreadable` rather than as "closed" or as zero. That 401 was a fact about the
credential in hand, not about the alert. Invariant 1 held in both directions here: the refusal was
not written down as a zero, and it was not left standing as one once an instrument existed that
could read it.

## D-32. The workflow files are read by a YAML parser, and `pyyaml` enters the pinned set by decision

**Decision.** `tests/test_workflows_parse.py` calls `yaml.safe_load` on every
`.github/workflows/*.yml` and `*.yaml` on every push and at the door, through
`scripts/verify_workflow_yaml.py`. `pyyaml` is added to `requirements/ci-tests.in` and
`ci-tests.txt` is recompiled — this entry is the deliberate edit D-30 requires for a hash set to
move, written in the same commit as the edit. `LAW-WORKFLOWS-PARSE` arms it.

**The fork this closes, and it was left open on purpose.**
`evidence/RED-031-seven-green-gates-and-a-workflow-that-never-parsed.txt` ends by naming the gap and
declining to close it, because closing it means either a new dependency in a hash-pinned set — which
D-30 says moves by a decision and not by a repair — or a second hand-written rule bolted onto the
scanner whose permissiveness IS the finding. The judge took the first. So the set grew by one line,
and the line has an entry.

**What was measured, on `66f61ea`.** Seven green gates on this host, 642 passed, coverage 92.87% —
and `main` red in the same second the push landed. `--only-binary=:all: ` sat in a plain scalar,
`: ` ended the key, and the run was created and concluded in the same second with ZERO jobs. Nothing
in the workflow failed because nothing in it started, and a startup failure publishes no check run
at all: `/commits/66f61ea/check-runs` answered with three successes for a commit whose gates were
red. `total_count: 3` looked like data and was absence.

**Why the existing gates could not have caught it, which is the whole of the argument.**
`scripts/verify_pip_pins.py` read all three broken lines correctly and reported them hash-pinned. It
still does, byte for byte, after the repair. It was not fooled and it did not lie — it reads the
file with what D-30 calls in its own words "a hand-written approximation of a shell lexer inside a
hand-written approximation of a YAML reader", and that approximation was WIDER than the machine it
stands in for. That direction is the silent one: a stricter approximation announces itself as a
false red on a working file, while a looser one stays quiet until the real parser refuses a document
seven gates have already blessed. Written up as **L-31**, and held in executable form by
`test_the_scanner_that_passed_the_broken_file_still_passes_it`, which runs BOTH readers over the
same fixture and asserts the disagreement — so the day somebody widens the hand-written reader, the
finding has to be deleted deliberately rather than quietly outlived.

**What this gate does NOT claim, since the split is the honesty of it.** PyYAML is not GitHub's
parser: GitHub reads these files with its own implementation, and PyYAML implements YAML 1.1 where
most modern parsers implement 1.2. A file accepted here is therefore not proven to be a file GitHub
accepts, and no schema is checked by anything in this tree — a misspelt key, an unknown `runs-on`,
a job that cannot start, all parse perfectly and fail where this gate cannot see. A duplicated
`jobs:` key parses too, and PyYAML silently keeps the last one; that boundary is asserted as a
control in the suite rather than left for a reader to assume otherwise.

**And the residue is not merely a smaller version of the same risk — for one class the T-S2
measurement trap stands entirely intact.** A `gates.yml` that PARSES and breaks GitHub's workflow
*schema* reproduces the RED-031 symptom in full: a startup failure, zero jobs, and a
`/commits/{sha}/check-runs` that answers with the other workflows' successes and cannot show the
failure at all. Neither the door nor CI sees that class, so `actions/runs?head_sha=` remains the
only instrument that can close "is `main` green" for it — which is why every push touching this
directory is measured that way rather than by a check-runs reading. Saying only "we do not check the
schema" would have left a reader to infer that the rest of the safety net catches it. Found by
Fable. What is bought is the class
of defect that was actually paid for — a document that is not well-formed YAML — refused at the
door instead of on `main`. Closing the residue means running GitHub's parser, which is not on this
host, so it is named here rather than covered by the word "parses".

**Where this gate bites is NOT where the others do, and that is the sentence most likely to be
misread out of this entry.** In CI the test cannot catch a broken `gates.yml`: a workflow that does
not parse runs no job, so the job that would run the test never starts — the defect deletes its own
detector, which is exactly how `66f61ea` produced seven green gates and three green check runs. What
the CI copy does catch is a broken `codeql.yml` or `scorecard.yml`, separate documents whose failure
does not stop the `gates` workflow. The copy that catches the RED-031 case is the one at the DOOR,
which runs the suite while the push does not yet exist. That inverts this repository's usual
arrangement — `gates.yml` opens by saying the door depends on the pusher's discipline and CI does
not — and the inversion is stated here because "the gate runs in CI" would otherwise be read as a
protection it structurally cannot give.

**Three states the gate reports rather than folding into a clean line.** An ABSENT workflow
directory, a workflow directory holding NO workflow file, and a file that cannot be decoded are each
their own reading. So is an absent PyYAML: `parse_problems` says `not_measured` and deliberately
does NOT say `DOES NOT PARSE`, because every fixture in the suite asserts that marker — without the
split, a host with no parser installed would run the whole file GREEN over documents nobody read,
which is invariant 1 arriving inside the gate written about instruments that do not measure what
they claim.

**The prose this falsified, corrected in the same commit rather than left to be found.**
`requirements/ci-tests.in` ended "NOTHING ELSE BELONGS HERE", and two test docstrings —
`tests/test_door_matches_ci.py` and `tests/test_reissue_obligation.py` — justified hand-parsing YAML
on the ground that the `tests` job installs pytest and pytest-cov and nothing more. That ground is
gone as of this entry. All three are corrected where they stand; a stale reason left in place is
what makes an inherited arrangement read as a decided one (L-2), and the copy in `ci-tests.in` was
the one that would have kept the other two sounding reasoned. **Rewriting those two hand-parsers
onto PyYAML is NOT done here** and is a named deferral rather than an oversight: each has measured
limits and fixtures around its reader, and swapping it is a change that must be watched to fire in
its own right. `scripts/ratchet_scope.py` keeps the original reason unchanged and unaffected — the
`ratchets` job installs nothing at all, so a ratchet importing PyYAML would not run there.

**The pin was run before it was committed**, by the standard D-30 set for itself and GREEN-005 kept:
`requirements/ci-tests.txt` was recompiled under this host's Python 3.10.12 — the jobs' own version
— with `pip-compile --generate-hashes`, and the diff is ONE package. Every other pin is byte for
byte what it was, because the set was compiled without `--upgrade`; a recompilation that quietly
bumped pytest would have moved the instrument this repository measures itself with, under cover of
a decision about a parser. The install under `--require-hashes --only-binary=:all:` and the suite
run under it are in
`evidence/GREEN-006-the-parser-was-installed-from-the-pinned-set-before-the-gate-relied-on-it.txt`.

**A divergence between the door and CI, named rather than closed.** CI installs `pyyaml==6.0.3`
from the hash-pinned set; the audit host carries PyYAML 5.4.1 from the system packages, and
`scripts/push.sh` runs the suite against whatever the host has. So the door and the arbiter parse
with two different parser versions. It is the same shape as the node divergence already recorded in
`push.sh` — 20.20.2 here, 22 there — and it is named for the same reason: the door/arbiter gate
matches commands, not toolchains, and is blind to this by construction. Both readings are measured
and the RED-031 form is refused by both.

**The red run is kept, and it is the real one rather than a mutation of the subject.**
`evidence/RED-034-*` restores the exact three lines `66f61ea` shipped into this tree's `gates.yml`,
takes both readings on that file — `verify_pip_pins.py` clean, this gate red at line 128, column 69
— and then mutates the gate itself, each edit in the permissive direction, to show the suite can
fail (L-21). The generator is checked in beside it so the run can be repeated rather than believed,
and the counts are kept in the artefact rather than recited here.

**That sentence read "six ways … each assertion in the suite is load-bearing" until Fable counted,
and both halves were wrong.** There were seven mutations, not six — the decision entry disagreeing
with the artefact it cites, which is the one thing this file exists not to do — and four tests were
killed by nothing at all. Two rounds of repair followed. Five mutations were added: the parser's
message dropped so the gate can say a file fails and not WHERE, and its LOCATION dropped separately;
the clean line stripped of the names it read; the directory listing replaced by a remembered
filename; and an absent parser folded into a clean tree ONE LEVEL ABOVE the function that reports
it — an edit no test on a host that HAS PyYAML could have seen, which is every host that runs the
suite. Two tests were SPLIT, because an assertion sitting under an earlier `assert` in the same test
cannot be shown to matter by an instrument that reads node ids out of pytest's summary: the mutation
dropping only the parser's position killed the identical test as the one dropping its whole message,
the generator refused the pair as indistinguishable, and splitting the test was the repair.
Declaring the granularity unreachable would have been the easier one.

**What is still uncovered is COUNTED in the evidence file**, as a subtraction over pytest's own
collection. Three tests survive: the acceptance control, which a permissive-only generator can never
legitimately kill; a stated boundary reachable only by a STRICTER edit; and a fact about
`requirements/ci-tests.txt` rather than about the gate. The unit is TESTS, and that limit is written
at the foot of the evidence file instead of being papered over with the word "assertion".

**The guard on that list is an instruction to a person, and calling it more than that was the last
thing Fable took out.** The generator refuses to rewrite its artefact while the measured set differs
from the one it expects, and the refusal names all four places these three tests are written down —
its own constant, the paragraph under the list, the suite's docstring and this entry — so a moved
list cannot appear under an unmoved explanation. But the check compares a frozenset: updating the
frozenset alone satisfies it. The previous draft of this paragraph said the explanation "cannot
outlive the measurement", which one edit to one field falsifies — an anti-drift repair making
exactly the claim it was written to end, in the entry about claims stronger than their artefacts.
It is also LATENT: nothing regenerates this evidence on a push, so between a test being added and
somebody regenerating, the drift is invisible. That is a property of a snapshot kept as evidence
rather than a defect to fix — the generator mutates its subject and runs the suite fifteen times,
which is not something a door can do on every push.

## D-33. A `git status` that warned did not measure the tree, whatever it exited

**The defect, and why nothing about it was a mistyped line.** `publishable_tree._porcelain` read
`git status --porcelain` and treated a zero exit as a reading of the whole tree. It is not one: a
file under a directory the process cannot enter makes git print `warning: could not open directory
'sub/': Permission denied` to stderr, **exit 0**, and leave that subtree out of stdout. So the gate
that decides whether the unattended publisher may ship received an empty list and called it a clean
tree — invariant 1's substitution, `check_did_not_run` arriving as `nothing_qualified`, inside the
gate this project built to catch exactly that. Measured on this host and kept in
`evidence/RED-035-*`: with an untracked file inside a `chmod 000` directory, `classify` returned
PUBLISHABLE and the process exited 0, and `deploy_label` — which imports the same reader — labelled
that tree with the commit's short sha and `COMMIT_DIRTY=false`.

**The fork this closes was already recorded, and by the hand that could not close it.** D-26 names
this limit in its own "what is NOT claimed" paragraph, `evidence/RED-023-*` measured it during T-H2
run 4, and both left it standing on the stated ground that the module belongs to the SCHEDULER's
gate and repairing another task's shipped gate in passing is not this project's habit. It went to
`~/orchestra/FINDINGS.md` for the judge. This decision is the execution of that referral, not a
fresh opinion about it.

**Decision: a non-empty stderr from `git status` is `check_did_not_run`, and the exit code does not
overrule it.** `_porcelain` returns its third state, the two gates built on it return UNREADABLE,
and git's own sentence is printed above the refusal rather than summarised — an UNREADABLE with no
cause sends the operator hunting for uncommitted work that is not there, and a refusal nobody can
act on is the one that gets routed around (L-5).

**Decision: the stderr text is NOT parsed, and the price of that is a false red we accept.** A
condition matching `could not open directory` would make this gate's coverage a list of the
warnings somebody thought of, and the warning that publishes an unread tree is by definition the
one nobody thought of. So any stderr at all is a refusal, and a warning with nothing to do with
readability — a transient filesystem fault, a future git printing an unrelated note — reddens a
cycle over a tree that may be perfectly publishable. That is accepted, and the third state is
precisely why it can be: what the red announces is that THE INSTRUMENT stopped, not a verdict that
the tree is unfit, and it prints git's reason for stopping beside it. It costs one cycle and sends
the operator to a real fault. The false GREEN it replaces publishes content nothing opened, says
nothing at all, and does it again tomorrow. Nothing here treats a false red as free — L-5 is about
exactly that — which is why the trade is written down at the line that makes it, in `_porcelain`'s
docstring, rather than left for the person the gate stops.

**Consequence, and it is the one that could have been shipped silently: a guard in the neighbouring
gate lost its subject.** `deploy_label`'s clean path re-reads every file `git ls-files` names, and
RED-023 run 8 proved that reading load-bearing by deleting it and watching a case go red. After
this change that case is caught one layer earlier, so the same deletion would have gone green
again — a guard whose removal nothing notices is already gone, which is run 8's own sentence turned
on the repair. The replacement case is in the same commit: a file git reports clean, with an EMPTY
stderr, over bytes it never opened (`assume-unchanged`, or any stat cache git trusts). Both cases
are kept, because they fail for different reasons, and the mutation proving each is in
`evidence/RED-035-*` parts 3 and 4.

**What is still not measured, named rather than implied.** The reader refuses every unreadable path
git NOTICES; the digest opens every path git LISTS. Neither sees a filesystem that answers without
error and without the truth, and neither claims to. `evidence/RED-023-*` is not edited — D-28 — and
the four sentences in it that this decision falsified are answered in a dated erratum beside it.

## D-34. A control that answers zero has proven nothing, and the word for that is not `instrument_blind`

**Measured 2026-08-24 20:33 UTC.** `~/orchestra/bing_probe.py` had published, since 2026-08-21,
`query_stats: {"count": 0, "state": "instrument_blind", "subject_call": "ok"}` for `provek.dev`, and
a ruling was built on that snapshot which called the `LAW-NOTES-CEILING` release condition
unreachable. The instrument was never blind. One key, one code path, the account's two sites side by
side: `GetQueryStats` answers **64 rows / 402 impressions / 18 clicks** at `defycard.com` and 0 rows
here; `GetRankAndTrafficStats` answers **985 impressions / 29 clicks** there and 0 rows here;
`GetCrawlStats` answers 6 rows there and 0 here. Every one of those rows is in
`~/orchestra/evidence/MEASURED-B10-the-control-pair.txt`, taken by a script that can be re-run,
because until Fable refuted this decision the numbers existed only in a terminal. `provek.dev`'s
zeros are real at the grain each call reports on: no row qualified for any of those reports.

**What those zeros do NOT say, and the first draft of this decision said it six times.** They do not
say "Bing has not crawled the site". That is a mechanism invented to sit on top of a zero (L-30),
and it is contradicted by a field in the same snapshot: `sitemap_accepted` carries
`crawl_status: Success` and `url_count: 13` — and D-24 above says of that very number, in its own
words, that it is "a number Bing could not hold without having fetched and parsed the file". Bing
demonstrably reaches this origin. What is measured is that no crawl, query or traffic row qualified
for a report, which is what `nothing_qualified` says and all it says. The same restraint applies to
the word "real": a proven-capable call still reports at its own grain, and the control proves it —
`GetQueryStats` totals 402 impressions where `GetRankAndTrafficStats` totals 985 in the same minute,
so two of the three `BLINDNESS_MECHANISMS` (a reporting threshold, differing windows) are measurably
active on a call whose capability is not in doubt. Fable found all of this by reading the artefact
the claim cited.

**One corroboration in this decision is not ours, and the first draft published it as though it
were.** The T-B10 brief REPORTS that the 985 and the 29 agree to the unit with the operator's
snapshot of the Bing web cabinet — and that snapshot has never been on this host, in `evidence/` or
anywhere else. The agreement is what would turn a reading *through* the instrument into a reading
*of* it, so it is the load-bearing sentence of the diagnosis, and it was restated in five places as
a measurement taken here. It is now attributed to the brief in all five. What this host measured is
the control pair; what it is told is that the pair matches the cabinet. Fable found it, and the
distinction is the whole subject of this repository.

**The defect is not the one the shape suggests, and naming it correctly is most of the decision.**
The call was right, the parameters were right, and the control pair was already being run — this
probe honoured L-10 from the hour it was written, and its docstring says so. What was wrong is that
a control which answered ZERO was treated as having settled the question. Two zeros are the single
outcome that establishes nothing: they are equally what a blind call and an empty control site
produce. The state published for them, `instrument_blind`, is a positive claim that the call cannot
see the quantity — asserted from an absence of evidence, which is this project's founding defect
committed by the instrument built to catch it.

**It was refuted in its own output, one line down.** `counted()` computed
`control_proven_capable: false` and wrote it into the record directly beneath the word `blind`. The
distinction existed, was measured, was serialised, and was destroyed by the name chosen for the
state — L-29 exactly, where the store learned to tell two states apart and the instrument printed
one word. Everything needed to refuse the false ruling was in the file the ruling cited.

**Decision: a state that names the instrument must carry evidence about the instrument.** The
classification is now taken from the control pair in three branches rather than two:

* the control returned rows → the call is **proven** able to see this quantity, and the subject's
  zero is `nothing_qualified`, a statement about the subject;
* both empty, **and an independent witness reading shows the control site holds the quantity
  anyway** → `instrument_blind`. Blindness demonstrated, not inferred. The witness for the query
  stats is `GetRankAndTrafficStats` at the control, a different call reading the same underlying
  quantity at a coarser grain;
* both empty, no witness → `capability_unproven`. A not-measured state that says which silence it
  was: no witness declared for this counter, or one declared that could not be read. `link_counts`
  is the standing instance — both inbound-link calls read empty at the control, so nothing on this
  account can show those calls able to see a link, and that counter is undecidable at zero. Saying
  so is the finding; inventing a witness for it would not be.

**WHY THE CONTROL WAS EMPTY ON 2026-08-21 IS `not_measured`, and it is left that way.** Nothing on
this host recorded Bing's side that morning. What CAN be established is that the call did not
change, and the first draft of this paragraph reached for the wrong evidence: it said the file was
"byte-identical" to the one that read 64 rows three days later, which is a comparison nobody
performed and could not have — `~/orchestra` had no version history until 2026-08-24 04:32, so no
copy of the file as it stood on the 21st exists. What was actually observed is an mtime six minutes
older than the snapshot, dressed in the language of a byte comparison. The real evidence is better
and was sitting one command away: commit `20b24cf` holds the pre-repair `counted()`, its branch is
literally `else: state = "instrument_blind"`, and the field structure it emits matches the
2026-08-21 snapshot exactly. Fable found the overstatement — inside the decision that is about
overstatements, which is where they are hardest to see. A mechanism assembled now from
what would plausibly be true is a claim like any other (L-30), and this decision is about a claim
assembled exactly that way. What the pair DOES establish is the load-bearing thing: a control's zero
is not durable, so a single zero from it may never be promoted into a statement about the instrument.

**The gate is armed outside this repository, and that is a limit rather than an arrangement to be
proud of.** A Bing Webmaster client answers to no `ABI-*` requirement (D-17, L-11, L-12), so the
subject, its falsification harness (`~/orchestra/bing_counted_check.py`, eleven worlds, seven
distinct states) and the red runs (`~/orchestra/evidence/RED-B10-*`) all live beside the log they
write. Three mutations are recorded, each applied as a textual edit to a copy of the real artefact
rather than to a paraphrase of its branch chain: deleting the branch that decides a real zero, so a
control carrying 64 rows still reports the instrument blind; restoring the pre-T-B10 rule, so two
zeros report blindness again; and asserting `control_proven_capable` instead of measuring it. The
generator refuses to write the evidence unless each anchor matched exactly once, the instrument
control stayed green, and no two mutations killed the same set of checks — L-21, L-28 and L-26 as
three executable preconditions. A fourth mutation strips `compatible_mechanisms` from the one state
that names the instrument, and it exists because Fable refuted the first draft's treatment of that
caveat. The preconditions are themselves broken one at a time, on copies of the generator, in
`~/orchestra/evidence/RED-B10-meta-*` — which exists because the first draft of this decision
claimed they had been "shown to bite" on the strength of a terminal session that left no artefact
(L-26, in the paragraph asserting L-26 compliance).

**This repository holds no gate on the rule, and the honest form of that sentence is the one in
L-11.** Nothing in a clone can read `~/orchestra`, so naming a `LAW-*` here would be an anchor
pointing at nothing. What this repository carries instead is the correction, and the count of places
needing it was wrong three times — four, then five, and it is six. Four documents stated the
blindness itself and all four are amended (L-2). Two more carry the same STEP under different words,
and both were found by looking for the step rather than for the phrase, after the first two searches
had looked for the phrase. `seo/KEYWORD_BASE.md` is the fifth and is amended here: it argues that
the `bing_serp_related` capture's empty result "is a statement about the client, not about Bing" on
the strength of three control queries that all returned zero, whose capability was argued from
plausibility. **The sixth is on the live site and is NOT repaired by this task**, and it is the
fifth's child rather than its sibling.
`web/notes/src/not-measured-is-not-zero.md` — the published note whose subject is absence — carries
that sentence verbatim, because the note was written FROM the paragraph above:
`~/orchestra/notes_topics.json` pins `seo/KEYWORD_BASE.md` lines 100–135 as this note's source
material, and the defective bullet sits inside that range. That is this decision's own rule broken
in public: zero controls establish nothing, and the honest state is a statement about nobody. The
conservative half of that section is sound — the source contributes no keys and no zeros — and the
sentence over it is not.

**The parenthood is the operational part, and it turns a deferred repair into a precondition.** A
re-capture that reads the pinned material unchanged reproduces the defect word for word — the
precedent is T-C6 — so the erratum went into `KEYWORD_BASE.md` NOW rather than being left to the
task that re-captures. `FINDINGS.md` recorded this as a check to perform "at re-capture time"; Fable
pointed out the check costs one `grep` and its answer was already yes, which is the difference
between deferring a repair and deferring the question of whether one is needed.

Repairing it is a separate task and the reason is not that it is hard. A note's prose is captured
once from a model and its provenance is published on the page, so a hand-edited correction would
falsify the disclosure; the repair is a re-capture with a dated correction block (SPEC §"a note that
turns out to be wrong is corrected in public"), a moved body hash, a manifest re-pin and a deploy.
This task did none of that, the false sentence is serving readers right now, and it is named in
`~/orchestra/FINDINGS.md` for the judge. Naming it is not fixing it, and L-25 is the lesson about
exactly that distinction — a named blind spot is still a blind spot.

**Not decided here, and referred rather than dropped.** `LAW-NOTES-CEILING` releases on "an
indexation reading from a verified Bing Webmaster property". A reading now exists and it says zero,
so read literally the condition is met — and meeting it would raise a publishing rate at the moment
the measurement says the published pages have reached nobody, which inverts what the ceiling is for.
The ceiling stands at three and two notes exist, so nothing presses either way today. The wording is
a named finding in `~/orchestra/FINDINGS.md` for the judge and the operator; an agent that rewrote a
release condition it had just made satisfiable would be fitting the measurement to the verdict.

## D-35. The referral D-34 left open is answered: an existence test becomes a ladder, one step per link

**The problem D-34 referred rather than fixed.** `LAW-NOTES-CEILING` released on "an indexation
reading exists from a verified Bing Webmaster property". T-B10 made a reading exist, and it read
zero. Read literally the condition was met the instant the probe answered — releasing a publishing
rate at the exact moment the measurement said the pages already published had reached nobody. T-B10
refused to rewrite the condition it had just made satisfiable, because an agent repairing a release
gate right after making it pass is fitting the measurement to the verdict, and referred the question
to Fable (`~/FABLE_A_d18.md`, 2026-08-24).

**The ruling's diagnosis, which changes the operator-facing sentence.** D-18's condition is not
*unreachable* — it is *unreachable by anything this project does*. No count of pages, submissions or
days moves `GetQueryStats`; only Bing's own pipeline does, on its own schedule. A gate that nothing
the subject does can move is not a gate, it is a wall, and D-18 promised "liftable by a reading", not
"liftable by Bing's internal pipeline, someday".

**Every candidate weighed and rejected, on the live tree rather than in the abstract.** nginx access
logs — there is no origin server; `provek.dev` is Cloudflare Pages in Direct Upload mode, and even a
Cloudflare log token would buy a probe for whether an edge-log instrument exists at all, not the
instrument itself. `URLSubmission` quota — `bing_verify.py` already names its own outcome honestly as
`received_quota_charged`, never `accepted`; that is a receipt for our own act of submitting, a
reading of us, not of a reader. Page age past N days — the project already rejected dates as a
condition once (D-18's own text); age is a date wearing a costume. Search Console — a real
instrument, but an action only the operator can take, so gating on it measures the operator rather
than the tree (the same figure as L-19, applied to a release condition instead of a rollback step).

**The candidate that had never been tried: the crawl link of the same Bing API.** `bing_probe.py`
polls `GetQueryStats`/`GetLinkCounts` — instruments of the impressions link, the last one in the
chain. The same account, same key, same control discipline reaches a crawl link too
(`GetCrawlStats`/`GetUrlInfo`/`GetCrawlIssues`), and nothing had ever asked it. There was already a
reason to expect it could answer: `sitemap_accepted` carries `crawl_status: Success, url_count: 13`
(D-24) — Bing cannot report a URL count for a sitemap it has not fetched and parsed, so bingbot
demonstrably walks this domain already. Polling the crawl link, control-paired against the same
`defycard.com` property, was the one measurement standing between "the referral is answered" and
"the referral is answered `instrument_blind`, honestly."

**The construction: a step per causal link, not per date or per count.** The chain is
publication → crawl → index → impressions, and each rung is bought by observing the *next* link
rather than by waiting or by re-reading the same one harder:

* **3 → 7** opens on a control-paired `crawl_stats` reading: a nonzero row for `provek.dev` against a
  control that itself returns nonzero, proving the call can see the quantity at all;
* **7 → 15** is D-18's original condition, unmoved: a control-paired `query_stats` (impressions)
  reading. The condition is not discarded, it moves up one rung, to the link that has no instrument
  yet rather than the one that might;
* **above 15** is a separate operator decision taken at live impressions, not an automatic
  consequence of crossing 15 — D-19 already declined to build a printing press, and a ladder that
  keeps climbing on its own past the point anyone chose would be exactly that.

**The first rung reads site-wide, not per-page, and the ruling's own wording is looser than a first
skim shows.** §1 of the ruling asks for "a nonzero crawl of *our note pages specifically*", but the
only control-proven crawl instrument this account has is `GetCrawlStats`, which reports at the
property grain — a crawl of the home page would open this rung exactly as a crawl of a note would.
This is not an oversight the implementation introduced silently: the ruling's own §2 blesses the
site-wide crawl pair as "the first rung's instrument" in the same paragraph that reserves per-URL
reading (`GetUrlInfo`) for a possible *third* step, because `GetUrlInfo`'s capability is undemonstrated
— the tension is in the ruling, not resolved by it, and this decision resolves it toward the weaker
predicate because that is the only one with a proven instrument today. Recorded so a future reader
does not mistake "a crawl row" for "a crawl row of a note page": it is not, until `GetUrlInfo` is
shown control-capable and used to build a per-URL third rung.

**The numbers 7 and 15 are ASSIGNED, and this is said as loudly as D-18 says its own bounds.** There
is no reading behind either number, exactly as there was none behind 3 on 2026-08-20. What is
measured is *which step is open*; *how far a step carries* is a choice, and a ladder that looked
fully measured because it climbs on readings would be a stronger unearned claim than the flat
ceiling it replaces, so the unmeasured half is written down next to the measured one, in
`web/notes/emit.mjs` itself and not only here.

**The cap does not lift; it becomes climbable in one place it previously wasn't.** The reason three
was chosen — nothing has shown these pages reach a reader — has not disappeared, and does not
disappear at 7 either: a crawl row proves Bing fetched something at this origin, not these note pages
specifically and not that anyone found them through Bing. A date remains categorically excluded as a
condition, per the operator's standing instruction
that "~22 August" already once stood in for a true predicate rather than being one (D-18).

**What the first reading under the new rule says.** `web/notes/reach.json`, copied from
`~/orchestra/bing_probe.py`'s output by `~/orchestra/notes_reach.py` (no `ABI-*` binds it — the
probe lives outside this repository, L-11 — so the copy is the artefact this repository can hold),
captured 2026-08-24T20:49:44Z: `crawl_stats` is `nothing_qualified`, 0 rows here against 6 at the
control, `control_proven_capable: true`; `query_stats` likewise 0 against 64, with
`GetRankAndTrafficStats` at the control as an independent capability witness (985 impressions);
`rank_and_traffic` 0 against 8. Every zero is a proven-capable call reporting nothing, not an unproven
one — the distinction D-34 exists to keep. The first rung is shut for an honest reason: the corpus
stays at the floor, 3, and two note sources stand under it.

**The gate.** `NOTE_LADDER` in `web/notes/emit.mjs` is the single source — a ladder described in
prose and enforced elsewhere is the promise D-18 refused to be. `readReach` files the reading's
absence, parse failure, wrong-subject and success as four distinct states rather than collapsing any
pair (invariant 1); `stepState` requires `control_proven_capable` in both directions, so a rung
cannot open on rows nobody proved the call could see, and cannot stay shut on two zeros dressed as
`instrument_blind` — the T-B10 defect, forbidden here on the other side of the same account.
`ceilingFrom` climbs a ladder rather than checks a menu: a closed rung blocks every rung above it, so
an impressions row cannot arrive without a crawl row and skip past it. `tests/test_notes_ceiling.py`
carries its own copy of the four-number, two-counter-name ladder and diffs it against the literal in
`emit.mjs` — a single integer invites an edit to a single integer, a ladder needs both files to agree
on four numbers and two names — and separately re-derives the ceiling from the same `reach.json`
through a subprocess call into the real gate, so the test can drift from the build and still be
caught rather than trusted on its own arithmetic.

**The red run.** `evidence/RED-036-a-ladder-that-climbed-on-a-control-that-had-said-nothing.txt`,
produced by `evidence/RED-036-generator.py`, kept per invariant 5. Part one puts a fourth note source
in the tree against today's shut first rung and shows both `loadNotes()` and the suite refuse it,
then restores the directory and checks it byte for byte. Part two applies ten single-anchor mutations
to `emit.mjs` — each the shape of one way a *measurement* can be over-read where a flat constant
could only be mis-typed (a control silently dropped, a zero treated as a row, an absent file climbed
as though read, the build's ladder and the test's ladder let drift apart, a reading about the wrong
site accepted, an unread counter treated as passing, a shut rung failing to block the ones above it,
a non-numeric count accepted, two distinct silences collapsed into one name, climbing disabled
entirely so the ladder looks like a wall) — asserts each leaves the control test green and kills a
distinct set of tests, and reverts `emit.mjs` byte for byte afterward. The generator's own prose
undercounted its mutations as "eight" while the list held ten; caught while regenerating this
evidence and corrected in the same pass, because a generator whose count of its own mutations
disagrees with the mutations is this decision's defect committed by the tool built to catch it.

**Not decided here.** The publishing rate (`NOTES_PER_DAY` in `~/orchestra/notes_cron.py`) is a
separate question from the ceiling and stays where it is — raising it is untested territory the
ruling declines to touch alongside the ceiling in one move. Whether the crawl link and the
impressions link disagree the way `GetQueryStats` and `GetRankAndTrafficStats` already do (D-34) is
unmeasured for `crawl_stats` specifically and is not required to be measured for this rung to hold:
one control-proven instrument per rung is what the ladder asks for.

## D-36. The retirement banner named a path this project never called

**The task.** T-B12's brief read Bing Webmaster's cabinet banner — "Legacy SOAP and POX APIs will
be retired on August 31, 2026. Migrate to our REST APIs to avoid service disruption." — as a
statement about `bing_probe.py`'s `API` constant, `https://ssl.bing.com/webmaster/api.svc/json`,
and asked for a migration to REST before the cutoff.

**The premise did not survive contact with Microsoft's own documentation.** Fetched 2026-08-24,
`learn.microsoft.com/en-us/bingwebmaster/api-protocols` carries that exact banner directly above a
table titled "POX and JSON protocol URL Format" naming exactly two surviving formats:
`/api.svc/pox/METHOD` and `/api.svc/json/METHOD`. The retirement notice itself (the primary page,
`bing.com/webmasters/help/soap-pox-api-retirement-s0appox01`, answers this host's fetcher with an
empty body — recorded rather than papered over; quoted via
relevantaudience.com/seo/bing-webmaster-tools-soap-pox-apis-retire-august-2026/) states "All API
methods remain fully available over JSON/HTTP with identical functionality." What retires 2026-08-31
is `/api.svc/soap` and `/api.svc/pox`. `/api.svc/json` is the JSON/HTTP format the same banner calls
"our REST APIs", and it is what `bing_probe.py`'s `API`, `keyword_probe.py`'s `WMT` and
`notes_cron.py`'s `BING_API` have always pointed at. Nothing in this project ever called
`/api.svc/soap` or `/api.svc/pox`. There was no legacy transport to migrate off, and "migrating to
REST" would have been a change with nothing under it — nothing runs differently before it and after
it, which is the flattering twin of the defect this project exists to catch: not a claim stronger
than its artefact, but an artefact (a diff) manufactured to match a claim that turned out to be
about a different system.

**What was done instead of a no-op migration.** Each of the three constants now carries a guard —
`assert not any(p in API for p in ("/api.svc/soap", "/api.svc/pox"))` — so a future edit that
regresses toward either retiring path fails the import immediately rather than working until
2026-08-31 and then silently not; the full citation trail lives beside `bing_probe.py`'s `API`, and
the two siblings point to it rather than repeating it (L-2). `~/orchestra/bing_rest_transport_check.py`
took a live reading of the JSON/HTTP path on both sites of the T-B10/D-34 control pair, 2026-08-24
21:57:57 UTC: `GetRankAndTrafficStats` on the control answered 8 rows, 985 impressions, 29 clicks —
matching D-34's `MEASURED-B10-the-control-pair.txt` reading to the unit, five days ahead of the
cutoff. That script writes its own evidence file,
`evidence/MEASURED-B12-json-http-is-not-legacy.txt`, rather than rerunning `bing_control_pair.py`
over `MEASURED-B10-the-control-pair.txt`: this decision quotes that file's numbers verbatim, and a
rerun landing different figures (a rolling-window call, read days later) would have broken the
citation silently. `bing_states_check.py` and `bing_counted_check.py`, the two falsification
harnesses guarding this instrument, stay green against the edited files.

**What this does not show.** That the endpoint survives 2026-08-31 — no reading taken before that
date can show that; what is measured is that the JSON/HTTP path answers correctly today, and that
it is the path Microsoft's own notice describes as continuing rather than the one it retires. Also
not shown: why the cabinet's banner reads as broadly as it does, or whether Bing intends to widen
the retirement later — both are the operator's cabinet, unreadable from this host.

## D-37. T-B13's brief asked D-35 to answer twice; the actual gap was one unsynced copy

**Numbering.** Commissioned as a task against D-34's open referral. By the time it was picked up,
D-35 above had already answered that referral — landed the same day, one number back. The next
free number is taken rather than either decision above being reopened, the same device D-31 used
for the D-30 collision.

**The premise did not survive contact with the tree.** T-B13's brief, verbatim in
`~/orchestra/tasks/ORCHESTRA_PLAN.md`, restates D-34's finding — a literal "an indexation reading
exists" condition is satisfied by a zero, releasing the ceiling at the exact moment measurement
says the published pages reached nobody — and proposes a fix: require at least one qualifying
row for `provek.dev` from a verified property under live control before the ceiling moves. Read
against `enforced_by.yaml`, `web/notes/emit.mjs` and `tests/test_notes_ceiling.py` as they stand
today, that fix is already in the tree, and it is stricter than the brief's own proposal: D-35
replaced the flat condition with a ladder that requires a control-proven NONZERO row at each of
two separate rungs (a crawl row, then an impressions row) rather than one lift point, and pairs
every reading against a control site the same way T-B13 asks for. Writing a second decision that
restated T-B13's single-threshold version beside D-35's ladder would not have closed the gap D-34
left open — it would have given the same law two live definitions, which is the failure L-2 names,
not a repair of it.

**The gap that was real.** `~/orchestra/notes_cron.py` is named directly in T-B13's brief, and
reading it on 2026-08-25 found it still carrying D-18's retired wording in two places: the
docstring above `NOTES_PER_DAY` ("an indexation reading from a VERIFIED Bing Webmaster property")
and the `ceiling_reached` journal line's `detail` string, unsynced since before D-34 measured the
zero and untouched across T-B12's edit to the same file on 2026-08-24 21:59 UTC — after D-35
landed. Both are corrected in this task to describe the ladder and cite D-35, rather than to
restate a condition the tree no longer enforces.

**A second, more urgent defect found in the same function while fixing the first.**
`note_ceiling()` read `emit.mjs`'s source text with `re.search(r"export const NOTE_CEILING =
(\d+);", ...)`. D-35 turned that export from a literal digit into a derived expression,
`NOTE_STEP.ceiling`; the regex requires a digit immediately after `=` and stopped matching the
moment the ladder landed. Measured directly: `re.search(r"export const NOTE_CEILING = (\d+);",
pathlib.Path("web/notes/emit.mjs").read_text())` returns `None` against the live file. Every call
to `step_capture()` therefore raises `Red` before it reaches the line this task was sent to edit —
`note_ceiling()` is the first statement in that function. `logs/notes_cron.run.log` shows the cron
has not reached its capture slot since the ladder landed (today's slot is 04:53 UTC, checked at
00:56), so the break was live and undetected, roughly four hours from firing. This is not a
neighbouring task: it is the same function, in the file this task was sent to edit, whose only
purpose is to produce the number the corrected wording describes — leaving it broken while
polishing the comment beside it would itself be a claim (the comment) outrunning its artefact (a
function that cannot run), which is the defect this whole project exists to catch. `note_ceiling()`
now imports `emit.mjs` and reads its live `NOTE_CEILING` export via `node --input-type=module`,
the same pattern `tests/test_notes_ceiling.py` already uses to hold the build to its own ladder —
reading the computed value rather than re-deriving `ceilingFrom()` a second time in Python, which
would itself be the L-2 copy the function's own docstring disclaims. Verified after the edit:
`note_ceiling()` returns `3` against the live tree, matching `NOTE_STEP.ceiling`.

**What is not decided here.** The ladder's rungs, numbers and control-pairing rule are D-35's and
are unchanged by this entry. `NOTES_PER_DAY` and the publishing rate stay where D-35 left them.
Whether other files outside `~/orchestra/notes_cron.py` still read `emit.mjs`'s ceiling by
scraping source text rather than running it was not swept — `note_ceiling()` was the one this task
named and the one measured broken; a repository-wide sweep for the same pattern is a separate,
unstarted question, named here rather than assumed answered.

## D-38. Two more hand-written YAML readers are judged by a real parser, and the D-30 fork is resolved by reuse rather than a new pinned set

**Decision.** `scripts/ratchet_scope.py._load_map` (reading `requirements/ABI_MAP.yaml`) and
`scripts/ratchet_decisions.py._load_laws` (reading `enforced_by.yaml`) are hand-written scanners,
not YAML parsers, and T-S7 already named the general shape: *a checker more permissive than the
machine it stands in for will certify files that machine cannot run* (L-31). `tests/test_ratchet_scope.py`
and `tests/test_ratchet_decisions.py` now put each reader's output beside PyYAML's — on the live
file and on planted fixtures — and a divergence fails the suite. Neither reader is replaced or
retired: T-S13's brief said so explicitly, and it is the same argument D-30 makes about its own
shell lexer — the comparison is what buys the property, not a rewrite into a full parser.

**The D-30 fork, and which branch was taken.** T-S13 offered two ways to get PyYAML in front of
these two files: pin a hash-checked set for the `ratchets` CI job (D-30's own pattern, a fourth
file beside `ci-tests.txt`, `ci-shipped.txt` and `ci-lint.txt`), or run the comparison where PyYAML
already lives. The second was cheaper and is what T-S7 had already done for the same class of
defect: `verify_workflow_yaml.py`'s own docstring records that "the `ratchets` job … installs
nothing at all, by design, so `scripts/ratchet_*.py` hand-parse," and PyYAML has lived in
`requirements/ci-tests.in` since D-32, installed by the `tests` job and, on this host, present
without being pinned by `scripts/push.sh` at all (measured: PyYAML 5.4.1 on the audit host,
6.0.3 in CI). Adding a new pinned set would have meant a `pip-compile` run, a fourth file for
`verify_pip_pins.py`'s cross-set version check to hold in sync, and a new install step in a job
whose one architectural property — that it installs nothing — a docstring elsewhere in this
repository already treats as load-bearing. Writing the cross-check as a TEST instead costs none of
that: the ratchets themselves are unchanged in shape (no `import yaml` at module scope, so they
still start with zero dependencies in the `ratchets` job), and the comparison runs in the `tests`
job and at the door's own pytest step, exactly where `test_workflows_parse.py` already runs the
identical class of check for the workflow files. "Ratchets move to the `tests` job's environment"
is true of the VERIFICATION, not of the two ratchet scripts, which is the reading that keeps both
of T-S7's docstrings — the one on `verify_workflow_yaml.py` and the one on
`test_door_matches_ci.py` — true rather than retroactively wrong.

**What the comparison found, on the first file it was pointed at.** `enforced_by.yaml`'s
`LAW-EMITTED-IDS-UNIQUE` carries a `text` field quoting `url(#x)`. `_load_laws` stripped every line
on the first `#` before ever tokenising it — correct for an actual comment, blind to one quoted
inside a value — so the field had been silently truncated to `...a url(` for as long as this law
has existed in the file, with no error and no divergence anyone could see: `id`, `gate` and `test`,
the three fields this ratchet actually judges dangling-ness by, sit on later, unaffected lines, and
`text` is read by nothing downstream. That is the found instance of class L-31 rather than a
constructed one. `_strip_comment` — quotes tracked, `#` inside them left alone — closes it in both
readers; `requirements/ABI_MAP.yaml` carries no live instance (every value there is a bare
identifier, never free text), and the identical fix is applied to `_load_map` anyway, before an
instance rather than after one, because the defect is a property of the parsing strategy and not
of today's data. The red run, captured against the pinned pre-fix commit and the live file rather
than asserted, is `evidence/RED-039-a-hand-written-yaml-reader-silently-truncated-a-law.txt`.

**What the new tests prove beyond the live file, per invariant 5.** A test that only reads the
current tree and finds it clean cannot tell a working comparison from a function returning `[]` —
the same argument `test_workflows_parse.py`'s own docstring makes about itself. Both new test
modules therefore also carry a fixture the fix does not and was never meant to cover — a YAML block
scalar for `enforced_by.yaml`, a flow sequence spanning two physical lines for `ABI_MAP.yaml` —
and assert the divergence is CAUGHT, not merely that the live file passes.

**What was not done.** Neither reader is rewritten into a general YAML parser; T-S13's brief
forbade exactly that move, and D-30 already argues why a hand-written approximation kept honest by
a comparison is the right shape rather than a first draft of one. `scripts/push.sh` is unchanged:
it already runs the full suite at step 7, on a host where PyYAML happens to be present without any
`pip install` naming it, which is the same unpinned-toolchain gap D-30 names and declines to close
for `pytest`, `ruff` and `mypy` at the door — named here rather than treated as newly created by
this task, since it predates it. No new `enforced_by.yaml` entry is added, unlike T-S7's
`LAW-WORKFLOWS-PARSE`: T-S7 was arming a check with no existing home, while `tests/test_ratchet_scope.py`
and `tests/test_ratchet_decisions.py` are already the `test` of record for `LAW-SCOPE-RATCHET` and
`LAW-DECISION-RATCHET`, and `ratchet_decisions.py`'s own dangling check asks only whether a law's
gate and test files exist, not what they assert — a new law naming the same two files a third and
fourth time would be the shape L-2 already names, not a repair of it.

## D-39. Evidence artefacts now name the tree revision they were captured against, forward-only

**Decision.** `evidence/*.txt` quotes line numbers, diffs and file paths out of the working tree at
the moment its generator ran, and until T-S14 no artefact said which revision that was. The
divergence had already happened once: RED-032's citations were written against one revision and
T-S5 moved the lines they pointed at, with nothing in RED-032 itself to tell a reader the citations
had gone stale. `scripts/evidence_stamp.py` gives every `*-generator.py` a shared `tree_stamp()` -
clean, dirty, or `unreadable`, never a silent default (invariant 1, the same ABI-13-6/ABI-16-11/
ABI-33-4 cluster `src/abs_profile/measured.py` already binds, applied here to a different counter
that can just as easily lie) - and reuses `publishable_tree._porcelain` for the dirty reading
rather than a second `git status` parser (L-2), which means it inherits D-33's stderr fix instead
of reopening the hole that fix closed.

**Forward-only, per D-28.** RED-032 is not rewritten - editing an old artefact to fix it is exactly
what D-28 forbids. All fifteen existing `*-generator.py` scripts are edited instead, so the NEXT
time any of them runs it produces a stamped artefact; their already-committed `.txt` outputs are
untouched (verified: `git diff` against each was checked empty after every generator that was test-
run during this task, and the one accidental regeneration - RED-032, run once to smoke-test the
mechanism - was reverted with `git checkout --` the moment the diff showed it had rewritten
committed evidence). `scripts/ratchet_evidence.py` is the enforcing half: it fails the build on any
file under `evidence/` that carries no stamp and is not named in `requirements/EVIDENCE_LEGACY.txt`
- the sixty-seven files that predate this law, frozen once, in this commit, as an explicit list
rather than a pattern (CLAUDE.md's own doctrine for `~/orchestra`'s `.gitignore`: a wildcard
exemption for "whatever already exists" would silently cover the next hand-added file too).

**Why no new pinned set, no new push.sh step, no CI change.** The same reasoning D-38 gives for
`test_ratchet_scope.py`/`test_ratchet_decisions.py`: `scripts/ratchet_evidence.py` carries no
`import yaml`-equivalent external dependency, so there is nothing to pin, and the check runs as a
test (`tests/test_ratchet_evidence.py`) inside the existing `7/7 tests` step rather than as an
eighth door step - the same shape T-S7's `LAW-WORKFLOWS-PARSE` already established for a check with
no prior home. `tests/test_door_matches_ci.py` stays green unchanged.

**What RED-040 proves, and why it is one mutation and not several.** Invariant 5: a ratchet that
has only ever been run against a tree it already agrees with cannot be told apart from `return []`.
`evidence/RED-040-generator.py` plants one real, unstamped file directly under `evidence/`, runs
`scripts/ratchet_evidence.py` as a subprocess against the actual working tree, captures the refusal
verbatim, removes the plant, and proves the ratchet is clean again - refusing to write its artefact
unless every one of those states was true. One mutation is the right count here, unlike RED-032's
six: this ratchet has exactly one behaviour to demonstrate (an unstamped, non-legacy file is
refused), so a second mutation would restate the same fact rather than cover a distinct direction.
RED-040's own output carries the stamp it argues for, produced by the same helper - a generator
demanding a rule its own artefact did not follow would be the exact asymmetry SPEC.md §3.1 was
corrected for once already.

**What this does not do.** It does not retrofit `scripts/measure_qm1.py`, `scripts/measure_qm2.py`
or `scripts/amadeus_demo.py`, which also write into `evidence/` under a different naming
convention and were out of this task's brief (`*-generator.py` only). If any of them writes a new,
unstamped file after this commit, `scripts/ratchet_evidence.py` will fail the build over it - which
is the ratchet doing its job, not a gap in it - and wiring those three scripts to the same helper is
named here rather than assumed done.

## D-40. The door-matches-CI and re-issue-clock readers are judged by a real parser too, and neither is rewritten

**Decision.** `tests/test_door_matches_ci.py.parse_steps` (reading `.github/workflows/gates.yml`'s
job/step structure) and `tests/test_reissue_obligation.py._has_cron` (reading the same file's
`on.schedule` trigger) are hand-written scanners, not YAML parsers - the last two instances of class
L-31 named in T-S7 and closed for `ratchet_scope.py`/`ratchet_decisions.py` by T-S13/D-38. Both
files now carry the same shape of cross-check D-38 used: the hand reader's output beside PyYAML's,
on the live workflow and on a fixture chosen to exercise a limit each reader's own docstring already
named rather than a limit invented for this task. Neither reader is replaced or retired - the
argument is unchanged from D-38 and D-30: a hand-written approximation kept honest by a comparison
is the right shape here, not a first draft of a general parser, and `executable_lines` (which reads
`scripts/push.sh`, a shell script) is untouched because PyYAML has nothing to say about it.

**Where the comparison runs, and why nothing new is pinned.** The same D-30 fork D-38 already
resolved the same way: PyYAML has lived in `requirements/ci-tests.in` since D-32, installed by the
`tests` job, which is the job both of these files already run in (`gates.yml`'s `tests` job runs
`pytest tests -q ...` over the whole tree, and `scripts/push.sh` step 7 runs the identical command).
Adding `import yaml` at test-module scope costs nothing new: neither `scripts/ratchet_scope.py` nor
`scripts/ratchet_decisions.py` nor the code under test here (`parse_steps`, `_step_keys`,
`_has_cron`) imports it, so the `ratchets` job's zero-dependency property, and `scripts/push.sh`
itself, are both unchanged.

**What the comparison found: no live defect, unlike D-38's truncated law.** Both hand readers agree
with PyYAML on the actual `gates.yml` today - `test_hand_written_parser_matches_pyyaml_on_the_live_
workflow` and `test_hand_written_reader_matches_pyyaml_on_the_live_workflow` both pass unmodified.
One real quirk surfaced and was normalised rather than treated as a divergence: `_step_keys` does
not strip trailing comments from a `uses:` value (`actions/checkout@<sha>  # v4.4.0`), while PyYAML
does not see the comment at all - `_step_identity` compares only the action name before `@`, which
is the same substring `divergences()` itself uses to classify third-party actions, so the comment is
not something either reader's correctness depends on.

**What the new tests prove beyond the live file, per invariant 5.** Each file's docstring already
named a limit its hand reader was never meant to cover: `parse_steps` does not follow YAML anchors
or aliases ("a step defined by an alias reads as absent"), and `_has_cron` does not either
("`schedule: *defaults` ... cannot follow an anchor and guessing would be a false green"). Both new
suites add a fixture where the alias resolves to something live - a step, a cron entry - so PyYAML
reads it as present while the hand reader reads the same document as absent, and assert the two
readers actually diverge there rather than merely stating the limit in prose. `_has_cron`'s existing
`DEAD_CLOCKS["aliased schedule"]` fixture is excluded from the table-wide comparison for a distinct
reason: it names an anchor that is undefined anywhere in that fixture, which is invalid YAML on its
own terms and raises out of `yaml.safe_load` rather than returning a boolean a table can compare -
an exception is not the same statement as "resolves to nothing live," and the new alias fixture is
built to be valid YAML so the divergence is a boolean rather than a crash.

**Every fixture that predates this task is unaffected, because neither reader's behaviour changed.**
`divergences()`, `parse_steps`, `_step_keys`, `executable_lines`, and `_has_cron` are all byte-for-
byte what they were before this commit; only new functions were added beside them. The full suite
(751 tests, unchanged pass count) and every fixture in `test_the_comparison_is_able_to_fail`,
`test_a_step_commented_out_at_the_door_is_not_vouched_for_by_its_own_comment`, and
`test_the_clock_check_is_able_to_fail` still reads the same red on the same mutation it did before -
watched, not merely re-run, per the brief's own instruction not to change a reader without watching
its fixtures fail on the new code path.

**What was not done.** Neither reader is rewritten into a general YAML parser, for the reason both
module docstrings already gave and D-38 already generalised. No `enforced_by.yaml` entry is added:
these two test files are already the `test` of record for `LAW-DOOR-MATCHES-ARBITER` and
`LAW-REISSUE-OR-FINDING`, and a new law naming the same two files a third time would be the L-2
shape D-38 already declined to repeat.

## D-41. A stale `deploy-label.txt` was measured against a build-determinism check, not against
the live label itself - Fable's round-3 refutation caught two absences this record now names

**The gap, measured.** T-E1 opened with `https://provek.dev/deploy-label.txt` reading `8c9e969`
while `HEAD` was `0983b4b` - one commit ahead. `LAW-DEPLOY-LABEL-TRUE` (D-25/T-C7) only proves the
label matches the tree a given deploy run published; it says nothing about a tree that moved
afterward, and inventing "the label is close enough" would be exactly the unearned claim this
project exists to catch (invariant 1's cousin: a name is not the artefact).

**What actually separates the two commits.** `git show --stat 0983b4b` (T-S15) touches
`DECISIONS.md`, `tests/test_door_matches_ci.py`, and `tests/test_reissue_obligation.py` only -
nothing under `web/`. That is a reason to expect the built site is unchanged, not a proof of it;
the brief's own instruction was to measure the second branch of the criterion rather than trust the
diff.

**The measurement, and what a first draft of it over-claimed.** `web/dist` was built twice from a
clean `npm run build`: once from the working tree at `HEAD` (`0983b4b`), once from a `git worktree`
checked out at the label's commit (`8c9e969`, `web/node_modules` symlinked in - the lock files are
byte-identical between the two commits, but that fact is beside the point since neither build runs
`npm ci` at all, matching what `~/orchestra/deploy.sh` itself does). Both builds reduce to
`find dist -type f | sort | xargs sha256sum`; the two listings diff byte-for-byte equal - full
listing and combined digest recorded in
`evidence/MEASURED-003-dist-build-is-deterministic-across-0983b4b-and-8c9e969.txt`, stamped with the
tree it was taken against. A first draft of this record read that result as "the tree a fresh
deploy of `HEAD` would publish is provably the same tree the stale label already names." Fable's
round-3 refutation (`~/orchestra/fable_E1_round3_answer.md`) caught that this is false by
construction, in two named ways the digest cannot see:

1. `deploy-label.txt` is written by `deploy_stamp.sh` AFTER `npm run build` and BEFORE
   `wrangler pages deploy` - it is never produced by the build itself, so neither `dist/` above
   contains one at all. The live site necessarily still reads `8c9e969` in that exact file until a
   real deploy runs; a fresh deploy of `HEAD` would differ from the current live site in precisely
   the byte-readable file the whole task is about, and this measurement never claimed otherwise once
   named correctly.
2. `wrangler pages deploy dist` reads the Cloudflare Pages Functions bundle (`web/functions/`,
   backing `/api/apply`) from the working directory, not from inside `dist/` - `find dist` cannot
   see it, and `wrangler@4` is deliberately not pinned to an exact version (D-26), so a fresh deploy
   could bundle Functions differently from what is currently live. Not measured, not ruled out.

What survives, precisely: the STATIC ASSET TREE built from `HEAD` is byte-identical to the STATIC
ASSET TREE built from `8c9e969`, confirming via a second, independent path (build determinism
across checkout locations) a fact the source-level diff already implied. It is not proof that the
live site and a fresh `HEAD` deploy are indistinguishable overall - the label file and the Functions
bundle are named exceptions, not silently covered.

**The live sweep.** `PROVEK_BASE_URL=https://provek.dev ./scripts/verify_live.sh` read all eight
addresses (`/`, `/apply/`, `/registry/`, `/method/`, `/phase-2/`, `/api/apply`, `/method/notes/`,
`/method/notes/not-measured-is-not-zero/`) at 200/405 as required - `LIVE READING GREEN`.

**What is still open, and why this entry does not close T-E1.** T-E1's own acceptance bar also
requires T-C5 counted, and T-C5 is `submitted-unverified` pending the scheduled cron tick at 04:53
UTC on 2026-08-25 - `notes_cron.jsonl` carries no `day: 2026-08-25` entry as of this measurement
(03:04 UTC), and T-C5's own criterion forbids forcing that door. This record closes the
build-determinism branch for the pair `0983b4b` / `8c9e969` only, on its own terms and no further:
committing it moves `HEAD`, so if the 04:53 tick lands green it deploys unconditionally and the
label moves past `0983b4b` on its own (first branch of T-E1's criterion, nothing left to measure
here); if the tick lands red or does not land, `deploy-label.txt` stays at `8c9e969` but `HEAD` is
now past this commit, and this record's byte-identity claim would need remeasuring for whatever
`HEAD` is current at that point rather than being read forward as still covering it.

## D-42. A narrow, predicate-gated exception to the ornament ban - three landing-page clips, admitted below the first screen and nowhere else

**Decision.** The operator ordered three short video clips for the landing page on 2026-08-31.
Fable reviewed the request against every existing ban on manufactured or stock imagery and ruled
that a narrow exception is admissible without weakening D-07: D-07 itself already carves out
"density and restraint **everywhere except the landing**", and SPEC.md:405 gives the landing page
the one screen this project has ever allowed air. A sketch that asserts no fact about Provek and
shows only mechanism - two robots, a card changing hands - functions as a diagram, and SPEC.md
already permits diagrams; it is not the marketing photograph or the fabricated-evidence image the
prior bans were written to stop. The exception is bounded by five checkable predicates, not by
intent, exactly because "it isn't really ornament" is the argument every future request for an
image will also make.

**The five admissibility predicates. An image or clip is admissible if and only if all five hold:**

1. **Zero readable generated characters.** OCR over the raw frames is empty; every character a
   viewer reads is burned in afterward by `ffmpeg drawtext` from the committed script
   (`docs/media/FILM_SCRIPT.md`), character-for-character.
2. **No interface, document, chart, data screen, or number in frame** - nothing a reader could crop
   out and cite as evidence of a fact.
3. **Fictionality on the face of the artefact.** The characters exist nowhere real, and the page
   captions the clip "Staged scene - an illustration, not a measurement."
4. **Placement is the landing page only, below the first screen.** Zero media on any evidence
   surface: passport, registry, brief, method, notes, phase-2.
5. **No fact from `registry.json` or a passport is reproduced in pixels.** Every number a reader
   sees lives in the DOM and goes stale with the data, never with a video file that outlives it.

**Drift test, so the boundary does not migrate by analogy.** "Generate a dashboard screenshot for
a note" fails predicate 2. "A photograph of a server" fails predicate 3 (it asserts a real thing,
not a staged fiction). "A clip on a passport page" fails predicate 4. A future request that clears
all five is still, on its own terms, the same narrow admission this decision makes - it does not
widen it.

**Every prior copy of the ban this project ever wrote, cited, and ruled on individually:**

- **`DECISIONS.md:457-463`** (inside D-18, on method notes): *"A stock photograph of a person at a
  laptop carries no fact about anything this page says [...] it is ornament, and ornament is
  forbidden by D-07 and SPEC S10. `REPLICATE_API_TOKEN` is refused separately and more firmly: an
  image manufactured by a model to look like evidence, on a site about evidence, is worse than
  stock."` **This is the one instance the exception narrows, and only for the surface it was never
  written about.** D-18's ban stood for `/method/notes/`, a page whose entire genre is descriptive
  provenance of a measurement - an image there would sit beside real figures computed from
  `registry.json` and could be read as one of them. That is predicate 5 by another name, and D-18's
  ban stands there completely unchanged: no note may carry an image, generated or stock, today or
  under this decision. What D-42 adds is a second, disjoint surface - the landing page, below the
  first screen - that D-18's paragraph never addressed and predicate 4 now names explicitly so the
  two do not get reread as one rule.
- **`DECISIONS.md:87-93`** (D-07, "Strict instrument, not a marketing page"): untouched. D-07's own
  text is the source of the exception, not its casualty - "density and restraint everywhere
  **except the landing**" already drew this exact line before this decision existed. D-42 exercises
  a permission D-07 already granted; it repeals nothing in it.
- **`SPEC.md:63`** ("Density over decoration") - untouched. That sentence describes the registry
  table, a page predicate 4 forbids the exception from ever reaching.
- **`SPEC.md:202`** ("an ornament on a page about evidence is the failure this product exists to
  find") - untouched. That sentence is written about method notes' figure rule (SPEC S3.6), the
  same surface D-18 already covers above; predicate 4 keeps the exception structurally unable to
  reach it.
- **`SPEC.md:405`** (design direction, "The landing is the only screen with air") - untouched, and
  it is the clause that makes this decision possible rather than one it revises.
- **`SPEC.md:425-433`** (S10 Forbidden) - untouched. Nothing in the forbidden list is struck: "the
  stock hero of centred headline plus two buttons plus a framed screenshot" is still forbidden, and
  the three admitted clips are neither a stock hero nor a screenshot; "any fabricated registry
  entry" is still forbidden, and predicate 5 is what keeps a rendered pixel from ever being read as
  one.

**What is not decided here.** This decision authorises the exception and arms its gate before any
asset exists - `web/public/media/` is not created by this commit and no image, video, or Renoise
render is produced or committed by it (that work is later steps, blocked separately). The shot
script the caption and predicate 1 depend on is committed verbatim, unedited, as
`docs/media/FILM_SCRIPT.md`.

**Enforcement.** `LAW-STAGED-MEDIA-LANDING-ONLY` (`enforced_by.yaml`) binds this decision's two
checkable-in-source-tree predicates - placement (4) and captioning (3) - to
`scripts/ratchet_staged_media.py`, proved by mutation in `tests/test_ratchet_staged_media.py`: a
`<video>` planted in `Passport.tsx` fails the build. Predicates 1, 2 and 5 are properties of a
rendered file this ratchet cannot see with nothing yet committed to inspect; they are named here as
owed to whatever gate runs at generation time, not silently assumed covered - a ratchet that
claimed more than it measures would be exactly the false-green this project has already paid for
twice (D-15, and the truncated-law defect in D-38).

## D-43. The derived-markdown converter's input became partly untrusted, and where the boundary now stands

**Decision.** `web/html_to_markdown.mjs` reads output that already mixes our own markup with a
subject's declared text, and has since 2026-08-31: the accountability block renders four fields
read from a SUBJECT'S OWN `provek.json`, React escapes them into the prerendered page, and this
converter is what reads that page. Before that date its only input was our own site markup and a
single-pass tag strip was merely fragile; since, it is a question a stranger gets to ask. Five
things are ratified here rather than left standing only as comments in two `.mjs` files and one
`.py` file - a rule that lives only in a comment is not armed by anything that runs.

**1. Strip before decode, and the order is not to be reversed.** Stripping runs on the page's
markup; decoding runs after it (`NEVER_UNESCAPED` in `web/html_to_markdown.mjs`, holding `<`/`>`
escaped regardless of which spelling - named, decimal, hex - asked for them). Reversing the order
would let an honestly ESCAPED sequence like `&amp;lt;div&amp;gt;` be decoded into a live tag and
then silently eaten by the strip that follows - a loss of a stranger's text nobody attacked, and
the opposite failure from the one this boundary exists to prevent. **Any future patch that
decodes before stripping is a regression of this decision, not a refactor of it.**

**2. `js/incomplete-multi-character-sanitization` (code-scanning alerts #68-74): closed by
measurement, not by argument.** The prior commit wrapped every tag-strip loop in a generic
`untilStable(text, rewrite, limit)` helper. CodeQL's own re-scan of that commit still reported
seven instances of this rule against the individual `.replace()` calls inside the wrapper, because
its static analysis does not follow a rewrite function passed as a parameter through to prove the
loop around it reaches a fixed point. The rule's documented recommendation is a literal
`do {...} while (input !== previous)` around one `.replace()`; `web/html_to_markdown.mjs` now
carries exactly that shape in two functions - `stripTags(s)`, called from the five places that used
to each wrap their own loop, and `strip(html)`'s own second and last loop around its four-regex
chain. Re-scanned on the commit that made this change: **all seven of #68-74 are `fixed`.**
Evidence: `evidence/GREEN-007-seven-alerts-fixed-two-opened-by-the-fix.txt` — the alert states and
their `most_recent_instance.commit_sha` were read directly from the GitHub code-scanning API
before and after, not assumed from the diff.

**3. Two NEW instances of the same rule (#76, #77) were opened by the literal-loop commit itself,
and are DISMISSED, per the fallback this ruling named in advance of seeing the scan.** `strip()`
chains four different regexes (comment, script/style/template, svg, sr-only span) inside one loop
rather than four separate ones, because they interact across regex boundaries within a single
pass - removing `<script>y</script>` from `x<!<script>y</script>--z-->w` reconstructs `<!--z-->`
from characters the comment regex, having already run earlier in the same pass, will not see again
until the loop repeats. CodeQL flagged this exact interaction at the two regexes nearest the front
of the chain. The dismissal rests on three things, not on the alert being wrong:
   - **(a) A mutation-sensitive control exists and passes against the shipped code.**
     `tests/sanitisation_probe.mjs`'s `cross_category_reconstruction` case
     (`x<!<script>y</script>--z-->w`) is verified BY HAND to return `<!--z-->w` from a copy of
     `strip()`'s chain with the surrounding loop deleted, and returns `w` from the shipped,
     looped `strip()` - `tests/test_markdown_sanitisation.py::
     test_a_tag_reconstructed_across_strip_categories_does_not_survive` holds the shipped answer.
   - **(b) The shape is the rule's own documented fix.** CodeQL's help text for this rule
     recommends "applying the regular expression replacement repeatedly until no more replacements
     can be performed" via a `do {...} while (input !== previous)` loop - `strip()`'s loop is that
     shape, wrapped around the one place in this file where four such replacements must converge
     together rather than in isolation (running each regex to its OWN fixed point in sequence,
     the alternative that stays legible to the analyser, is weaker: it cannot catch a construct
     that regex 4 exposes for regex 1 after regex 1 has already finished converging).
   - **(c) Conditions of reopening, stated here rather than left implicit.** This dismissal is void
     - and #76/#77 (or their successors) are to be treated as open again - the moment any of: a new
     `.replace()` that strips tag-like markup is added to `web/html_to_markdown.mjs` outside
     `stripTags` or `strip`'s own loop; `strip`'s iteration ceiling changes from 20; or the CodeQL
     JavaScript query pack is upgraded and re-flags this shape. No one of those is presumed to have
     happened; each is a fact to check before relying on this entry again.

**4. The remaining gap is markdown syntax, not angle brackets, and it sits in a DIFFERENT
assembler.** `web/markdown.mjs:buildPassportMarkdown` writes `/p/<slug>/index.md` directly from
passport data and does not go through `web/html_to_markdown.mjs` at all - no `stripTags`, no
`NEVER_UNESCAPED`. It does not read `passport.accountability` today (a drift against D-10: the HTML
passport shows the block, its markdown sibling silently does not), so a value like
`[urgent: verify here](https://evil.example)` - no angle bracket at all, markdown's own link syntax
- has nothing to reach through YET. Two things now stand between that value and a published
artefact: `src/collector/declaration.py`'s `_bounded_str` refuses `[`, `]` and a backtick in any
declared string at the source, invalidating the whole declaration exactly as it already does for
`FIELD_MAX_CHARS` (parentheses alone stay legal - this module's own `_join` already writes
`f"({contact})"`, and parentheses form no markdown construct without a preceding `[...]`); and
`tests/passport_accountability_probe.mjs` + `tests/test_passport_markdown_accountability.py` arm a
tripwire that is vacuously true today (nothing reads the field) and starts exercising a real
interpolation - and failing in the gate, not in production - the day someone adds one without
routing it through an escaping step. Two paths were also checked and found not to need either
fix today: `Fact.unreadable()` takes no note text and `DeclarationResult.notes` is discarded by
`apply_declaration` before reaching any passport field, so a malformed subject document's error
text does not currently reach a published artefact; `web/functions/api/apply.js` sends its
Telegram notice with no `parse_mode`, so Telegram renders applicant-supplied `repo`/`contact` as
literal text rather than interpreting any markup in it.

**5. Comments in the two `.mjs` files reference this entry rather than re-narrate it** (LAW
#ONE-PLACE) - a comment corrected the record once already: `web/html_to_markdown.mjs`'s security
comment used to name `/p/<subject>/index.md` as the artefact a live tag was measured on, which is
built by `web/markdown.mjs` and does not read a declaration at all. What was actually run was
`tests/sanitisation_probe.mjs` against the converter directly; the comment now says that, and
points here for the rest.

**Why a decision record rather than a new law.** No armed rule was missing - `LAW #ONE-PLACE` and
`LAW #ALLOWLIST-WHAT-YOU-INSPECT` already exist and are cited above where they apply. What was
missing was a place for "decode never runs before strip" and the seven-alert verdict to live at
ratified strength instead of only in code comments a future edit could quietly narrow. The gate for
all of it is the test suite named throughout this entry, run at the door on every push; this record
is what a future editor reads before deciding a comment disagrees with it.


## D-44. `whiteknightonhorse/APIbase` had no `provek.json`, so accountability read empty - that emptiness was correct, and a declaration now exists

**Decision.** The operator opened `/p/git_whiteknightonhorse_APIbase/` and saw all four
accountability fields as NOT MEASURED. Measured before anything else: the mechanism was not
broken. `src/collector/declaration.py` reached `raw.githubusercontent.com` for that subject,
pinned the read to a real `head_sha`, and got back HTTP 404 for `provek.json` - a repository that
genuinely carried no declaration document. `_not_declared` folded that into
`NotMeasured.NOT_DECLARED` on all four fields exactly as designed (world 3 of the four-world
contract this module's own docstring lays out). An empty accountability block is not a defect in
the collector; it is what "the subject said nothing" is supposed to look like. Fixing this meant
publishing a declaration, not patching code.

**1. Accountability does not move the score, so publishing our own declaration is not
self-dealing.** `src/passport/passport.py` states plainly that `Accountability` "does NOT affect
the score", and `declaration.py`'s own docstring repeats it: the block enters neither `verified`
nor the projection, by construction. Every field the render shows carries `confidence="assumed"`,
never `"measured"`, and is labelled self-declared on the page. Filing `provek.json` for our own
repositories therefore cannot inflate a number this project publishes about itself - the objection
"we are an interested party" does not apply to a channel the ladder was built to ignore.

**2. What `whiteknightonhorse/APIbase` now declares, and what it does not.** `provek.json` at
that repository's root (merged to `main`, pinned SHA `5ef9826000d41079d12cbe52b81ff1b562da6afd`)
states: `emergency_stop` exists, held by the operator, mechanism "ssh + service stop halts all
paid calls" - true of every repository on this operator's Hetzner box, and stated in the paid-call
terms specific to APIbase's own business model; `insurance` does NOT exist - a stated absence,
which the render distinguishes from silence as "none - stated, not omitted"; `claims_addressee` is
`api@apibase.pro`, the mailbox the operator already uses for provider registrations; `dispute_path`
is `type: "contact"`, the only path that becomes honest once a real addressee is on record.
`operations.treasury_control` was deliberately OMITTED - the operator chose "declare nothing" over
inventing a level, and an omitted key reads as `NOT_DECLARED`, never as a zero or a level nobody
asserted. Inventing an insurance policy or a treasury level neither field carries would have been
exactly the fraud LAW-NOT-MEASURED and this whole project exist to make uneconomical; a declared
`false` is stronger evidence than silence, and was preferred to it here on purpose.

**3. The rollout to the rest of the registry carried only the fields with a confirmed answer.**
Nine other subjects in this operator's cohort (`AI-Property-Sales-Platform`, `AIpush`,
`audiobook-shorts-series`, `cryptocardhub-defycard`, `cryptocardhub-public`, `gov-auction-report`,
`mcp-protocol-tester`, `provek`, `provek-method`) now carry `provek.json` declaring
`emergency_stop` (same ssh/service-stop mechanism, worded for automated activity rather than paid
calls where the subject is not one) and `insurance: false` - both generically true of every
repository this operator runs. `claims_addressee` and `dispute_path` were NOT copied across:
`api@apibase.pro` is the mailbox for APIbase's own provider registrations, and asserting it as the
claims address for an unrelated project would have been the fabrication this decision's own second
point refuses, not a rollout. Those two fields stay `NOT_DECLARED` on every subject but APIbase
until a real answer for each is on record. Four subjects (`AI-Property-Sales-Platform`,
`audiobook-shorts-series`, `gov-auction-report`, `cryptocardhub-defycard`) are private repositories
that an anonymous collector already read as `unreadable`/`not_declared` before this work and still
does after it - `raw.githubusercontent.com` answers a private repo's file with the same 404 an
absent file gets, so a declaration pushed there cannot be read by this pipeline without a
credential the anonymous collector does not carry by design (Q-M2 refuses a token at the point of
publication, not only at the point of reading). This is a pre-existing property of the collector,
not something this decision introduces or was asked to change.

**4. "the check did not run" on Deployment and Treasury control is a true sentence, not a
softened one.** Both operations show `level: check_did_not_run` in every passport, APIbase's
included. That is `NotMeasured.CHECK_DID_NOT_RUN`, and it is the honest reason because no collector
for either operation exists anywhere in this codebase: `src/verify/control_map.py` names the
reasons as facts about what THIS CODEBASE has built - `DEPLOYMENT_NOT_COLLECTED = "collector not
implemented"`, `TREASURY_OUT_OF_SCOPE = "outside MVP scope"` - not facts about any one subject.
`APPARATUS_ABSENT` was ruled out on purpose: that reason means the check RAN and read a genuine
structural zero (a subject with zero workflow runs, ever), which requires an apparatus that reads
the subject to exist in the first place. For deployment and treasury there is no such apparatus at
all, for any subject, so the check was never dispatched - `CHECK_DID_NOT_RUN` is the only one of
the six reasons in `src/abs_profile/measured.py` that describes "we have not built this yet", and
using it here says exactly that, to every reader, including a stranger who has never read this
file.

**5. No seventh reason, no reopening.** A "the operation is out of scope for what we sell" reason
was considered and rejected again today, for the same argument already on record: `deployment` and
`treasury` are real operations a subject can run, out of reach only because this collector has not
been built for them, not because the operation is somehow outside what accountability could ever
mean. Adding a reason here would re-litigate a boundary this project has already drawn, on no new
fact - the four private subjects reading `unreadable`/`not_declared` above are the closest thing to
new evidence this session produced, and they are explained by point 3, not by a missing sixth
world.

**Why a decision record rather than a new law or gate.** No rule was missing - `LAW-NOT-MEASURED`
and the four-world contract in `src/collector/declaration.py` already say everything points 1-4
depend on; nothing here needed rearming. What was missing was a `provek.json` this project's own
subjects could be measured from, and a place recording why the emptiness that preceded it was a
correct reading rather than a bug report waiting to be filed again.


## D-45. Specification revision 1.4 is ratified: the phase grid is renumbered, and the §8.3 erratum becomes a norm

**Decision.** The operator ratified Fable's draft amendment to specification §4 and §8
(dated 2026-09-02) as specification revision **1.4**, applied to `SPEC_AI_Business_Incubator_v1.md` as a
dated, non-silent revision — a changelog table in the header, not an edit that leaves no trace of
what changed or when. Five things land in this one commit, because the brief that ratified them
named the same coupling this entry keeps: an edit to specification §8 requires this repository's
own `SPEC.md` §4 to be re-derived in the SAME commit, not a follow-up one, or the two documents
would disagree about what "phase 2" means for exactly as long as the follow-up takes.

**1. The phase grid is renumbered, and no norm of §8 changed.** "Phase 2" now names the Provider
Catalog (new specification §4.2-bis: a verified subject's outward "Order ↗" link, the `service`
declaration block, and WitnessRecord v0). Funding Tasks — all 47 requirements of specification §8
— move to phase 3 unchanged; only the moment they take effect moved. Decision A-10 (projects
first) is what ordered them this way, and nothing here revisits that ordering, only the label on
top of it.

**2. `SPEC.md` §4 is re-derived, not left to read as if phase 2 still meant Funding Tasks.** The
section is renamed to "Phase 3 — Funding Tasks", a new §4.0 states the Provider Catalog is now
phase 2 without duplicating its full page design (owed to the phase-2 implementation cycle's own
design-circle step), and §4.2's layout table is corrected: the registry's trailing action column
and the passport's task-history slot are filled by the Catalog (Order link, WitnessRecord) in
phase 2, not by "commission work" that was never phase 2's content in the first place under either
numbering.

**3. The §8.3 erratum this repository already carried as a reconstruction is now a norm of the
specification itself.** `SPEC.md` §4.1 has said since before this revision that the `rejected`
arrow missing from §8.3's diagram was "a reconstruction, not a quotation" — a reading taken here to
resolve a contradiction between §8.3 calling `rejected` terminal and §8.2 saying a task missing a
condition of creation is never created at all. Revision 1.4 adds the arrow to the master
specification's own diagram and states the same reading there, so the reconciliation is no longer
something only this project's site asserts about the specification; the specification asserts it
about itself. `SPEC.md` §4.1's hedge is updated to say so and to point here.

**4. A new gate holds the fact stated twice in `SPEC.md` §4 to itself.** The renumbering note
appears once framing the whole section and once inside §4.1's own re-derivation warning, because a
reader can land on either half without having read the other — the load-bearing habit LAW #ONE-PLACE
names, applied here before an editor gets the chance to update one copy and leave the other stale.
`scripts/ratchet_phase3_note.py` extracts both marked copies and fails the build if fewer than two
exist or if any two disagree; `tests/test_ratchet_phase3_note.py` mutates the live file and restores
it, proving the gate actually catches drift rather than merely existing beside it. What this gate
cannot do, and does not claim to: check either copy against the master specification itself, which
lives on the operator's laptop and is not tracked by this repository — a limit `SPEC.md` §4.1 has
named on its own re-derivation duty since before this revision and repeats here.

**5. Nothing else moves.** Specification §8 in full, §11.4's four revenue streams, every A-decision,
the non-goals of §4.3, and the thresholds of Q-D1 are unchanged — the amendment's own closing
section says so and this entry does not relitigate it. The operator's five ratified answers to the
open questions of phase 2 (self-declared order pages rather than a task board; a reason string
rather than a blank cell for non-eligible rows; the witness free with an explicit label, paid-ness
excluded pending A-1's trigger; Provek's own self-application through a `service` block; taglines
deferred to the design circle) are the brief this and the following phases execute against, and are
recorded here as the boundary of what this phase-0 step was asked to ratify — not as a fresh decision, since the
operator made them, not this session.

**Why a decision record and a new law together, rather than either alone.** The renumbering and the
erratum are facts about the specification, which a decision record is for; the risk that the two
`SPEC.md` copies of the same fact drift apart is a risk about THIS repository's own text, which
needs a gate that runs on every push, not a paragraph a future editor might not read. Recording the
first without arming the second would leave exactly the gap D-37 already found once in a different
file — a rule believed synced because nothing had yet proven otherwise.


## D-46. Schema 1.1.0 lands: `service` and `service_endpoint`, mirroring `Accountability` exactly, outside the score

**Decision.** Phase 2's Provider Catalog (specification 4.2-bis, points 1-2) needs a subject's
self-declared order-intake channel and its anonymous reachability, published on the same terms
`Accountability` already set: self-declared content is `assumed`, never `measured`; a
platform-observed check is `measured` because this collector performed it; and NEITHER block can
move a ladder level or the projection - built as a sibling, not a special case.

**1. `Service` and `ServiceEndpoint` are new `Passport`-level fields, outside `verified`.** Same
shape as `Accountability`: four `Fact`-wrapped fields (`order_url`, `offering`, `pricing_url`,
`terms_url`) for `Service`, and `declared`/`reachable`/`checked_at` for `ServiceEndpoint`. `build()`
takes both as optional keyword arguments, defaulting to the empty/not-declared shape when a subject
has no GitHub remote to read a declaration from at all.

**2. `order_url` is required and https-or-invalidate-the-whole-declaration, same boundary as D-43.**
`src/collector/declaration.py`'s `_https_url` extends `_bounded_str`'s existing FIELD_MAX_CHARS/
bracket rule with a scheme+host check; a missing, non-https, or malformed `order_url` invalidates
the entire declaration (accountability included), never a silent per-field drop. `pricing_url` and
`terms_url` are optional but held to the identical https rule when present - a weaker gate on two
of three URL fields would be the inconsistency LAW #ONE-PLACE forbids.

**3. The SSRF boundary is checked TWICE, by ONE routine, for two different reasons.**
`src/collector/reachability.py:resolve_public_ip` resolves a hostname and refuses a private,
loopback, link-local, reserved, multicast, unspecified, or IPv4-mapped-private address - checked
AFTER resolution, never against the hostname string, which a DNS-rebinding attack or a hostname
that simply answers privately would defeat. `declaration.py` calls it at DECLARATION PARSE TIME
(a private `order_url` invalidates the whole document, the operator's mandatory control); the same
routine is called again at PROBE TIME inside `_one_hop`, for every hop of a redirect chain, because
DNS can change between when a declaration is accepted and when it is next re-measured, and because
a redirect is exactly as capable of naming a private address as the original URL. One routine, two
callers, so the rule cannot drift between "this declaration is invalid" and "this URL is
unreachable now" - LAW #ONE-PLACE, applied before the second copy could exist rather than after.

**4. The address CHECKED is the address CONNECTED TO.** `curl --resolve host:port:ip` pins the
GET to the exact IP `resolve_public_ip` validated, closing the check-then-use gap a second,
independent resolution at connect time would reopen. Redirects are followed by this module's own
loop, at most `MAX_REDIRECTS` (2) hops, each fully re-validated from scratch - curl's own `-L`
would follow a hop without ever calling back into this file's checks, which is why it is never
used here. GET only; a bounded timeout.

**5. Two mandatory controls, both run live rather than only argued.**
`tests/test_phase2_service.py::test_MANDATORY_CONTROL_private_address_in_order_url_invalidates_whole_declaration`
mocks a private resolution result and proves the WHOLE declaration - not merely `service_endpoint`
- comes back invalid.
`tests/test_MANDATORY_CONTROL_a_scorer_that_read_service_would_be_CAUGHT` wraps `build()` for the
duration of one test with a deliberate defect (a declared, reachable `order_url` bumps the
projection by one) and proves the projection-invariance assertion that guards `service` would
actually go red against it - the same discipline this project's ratchet mutation tests already
hold themselves to, applied here to a domain invariant rather than a ratchet.
`test_MANDATORY_CONTROL_positive_a_plain_https_order_url_is_accepted` is the control-positive: an
ordinary declaration is not swept up by either boundary.

**6. `registry.json` carries `service_url`/`service_reachable` per subject** (`src/registry/
public_registry.py:Row`), read back off the passport's own machine form rather than re-derived a
second way in each of the three emitters (`src/pipeline.py`, `scripts/cohort.py`,
`scripts/measure_qm2.py`) - `scripts/measure_qm2.py:registry_row` in particular derives both
fields from `p.to_machine()` rather than taking them as extra parameters, so "how to read a
declared order_url out of a passport" has exactly one implementation.

**7. `apply_declaration` now returns a 3-tuple** (`accountability, service, claims`), not 2 - every
call site (`src/pipeline.py`, `scripts/cohort.py`, `scripts/measure_qm2.py`, and this project's own
tests) updated in this commit. No UI reads any of this yet (the operator's phase-2 plan builds
the pages in its own next step); this decision covers the backend and collector only.

**What is explicitly NOT done here, per Fable's standing prohibition.** `service` and
`service_endpoint` are never read by `src/verify/scorer.py` or folded into `operations` or
`projection` - the mutation control in point 5 exists specifically to keep that true under future
edits, not merely today. Putting reachability in `operations` or the score was ruled out in
advance and is not reopened by anything in this entry.


## D-47. The Order link ships on the registry, the landing rail and the passport - one predicate, three callers

**Decision.** The Provider Catalog's outward "Order" link (specification 4.2-bis point 3) is
implemented as CODE in exactly one place - `orderLinkUrl`/`orderAbsentReason` in `web/src/types.ts`
- and every surface that can show it calls that function rather than re-deriving eligibility from
`status`/`service_url`/`service_reachable` a second way. The predicate itself is not this
project's to redesign; it is stated verbatim in the operator's brief
(`verified (by time) AND declared AND reachable`) and this commit implements it literally, in the
same order the brief states the three conditions.

**1. `/registry/`'s reserved tail column (decision D-05) is filled**, not replaced: eligible rows
get `Order ↗` with `rel="noopener noreferrer nofollow"` and `target="_blank"`; every other row
shows WHY, reusing `AbsentMark` with a plain-English reason string rather than a coded key -
`AbsentMark`'s own fallback (`REASON_TEXT[reason] ?? reason`) already renders an unrecognised
string verbatim, so no new dictionary entry was needed to keep its "reason is the substance of
this state" guarantee (D-03).

**2. The landing page's registry rail funnels passport-before-button.** The Order link, when the
predicate holds, sits BELOW the passport link in the same list item rather than beside the subject
name - specification 4.2-bis's own framing is that the button is downstream of a real, current
passport, not an alternative to reading one.

**3. The passport page gets both a Service section and its own Order link.** The section mirrors
`Accountability` exactly (self-declared fields, `assumed` register, a `not_checked` empty state)
and adds one line for `service_endpoint` (PLATFORM_OBSERVED, a different register, rendered apart
from the four self-declared tiles rather than as a fifth one that would blur the two together). The
passport - the load-bearing page per D-01 - shows the same Order link a reader who arrived by a
shared URL rather than through the registry would otherwise never see.

**4. `/method/` publishes the predicate as a rule** - what it asserts (a page answered an
anonymous GET at last check, behind a passport that had not lapsed) and what it does NOT assert
(fulfilment, pricing accuracy, safety, reachability at the exact click, or that this project is a
party to anything downstream) - specification 4.2-bis's own boundary, stated where a reader can
find it rather than left implicit. `/apply/` gets the one line the brief asked for, linking to it.

**5. The mandatory synthetic-registry control renders the REAL shipped code, not a
reimplementation.** `tests/test_order_link_predicate.py` imports `renderRoute` from the built
`web/dist-ssr/entry-server.js` - the same export `web/prerender.mjs` calls for every live page -
and renders `/registry/` against four synthetic rows (stale, unverified, verified-but-unreachable,
and the one eligible row), asserting the three ineligible rows carry no link and their reasons
print, and the eligible row's link and both required `rel`/`target` attributes are present. A
fourth test performs the operator's named mutation live: `orderLinkUrl` is rewritten to ignore
status and reachability, the SSR bundle is rebuilt from the mutated source, and the same render is
asserted to now link ALL THREE previously-ineligible rows - proving the first test is not
vacuously green. Both the source text and the built bundle are restored to their exact original
bytes in `finally`.

**6. The real corpus was re-measured, not left stale against the new schema.** `scripts/cohort.py`
was run in full after D-46 landed (schema 1.1.0); every one of the ten registry rows now carries
`service_url`/`service_reachable` (all `null`, since no subject has declared a `service` block
yet) and every passport carries the `service`/`service_endpoint` blocks - without this, the site's
own prerender crashed reading `undefined.order_url` off passports built under the old schema.

**What is deferred, named rather than silently skipped.** `/phase-2/` is reworked LAST in this
implementation cycle, after a live check of every button on the deployed site - editing the page
that announces what is "specified, not built" before confirming what IS built would risk the exact
claim-stronger-than-artefact defect this project exists to catch. The passport's task-history slot
stays empty until phase 5 (WitnessRecord), per the operator's own sequencing; nothing here reserves
or fills it early.
