# Project laws

Grows as work proceeds. Every law MUST have an anchor in `enforced_by.yaml`.
A law with no armed gate is a defect, not a note.

## L-1 A return value that means two states of the world
"No data" and "the source is dead" must never read identically. Seven instances in the operator's
systems; a twelve-week source outage hid in exactly this shape.
Anchor: LAW-NOT-MEASURED.

## L-2 A rule written in more than one place survives its own repeal
Before declaring a rule repealed, find ALL of its copies.
Anchor: LAW-DECISION-RATCHET.

## L-3 Measure the shipped artefact
A file in the repository, a registry row and an exit code are not what the consumer receives.
Anchor: LAW-MEASURE-SHIPPED.

## L-4 A gate that does not stop is not a gate
The first push succeeded while the ratchet was red, because the checks ran without `set -e`.
Anchor: LAW-GATE-MUST-BLOCK.

## L-5 A pipeline's exit status belongs to its LAST command
The secret scan ended in `| head -5` and therefore always reported success, blocking a clean tree.
A false red teaches bypassing the gate exactly as a false green does.
Anchor: LAW-GATE-MUST-BLOCK.

## L-6 A checker that inspects one shape reports success on every other
The scope ratchet looked only at `*.py`; shell scripts were outside supervision entirely.
Anchor: LAW-SCOPE-RATCHET.

## L-7 A rule that lives only in a comment is not enforced
The weak-signal limiters were a docstring note until they became code.
Anchor: LAW-WEAK-SIGNAL-LIMITERS.

## L-8 On a shared host, a file you cannot write may still be one you read

`git commit -F /tmp/m.txt` picked up ANOTHER project's commit message. The host has ten project
users; `/tmp/m.txt` already existed and belonged to one of them. The write failed with permission
denied - which is visible - but the read succeeded silently, and the commit landed carrying a
message about a completely different codebase.

Two things made it survivable: the commit had not been pushed, and the language gate would have
caught it at the door anyway. Neither is a reason to rely on luck.

Rule: scratch files go to the project's own directory, never to a shared `/tmp`. The same host
already carries a related trap - a stray `/tmp/re.py` shadows the standard library for any script
run from there.

Anchor: no code gate. This is a working habit, and it is recorded as such rather than pretended to
be enforced - a law with a fake anchor is worse than an honest note.

## L-9 Trace the path to the acceptance criterion BEFORE taking the step

A task whose gate is a live URL begins by establishing how a commit becomes that URL. This one did
not: the page was built, reviewed, corrected and pushed before anyone asked what publishes it, and
the answer turned out to be a manual `wrangler pages deploy` needing a credential this host does not
hold. A push to `main` publishes nothing here.

The path was readable in advance - `web/wrangler.toml`, a `.wrangler/cache` in the tree, and an
`AUDIT.md` that names the Pages project while saying nothing about the mechanism. Cost was small
(the push was needed anyway) and the damage was to the ORDER in which facts were discovered, which
is exactly the damage that is invisible until it is large.

Anchor: no code gate. A checker cannot know which of a task's criteria is the load-bearing one. It
is recorded as a habit, in L-8's form, rather than dressed as an enforced rule.

## L-10 A wrong instrument reports absence, and absence reads as a finding

`/commits/{sha}/status` returned zero statuses for every commit in this repository, and that was
read as "no deploy integration". The reading happened to be right; the measurement was empty.
`/commits/{sha}/check-runs` returns four successful runs on the same commits - the legacy endpoint
simply does not carry what the modern one does. A conclusion drawn from an instrument that cannot
see the quantity is not evidence, and it is more dangerous when correct, because it will be repeated.

This extends L-1 and specification 2.9 by a third sibling. Beside `nothing_qualified` and
`unreadable` sits **the wrong source was asked** - a state that answers HTTP 200 with an empty list
and is therefore indistinguishable from a true zero at the point of reading.

Found by Fable while refuting a brief in which the empty measurement was offered as proof.

Anchor: no code gate for the general rule - a checker cannot know that an endpoint is blind. One
instance of it IS armed, and it is the model to copy: every passport publishes the `access_channel`
its evidence arrived through, so a verdict carries the instrument beside the reading
(LAW-GRANTED-CHANNEL-ONLY, `tests/test_granted_channel_only.py`).

