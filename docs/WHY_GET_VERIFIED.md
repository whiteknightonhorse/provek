# Why get a Proof of Autonomy passport

**Status:** the offer that must exist BEFORE mandate intake opens (spec 4.6, plan T-2.14).
The go/no-go clock in section 1.5 measures conversion of THIS offer. Starting the clock before the
offer exists would measure our own marketing delay and call it demand.

---

## The problem you have that we solve

You built a business that runs on agents. Your customers cannot tell you apart from a company that
put "AI-powered" on a landing page and hired three people to answer chats. Neither can your
partners, and neither can anyone deciding whether to route money or work through you.

That asymmetry is not a marketing problem. It is a verification problem, and marketing cannot fix
it: any claim you make, a competitor can make more loudly.

## What a passport is

A machine-readable record that states, per business operation, how much of it runs without a human
in the loop - and shows the evidence behind each number. It also states, in the same document,
what we could NOT measure and why.

It is published in a public registry, and it carries the protocol version and an expiry date.

## The honest limits, stated up front

We would rather lose you as a subject than have you discover these later.

* **We measure autonomy, not quality.** The passport says nothing about whether your decisions are
  good, whether you are profitable, or whether you are safe to rely on.
* **Some claims are not verifiable at reasonable cost.** "No human wrote this commit" is one of
  them. Where a signal is probabilistic we publish it as probabilistic, and it never becomes a
  verdict.
* **A control-path map proves a path EXISTS; it can never prove that no undiscovered path exists.**
  Every map publishes its own coverage: what was inspected, what was out of reach, and what a
  missed path would look like.
* **An absent measurement is not a zero and not a failure.** If we could not read something, the
  passport says so.

## Four reasons this is worth your time TODAY, with no funders in the system yet

**1. It is an artefact for YOUR customers, not for ours.** This is the load-bearing one. Your
buyers are already asking how much of your product is really automated. A verified passport is the
one answer a competitor running an "AI theatre" cannot copy - because copying it requires actually
being autonomous.

**2. Differentiation where agents compete for attention.** Ecosystems now list agents by the
thousand. A verified record is a filter that works in your favour.

**3. A regulatory dossier you will need anyway.** If you are a crypto-adjacent project, your
counsel will at some point have to argue about who controls what. Our control map is evidence
input for that argument - built before you need it, by a third party, with a timestamp.
(It is evidence, not a legal conclusion; the conclusion is your lawyer's to draw.)

**4. It costs nothing right now.** Early passports are free. We are not doing you a favour: a
registry with no entries is worth nothing, and we need the first ones as much as you do. Saying
that plainly is cheaper than pretending otherwise.

## What we ask of you

* a scoped read-only token or a public repository - the same access any auditor would need;
* nothing else today. **Every verification at this stage is read-only** — we read what is already
  public and touch nothing. Fewer operations can be measured that way, and the passport says which
  ones and why.

  Active probing is now offered, and it is one operation wide. The prober built under T-2.12 does
  exactly one thing: **it attempts to use a path you tell us is closed, and reports whether your
  running system actually refuses it** — a fact your repository cannot show, because a file
  describing a control and a deployment enforcing one are different things. Nothing else is
  implemented, so nothing else is asked for. It has been run against one subject, our own site, and
  no third party has been probed yet; you would be the first, and that is stated here rather than
  discovered by you afterwards.

  It requires an explicit mandate naming the action, the paths, a ceiling on how often, what must
  not be affected, who answers for damage, what aborts the run and how you revoke it — **without a
  mandate we do not touch your production, and probing someone's live system without one is an
  incident, not a verification.** The form records that you want one; a document follows, and no
  request is sent at your systems before you have signed it. Ticking the box authorises nothing:
  the intake stores what you asked for beside a policy field that reads `passive` on every
  submission, and no HTTP request can change the second one (D-23).

  This bullet asked for the mandate in the present tense while there was no prober, then said the
  opposite for one day, and both times it was the last copy to be corrected — this document IS the
  offer, and it is the copy nobody re-reads (D-21, L-2).

## What we never do

We never hold your funds. We never take custody of your keys. We never store your secrets - they
are redacted before they become an artefact. We never verify anyone who did not ask.

## Conflict of interest, disclosed rather than hidden

The first entries in the registry are the operator's own systems. They carry
`verifier_affiliation: same_owner` in the passport, because a first cohort that reads as
independent verification would be a quiet lie on the shop window. You can see exactly which
records are affiliated and which are not.

---

*Proof of Autonomy - a verification layer built as an ERC-8004 validator. The standard supplies
the transport; the methodology is ours and is published in full.*
