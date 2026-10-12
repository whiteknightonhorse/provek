/**
 * Pure helpers for the GenLayer Evidence Witness page (`pages/Witness.tsx`, route `/witness/`).
 * Plain JavaScript, not `.ts`, by the precedent `slug.js` and `formatObservation.js` set: the gate
 * that guards this (`tests/test_witness_page.py`, via `tests/witness_view_probe.mjs`) runs
 * these bytes directly under Node, and Node on this host is v20 and cannot strip types.
 *
 * NAMING. This is NOT Provek's own WitnessRecord (`/w/<id>/`). Everything here is the GenLayer
 * Evidence Witness - an Intelligent Contract on the GenLayer testnet Bradbury - and every label
 * built from these helpers says so.
 *
 * NOTHING HERE INVENTS A VALUE. Each function either returns what an RPC response carried or
 * returns an explicit refusal (`null`, or an object with `ok: false` and a reason). A caller that
 * renders the refusal is showing a fact about the read; a caller that renders a default would be
 * showing a number nobody measured.
 */

/** The deployed contract - the single place in `web/` that names it. `tests/test_witness_page.py`
 *  compares these against `integrations/genlayer-witness/deploy/deployment.json`. */
export const CONTRACT_ADDRESS = "0x499eD0E23CbCdC8Fc7735709dca32bCb01638fd6";
export const CHAIN_ID = 4221;
export const NETWORK_LABEL = "GenLayer testnet Bradbury (chain 4221)";
export const EXPLORER_BASE = "https://explorer-bradbury.genlayer.com";
export const DEFAULT_SUBJECT = "git:whiteknightonhorse/provek";

/** Statuses from the GenLayer consensus docs (v0.6) that end the watch. FINALIZED, UNDETERMINED and
 *  CANCELED are the three the order names; the two timeout statuses are the "timeout status" case. */
export const TERMINAL_STATUSES = [
  "FINALIZED", "UNDETERMINED", "CANCELED", "VALIDATORS_TIMEOUT", "LEADER_TIMEOUT",
];
/** Every status the docs list, in lifecycle order where there is one. A status outside this list is
 *  still shown verbatim - it is never mapped to a known one. */
export const KNOWN_STATUSES = [
  "PENDING", "PROPOSING", "COMMITTING", "REVEALING", "ACCEPTED", "UNDETERMINED", "FINALIZED",
  "CANCELED", "APPEAL_REVEALING", "APPEAL_COMMITTING", "VALIDATORS_TIMEOUT", "LEADER_TIMEOUT",
  "LEADER_REVEALING",
];

export const UNDETERMINED_EXPLANATION =
  "Validators could not agree, typically because the evidence URL was unavailable to them; "
  + "no record was written.";

const TX_HASH = /^0x[0-9a-fA-F]{64}$/;

/** `?tx=0x...` or typed input -> a hash, or null. Never "fixes" a malformed value. */
export function parseTxHash(input) {
  if (typeof input !== "string") return null;
  const s = input.trim();
  return TX_HASH.test(s) ? s : null;
}

/** The `tx` value of a query string (`location.search`), or null when absent. */
export function txFromQuery(search) {
  if (typeof search !== "string") return null;
  const v = new URLSearchParams(search).get("tx");
  return v === null ? null : v;
}

export function explorerTxUrl(hash) {
  return `${EXPLORER_BASE}/tx/${hash}`;
}
export function explorerAddressUrl(address) {
  return `${EXPLORER_BASE}/address/${address}`;
}

/** `list_by_subject` returns a JSON ARRAY IN A STRING. Anything else is a failed read, not "[]". */
export function parseIdList(raw) {
  if (typeof raw !== "string") return { ok: false, why: "list_by_subject did not return a string" };
  let v;
  try {
    v = JSON.parse(raw);
  } catch {
    return { ok: false, why: "list_by_subject returned text that is not JSON" };
  }
  if (!Array.isArray(v) || !v.every((x) => typeof x === "string")) {
    return { ok: false, why: "list_by_subject did not return an array of strings" };
  }
  return { ok: true, ids: v };
}

const RESULT_FIELDS = [
  "subject_id", "criterion", "evidence_url", "expected", "result", "evidence_digest",
  "checked_at", "observation",
];

/**
 * `get_result` response -> the card the page renders. The contract's `result` is PASS or FAIL;
 * anything else is carried through as-is with `recognised: false` so the badge can say so.
 * A missing field is `null` (rendered as "not returned"), never an empty string standing in.
 */
