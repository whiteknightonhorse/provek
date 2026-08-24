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
   record stays at `delivered: null`: durable, and carrying no delivery outcome. Until 2026-08-20
   the applicant was ALSO told that nothing had been saved, because the throw became a 500 and the
   form reads a 500 as a refusal — the one place on this site where that sentence was false.
   `apply.js` now catches it and step 5 happens anyway, with the delivery outcome that was actually
   measured, and it writes a `writeback-refused:` sentinel under a different key — the limit that
   causes this is one write per second to the same KEY, so the store is not unavailable, only that
   key is. Without the sentinel `delivered: null` would mean both "answered honestly" and "died
   before answering", which is the sweep's whole decision (`tests/test_intake_survives_a_failed_writeback.py`,
   `evidence/RED-017-nothing-was-saved-about-a-saved-record.txt`).
   How often that happens is argued once, under "What one submission costs" below, and deliberately
   not repeated here: it is the claim most likely to be corrected by the next reading of the
   namespace, and a frequency stated in two places is a frequency that will be updated in one.
   Written into this list because a five-step description that admits two endings is how the third
   one stays invisible.

## The habit — daily for the week the link goes out, weekly after it

**Sweep KV for every record whose delivery outcome is not `true`, and print the states apart.**

Three drafts of this filter, and the third is what this section is now about. It matched
`delivered == false` alone — blind to the state both of T-A2-2's failures land in — then
`false or null`, which finds them and printed both under one word, `UNSEEN`. Those are not one
finding. `false` is a MEASURED outcome: the notice was attempted and did not reach the operator.
`null` is the ABSENCE of that measurement: the record never got its outcome written back and
carries nothing about what the notice did. They are followed up differently — the pairing two
paragraphs down is entirely about `null` — so a label covering both hands the operator a count that
cannot be acted on. Invariant 1, in the instrument this project keeps for enforcing it.

