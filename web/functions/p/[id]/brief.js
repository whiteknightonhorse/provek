/**
 * The brief page. `GET /p/<slug>/brief` - what a verified subject links its OWN clients to, and
 * what the badge's `<a href>` points at. Short on purpose (decision, this task): the full
 * `/p/<slug>/` passport stays exactly as it is, built for a due-diligence reader who wants the
 * control map, the observations and the accountability block. This page is for that subject's
 * client, who needs three things - who, how much of the business runs without a human PER
 * OPERATION, and until when - and a way to reach the long version if they want it.
 *
 * WHY A FUNCTION, LIKE THE BADGE, AND NOT A PRERENDERED REACT ROUTE. The site's own registry and
 * passport pages are prerendered at `npm run build` and corrected only by a client re-running
 * `effectiveStatus` after hydration (`web/src/App.tsx`) - which is invisible to a crawler, a link
 * unfurler, or any other reader that does not execute the site's JavaScript, and exactly the gap
 * this task's badge exists to close for the `<img>` case. A page meant to be linked FROM OTHER
 * PEOPLE'S SITES will be fetched by exactly that kind of reader more often than the main site is,
 * so it gets the same treatment as the badge: rendered fresh on every request, against the
 * request's own clock, from the same `effectiveStatus` this Function shares with the badge
 * (`../../_lib/status.js`) rather than from whatever was true at the last scheduled rebuild.
 *
 * ABI-2-3, restated for this surface. The vector is the point: every operation is listed with its
 * own level or its own absence, never folded into one figure. The autonomy projection, when it
 * exists, is shown once, under its own name, with the same one-line caveat the full passport
 * carries - never as an unlabelled headline number.
 *
 * NO EXTERNAL FONT REQUEST, matching `web/src/index.css`'s own reasoning for the main site: a page
 * meant to be embedded on a client's client's site should not add a third party's font fetch to
 * whatever that page already costs its own visitors. The family names are the ones the fontstack
 * degrades to identically on the main site when the real face has not loaded yet.
 */
import { effectiveStatus } from "../../_lib/status.js";
import { LIGHT, DARK } from "../../_lib/palette.js";
import { OP_LABEL, OP_DESC, REASON_TEXT } from "../../_lib/copy.js";

const SLUG = /^[A-Za-z0-9_-]+$/;
const SITE = "https://provek.dev";

function esc(s) {
  return String(s).replace(/[<>&"]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;" }[c]));
}

function daysUntil(validUntil, now) {
  return Math.ceil((new Date(validUntil).getTime() - now.getTime()) / 86_400_000);
}

