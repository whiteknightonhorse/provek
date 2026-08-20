# Liveness: who re-runs what, when, and what happens if nobody does

Two obligations are declared into the registry, and they watch opposite things. The first watches a
**lapse** — verdicts that expire by time whether or not anybody acts. The second watches a
**blocker** — a step of ours that cannot proceed until somebody outside this repository does
something, where nothing expires at all and the only thing that decays is our knowledge of it. The
cohort is below; the blocker is the last section.

## The cohort: who re-runs it, when, and what happens if nobody does

The eight rows on `/registry` are not permanent. Each carries a `valid_until`, and
`effectiveStatus()` turns a row `stale` at read time the moment that date passes — with no event, no
commit and no notice (ABI-15-5, `LAW-STALE-IS-COMPUTED-AT-READ-TIME`). As of the run of
2026-08-20 08:30 UTC that date is **2026-09-19** for all eight.

Nothing re-issues them. This document is the habit that does, and the gate that makes forgetting
audible.

## Why this needed writing down at all

`src/liveness/obligations.py` has existed since T-2.10. It defines silence as a finding, names the
five states of sleeping code — including *`produces_result_nobody_reads`* — and its `sweep()` reports
an empty registry as suspicious rather than clean. It had seven passing tests and two laws pointing
at it, and **nothing had ever declared an obligation into it**: every `Registry` in the tree was
built inside a test and filled by that same test.

So the layer whose subject is code that runs and is never read was, for its whole life, code that
ran and was never read. No test could see it, because a test that constructs its own registry never
finds one empty. That is the difference between a module being correct and a module participating
(ABI-16-3), and it is the gap MVP §4.1 p.8 means when it asks for the liveness layer *working*
rather than *present*.

## The habit

**Who.** The executing agent, on the audit host, as a step inside a task cycle. **Nothing re-runs
the cohort on a timer** — `notes_cron.py` (D-19) runs the note cycle, not this, and the daily
`schedule:` added to `gates.yml` below is a clock on the CHECK, not on the remedy. Writing "a job
re-runs it nightly" here would be exactly the claim-stronger-than-artefact this project exists to
catch.

**When.** Whenever the gate below says the interval has elapsed, and in any case before the
`valid_until` on the rows. The gate is the reminder, and its terminus is a person reading a red run —
either at the door or in the Actions log. Nobody is asked to remember a date; somebody is still
asked to look.

**What.** Six commands, and then a seventh step that is not a command on this host:

```bash
python3 scripts/cohort.py                       # 24 anonymous GitHub reads, no credential needed
cp public/registry/registry.json web/public/data/registry.json
cp public/passports/*.json web/public/data/passports/
python3 -m src.liveness.commitments             # reads back what was just written
git add public web/public/data && git commit -m "re-issue the cohort: eight rows re-stamped"
./scripts/push.sh                               # the only door outward
```

The commit is on that list because both registry copies are tracked, so the `cp` always dirties the
tree and `scripts/push.sh` stops there. The first draft of this document omitted it and so did the
remedy attached to the finding, which meant the instructions ended at `REFUSED: the working tree is
not clean` — a remedy that does not reach the door it names, written into the finding whose selling
point is that the reader does not have to work out what to do (L-9). The `-m` is there for the same
reason one step further in: the reader named under **Who** above is an agent in a non-interactive
shell, where a bare `git commit` opens no editor and aborts. Both found by Fable, one round apart —
and the second omission was written into the fix for the first, which is the more useful half of it.

The seventh step is the operator's: **`wrangler pages deploy` from the laptop.** This host holds no
Cloudflare credential it is authorised to deploy with (L-9, D-19), so a push publishes nothing. Until
that step happens a reader at provek.dev still holds the previous verdicts, and the gate below cannot
see it — the deepest thing measurable from here is the copy that enters the build.

**The one reading that closes the loop, and it is the operator's too:**

```bash
curl -s https://provek.dev/data/registry.json | python3 -m json.tool | head -5
```

`generated_at` there is the only number that says what a reader actually receives. Everything else in
this document is about the repository (L-3).

## What happens if nobody does it

`tests/test_reissue_obligation.py` sweeps the obligation against the real clock on every run of the
suite. When the interval has elapsed the finding is named, carries the remedy, and the build is red:

```
SILENCE: cohort_reissue has been silent longer than its before_reissue interval
(last seen 2026-08-20T08:30:14.931533+00:00). Remedy: `python3 scripts/cohort.py`, ...
```

