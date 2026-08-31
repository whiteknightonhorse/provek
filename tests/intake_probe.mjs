/**
 * The instrument for `tests/test_intake_survives_a_failed_writeback.py`: it RUNS the intake
 * endpoint instead of reading it.
 *
 * WHY IT EXISTS AT ALL. Every other gate over `web/functions/api/apply.js` strips its comments and
 * matches regular expressions against the source, which can say that a `try` is written and can
 * never say what the handler answers. The property this file's caller asserts is a property of the
 * ANSWER - a 200 with `ok: true` on the path where the record is already durable - and a source
 * scan would go green on a `try` that wrapped the wrong line or swallowed the wrong failure. L-25
 * is the standing form of this: a test can only be about what it can read, and until now the
 * boundary of the intake's suite was the file tree.
 *
 * WHAT IT IS STILL NOT. This runs the module under Node with a stubbed KV binding, not under
 * `workerd` and not on Cloudflare. The 500 that a thrown handler becomes, and the browser that
 * renders it, are outside what any of this can see; `durable_write_fails` below therefore reports
 * that the invocation FAILED, and the step from there to what the visitor reads is stated in
 * docs/INTAKE_OPERATIONS.md rather than measured here.
 *
 * Emits one JSON object on stdout. Every failure is loud: an unreadable scenario name exits 2, and
 * an import that does not resolve exits non-zero on its own.
 */

import { onRequestPost } from "../web/functions/api/apply.js";

const SUBMISSION = {
  repo: "https://github.com/example-org/example-repo",
  contact: "applicant@example.com",
  mandate: "passive",
  // The endpoint refuses a submission with no consent, and refuses one naming a wording it does
  // not serve - the same boundary D-21 drew for the mandate, since a hand-built POST walks past
  // the form's disabled button. This probe measures the ORDINARY path, so it sends what an
  // ordinary browser sends. The refusals themselves are judged by
  // tests/test_consent_text_is_one_sentence.py and by a live check against the deployed site.
  consent: true,
  consent_version: "updates-1.0.0",
};

/**
 * A KV binding that records every write it was ASKED for and refuses the ones it is told to.
 *
 * `stored` is the distinction the caller needs and the first draft of this file did not make: a
 * refused write is still an attempt, so counting attempts would have reported the durable record
 * as present in the one scenario where nothing was written at all - the endpoint's own defect,
 * rebuilt inside the instrument measuring it.
 *
 * `refuseWith` is here because of a measured false green. The stub threw one failure shape, a 429,
 * and a `catch` narrowed to `if (!String(e).includes("429")) throw e` kept the whole suite green
 * while the 500-over-a-durable-record defect returned for every other KV failure. A gate that
 * exercises one shape is a gate about that shape. Found by Fable, by applying that mutation.
 */
function intake(refuse, refuseWith) {
  const writes = [];
  return {
    writes,
    binding: {
      put: async (k, v) => {
        const refused = refuse.includes(writes.length + 1);
        writes.push({ key: k, value: v, stored: !refused });
        if (refused) throw refuseWith();
      },
    },
  };
}

const RATE_LIMIT = () =>
  new Error("KV PUT failed: 429 rate limited (1 write per second to the same key)");
// Not a 429, and not an `Error` at all. A rejected promise carries whatever it was rejected with,
// and a handler that recognises failures by their text recognises nothing about this one.
const UNRECOGNISABLE = () => "KV unavailable";

/**
 * Telegram's sendMessage, stubbed at the one call site that reaches it.
 *
 * `ok` was a parameter that was only ever passed `true` - a control that could not go false, which
 * is this repository's own founding defect sitting in a test helper. With it dead, `delivered`
 * could be hardcoded to `true` in the endpoint and all ten assertions stayed green, so the value
 * the operator's follow-up acts on was unmeasured in the direction that matters. Found by Fable,
 * by applying that mutation.
 */
function telegram(mode) {
  const sent = [];
  return {
    sent,
    fetch: async (url, init) => {
      sent.push({ url: String(url), body: init && init.body });
      // THROWING IS A THIRD OUTCOME, not a rude way of saying 502. A refused message is a reply;
      // an unreachable Telegram is no reply at all, and it lands in the endpoint's OTHER branch -
      // the `catch` beside the notice, whose body was dead in every scenario until this existed.
      // A `catch { delivered = true }` there passed all eleven assertions. Found by Fable.
      if (mode === "throws") throw new TypeError("fetch failed");
      return new Response("{}", { status: mode === "ok" ? 200 : 502 });
    },
  };
}