## L-11 The origin answers a different question depending on who asks

The Bing probe read `https://provek.dev/BingSiteAuth.xml` with Python's default user agent and got
`403` - as it did for the homepage, which a browser agent gets `200` for. Cloudflare was refusing
the CLIENT, and the probe was one line from writing that refusal into the log as
`carries_expected_code: false`, i.e. as a finding about whether the site publishes the file.

What makes it worth a law of its own beside L-10 is WHEN it happened. The probe was written that
same hour, deliberately, to honour L-10 - it already ran a control site beside every zero-capable
API call. The lesson did not transfer, because it had been learned in the shape "ask the endpoint
that carries the quantity" and this failure has a different mechanism: the right endpoint, asked
correctly, returning a status that encodes the asker's identity rather than the resource's state.

Rule: a status code is not a measurement until the client has been ruled out as its cause. `404` is
absence. `403`, `429` and `5xx` are the server declining to say, and must land in a state named for
not knowing - never in the same field as a measured `false`. The general form: **before recording
absence, establish that the instrument would have been able to see presence.**

Anchor: no code gate here - this repository does not own the probe, which lives at
`~/orchestra/bing_probe.py` (a Bing client is bound to no `ABI-*` requirement, so `scripts/` would
have to be rubber-stamped to hold it). Recorded in L-8's and L-9's form as a habit, not dressed as
an enforced rule.

## L-12 A ratchet that scans two directories reports success on the third

`scripts/ratchet_scope.py` scans `src` and `scripts` for `*.py` and `*.sh`. The entire `web/`
directory - twelve components, the static emit that produces every shipped page, and now the note
emit - has never been under scope supervision at all. Nothing there needs an `ABI-*` binding,
because nothing there is looked at.

This was found while placing the note generator, and it is recorded rather than fixed, because both
available fixes are worse than the hole. Extending the ratchet to `web/**/*.mjs` immediately demands
an ABI binding for `prerender.mjs`, and no requirement in the master specification covers static
emit - so the binding would be invented to satisfy the checker, which is the rubber stamp the
ratchet's own docstring names as the degeneration to watch for. Leaving the generator in `web/`
without saying anything would have been routing around the ratchet by choosing a file extension.

What was done instead: the model-facing generator lives outside the repository entirely
(`~/orchestra/notes_gen.py`), by the precedent D-17 set for the keyword collector, and only
deterministic emit sits in `web/`. The hole is unchanged and now written down.

It is L-6's shape one level up. L-6 was a checker that inspected one file type; this is a checker
that inspects one part of the tree. The general form: **before trusting a green ratchet, read what
it scans, not what it reports.**

Anchor: no code gate. Closing it properly is its own task with its own red run, and dressing this
note as an enforced rule would be the fake anchor L-8 refuses.

## L-13 A rule whose only beneficiary is today's acceptance criterion

The scheduler needed a cycle to run inside the session that installed it, and the jittered slot for
the day had already passed. The rule nearly written was: "on the first tick after installation
there is no record of a previous cycle, so run immediately". It reads like anacron semantics. It is
not. Real catch-up serves the schedule for as long as the schedule exists - a slot missed to a
reboot, to a deferral, to an install that happened late, all caught up the same way. The rule
drafted here fires exactly once, on the day of its own acceptance, and is dead code the following
morning.

The test that separates the two takes one question, and it is worth asking of any rule written
while looking at whether the task closes: **does this rule still do work tomorrow?** If it does, it
is a rule. If its last useful act was to make today's criterion true, it is the measurement being
fitted to the verdict, and the fit is invisible afterwards because the code looks principled.

There is a second edge on the same tool. The jitter seed is chosen by the agent that is judged on
where the slot lands, and nothing outside can detect a seed quietly re-rolled until the slot is
convenient - the journal records only the seed that survived. Cryptography does not fix that;
removing the motive does. Under a general catch-up rule the first cycle runs wherever the slot
sits, so there is nothing to gain by re-rolling. Where a knob cannot be audited, delete the reason
to turn it.