The suite does not skip in any state. That is L-16: the four note suites were counted among the
armed while every assertion in them stood down in precisely the state that shipped a defect. Here the
state that would ship the defect — a registry of verdicts nobody re-measured — is the state the
gate exists to speak in.

**The gate is a time bomb by design.** It goes red with no commit and no event, because that is what
"silence becomes a finding" has to mean if it means anything: an obligation you can only fail by
doing something is not an obligation. The way past it is to perform it. `--no-verify` is forbidden
and there is no second door.

### A time bomb needs a clock, and the first draft of this gate had none

Every trigger in `.github/workflows/gates.yml` — `push`, `pull_request`, `workflow_dispatch` —
requires a person to act first, and so does `scripts/push.sh`. So in the exact state this obligation
exists for, where nobody acts, nothing would have run the sweep, nothing would have gone red, and
the eight rows would have lapsed in silence on 2026-09-19 under a gate that four documents said
fires on its own. A tripwire that only trips when you walk into it is not a clock. Found by Fable,
in the change that made the claim.

`gates.yml` now carries `schedule: cron "17 7 * * *"` — a daily run of the whole gate set, free on a
public repository and costing this host nothing, since it runs on GitHub's machines rather than
against the 10 GB / 1.5 GB / one-core budget in `CLAUDE.md`.

**What that proves and what it does not.** The trigger is in the workflow, and the check that says
so parses the file: it locates the top-level `on:`, finds `schedule:` inside it, and requires a
`cron:` with a value under *that* key — so a commented-out trigger, one mis-indented to the top
level, one under a job, and an empty `schedule:` with a cron string elsewhere in the file are all
rejected, and the block, flow and same-indent spellings of a live one are all accepted. Its limits
are named in the helper's own docstring rather than left to be found: comments are stripped without
respect for quoting, an aliased `schedule: *defaults` reads as absent, and the table of shapes it is
tested against is enumerated from cases somebody reported — evidence that those shapes are handled,
not a proof of coverage. Three drafts of that check were wrong, each in a way the previous draft's
control table could not see.

Whether GitHub *dispatches* the run is a different matter and is not observable from the audit host;
scheduled runs are queued rather than guaranteed at the minute named. The first scheduled run to
appear in the Actions log is the evidence; until one has, this is a request rather than a
measurement (L-10).

**And the clock switches itself off, though not before it has done its work.** GitHub disables
scheduled workflows in a public repository automatically when no repository activity has occurred in
sixty days — so total inaction, the state this gate exists to detect, is eventually also the state
that stops the gate, silently. **The bound is what matters and it is comfortable:** the counter runs
from the last repository activity, so with nobody doing anything the daily runs continue. Taking the
run of 2026-08-20 08:30 UTC as the last activity, the deadline falls on 2026-09-12 08:30 and the
cron fires at 07:17 — so the first scheduled run that can *see* the finding is the next morning,
2026-09-13, and it then fires every morning until the schedule is disabled around 2026-10-19. That
is of the order of thirty-seven alarms. The rows lapse on 2026-09-19, seven days into that run, so
the obligation's whole lifecycle — deadline to lapse — happens inside the window with about eight
times its own length to spare. What is lost is a repository nobody has touched for two months, by
which point the registry has been stale for a month and has said so every morning.

Two drafts of this paragraph got that wrong, in opposite ways worth recording. The first guessed —
"the first alarm survives; everything after it does not" — when the alarm is daily, not single. The
second computed the alarm count and then attached it to the lifecycle instead ("completes inside the
window, roughly thirty-eight times over"), which is a true number welded to the wrong noun; seven
days fits into sixty about eight times, not thirty-eight. And the count itself ignored the phase: a
07:17 cron against an 08:30 deadline loses the first day. A stated limit that is not the measured
limit is a defect in the paragraph whose subject is stating limits accurately — and the sentence
saying so was written in the draft that then made the same mistake one line above it.

Worth naming how the 60-day limit was nearly missed altogether. Two limits were written down here —
queued not guaranteed, dispatch not observable — and the list stopped, because two caveats read like
a careful paragraph. This is the third, it is the only one that touches the case the schedule was
added for, and it was found by opening GitHub's own documentation rather than recalling it (L-14: a
measurement consulted until it agrees is not a reading).

And the chain stops there, deliberately (ABI-16-7): a red scheduled run is seen by a person, not by
another watcher. `RENEWAL_MARGIN` is what pays for the lag between the run going red and somebody
looking — a second estimate, named in the constant's own docstring rather than left implicit.

