# ADR-0010. A step blocked from outside keeps a sentinel, and the block lifting is a red build

**Date:** 2026-08-20. **Status:** accepted. **Relates to:** ADR-0001 (built as a validator, so the
Validation Registry is our distribution channel), T-2.15b, `docs/MEASUREMENT_QM1.md`.

## Decision
T-2.15b — on-chain publication into the ERC-8004 Validation Registry — has no target: the registry
is not deployed on any chain, measured on 2026-08-20. That "cannot" is now held by an instrument
rather than by a sentence in a plan. `scripts/watch_validation_registry.py` reads the deployment
list anonymously and writes the reading, with its date, to
`public/erc8004/validation_registry.json`; a liveness obligation (`validation_target_watch`,
interval `while_blocked`) goes red when nobody has taken that reading inside the interval; and the
appearance of an address is itself a finding that stops the build.

The record keeps **two blocks**, and that is load-bearing rather than tidy. `measurement` is the
last run that established something and is the only thing the interval rides, so a run that
measures nothing never advances the clock. `last_attempt` is what the last run did, whatever that
was, and the gate reports it the same minute — including when it is GOOD news, and including when
the two blocks disagree, which no single run can produce and a partial restore can. A draft that kept only the first left the record
saying `no_target` inside its interval while the last run had reported the list unrecognisable, and
the sweep came back clean — a green gate meaning *did not look*, which is the defect this whole
layer exists to refuse.

## Why
An external blocker is not like a lapse. Nothing expires while there is nowhere to publish, so no
deadline in the world would ever produce a reminder — and the state changes on somebody else's
schedule, with no event that reaches this repository. That is the precise shape in which "cannot"
becomes "forgot": the plan goes on saying the step is blocked long after it stopped being true,
and it stays a claim nobody can refute because nobody re-measured it. This project exists to find
claims that have outrun their artefact; one of its own would be the worst kind.

## Why good news is red
When an address appears, three things are wrong at once and none of them announces itself:
`docs/MEASUREMENT_QM1.md` still says NOT DEPLOYED, T-2.15b is still unschedulable in the plan, and
the unaudited-contract risk — named in the plan but never decided — becomes live. A green run
would let all three stand. So the finding stops the door, names the address, names the step it
unblocks, and names the document that has become false. Clearing it is a decision, not a rerun.

## What this deliberately is not
It is not a step towards writing on-chain. Nothing here acquires a target, holds a key or pays gas;
`Erc8004Transport.publish` still refuses — but now refuses citing the reading and its date instead
of a standing assumption, which is what makes the record something a component actually reads
(ABI-16-3) rather than a file that is written and never opened.

It is also not a watcher on a watcher. The chain still ends at a person (ABI-16-7): the finding is
read by whoever is at the door or in the daily gates run, and it is they, not another module, who
decide what to do about it.

## Cost, and the limits that are not closed
The reading is a parse of somebody else's README, so its shape is theirs to change. The instrument
carries a positive control — the Identity and Reputation registries are deployed and listed in the
same list, and if **either** cannot be found beside an address the answer is `unreadable`, never a
zero. Four limits are named rather than implied:

- the control catches the document being replaced, emptied, moved behind an error page or
  restructured; it does **not** catch a document that keeps two rows naming those registries while
  the live list moves elsewhere;
- it reads a document, not a chain, so a deployment the reference implementation has not written
  down is invisible here — the same gap `docs/MEASUREMENT_QM1.md` measured through;
- the finding carries the address and the document's own row, not the chain, because the document
  puts that in a heading; a testnet address is not a target and reading the row is part of the
  decision the finding asks for;
- and the parser cannot always tell a deployment row from a code example, so a line that only
  mentions validation beside an address is reported as `not_measured` with the line quoted, rather
  than resolved in either direction. It is the one finding here that a rerun cannot settle: the
  only act that clears it is teaching the parser to classify that shape, with a test. Scheduling
  the step does not clear it and is not meant to — there is no acknowledgement mechanism anywhere
  in this design, deliberately, because an acknowledgement is a way to mark an unread instrument
  as read.

Closing the second would mean watching chains rather than a document — a cost with no reason to be
paid before there is a target. All four are why the reading records the document's `sha256` and is
re-taken on an interval instead of being trusted.

## What it cost to get here
Three drafts of the write rule and three of the parser's tiers, each defect found by Fable inside
the fix for the previous one: a false red that fired on the operator performing the habit; then a
green gate that hid every instrument failure for the length of the interval; then a target label so
strict it missed a renamed row, then so loose it read `validationRequest(0x…)` in a code sample as
a deployment, then strict again but matching a cross-reference on the Identity Registry's own row.
The pattern is worth the space it takes here: **every one of them was a fix that closed the
previous instance and re-opened its mirror**, and none was visible from the side the previous round
had been argued from. L-27 is the general form.
