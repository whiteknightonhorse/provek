/**
 * The instrument for `tests/test_markdown_negotiation.py`: RUNS `web/functions/_middleware.js`
 * instead of reading it, the same shape and for the same reason as `tests/intake_probe.mjs` - a
 * source scan can see that `next()` is called somewhere in the file and never that it is called on
 * the right request. The property under test is what the function ANSWERS and whether it called
 * through, not what its source contains.
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
  body: await response.text(),
};
process.stdout.write(JSON.stringify(result));
