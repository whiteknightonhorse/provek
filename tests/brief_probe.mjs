/**
 * Runs `web/functions/p/[id]/brief.js` under Node with a stubbed `env.ASSETS`, the same
 * instrument shape as `tests/badge_probe.mjs` and `tests/intake_probe.mjs`.
 *
 * Emits { scenario, status, contentType, cacheControl, body } as JSON on stdout.
 */
import { onRequestGet } from "../web/functions/p/[id]/brief.js";

function assets(fixture) {
  return {
    fetch: async () => {
      if (fixture === null) return new Response("not found", { status: 404 });
      return new Response(JSON.stringify(fixture), { status: 200 });
    },
  };
}

const THREE_OPS_PASSPORT = {
  subject_id: "git:whiteknightonhorse/provek",
  passport: {
    subject_id: "git:whiteknightonhorse/provek",
    status: "verified",
    valid_until: "2099-01-01T00:00:00Z",
    verifier_affiliation: "same_owner",
    verified: {
      projection: 60,
      operations: [
        { operation: "development_initiation", level: "L3", measured: true, confidence: "inferred", limiters_applied: [] },
        { operation: "deployment", level: "check_did_not_run", measured: false, confidence: null, limiters_applied: [] },
        { operation: "treasury_control", level: "check_did_not_run", measured: false, confidence: null, limiters_applied: [] },
      ],
    },
  },
};

const LAPSED = {
  ...THREE_OPS_PASSPORT,
  passport: { ...THREE_OPS_PASSPORT.passport, valid_until: "2020-01-01T00:00:00Z" },
};

const INDEPENDENT_NO_PROJECTION = {
  subject_id: "git:whiteknightonhorse/independent-example",
  passport: {
    subject_id: "git:whiteknightonhorse/independent-example",
    status: "unverified",
    valid_until: "2099-01-01T00:00:00Z",
    verifier_affiliation: "independent",
    verified: {
      projection: null,
      operations: [
        { operation: "development_initiation", level: "unreadable", measured: false, confidence: null, limiters_applied: [] },
        { operation: "deployment", level: "check_did_not_run", measured: false, confidence: null, limiters_applied: [] },
        { operation: "treasury_control", level: "check_did_not_run", measured: false, confidence: null, limiters_applied: [] },
      ],
    },
  },
};

const CASES = {
  verified_three_ops: { id: "git_whiteknightonhorse_provek", fixture: THREE_OPS_PASSPORT },
  lapsed_shows_stale: { id: "git_whiteknightonhorse_provek", fixture: LAPSED },
  independent_no_projection: { id: "git_x", fixture: INDEPENDENT_NO_PROJECTION },
  unknown_slug: { id: "git_no_such_subject", fixture: null },
  malformed_id: { id: "not a slug" },
};

const name = process.argv[2];
const chosen = Object.prototype.hasOwnProperty.call(CASES, name) ? CASES[name] : null;
if (!chosen) {
  process.stderr.write(`unknown scenario ${JSON.stringify(name)}\n`);
  process.exit(2);
}

const env = { ASSETS: assets(chosen.fixture ?? null) };
const request = new Request(`https://provek.dev/p/${encodeURIComponent(chosen.id)}/brief`);
const response = await onRequestGet({ request, params: { id: chosen.id }, env });
const body = await response.text();

process.stdout.write(JSON.stringify({
  scenario: name,
  status: response.status,
  contentType: response.headers.get("content-type"),
  cacheControl: response.headers.get("cache-control"),
  body,
}));
