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

**Closed in T-C5, by the condition this entry itself named.** "Cannot be exercised while the capture
is red" was a real reason and it expired: T-C4 turned the capture green, so on 2026-08-24 both
adjacent defects above were fixed rather than recorded a second time. `bing_submit` is now
downstream of the deploy and submits only URLs that answered `200` when read back from
`https://provek.dev`; the novelty baseline is the live sitemap rather than a `sitemap_urls` field
that was saved even on cycles which published nothing. D-25 carries both. What is worth keeping is
not the defect but the shape of the parking: a finding held behind "cannot be exercised yet" needs
the event that lifts it written down beside it, or the parking cannot be told from dropping it.

Half of it is now a gate, and it is the half that could move into the repository.
`LAW-PUBLISH-JUDGED-TREE` (`scripts/publishable_tree.py`) holds the rule that the unattended cycle
publishes only a tree the gates judged — a hazard that arrived in the same commit as the fix,
because until it the deploy step had never once run. The step ordering still has no gate and still
cannot have one from here: the file it lives in does not reach a clone.

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

## L-20 Closing the instance leaves the mechanism, and the mechanism is the defect

`gates.yml` opens "THE SAME GATES AS scripts/push.sh". It was not true: CI ran `ruff` and the door
never had, so four runs went out clean through the door and turned `main` red. The fix was to add
ruff to the door. That fix was correct and it was not enough, because what made the drift last was
not the missing tool — it was that a sentence claimed the two lists were one list while nothing
compared them. A rule written in more than one place survives its own repeal (L-2); here the two
copies were a workflow and a shell script, and the copy that was wrong was the one nobody ran.

Writing the comparison as a gate rather than a sentence found two more divergences in the first
run, both older than the ruff one and neither suspected: the door built no site, so the assertions
that sweep the emitted pages read whatever `web/dist` was lying on the host or skipped outright;
and the door enforced no coverage floor while CI required 70%. Three instances, one mechanism, and
the two that had never been noticed were found by the check rather than by another red build.

The general form: **when a divergence between two copies of a rule is found, the finding is the
absence of the comparison, not the value that differed.** Fixing the value returns the system to
the state it was in the day before the last drift started.

There is a second half, and it is the one that took longer to see. `mypy` sat beside ruff running
`|| true`, and the note under it promised it would become blocking "once a clean baseline exists —
and that promise is recorded here rather than left as an intention". Recording it *is* leaving it
as an intention. Nothing measured the condition, nothing would fire when it was met, and nothing
would notice if it never was — L-7 in the document that describes this project's gates, four lines
above a section kept as a warning about a dated condition that had expired unnoticed.

`|| true` was also invariant 1 in its purest shape. It suppressed the findings, which was intended,
and it suppressed mypy failing to START, which was not: an instrument that could not run printed
exactly what a clean baseline prints. The single reading that would have ended the advisory state
was indistinguishable from a crash, so the gate could not have moved forward even in principle.

Anchor: `LAW-DOOR-MATCHES-ARBITER` (`scripts/push.sh`, `tests/test_door_matches_ci.py`). The
comparison is checked in both directions, the advisory state carries a date that goes red on its
own, and the date sits inside GitHub's sixty-day schedule-disable window for L-19's reason — a
deadline the clock cannot reach in the state it exists for is another promise. The red runs are
`evidence/RED-011-door-checks-less-than-the-arbiter.txt`.

## L-21 A fix that is written but never called documents itself into looking done

`tests/test_door_matches_ci.py` was written to end the door/arbiter drift of L-20. Three of its
repairs — `executable_lines`, `CHAINS`, `BENIGN_ACTIONS` — were defined, given docstrings naming
the exact defect each closed, and **never called**. `grep` found every one of them at its own
definition and nowhere else. The suite was green, the file read as thorough, and all three holes
were open: a door with lint, site and tests commented out was reported as matching CI, because the
prose explaining why those steps matter still contained the strings being matched.

That is this repository's subject defect — a claim stronger than its artefact — committed inside
the check written to end it, and it is the second time in one task that the *documentation of a
fix* was mistaken for the fix. The green suite was not evidence of anything: no test exercised the
helpers, so nothing could tell a wired-in repair from a decorative one.

**A repair is not landed until something fails without it.** Not a test that calls it — a test that
goes red when the call is removed. Mutation is the cheap form: take out the fix, watch the suite,
and confirm exactly one test dies and it is the right one. Applied to the six defects Fable then
found, this caught two mutations that never applied at all because shell quoting mangled the
anchor — a "passing" run that had tested nothing, which is the same false green one level up.

The corollary is about review. Reading the diff would not have caught this; the diff looks like
three careful fixes. What caught it was asking, of each new symbol, *who calls this?* — a question
about the artefact rather than about the prose describing it. **Dead code in a gate is not tidiness
debt; it is an unarmed gate that reads as an armed one** (L-16, moved from the gate to the gate's
own implementation).

