/**
 * The badge. `GET /badge/<slug>.svg` - a small SVG a verified subject embeds on ITS OWN site to
 * show ITS OWN clients that Provek looked, with one line of markup:
 *
 *   <a href="https://provek.dev/p/<slug>/brief"><img src="https://provek.dev/badge/<slug>.svg" ...></a>
 *
 * WHY A FUNCTION AND NOT A FILE UNDER `web/public/badge/`. A static file is baked at the last
 * `npm run build` and would go on reading `verified` after a passport lapses to `stale` between
 * deploys - the exact defect ABI-15-5 exists to name. An `<img>` tag runs no JavaScript, so there
 * is nobody on the visitor's side to recompute the date the way the hydrated site already does at
 * every real visit (`web/src/types.ts:effectiveStatus`). The recomputation has to happen HERE,
 * against the request's own clock, which is what makes this a Function rather than an asset.
 *
 * ABI-2-3 (Fable's ruling), AND WHY THIS IS THE ONE FILE MOST LIKELY TO BREAK IT. A level is
 * assigned to an OPERATION, never to a company: a single scalar per company is the marketing
 * number this product exists to replace. A badge is the single most viral artefact this project
 * makes - the one surface most likely to be copy-pasted onto somebody else's homepage with no
 * other context around it - so a bare "L4" printed here would make Provek the producer of exactly
 * the number it was built to replace. This file prints three things and none of them is a level:
 *
 *   - STATUS, a validity state (verified / stale / unverified / ...), not an autonomy measurement;
 *   - the expiry date;
 *   - the "projection" - only under that name, the spec's own aggregate, whose composition is one
 *     click away on the full passport this badge links to (`v.projection` in `Passport.tsx`).
 *
 * `tests/test_badge_never_prints_a_bare_level.py` asserts the negative directly, over every
 * status this file can render and over the real per-subject data on disk.
 *
 * `?plain=1` (T-SG-14, `~/taskloop/briefs/SG-00-ruling-1.md` §SG-14): a second rendering that
 * drops the projection row entirely rather than merely labelling it. The growth brief's own
 * argument for this is narrower than ABI-2-3 above - it is not that "projection 60/100" reads as a
 * bare level (the module header already answers that), it is that a badge meant to be seen by a
 * stranger who has never opened a passport, in a context this project does not control (a cold
 * outreach email, a third party's own marketing page), is the single worst place for ANY number
 * next to the word Provek, labelled or not, because that reader has no passport page open beside
 * it to learn what the number is a fraction OF. STATUS and the expiry date survive in `?plain=1`
 * because a date a reader can check against today's is not a rating - it is the same fact the
 * healthy badge already states in `dateLine`, just standing without the projection row beside it.
 * `healthySvg` never reads `projection` at all when `plain` is true, so this is not a rendering
 * choice sitting on top of a value still being computed - see `onRequestGet` below, which skips
 * the read outright.
 */
import { effectiveStatus } from "../_lib/status.js";
import { LIGHT, STATUS_COLOR_LIGHT } from "../_lib/palette.js";

const SLUG = /^[A-Za-z0-9_-]+$/;
const SVG_SUFFIX = /\.svg$/i;

function escapeXml(s) {
  return String(s).replace(/[<>&"]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;" }[c]));
}

const W = 280;
const H = 60;

function frame(rows, title) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${escapeXml(title)}">
  <title>${escapeXml(title)}</title>
  <rect x="0.5" y="0.5" width="${W - 1}" height="${H - 1}" rx="2" fill="${LIGHT.paper}" stroke="${LIGHT.line}"/>
  ${rows.join("\n  ")}