```bash
NS=5d93877f53d94f3fbc4863a0195fc9a4

# A FUNCTION, because two of the branches below have to be able to say "this sweep did not run"
# with an exit status, and `exit` in a pasted-in snippet closes the terminal it was pasted into.
# Paste once; on any later day the sweep is the word `sweep`.
sweep() {
  local raw keys k v d m mark rc=0
  local records=0 notified=0 not_notified=0 no_outcome=0 unreadable=0 marks=0

  # THE LIST IS AN INSTRUMENT AND IT CAN REFUSE, and a refused list prints exactly what an empty
  # namespace prints: nothing. Reported as a state of its own rather than folded into the clean
  # line - a sweep that did not run is not a sweep that found nothing.
  if ! raw=$(npx wrangler kv key list --namespace-id "$NS" </dev/null); then
    echo "SWEEP DID NOT RUN: the namespace could not be listed, so nothing below was measured."
    return 2
  fi
  if ! keys=$(jq -r '.[].name' <<<"$raw" 2>/dev/null); then
    echo "SWEEP DID NOT RUN: the key list came back unreadable, so nothing below was measured."
    return 2
  fi

  while read -r k; do
    [ -n "$k" ] || continue
    # WHAT A KEY IS, BEFORE ANYTHING IS READ FROM IT. A submission and a sentinel are told apart by
    # the key prefix, exactly as the threshold counts below do it, and both are counted here rather
    # than after a successful read - a key the store will not hand over was still LISTED, and a
    # count that only rises on a readable value drops the ones that matter most.
    case "$k" in
      writeback-refused:*) mark=1; marks=$((marks + 1)) ;;
      *)                   mark=0; records=$((records + 1)) ;;
    esac

    # A REFUSED READ IS NOT A RECORD WITH NOTHING WRONG WITH IT. The draft before this one assigned
    # the output of a failed `get` into `$v` and read on, so the one key the store would not hand
    # over printed nothing - which is what a healthy `delivered: true` prints.
    if ! v=$(npx wrangler kv key get "$k" --namespace-id "$NS" </dev/null); then
      echo "UNREADABLE: $k - the store refused the read."
      unreadable=$((unreadable + 1)); rc=1; continue
    fi

    # A REFUSED WRITE-BACK, and the reason this branch exists rather than one filter for everything:
    # a sentinel carries no `delivered` key at all, so a filter over that field matches it and the
    # old one-line sweep would have printed it as an unseen submission. An instrument that reports
    # its own marker as a finding is worse than one that ignores it.
    if [ "$mark" = 1 ]; then
      # AND THE MARK IS READ RATHER THAN ASSUMED. `jq` writes its parse errors to stderr, so an
      # unreadable sentinel printed as a healthy one with an empty summary after it - and the
      # emptiness is invisible to anything capturing stdout, which is what a scheduled job does.
      #
      # THE THREE FIELDS ARE REQUIRED TO BE THERE, and the draft that only checked that `jq` had
      # not failed is why. `{of, notice_delivered, reason}` over a stored `null` or `{}` builds an
      # object of three nulls and succeeds, so a mark carrying nothing printed as a mark that had
      # been read. `has()` rather than a truthiness test, because `notice_delivered: false` is a
      # measured value and must not read as an absent one. The `-z` is the same defect once more,
      # from the tool: jq 1.6 - measured, the version on the audit host - exits 0 on empty input
      # having printed nothing at all, so a mark stored empty passed a check on jq's exit status.
      # What other versions do is NOT measured here, which is the reason the emptiness is tested in
      # the shell rather than inherited from whichever jq the operator's laptop has.
      # Found by Fable, twice on this branch.
      if ! m=$(jq -ce 'if type == "object" and has("of") and has("notice_delivered")
                          and has("reason")
                       then {of, notice_delivered, reason}
                       else error("not a refusal mark") end' <<<"$v" 2>/dev/null) || [ -z "$m" ]; then
        echo "UNREADABLE: $k - the refusal mark itself could not be read."
        unreadable=$((unreadable + 1)); rc=1
      else
        echo "SURVIVED TO ANSWER: $k $m"
      fi
      continue
    fi

    # The value itself and not a rendering of it: `tostring` would print the string "false" and the
    # boolean `false` identically, and only one of those is a delivery outcome this endpoint writes.
    d=$(jq -c 'if type == "object" and has("delivered") then .delivered else "no-such-field" end' \
          <<<"$v" 2>/dev/null) || d=unreadable
    case "$d" in
      true)  notified=$((notified + 1)) ;;
      false) echo "NOT NOTIFIED: $k - stored, and the notice to the operator did not go out."
             not_notified=$((not_notified + 1)); rc=1 ;;
      null)  echo "NO OUTCOME: $k - stored, and nothing recorded what the notice did."
             no_outcome=$((no_outcome + 1)); rc=1 ;;
      *)     echo "UNREADABLE: $k - no readable delivery outcome in the record (got: $d)."
             unreadable=$((unreadable + 1)); rc=1 ;;
    esac
  done <<<"$keys"

  # RECORDS PLUS MARKS IS EVERY LINE THE LIST YIELDED, whether or not it could be read, so the two
  # numbers account for the namespace and `UNREADABLE` says how much of it was not measured. A key
  # containing a newline would be counted as two, and one padded with spaces read under a name it
  # does not have; `apply.js` builds every key from a timestamp and a UUID, so neither shape can
  # come from this endpoint, and both are named here rather than defended against. Found by Fable.
  echo "SWEPT $records records and $marks refusal marks: notified $notified," \
       "NOT NOTIFIED $not_notified, NO OUTCOME $no_outcome, UNREADABLE $unreadable."
  # ONLY WHEN THE NAMESPACE WAS EMPTY, and the first draft of this line asked `records == 0` alone.
  # A refused read leaves `records` at zero on a namespace holding a submission, and a sentinel
  # exists only because a submission was made - so that draft printed "no submission has ever been
  # made" over both, which is a claim about values nobody read, in the sentence this document keeps
  # in order to forbid exactly that. Found by Fable.
  [ "$records" -eq 0 ] && [ "$marks" -eq 0 ] &&
    echo "Zero keys is a reading of its own: no submission has ever been made."
  return $rc
}

sweep
```

**Four labels, a count that always prints, and one line that replaces all of them.**

