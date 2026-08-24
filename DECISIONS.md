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
