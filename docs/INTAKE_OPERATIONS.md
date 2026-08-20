# Intake: what the operator has to do, and how often

Intake is machinery plus one human habit. The machinery is described so the habit has something to
key on; the habit is written down because Fable made the human reply leg conditional on it actually
being performed rather than intended.

## What happens without anyone

1. A submission is validated at `/api/apply` — repository URL shape, address shape, honeypot.
2. It is written to the `provek-intake` KV namespace **before** anything else, with
   `delivered: null`. A submission survives a failed announcement.
3. A notice goes to the operator's ops channel.
4. The record is written again with `delivered: true` or `false`.
5. The applicant is told which of the two happened, in different words. *"The notification to the
   operator went out"* is only said when it did — the page used to claim the notice had *reached*
   the operator, which is a stronger fact than `r.ok` from Telegram measures, and it was corrected
   on the page before it was corrected here.
6. **And there is a third outcome, which steps 1-5 read as impossible.** If step 4 throws, the
   record stays at `delivered: null` and the applicant is told nothing was saved — while it was.
   How often that happens is argued once, under "What one submission costs" below, and deliberately
   not repeated here: it is the claim most likely to be corrected by the next reading of the
   namespace, and a frequency stated in two places is a frequency that will be updated in one.
   Written into this list because a five-step description that admits two endings is how the third
   one stays invisible.

## The habit — daily for the week the link goes out, weekly after it

**Sweep KV for `delivered: false` — and for `delivered: null`, which is the worse case.**

```bash
npx wrangler kv key list --namespace-id 5d93877f53d94f3fbc4863a0195fc9a4 \
  | jq -r '.[].name' \
  | while read -r k; do
      npx wrangler kv key get "$k" --namespace-id 5d93877f53d94f3fbc4863a0195fc9a4 \
        | jq -e 'select(.delivered == false or .delivered == null)' >/dev/null \
        && echo "UNSEEN: $k"
    done
```

`null` is the value the record carries between the durable write and the write-back, so a record
still holding it is one whose request died in between — and its submitter was told *nothing was
saved* while this record existed. `false` means the operator was not told; `null` means the
applicant was told something untrue as well. The reasoning is under "What one submission costs"
below; the filter is here because the sweep is where it has to be acted on.

Anything it prints is a person whose request nobody saw. On a `false` they were told their request
was recorded, and the confirmation page promises them that the record is safe and may be read later
than usual; this sweep is what makes that sentence true rather than consoling. On a `null` they
were told the opposite — that nothing was saved — so that person needs the record acted on AND a
correction, and they are the reason to open the printed key rather than only count it.

**Cadence.** Weekly was proportionate at the volume this form has had, and that volume is the
volume of a page nobody has been pointed at. The day a link is published that sentence stops being
true, and it would go on reading as though it were, because it is written in the present tense
about a past measurement. So: **for the seven days that follow publication of the link the sweep is
daily**, and after that it returns to weekly unless one of the thresholds below has fired.

    Link published on: NOT YET PUBLISHED as of 2026-08-20.

That line is filled in on the day it happens, and the seven days are counted from it. An unfilled
date means the window has not started, not that it has quietly closed.

The sweep runs on the operator's laptop: `wrangler` is not installed on the audit host and the
account is not reachable from it, so "daily" is a habit of a person, not a job on a machine. If a
record is ever found this way, or if volume rises enough that a day is too long, the sweep becomes
a scheduled job — not before, because machinery built against a risk that has not appeared is
machinery nobody maintains.

## What one submission costs, and where the plan's ceiling is

One accepted submission is **two KV writes to the same key**: `delivered: null` before the notice,
then `delivered: true|false` after it (`web/functions/api/apply.js`). The second write is what the
sweep reads for its `delivered` value — when it lands; the third bullet below is about the case
where it does not, and in that case the sweep is reading the first write. Neither write can simply
be dropped without giving up survival-of-a-failed-notice or the sweep's evidence, which is not the
same as saying nothing can be done: writing one record under two distinct keys keeps both
properties and has no same-key problem at all.

Workers KV, free plan, from the Cloudflare limits page read on 2026-08-20 — *1,000 writes to
different keys per day*, *1 per second to the same key*, *100,000 reads per day*, *1 GB stored*,
*512 byte keys*, *25 MiB values*.

