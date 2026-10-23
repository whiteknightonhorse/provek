/**
 * The instrument for `tests/test_apply_status_names_its_states.py` (T-IN-03, D-69): it RUNS
 * `GET /api/apply/<id>` against a Map-backed KV instead of reading the source, by the precedent
 * `tests/intake_probe.mjs` set. The record is created by the REAL `onRequestPost`, so the key
 * layout and the `request-id:` index under test are the ones the endpoint writes, then the fields
 * the intake run adds (`provek_*`, T-IN-01) are patched onto it the way the run's `put_record` does.
 *
 * Node with a stub is not `workerd`; the deployed route is not measured here.
 * Emits one JSON object on stdout; an unknown scenario exits 2.
 */
import { onRequestPost } from "../web/functions/api/apply.js";
import { onRequestGet } from "../web/functions/api/apply/[id].js";

const SUBMISSION = {
  repo: "https://github.com/example-org/example-repo",
  contact: "applicant@example.com",
  mandate: "passive",
  consent: true,
  consent_version: "updates-1.1.0",
};

const PATCHES = {
  received: {},
  deferred: {
    provek_deferred_until: "2026-10-23T12:00:00Z",
    provek_defer_reason: "github_rate_limited_until_2026-10-23T12:00:00Z",
    provek_attempts: 2,
  },
  refused: { provek_outcome: "refused", provek_reason: "repository_did_not_answer_http_404" },
  published: { provek_outcome: "published", provek_projection: 0.4, provek_status: "unverified" },
  withdrawn: { provek_outcome: "withdrawn_by_operator" },
  unknown_outcome: { provek_outcome: "quarantined" },
  // An intake field with neither an outcome nor a deferral: not "received", and not a known state.
  half_written: { provek_attempts: 1 },
};

const name = process.argv[2];

function store(refuseIndex) {
  const m = new Map();
  return {
    m,
    binding: {
      put: async (k, v) => {
        if (refuseIndex && k.startsWith("request-id:")) throw new Error("KV PUT failed: 429");
        m.set(k, v);
      },
      get: async (k) => (m.has(k) ? m.get(k) : null),
    },
  };
}

async function get(env, id) {
  const r = await onRequestGet({
    request: new Request(`https://provek.dev/api/apply/${id}`),
    env,
    params: { id },
  });
  const raw = await r.text();
  return { status: r.status, cache: r.headers.get("cache-control"), raw, body: JSON.parse(raw) };
}

const kv = store(name === "index_write_refused");
const env = { INTAKE: kv.binding };
const out = { scenario: name };

if (name === "no_such_request") {
  out.get = await get(env, "123e4567-e89b-42d3-a456-426614174000");
} else if (name === "malformed_id") {
  out.get = await get(env, "../../etc/passwd");
} else if (name in PATCHES || name === "index_write_refused") {
  const posted = await onRequestPost({
    request: new Request("https://provek.dev/api/apply", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify(SUBMISSION),
    }),
    env,
  });
  out.post = { status: posted.status, body: await posted.json() };
  const key = [...kv.m.keys()].find((k) => k.startsWith("request:"));
  if (name in PATCHES) kv.m.set(key, JSON.stringify({ ...JSON.parse(kv.m.get(key)), ...PATCHES[name] }));
  out.index = kv.m.get(`request-id:${out.post.body.id}`) ?? null;
  out.key = key;
  out.get = await get(env, out.post.body.id);
} else if (name === "dangling_index") {
  kv.m.set("request-id:123e4567-e89b-42d3-a456-426614174000", "request:gone");
  out.get = await get(env, "123e4567-e89b-42d3-a456-426614174000");
} else {
  process.stderr.write(`unknown scenario ${JSON.stringify(name)}\n`);
  process.exit(2);
}
process.stdout.write(JSON.stringify(out));