const CASES = {
  // The control. Without it, an assertion that the failure path answers 200 would also pass on a
  // handler that answers 200 to everything, and the probe would be proving nothing about the fix.
  both_writes_land: { refuse: [], body: SUBMISSION },
  // The defect. The first write landed, so the submission exists; the second is refused.
  writeback_fails: { refuse: [2], body: SUBMISSION },
  // The defect on the path that MATTERS MOST, and the reason the notice is stubbed at all: the
  // operator has been told, so the visitor may be told so too - and that is the sentence the 500
  // used to replace with "Nothing was saved".
  notice_sent_writeback_fails: { refuse: [2], body: SUBMISSION, notice: true },
  // The same, with Telegram refusing the message. Two things are pinned that nothing pinned
  // before: that `delivered` follows what the notice actually did rather than being a constant,
  // and that the sentinel carries the same value in the FALSE direction.
  notice_refused_writeback_fails: { refuse: [2], body: SUBMISSION, notice: true, wire: "refuses" },
  // Telegram unreachable rather than refusing - the endpoint's `catch`, not its `r.ok`.
  notice_throws_writeback_fails: { refuse: [2], body: SUBMISSION, notice: true, wire: "throws" },
  // THE ONE COMBINATION NOTHING EXERCISED: a notice that went out AND a write-back that landed.
  // Every notice scenario refused write 2 and the only successful write-back had no notice, so
  // the write whose whole purpose is carrying the measured outcome into the store was never
  // watched doing it - `delivered: false` hardcoded there passed all eleven. Found by Fable.
  notice_sent_both_writes_land: { refuse: [], body: SUBMISSION, notice: true },
  // The same failure wearing a shape nothing can pattern-match on. See `refuseWith` above.
  writeback_fails_unrecognisably: { refuse: [2], with: UNRECOGNISABLE, body: SUBMISSION },
  // The sentinel's own failure. Write three is the different-key sentinel, so refusing both leaves
  // the store with a record and nothing beside it - which is what a dead invocation leaves, and is
  // read that way rather than being claimed as anything better.
  both_writes_refused: { refuse: [2, 3], body: SUBMISSION },
  // The OTHER direction, and the one that keeps the fix from being "catch everything". Nothing is
  // stored, so "Nothing was saved" is true and the invocation must still fail.
  durable_write_fails: { refuse: [1], body: SUBMISSION },
  // A second control, on the code rather than on the answer: a rejected submission proves the
  // probe reached the real validation and is not exercising a stub of its own making.
  invalid_repo: { refuse: [], body: { ...SUBMISSION, repo: "https://example.com/elsewhere" } },
};

const name = process.argv[2];
const chosen = Object.prototype.hasOwnProperty.call(CASES, name) ? CASES[name] : null;
if (!chosen) {
  process.stderr.write(`unknown scenario ${JSON.stringify(name)}\n`);
  process.exit(2);
}

const kv = intake(chosen.refuse, chosen.with || RATE_LIMIT);
const env = { INTAKE: kv.binding };
const wire = telegram(chosen.wire || "ok");
if (chosen.notice) {
  // Both variables, because the endpoint sends the notice only when it holds both. Their values
  // are nonsense and never leave this process: the fetch that would carry them is replaced below.
  env.TELEGRAM_BOT_TOKEN = "probe-token-not-a-credential";
  env.TELEGRAM_CHAT_ID = "probe-chat";
  globalThis.fetch = wire.fetch;
}

const request = new Request("https://provek.dev/api/apply", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify(chosen.body),
});

const result = { scenario: name };
try {
  const response = await onRequestPost({ request, env });
  result.outcome = "answered";
  result.status = response.status;
  result.body = await response.json();
} catch (err) {
  // The handler threw, which is what Cloudflare turns into the 500 the form reads as a failure.
  result.outcome = "invocation_failed";
  // `|| err` because a rejection is not necessarily an Error, and `String(undefined)` in the
  // transcript is the instrument reporting nothing while looking like a reading - the endpoint's
  // own repaired defect, which was sitting in this line. Found by Fable.
  result.error = String((err && err.message) || err);
}
result.writes = kv.writes.map((w) => ({ key: w.key, stored: w.stored, value: JSON.parse(w.value) }));
result.notices = wire.sent.length;
process.stdout.write(JSON.stringify(result));