## The interval, and why it is not thirty days

`Interval.BEFORE_REISSUE` is bounded at `PASSPORT_VALIDITY - RENEWAL_MARGIN` — thirty days minus
seven, so twenty-three. Both constants and their origins are in `src/liveness/obligations.py`.

An interval equal to the validity window would put the finding on the day the rows go stale, which
reports the loss rather than preventing it. The margin is the lead time the remedy needs, and it is
an estimate rather than a measurement: re-issuing takes a cohort run, a push and an operator at a
laptop, and nothing here records how long the operator is usually away. That is the number to move
when there is a reading to move it with.

The thirty is a **second copy** of the window `passport.build` stamps, which is the shape L-2 warns
about. It is kept honest by measurement rather than by discipline: `findings()` compares the interval
against the validity window the shipped rows actually carry, and reports `DEADLINE TOO LATE TO ACT
ON` if the two have drifted. Shortening the validity by more than an hour therefore produces a finding
here instead of a deadline that is quietly too late.

**"By more than an hour" is doing real work in that sentence**, and the boundary is exact: the
comparison is strict, so a window short by exactly one hour reads clean and one short by an hour and
a second does not. The comparison carries an hour of slack
(`POLICY_TOLERANCE`), and the slack is not tidiness: the two quantities are policies stated in days,
but what is measured is the gap between two timestamps, and those agree exactly only because
`scripts/cohort.py` happens to hold a single module-level `now`. Take the clock twice — the natural
refactor — and a strict comparison fires `DEADLINE TOO LATE TO ACT ON` over a two-second difference
**on the day the obligation is performed**, which is a false accusation aimed at the operator for
doing the right thing, and a false red teaches walking past a gate exactly as a false green does
(L-5).

The slack was a full day first, and that was the wrong size in an instructive way. A day is exactly
the granularity of the thing being watched, so `validity_days = 29` — the likeliest change anyone
would ever make to a policy stated in whole days, and precisely the L-2 divergence this comparison
exists to detect — passed in silence. It passed the test suite too, because the assertion that
happened to catch it was a duplicate implementation of the same rule, deleted in the same round for
being a duplicate. Two corrections cancelling each other out, with nothing left where they met. An
hour is three orders of magnitude above the noise being tolerated (the elapsed time inside one
cohort run) and a full day below the smallest change worth calling a change. All of it found by
Fable, over three rounds.

## What the gate can and cannot see

| State | Named as |
| --- | --- |
| the cohort ran within the interval | clean — and clean means *checked*, not *did not look* |
| the cohort has been silent past the interval | `SILENCE: cohort_reissue …` + the remedy |
| `web/public/data/registry.json` is missing | `NOT MEASURED: … registry_file_absent` **and** `NOT ASSESSED` for the obligation |
| it exists but is not JSON, or has no `generated_at` | `NOT MEASURED: unreadable:…` **and** `NOT ASSESSED` |
| it reads and lists no subjects | `EMPTY SHIPPED REGISTRY` — a measured zero |
| rows ship with no readable `valid_until` | `NOT MEASURED: … the date this obligation exists to beat IS UNKNOWN` |
| the cohort ran but the build copy is older | `RUN NOT SHIPPED` |
| the build copy is newer than anything `cohort.py` emitted | `SHIPPED AHEAD OF THE RUN` — something other than a cohort run wrote it, and *which* is not knowable from here |
| the emitted copy could not be read, so the two were not compared | `NOT COMPARED: …` |
| `generated_at` read but the rest of the file did not | `PARTIALLY READ` — and the interval is still assessed, on a measurement that was taken |
| the deployed site is older than the build copy | **not visible from here.** The `curl` above is the only instrument, and it is the operator's |

`NEVER_RUN` is deliberately absent from that list. A missing registry file means the cohort has not
run, or the build copy was removed, or the checkout is partial; collapsing those into one answer
would be inventing a measurement to fill a state (invariant 1).

The `NOT ASSESSED` rows above are the same rule applied one level down, and it had to be added to
`Obligation` itself. `last_seen=None` meant *this component has never presented evidence* and *we
could not look* — one value for two states of the world, inside the dataclass built to forbid
exactly that. An absent registry therefore printed "has never presented evidence of participation …
This is a FINDING, not missing data" directly beneath the admission that nothing had been read.
`Obligation.evidence_unreadable` separates them. Found by Fable, in the first draft of this table,
which listed only the honest half of what the code actually printed.