Found by Fable, from a brief that flagged the rule as suspect without being able to say why.

Anchor: no code gate. A checker cannot tell a principled rule from a convenient one; that is the
whole difficulty. Recorded as a habit in L-8's form rather than dressed as an enforced rule.

## L-14 A measurement already taken is not yet a reading

`bing_state.json` was captured at 11:45 and read at 14:00 to establish that Bing ownership is
blocked behind a deploy this host cannot perform. The chain "verification needs BingSiteAuth.xml,
the file needs a deploy, the deploy needs a credential we lack" is correct in every link, and it
was used to argue that half the task was unreachable. Four lines below the field that was read sits
`dns_cname_record` - Bing offers ownership verification by DNS record, which needs no deploy, no
wrangler and no credential, and which closes the same blockage in a minute of the operator's time.

Nothing failed. The instrument answered, the answer was stored, the file was opened, and the
reading stopped at the first field that confirmed the expected shape. That is the failure mode:
not an absent measurement but a complete one, consulted until it agreed. The cost here was nearly
an operator request for the expensive unblock while the cheap one sat unmentioned in the evidence.

This is L-10's family - an instrument that cannot see the quantity - one step further in. There the
wrong source was asked; here the right source answered in full and the rest of its answer was never
read. The general form: **when a measurement confirms the expectation, keep reading; a file is not
a reading until the part that would have contradicted you has been looked at.**

Found by Fable, in the same file the brief cited as its own evidence.

Anchor: no code gate. Recorded in L-8's form.

## L-15 A process that is killed leaves a journal indistinguishable from one still running

The note capture died twice on 2026-08-20 without writing a line about it. The 13:29 run wrote five
of six prose sections and stopped at 13:39:02; the 13:43 run wrote `plan ok` at 13:45:34 and
stopped eighteen seconds before the orchestra opened its next iteration. Both journals simply end.
`notes_gen.py` is careful - it raises named refusals, it prints both streams, a failed model is a
RED line and never a skip - and none of that helps, because SIGKILL runs no handler. Every
discipline about naming failures is discipline about failures the process survives.

So the last writer cannot be the one who reports the death. The only witness available is the next
run: a marker persisted BEFORE the work starts and cleared after it finishes, so a successor
finding it still set knows its predecessor was killed rather than finished, and says so with the
timestamp of the last thing it managed to write. `notes_cron.py` opens each cycle this way and
reports `previous_cycle_interrupted`.

It is L-1 in the shape of a log file. "The cycle is running" and "the cycle was killed" are two
states of the world, and a journal that ends is how both of them look.

Anchor: no code gate in this repository - the scheduler that implements the marker lives outside
it (D-19), so there is nothing here to arm against. Naming a `LAW-*` for it would be an anchor
pointing at nothing, which L-8 refuses.

## L-16 A suite that skips itself is counted among the armed

Four laws were registered for the method notes, each with a gate file and a test module, and
`ratchet_decisions.py` reported "40 laws, all armed". Three of the four modules opened with
`pytestmark = skipif(not sources())`, and the fourth skipped its only counting test the same way.
Zero notes were captured. So in the one state that actually existed, every assertion about the
notes skipped - and that is the state in which the build shipped a Method page linking to
`/method/notes/`, a route `prerender.mjs` emits only when a note exists. One dangling link and one
present-tense claim that a body of writing existed, on the site whose product is catching claims
that outrun their artefact, past four laws written to prevent exactly that.

Two failures stack here, and only the second one is interesting.

The first is ordinary: a suite conditioned on its own subject cannot speak about the subject's
absence. `skipif(not sources())` is the sensible-looking line that makes "the notes are correct"
and "there are no notes" read identically - L-1, in a `pytestmark`.

The second is that the tool built to catch unenforced rules SAW nothing wrong, because
`check()` resolves two paths and asks whether the files exist. `present` and `armed` are different
states of the world and it printed the stronger one. That is this project's founding defect turned
on its own control instrument, and it is worse there than anywhere else: this ratchet is what the
other gates are audited with, so a claim it overstates is a claim nothing downstream can correct.
The report now says what it measures - "every gate and test present" - which is a smaller sentence
and a true one.