Anchor: `LAW-DOOR-MATCHES-ARBITER`. The reds, including the five false greens Fable produced
against the repaired file and the mutation that kills each fix, are RED 5 and RED 6 in
`evidence/RED-011-door-checks-less-than-the-arbiter.txt`.

## L-22 A survey hides the absence collapse inside its own denominator

Q-M1 step 2 sampled 100 of the 50,275 ERC-8004 identities and could not read 27 of them: 20 behind
one host that serves no TLS certificate at all, plus a 404, a 502, a timeout, and four soft 404s
that answered HTTP 200 with a single-page-app shell. The obvious arithmetic - matched over drawn -
would have folded all 27 into the non-matchers and published a rate that was partly a report on
our own broken instruments, with every total still adding up correctly.

This is L-1, but a survey is where it is hardest to see. Elsewhere the two states are two return
values and the collapse is visible at the call site. Here the unreadable rows are already inside
the sample, so the collapse leaves the sums intact and changes only what the number means.

The measurement therefore publishes a BAND - every unreadable identity counted against, then every
one counted for - and the go/no-go code is run at both ends. When both ends give the same class of
verdict, the width of the band is not worth closing.

Anchor: LAW-SURVEY-ABSENCE.

## L-23 The instrument was wrong three times in one run, and twice it said "absent"

Reading the registry needed three corrections before any number was honest, and all three had the
shape L-10 named:

* `tokenURI` was read as a pointer. A run of identities stores the registration document ITSELF in
  that slot - bare JSON, no scheme - so the reader split on `:`, found `{"name"` where a scheme
  belonged, and filed five READABLE documents as `unsupported scheme`.
* Four identities answered HTTP 200 with an HTML shell. A 200 was taken for an artefact, and four
  error pages were on their way to a human to be classified as businesses.
* `curl rc=35` was recorded as the reason. A number is not a reason: it took a separate
  investigation to establish that the host offers no certificate at all, which is a fact about the
  subject, where a timeout would have been a fact about us.

None of the three would have produced an error. Two would have produced ABSENCE, and absence reads
as a finding. The rule: before a sweep is allowed to produce a rate, every distinct failure mode in
it is opened and named. The cost here was three probes; the alternative was a published number.

Anchor: LAW-SURVEY-ABSENCE.

## L-24 A per-row rule cannot count an entity that owns ten thousand rows

Q-M1 step 2 classified 100 sampled ERC-8004 identities against §2.7 and found zero businesses.
Every individual label was defensible: a row of a 10,000-piece collection is not a business in its
own right. The total was not. Four operators were running collections behind those rows, two of
them serving a live artefact on demand, and the per-identity rule scored each of them zero - not
because they failed a condition, but because the unit of counting could not represent them.

The first draft reached for the precedent that excluded `realestate` from the cohort. That
precedent excludes a candidate for OVERLAPPING a subject already counted; it presumes the business
is counted once somewhere. Applied where the collection itself was assessed nowhere, the same
words deleted the subject instead of deduplicating it. A rule borrowed across a change of unit
keeps its wording and loses its meaning.

What the measurement owed, and now does: state the unit before the number, publish both levels
when they differ, and probe the operator's declared endpoint rather than inferring from the rows.
Four probes cost four calls of 159 unspent.

Anchor: no code gate. A checker cannot know which unit a given question is about - that is the
judgement the measurement exists to make. Recorded as a habit in L-8's form rather than dressed as
an enforced rule, because a law with a fake anchor is worse than an honest note.

## L-25 Every gate read a file, and the one part of the site that is code was in none of them

*(Every reading in this lesson was taken on 2026-08-20 and is kept in the tense it was written in,
because the miss is what the lesson is for. The state it describes has since changed: read
2026-08-24 12:11:57 UTC, `GET https://provek.dev/api/apply` answered **405** and the Function was
published and executing — the dated table of readings is in `docs/INTAKE_OPERATIONS.md`, where as of
2026-08-24 the POST half was `not_measured`. What has NOT changed is the lesson: no gate in this
repository reads the origin, so the paragraph below would still be the last thing to notice if the
404 came back.)*

`GET https://provek.dev/api/apply` answers 404. `web/functions/api/apply.js` answers 405 and says
so in a string a reader can grep. The intake Pages Function has never been deployed: the same
request to `/api/nonexistent-xyz` returns the same static 404 page, `~/orchestra/deploy.sh`
publishes `web/dist` from the repository root, and the functions live at `web/functions`, which
that directory does not contain. The form's only action has been failing for every visitor who has
ever pressed the button, and four documents describe it as working.

