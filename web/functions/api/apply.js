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

  await env.INTAKE.put(key, JSON.stringify({ ...record, delivered }));
  return Response.json({ ok: true, id, delivered });
}

export async function onRequestGet() {
  return bad("This endpoint accepts a submission, not a reading.", 405);
}