The general form: **a green suite tells you about the runs that happened; ask what it asserted in
the state you are actually in.** Where a rule has an empty-set case, the empty set is a case, not a
reason to skip - and it is usually the case that ships.

Anchor: NO CODE GATE FOR THE GENERAL RULE, and the first draft of this line claimed one. It named
LAW-NOTES-ENTRANCE — which knows nothing about skipping and nothing about what the ratchet prints,
and is an ILLUSTRATION of the lesson rather than a gate on it. Writing it as the anchor was the
fake anchor L-8 refuses, committed in the very lesson about instruments that report a stronger
state than they measure. Fable caught it in the patch that fixed the original.

What the general rule would need is a ratchet that refuses a law whose test module collects zero
un-skipped assertions in the current state of the tree. That is a real gate and it is not written
here; the four modules that skip themselves at zero notes still do.

Two instances ARE armed, and they are the model to copy rather than a fix for the four:

  * `LAW-NOTES-ENTRANCE` (`tests/test_notes_entrance.py`) never skips — it asserts a biconditional,
    red if the entrance is offered while nothing is captured and red if a note is captured while no
    page names the entrance. Both directions were made to fail before it was trusted
    (`evidence/RED-006-notes-entrance-without-notes.txt`);
  * `scripts/ratchet_decisions.py` now separates `present` from `reaches a clone`: a law whose gate
    or test is untracked is dangling, because five of them were, and it says `unknown` rather than
    `clean` when git cannot be asked at all (`evidence/RED-007-law-that-never-leaves-this-host.txt`).

And the emitted-artefact sweep that skipped in CI for want of a build now has one
(`.github/workflows/gates.yml`, job `shipped`), because a check that skips where it matters is the
subject of this lesson rather than an exception to it.

## L-17 A promise made by a step that the run never reaches

D-19 was written as "every step writes one line naming its own state, and two of those steps are
refusals today" - the daily naming of the blocked publication channel was the decision's whole
selling point. The steps run in series and a red capture raises past the remainder, so on both of
the cycle's only two real runs the journal ended at `capture RED` and no line about `deploy` or
`bing_submit` was ever written. The two refusals the decision is NAMED after have never once been
recorded by the mechanism that promises to record them daily; they were established by hand.

What makes it worth a line beside L-15 is that nothing was silent. Every step that ran reported
itself correctly, the failure was named, the exit code was right, and the journal is honest about
everything it contains. The claim was about steps the journal never got to - and the difference
between "reported blocked" and "never reached" is invisible in a log that only ever shows the
former when things go well.

Adjacent, found in the same reading and recorded before it is lost: the cycle catches `Blocked`
from `deploy` inline and still runs `bing_submit`, so a day when ownership verification is closed
but the deploy is not would submit to Bing the URL of a page that does not exist - an automated
claim stronger than its artefact. And `sitemap_urls` is saved on blocked cycles too, so a URL's
novelty is spent on the day it is BUILT rather than the day it is published: pages built while the
channel is blocked would later be `nothing_to_submit` and never submitted at all.

The general form: **before believing that a pipeline reports something daily, find the report in
the journal.** A step's promise is worth what its predecessors' success rate is.

Anchor: no code gate. `notes_cron.py` is outside this repository (D-19) and reordering its steps is
a change that cannot be exercised while the capture is red, so what was corrected is the sentence
in D-19, not the code. Recorded in L-8's form rather than dressed as an enforced rule.

## L-18 A test that builds its own subject can never find the subject missing

`src/liveness/obligations.py` is the module that defines silence as a finding, names
`produces_result_nobody_reads` as the fifth state of sleeping code, and reports an empty registry as
suspicious rather than clean. It shipped with T-2.10, passed seven tests, and carried two laws in
`enforced_by.yaml`. For its entire life nothing declared an obligation into it: every `Registry` in
the repository was constructed inside a test and filled by the same test, three lines later. The
layer whose subject is code that runs and is never read was code that ran and was never read, and
`PRODUCT.md` listed it under *works today*.