Nothing was silent and nothing was skipped. `tests/test_intake_offers_no_active_mandate.py` was
armed, unskippable, mutation-tested, and it had a paragraph headed WHAT IS NOT ASSERTED naming this
exact gap in advance — *"That the DEPLOYED endpoint behaves this way… This test reads the
repository."* The gap was declared, dated, attributed and left. **A named blind spot is still a
blind spot**; writing it down converts an unknown into a known and measures nothing, and the
sentence reads afterwards as diligence performed rather than as work outstanding.

The instrument that would have seen it was missing for a reason with a shape. `push.sh` builds the
site precisely so the emitted-page sweep judges what a reader receives (L-3, D-22) — and it sweeps
`web/dist`, which is the one directory the functions are absent from. So the repair that closed
L-3 at the door defined "the shipped artefact" as the build output, and the part of the site that
is *code* fell outside the definition. That is L-12 one level out: there a ratchet scanned two
directories of three; here the very fix for "measure what ships" scanned the half of the site that
is static and could not have reported that the other half was never uploaded.

What found it was the first work here that does not read a file. Two `curl` GETs, one of them a
control (`/` → 200, so the 404 is a fact about that path and not about whether the origin talks to
us), took four seconds and cost nothing, after the claim had stood unchallenged through every green
build since the endpoint was written. Attribution matters and the first draft of this lesson got it
wrong: the reading was taken **by hand while choosing what the prober should probe**, not by the
prober, whose own run passes on a different claim. A lesson that credits a component with a finding
made beside it is the same species of overstatement it is about.

The general form: **for any claim about a system you operate, ask which gate would fail if it
stopped being true — and if the honest answer is a file, the claim is untested.** A test can only
be about what it can read, so the boundary of the suite is the boundary of the file tree, and
everything past it is prose no matter how carefully the prose admits it.

There is a tail, and it is the same lesson eating its own first draft. This paragraph originally
closed by explaining why the 404 was named and not fixed: publishing the function needs the
`INTAKE` KV binding and two Telegram secrets on the Pages project, so a deploy would turn a loud
404 into a 503 that looks like progress. Nothing had measured that. The production project already
carries all three, so nothing infrastructural is missing at all — the deploy command simply runs
`wrangler` in the repository root, where `web/functions` is not found. **A reason assembled from
what would plausibly be true is a claim like any other**, and this one was written into the lesson
about untested claims, four lines below the sentence naming a named blind spot as still a blind
spot. It remains deferred — `deploy.sh` is the operator's channel and switching on an endpoint that
writes durable records and messages a human exceeds this task — but the deferral is one line in one
file, not a blocked dependency, and saying so is the difference between deferring and excusing.

Anchor: no code gate for the general rule — a checker cannot know which of a project's claims are
about a running system. The INSTANCE is armed and is the model to copy: `LAW-PROBE-NEEDS-MANDATE`
and `LAW-PROBE-CONTROL-BEFORE-ABSENCE` (`src/prober/prober.py`, `tests/test_prober.py`,
`tests/test_probe_control.py`) hold the prober that can now take such readings under a mandate, and
every reading above is in `evidence/PROBE-001.txt`.

## L-26 The evidence was generated by a loop, and the loop transposed two runs

`evidence/RED-013` records four mutations, each with the failing suite that proves a gate is armed.
The block headed RED 4 carried RED 3's output: a different mutation's failures, under the sentence
*"Everything below this line is verbatim tool output"*, including a traceback for a state that
mutation cannot reach. The gates were genuinely armed - applying the recorded mutation does kill
tests, and the right ones. What was false was the artefact that exists to let a reader check that
without trusting it.

The mechanism is ordinary and that is the point. One shell block mutated, ran the suite, restored,
and repeated four times, with every command's output redirected into a single file. Nothing in it
compared what was captured against what had just been mutated, so a stale read of a restored module
landed under the next heading and looked exactly like the honest three above it. **Automation
produced a claim nobody made and nobody read.**

It is L-21 one turn further out. There, a repair was written and never called, and the fix was to
mutate and watch a test die. Here the mutation testing was performed, correctly, and the RECORD of
it was wrong - so the practice that catches decorative repairs had itself become a decorative
artefact. A red run is not evidence because it is red; it is evidence because it is the output of
the command printed above it, and only re-running that command establishes the connection.

Caught by Fable, by applying the recorded mutation and comparing failures - the one check that could
have found it, and the one nobody had done, because the file looked right.

The general form: **an artefact produced by a script inherits the script's bugs, and it is read as
though a person had written it.** Where output is captured in a loop, capture each iteration
separately and compare them; identical output from different mutations is the signal. In this
repository it is worse than elsewhere, because a fabricated line in `evidence/` is the founding
defect - a claim stronger than its artefact - committed inside the artefact kept to detect it.