const STYLE = `
:root {
  --ink: ${LIGHT.ink}; --ink-2: ${LIGHT.ink2}; --ink-3: ${LIGHT.ink3};
  --line: ${LIGHT.line}; --line-2: ${LIGHT.line2};
  --paper: ${LIGHT.paper}; --paper-2: ${LIGHT.paper2};
  --pass: ${LIGHT.pass}; --warn: ${LIGHT.warn}; --fail: ${LIGHT.fail}; --unknown: ${LIGHT.unknown};
  --slot: ${LIGHT.slot};
  color-scheme: light dark;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ink: ${DARK.ink}; --ink-2: ${DARK.ink2}; --ink-3: ${DARK.ink3};
    --line: ${DARK.line}; --line-2: ${DARK.line2};
    --paper: ${DARK.paper}; --paper-2: ${DARK.paper2};
    --pass: ${DARK.pass}; --warn: ${DARK.warn}; --fail: ${DARK.fail}; --unknown: ${DARK.unknown};
    --slot: ${DARK.slot};
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--paper-2); color: var(--ink);
  font-family: "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif;
  line-height: 1.5; font-size: 15px;
}
main { max-width: 40rem; margin: 0 auto; padding: 2rem 1.25rem 3rem; }
.brand { font-size: 0.75rem; letter-spacing: 0.06em; text-transform: uppercase; color: var(--ink-3); }
.brand a { color: inherit; text-decoration: none; }
h1 { font-size: 1.375rem; margin: 0.5rem 0 0; word-break: break-word; }
.meta { margin: 0.5rem 0 0; font-size: 0.8125rem; color: var(--ink-3); }
.status { font-family: "IBM Plex Mono", ui-monospace, SFMono-Regular, monospace; font-weight: 600;
  letter-spacing: 0.02em; text-transform: uppercase; }
.status--verified { color: var(--pass); }
.status--stale { color: var(--warn); }
.status--suspended, .status--failed, .status--withdrawn { color: var(--fail); }
.status--unverified, .status--in_progress { color: var(--unknown); }
.strip { margin-top: 1rem; border: 1px solid var(--line); padding: 0.75rem 1rem; background: var(--paper); font-size: 0.875rem; }
.strip--warn { background: color-mix(in srgb, var(--warn) 12%, var(--paper)); }
section { margin-top: 1.5rem; }
h2 { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ink-2); margin: 0 0 0.5rem; }
.ops { border-top: 1px solid var(--line); }
.op { display: flex; gap: 1rem; padding: 0.6rem 0; border-bottom: 1px solid var(--line); align-items: baseline; }
.op-level { font-family: "IBM Plex Mono", ui-monospace, SFMono-Regular, monospace; width: 2.5rem; flex: none; color: var(--ink); }
.op-body { min-width: 0; }
.op-name { font-weight: 500; }
.op-desc { color: var(--ink-2); font-size: 0.8125rem; margin-top: 0.1rem; }
.slot { display: inline-block; min-width: 2.75ch; height: 1em; border-bottom: 2px solid var(--slot); vertical-align: baseline; }
.tag { font-family: "IBM Plex Mono", ui-monospace, SFMono-Regular, monospace; font-size: 0.6875rem;
  letter-spacing: 0.05em; text-transform: uppercase; color: var(--ink-2); border-bottom: 1px solid var(--line-2); padding-bottom: 0.05em; margin-left: 0.4rem; }
.projection { border: 1px solid var(--line); background: var(--paper); padding: 0.9rem 1rem; }
.projection .value { font-size: 1.75rem; font-weight: 600; }
.caveat { color: var(--ink-2); font-size: 0.8125rem; margin-top: 0.4rem; }
footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--line); font-size: 0.8125rem; color: var(--ink-3); }
a.full-link { color: var(--ink); }
:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }
`;

function opRow(op) {
  const absent = !op.measured;
  const level = absent
    ? `<span class="slot" aria-hidden="true"></span><span class="visually-hidden">not measured</span>`
    : esc(op.level);
  const confidence = !absent && op.confidence === "inferred"
    ? `<span class="tag">inferred</span>` : "";
  const reasonText = absent ? (REASON_TEXT[op.level] ?? op.level) : "";
  return `<div class="op">
    <div class="op-level">${level}</div>
    <div class="op-body">
      <span class="op-name">${esc(OP_LABEL[op.operation] ?? op.operation)}</span>${confidence}
      <div class="op-desc">${esc(OP_DESC[op.operation] ?? "")}${absent ? ` &mdash; not measured: ${esc(reasonText)}` : ""}</div>
    </div>
  </div>`;
}