That flag then over-reached in its turn, and the `PARTIALLY READ` row is the correction. It was set
from *the file was not fully readable* rather than from *no timestamp could be read*, so a registry
whose `generated_at` parsed cleanly beside a corrupt `subjects` array reported `IS UNKNOWN` over a
quantity the instrument was holding — and dropped the remedy with it, since the remedy rides on the
`SILENCE` finding. Discarding a measurement you took is the same defect as inventing one you did
not. Two rounds, two directions, same field.

The `NOT COMPARED` row is the same family facing outward: the shipped-vs-emitted check used to stand
down silently when the emitted copy was unreadable, so *the comparison did not run* and *the copies
are in step* both printed nothing. And `SHIPPED AHEAD OF THE RUN` is the second direction of that
comparison, which the first draft never read. Every reading in this gate is taken from the shipped
copy; the file `cohort.py` actually writes, sitting beside it, is the only thing that could say
whether the shipped copy came out of a cohort run at all.

That row names a reading and not a cause, and the first draft of it named a cause — it called the
state a forgery, two hundred lines below the paragraph explaining why `NEVER_RUN` is not in the
list. A hand edit produces it; so does `git checkout <older> -- public/`, a partial restore, or a
revert that touches one path. Same standard, opposite application, in the same file.

## What is deliberately not built

**No second obligation for the deploy.** It would be the fifth state with extra steps: nothing here
can observe a deploy, so an obligation about one would be a component watching a signal it cannot
receive, reporting silence every day and teaching the reader to ignore it. The watcher chain ends at
`external_heartbeat` and it ends on purpose (ABI-16-7) — the operator's `curl` is that terminus, and
it is a person, not another module.

**No automatic copy from `public/` into `web/public/data/`.** The two copies are kept in step by
hand and the gate reports the divergence rather than hiding it. A script that copied silently would
remove the finding without removing the failure mode.

---

# The blocker: is there anywhere to publish yet?

T-2.15b publishes a passport's projection on-chain, into the ERC-8004 Validation Registry — the
distribution channel ADR-0001 chose. It cannot be scheduled, and the reason is not ours:
`docs/MEASUREMENT_QM1.md` measured on 2026-08-20 that **the Validation Registry is not deployed on
any chain**. The reference implementation lists Identity and Reputation registry addresses across
twenty-odd chains and states that the Validation Registry portion is still under active update,
with no addresses given at all.

Nothing about this repository expires while that stays true, and that is exactly why it needed an
instrument. A deadline produces a reminder; a blocker produces nothing, changes on somebody else's
schedule, and sends no event here. Left alone, "we cannot" becomes "we forgot" with no moment at
which anybody was wrong — and the plan goes on stating a blocker whose last measurement is months
old, which is a claim stronger than its artefact, of our own making.

## The habit

**Who.** The same reader as above: the executing agent, on the audit host, inside a task cycle.

**When.** On the same beat as the re-issue habit — `Interval.WHILE_BLOCKED` is defined as
`MAX_AGE[BEFORE_REISSUE]`, twenty-three days, **by reference and not as a number**. Nothing in the
world sets this deadline, so there was nothing to derive it from; what is real is the cadence at
which anybody is actually standing in this tree doing liveness work, and that is the cohort's. A
faster interval would be red most mornings with no act available to clear it, which is the same
reason the section above refuses an obligation for the deploy.

**What.** Four commands, and — unlike the cohort's — no last step held by anybody else:

```bash
python3 scripts/watch_validation_registry.py    # one anonymous read; the read needs no credential
python3 -m src.liveness.commitments             # the line that prints the reading
git add public/erc8004 && git commit -m "re-check the validation target: still no address"
./scripts/push.sh
```

The commit is on the list for the same reason it is on the cohort's: the record is tracked, so a
run that writes dirties the tree and `push.sh` stops there. A run that established nothing still
writes — into the attempt block, carrying the measurement forward verbatim — so it is committable
too. The one exception is a record this script cannot read well enough to carry that block
forward: it reports `NOT WRITTEN`, leaves the file byte-identical, and the tree stays clean.
Overwriting there would replace "we could not read this" with "this never happened". **No deploy is involved** — the record is deliberately
not copied into `web/public/data/`, because nothing on provek.dev makes any claim about the
Validation Registry and publishing the file would manufacture a claim with no reader. The read
needs no credential; `push.sh` still does, which is why that qualifier is attached to the read and
not to the sequence.

## What the gate can and cannot see