Seven passing tests could not see it, and the reason is the interesting part. Each one begins
`r = Registry()` and then declares into it, so the empty case — the case that was actually true of
the whole project — is a state those tests construct their way out of before asserting anything.
`test_empty_registry_is_SUSPICIOUS_not_clean` even asserts the right thing about it, on a registry
that exists for one line inside the test. The assertion is correct and the world it describes is
not the world the code was in.

This is L-16 one turn further round. There the suites SKIPPED in the state that shipped; here they
run, pass, and are about a subject they manufactured. A fixture is a claim about the input, and a
suite made entirely of fixtures has no way to notice that no real caller supplies one.

The general form: **for any component, ask who constructs it in production. If the honest answer is
"the tests do", the green suite is measuring a subject that exists only during the measurement.**
That question is worth asking of the whole `src/` tree; it was asked of the liveness layer because
a task went looking for the reissue commitment and found the registry empty.

Anchor: no code gate for the general rule — a checker cannot tell a production caller from a test
one without knowing what production means for each module. Naming a `LAW-*` for it would be the
fake anchor L-8 refuses, and L-16's first draft committed exactly that mistake in exactly this
place. The INSTANCE is armed and is the model to copy: `LAW-REISSUE-OR-FINDING`
(`src/liveness/commitments.py`, `tests/test_reissue_obligation.py`) declares the incubator's own
obligation outside any test and sweeps it against the real clock, so the gate goes red once the
cohort has been silent past its interval. The red run is
`evidence/RED-010-cohort-silence-is-not-a-finding.txt`.

## L-19 A gate that runs only when somebody acts cannot observe inaction

The gate above was written to fire when nobody re-runs the cohort, and four documents said it fires
on its own. Every trigger that could have run it — `push`, `pull_request`, `workflow_dispatch` in
`gates.yml`, and `scripts/push.sh` at the door — begins with a person doing something. So in the
single state the obligation exists for, where nobody does anything, the suite would never have been
executed, nothing would have gone red, and the eight published rows would have lapsed on 2026-09-19
in exactly the silence the change was built to end. The test was correct, armed, unskippable, and
unreached.

Nothing about it looked wrong. The assertion is real, its red run is in `evidence/`, and running the
suite by hand demonstrates the failure perfectly — which is the trap, because the demonstration is
performed by the person whose absence is the thing being detected. A tripwire that only trips when
you walk into it measures your presence.

It is L-17's sibling. There the promise belonged to a step the run never reached; here it belongs to
a run that never happens. Both are invisible in the logs, and for the same reason: what is missing
produces no line.

The general form: **for any check about something NOT happening, name the thing that will execute
the check in the world where that something does not happen.** If the answer requires a person, the
check measures the person.

Found by Fable, refuting the change that claimed the property.

There is a tail to it. The clock chosen was GitHub's `schedule:`, and GitHub disables a public
repository's schedules after sixty days with no repository activity — so the fix has the same shape
as the defect one layer out: it works until the inaction is total, and then it stops, quietly. Here
it is harmless, and the arithmetic is the point rather than the worry: the finding fires daily from
day 23 and the rows lapse at day 30, so the whole lifecycle runs inside the sixty. The first draft
of this paragraph guessed instead — "the first alarm survives, everything after it does not" — and
was wrong in the safe direction, which is still a stated limit that is not the measured one, written
into the lesson about clocks. The bound is computed once, in `docs/LIVENESS_OPERATIONS.md`.

Anchor: `LAW-REISSUE-OR-FINDING` covers the instance — `.github/workflows/gates.yml` carries a daily
`schedule:`, and `test_the_gate_has_a_clock_and_not_only_a_door` fails the build if it is removed.
That test earned its own instrument control the hard way: the first version asked whether the
strings `schedule:` and `cron:` appeared anywhere in the file, which a commented-out trigger
satisfies exactly as well as a live one — `present` reported as `armed`, L-16 committed inside the
gate written to close this lesson. `test_the_clock_check_is_able_to_fail` now holds it.

The general rule has no gate: a checker cannot tell which of a repository's tests are about absence.
The limits on the instance are recorded once, in `docs/LIVENESS_OPERATIONS.md`, rather than listed
again here — including the one in L-10's form, that the trigger being in the file is checkable from
this host and its dispatch by GitHub is not.
