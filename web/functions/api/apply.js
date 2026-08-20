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
  const mandate = body.mandate === "active" ? "active" : "passive";

  if (!/^https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/.test(repo))
    return bad("That does not look like a public GitHub repository URL.");
  if (!/^[^@\s]+@[^@\s.]+\.[^@\s]+$/.test(contact))
    return bad("That does not look like an address we could reply to.");

  const id = crypto.randomUUID();
  const received_at = new Date().toISOString();
  const record = {
    id, received_at, repo, contact, mandate,
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
        `repo: ${repo}\ncontact: ${contact}\nmandate: ${mandate}\nid: ${id}`;
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