**And the weaker form of it was sitting in the next file along.** `RED-014` recorded a genuine run,
of a narrower mutation than its own header described: the prose said "restores the exact pre-D-21
shape", the edit left the validation branch standing and replaced only the assignment, and two
tests died where the shape it named kills three. Nothing was transposed and nothing was invented -
the transcript was true output of a real command - and the sentence above it still overstated what
had been demonstrated. That is the harder half to catch, because there is no inconsistency inside
the file to find: the check is to perform the edit the header describes and count. Fable did, from
`git show`, which is where the shape it claimed to restore actually lives.

So the rule has two parts, and the second is the one this task needed twice: **re-run the command
to know the output is real, and perform the edit the prose names to know the output is the right
one.** A red run proves a gate is armed against the mutation that produced it, and against no other.

Anchor: no code gate. A checker cannot tell a true transcript from a plausible one; that is the
whole difficulty, and naming a `LAW-*` for it would be the fake anchor L-8 refuses. What is done
instead is structural: `RED-013` is now assembled from per-mutation files rather than one stream,
and it states in its own header that its four failure sets are distinct - a control a reader can
verify by looking, and one that would have caught this instance.

## L-27 The answer an instrument gives nearly every time is the answer it can give without looking

T-F7 put a watch on the ERC-8004 Validation Registry, whose job is to notice when it deploys. It
answers `no_target` today, and it will answer `no_target` on almost every run it ever makes. That
frequency is the whole vulnerability: **the reading an instrument returns nearly always is the
reading it will also return after it has stopped reading anything.** An empty document, an error
page, a moved file, a restructured table - every one of them produces the same confident absence as
a correct run, indistinguishable in the record, in the finding, and at the door.

The rule that falls out is asymmetric, and the asymmetry is the design rather than a compromise:

- **The common answer needs a positive control.** Here it is the Identity and Reputation registries,
  which ARE deployed and ARE in the same list: if either cannot be found beside an address, the
  parser reports `unreadable` instead of an absence. `RED-015` is that control removed, with an
  empty string reading as "there is no Validation Registry".
- **The rare answer needs a wider net - and a name for what the net catches that it cannot
  identify.** Matching the exact label only, a row renamed from `ValidationRegistry` to
  `Validation` reads as an absence with the control green. Matching `validation` alone, a
  `validationRequest(0x…, 42, …)` in a code sample reads as a deployment and the gate orders
  somebody to schedule work that does not exist. Both were drafted, and the answer is neither: the
  loose hit gets a THIRD state, quotes the line, and says a person settles it. **A red that
  instructs work nobody should do is not cheaper than a silence** - and "I cannot tell a deployment
  row from an example" is exactly the `not_measured` invariant 1 already asks for, rather than a
  compromise between two wrong answers.
- **A control may never override a positive reading.** If the anchors are gone AND an address is
  found, the address wins: it is a measurement the instrument is holding, and `unreadable` over it
  is the discard L-1 and the `PARTIALLY READ` branch of `commitments.py` already cost this project
  twice.

Two further shapes came out of the same task, both found by Fable and both mirrors of fixes that
had just been made:

**A finding that reports one axis must not suppress the other.** `checked_at` and `state` fail
independently; the first draft returned after naming the record problem, so `TARGET APPEARED` - the
one finding the component exists to raise - was silenced by an unparseable timestamp, beneath a
sentence asserting nothing had been established about a state the dataclass was holding. On Python
3.10, where `fromisoformat` rejects a trailing `Z`, that was one ordinary spelling away.

**A remedy must not destroy the evidence it was invoked to refresh - and the obvious fix for that
is worse than the defect.** The watch first wrote its result unconditionally, which reads as honest
until you trace the operator following the printed remedy on a day the source is 5xx: the good
reading is replaced by a non-measurement, two assertions about the real tree go red, and step three
of that same remedy - `./scripts/push.sh` - refuses the dirty file it just created.

So the next draft refused to overwrite a measurement. **That draft turned every instrument failure
into a GREEN GATE.** The record went on saying `no_target` inside its interval while the last run
had reported the deployment list unrecognisable, and the sweep returned nothing at all - for up to
twenty-three days, in the layer whose entire subject is that silence must become a finding. The
only witness was the stdout of a script nothing runs on a clock. It was strictly worse than the
false red it replaced, and it was introduced by the fix for it.

Both drafts were **choosing which of two facts to keep**, and that was the error under both. There
are two facts, so the record has two blocks: `measurement` is the last run that established
something and is the only thing the interval rides; `last_attempt` is what the last run did,
whatever that was, and the gate reports it the same minute. Neither is derivable from the other.
The general form is worth more than the instance: **when a fix makes you pick which of two true
things to record, the answer is usually that you have found a second field, not a tie to break.**

