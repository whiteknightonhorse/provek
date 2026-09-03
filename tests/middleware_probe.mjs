/**
 * The instrument for `tests/test_markdown_negotiation.py`: RUNS `web/functions/_middleware.js`
 * instead of reading it, the same shape and for the same reason as `tests/intake_probe.mjs` - a
 * source scan can see that `next()` is called somewhere in the file and never that it is called on
 * the right request. The property under test is what the function ANSWERS and whether it called
 * through, not what its source contains. Covers both of that file's request-shape fixes - the
 * encoded-fragment redirect and markdown negotiation - since both are proven the same way.
 *
 * Emits one JSON object on stdout: whether `next()` fired, and the response actually returned.
 */
import { onRequest } from "../web/functions/_middleware.js";

/** `env.ASSETS`, stubbed to hold exactly the markdown siblings named in `mdFiles` - everything
 *  else answers 404, which is what the real asset store does for a route with no `.md` sibling. */
function assets(mdFiles) {
  return {
    fetch: async (u) => {
      const path = new URL(u).pathname;
      if (Object.prototype.hasOwnProperty.call(mdFiles, path)) {
        return new Response(mdFiles[path], { status: 200 });
      }
      return new Response("Not found", { status: 404 });
    },
  };
}

/** The rest of the Pages Functions pipeline, stubbed as one sentinel response. In production this
 *  is either `web/functions/api/apply.js` / `badge/[id].js` / `p/[id]/brief.js` for the three paths
 *  that have their own handler, or the prerendered HTML for every page - this probe does not need
 *  to tell those apart, because the property under test is only WHETHER the middleware called
 *  through to whichever of them applies, not which one it was. */
function nextStub() {
  const calls = { count: 0 };
  const fn = async () => {
    calls.count += 1;
    return new Response("ORDINARY-PIPELINE-RESPONSE",
      { status: 200, headers: { "content-type": "text/html; charset=utf-8" } });
  };
  return { calls, fn };
}

const MD_FILES = { "/registry/index.md": "# Provek registry\n\nfixture body\n" };

const CASES = {
  // THE CONTROL. No Accept header at all - the ordinary browser request. If this scenario ever
  // returns markdown, negotiation has become a substitution rather than an addition.
  no_header_gets_the_old_html: { path: "/registry/", headers: {} },
  html_accept_gets_the_old_html: { path: "/registry/", headers: { Accept: "text/html" } },
  markdown_accept_on_a_page_with_a_sibling: { path: "/registry/", headers: { Accept: "text/markdown" } },
  markdown_accept_wins_when_both_are_offered:
    { path: "/registry/", headers: { Accept: "text/html,text/markdown;q=0.9" } },
  // A page that plainly exists but has no generated sibling (every prose page, until one is
  // built for it) - must fall through to the ordinary HTML, not answer 404.
  markdown_accept_on_a_page_with_no_sibling: { path: "/method/", headers: { Accept: "text/markdown" } },
  // The three existing Functions, none of which end in "/" - proven untouched EVEN WHEN a client
  // sends the markdown header, which is the case that would expose a middleware that intercepted
  // by header alone instead of by route shape.
  api_apply_untouched_even_with_markdown_accept:
    { path: "/api/apply", method: "POST", headers: { Accept: "text/markdown" } },
  badge_untouched_even_with_markdown_accept:
    { path: "/badge/git_whiteknightonhorse_APIbase.svg", headers: { Accept: "text/markdown" } },
  brief_untouched_even_with_markdown_accept:
    { path: "/p/git_whiteknightonhorse_APIbase/brief", headers: { Accept: "text/markdown" } },
  // Ordinary static data, same shape as the three above: no trailing slash, never intercepted.
  registry_json_untouched_even_with_markdown_accept:
    { path: "/data/registry.json", headers: { Accept: "text/markdown" } },

  // An in-app browser that percent-encoded the page's own `#` before requesting it (reproduced
  // against provek.dev 2026-09-03) - must land on the page the fragment names, not 404.
  encoded_hash_redirects_to_the_clean_page:
    { path: "/method/%23the-order-link", headers: {} },
  // The same shape with a trailing slash already on the encoded segment - a browser that also
  // appended one, which must not produce a double slash or a different target.
  encoded_hash_with_a_trailing_slash_redirects_the_same_way:
    { path: "/method/%23the-order-link/", headers: {} },
  // No `/` between the route and the encoded hash - not this site's own link shape, but a
  // malformed one must still land on a real page rather than 404.
  encoded_hash_without_a_leading_slash_still_lands_on_a_page:
    { path: "/apply%23whatever", headers: {} },
  // The encoded hash on the site root itself - the one case where "everything before it" is empty,
  // proven separately from the general case so an off-by-one here cannot hide behind it.
  encoded_hash_on_the_root_redirects_to_the_root:
    { path: "/%23whatever", headers: {} },
  // THE CONTROL for the redirect: an ordinary request for the same page, no encoded hash anywhere
  // in it, must never be redirected.
  no_encoded_hash_is_never_redirected:
    { path: "/method/", headers: {} },
  // The method guard applies to the redirect too, not only to markdown negotiation - a POST must
  // reach its endpoint even if its path happens to contain an encoded hash.
  post_with_an_encoded_hash_is_not_redirected:
    { path: "/api/apply%23x", method: "POST", headers: {} },
};

const name = process.argv[2];
const chosen = Object.prototype.hasOwnProperty.call(CASES, name) ? CASES[name] : null;
if (!chosen) {
  process.stderr.write(`unknown scenario ${JSON.stringify(name)}\n`);
  process.exit(2);
}

const request = new Request(`https://provek.dev${chosen.path}`, {
  method: chosen.method || "GET",
  headers: chosen.headers,
});
const { calls, fn } = nextStub();
const response = await onRequest({ request, env: { ASSETS: assets(MD_FILES) }, next: fn });
const result = {
  scenario: name,
  next_called: calls.count,
  status: response.status,
  content_type: response.headers.get("content-type"),
  location: response.headers.get("location"),
  body: await response.text(),
};
process.stdout.write(JSON.stringify(result));