* **`NOT NOTIFIED`** — `delivered: false`: the record is stored and the operator was not told. The
  applicant was told their request was recorded and that the record is safe and may be read later
  than usual; this sweep is what makes that sentence true rather than consoling.
* **`NO OUTCOME`** — `delivered: null`: stored, carrying no delivery outcome, and the worse case,
  because it is what both a refused write-back and a dead invocation leave. Printing here is not the
  same as nobody having been told — a `null` paired with a sentinel reading `notice_delivered: true`
  prints here and the operator WAS told about it, in time, by the notice. Read the pairing below
  before acting.
* **`UNREADABLE`** — the store refused the read, or what came back is not a record carrying a
  `delivered` field, or it is a sentinel that could not be parsed. A refusal that returns as an
  ordinary answer takes from the follow-up its only evidence that anything was missed (§2.9), and
  this is the label that keeps it. It is the one label that is not about the applicant: it says
  which part of the namespace this run did not measure.
* **`SURVIVED TO ANSWER`** — a `writeback-refused:` sentinel, under its own label because it is not
  a submission and cannot be answered, and only once its `of`, `notice_delivered` and `reason` have
  actually been read out of it.
* **`SWEPT n records and m refusal marks: …`** — printed on every run that ran, including
  `SWEPT 0 … and 0 …`. A sweep whose findings are its whole output cannot say *I read eleven records
  and none of them qualified*, which is the reading that ends a quiet day. `n + m` is every key that
  was LISTED, readable or not, so the two numbers account for the namespace and `UNREADABLE` says
  how much of it went unmeasured. And zero keys is itself a reading: no submission has ever been
  made — the state in which the endpoint has never once been exercised end to end. That sentence is
  printed only for zero keys, never for zero readable ones; a sentinel with no readable record beside
  it is a namespace that has had a submission.
* **`SWEEP DID NOT RUN`** — instead of the count, never beside it. Nothing was measured, and that is
  not an empty namespace.

**The exit status carries the same three states**, for the day this stops being a habit and becomes
a scheduled job: `0` ran and nothing qualified, `1` ran and there is something to act on, `2` did
not run. A job that reported *did not run* as `0` would go quiet in precisely the way this whole
document is about.

*(`false` is itself two states — the notice was attempted and refused, or no Telegram credentials
were configured so nothing was attempted at all. Invariant 1, open, and named here rather than
fixed: the production Pages project carries both variables, so the second state is not reachable
there today, and widening the field's domain would touch the sweep above, the confirmation copy and
the shipped list of stored fields on the form. It is a task, not a line.)*

What any of the three findings names is a submission whose fate nobody has CONFIRMED, which is not
the same as one nobody saw: this line said the stronger thing until the sentinel made the weaker one
representable. Which is why a `NO OUTCOME` is not acted on by its label alone.

**A `NO OUTCOME` is read together with the sentinel beside it, and that pairing is the whole of the
follow-up:**

* **`null` WITH a `writeback-refused:` key for the same id** — the write-back was refused, the
  endpoint caught it, and it was still running when it wrote the sentinel, one statement before it
  answered. Act on the record. The store holds no evidence that anything false was said, which is
  weaker than "nothing false was said" and is deliberately weaker: the sentinel is written *before*
  the `return`, so a death in between, or an answer lost on the way to the browser, still shows this
  shape. The sentinel's `reason` is worth reading: the documented same-key 429 is a known cost, and
  anything else is a finding.
* **`null` with NO sentinel** — nothing recorded that the endpoint reached its answer. Two ways in:
  the invocation died, or both writes were refused (the sentinel's own write is caught too, and
  then the applicant WAS answered honestly). Nothing distinguishes them, so act on the record and
  treat the person as uninformed. This is the state the sentinel exists to separate out; before it
  existed, every `null` was this one.

**What a correction may say, in either case.** Not *"you were told your submission was lost"* — we
do not know that, and in the both-writes-refused case it is false. What we hold is the record, so
that is what the reply states: the request is here, this is what it says, and this is what happens
next. A correction that asserts what someone's browser displayed is the same class of claim as the
one this whole section is about.

