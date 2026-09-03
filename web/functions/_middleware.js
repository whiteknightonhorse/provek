/**
 * Two request-shape fixes that apply to every route, ahead of the ordinary pipeline: an encoded
 * URL fragment landed on its page instead of a 404, and markdown negotiation.
 *
 * ENCODED-FRAGMENT REDIRECT. A `#fragment` is a browser-only construct - it is never sent in an
 * HTTP request, so a link like `/method/#the-order-link` reaches this server as a plain
 * `GET /method/`. Some in-app browsers (messenger webviews, reproduced 2026-09-03 against a link
 * opened from one) percent-encode the `#` themselves before requesting the page, so the SAME link
 * instead arrives as `GET /method/%23the-order-link` - a literal, non-existent path segment, which
 * 404s where the real fragment 200s. The reader did nothing wrong; the app that opened the link
 * did. This is the ONE place every request passes through regardless of route, so the fix lives
 * here rather than on any one page: strip everything from the first `%23` onward and send the
 * reader to the page it names, rather than a dead end that plainly exists. Covers every page with
 * an anchor, not just `/method/` - checked 2026-09-03, this is the only site defect of its shape.
 *
 * MARKDOWN NEGOTIATION.
 *
 * WHY IT EXISTS. Fable's ruling on the axis a public checker scored this site 0/100 on: "Provek
 * sells machine-readability and shows 0/100 on Content on its own site." The registry and every
 * passport are already served as JSON (`/data/*.json`) and as prose HTML (the pages themselves);
 * what was missing is the same content in the format a checker on that axis asks for at the SAME
 * address a browser reads - `GET /registry/` with `Accept: text/markdown` answering markdown
 * instead of the HTML `Accept: text/html` gets. The markdown itself is generated at build time
 * from registry+passport data by `web/markdown.mjs` and written beside each page's `index.html` as
 * `index.md` (`web/prerender.mjs`), never by hand - `web/discovery.mjs`'s own header names the
 * reason a hand-maintained copy would drift.
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
const ENCODED_HASH = /%23/i;

/** The generated sibling for a page route, or `null` for anything that is not one. Mirrors
 *  `web/prerender.mjs:write()`'s own rule for where an `index.html` lands - the markdown sits
 *  beside it as `index.md` in the same directory, so nothing here needs to know the route list. */
function markdownSiblingPath(pathname) {
  if (pathname === "/") return "/index.md";
  if (!pathname.endsWith("/")) return null;
  return `${pathname}index.md`;
}

/** Everything up to a percent-encoded `#`, normalised back to this site's own route shape (a
 *  trailing slash - see `norm()` in `web/src/App.tsx`). `null` when the path carries no encoded
 *  hash at all, so the caller can tell "nothing to do" from "the clean page is the site root". */
function stripEncodedFragment(pathname) {
  const i = pathname.search(ENCODED_HASH);
  if (i === -1) return null;
  const clean = pathname.slice(0, i);
  if (clean === "") return "/";
  return clean.endsWith("/") ? clean : `${clean}/`;
}

export async function onRequest(context) {
  const { request, env, next } = context;

  // Both fixes below are GET/HEAD concerns. A POST to /api/apply carries no Accept header worth
  // reading and no fragment worth stripping, and must reach the endpoint regardless - `next()`
  // either way, but stated up front rather than left to fall out of either check by accident.
  if (request.method !== "GET" && request.method !== "HEAD") return next();

  const url = new URL(request.url);

  // THE CONTROL for the redirect: reproduced against provek.dev 2026-09-03, `/method/#the-order-
  // link` (a real fragment, never sent here) answers 200 while `/method/%23the-order-link` (the
  // same link, percent-encoded by the client that opened it) 404s. Land on the named page instead.
  const clean = stripEncodedFragment(url.pathname);
  if (clean !== null) {
    url.pathname = clean;
    url.search = "";
    url.hash = "";
    return Response.redirect(url.toString(), 301);
  }

  // THE CONTROL for negotiation. No `Accept: text/markdown` - including no Accept header at all,
  // which is what an ordinary browser sends - and this file does nothing whatsoever from here on.
  // Every branch below this line runs only for a request that asked for markdown by name.
  const accept = request.headers.get("Accept") || "";
  if (!MARKDOWN.test(accept)) return next();

  const pathname = url.pathname;
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
