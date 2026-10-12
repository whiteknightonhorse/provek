/**
 * The instrument for `tests/test_witness_relay.py`: it RUNS the relay (`web/functions/_lib/
 * witnessRelay.js`, behind `web/functions/api/witness-submit.js`) under Node with a MOCKED genlayer-js
 * client and a Map-backed KV. No network is touched and no real key exists here: the key is a fake
 * constant, and one scenario derives an address from the well-known test key 0x00..01 with the REAL
 * `createAccount` (a pure local computation, no request).
 *
 * What it cannot see: the Workers runtime and the Bradbury RPC. Both are the dispatcher's live E2E.
 *
 * Every scenario prints one JSON object `{ scenario, result }`. Anything that reaches a caller -
 * response bodies, headers, console output - is captured so the Python side can assert that the fake
 * key is nowhere in it.
 */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import * as relay from "../web/functions/_lib/witnessRelay.js";
import * as route from "../web/functions/api/witness-submit.js";

const FAKE_KEY = "0x" + "ab12".repeat(16);
const NOW = new Date("2026-10-12T10:15:30Z");
const HASH = "0x" + "aB09".repeat(16); // mixed case on purpose: it must come back exactly as given
const CONTRACT = "0x499eD0E23CbCdC8Fc7735709dca32bCb01638fd6";

const logs = [];
for (const m of ["log", "info", "warn", "error", "debug"]) console[m] = (...a) => logs.push(a.map(String).join(" "));

function kvStub({ unreadable = false } = {}) {
  const m = new Map();
  return {
    m,
    get: async (k) => { if (unreadable) throw new Error("KV down"); return m.has(k) ? m.get(k) : null; },
    put: async (k, v, o) => { m.set(k, v); m.ttl = { ...(m.ttl || {}), [k]: o && o.expirationTtl }; },
  };
}

function mockDeps({ write, hash = HASH } = {}) {
  const calls = { createAccount: [], createClient: [], writeContract: [] };
  const deps = {
    now: () => NOW,
    loadGenlayer: async () => ({
      createAccount: (k) => { calls.createAccount.push(k); return { address: "0x" + "12".repeat(20) }; },
      createClient: (cfg) => {
        calls.createClient.push({ chain: cfg.chain, account: cfg.account });
        return { writeContract: async (a) => { calls.writeContract.push(a); if (write) return write(a); return hash; } };
      },
      testnetBradbury: { id: 4221, name: "mock-bradbury" },
    }),
  };
  return { deps, calls };
}

const GOOD = { subject_id: "git:whiteknightonhorse/provek", criterion: "url_reachable", evidence_url: "https://provek.dev/", expected: "" };
const SHA = "0123456789abcdef".repeat(4);

function req(body, { ip = "203.0.113.7", origin, raw } = {}) {
  const headers = { "content-type": "application/json", "cf-connecting-ip": ip };
  if (origin) headers.origin = origin;
  return new Request("https://provek.dev/api/witness-submit", { method: "POST", headers, body: raw ?? JSON.stringify(body) });
}

async function snap(res) {
  const text = await res.text();
  let body = null;
  try { body = JSON.parse(text); } catch { /* keep text */ }
  return { status: res.status, headers: Object.fromEntries(res.headers), text, body };
}

const post = async (env, deps, body, opts) => snap(await relay.handlePost({ request: req(body, opts), env }, deps));
const envOk = (kv) => ({ GL_OPERATOR_KEY: FAKE_KEY, WITNESS_RL: kv });
const out = (result, extra = {}) => ({ result, logs, ...extra });