**The record has two blocks and the table below has two halves, because there are two facts.**
`measurement` is the last run that *established* something; the interval rides it, so a run that
measures nothing never advances the clock. `last_attempt` is what the last run did, whatever that
was; the gate reports it the same minute — a non-measurement on its own line, a `target_present`
as `TARGET APPEARED` from whichever block holds it, and any disagreement between the two blocks as
`BLOCKS DISAGREE`. A draft that kept only the first is the worst defect this
component has had — see the end of this section.

| State | Named as |
| --- | --- |
| the last run measured, within the interval, and the list carries no address | clean — `python3 -m src.liveness.commitments` prints the reading; the gates print only red or green |
| no run has measured for longer than the interval | `SILENCE: validation_target_watch …` + its own remedy |
| a row spelled `ValidationRegistry`, naming no other registry, carries an address | **`TARGET APPEARED`** — a red, on good news, deliberately |
| a line names validation beside an address and could be either | `NOT MEASURED: … unreadable:validation_row_not_conclusive`, quoting the line — cleared by teaching the parser, not by another run |
| no HTTP client could be launched here | `NOT MEASURED: … check_did_not_run:no_http_client` — entirely ours |
| the request never completed | `NOT MEASURED: … check_did_not_run:no_answer` — **whose** failure is not established, and the name refuses to guess |
| the source answered and declined | `NOT MEASURED: … check_did_not_run:source_answered_non_200`, with the status in the record |
| the list answered but an anchor registry could not be found in it | `NOT MEASURED: … unreadable:deployment_list_not_recognised` |
| every run so far failed, so `measurement` is `null` | the attempt's own `NOT MEASURED`, **and** `SILENCE: … has never presented evidence` — both true, and the record was read perfectly |
| the `measurement` key is **absent** rather than `null` | `NOT MEASURED: … unreadable:no_measurement_key` **and** `NOT ASSESSED` — an absent key is somebody else's shape, not this project saying "never" |
| the two blocks cannot have come from one run | `BLOCKS DISAGREE` — a partial restore, a merge taking one block from each side, or a hand edit; **which** is not knowable from here |
| the last run measured `target_present` while the measurement block is older | **`TARGET APPEARED`** fires from the attempt block too, beside `BLOCKS DISAGREE` |
| the record is missing, is not JSON, or has no `last_attempt` block | `NOT MEASURED: …` **and** `NOT ASSESSED` for the obligation |
| `checked_at` read but the state did not | `PARTIALLY READ` — the interval is still assessed, on a measurement that was taken |
| the state read but `checked_at` did not | `PARTIALLY READ` — the interval is `NOT ASSESSED`, and **what the list said is still reported**, including `TARGET APPEARED` |
| a deployment the reference implementation has not written down | **not visible from here.** This reads a document, not a chain |
| a deployment written in a shape this parser cannot read — label in a column header, or split from its address across lines — while the anchors stay intact | **reported as `no_target`, a MEASURED absence.** The anchors cannot catch it, because they are still there and still readable; this is the residue the control does not cover |

The five middle rows all describe the **last attempt**, and they fire while the measurement below
them is still perfectly good — that is the point. Three of them are one distinction: **"we could
not read it" is not "they would not answer"** (L-11). A single `source_refused` covered all three
in the first draft, which asserted a fact about somebody else's server on the evidence that a
socket had not opened on ours.

**The anchors are the load-bearing part, and what they establish is narrower than it sounds.**
`no_target` is the answer this watch returns nearly every time, so `no_target` is the answer an
instrument that had stopped looking would also return — for ever, silently, and precisely in the
state where a real deployment would be missed. The Identity and Reputation registries *are*
deployed and *are* in that list, so the parser requires **both** of them to be findable beside
addresses before it will report an absence — either one going missing is enough to refuse.
`evidence/RED-015-absence-measured-with-a-broken-instrument.txt` is that control removed, with an
empty document reading as "there is no Validation Registry".

What that rules out is the document being replaced, emptied, moved behind an error page, or
restructured past the shape this parser reads. What it does **not** rule out is a document that
keeps two rows naming those registries while the current list moves elsewhere. That residue is
stated rather than left to be discovered: it is the price of reading a README, and it is the reason
the reading carries the document's `sha256` and is re-taken rather than trusted.

**The target is matched in three tiers, and the middle one is the interesting answer.** A row still
spelled `ValidationRegistry` — with any suffix — beside an address is a deployment, and that is
`TARGET APPEARED`. A line that only mentions validation beside an address is neither: it might be a
row renamed to `Validation`, and it might be `validationRequest(0x…, 42, …)` in a code sample, and
this reader cannot tell. It reports **`not_measured`**, quotes the line, and names both exits —
schedule the step, or tighten the parser with a test.

