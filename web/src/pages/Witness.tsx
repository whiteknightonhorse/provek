/** `/witness/` - read path and lifecycle view for the GenLayer Evidence Witness.
 *
 * THIS IS NOT PROVEK'S WITNESSRECORD. The site already uses the word for its own records at
 * `/w/<id>/` (spec 4.2-bis point 4, D-50) and that is untouched. This page reads a different
 * thing: an Intelligent Contract on the GenLayer testnet Bradbury, whose validators each fetch an
 * evidence URL on their own and must agree on PASS or FAIL. Every heading and label here says
 * "GenLayer Evidence Witness" so the two are never confused.
 *
 * NOTHING ON THIS PAGE IS FABRICATED. The server-rendered HTML carries the explanation, the
 * contract address (a fact from `deployment.json`) and empty forms - no record, no status, no
 * example row. Every value in a result card, the criteria list and the lifecycle comes from an RPC
 * response received in this session, and a failed read shows the RPC's own error text.
 *
 * THE PAGE HOLDS NO KEY AND SIGNS NOTHING. `witness(...)` is operator-only on the contract, so the
 * "Request a check" form posts to `/api/witness-submit`, a rate-limited relay that signs with the
 * Provek operator key on the server. Everything the page then shows is still read from the chain. */

import { useEffect, useRef, useState } from "react";
import { Page, Strip } from "../components/Chrome";
import { readTransaction, readView } from "../witnessChain";
import {
  CONTRACT_ADDRESS, DEFAULT_SUBJECT, NETWORK_LABEL, UNDETERMINED_EXPLANATION,
  explorerAddressUrl, explorerTxUrl, expectedLabel, matchRecords, parseIdList,
  parseTxHash, readableError, relayOutcome, resultCard, safeHref, summariseTx, trackStep, trackUrl, txFromQuery,
} from "../witnessView.js";
import type { Match, Observed, ResultCard, TxFound, TxSummary } from "../witnessView.js";

const POLL_MS = 4000;

type Cards = Extract<ResultCard, { ok: true }>;

function Badge({ card }: { card: Cards }) {
  const text = card.result ?? "not returned";
  const tone = card.result === "PASS" ? "var(--c-wash-pass)" : card.result === "FAIL" ? "var(--c-wash-warn)" : "var(--c-wash-info)";
  return (
    <span
      className="inline-block font-mono text-xs border border-[var(--color-line-2)] px-2 py-0.5"
      style={{ background: tone }}
    >
      {text}
      {card.recognised ? "" : " (not PASS or FAIL)"}
    </span>
  );
}

function Mono({ children }: { children: React.ReactNode }) {
  return <span className="font-mono text-xs break-all">{children}</span>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-[11rem_1fr] gap-x-4 gap-y-0.5 py-1.5 border-b border-[var(--color-line)] last:border-b-0">
      <dt className="text-xs text-[var(--color-ink-3)]">{label}</dt>
      <dd className="text-sm min-w-0">{children}</dd>
    </div>
  );
}

function orNotReturned(v: string | null) {
  return v === null ? <em className="text-[var(--color-ink-3)]">not returned</em> : v === "" ? <em className="text-[var(--color-ink-3)]">(empty)</em> : <Mono>{v}</Mono>;
}

