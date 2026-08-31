/**
 * Runs `web/functions/badge/[id].js` under Node with a stubbed `env.ASSETS`, the way
 * `tests/intake_probe.mjs` runs `apply.js` with a stubbed KV binding. A source scan can prove a
 * `status.toUpperCase()` call is written and can never prove what an actual response body is -
 * which is exactly the property `tests/test_badge_control_stale_not_green.py` and
 * `tests/test_badge_never_prints_a_bare_level.py` need.
 *
 * Emits one JSON object on stdout: { scenario, status, contentType, cacheControl, body, fetched }.
 * `fetched` records whether `env.ASSETS.fetch` was called at all, for the scenarios where it must
 * not be (an unsafe slug must never reach a fetch call).
 */
import { onRequestGet } from "../web/functions/badge/[id].js";

function assets(fixture, { throws = false } = {}) {
  const calls = [];
  return {
    calls,
    binding: {
      fetch: async (url) => {
        calls.push(String(url));
        if (throws) throw new TypeError("fetch failed");
        if (fixture === null) return new Response("not found", { status: 404 });
        return new Response(JSON.stringify(fixture), { status: 200 });
      },
    },
  };
}

const PROVEK = {
  subject_id: "git:whiteknightonhorse/provek",
  passport: {
    subject_id: "git:whiteknightonhorse/provek",
    status: "verified",
    valid_until: "2099-01-01T00:00:00Z",
    verified: { projection: 60 },
  },
};

const LAPSED = {
  ...PROVEK,
  passport: { ...PROVEK.passport, valid_until: "2020-01-01T00:00:00Z" },
};

const NO_PROJECTION = {
  subject_id: "git:whiteknightonhorse/AI-Property-Sales-Platform",
  passport: {
    subject_id: "git:whiteknightonhorse/AI-Property-Sales-Platform",
    status: "unverified",
    valid_until: "2099-01-01T00:00:00Z",
    verified: { projection: null },
  },
};

const SUSPENDED = {
  subject_id: "git:whiteknightonhorse/suspended-example",
  passport: {
    subject_id: "git:whiteknightonhorse/suspended-example",
    status: "suspended",
    valid_until: "2099-01-01T00:00:00Z",
    verified: { projection: null },
  },
};

const CASES = {
  verified_with_projection: { id: "git_whiteknightonhorse_provek.svg", fixture: PROVEK },
  // THE CONTROL THIS TASK ASKED FOR. Stored status is still "verified"; the date has passed. The
  // badge must read STALE, not the stored word.
  verified_lapsed_shows_stale: { id: "git_whiteknightonhorse_provek.svg", fixture: LAPSED },
  unverified_no_projection: { id: "git_x.svg", fixture: NO_PROJECTION },
  suspended: { id: "git_x.svg", fixture: SUSPENDED },
  unknown_slug: { id: "git_no_such_subject.svg", fixture: null },
  // Rejected before any fetch - the same boundary `web/src/slug.js` draws for the browser.
  malformed_id: { id: "not-a-slug!!.svg" },
  missing_svg_extension: { id: "git_whiteknightonhorse_provek" },
  asset_fetch_throws: { id: "git_whiteknightonhorse_provek.svg", fixture: PROVEK, throws: true },
};

const name = process.argv[2];
const chosen = Object.prototype.hasOwnProperty.call(CASES, name) ? CASES[name] : null;
if (!chosen) {
  process.stderr.write(`unknown scenario ${JSON.stringify(name)}\n`);
  process.exit(2);
}

const kv = assets(chosen.fixture ?? null, { throws: !!chosen.throws });
const env = { ASSETS: kv.binding };
const request = new Request(`https://provek.dev/badge/${chosen.id}`);
const response = await onRequestGet({ request, params: { id: chosen.id }, env });
const body = await response.text();

process.stdout.write(JSON.stringify({
  scenario: name,
  status: response.status,
  contentType: response.headers.get("content-type"),
  cacheControl: response.headers.get("cache-control"),
  body,
  fetched: kv.calls.length > 0,
}));
