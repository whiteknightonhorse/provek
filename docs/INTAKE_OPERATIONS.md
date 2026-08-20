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
5. The applicant is told which of the two happened, in different words. "Recorded and has reached
   the operator" is only said when it did.

## The habit — weekly, and it is not optional

**Sweep KV for `delivered: false`.**

```bash
npx wrangler kv key list --namespace-id 5d93877f53d94f3fbc4863a0195fc9a4 \
  | jq -r '.[].name' \
  | while read -r k; do
      npx wrangler kv key get "$k" --namespace-id 5d93877f53d94f3fbc4863a0195fc9a4 \
        | jq -e 'select(.delivered == false)' >/dev/null && echo "UNSEEN: $k"
    done
```

Anything it prints is a person who was told their request was recorded and whose request nobody
saw. The confirmation page promises them that the record is safe and may be read later than usual;
this sweep is what makes that sentence true rather than consoling.

Weekly is proportionate at this volume. If a record is ever found this way, or if volume rises
enough that a week is too long, the sweep becomes a scheduled job — not before, because machinery
built against a risk that has not appeared is machinery nobody maintains.

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