The same page calls the paid plan *unlimited*, and this section's first draft repeated the word.
The pricing page prices it: *reads 10 million/month, + $0.50/million*; *writes 1 million/month, +
$5.00/million*; *deletes and list requests the same*; *stored data 1 GB, + $0.50/GB-month*.
"Unlimited" means no hard ceiling — it does not mean no meter, and upgrading converts a wall into a
bill. Worth stating precisely because the plan is unknown (next bullets), and "we are probably on
paid, so this is all moot" is the comfortable direction of error.

Four things follow, and the last two are the ones to hold on to:

* **The daily ceiling is between 500 and 1,000 accepted submissions, and the page does not say
  which.** The limited row is *writes to different keys*; a submission touches exactly one key, and
  the second write to it falls under the separate *writes to same key* row. Whether that second
  write also spends daily budget is not stated. So one submission costs either one unit or two, the
  ceiling is 1,000/day or 500/day, and the smaller number is the one to plan against — the point of
  writing both down is that a later reader can see the assumption instead of inheriting it. The
  budget belongs to the ACCOUNT, not to this namespace: anything else on the same account spends
  from the same 1,000. (The third bullet cuts across this one: a second write rejected at the
  same-key rate limit stores nothing and probably costs nothing, which pushes the true ceiling
  toward 1,000 and makes the pessimistic 500 — the reading S-4 is calibrated against — the less
  likely of the two. S-4 is left where it is; a threshold that fires early is the safe error here,
  and the calibration is revisited once the ceiling is known rather than guessed.)
* **Which plan this account is on is `not_measured` here.** It cannot be read from this host, and
  free is therefore the binding assumption until the operator reads the dashboard. Assuming paid
  because the numbers would then be comfortable is precisely the direction of error this project
  exists to detect.
* **⚠️ The two writes go to the same key inside one invocation, and Cloudflare documents that as an
  error rather than as a limit to stay under.** The limits page has only the bare row *writes to
  same key: 1 per second*, and this section's first draft stopped there and recorded the
  consequence as `not_measured` — which was L-14 committed one page away from the answer. The write
  API page states it: *"Workers KV has a maximum of 1 write to the same key per second. Writes made
  to the same key within 1 second will cause rate limiting (`429`) errors to be thrown."* It also
  gives the instruction this endpoint does the opposite of: *"Consider consolidating your writes to
  a key within a Worker invocation to a single write, or wait at least 1 second between writes."*
  `apply.js:82` and `apply.js:103` are two writes to one key in one invocation, with at most a
  Telegram round trip between them and, when no Telegram credentials are configured, nothing at all.
  So the documented behaviour puts the next bullet on the MAIN PATH rather than on a rare failure:
  it predicts that every submission whose two writes fall inside one second is stored and then
  reported to its applicant as lost. Not every submission unconditionally — a Telegram round trip
  longer than a second would separate the writes legitimately — and not "intake is broken", because
  the record survives; what breaks is the applicant's confirmation and the `delivered` signal the
  whole habit above keys on.

  **Enforcement has not been observed, and the first draft of this paragraph said the only way to
  observe it would be to POST a fabricated submission into the operator's live intake. That was
  false, and the instrument sits eighty lines above.** The sweep IS the measurement, retrospectively
  and for free: if the second write always fails, every record in the namespace is stuck at
  `delivered: null`; if it lands, records carry `true` or `false`. One `list`, no notice, nothing
  fabricated, and the operator runs it anyway. **Do that before publishing the link, and read the
  `delivered` values rather than only the count.** Two more paths exist if it is inconclusive: a
  preview deployment exercises the real binding with no Telegram credentials configured, and two
  `wrangler kv key put` calls inside one second on a scratch key test the limit directly — the
  latter over the REST path rather than the Worker binding, which is an L-10 caveat on the reading
  and not a reason to skip it. And the empty case is a case: **zero records means no submission has
  ever been made**, which is itself the reading — the state in which the endpoint has never once
  been exercised end to end, and the one the launch is about to leave.

  Only after that reading is the fix a code change with its own red run — one write instead of two,
  or two distinct keys. It is not taken here.