export function RecordCard({ card }: { card: Cards }) {
  const href = safeHref(card.evidence_url);
  return (
    <div className="bg-[var(--color-paper)] border border-[var(--color-line)] px-4 py-2" data-witness-id={card.witnessId}>
      <dl>
        <Field label="Result"><Badge card={card} /></Field>
        <Field label="Criterion">{orNotReturned(card.criterion)}</Field>
        <Field label="Evidence URL">
          {card.evidence_url === null ? orNotReturned(null) : href ? (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-[var(--color-accent)] hover:underline break-all text-xs font-mono">{card.evidence_url}</a>
          ) : <Mono>{card.evidence_url}</Mono>}
        </Field>
        <Field label="Expected">{card.expected === null ? orNotReturned(null) : card.expected === "" ? <em className="text-[var(--color-ink-3)]">{expectedLabel(card)}</em> : <Mono>{card.expected}</Mono>}</Field>
        <Field label="Observation">{orNotReturned(card.observation)}</Field>
        <Field label="Evidence digest">{orNotReturned(card.evidence_digest)}</Field>
        <Field label="Checked at">{orNotReturned(card.checked_at)}</Field>
        <Field label="Witness id"><Mono>{card.witnessId}</Mono></Field>
      </dl>
    </div>
  );
}

type Lookup =
  | { state: "idle" }
  | { state: "loading" }
  | { state: "error"; why: string }
  | { state: "empty"; subject: string }
  | { state: "ready"; subject: string; rows: Row[] };

type Row = { id: string; card: ResultCard } | { id: string; error: string };

async function fetchRows(ids: string[]): Promise<Row[]> {
  return Promise.all(
    ids.map(async (id): Promise<Row> => {
      try {
        const card = resultCard(id, await readView("get_result", [id]));
        return { id, card };
      } catch (e) {
        return { id, error: readableError(e) };
      }
    }),
  );
}

function LookUp() {
  const [subject, setSubject] = useState(DEFAULT_SUBJECT);
  const [lookup, setLookup] = useState<Lookup>({ state: "idle" });
  const seq = useRef(0);

  const run = (s: string) => {
    const subj = s.trim();
    if (!subj) return;
    const mine = ++seq.current;
    setLookup({ state: "loading" });
    readView("list_by_subject", [subj])
      .then(async (raw) => {
        const parsed = parseIdList(raw);
        if (!parsed.ok) return mine === seq.current && setLookup({ state: "error", why: parsed.why });
        if (parsed.ids.length === 0) return mine === seq.current && setLookup({ state: "empty", subject: subj });
        const rows = await fetchRows(parsed.ids);
        if (mine === seq.current) setLookup({ state: "ready", subject: subj, rows });
      })
      .catch((e) => mine === seq.current && setLookup({ state: "error", why: readableError(e) }));
  };

  useEffect(() => { run(DEFAULT_SUBJECT); /* eslint-disable-next-line */ }, []);

  return (
    <section aria-labelledby="lookup-h" className="mt-10">
      <h2 id="lookup-h" className="text-lg font-semibold tracking-tight">Look up records for a subject</h2>
      <p className="mt-1 text-sm text-[var(--color-ink-2)]">
        Calls the contract&apos;s <code className="font-mono text-xs">list_by_subject</code> and then{" "}
        <code className="font-mono text-xs">get_result</code> for each id it returns.
      </p>
      <form
        className="mt-3 flex flex-wrap gap-2"
        onSubmit={(e) => { e.preventDefault(); run(subject); }}
      >
        <label htmlFor="wit-subject" className="sr-only">Subject id</label>
        <input
          id="wit-subject"
          value={subject}
          onInput={(e) => setSubject((e.target as HTMLInputElement).value)}
          className="flex-1 min-w-[16rem] border border-[var(--color-line-2)] bg-[var(--color-paper)] px-3 min-h-11 font-mono text-sm"
          spellCheck={false}
          autoComplete="off"
        />
        <button type="submit" className="text-sm border border-[var(--color-line-2)] px-3.5 min-h-11 hover:bg-[var(--color-paper-2)]">
          Look up
        </button>
      </form>
      <div className="mt-4" aria-live="polite">
        {lookup.state === "idle" && null}
        {lookup.state === "loading" && <p className="text-sm text-[var(--color-ink-3)]">Reading from Bradbury...</p>}
        {lookup.state === "error" && (
          <Strip tone="warn"><strong>The read failed.</strong> {lookup.why}</Strip>
        )}
        {lookup.state === "empty" && <p className="text-sm">No witness records for this subject yet.</p>}
        {lookup.state === "ready" && (
          <div className="space-y-3">
            <p className="text-xs text-[var(--color-ink-3)]">
              {lookup.rows.length} record{lookup.rows.length === 1 ? "" : "s"} for{" "}
              <code className="font-mono">{lookup.subject}</code>, as returned by the contract just now.
            </p>
            {lookup.rows.map((r) =>
              "error" in r ? (
                <Strip key={r.id} tone="warn">
                  <strong>Could not read record</strong> <Mono>{r.id}</Mono>: {r.error}
                </Strip>
              ) : r.card.ok ? (
                <RecordCard key={r.id} card={r.card} />
              ) : (
                <Strip key={r.id} tone="warn"><strong>Unreadable record</strong> <Mono>{r.id}</Mono>: {r.card.why}</Strip>
              ),
            )}
          </div>
        )}
      </div>
    </section>
  );
}