Two earlier drafts got that wrong in opposite directions and both are worth keeping. The first
matched the exact spelling only, so a renamed row read as `no_target` with the anchors green, for
as long as the document kept the new name — the anchors cannot catch it, because it is a different
label. The second matched `validation` alone and called a false positive "a red one reading of the
document clears"; the section this parser reads already contains `validationRequest(...)`,
`getValidationStatus` and an event signature taking an `address`, so one example value would have
had the gate ordering somebody to schedule on-chain publication against a line of documentation.
**A red that instructs work nobody should do is not cheaper than a silence.** The third tier is
what neither draft had: a name for "I cannot tell", which is what invariant 1 asks for anyway.

A positive reading is never overridden by the control, and the ordering in `parse()` is where that
is decided: if an address IS found, that is a measurement, and reporting `unrecognised` over it
would discard a reading the instrument was holding. The control protects the negative answer,
because the negative answer is the only one that can be produced by not looking.

### Two drafts of the write rule, and the second was the worse one

**Draft one wrote the latest run over the top.** An operator who met `SILENCE` and followed the
remedy exactly as printed on a day the source was 5xx thereby replaced `no_target` with a
non-measurement, turned two assertions about the real tree red, and left a dirty file that step
three of that same remedy — `./scripts/push.sh` — then refused to send. A false red at the moment
somebody performs the habit, with the recovery step written down nowhere.

**Draft two refused to overwrite a measurement, and that was worse.** The record went on saying
`no_target` inside its interval while the last run had reported the deployment list unrecognisable
— and the sweep returned **nothing**. A green gate meaning *did not look*, for up to twenty-three
days, in the layer built to forbid exactly that, introduced by the fix for draft one. The only
witness was the stdout of a script that nothing runs on a clock.

Both drafts were choosing which of two facts to keep, and there are two facts, so there are two
blocks. A run that establishes nothing still writes — into the attempt block, never over the
measurement — so it stays committable, the clock is not advanced, and the finding is visible the
same minute. What it says changes as the runs do — that is the point of keeping the attempt — and
what it never does is disappear while the thing it reports is still true.

## Why the finding fires on GOOD news

When an address appears, the build stops. That is not a mistake in the sign of a comparison.

Three things go wrong at the same moment, and none of them announces itself: `MEASUREMENT_QM1.md`
still says NOT DEPLOYED, the plan still says T-2.15b cannot be scheduled, and the
**contract-without-audit** risk — named in the plan and never decided, because there was nothing to
decide about — becomes live. A green run would let all three stand while the reason for them had
gone. So the finding names the address it found, names the step that is unblocked, and names the
document that has become false; clearing it is a decision recorded in `DECISIONS.md`, not a rerun.

## What runs this in the state it exists for, and how long that lasts

The same daily `schedule:` in `gates.yml` — no second clock, and the argument above it applies
unchanged. What does **not** carry over is the arithmetic that follows it, and borrowing the
conclusion would be borrowing a number away from the noun it was computed for.

That paragraph's load-bearing step is that the cohort's whole lifecycle — deadline on 2026-09-12,
lapse on 2026-09-19 — happens inside the sixty-day window before GitHub disables the schedule for
inactivity. **This obligation has no lapse.** It fires from day twenty-three and never terminates:
there is no date on which being late stops mattering, because nothing expires. So the honest
statement is the plainer one: after roughly sixty days of total inaction the schedule switches
itself off and both alarms stop together, having by then said so every morning for about a month.
Nothing is lost that a person returning to the repository would not immediately see — the door
still goes red on the next push, because the sweep runs in the test suite as well as on the clock.

## This is not the second obligation the cohort section refuses

That refusal was specific: **nothing here can observe a deploy**, so an obligation about one would
be a component watching a signal it cannot receive, reporting silence every day and teaching the
reader to ignore it. The difference is the instrument. This state *is* observable from this host,
by one anonymous HTTP request that any third party could repeat, and the obligation reports silence
only when nobody has taken that reading. The rule both cases follow is the same one: an obligation
is worth declaring exactly when something can actually be measured to satisfy it.

And the chain still stops at a person (ABI-16-7). The `TARGET APPEARED` finding is read by whoever
is at the door or in the daily gates run; no module decides what to do about it, and none is added.