* **A failed second write strands a record the sweep was blind to until today, and tells the
  applicant the opposite of the truth.** The first `put` stores `delivered: null`; if the second
  `put` throws,
  nothing catches it — the notice block has its own `try/catch` (`apply.js:88-100`) and a failed
  notice merely sets `delivered = false`, so the second `put` is the only uncaught step — the
  Function answers 500, the client renders `HTTP 500` as its reason, and the form says *"Not
  recorded. … Nothing was saved"* (`web/src/pages/Apply.tsx`, where it is an honest sentence in
  every other failure). Here the record WAS saved. It sits at `delivered: null`, which the sweep's
  original filter — `select(.delivered == false)` — does not match, so the one record in the
  namespace that nobody has seen and nobody will follow up was the one record the habit above
  skipped. That is exactly the case the sweep exists for, and it is why the filter now matches
  `null` as well as `false`. The endpoint is still not changed here: a stranded `null` also wants
  the applicant told something truer than "nothing was saved", and that is a code change with its
  own red run, not a line in an operations note. Named, dated 2026-08-20, not left as a silence.

The limits page says nothing about `list` and delete ceilings; the **pricing** page does, and the
first draft of this paragraph called them unknown without opening it. Free plan, read 2026-08-20:
*Keys read 100,000/day*, *Keys written 1,000/day*, *Keys deleted 1,000/day*, *List requests
1,000/day*, *Stored data 1 GB*. The sweep costs one `list` request per run (more only if the
namespace outgrows a single page) plus one read per stored key, so a daily sweep over K records
spends 1 of 1,000 list requests and K of 100,000 reads. The sweep is not what will run out.

## Thresholds for turning defence on, written before the spam rather than during it

Nothing is built today. The philosophy holds: defence is built when spam arrives, not in
anticipation of it. What is written now is the number at which it gets built, because a threshold
chosen while the inbox is filling is chosen by whoever is filling it.

**Junk** has to be countable or the thresholds are a mood. A junk record is one the operator,
performing the sweep, would not answer: a repository URL that resolves to nothing, a contact no
reply could go to, or a duplicate of a record already stored. Counted per calendar day by
`received_at` (UTC), from the records in KV — junk needs the repo and contact, so it needs the
record. S-3 and S-4 do not: keys are `request:${received_at}:${id}` (`apply.js:77`), so counting
accepted submissions per hour or per day is one `list` request and no reads at all.

* **S-1 — 3 junk records in a day, or 5 across seven days.** Nothing is built. The sweep stays
  daily until two consecutive days read zero, and the daily counts go into the operations log. This
  step exists so that S-2 fires on a record rather than on an impression.
* **S-2 — 10 junk records in one calendar day, or 25 across seven days.** Turnstile goes on the
  form and is verified server-side in `apply.js` — cookieless, as that file's comment has promised
  since 2026-08-20. If cookieless cannot be made to work, the fallback is S-3, not a cookie.
* **S-3 — 20 accepted submissions inside one hour, by `received_at`. This one opens an
  investigation; it does not by itself switch anything on.** The operator reads the Cloudflare
  dashboard for concentration, and the per-IP rate limit goes on only if the traffic is in fact
  concentrated — that rule is a Cloudflare setting and needs nothing stored on our side. A per-IP
  limit is the answer to a concentrated burst and is blind to volume spread thinly across
  addresses, which is S-2's shape; both may end up on, for different reasons.

  **Two rewrites, and the second is the instructive one.** The trigger first read *"5 submissions
  from one IP within an hour, or one IP responsible for more than half of a day's junk"* — and no
  record in KV carries an IP. `apply.js:69-74` stores id, `received_at`, repo, contact, mandate and
  `source_country` (`cf-ipcountry`), and the counting method three paragraphs up is "from the
  records in KV". So the rule could never have fired, in the section whose own
  first sentence is that a threshold on an uncountable quantity is a mood. Nor is storing the IP an
  available fix: the shipped form enumerates every stored field and says *"Nothing further"*
  (`web/src/pages/Apply.tsx`), and that list has already been corrected once for being short of
  what the endpoint writes — quietly adding an IP would make a live page lie to close a gap in an
  internal note.

  The second draft replaced it with *5 accepted submissions inside one hour*, which is countable
  but fires on the wrong event: five submissions in an hour from a link that has just been
  published is a good launch hour, not an attack. It was also arithmetically fused to S-4 — at most
  4/hour × 24 = 96 accepted in a day, under S-4's 125, so S-4 could never have been reached without
  S-3 firing first, and S-4's instruction to enable "whichever is not yet on" quietly collapsed to
  "enable S-2". Curing *the rule cannot fire* by substituting a quantity that fires on success is
  the same defect facing the other way. Hence 20/hour, which leaves 19 × 24 = 456 — S-4 reachable
  on its own — and hence the demotion from a switch to an investigation, because the concentration
  question that actually decides the response is not answerable from KV at all. The dashboard is
  the instrument for it, it is sampled, and it is named rather than assumed.