type Track = {
  hash: string;
  lifecycle: Observed[];
  tx: TxFound | null;
  notFound: "not_indexed_yet" | "absent" | null;
  notIndexedSeconds: number | null;
  error: string | null;
  done: "terminal" | "limit" | null;
  match: Match | null;
  matchError: string | null;
};

function Tracker() {
  const [input, setInput] = useState("");
  const [badInput, setBadInput] = useState<string | null>(null);
  const [track, setTrack] = useState<Track | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const gen = useRef(0);

  const stop = () => { gen.current++; if (timer.current) clearTimeout(timer.current); };
  useEffect(() => stop, []);

  const start = (raw: string) => {
    stop();
    const hash = parseTxHash(raw);
    if (!hash) {
      setBadInput("That is not a transaction hash: expected 0x followed by 64 hexadecimal characters.");
      setTrack(null);
      return;
    }
    setBadInput(null);
    const mine = gen.current;
    const startedAt = Date.now();
    let lifecycle: Observed[] = [];
    let matched = false;
    setTrack({ hash, lifecycle, tx: null, notFound: null, notIndexedSeconds: null, error: null, done: null, match: null, matchError: null });

    const tick = async () => {
      let read: TxSummary;
      try {
        read = summariseTx(await readTransaction(hash));
      } catch (e) {
        read = { ok: false, why: readableError(e) };
      }
      if (mine !== gen.current) return;
      const step = trackStep({ startedAt, lifecycle }, read, Date.now());
      lifecycle = step.lifecycle;
      const { tx, done } = step;
      setTrack((t) => (t ? { ...t, lifecycle, tx: tx ?? t.tx, notFound: step.notFound, notIndexedSeconds: step.notIndexedSeconds, error: step.error, done } : t));

      if (tx && tx.succeeded && tx.forThisContract && !matched) {
        matched = true;
        findRecords(tx).then(
          (m) => mine === gen.current && setTrack((t) => (t ? { ...t, match: m } : t)),
          (e) => { matched = false; if (mine === gen.current) setTrack((t) => (t ? { ...t, matchError: readableError(e) } : t)); },
        );
      }
      if (!done) timer.current = setTimeout(tick, POLL_MS);
    };
    tick();
  };

  useEffect(() => {
    const q = txFromQuery(window.location.search);
    if (q !== null) { setInput(q); start(q); }
    /* eslint-disable-next-line */
  }, []);

  const t = track;
  const tx = t?.tx ?? null;
  return (
    <section aria-labelledby="track-h" className="mt-10">
      <h2 id="track-h" className="text-lg font-semibold tracking-tight">Track a transaction</h2>
      <p className="mt-1 text-sm text-[var(--color-ink-2)]">
        Paste the hash of a transaction sent to the contract. The page reads its status every 4
        seconds and lists each status it observes, with the time it was first seen here.
      </p>
      <form className="mt-3 flex flex-wrap gap-2" onSubmit={(e) => { e.preventDefault(); start(input); }}>
        <label htmlFor="wit-tx" className="sr-only">Transaction hash</label>
        <input
          id="wit-tx"
          value={input}
          onInput={(e) => setInput((e.target as HTMLInputElement).value)}
          placeholder="0x..."
          className="flex-1 min-w-[16rem] border border-[var(--color-line-2)] bg-[var(--color-paper)] px-3 min-h-11 font-mono text-sm"
          spellCheck={false}
          autoComplete="off"
        />
        <button type="submit" className="text-sm border border-[var(--color-line-2)] px-3.5 min-h-11 hover:bg-[var(--color-paper-2)]">
          Track
        </button>
      </form>
      <div className="mt-4 space-y-3" aria-live="polite">
        {badInput && <Strip tone="warn">{badInput}</Strip>}
        {t && (
          <>
            <p className="text-sm">
              Transaction <Mono>{t.hash}</Mono> -{" "}
              <a href={explorerTxUrl(t.hash)} target="_blank" rel="noopener noreferrer" className="text-[var(--color-accent)] hover:underline">
                open in the Bradbury explorer
              </a>
            </p>
            {t.error && <Strip tone="warn"><strong>The last read failed.</strong> {t.error}{t.done ? "" : " Retrying."}</Strip>}
            {t.notFound === "not_indexed_yet" && (
              <Strip tone="info">Bradbury has not indexed this transaction yet ({t.notIndexedSeconds} s); it answered UNINITIALIZED. A hash that was only just submitted can take a moment to appear. Still watching.</Strip>
            )}
            {t.notFound === "absent" && (
              <Strip tone="info">Bradbury has no transaction with this hash (it answered UNINITIALIZED for over a minute). It may not have been submitted, or the hash is wrong.</Strip>
            )}
            {t.lifecycle.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold">Observed lifecycle</h3>
                <ol className="mt-1 text-sm list-decimal pl-5 space-y-0.5">
                  {t.lifecycle.map((o, i) => (
                    <li key={`${i}-${o.status}`}><span className="font-mono text-xs">{o.status}</span> <span className="text-[var(--color-ink-3)]">first seen {o.at}</span></li>
                  ))}
                </ol>
              </div>
            )}
            {tx && (
              <dl className="bg-[var(--color-paper)] border border-[var(--color-line)] px-4 py-2">
                <Field label="Status now"><Mono>{tx.status ?? "not returned"}</Mono></Field>
                <Field label="Consensus result"><Mono>{tx.consensusResult ?? "not returned"}</Mono></Field>
                <Field label="Execution result"><Mono>{tx.execution ?? "not returned"}</Mono></Field>
                <Field label="Sent to">
                  <Mono>{tx.recipient ?? "not returned"}</Mono>
                  {!tx.forThisContract && <span className="text-xs"> - not the Evidence Witness contract</span>}
                </Field>
              </dl>
            )}
            {tx && tx.status === "UNDETERMINED" && <Strip tone="warn"><strong>UNDETERMINED.</strong> {UNDETERMINED_EXPLANATION}</Strip>}
            {tx && tx.status === "CANCELED" && <Strip tone="warn"><strong>CANCELED.</strong> The transaction was canceled; no record was written.</Strip>}
            {tx && (tx.status === "VALIDATORS_TIMEOUT" || tx.status === "LEADER_TIMEOUT") && (
              <Strip tone="warn"><strong>{tx.status}.</strong> The network reported a timeout for this transaction; no record is claimed here.</Strip>
            )}
            {tx && tx.settledButFailed && (
              <Strip tone="warn">
                <strong>Consensus reached, execution did not succeed.</strong> Status {tx.status} is
                about agreement among validators, not about the contract call: the execution result
                is <code className="font-mono text-xs">{tx.execution ?? "not returned"}</code>, not FINISHED_WITH_RETURN.
              </Strip>
            )}
            {t.done === "limit" && <Strip tone="info">Stopped watching after 15 minutes without a final status. The transaction may still progress; track it again to resume.</Strip>}
            {tx && tx.succeeded && !tx.forThisContract && (
              <Strip tone="info">This transaction succeeded, but it was not sent to the Evidence Witness contract, so no record is looked up for it.</Strip>
            )}
            {tx && tx.succeeded && tx.forThisContract && <MatchView t={t} call={tx.call} />}
          </>
        )}
      </div>
    </section>
  );
}