**And there is a residue neither of them can see, at any value of `delivered`.** If the answer is
lost after the record is written — the invocation killed between the last write and the return, the
connection dropped, a truncated body that fails to parse in the browser — the form shows *"Not
recorded … Nothing was saved"* over a record that is stored, and the store holds no trace of it: the
record reads `true` or `false` like any ordinary one and the sweep passes it by — or it reads `null`
with a sentinel, which the sweep prints under a label about the endpoint and not about the
applicant. What the browser
rendered is not observable from here at all, and no code inside a request can witness its own death
(L-15). It is not "the case is closed": it is a smaller residue than the one this endpoint had, with
its size unmeasured. **The reply to any applicant who writes to ask is therefore never "our records
show you were told" — it is the record itself, which is the fact we actually hold.**

The ops channel answers one question and only one: whether the notice went out for a given id. It
cannot say what the visitor's browser displayed, and an earlier draft of this section used it as the
tie-breaker for exactly that — the wrong instrument for the quantity (L-10), named by Fable.

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
then `delivered: true|false` after it (`web/functions/api/apply.js`) — plus, only when that second
write is refused, one write to a *different* key for the `writeback-refused:` sentinel (T-A2-2).

**What the sentinel costs depends on the same unresolved question as everything below**, and the
first draft of this paragraph said "the ceiling arithmetic is unchanged", which is true only under
the optimistic reading the rest of this section refuses to plan against. If a refused same-key write
spends nothing, a refused-writeback submission costs two units and the ceiling is unmoved. If it
spends a unit — the pessimistic reading, the one the numbers below are calibrated on — it costs
three, and the ceiling on a day where every write-back is refused is ~333 rather than 500, which
would make S-4's 125 more than a third of the budget instead of a quarter. Neither number is
measured; the sweep that settles the first question settles this one with it. Found by Fable. The second write is what the
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
  The two `put` calls in `apply.js` are two writes to one key in one invocation, with at most a
  Telegram round trip between them and, when no Telegram credentials are configured, nothing at all.
  So the documented behaviour puts the next bullet on the MAIN PATH rather than on a rare failure:
  it predicts that every submission whose two writes fall inside one second is stored with its
  delivery outcome unrecorded. Not every submission unconditionally — a Telegram round trip longer
  than a second would separate the writes legitimately — and not "intake is broken", because the
  record survives. Until 2026-08-20 what broke with it was the applicant's confirmation, which said
  the submission had been lost; that half is fixed. What remains is the `delivered` signal the whole
  habit above keys on, which stays `null` and is why the sweep matches it.

  **Enforcement has not been observed, and the first draft of this paragraph said the only way to
  observe it would be to POST a fabricated submission into the operator's live intake. That was
  false, and the instrument is the sweep under *The habit* above.** It IS the measurement, retrospectively
  and for free: if the second write always fails, every record in the namespace is stuck at
  `delivered: null`; if it lands, records carry `true` or `false`. One `list`, no notice, nothing
  fabricated, and the operator runs it anyway. **Do that before publishing the link, and read the
  `delivered` values rather than only the count.** Two more paths exist if it is inconclusive: a
  preview deployment would exercise a real binding with no Telegram credentials configured — WHICH
  namespace it binds is `not_measured`, and the answer decides whether that path measures production
  or writes into it, which a later section of this document sets out — and two
  `wrangler kv key put` calls inside one second on a scratch key test the limit directly — the
  latter over the REST path rather than the Worker binding, which is an L-10 caveat on the reading
  and not a reason to skip it. And the empty case is a case: **zero records means no submission has
  ever been made**, which is itself the reading — the state in which the endpoint has never once
  been exercised end to end, and the one the launch is about to leave.

  Only after that reading is the fix a code change with its own red run — one write instead of two,
  or two distinct keys. It is not taken here.