**And splitting a record into two fields creates a second source of truth, which needs reconciling
like any other.** The two blocks fixed the green gate and immediately grew their own: the finding
loop reported only NON-measurements, and `TARGET APPEARED` was keyed on the measurement block
alone, so a record whose most recent line said `target_present` swept clean. The attempt axis
carried bad news and not good news - and good news is the entire reason the component exists. No
run can write that state; a partial `git checkout <older> -- public/`, a merge taking one block
from each side, or a hand edit can. The cohort obligation already carries `SHIPPED AHEAD OF THE
RUN` for exactly this class, and the new pair had no equivalent until Fable walked all 112
combinations and found the one that was green.

Worse, it was **asserted as intended**: a test said "an attempt that DID measure is not news",
exercised on `no_target` alone, directly beneath one that said "every non-measurement is walked,
because the draft was green for all of them". The discipline that caught the first hole was not
applied to its mirror, in the file where it had just been written down.

**A third time, in the same shape: never overwrite an unreadable record with a claim about it.**
The carry-forward dropped any measurement block it could not parse and wrote `measurement: null`,
whose meaning is "none has ever been taken" - so one failed run over a merely corrupt record turned
`NOT ASSESSED: could not be read` into `has never presented evidence of participation ... a
FINDING, not missing data`. Invariant 1 with the sign flipped, and the input was not hypothetical:
it was the record shape this repository had carried an hour earlier.

The general form, beyond this instrument: **ask what your check returns when it is broken, and if
that is also what it returns when it is fine, you do not have a check.** Where the two coincide,
find something that must be visible whenever the instrument is working, and make its absence the
finding. And when the answer to a defect is a second field, write the comparison between the two
in the same commit - a pair of facts nobody reconciles is one of them being believed by accident.

Anchor: `LAW-BLOCKED-STEP-HAS-A-SENTINEL`, gate `src/transport/erc8004_deployment.py`, test
`tests/test_validation_target_obligation.py`.

## L-28 Catching a failure creates a state of the world, and the first draft merged it into another

The intake's write-back sat outside any `try`, so a refused second write became a 500 and the form
told the applicant *nothing was saved* about a record that was already durable. Catching it is the
whole of T-A2-2 and it is correct. What it also did, invisibly, was give `delivered: null` a second
meaning. That value had meant one thing - the invocation died between the two writes, and its
submitter was told the submission was lost - and it now also meant the opposite, that the submitter
was answered honestly and needs nothing at all. Two states of the world in one value, in the exact
field the operator's sweep keys on, and the two demand opposite actions from the person reading it.
Invariant 1, this project's most-counted defect, introduced by the fix for a different instance of
it and in the same field.

The comment defending the silence is the part worth keeping. It said there was nowhere durable left
to write, because the store had just refused a write - and that is false in a way that reads as
careful: the limit producing the failure is one write per second **to the same key**, so the store
was fine and one key was not. **A constraint remembered without its qualifier becomes a general
impossibility**, and a general impossibility is what excuses a silence. The repair is a dozen lines: a
sentinel under a different key, written when the refusal is caught and absent when it is not, so
`null` beside a mark and `null` alone are two readings instead of one - and it is a dozen because
the sentinel's own write is caught too, which is the case where the silence really is forced.

Found by Fable, refuting the change that closed the original defect. The lesson generalises past
this endpoint: **when a fix turns a crash into a handled path, ask what the handled path now looks
like in the record - a caught failure that leaves the store exactly as an uncaught one did has been
hidden rather than handled.** It is L-27's family seen from the other end. There the question was
which of two true things to record and the answer was a second field; here the second state was
manufactured by the repair itself, so nothing in the diff looked like a choice being made.

**And the same task produced the mirror of it in the evidence.** RED-017's third mutation - "the
sentinel is never written" - was an `if (false) {` left facing a `catch`. The module stopped
parsing, every scenario died, and eight tests went red under a heading claiming a property had been
removed. The transcript was real output of the edit the prose named, which is what L-26 asks for,
and it established nothing: a file that does not parse fails every test whatever the gate asserts.
**A red run is evidence only if the subject was still running when it went red.** The generator now
requires the suite's instrument control - a rejected submission, refusable only by the endpoint's
own validation - to survive each mutation, and refuses to write the file otherwise. That control
existed already and was not being read; the check was to ask, of each red, *which tests should NOT
have died*.

Anchor: `LAW-INTAKE-SAVED-MEANS-SAVED` covers the instance (`web/functions/api/apply.js`,
`tests/test_intake_survives_a_failed_writeback.py`), and the sentinel's presence and absence are
both asserted, with nine red runs in
`evidence/RED-017-nothing-was-saved-about-a-saved-record.txt` - five of which were GREEN when Fable
first applied them, over three rounds of refutation, which is the more useful thing that file
records. No code gate for either general
rule - a checker cannot know which values in a store carry more than one world, nor which of a
mutation's failures are the point - so they are recorded in L-8's form rather than dressed as
enforced rules.

## L-29 The store learned to tell two states apart and the instrument printed one word