async function findRecords(tx: TxFound): Promise<Match> {
  if (!tx.call) return { kind: "no_call" };
  const parsed = parseIdList(await readView("list_by_subject", [tx.call.subject_id]));
  if (!parsed.ok) throw new Error(parsed.why);
  const rows = await fetchRows(parsed.ids);
  const cards: ResultCard[] = rows.map((r) => ("card" in r ? r.card : { ok: false, why: r.error }));
  return matchRecords(tx.call, cards);
}

function MatchView({ t, call }: { t: Track; call: TxFound["call"] }) {
  if (t.matchError) return <Strip tone="warn"><strong>Could not read the record.</strong> {t.matchError}</Strip>;
  if (!t.match) return <p className="text-sm text-[var(--color-ink-3)]">Execution succeeded; reading the record...</p>;
  const m = t.match;
  return (
    <div className="space-y-2">
      <p className="text-xs text-[var(--color-ink-3)]">
        The return value of a transaction is not exposed by the client library on Bradbury, so the
        record is identified by matching this call&apos;s arguments
        {call ? <> (<code className="font-mono">{call.criterion}</code>, its evidence URL and expected value, subject <code className="font-mono">{call.subject_id}</code>)</> : null}{" "}
        against the contract&apos;s records for that subject.
      </p>
      {m.kind === "no_call" && <Strip tone="info">The transaction&apos;s call data did not decode as <code className="font-mono text-xs">witness(...)</code>, so no record is matched.</Strip>}
      {m.kind === "none" && <Strip tone="info">Execution succeeded but no record with these arguments is listed for the subject.</Strip>}
      {m.kind === "one" && <RecordCard card={m.card} />}
      {m.kind === "several" && (
        <>
          <Strip tone="info">{m.cards.length} records carry exactly these arguments (the same check was written more than once), so which one belongs to this transaction is not determinable here. All are shown.</Strip>
          {m.cards.map((c) => <RecordCard key={c.witnessId} card={c} />)}
        </>
      )}
    </div>
  );
}

