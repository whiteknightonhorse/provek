/**
 * The relay behind `/api/witness-submit` (T-PW-02): it asks the GenLayer Evidence Witness contract
 * for a check on behalf of a visitor, signed by the Provek operator key.
 *
 * WHY A RELAY AT ALL. `witness(...)` on the contract is operator-only ("only the operator may request
 * a witness check"), so a visitor's own wallet cannot call it. The operator approved holding the
 * operator key as the Pages secret `GL_OPERATOR_KEY` for exactly this. The RESULT is still produced
 * by GenLayer validators, each fetching the evidence URL on its own, and is read back from the chain
 * by the page - this function only signs and sends a request.
 *
 * WHAT THE KEY MAY DO HERE. It is read from `env`, turned into an account inside `createAccount`,
 * and goes nowhere else: not into a response, not into a log line, not into a thrown message
 * (`sanitise` removes it from upstream error text before anything leaves this module).
 *
 * VALIDATION IS THE CONTRACT'S, REPEATED. `integrations/genlayer-witness/contracts/
 * provek_evidence_witness.py` (`witness`, `_validate_url`) rejects a malformed request on-chain, which
 * costs a transaction and the operator's gas. The same rules run here first so a bad request is a 400
 * with the field and the reason, and never a transaction. `tests/test_witness_relay.py` pins the two
 * implementations against each other by running the contract's own rules on the same cases.
 *
 * RATE LIMITS are counters in KV (`WITNESS_RL`): 3 per client per hour, 50 per UTC day overall. KV
 * has no atomic increment, so two simultaneous requests can both read the same count; the day cap is
 * therefore a bound within a few requests, not an exact figure, and it is documented as such. Only
 * counters are stored - never a request body, never an address in clear (the client key is an HMAC of
 * the address under a per-day message, so it cannot be joined across days).
 */
import { CONTRACT_ADDRESS, explorerTxUrl } from "../../src/witnessView.js";

export const LIMITS = Object.freeze({ per_ip_per_hour: 3, per_day_global: 50 });
export const CRITERIA = Object.freeze(["url_reachable", "artifact_hash"]);
const MAX_BODY_BYTES = 8192;
const TX_HASH = /^0x[0-9a-fA-F]{64}$/;
const KEY_HEX = /^(0x)?[0-9a-fA-F]{64}$/;

const HEADERS = { "cache-control": "no-store" };
const json = (body, status, extra = {}) =>
  Response.json(body, { status, headers: { ...HEADERS, ...extra } });

// ----------------------------------------------------------------------------- validation

/** Code points, as Python's `len()` counts them (the contract's limits are in characters). */
const chars = (s) => [...s].length;