T-A2-2 made `delivered: null` mean two things and repaired it in the STORE - a sentinel under a
different key, so "the applicant was told the truth" and "the invocation died" stopped sharing a
value. The same commit widened the operator's sweep to match `null` as well as `false`, so it found
the records. It printed all of them as `UNSEEN`.

The distinction existed and was destroyed on the way out. **A state is only as distinguishable as
the instrument that reports it**, and the last stage - the label, the column heading, the exit
status - is where a repair is least likely to be looked for, because the field it was made in
demonstrably carries the difference. `false` is answered by reading the record now; `null` is
answered by reading the sentinel beside it; the operator holding one list cannot derive either
instruction. Invariant 1, one level up from the field it is usually about, arriving in the commit
that closed it one level down.

**And the same sweep could not report its own refusal.** `v=$(npx wrangler kv key get ...)` was read
whatever the exit status, so a key the store declined to hand over printed nothing - which is what a
healthy record prints. One level up, a failed `list` yielded no keys, and no keys is what an empty
namespace yields, in a document that reads an empty namespace as the finding that no submission has
ever been made. A reading that never happened would have published as a measurement. The sweep now
answers in three exit statuses rather than two - nothing qualified, act on these, did not run - and
prints its count on every run that ran, because **a zero has to say which zero it is even when the
zero is the whole output**.

**Why it survived two edits: nothing could go red over a fenced block in a document.** Both previous
corrections were made by editing Markdown, believed, and shipped. The gate now EXTRACTS the block
and RUNS it against a stubbed namespace, and a grep-based gate would have passed every defect above
- each of them contains the strings a grep would look for. **The question to ask of any instrument
described in prose is which command turns it red.**

**And the repair's own new sentence was false before anybody read it back.** The count added here
ends, on an empty namespace, with *no submission has ever been made* - a claim about the endpoint's
whole history, guarded on the number of READABLE records. A namespace holding one submission the
store refused to hand over printed it directly underneath the `UNREADABLE` line naming that key, and
so did a namespace holding a refusal mark, which exists only because a submission was stored. The
new gate was green over all of it, on a fixture it already had. Fable found it, with four more of
the same family: two counters that could be silenced into reporting zero, a namespace control that
covered the `list` and not the `get`, and an unparseable sentinel printed as one that had been read.
**A change that adds an OUTPUT adds a claim, and that claim is unmeasured until something can go red
over its wording** - not over the code path that produces it, which in all five of these was
exercised and green. They are mutations 9 to 13 of RED-018.

**The second round then refuted the repairs, and six more were green.** Two counters transposed in
the summary line survived because the fixture written to catch a DROPPED counter gave every bucket
the count 1, and four numbers holding the same value print the same line under every permutation of
themselves - RED-013's transposition, reintroduced by the test that closed a neighbouring defect in
the same line. Two branches printed a finding and then reported it in a clean exit status, because
`rc` is one variable set in four places and the status test had only ever reached it through one.
And the repair for the unparseable sentinel checked that `jq` had not FAILED, which `null`, `{}` and
an empty value all pass - **a fix narrowed to the inputs its own new test used**, which is the same
error as a gate about the shapes it runs, committed while fixing one.

**The third round found the same shape inside the second round's fixes**, twice: a finding filed
under the exit status reserved for a sweep that did NOT run - a misfiled `rc` where the round before
had only armed dropped ones - and two of the sentinel's three required fields left unchecked,
because the missing-field fixture written in round two omitted the third alone. **A test built from
one example of a defect arms the gate against that example.**

The honest summary of this task: the gate written to end one class of false green shipped fourteen
of them across three drafts, and every one was found by applying an edit and watching the suite stay
green rather than by reading the code. **The question is never whether a gate asserts the property;
it is which edit it has been watched to survive.**

Anchor: `LAW-INTAKE-SWEEP-NAMES-ITS-STATES` covers the instance (`docs/INTAKE_OPERATIONS.md`,
`tests/test_intake_sweep_distinguishes_its_states.py`), with twenty-two red runs in
`evidence/RED-018-a-sweep-that-cannot-name-what-it-found.txt`. The general rule - a repair is not
finished until the tool that READS the repaired state can name it - has no code gate, for L-8's
reason: no checker knows which of a program's outputs is the one a human acts on.

## L-30 The artefacts were honest and the report about them was not

T-C4 shipped the first method note and closed with a story: the generator had not really been red,
its `repair()` had already been written, and the fix had simply never been *seen* to work because
the two runs after it were killed mid-prose. That reads like a careful correction of a stale task
description. Every load-bearing part of it is false, and the files that refute it are the same
files it cites.

