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
- `push.sh` refuses a dirty tree, so the gates judge the artefact that is pushed;
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
