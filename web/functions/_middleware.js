/**
 * Markdown negotiation - the ONLY thing this file does.
 *
 * WHY IT EXISTS. Fable's ruling on the axis a public checker scored this site 0/100 on: "Provek
 * sells machine-readability and shows 0/100 on Content on its own site." The registry and every
 * passport are already served as JSON (`/data/*.json`) and as prose HTML (the pages themselves);
 * what was missing is the same content in the format a checker on that axis asks for at the SAME
 * address a browser reads - `GET /registry/` with `Accept: text/markdown` answering markdown
 * instead of the HTML `Accept: text/html` gets. This file is the negotiator, nothing else: the
 * markdown itself is generated at build time from registry+passport data by `web/markdown.mjs` and
 * written beside each page's `index.html` as `index.md` (`web/prerender.mjs`), never by hand -
 * `web/discovery.mjs`'s own header names the reason a hand-maintained copy would drift.
 *
 * WHY `context.next()` AND NOT `env.ASSETS.fetch(request)` FOR THE "OTHERWISE" BRANCH, THOUGH
 * THAT WAS THE LITERAL SHAPE NAMED FOR IT. A Cloudflare Pages Function router composes, for each
 * request, every `_middleware.js` on the path down to the matched handler - which for `/api/apply`,
 * `/badge/<slug>.svg` and `/p/<slug>/brief` is one of `web/functions/api/apply.js`,
 * `badge/[id].js`, `p/[id]/brief.js`, and for every other path is the static asset. `context.next()`
 * continues to WHICHEVER of those is next in that chain. `env.ASSETS.fetch(request)` instead reaches
 * straight into the static-asset bucket and answers from there regardless of what would otherwise
 * have matched - so a root middleware that used it for every non-markdown request would silently
 * turn `/api/apply` and the badge into "no such static file" for every ordinary browser request,
 * which is exactly the degradation the brief asked this file to rule out. `env.ASSETS.fetch` is
 * still the right call for the one thing this file actually needs to fetch by a DIFFERENT path than
 * the request's own - the generated `.md` sibling - the same use `badge/[id].js` already makes of
 * it to read a passport by a rewritten URL rather than the request's own.
 *
 * WHAT MAKES THE OTHER THREE FUNCTIONS SAFE BY CONSTRUCTION, NOT BY BEING NAMED HERE.
 * `markdownSiblingPath` only ever answers for a request whose path ends in `/` (a page route, in
 * this project's own convention - see every `write(route, ...)` call in `web/prerender.mjs`).
 * `/api/apply`, `/badge/<slug>.svg` and `/p/<slug>/brief` end in a literal segment, never a slash,
 * so this file never even asks whether a markdown sibling exists for them - it falls through on the
 * shape of the path, not on a list of exceptions that could go stale as routes are added.
 */

const MARKDOWN = /\btext\/markdown\b/;

/** The generated sibling for a page route, or `null` for anything that is not one. Mirrors
 *  `web/prerender.mjs:write()`'s own rule for where an `index.html` lands - the markdown sits
 *  beside it as `index.md` in the same directory, so nothing here needs to know the route list. */
function markdownSiblingPath(pathname) {
  if (pathname === "/") return "/index.md";
  if (!pathname.endsWith("/")) return null;
  return `${pathname}index.md`;
}

export async function onRequest(context) {
  const { request, env, next } = context;

  // Negotiation is a GET/HEAD concern. A POST to /api/apply carries no Accept header worth reading
  // for this purpose and must reach the endpoint regardless - `next()` either way, but stated up
  // front rather than left to fall out of markdownSiblingPath by accident.
  if (request.method !== "GET" && request.method !== "HEAD") return next();

  // THE CONTROL. No `Accept: text/markdown` - including no Accept header at all, which is what an
  // ordinary browser sends - and this file does nothing whatsoever. Every branch below this line
  // runs only for a request that asked for markdown by name.
  const accept = request.headers.get("Accept") || "";
  if (!MARKDOWN.test(accept)) return next();

  const pathname = new URL(request.url).pathname;
  const mdPath = markdownSiblingPath(pathname);
  if (!mdPath) return next();

  const mdUrl = new URL(request.url);
  mdUrl.pathname = mdPath;
  mdUrl.search = "";

  let asset;
  try {
    asset = await env.ASSETS.fetch(mdUrl.toString());
  } catch {
    // The asset store itself failed to answer - not "no such file". Falling through to the
    // ordinary HTML is the honest answer: this file has nothing else to offer for this request.
    return next();
  }
  // Since 2026-09-01 every page route HAS a sibling: `web/prerender.mjs` writes the two
  // purpose-built ones and derives the rest from the rendered page, and refuses the build if any
  // route is left without. This branch is therefore not the ordinary path any more - it is the
  // honest answer for a request whose sibling is genuinely absent (an asset published outside that
  // sweep, or a partial deploy). HTML stays the default for it: a 404 shown to a markdown-reading
  // client would be a false "this page does not exist" about a page that plainly does.
  //
  // The previous version of this comment listed `/`, `/method/`, `/apply/`, `/phase-2/` and the
  // notes as prose pages with no sibling. That was true when written and became false the moment
  // the sweep landed - a comment naming a state rather than a rule is a claim that expires without
  // anyone noticing, which is why it is corrected in the same commit as the code that dated it.
  if (!asset.ok) return next();

  return new Response(asset.body, {
    status: 200,
    headers: {
      "content-type": "text/markdown; charset=utf-8",
      // Same freshness rule as `/data/*` in `public/_headers`: this is a rendering of registry and
      // passport data, which re-measures daily, and a long cache would serve a superseded verdict.
      "cache-control": "public, max-age=0, must-revalidate",
    },
  });
}