* **A failed second write stranded a record the sweep was blind to, and told the applicant the
  opposite of the truth. Half of that is fixed and half of it is what the sweep is for.** The first
  `put` stores `delivered: null`; if the second `put` threw, nothing caught it — the notice block
  had its own `try/catch` and a failed notice merely sets `delivered = false`, so the second `put`
  was the only uncaught step — the Function answered 500, the client rendered `HTTP 500` as its
  reason, and the form said *"Not recorded. … Nothing was saved"* (`web/src/pages/Apply.tsx`, where
  it is an honest sentence in every other failure). Here the record WAS saved. It sits at
  `delivered: null`, which the sweep's original filter — `select(.delivered == false)` — does not
  match, so the one record in the namespace that nobody has seen and nobody will follow up was the
  one record the habit above skipped. That is exactly the case the sweep exists for, and it is why
  the filter matches `null` as well as `false` — and why, since T-A2-3, it prints them under
  different labels and a gate that RUNS the sweep fails the build if it stops
  (`tests/test_intake_sweep_distinguishes_its_states.py`,
  `evidence/RED-018-a-sweep-that-cannot-name-what-it-found.txt`). Until then the correction lived
  only in a fenced block in a document, where nothing could go red over it.

  **The endpoint was changed on 2026-08-20 (T-A2-2), the day after this bullet named the defect and
  left it.** The write-back is caught, the applicant gets the ordinary confirmation carrying the
  delivery outcome that was measured, and a `writeback-refused:` sentinel is written under a
  different key so the two meanings of `delivered: null` stay apart. The gate is a biconditional:
  red if a durable record is disclaimed, and red if a submission the endpoint tried and failed to
  store is confirmed (`tests/test_intake_survives_a_failed_writeback.py`, nine mutations in
  `evidence/RED-017-nothing-was-saved-about-a-saved-record.txt`, five of which were green when
  they were first applied). Scoped deliberately: the honeypot
  branch answers `ok: true` for a submission it discards on purpose, before any write, and is
  outside both directions — see the last bullet of "Two classes of traffic" below.

  What the fix does NOT reach is the record left by a dead invocation, and the residue described
  under the sweep above. A `null` with no sentinel is still a person who was told the opposite of
  the truth, and the sweep is still the only instrument that finds them.

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
`received_at` (UTC), from the `request:` records in KV — junk needs the repo and contact, so it
needs the record. S-3 and S-4 do not: submission keys are `request:${received_at}:${id}` (`apply.js`, the
`key` binding), so counting them per hour or per day is one `list` request and no reads at all —

```bash
npx wrangler kv key list --namespace-id "$NS" \
  | jq -r '[.[].name | select(startswith("request:"))] | length'
```

**The prefix filter is load-bearing and this line did not have it.** Since T-A2-2 the namespace
also holds `writeback-refused:` keys, and by the argument two sections up a refused write-back is
the MAIN path rather than a rare one — so a bare key count reads up to twice the number of
submissions, and every threshold below would fire at half its stated number while still sounding
like a count of people — S-3 and S-4, which are key counts. S-1 and S-2 count junk records, which
the operator classifies by reading them, so they are unaffected; the same filter belongs in that
reading anyway, because a sentinel is not a submission and cannot be answered. A threshold on a
quantity that has quietly changed its unit is L-24 in the small: the number stayed correct and
stopped meaning what it says. Found by Fable, in the sentence this same change had just edited.

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
  record in KV carries an IP. the `record` literal in `apply.js` stores id, `received_at`, repo, contact, both mandate
  fields and `source_country` (`cf-ipcountry`), and the counting method three paragraphs up is "from the
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
hit is answered `{ ok: true, id: "ignored" }` before any write (`apply.js`, the honeypot branch),
and a submission that fails URL or address validation is answered 400 (`apply.js`, the two
`bad("That does not look like")` refusals); neither reaches KV. So every number above counts only
what got PAST both — which is the traffic Turnstile and a per-IP limit exist to stop, so the
thresholds still fire on the right quantity, but the quiet they are measured against is not evidence
of quiet. *No bots came* and *bots came and were absorbed* read identically in KV: invariant 1,
inside the intake's own instrument.

