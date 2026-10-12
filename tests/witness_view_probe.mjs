/**
 * Runs `web/src/witnessView.js` directly under Node against `tests/fixtures/witness_bradbury_reads.json`
 * - responses captured from the live Bradbury RPC (T-PW-01, MEASURED-015). No network here: the
 * fixture is the network's answer, frozen. One scenario per argv[2]; prints JSON.
 */
import { readFileSync } from "node:fs";
import * as v from "../web/src/witnessView.js";

const fx = JSON.parse(readFileSync(new URL("./fixtures/witness_bradbury_reads.json", import.meta.url)));
const finalized = () => ({ ...fx.tx_finalized, txDataDecoded: { callData: new Map(Object.entries(fx.tx_finalized.txDataDecoded.callData)) } });
const card = (k) => v.resultCard(fx[k].witness_id, fx[k].response);

const CASES = {
  constants: () => ({ addr: v.CONTRACT_ADDRESS, chain: v.CHAIN_ID, subject: v.DEFAULT_SUBJECT }),
  pass_card: () => card("get_result_pass"),
  fail_card: () => card("get_result_fail"),
  id_list: () => v.parseIdList(fx.list_by_subject_raw),
  id_list_empty: () => v.parseIdList("[]"),
  id_list_garbage: () => v.parseIdList("not json"),
  id_list_wrong_shape: () => v.parseIdList('{"a":1}'),
  id_list_not_string: () => v.parseIdList(42),
  card_not_object: () => v.resultCard("x", "oops"),
  card_missing_field: () => v.resultCard("x", { result: "PASS" }),
  card_unrecognised_result: () => v.resultCard("x", { ...fx.get_result_pass.response, result: "MAYBE" }),
  expected_empty: () => v.expectedLabel({ expected: "" }),
  expected_missing: () => v.expectedLabel({ expected: null }),
  href_https: () => v.safeHref("https://provek.dev/"),
  href_javascript: () => v.safeHref("javascript:alert(1)"),
  error_unknown_id: () => v.readableError({ shortMessage: "Missing or invalid parameters.", message: fx.unknown_id_error_message }),
  error_plain: () => v.readableError(new Error("Failed to fetch")),
  error_long: () => v.readableError(new Error("x".repeat(500))).length,
  hash_ok: () => v.parseTxHash("0x" + "ab".repeat(32)),
  hash_padded: () => v.parseTxHash("  0x" + "AB".repeat(32) + " "),
  hash_short: () => v.parseTxHash("0x1234"),
  hash_no_prefix: () => v.parseTxHash("ab".repeat(32)),
  hash_from_query: () => v.txFromQuery("?tx=0xabc&x=1"),
  hash_from_empty_query: () => v.txFromQuery(""),
  explorer_tx: () => v.explorerTxUrl("0xabc"),
  explorer_address: () => v.explorerAddressUrl(v.CONTRACT_ADDRESS),
  observe_sequence: () => {
    let l = [];
    for (const [s, t] of [["PENDING", 0], ["PENDING", 4000], ["PROPOSING", 8000], ["ACCEPTED", 12000], ["ACCEPTED", 16000], ["FINALIZED", 20000]]) l = v.observe(l, s, t);
    return l;
  },
  observe_ignores_empty: () => v.observe([], "", 0),
  terminal: () => Object.fromEntries(v.KNOWN_STATUSES.map((s) => [s, v.isTerminal(s)])),
  tx_finalized: () => v.summariseTx(finalized()),
  tx_unknown: () => v.summariseTx(fx.tx_unknown),
  tx_accepted_but_failed: () => v.summariseTx({ ...finalized(), statusName: "ACCEPTED", txExecutionResultName: "FINISHED_WITH_ERROR" }),
  tx_undetermined: () => v.summariseTx({ ...finalized(), statusName: "UNDETERMINED", resultName: "DISAGREE", txExecutionResultName: "NOT_VOTED" }),
  tx_other_contract: () => v.summariseTx({ ...finalized(), recipient: "0x1111111111111111111111111111111111111111" }),
  tx_not_object: () => v.summariseTx(null),
  call_of_finalized: () => v.callOf(finalized()),
  call_of_wrong_method: () => v.callOf({ txDataDecoded: { callData: { method: "other", args: ["a", "b", "c", "d"] } } }),
  match_one: () => {
    const c = card("get_result_pass");
    const other = card("get_result_fail");
    return v.matchRecords(v.callOf(finalized()), [other, c]).kind + ":" + v.matchRecords(v.callOf(finalized()), [other, c]).card?.witnessId;
  },
  match_none: () => v.matchRecords(v.callOf(finalized()), [card("get_result_fail")]).kind,
  match_several: () => v.matchRecords(v.callOf(finalized()), [card("get_result_pass"), { ...card("get_result_pass"), witnessId: "dup" }]).kind,
  match_no_call: () => v.matchRecords(null, []).kind,
  // The tracker loop, driven with a clock: one status per 4 s poll, starting at t=0 (the first poll).
  track_not_indexed_then_finalized: () => runTrack(["UNINITIALIZED", "UNINITIALIZED", "PENDING", "PROPOSING", "COMMITTING", "REVEALING", "ACCEPTED", "FINALIZED"], 4000),
  track_uninitialized_for_60s: () => runTrack(Array(40).fill("UNINITIALIZED"), 4000),
  track_uninitialized_for_58s: () => runTrack(Array(15).fill("UNINITIALIZED"), 4000),
  track_appeal_recurrence: () => runTrack(["PENDING", "COMMITTING", "APPEAL_COMMITTING", "COMMITTING", "FINALIZED"], 4000),
  relay_202: () => v.relayOutcome(202, { tx_hash: "0x" + "ab".repeat(32), track_url: "/x" }),
  relay_202_without_hash: () => v.relayOutcome(202, { tx_hash: "nope" }),
  relay_400: () => v.relayOutcome(400, { ok: false, field: "evidence_url", error: "evidence_url: evidence_url must name a host" }),
  relay_429: () => v.relayOutcome(429, { ok: false, error: "Rate limit reached: at most 3 requests per client per hour. Try again in 2670 seconds." }),
  relay_502: () => v.relayOutcome(502, { ok: false, error: "The GenLayer network refused the request: boom" }),
  relay_503_not_json: () => v.relayOutcome(503, null),
  track_url: () => v.trackUrl("0x" + "ab".repeat(32)),
  undetermined_text: () => v.UNDETERMINED_EXPLANATION,
};

/** Feed `statuses` to `trackStep` one per `everyMs`, stopping when it says done, like the page does. */
function runTrack(statuses, everyMs) {
  let lifecycle = [];
  const log = [];
  for (let i = 0; i < statuses.length; i++) {
    const read = statuses[i] === "UNINITIALIZED" ? v.summariseTx(fx.tx_unknown) : v.summariseTx({ ...finalized(), statusName: statuses[i] });
    const step = v.trackStep({ startedAt: 0, lifecycle }, read, i * everyMs);
    lifecycle = step.lifecycle;
    log.push({ at_s: (i * everyMs) / 1000, notFound: step.notFound, seconds: step.notIndexedSeconds, done: step.done });
    if (step.done) break;
  }
  return { polls: log.length, last: log[log.length - 1], statuses: lifecycle.map((o) => o.status), log };
}

const name = process.argv[2];
if (!Object.prototype.hasOwnProperty.call(CASES, name)) {
  process.stderr.write(`unknown scenario ${JSON.stringify(name)}\n`);
  process.exit(2);
}
process.stdout.write(JSON.stringify({ scenario: name, result: CASES[name]() }));