type CriteriaState = { s: "loading" } | { s: "error"; why: string } | { s: "ready"; list: string[] };

/** `supported_criteria()` read from the contract once per page load, shared by the list and the form. */
function useCriteria(): CriteriaState {
  const [state, setState] = useState<CriteriaState>({ s: "loading" });
  useEffect(() => {
    readView("supported_criteria")
      .then((v) => {
        if (Array.isArray(v) && v.every((x) => typeof x === "string")) setState({ s: "ready", list: v as string[] });
        else setState({ s: "error", why: "supported_criteria did not return a list of strings" });
      })
      .catch((e) => setState({ s: "error", why: readableError(e) }));
  }, []);
  return state;
}

function Criteria({ state }: { state: CriteriaState }) {
  if (state.s === "loading") return <span className="text-[var(--color-ink-3)]">read live from the contract when this page loads...</span>;
  if (state.s === "error") return <span>not read: {state.why}</span>;
  return <>{state.list.map((c, i) => <span key={c}>{i ? ", " : ""}<code className="font-mono text-xs">{c}</code></span>)}</>;
}

type Relay = { state: "unknown" } | { state: "enabled" } | { state: "disabled"; why: string } | { state: "unreachable"; why: string };

/** Whether the relay accepts submissions (`GET /api/witness-submit`); the read path never depends on it. */
function useRelay(): Relay {
  const [relay, setRelay] = useState<Relay>({ state: "unknown" });
  useEffect(() => {
    fetch("/api/witness-submit", { headers: { accept: "application/json" } })
      .then(async (r) => {
        const b = await r.json().catch(() => null);
        if (!r.ok || !b || typeof b.enabled !== "boolean") throw new Error(`the relay answered HTTP ${r.status} without a status object`);
        setRelay(b.enabled ? { state: "enabled" } : { state: "disabled", why: typeof b.reason === "string" ? b.reason : "no reason given" });
      })
      .catch((e) => setRelay({ state: "unreachable", why: e instanceof Error ? e.message : String(e) }));
  }, []);
  return relay;
}