**The honeypot's `ok: true` is the one confirmation on this site that is deliberately false**, and
it is worth saying out loud beside a gate whose subject is confirmations that outrun their records:
the form shows *"Your request is recorded … The record itself is safe"* to whoever tripped it, and
nothing was written. For a bot that is the design. For a human it would be the exact defect T-A2-2
closed, facing the other way — and the hidden field is `<input name="website">`, which is a name
form-fillers are known to recognise. Whether any real client fills it here is **not measured**: it
needs one submission from a browser with a filler enabled, which nobody has made, and it is written
down as an open question rather than answered by reasoning about browsers. If it turns out to be
reachable, the answer is a field name no filler targets, not a weaker honeypot.

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

**No probing on submission, and none without a signature.** The probing mandate was removed from
the form on 2026-08-20 because no prober existed to honour it. T-2.12 built one, so the option
returned the same day (D-23) — and what returned is a QUESTION, not a grant.

Removed from the ENDPOINT as well as the form, and only after that was it actually gone: `apply.js`
had kept `body.mandate === "active" ? "active" : "passive"`, which honours `active` for any client
that is not the form, so a `curl` POST could have recorded a probing mandate over production. That
property is unchanged by the option's return. The endpoint now writes two fields:

| field | who decides it | today's value |
| --- | --- | --- |
| `mandate_requested` | the applicant | `passive` or `active`; anything else is a 400, never a guess |
| `mandate_applied` | us, in code | `passive`, on every submission without exception |

`tests/test_intake_records_the_mandate_request.py` fails the build if the applied policy stops
being a constant, if it is ever computed from the request body, if the two fields collapse back
into one, or if the form starts offering a value the endpoint would refuse.

**What the operator does with an `active` request.** Write back with a mandate document naming the
one action the prober implements (`unauthenticated_access_attempt`), **the three requests one probe
spends on their origin** (`CALLS_PER_PROBE`: a positive control, a negative control and the
attempt, all three counted against the ceiling), the paths, the hourly ceiling, the blast radius,
the liability, the abort condition and the revocation route — the fields `src/mandate/mandate.py`
requires.

⚠️ The count is in this list because `/apply/` now tells the applicant the document will contain
it: the confirmation reads "it names the one action and the three requests it spends on your
origin". An instruction that omits what the page promised is how the page becomes false without
anybody editing it — the promise is kept by the operator, not by the form, and T-A2-5 corrected the
form first. `tests/test_apply_names_the_probe_cost.py` holds the page's copy against
`src/prober/prober.py`; nothing can hold a document the operator has not written yet, so this line
is the whole of the mechanism and it is prose. The Telegram notice carries both values for this reason: an
`active` request is the one submission that needs a composed reply rather than a queue position.

⚠️ **Read 2026-08-24 12:11:57 UTC, `GET https://provek.dev/api/apply` answered 405 — the Function was
published and executing at that minute, and what it does with a POST is `not_measured`.** Both
halves are read from the origin rather than from a tool's report of itself, and both readings carry
the minute they were taken. The paragraph this replaces carried a date too and that was not what
went wrong with it: it spoke in the present tense around the dated reading — *is not deployed at
all*, *today*, *until that is fixed* — so the reading stayed pinned to 2026-08-20 while the sentences
built on it went on asserting themselves after they had stopped being true. Every status sentence in
this section is therefore in the past tense of its own stamp, including that one.

| request | read 2026-08-24 12:11:57 UTC | what it settles |
| --- | --- | --- |
| `GET https://provek.dev/api/apply` | **405**, body `{"ok":false,"error":"This endpoint accepts a submission, not a reading."}` | the handler was deployed AND running: that sentence is `web/functions/api/apply.js:196` and no edge default carries it |
| `GET https://provek.dev/functions/api/apply.js` | **404** | the source was not served in place of the handler — the outcome D-23 named as worse than the 404 it replaced |
| `GET https://provek.dev/api/nonexistent-xyz` | **404** | control: the 405 is a fact about this path, not the site's answer to everything unknown |
| `GET https://provek.dev/` | **200** | control: the origin answered this client at all, so the codes above describe resources and not us (L-11) |
| `GET https://provek.dev/deploy-label.txt` | **200**, body `57a267c` | WHICH deployment answered, so the 405 belongs to a named deployment rather than to whatever happened to be serving |