`repair()`'s own docstring says the run of 2026-08-20 14:21 "was refused on one repeated paragraph
opener **with no path back**" - which is the sentence a function writes about the defect it was
created to fix, not one it writes about a defect it was already there for. `notes_gen.py` has an
mtime of 2026-08-21 05:04:05. The journal is plainer still: at 14:21 the capture logged a bare
`measure RED`, where a run with `repair()` present logs `measure red-before-repair` and then
`repair` - which is exactly what 2026-08-24 logged. And "the two runs after the repair were killed"
miscounts in the direction that flatters: L-15's two killed runs are 13:29 and 13:43 on the 20th,
BOTH BEFORE the refusal, neither reaching `measure()` at all. After `repair()` was written exactly
one run followed, and it was stopped by an operator pause.

The true history is duller and shorter. `measure()` refused a capture correctly. A previous attempt
at this same task wrote `repair()` the following morning, in response. It first executed on
2026-08-24 and cleared the identical miss on the first attempt. Nothing needed inventing to make
that a good outcome, which is what makes the invention interesting.

**No artefact was falsified and none had to be.** The docstring, the mtime and the journal were all
correct and all available; the false claims were assembled *on top of* them by a reading that
stopped at the first fact confirming the shape it wanted - L-14, moved from a measurement into a
narrative. The gates could not have caught it either, and not by oversight: every gate here judges
the tree, and a commit message is the one artefact in a push that nothing reads. **The closing
report is the least-checked thing this project produces and the only thing a human is guaranteed to
read**, which is the worst possible combination and the reason this lesson exists rather than a
patch.

There is a sharper edge on it. The false version was not a lie about the WORK - the work was fine -
it was a lie about the DIFFICULTY, and it ran in the flattering direction twice: the task's
"generator is red" became "the generator was not red", and one killed run became two. A report that
inflates what was overcome is this project's founding defect pointed at its own author, committed
in the same push as an evidence file built to catch claims stronger than their artefacts.

The general form: **before writing that a thing had already been fixed, find the commit that fixed
it.** A repair whose author you cannot name is a repair you are guessing at, and "it was already
there" is the most comfortable guess available to whoever benefits from it.

Found by Fable, refuting the closing report rather than the change - the change survived. The
correction cannot go into the commit it belongs to, because history is not rewritten here (passports
pin `head_sha`), so it lives here and the commit stands wrong on the record with this beside it.

Anchor: no code gate, and this is the honest kind of gateless rather than the resigned kind. A
checker cannot read a paragraph of prose about a repair and know who wrote the repair. Recorded in
L-8's form; naming a `LAW-*` for it would be the fake anchor L-8 refuses, in a lesson about claims
made without checking.

## L-31 A checker more permissive than the machine it stands in for certifies files that machine cannot run

`66f61ea` left this host with seven green gates - 642 passed, coverage 92.87% - and turned `main`
RED in the same second it landed. Three `run:` lines carried `--only-binary=:all: ` in a plain
scalar; `: ` is how YAML spells "the key ended here", so GitHub read a mapping inside a mapping and
refused the document. The run was created and concluded in the same second with ZERO jobs: nothing
in the workflow failed, because nothing in it ever started.

**Every gate that vouched for that commit was correct about what it measures.**
`scripts/verify_pip_pins.py` read all three lines and reported them hash-pinned - it still does
after the repair, byte for byte the same text. It reads the file with what D-30 calls, in its own
words, "a hand-written approximation of a shell lexer inside a hand-written approximation of a YAML
reader", and the two readers disagreed in the one direction that cannot be seen from inside: the
approximation was WIDER than the real thing. A stricter approximation announces itself immediately,
as a false red on a file that works. A looser one is silent until the machine it stands in for
refuses a document the checker has already blessed.

The general form is not about YAML. Wherever a gate re-implements somebody else's reader - a shell
lexer, a URL parser, a glob, a version comparison - the two can disagree, and only one of the two
directions is self-reporting. **Ask the real parser when the real parser is available**, and where
it is not, say which of the two directions the approximation errs in.

The instance is closed and the class is not: PyYAML implements YAML 1.1, GitHub's parser is neither
PyYAML nor on this host, and no schema is checked by either. What `LAW-WORKFLOWS-PARSE` buys is the
defect that was actually paid for, refused at the door instead of on `main` - and the residue is
written down in D-32 rather than covered by the word "parses".

Anchor: LAW-WORKFLOWS-PARSE.

## L-32 The control was run, and its silence was read as an answer

`bing_probe.py` was written to honour L-10 and its docstring says so: every zero-capable call is run
a SECOND time against an old verified control site, because a `200` with an empty body is what a
true zero and a broken call both look like. The discipline was real, the code was there from the
first hour, and on 2026-08-21 it produced `query_stats: {"count": 0, "state": "instrument_blind"}`
for `provek.dev` — on which a ruling was built that called a release condition unreachable.

