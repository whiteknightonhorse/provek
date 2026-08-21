/**
 * Intake. The one action this site asks a visitor to take, and until 2026-08-20 it did nothing.
 *
 * WHAT IT REPLACED. `onSubmit` was `preventDefault` and nothing else: measured with fetch, XHR and
 * sendBeacon all instrumented, pressing the button produced zero requests, no confirmation and no
 * error. A visitor filled in their repository and their address, pressed the only button on the
 * page, and could not tell "received" from "discarded". Worse, both fields are `required`, so the
 * visitor who left them empty got browser feedback while the one who filled them in correctly got
 * silence — the better they behaved, the less they learned.
 *
 * WHY IT MATTERS BEYOND COURTESY. Specification 1.5 starts the go/no-go clock from the first ten
 * mandate offers made, and 4.6 requires the offer to exist before the clock starts. A dead form
 * does not merely fail an applicant; it destroys the measurement the operator's decision runs on.
 *
 * WHAT "RECEIVED" MAY CLAIM. Fable's ruling: "received" asserts that someone has taken
 * responsibility for reading it, and is honest only if the submission lands somewhere a human
 * actually looks. The durable write alone does not confer that. So the record goes to KV AND a
 * notice goes to the operator's ops channel, and the reply says what actually happens next — a
 * human decision, not a service level. No "we will respond within N days": nothing on our side has
 * promised a clock, so the page may not either.
 */

const MAX = 2000;

function bad(reason, status = 400) {
  return Response.json({ ok: false, error: reason }, { status });
}

function clean(v) {
  return typeof v === "string" ? v.trim().slice(0, MAX) : "";
}