</svg>
`;
}

const MONO = "'IBM Plex Mono',ui-monospace,SFMono-Regular,monospace";
const SANS = "'IBM Plex Sans',ui-sans-serif,system-ui,sans-serif";

/** The healthy badge: status, expiry, and - unless `plain` (T-SG-14, `?plain=1` above) - the
 *  projection under its own name. See the module header for why none of these may ever be a bare
 *  ladder level, and for why `plain` drops the row rather than merely keeping it labelled. */
function healthySvg({ status, validUntil, projection, plain = false }) {
  const color = STATUS_COLOR_LIGHT[status] ?? LIGHT.unknown;
  const dateLine = `valid until ${validUntil.slice(0, 10)}`;
  if (plain) {
    return frame(
      [
        `<text x="10" y="24" font-family="${MONO}" font-size="12" font-weight="600" letter-spacing="0.04em" fill="${LIGHT.ink}">PROVEK</text>`,
        `<text x="${W - 10}" y="24" text-anchor="end" font-family="${MONO}" font-size="12" font-weight="600" letter-spacing="0.04em" fill="${color}">${escapeXml(status.toUpperCase())}</text>`,
        `<text x="10" y="42" font-family="${SANS}" font-size="11" fill="${LIGHT.ink2}">${escapeXml(dateLine)}</text>`,
      ],
      `Provek verification: ${status}, ${dateLine}`,
    );
  }
  // NEVER A BARE NUMBER STANDING FOR THE SUBJECT. "projection" is part of the string on both
  // branches, so the label travels with the value wherever this text is read, screen reader
  // included - there is no rendering path here where the number appears without its name.
  const projLine = projection === null ? "projection: not measured" : `projection ${projection}/100`;
  return frame(
    [
      `<text x="10" y="21" font-family="${MONO}" font-size="12" font-weight="600" letter-spacing="0.04em" fill="${LIGHT.ink}">PROVEK</text>`,
      `<text x="${W - 10}" y="21" text-anchor="end" font-family="${MONO}" font-size="12" font-weight="600" letter-spacing="0.04em" fill="${color}">${escapeXml(status.toUpperCase())}</text>`,
      `<text x="10" y="38" font-family="${SANS}" font-size="11" fill="${LIGHT.ink2}">${escapeXml(dateLine)}</text>`,
      `<text x="10" y="53" font-family="${SANS}" font-size="11" fill="${LIGHT.ink2}">${escapeXml(projLine)}</text>`,
    ],
    `Provek verification: ${status}, ${dateLine}, ${projLine}`,
  );
}

/** The one state an `<img>` tag can still show something for: no slug at all, or one this site
 *  never issued a passport for. Answered 200 rather than 404 - shields.io's convention, kept for
 *  the same reason it holds there: a broken-image icon tells a visitor nothing, and a badge that
 *  names its own failure at least says which one. */
function unknownSvg(reason) {
  return frame(
    [
      `<text x="10" y="24" font-family="${MONO}" font-size="12" font-weight="600" letter-spacing="0.04em" fill="${LIGHT.ink}">PROVEK</text>`,
      `<text x="10" y="42" font-family="${SANS}" font-size="11" fill="${LIGHT.ink3}">${escapeXml(reason)}</text>`,
    ],
    `Provek: ${reason}`,
  );
}

const CACHE = "public, max-age=300, s-maxage=300";
// Five minutes - short enough that a passport's lapse into `stale` (a pure date comparison, so it
// needs no fresh evidence to be correct) is never left showing its old word for long, and long
// enough that an embed on a busy page does not put a fresh render on every load.

function svgResponse(body, status = 200) {
  return new Response(body, {
    status,
    headers: { "content-type": "image/svg+xml; charset=utf-8", "cache-control": CACHE },
  });
}

export async function onRequestGet({ request, params, env }) {
  const raw = params.id;
  if (typeof raw !== "string" || !SVG_SUFFIX.test(raw))
    return new Response("Expected /badge/<slug>.svg", { status: 400 });
  const slug = raw.slice(0, -4);
  if (!SLUG.test(slug)) return svgResponse(unknownSvg("not a subject identifier"));

  // T-SG-14: read before the fetch, off the request's own URL, never off the fixture - a fixture
  // that happened to carry a `plain` key could otherwise steer which branch renders.
  const plain = new URL(request.url).searchParams.get("plain") === "1";

  let res;
  try {
    const assetUrl = new URL(request.url);
    assetUrl.pathname = `/data/passports/${slug}.json`;
    assetUrl.search = "";
    res = await env.ASSETS.fetch(assetUrl.toString());
  } catch {
    return svgResponse(unknownSvg("could not be read"), 200);
  }
  if (!res.ok) return svgResponse(unknownSvg("no such passport"));

  let data;
  try {
    data = await res.json();
  } catch {
    return svgResponse(unknownSvg("could not be read"));
  }
  const p = data && data.passport;
  if (!p) return svgResponse(unknownSvg("no such passport"));

  const status = effectiveStatus(p.status, p.valid_until, new Date());
  // Not read at all in the `plain` branch (T-SG-14) - the badge is "without a number" in the
  // source, not only in the markup: the ternary below is `null` outright rather than a value the
  // `plain` branch of `healthySvg` merely declines to print.
  const projection = plain
    ? null
    : p.verified && typeof p.verified.projection === "number" ? p.verified.projection : null;
  return svgResponse(healthySvg({ status, validUntil: p.valid_until, projection, plain }));
}

export async function onRequestPost() {
  return new Response("This endpoint answers a reading, not a submission.", { status: 405 });
}
