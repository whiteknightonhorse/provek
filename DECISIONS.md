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