export function resultCard(witnessId, raw) {
  if (raw === null || typeof raw !== "object" || Array.isArray(raw)) {
    return { ok: false, why: "get_result did not return an object" };
  }
  const o = raw instanceof Map ? Object.fromEntries(raw) : raw;
  const card = { ok: true, witnessId };
  for (const k of RESULT_FIELDS) card[k] = typeof o[k] === "string" ? o[k] : null;
  card.recognised = card.result === "PASS" || card.result === "FAIL";
  return card;
}

/** `https://` / `http://` only: an evidence URL is rendered as a link, and `javascript:` must not be. */
export function safeHref(url) {
  return typeof url === "string" && /^https?:\/\//i.test(url) ? url : null;
}

/** An empty `expected` is a real value for `url_reachable`; say so rather than leaving a blank cell. */
export function expectedLabel(card) {
  if (card.expected === null) return "not returned";
  return card.expected === "" ? "(empty - this criterion has no expected value)" : card.expected;
}

/**
 * RPC errors from `gen_call` carry the contract's UserError as a Go-printed struct whose
 * `ReturnData:[]uint8{...}` is the message in bytes. Pull a readable message out of those bytes
 * when it is there; otherwise show the first line of the error text, truncated. The raw text is
 * never replaced by a guess.
 */
export function readableError(err) {
  const parts = [err && err.shortMessage, err && err.details, err && err.message]
    .filter((x) => typeof x === "string" && x !== "");
  const whole = parts.length ? parts.join("\n") : String(err || "unknown error");
  const m = /ReturnData:\[\]uint8\{([0-9a-fx, ]+)\}/.exec(whole);
  if (m) {
    const bytes = m[1].split(",").map((x) => parseInt(x.trim(), 16)).filter((n) => Number.isFinite(n));
    const ascii = bytes.map((b) => (b >= 32 && b < 127 ? String.fromCharCode(b) : "\u0000")).join("");
    const found = /unknown witness_id '[^']*'/.exec(ascii);
    if (found) return `The contract answered: ${found[0]}`;
  }
  // No decodable contract message: show the library's short message, never a made-up reason.
  const first = (parts[0] || whole).split("\n")[0];
  return first.length > 300 ? `${first.slice(0, 300)}...` : first;
}

/** Append `statusName` to the observed lifecycle only when it differs from the last one seen. */
export function observe(lifecycle, statusName, atMs) {
  if (typeof statusName !== "string" || statusName === "") return lifecycle;
  const last = lifecycle[lifecycle.length - 1];
  if (last && last.status === statusName) return lifecycle;
  return [...lifecycle, { status: statusName, at: new Date(atMs).toISOString() }];
}

export function isTerminal(statusName) {
  return TERMINAL_STATUSES.includes(statusName);
}

/** A hash the relay has just returned may not be indexed by Bradbury yet. For this long after the
 *  first poll, UNINITIALIZED means "not indexed yet" and the watch goes on; after it, the hash is
 *  reported as unknown. */
export const NOT_INDEXED_GRACE_MS = 60 * 1000;
/** The watch stops after this long even if no terminal status arrived. */
export const WATCH_LIMIT_MS = 15 * 60 * 1000;

/**
 * One poll of the tracker. `prev` is `{ startedAt, lifecycle }` (`startedAt` = the first poll),
 * `read` is a `summariseTx` result (an `{ ok: false, why }` is a failed read, shown and retried).
 * Returns what the page shows and `done`: "terminal" | "limit" | null. UNINITIALIZED inside the
 * grace window is `notFound: "not_indexed_yet"` and does NOT end the watch; past it, `"absent"`
 * does.
 */
export function trackStep(prev, read, nowMs, limitMs = WATCH_LIMIT_MS) {
  let lifecycle = prev.lifecycle;
  let tx = null;
  let notFound = null;
  let error = null;
  const waitedMs = nowMs - prev.startedAt;
  if (!read.ok) error = read.why;
  else if (read.found) {
    tx = read;
    if (tx.status) lifecycle = observe(lifecycle, tx.status, nowMs);
  } else notFound = waitedMs < NOT_INDEXED_GRACE_MS ? "not_indexed_yet" : "absent";
  const terminal = !!(tx && tx.status && isTerminal(tx.status));
  const done = terminal ? "terminal" : waitedMs > limitMs ? "limit" : notFound === "absent" ? "terminal" : null;
  return { lifecycle, tx, notFound, notIndexedSeconds: notFound ? Math.floor(waitedMs / 1000) : null, error, done };
}