const CASES = {
  health_enabled: async () => {
    const { deps, calls } = mockDeps();
    const r = await snap(await relay.handleGet({ env: envOk(kvStub()) }, deps));
    return out(r, { calls });
  },
  health_no_secret: async () => {
    const { deps, calls } = mockDeps();
    const r = await snap(await relay.handleGet({ env: { WITNESS_RL: kvStub() } }, deps));
    return out(r, { calls });
  },
  health_bad_key: async () => {
    const { deps, calls } = mockDeps();
    const r = await snap(await relay.handleGet({ env: { GL_OPERATOR_KEY: "not-a-key", WITNESS_RL: kvStub() } }, deps));
    return out(r, { calls });
  },
  health_no_kv: async () => {
    const { deps } = mockDeps();
    return out(await snap(await relay.handleGet({ env: { GL_OPERATOR_KEY: FAKE_KEY } }, deps)));
  },
  route_get_uses_the_same_handler: async () => {
    const res = await route.onRequestGet({ env: { WITNESS_RL: kvStub() } });
    return out(await snap(res));
  },
  route_other_method: async () => out(await snap(await route.onRequest())),
  post_ok: async () => {
    const kv = kvStub();
    const { deps, calls } = mockDeps();
    const r = await post(envOk(kv), deps, GOOD);
    return out(r, { calls: { ...calls, writeContract: calls.writeContract.map((a) => ({ ...a, value: String(a.value) })) }, kv: [...kv.m.entries()] });
  },
  post_artifact_hash_uppercase_is_normalised: async () => {
    const { deps, calls } = mockDeps();
    const r = await post(envOk(kvStub()), deps, { ...GOOD, criterion: "artifact_hash", expected: `  ${SHA.toUpperCase()} ` });
    return out(r, { args: calls.writeContract.map((a) => a.args) });
  },
  post_missing_secret: async () => {
    const { deps, calls } = mockDeps();
    const r = await post({ WITNESS_RL: kvStub() }, deps, GOOD);
    return out(r, { calls });
  },
  post_bad_key: async () => {
    const { deps, calls } = mockDeps();
    const r = await post({ GL_OPERATOR_KEY: "zz", WITNESS_RL: kvStub() }, deps, GOOD);
    return out(r, { calls });
  },
  post_no_kv: async () => {
    const { deps, calls } = mockDeps();
    return out(await post({ GL_OPERATOR_KEY: FAKE_KEY }, deps, GOOD), { calls });
  },
  validation_matrix: async () => {
    const rows = {};
    const v = (name, patch) => { rows[name] = { ...GOOD, ...patch }; };
    v("good_url_reachable", {});
    v("good_artifact_hash", { criterion: "artifact_hash", expected: SHA });
    v("good_upper_scheme_and_host", { evidence_url: "HTTP://Example.COM/x?y=1#z" });
    v("good_port_and_ipv6", { evidence_url: "https://[2001:db8::1]:8443/x" });
    v("good_subject_256", { subject_id: "s".repeat(256) });
    v("subject_empty", { subject_id: "" });
    v("subject_257", { subject_id: "s".repeat(257) });
    v("subject_not_string", { subject_id: 7 });
    v("subject_missing", { subject_id: undefined });
    v("criterion_unsupported", { criterion: "page_title" });
    v("criterion_missing", { criterion: undefined });
    v("url_empty", { evidence_url: "" });
    v("url_missing", { evidence_url: undefined });
    v("url_2049", { evidence_url: "https://a.example/" + "x".repeat(2049 - 18) });
    v("url_2048_ok", { evidence_url: "https://a.example/" + "x".repeat(2048 - 18) });
    v("url_space", { evidence_url: "https://a.example/a b" });
    v("url_newline", { evidence_url: "https://a.example/\n" });
    v("url_del", { evidence_url: "https://a.example/\u007f" });
    v("url_ftp", { evidence_url: "ftp://a.example/" });
    v("url_javascript", { evidence_url: "javascript:alert(1)" });
    v("url_no_scheme", { evidence_url: "a.example/x" });
    v("url_no_host_triple_slash", { evidence_url: "https:///x" });
    v("url_no_slashes", { evidence_url: "https:a.example" });
    v("url_userinfo", { evidence_url: "https://user:pw@a.example/" });
    v("url_at_without_host", { evidence_url: "https://user@/x" });
    v("artifact_missing_expected", { criterion: "artifact_hash", expected: undefined });
    v("artifact_63_hex", { criterion: "artifact_hash", expected: SHA.slice(1) });
    v("artifact_non_hex", { criterion: "artifact_hash", expected: "g".repeat(64) });
    v("reachable_with_expected", { expected: SHA });
    v("expected_not_string", { expected: 5 });
    const res = {};
    for (const [name, body] of Object.entries(rows)) {
      const kv = kvStub();
      const { deps, calls } = mockDeps();
      const r = await post(envOk(kv), deps, body);
      res[name] = { status: r.status, field: r.body && r.body.field, reason: r.body && r.body.reason, error: r.body && r.body.error, sent: calls.writeContract.length, kv_writes: kv.m.size };
    }
    return out(res);
  },
  url_matrix: async () => {
    const cases = JSON.parse(readFileSync(new URL("./fixtures/witness_relay_url_cases.json", import.meta.url)));
    return out(Object.fromEntries(Object.entries(cases).map(([k, u]) => [k, relay.urlProblem(u)])));
  },
  validation_non_object_and_bad_json: async () => {
    const res = {};
    const env = envOk(kvStub());
    const { deps } = mockDeps();
    res.array = (await post(env, deps, [1])).status;
    res.null = (await post(env, deps, null)).status;
    res.bad_json = (await snap(await relay.handlePost({ request: req(null, { raw: "{nope" }), env }, deps))).status;
    res.too_large = (await snap(await relay.handlePost({ request: req(null, { raw: JSON.stringify({ subject_id: "x".repeat(9000) }) }), env }, deps))).status;
    return out(res);
  },
  cross_origin: async () => {
    const { deps, calls } = mockDeps();
    const r = await post(envOk(kvStub()), deps, GOOD, { origin: "https://evil.example" });
    const same = await post(envOk(kvStub()), deps, GOOD, { origin: "https://provek.dev" });
    return out({ foreign: r.status, same: same.status }, { sent: calls.writeContract.length });
  },
  rate_per_ip: async () => {
    const kv = kvStub();
    const { deps, calls } = mockDeps();
    const env = envOk(kv);
    const statuses = [];
    let fourth;
    for (let i = 0; i < 4; i++) {
      const r = await post(env, deps, GOOD, { ip: "203.0.113.7" });
      statuses.push(r.status);
      fourth = r;
    }
    const other = await post(env, deps, GOOD, { ip: "198.51.100.9" });
    return out({ statuses, fourth, other: other.status }, { sent: calls.writeContract.length, kv: [...kv.m.entries()], ttl: kv.m.ttl });
  },
  rate_global_day: async () => {
    const kv = kvStub();
    kv.m.set("rl:day:20261012", "50");
    const { deps, calls } = mockDeps();
    const r = await post(envOk(kv), deps, GOOD);
    return out(r, { sent: calls.writeContract.length });
  },
  rate_global_day_under_the_cap: async () => {
    const kv = kvStub();
    kv.m.set("rl:day:20261012", "49");
    const { deps } = mockDeps();
    const a = await post(envOk(kv), deps, GOOD, { ip: "198.51.100.1" });
    const b = await post(envOk(kv), deps, GOOD, { ip: "198.51.100.2" });
    return out({ a: a.status, b: b.status, b_scope: b.body && b.body.limit });
  },
  rate_invalid_request_costs_no_slot: async () => {
    const kv = kvStub();
    const { deps } = mockDeps();
    await post(envOk(kv), deps, { ...GOOD, evidence_url: "ftp://x" });
    return out({ kv_writes: kv.m.size });
  },
  rate_kv_unreadable_fails_closed: async () => {
    const { deps, calls } = mockDeps();
    const r = await post(envOk(kvStub({ unreadable: true })), deps, GOOD);
    return out(r, { sent: calls.writeContract.length });
  },
  rate_corrupt_counter_fails_closed: async () => {
    const kv = kvStub();
    kv.m.set("rl:day:20261012", "lots");
    const { deps, calls } = mockDeps();
    return out(await post(envOk(kv), deps, GOOD), { sent: calls.writeContract.length });
  },
  upstream_error_with_the_key_inside: async () => {
    const bare = FAKE_KEY.slice(2);
    const msgs = [
      `request failed for key ${FAKE_KEY}`,
      `bad key ${bare}`,
      `bad key ${bare.toUpperCase()}`,
      `bad key ${FAKE_KEY.toUpperCase().replace("0X", "0x")}`,
      `a hash ${"1f".repeat(32)} somewhere`,
    ];
    const res = [];
    for (const m of msgs) {
      const { deps } = mockDeps({ write: () => { const e = new Error(m); e.shortMessage = m; throw e; } });
      const r = await post(envOk(kvStub()), deps, GOOD);
      res.push({ status: r.status, text: r.text });
    }
    return out(res);
  },
  upstream_error_text_is_shown: async () => {
    const { deps } = mockDeps({ write: () => { throw new Error("execution reverted: insufficient funds for gas\nsecond line"); } });
    return out(await post(envOk(kvStub()), deps, GOOD));
  },
  upstream_returns_a_non_hash: async () => {
    const { deps } = mockDeps({ write: () => "oops" });
    return out(await post(envOk(kvStub()), deps, GOOD));
  },
  upstream_loader_fails: async () => {
    const deps = { now: () => NOW, loadGenlayer: async () => { throw new Error(`cannot load; key was ${FAKE_KEY}`); } };
    return out(await post(envOk(kvStub()), deps, GOOD));
  },
  real_createaccount_derivation: async () => {
    // The well-known test key 0x00..01 -> 0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf (public vector).
    const gl = await import("../web/node_modules/genlayer-js/dist/index.js");
    const k = "0x" + "00".repeat(31) + "01";
    const real = { now: () => NOW, loadGenlayer: async () => ({ createAccount: gl.createAccount, createClient: gl.createClient, testnetBradbury: {} }) };
    const r = await snap(await relay.handleGet({ env: { GL_OPERATOR_KEY: k, WITNESS_RL: kvStub() } }, real));
    const bare = await snap(await relay.handleGet({ env: { GL_OPERATOR_KEY: k.slice(2), WITNESS_RL: kvStub() } }, real));
    return out({ with_prefix: r.body, without_prefix: bare.body });
  },
  clienthash_is_not_the_address: async () => {
    const kv = kvStub();
    const { deps } = mockDeps();
    await post(envOk(kv), deps, GOOD, { ip: "203.0.113.7" });
    return out({ keys: [...kv.m.keys()], values: [...kv.m.values()] });
  },
  constants: async () => out({ contract: relay.LIMITS, addr: CONTRACT, sha_of_url: createHash("sha256").update("x").digest("hex").length }),
};

const name = process.argv[2];
if (!Object.prototype.hasOwnProperty.call(CASES, name)) {
  process.stderr.write(`unknown scenario ${JSON.stringify(name)}\n`);
  process.exit(2);
}
const result = await CASES[name]();
process.stdout.write(JSON.stringify({ scenario: name, ...result }));
