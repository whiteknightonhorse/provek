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