function page(p, slug) {
  const now = new Date();
  const status = effectiveStatus(p.status, p.valid_until, now);
  const projection = p.verified && typeof p.verified.projection === "number" ? p.verified.projection : null;
  const left = daysUntil(p.valid_until, now);
  const title = `${p.subject_id} - summary - Provek`;
  const ops = (p.verified?.operations ?? []).map(opRow).join("\n    ");

  const staleStrip = status === "stale" ? `
  <div class="strip strip--warn">
    <strong>This passport has lapsed.</strong> Its evidence window closed on ${esc(p.valid_until.slice(0, 10))}
    and it has not been renewed. What is below was true when measured; it is not a current statement.
  </div>` : "";

  const affiliatedStrip = p.verifier_affiliation === "same_owner" ? `
  <div class="strip">
    <strong>Affiliated verification.</strong> The subject and the verifier's owner are the same
    party. This is a rehearsal of the protocol, not an independent verification.
  </div>` : "";

  const projectionBlock = `
  <section>
    <h2>Autonomy projection</h2>
    <div class="projection">
      ${projection === null
        ? `<span class="slot" aria-hidden="true"></span><span class="visually-hidden">not measured</span>`
        : `<span class="value">${projection}</span> / 100`}
      <p class="caveat">Measures autonomy. Not reliability, decision quality, profitability, or the
        presence of an accountable party. Full composition on the <a class="full-link" href="/p/${esc(slug)}/">full passport</a>.</p>
    </div>
  </section>`;

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="Summary autonomy passport for ${esc(p.subject_id)}. Status ${esc(status)}.">
<link rel="canonical" href="${SITE}/p/${esc(slug)}/brief">
<style>${STYLE}.visually-hidden{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);}</style>
</head>
<body>
<main>
  <p class="brand"><a href="${SITE}/">Provek &mdash; evidence, not claims</a></p>
  <h1>${esc(p.subject_id)}</h1>
  <p class="meta">
    <span class="status status--${esc(status)}">${esc(status)}</span>
    &nbsp;&middot;&nbsp; valid until ${esc(p.valid_until.slice(0, 10))}${left > 0 ? ` (${left} days)` : ""}
  </p>
  ${staleStrip}${affiliatedStrip}

  <section>
    <h2>Per operation</h2>
    <p class="caveat" style="margin-top:0">A level is assigned to an operation, never to the whole
      company &mdash; a single number for a company is a marketing number.</p>
    <div class="ops">
    ${ops}
    </div>
  </section>
  ${projectionBlock}

  <footer>
    <p><a class="full-link" href="/p/${esc(slug)}/">Full passport, with the evidence behind every number &rarr;</a></p>
    <p>Verified by <a class="full-link" href="${SITE}/">Provek</a>. The score measures autonomy
      only, and does not measure reliability, decision quality, profitability, or the presence of
      an accountable party.</p>
  </footer>
</main>
</body>
</html>
`;
}

function notFound(reason) {
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>No such passport - Provek</title>
<style>body{font-family:ui-sans-serif,system-ui,sans-serif;max-width:40rem;margin:3rem auto;padding:0 1.25rem;}</style>
</head><body><h1>No such passport</h1><p>${esc(reason)}</p>
<p><a href="${SITE}/registry/">Back to the registry</a></p></body></html>
`;
}

export async function onRequestGet({ request, params, env }) {
  const slug = params.id;
  if (typeof slug !== "string" || !SLUG.test(slug))
    return new Response(notFound("This address is not a subject identifier."),
      { status: 404, headers: { "content-type": "text/html; charset=utf-8" } });

  let res;
  try {
    const assetUrl = new URL(request.url);
    assetUrl.pathname = `/data/passports/${slug}.json`;
    assetUrl.search = "";
    res = await env.ASSETS.fetch(assetUrl.toString());
  } catch {
    return new Response(notFound("The record could not be read."),
      { status: 502, headers: { "content-type": "text/html; charset=utf-8" } });
  }
  if (!res.ok)
    return new Response(notFound("Nothing has been issued under this identifier."),
      { status: 404, headers: { "content-type": "text/html; charset=utf-8" } });

  let data;
  try {
    data = await res.json();
  } catch {
    return new Response(notFound("The record could not be read."),
      { status: 502, headers: { "content-type": "text/html; charset=utf-8" } });
  }
  const p = data && data.passport;
  if (!p)
    return new Response(notFound("Nothing has been issued under this identifier."),
      { status: 404, headers: { "content-type": "text/html; charset=utf-8" } });

  return new Response(page(p, slug), {
    status: 200,
    // Short, for the same reason as the badge: a lapse into `stale` needs no new evidence, only
    // the date to pass, and a long cache would go on showing the old word after it has.
    headers: { "content-type": "text/html; charset=utf-8", "cache-control": "public, max-age=300, s-maxage=300" },
  });
}

export async function onRequestPost() {
  return new Response("This endpoint answers a reading, not a submission.", { status: 405 });
}