/** Python `urlparse(url).hostname` for the shapes `_validate_url` can meet. */
function hostOf(url) {
  const m = /^[A-Za-z][A-Za-z0-9+.-]*:\/\/([^/?#]*)/.exec(url);
  if (!m) return { netloc: "", hostname: "" };
  const netloc = m[1];
  const hostinfo = netloc.slice(netloc.lastIndexOf("@") + 1);
  let hostname;
  if (hostinfo.startsWith("[")) {
    const end = hostinfo.indexOf("]");
    hostname = end > 0 ? hostinfo.slice(1, end) : "";
  } else hostname = hostinfo.split(":")[0];
  return { netloc, hostname };
}

/** `_validate_url` of the contract, reason strings included. Returns a reason or null. */
export function urlProblem(url) {
  if (typeof url !== "string" || url.length === 0 || chars(url) > 2048) {
    return "evidence_url must be a non-empty string of at most 2048 characters";
  }
  for (const ch of url) {
    const c = ch.codePointAt(0);
    if (c <= 0x20 || c === 0x7f) return "evidence_url must not contain whitespace or control characters";
  }
  const sm = /^([A-Za-z][A-Za-z0-9+.-]*):/.exec(url);
  const scheme = sm ? sm[1].toLowerCase() : "";
  if (scheme !== "http" && scheme !== "https") {
    return `evidence_url must be http or https, got scheme '${scheme}'`;
  }
  const { netloc, hostname } = hostOf(url);
  if (!hostname) return "evidence_url must name a host";
  if (netloc.includes("@")) return "evidence_url must not carry userinfo";
  return null;
}

/**
 * Body -> `{ ok: true, args }` (the four `witness(...)` arguments, `expected` normalised exactly as
 * the contract normalises it, so what is sent is what the chain stores) or
 * `{ ok: false, field, reason }`. Rules and order are the contract's.
 */
export function validate(body) {
  if (body === null || typeof body !== "object" || Array.isArray(body)) {
    return { ok: false, field: "body", reason: "the request body must be a JSON object" };
  }
  const { subject_id, criterion, evidence_url } = body;
  if (typeof subject_id !== "string" || subject_id.length === 0 || chars(subject_id) > 256) {
    return { ok: false, field: "subject_id", reason: "subject_id must be a non-empty string of at most 256 characters" };
  }
  if (typeof criterion !== "string" || !CRITERIA.includes(criterion)) {
    return {
      ok: false, field: "criterion",
      reason: `unsupported criterion ${JSON.stringify(criterion ?? null)}: supported types are ${CRITERIA.join(", ")}`,
    };
  }
  const why = urlProblem(evidence_url);
  if (why) return { ok: false, field: "evidence_url", reason: why };
  if (body.expected !== undefined && typeof body.expected !== "string") {
    return { ok: false, field: "expected", reason: "expected must be a string" };
  }
  const expected = (body.expected ?? "").trim().toLowerCase();
  if (criterion === "artifact_hash") {
    if (!/^[0-9a-f]{64}$/.test(expected)) {
      return { ok: false, field: "expected", reason: "artifact_hash requires a 64-character hex sha256 in `expected`" };
    }
  } else if (expected !== "") {
    return { ok: false, field: "expected", reason: "url_reachable does not take an `expected` value" };
  }
  return { ok: true, args: [subject_id, criterion, evidence_url, expected] };
}

// ----------------------------------------------------------------------------- key and errors

/** The key as `0x` + 64 lowercase hex, or null when absent or malformed. Never a random fallback:
 *  `createAccount("")` in genlayer-js GENERATES a key, which would sign as a stranger. */
export function normaliseKey(raw) {
  if (typeof raw !== "string") return null;
  const k = raw.trim();
  return KEY_HEX.test(k) ? `0x${k.replace(/^0x/, "").toLowerCase()}` : null;
}

/** Upstream error text with the key removed, first line only, bounded. */
export function sanitise(err, key) {
  const raw = [err && err.shortMessage, err && err.details, err && err.message]
    .filter((x) => typeof x === "string" && x !== "")[0] ?? String(err ?? "unknown error");
  let text = raw.split("\n")[0];
  if (key) {
    const bare = key.replace(/^0x/, "");
    text = text.split(key).join("[redacted]").split(bare).join("[redacted]");
    text = text.split(key.toUpperCase()).join("[redacted]").split(bare.toUpperCase()).join("[redacted]");
  }
  text = text.replace(/\b(0x)?[0-9a-fA-F]{64}\b/g, "[redacted-64-hex]");
  return text.length > 300 ? `${text.slice(0, 300)}...` : text;
}

// ----------------------------------------------------------------------------- rate limits

const pad = (n) => String(n).padStart(2, "0");
const dayOf = (d) => `${d.getUTCFullYear()}${pad(d.getUTCMonth() + 1)}${pad(d.getUTCDate())}`;

/** HMAC-SHA256 of the address under a message that names the UTC day, keyed by the operator key. */
async function clientKey(ip, day, secret) {
  const enc = new TextEncoder();
  const k = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = new Uint8Array(await crypto.subtle.sign("HMAC", k, enc.encode(`witness-rl:${day}:${ip}`)));
  return [...sig.slice(0, 16)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function count(kv, key) {
  const v = await kv.get(key);
  if (v === null || v === undefined) return 0;
  const n = Number(v);
  if (!Number.isInteger(n) || n < 0) throw new Error("unreadable counter");
  return n;
}

/** Read both counters; refuse if either is at its limit; else increment both. */
async function takeSlot(kv, ip, secret, now) {
  const day = dayOf(now);
  const hour = `${day}${pad(now.getUTCHours())}`;
  const ipKey = `rl:ip:${await clientKey(ip, day, secret)}:${hour}`;
  const dayKey = `rl:day:${day}`;
  const [ipN, dayN] = await Promise.all([count(kv, ipKey), count(kv, dayKey)]);
  const toNextHour = 3600 - (now.getUTCMinutes() * 60 + now.getUTCSeconds());
  const toNextDay = 86400 - (now.getUTCHours() * 3600 + now.getUTCMinutes() * 60 + now.getUTCSeconds());
  if (ipN >= LIMITS.per_ip_per_hour) return { ok: false, scope: "per_ip_per_hour", retry: toNextHour };
  if (dayN >= LIMITS.per_day_global) return { ok: false, scope: "per_day_global", retry: toNextDay };
  await Promise.all([
    kv.put(ipKey, String(ipN + 1), { expirationTtl: 7200 }),
    kv.put(dayKey, String(dayN + 1), { expirationTtl: 172800 }),
  ]);
  return { ok: true };
}

// ----------------------------------------------------------------------------- handlers

export const defaultDeps = {
  now: () => new Date(),
  loadGenlayer: async () => {
    const [gl, chains] = await Promise.all([import("genlayer-js"), import("genlayer-js/chains")]);
    return { createAccount: gl.createAccount, createClient: gl.createClient, testnetBradbury: chains.testnetBradbury };
  },
};

function configState(env) {
  const key = normaliseKey(env.GL_OPERATOR_KEY);
  const kv = env.WITNESS_RL && typeof env.WITNESS_RL.get === "function" ? env.WITNESS_RL : null;
  if (!key) {
    const reason = env.GL_OPERATOR_KEY ? "GL_OPERATOR_KEY is set but is not a 32-byte hex key" : "GL_OPERATOR_KEY is not set";
    return { enabled: false, key: null, kv, reason };
  }
  if (!kv) return { enabled: false, key, kv: null, reason: "the WITNESS_RL KV binding is not set, so submissions cannot be rate limited" };
  return { enabled: true, key, kv, reason: null };
}

export async function handleGet({ env }, deps = defaultDeps) {
  const cfg = configState(env);
  let operator = null;
  let operator_error = null;
  if (cfg.key) {
    try {
      operator = (await deps.loadGenlayer()).createAccount(cfg.key).address;
    } catch (e) {
      operator_error = sanitise(e, cfg.key);
    }
  }
  return json({
    enabled: cfg.enabled && operator !== null,
    operator,
    contract: CONTRACT_ADDRESS,
    limits: LIMITS,
    ...(cfg.reason ? { reason: cfg.reason } : {}),
    ...(operator_error ? { reason: `the operator address could not be derived: ${operator_error}` } : {}),
  }, 200);
}

export async function handlePost({ request, env }, deps = defaultDeps) {
  const cfg = configState(env);
  if (!cfg.enabled) {
    return json({ ok: false, error: `Submissions are temporarily disabled: ${cfg.reason}.` }, 503);
  }
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin) {
    return json({ ok: false, error: "Cross-origin submissions are not accepted." }, 403);
  }

  let body;
  try {
    const text = await request.text();
    if (new TextEncoder().encode(text).length > MAX_BODY_BYTES) {
      return json({ ok: false, field: "body", error: `The request body is larger than ${MAX_BODY_BYTES} bytes.` }, 400);
    }
    body = JSON.parse(text);
  } catch {
    return json({ ok: false, field: "body", error: "The request body is not valid JSON." }, 400);
  }
  const v = validate(body);
  if (!v.ok) return json({ ok: false, field: v.field, reason: v.reason, error: `${v.field}: ${v.reason}` }, 400);

  const now = deps.now();
  let slot;
  try {
    slot = await takeSlot(cfg.kv, request.headers.get("cf-connecting-ip") || "unknown", cfg.key, now);
  } catch {
    // Fail closed: a limiter that cannot be read is not a limiter.
    return json({ ok: false, error: "The rate limiter is unavailable, so the request was not sent." }, 503);
  }
  if (!slot.ok) {
    const what = slot.scope === "per_ip_per_hour"
      ? `at most ${LIMITS.per_ip_per_hour} requests per client per hour`
      : `at most ${LIMITS.per_day_global} requests per UTC day for the whole service`;
    return json({ ok: false, limit: slot.scope, retry_after_seconds: slot.retry, error: `Rate limit reached: ${what}. Try again in ${slot.retry} seconds.` },
      429, { "retry-after": String(slot.retry) });
  }

  let hash;
  try {
    const { createAccount, createClient, testnetBradbury } = await deps.loadGenlayer();
    const account = createAccount(cfg.key);
    const client = createClient({ chain: testnetBradbury, account });
    hash = await client.writeContract({ address: CONTRACT_ADDRESS, functionName: "witness", args: v.args, value: 0n });
  } catch (e) {
    const message = sanitise(e, cfg.key);
    console.error(`witness-submit upstream failure: ${message}`);
    return json({ ok: false, error: `The GenLayer network refused the request: ${message}` }, 502);
  }
  if (typeof hash !== "string" || !TX_HASH.test(hash)) {
    console.error("witness-submit: the client library returned something that is not a transaction hash");
    return json({ ok: false, error: "The GenLayer client returned something that is not a transaction hash." }, 502);
  }
  return json({ tx_hash: hash, explorer_url: explorerTxUrl(hash), track_url: `/witness/?tx=${hash}` }, 202);
}

export const methodNotAllowed = () =>
  json({ ok: false, error: "Use GET for status or POST to submit." }, 405, { allow: "GET, POST" });