/**
 * One `getTransaction` response -> the facts the tracker shows. `UNINITIALIZED` with a zero
 * recipient is what Bradbury answers for a hash it has never seen: that is "not found", which is
 * a fact about the chain, not an error of ours and not a pending transaction.
 */
export function summariseTx(tx, contractAddress = CONTRACT_ADDRESS) {
  if (tx === null || typeof tx !== "object") return { ok: false, why: "no transaction object returned" };
  const status = typeof tx.statusName === "string" ? tx.statusName : null;
  const recipient = typeof tx.recipient === "string" ? tx.recipient : null;
  if (status === "UNINITIALIZED" || /^0x0+$/.test(recipient || "")) {
    return { ok: true, found: false };
  }
  const exec = typeof tx.txExecutionResultName === "string" ? tx.txExecutionResultName : null;
  const forThisContract = recipient !== null && recipient.toLowerCase() === contractAddress.toLowerCase();
  const settled = status === "ACCEPTED" || status === "FINALIZED";
  // ACCEPTED/FINALIZED is consensus, not execution: the execution result is a separate field.
  const succeeded = settled && exec === "FINISHED_WITH_RETURN";
  return {
    ok: true,
    found: true,
    status,
    consensusResult: typeof tx.resultName === "string" ? tx.resultName : null,
    execution: exec,
    sender: typeof tx.sender === "string" ? tx.sender : null,
    recipient,
    forThisContract,
    succeeded,
    settledButFailed: settled && exec !== "FINISHED_WITH_RETURN",
    createdAt: Number.isFinite(Number(tx.createdTimestamp)) && Number(tx.createdTimestamp) > 0
      ? new Date(Number(tx.createdTimestamp) * 1000).toISOString() : null,
    call: callOf(tx),
  };
}

/** The `witness(...)` call a transaction made, as decoded by genlayer-js, or null. */
export function callOf(tx) {
  const cd = tx && tx.txDataDecoded && tx.txDataDecoded.callData;
  if (!cd) return null;
  const method = cd instanceof Map ? cd.get("method") : cd.method;
  const args = cd instanceof Map ? cd.get("args") : cd.args;
  if (method !== "witness" || !Array.isArray(args) || args.length < 4) return null;
  if (!args.slice(0, 4).every((a) => typeof a === "string")) return null;
  const [subject_id, criterion, evidence_url, expected] = args;
  return { subject_id, criterion, evidence_url, expected };
}

/**
 * The transaction's return value is not exposed by genlayer-js on Bradbury (measured, MEASURED-015:
 * `eqBlocksOutputs` is an undecoded blob), so the witness id is found by DIFFERENCE: the records
 * under the call's subject whose criterion, URL and expected value equal the call's arguments.
 * Exactly one match is an answer; zero or several are reported as such, never narrowed by a guess.
 */
export function matchRecords(call, cards) {
  if (!call) return { kind: "no_call" };
  const hits = cards.filter((c) => c.ok && c.subject_id === call.subject_id
    && c.criterion === call.criterion && c.evidence_url === call.evidence_url
    && c.expected === call.expected);
  if (hits.length === 0) return { kind: "none" };
  if (hits.length === 1) return { kind: "one", card: hits[0] };
  return { kind: "several", cards: hits };
}

/**
 * The relay's answer (`/api/witness-submit`) -> what the form does. A 202 must carry a usable hash;
 * every other status shows the relay's own `error` text verbatim (400 names the field, 429 the wait,
 * 502 the upstream message), or says that there was none - it never substitutes a friendlier reason.
 */
export function relayOutcome(status, body) {
  if (status === 202) {
    const hash = body && typeof body === "object" ? parseTxHash(body.tx_hash) : null;
    return hash ? { ok: true, hash } : { ok: false, status, message: "The relay answered 202 without a usable transaction hash." };
  }
  const msg = body && typeof body === "object" && typeof body.error === "string" && body.error !== "" ? body.error : null;
  return { ok: false, status, message: msg ?? `The relay answered HTTP ${status} without a message.` };
}

/** Where the tracker for a hash lives. */
export function trackUrl(hash) {
  return `/witness/?tx=${hash}`;
}