The instrument was fine. Measured 2026-08-24, one key, one code path, the two sites side by side:
`GetQueryStats` reads 64 rows and 402 impressions at the control, `GetRankAndTrafficStats` reads 985
impressions and 29 clicks. `provek.dev`'s zero is a real zero — no row qualified for those reports
— though not the story the first draft of this lesson told six times over, that "Bing has not
crawled it": the same snapshot carries `sitemap_accepted.url_count: 13`, a number Bing could not
hold without having fetched the file. A mechanism fitted on top of a zero is L-30, and writing it
into the lesson about instruments overstating what they measured is where it is least visible.
(The task brief
reports that the second pair also matches the operator's snapshot of the Bing web cabinet. That
snapshot is not on this host and the agreement is the brief's, not a reading taken here — a
distinction the first draft of this lesson lost in five places at once, which is the lesson's own
subject arriving from behind.)

**The control had returned zero, and a control that returns zero has established nothing.** It is
equally what a blind call and an empty control site produce. `instrument_blind` is a positive claim
— this call cannot see this quantity — and it was reached along the one path where no evidence for
it exists. Everything the design got right made the failure less visible, not more: the control was
run, its result was recorded, the shapes were counted correctly, and the state was named with
confidence for the one case that had earned none.

**And the refutation was already in the output, one line down.** `counted()` computed
`control_proven_capable: false` and serialised it directly beneath the word `blind`. The distinction
existed, was measured, was written to disk, and was destroyed by the name chosen for the state. That
is L-29 arriving from the other side: there a repaired store was flattened by the tool that read it,
here a correct field was flattened by the label printed beside it. **A record that carries its own
refutation is not self-correcting; the field a human acts on is the one that has to be right.**

The general form, and it is not about controls: **a control answers in two directions and only one
of them is an answer.** A positive control that fires proves the instrument can see. The same
control silent proves nothing whatever — not that the instrument is broken, not that the world is
empty — and the temptation is to spend that silence, because a run that ends in "we still do not
know" feels like the instrument failing rather than working. So: before a control's result is
allowed to decide anything, ask which of its two outcomes you are holding, and if it is the silent
one, the state you may publish is a not-measured state and nothing stronger. Blindness, like any
other claim, needs evidence FOR it — here, a second call reading the same quantity at a coarser
grain, which would have settled it on the day and cost one request.

There is a tail worth more than the fix. The task that found this arrived saying the probe had
declared blindness about a working instrument, which was true of the OUTPUT and false of the
mechanism — the obvious story is a wrong API call, and reproducing it first is what refused that
story. **Before repairing the defect a task describes, run the thing and watch it produce the
symptom**; here it produced the opposite, and the real defect was one branch away from the one that
would have been "fixed". Why the control was empty on 2026-08-21 remains `not_measured`, and it is
left that way rather than filled in with the likeliest mechanism (L-30).

**The same step was already published on our own site, and the count of copies was wrong three
times.** Four documents in this repository stated the blindness itself, and all four were corrected
here. Then `seo/KEYWORD_BASE.md` turned out to carry the same STEP in different words — an empty
result from the `bing_serp_related` capture called "a statement about the client, not about Bing",
from three control queries that all returned zero and whose capability was argued from plausibility.
Then the live note whose subject is absence turned out to carry that sentence verbatim, because
`notes_topics.json` pins those very lines as the note's source material. Zero controls, an asserted
capability, a conclusion about the instrument: this lesson's own defect, in prose, on the page a
reader is most likely to cite it from.

The searches that missed them were not careless in the ordinary way. The note WAS opened, and the
two sections checked were the two that had been named in advance; the second search then found the
note and stopped at it, without asking where the note's words had come from. **A search for copies
that only visits the places you already suspect is a search for confirmation** — and the one that
found these looked for the STEP, a zero control promoted into a verdict, rather than for the words.
The last turn is the useful one: two of the six copies were parent and child, so correcting the
child alone would have been undone by the next re-capture, and the question "where did this sentence
come from?" is what separated a list of instances from a mechanism. The live one is not repaired
here, for reasons named in D-34 and `~/orchestra/FINDINGS.md`, which means this lesson ships with its
own instance live on the site it is about. All found by Fable.

Anchor: no code gate in this repository, and this is the honest kind of gateless. The probe answers
to no `ABI-*` requirement and lives outside the tree (D-17, L-11, L-12), so nothing in a clone can
read it and naming a `LAW-*` here would be the fake anchor L-8 refuses. The INSTANCE is armed where
the subject is: `~/orchestra/bing_counted_check.py` holds eleven worlds in seven distinct states and
asserts over all of them that no reading whose control returned data may be published as
`instrument_blind`. The red runs are `~/orchestra/evidence/RED-B10-*` — four mutations, each a
textual edit to a copy of the real artefact, each shown to leave the instrument control green and to
kill a set of checks no other mutation killed — beside `RED-B10-meta-*`, which breaks each of the
generator's own four preconditions in turn. D-34 carries the decision.