type Sending = { s: "idle" } | { s: "sending" } | { s: "failed"; message: string };

function RequestCheck({ criteria }: { criteria: CriteriaState }) {
  const relay = useRelay();
  const [subject, setSubject] = useState(DEFAULT_SUBJECT);
  const [criterion, setCriterion] = useState("");
  const [url, setUrl] = useState("");
  const [expected, setExpected] = useState("");
  const [sending, setSending] = useState<Sending>({ s: "idle" });

  const list = criteria.s === "ready" ? criteria.list : [];
  const chosen = criterion || list[0] || "";
  const needsExpected = chosen === "artifact_hash";
  const disabled = relay.state === "disabled" || criteria.s !== "ready" || sending.s === "sending";

  const submit = async (e: { preventDefault(): void }) => {
    e.preventDefault();
    if (disabled) return;
    setSending({ s: "sending" });
    try {
      const r = await fetch("/api/witness-submit", {
        method: "POST",
        headers: { "content-type": "application/json", accept: "application/json" },
        body: JSON.stringify({ subject_id: subject, criterion: chosen, evidence_url: url, expected: needsExpected ? expected : "" }),
      });
      const body = await r.json().catch(() => null);
      const outcome = relayOutcome(r.status, body);
      if (outcome.ok) window.location.assign(trackUrl(outcome.hash));
      else setSending({ s: "failed", message: `${outcome.status}: ${outcome.message}` });
    } catch (err) {
      setSending({ s: "failed", message: `The request did not reach the relay: ${err instanceof Error ? err.message : String(err)}` });
    }
  };

  const input = "w-full border border-[var(--color-line-2)] bg-[var(--color-paper)] px-3 min-h-11 font-mono text-sm";
  return (
    <section aria-labelledby="request-h" className="mt-10">
      <h2 id="request-h" className="text-lg font-semibold tracking-tight">Request a check</h2>
      <p className="mt-1 text-sm text-[var(--color-ink-2)]">
        Asks the contract&apos;s validators to fetch an evidence URL and agree on PASS or FAIL. When
        the request is accepted you are taken to its lifecycle below.
      </p>
      <p className="mt-1 text-xs text-[var(--color-ink-3)]">
        Requests are signed by the Provek operator key through a rate-limited relay because the contract
        only accepts the operator as caller; results are produced by GenLayer validators and read
        directly from the chain.
      </p>
      {relay.state === "disabled" && (
        <div className="mt-3"><Strip tone="warn"><strong>Submissions are temporarily disabled.</strong> {relay.why}. Looking up and tracking still work.</Strip></div>
      )}
      {relay.state === "unreachable" && (
        <div className="mt-3"><Strip tone="info">The relay&apos;s status could not be read ({relay.why}). You can still try to submit; its answer will be shown here.</Strip></div>
      )}
      {criteria.s === "error" && (
        <div className="mt-3"><Strip tone="warn"><strong>The supported criteria could not be read</strong>, so the form is off: {criteria.why}</Strip></div>
      )}
      <form className="mt-3 space-y-3" onSubmit={submit}>
        <div>
          <label htmlFor="wit-req-subject" className="text-xs text-[var(--color-ink-3)]">Subject id (1 to 256 characters)</label>
          <input id="wit-req-subject" value={subject} onInput={(e) => setSubject((e.target as HTMLInputElement).value)} className={input} spellCheck={false} autoComplete="off" required maxLength={256} />
        </div>
        <div>
          <label htmlFor="wit-req-criterion" className="text-xs text-[var(--color-ink-3)]">Criterion</label>
          <select id="wit-req-criterion" value={chosen} onChange={(e) => setCriterion((e.target as HTMLSelectElement).value)} className={input} disabled={criteria.s !== "ready"}>
            {criteria.s === "loading" && <option value="">reading the contract...</option>}
            {criteria.s === "error" && <option value="">not read</option>}
            {list.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="wit-req-url" className="text-xs text-[var(--color-ink-3)]">Evidence URL (http or https, at most 2048 characters)</label>
          <input id="wit-req-url" type="url" value={url} onInput={(e) => setUrl((e.target as HTMLInputElement).value)} className={input} placeholder="https://provek.dev/" spellCheck={false} autoComplete="off" required maxLength={2048} />
        </div>
        {needsExpected && (
          <div>
            <label htmlFor="wit-req-expected" className="text-xs text-[var(--color-ink-3)]">Expected digest</label>
            <input id="wit-req-expected" value={expected} onInput={(e) => setExpected((e.target as HTMLInputElement).value)} className={input} spellCheck={false} autoComplete="off" required aria-describedby="wit-req-expected-hint" />
            <p id="wit-req-expected-hint" className="mt-1 text-xs text-[var(--color-ink-3)]">sha256 of the exact bytes at the URL, 64 hex</p>
          </div>
        )}
        <button type="submit" disabled={disabled} className="text-sm border border-[var(--color-line-2)] px-3.5 min-h-11 hover:bg-[var(--color-paper-2)] disabled:opacity-50">
          {sending.s === "sending" ? "Sending..." : "Request check"}
        </button>
      </form>
      <div className="mt-3" aria-live="polite">
        {sending.s === "failed" && <Strip tone="warn"><strong>The request was not accepted.</strong> {sending.message}</Strip>}
      </div>
    </section>
  );
}

export default function Witness() {
  const criteria = useCriteria();
  return (
    <Page>
      <div className="max-w-[46rem]">
        <h1 className="text-2xl font-semibold tracking-tight">GenLayer Evidence Witness</h1>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          An Intelligent Contract on GenLayer. Each validator independently fetches an evidence URL
          and the validators must agree on PASS or FAIL before a record is written. This page reads
          that contract, shows what it holds, and can request a new check through a relay.
        </p>
        <p className="mt-2 text-xs text-[var(--color-ink-3)]">
          Not to be confused with Provek&apos;s own WitnessRecord pages under{" "}
          <code className="font-mono">/w/</code>, which are a different thing.
        </p>

        <dl className="mt-5 bg-[var(--color-paper)] border border-[var(--color-line)] px-4 py-2">
          <Field label="Contract">
            <Mono>{CONTRACT_ADDRESS}</Mono>{" "}
            <a href={explorerAddressUrl(CONTRACT_ADDRESS)} target="_blank" rel="noopener noreferrer" className="text-[var(--color-accent)] hover:underline text-xs">explorer</a>
          </Field>
          <Field label="Network">{NETWORK_LABEL}</Field>
          <Field label="Supported criteria"><Criteria state={criteria} /></Field>
        </dl>

        <RequestCheck criteria={criteria} />
        <LookUp />
        <Tracker />

        <p className="mt-10 text-xs text-[var(--color-ink-3)]">
          Reads go directly from your browser to the Bradbury RPC (rpc-bradbury.genlayer.com); there
          is no Provek server in between. Only a request for a new check goes through Provek&apos;s relay. Bradbury is a test network: a record here is a testnet
          fact, not a Provek score.
        </p>
      </div>
    </Page>
  );
}