The same four codes were read twice before, and both earlier readings answered under a DIFFERENT
deployment label, `a369de3`: at **2026-08-24 04:37 UTC** and again at **07:04 UTC**. The 04:37
reading is the one with a surviving artefact — it is the table inside
`evidence/T-H4-stash-e64678f-intake-operations.patch`, which this commit carries, its label line
included — so the comparison does not rest on a reading whose only carrier has since been discarded.
The 405 therefore answered under two distinct deployment labels; on the premise that a deployment
serves only what it carries, that places the handler in the published tree rather than in a single
upload. The premise is platform behaviour and is not itself measured here — what is measured is two
labels and the same four codes.

The **404** this paragraph carried until 2026-08-24 was a true reading of 2026-08-20
(`evidence/PROBE-001.txt`) with one cause: `wrangler pages deploy` finds `functions/` relative to
its working directory, `~/orchestra/deploy.sh` ran it from the repository root, and the handler
lives in `web/functions/`. That file was changed to run the deploy from `web/` (read 2026-08-24). It
sits outside this repository, so this document records that the change happened and not who made it.

**The POST path is `not_measured`, and the named reason is that the only probe that would answer it
is a real submission.** This is `check_did_not_run` — not a zero, not a pass inherited from the 405.
A `GET` enters `onRequestGet` and returns without touching `env`, so every line the intake actually
depends on sits in `onRequestPost`, and no reading taken here exercises any of it: that `env.INTAKE`
resolves at runtime (`apply.js:91` answers 503 if it does not), that `TELEGRAM_BOT_TOKEN` and
`TELEGRAM_CHAT_ID` are readable by the Function, that the two writes to one key land rather than
hitting the 1/s refusal the bullet above predicts, and that the `writeback-refused:` sentinel is
written when they do. Whether some stranger has exercised it since the deploy is a separate
`not_measured`: it is answered by reading the namespace, and the namespace has not been read here. A
VALID submission is the only probe that reaches any item on that list — an invalid one is refused
at validation before the first `put` (`apply.js:38`–`80`) and settles none of them — and a valid one
puts a durable record into the production `INTAKE` namespace and wakes the operator on Telegram.
The endpoint has no dry run, and nothing here submits to a live intake in order to produce a green
line in a document. The Pages project was recorded as carrying
the `INTAKE` namespace and both Telegram variables on 2026-08-20 (`evidence/PROBE-001.txt`) — that
is a fact about the project's configuration, and the list above is about the Function resolving them
at runtime, which is a different reading.

**One thing lifts it, and the second candidate is itself unmeasured.** The sweep under *The habit*
above reads the namespace retrospectively: it fabricates nothing, sends no notice, and answers both
questions — whether anyone has submitted, and what the `delivered` values are — in one `list`. The
preview deployment named in the bullet above is the other candidate, and what a preview deployment
BINDS has never been read: `evidence/PROBE-001.txt` asked the Pages project for names and got
`production kv_namespaces` and `production env_vars`, which is a reading about production and about
nothing else. The two possibilities fall on opposite sides of the point — if preview binds the
production namespace, a POST there puts a durable record into the operator's live intake, which is
the fabricated submission this section refuses; if it binds its own, the probe cannot settle the
first item on the list, which is about production resolving at runtime. So read the preview
configuration before treating it as a way in. Until one of these runs, this section describes an
endpoint whose GET half is measured and whose POST half is not. See D-23.

**Nothing goes red when the readings above expire, and that is named rather than left implicit.**
No gate in this repository reads the origin for this paragraph — the one that runs
(`tests/test_intake_sweep_distinguishes_its_states.py`) extracts the sweep's fenced block and knows
nothing about `/api/apply`. The date beside the readings is the whole of the staleness mechanism and
it is prose, which is L-25's boundary exactly: a suite is about what it can read. The argument that
a check against a live origin would go red over somebody else's network does not hold — a refusal is
`check_did_not_run` and a measured 404 is the finding, and telling those apart is invariant 1 rather
than a reason not to build it. It is a task with its own red run, it is not taken here, and it is
recorded so the next reader inherits a named gap instead of a confident date.