* **S-4 — 125 accepted submissions in one calendar day**, junk or not. That is a quarter of the
  free-tier daily write budget under the pessimistic reading of the previous section and an eighth
  under the optimistic one; it is stated in submissions rather than in writes so that it stays
  measurable while the reading is unresolved. On that day Turnstile goes on if it is not already,
  and S-3's investigation is performed immediately rather than waited for — S-3 is a look at the
  dashboard, not a switch, so "enable whichever is not on" would have been an instruction with only
  one half that means anything. This fires regardless of how legitimate the traffic looked, because
  the budget does not care. Past this line the next thing to fail is the durable write itself, and
  a failure the applicant is told about honestly is still a submission nobody received.

**Two classes of traffic these counts cannot see, and neither may be read as a zero.** A honeypot
hit is answered `{ ok: true, id: "ignored" }` before any write (`apply.js:43`), and a submission
that fails URL or address validation is answered 400 (`apply.js:62-65`); neither reaches KV. So
every number above counts only what got PAST both — which is the traffic Turnstile and a per-IP
limit exist to stop, so the thresholds still fire on the right quantity, but the quiet they are
measured against is not evidence of quiet. *No bots came* and *bots came and were absorbed* read
identically in KV: invariant 1, inside the intake's own instrument.

They are not invisible everywhere, and the first draft of this paragraph said "leaves no trace
anywhere", which was a stronger claim than the artefact and the wrong lesson. Every one of those
requests is a Function invocation and appears in Cloudflare's request metrics; requests to
`/api/apply` minus records in KV is the count, readable by the operator from the dashboard and by
nobody from this host. **Read it on each day of the launch week** — it is the only reading that
distinguishes a quiet form from a form under a flood the honeypot happens to be catching, and it
costs one dashboard page.

That budget is also the one nothing above guards. The Workers free plan states *Requests:
100,000/day*, and the draft before this one recorded as `not_measured` whether Pages Functions draw
on it — the third time in this document that a hedge survived only by not opening the neighbouring
page, which is why the pattern is confessed each time rather than tidied away. The Pages limits
page states it: *"Requests to Pages functions count towards your quota for Workers plans, including
requests from your Function to KV or Durable Object bindings."* So an accepted submission spends
more than one unit — the invocation plus its KV calls — and a honeypot hit still spends one.

A pure honeypot flood therefore trips no S-threshold, because it writes nothing and spends no KV
budget, while draining the request budget; the form's failure mode when that runs out is refusing
humans. Turnstile and a per-IP limit would both stop that traffic too, which is the reason its
invisibility bears on whether to enable them, rather than a footnote to thresholds aimed elsewhere.
If the dashboard count is ever wanted historically it has to be read as it happens; nothing
recovers it afterwards.

## Answering a request

Verification is by hand at this stage, and the site says so: no queue position, no promised date.
What the applicant was promised is that **if** their verification runs, the passport appears in the
registry and they are contacted at the address they gave. Both halves are the operator's to perform.

Declining is a legitimate outcome and should be said plainly rather than left as silence. A
verifier that ignores an application it does not intend to run has made the same mistake the intake
form itself made for a day and a half.

## What is deliberately not built

**No automatic verification on submission.** A stranger's repository is not measured because a form
was filled in; the operator decides. That is §4.6 and A-9: nobody is assessed without their request,
and the request being made does not oblige us to act on it.

**No probing.** The probing mandate was removed from the form on 2026-08-20 because no prober
exists to honour it, and offering it would have promised a document nobody would send. It returns
with T-2.12.

Removed from the ENDPOINT the same day, and only after that was it actually gone: `apply.js` had
kept `body.mandate === "active" ? "active" : "passive"`, which honours `active` for any client that
is not the form, so a `curl` POST could still have recorded a probing mandate over production. It
now assigns `passive` unconditionally, and `tests/test_intake_offers_no_active_mandate.py` fails
the build if that changes. The stored `mandate` field therefore records the policy applied rather
than what the request asked for — see D-21, including what that costs.