export async function onRequestPost({ request, env }) {
  let body;
  try {
    body = await request.json();
  } catch {
    return bad("The request body could not be read.");
  }

  // Honeypot. A field no human sees and no human fills. Turnstile is deliberately not here yet:
  // it is added if real spam arrives, not in anticipation of it, and it is cookieless when it is.
  if (clean(body.website)) return Response.json({ ok: true, id: "ignored" });

  const repo = clean(body.repo);
  const contact = clean(body.contact);

  // TWO FIELDS, BECAUSE THEY ARE TWO FACTS (D-23, and the previous version of this comment asked
  // for exactly this change).
  //
  // D-21 withdrew the probing mandate from the intake while no prober existed, and did it here
  // rather than only on the form, because a curl POST could otherwise grant an active mandate over
  // a live system and have it stored durably and announced to the operator as though somebody had
  // agreed to it. The form is not the security boundary (L-2). What the withdrawal left behind was
  // a single `mandate` field holding the POLICY APPLIED, so "asked for active, refused" and "asked
  // for passive" were indistinguishable in KV - invariant 1, named in this comment at the time and
  // deferred until the value could differ. T-2.12 built the prober, so it can differ now.
  //
  // WHAT EACH FIELD MEANS, AND THE SECOND ONE IS STILL A CONSTANT. `mandate_requested` is the
  // applicant's own answer and grants nothing. `mandate_applied` is what we may actually do, and
  // it is `passive` for every submission without exception: a mandate is a legal object and not a
  // checkbox (src/mandate/mandate.py), so no HTTP request can produce one. An active mandate
  // begins with a signed document naming permitted actions, a rate ceiling, what must not be
  // affected, liability, an abort condition and how it is revoked - a form cannot collect that and
  // is not asked to. Recording the request is what lets the operator start that exchange.
  const requested = clean(body.mandate);
  if (requested !== "passive" && requested !== "active")
    // NOT COERCED TO A DEFAULT, and that is the whole point of the pair. Guessing what an
    // unrecognised value meant would put our assumption in the field that records the applicant's
    // own answer, which is the collapse the two fields exist to end. The form always sends one of
    // the two, so only a hand-built client reaches this line, and it gets told why.
    return bad('The mandate field must be "passive" or "active" - it is what you are asking for, ' +
               "and we will not guess it on your behalf.");
  const mandate_requested = requested;
  const mandate_applied = "passive";

  if (!/^https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/.test(repo))
    return bad("That does not look like a public GitHub repository URL.");
  if (!/^[^@\s]+@[^@\s.]+\.[^@\s]+$/.test(contact))
    return bad("That does not look like an address we could reply to.");

  const id = crypto.randomUUID();
  const received_at = new Date().toISOString();
  const record = {
    id, received_at, repo, contact, mandate_requested, mandate_applied,
    // Recorded because it is a fact about the submission, and because a verifier that keeps no
    // provenance for its own intake is asking for a trust it does not extend.
    source_country: request.headers.get("cf-ipcountry") || null,
  };

  if (!env.INTAKE) return bad("Intake storage is not configured on this deployment.", 503);
  const key = `request:${received_at}:${id}`;
  // Written BEFORE the notice, so a submission survives a failed announcement. The outcome is
  // written back after, because a record that does not carry whether anyone was told gives a
  // sweep nothing to key on - and an unwatched durable record is "received" drifting back
  // towards "discarded", which is this project's founding defect in its operational form.
  await env.INTAKE.put(key, JSON.stringify({ ...record, delivered: null }));

  // The notice. If this fails the submission is already durable, so the visitor is not told the
  // request was lost - but the claim we may make about it changes, and the response says which.
  let delivered = false;
  if (env.TELEGRAM_BOT_TOKEN && env.TELEGRAM_CHAT_ID) {
    try {
      const text =
        `[provek] verification request\n` +
        // BOTH VALUES, because the notice is the only one of the two records a human reads in
        // time to act. An applicant asking for active probing is the one submission that needs a
        // reply the operator has to compose - a signed mandate - and a message showing only the
        // applied policy would show `passive` for every request forever and hide exactly that.
        `repo: ${repo}\ncontact: ${contact}\n` +
        `mandate requested: ${mandate_requested}, applied: ${mandate_applied}\nid: ${id}`;
      const r = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text, disable_web_page_preview: true }),
      });
      delivered = r.ok;
    } catch {
      delivered = false;
    }
  }

  // THE WRITE-BACK IS THE ONLY STEP THAT RUNS AFTER THE SUBMISSION IS ALREADY DURABLE, AND IT WAS
  // THE ONLY UNCAUGHT ONE. Every other failure in this handler happens before the first `put`, so
  // the 500 it produces makes the form's sentence - "Not recorded ... Nothing was saved" - true.
  // A throw HERE produced the same 500 and therefore the same sentence, about a record that was
  // written eight lines above and a notice that may already have reached the operator. The form
  // was accurate on every path but the one where it was telling somebody their submission was lost
  // while it sat in KV. So the failure is caught and the answer is the true one: the request is
  // recorded, and `delivered` is the delivery outcome that was actually measured.
  //
  // NOT A RARE PATH. Workers KV documents one write per second to the same key and rejects the
  // second with a 429; this is the second write to `key` inside one invocation, separated by at
  // most a Telegram round trip and, with no Telegram credentials configured, by nothing at all.
  // On the documented behaviour the failure is ordinary rather than exceptional
  // (docs/INTAKE_OPERATIONS.md, which measured the limit and predicted this).
  //
  // AND THE RESPONSE IS DELIBERATELY THE SAME ONE THE SUCCESS PATH SENDS. The applicant has two
  // facts to be told - the request is recorded, and whether the operator was notified - and
  // neither changes with whether we managed to write the second of them down. A field reporting
  // our own bookkeeping would be a fact about us, sent to the one party who can do nothing with it
  // and read by nothing on the page.
  //
  // THE OPERATOR IS A DIFFERENT MATTER, AND THIS IS WHERE THE FIRST DRAFT WENT WRONG. It caught the
  // failure, answered honestly, wrote nothing, and defended the silence with "there is nowhere to
  // write it" - which is false, and false in a way that mattered. The limit that produces this
  // failure is one write per second TO THE SAME KEY; a different key is a different write and is
  // not refused by it. So a caught write-back left the record at `delivered: null`, which already
  // meant "the invocation died before it could answer" - and the fix quietly gave that one value a
  // second world, in which the applicant was told the truth and needs nothing. Two states of the
  // world reading identically, in the field the operator's sweep keys on: invariant 1, introduced
  // by the change that closed a different instance of it. Found by Fable.
  //
  // The sentinel is therefore written where the same-key limit does not reach, and it says what
  // was true at the moment it was written: this invocation survived the refusal and is answering.
  // A failure of BOTH writes is caught too, and then there genuinely is no durable channel left -
  // the applicant is still answered, and the record is a bare `null` with no sentinel beside it,
  // which is exactly what the death case looks like and is read the same way.
  //
  // WHAT NO CODE HERE REACHES. Between this sentinel and the `return` below, and between that
  // return and the browser, the answer can still be lost - to eviction, to a dropped connection -
  // and the form then says "Nothing was saved" over a durable record with nothing on our side to
  // show for it. That residue is smaller than it was and it is not empty; L-15 is the standing
  // form of it, and docs/INTAKE_OPERATIONS.md carries the sweep and the limit rather than a claim
  // that the case is closed.
  //
  // None of this is the fix for the same-key limit itself - one write instead of two, or the record
  // under two keys. Which of those is right depends on a reading of the namespace that only the
  // operator can take, and guessing now would spend that reading (docs/INTAKE_OPERATIONS.md).
  try {
    await env.INTAKE.put(key, JSON.stringify({ ...record, delivered }));
  } catch (refusal) {
    try {
      await env.INTAKE.put(
        `writeback-refused:${received_at}:${id}`,
        // `notice_delivered` rather than `delivered`, so the sweep's filter over the records does
        // not also match sentinels: this key is read BESIDE a record, never instead of one.
        JSON.stringify({
          of: key, id, notice_delivered: delivered,
          refused_at: new Date().toISOString(),
          // The store's own words for why it refused. A number or a boolean here would be this
          // project's oldest defect: the reason is what tells the operator whether they are
          // looking at the documented same-key limit or at something nobody has seen yet.
          reason: String((refusal && refusal.message) || refusal),
        }));
    } catch {
      // Both writes refused. There is no durable channel left, the applicant is still answered
      // honestly, and the state on disk is a record with no sentinel - which reads as "we cannot
      // tell whether this applicant was answered", the true statement about it.
    }
  }
  return Response.json({ ok: true, id, delivered });
}

export async function onRequestGet() {
  return bad("This endpoint accepts a submission, not a reading.", 405);
}
