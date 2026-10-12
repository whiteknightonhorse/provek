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
 * THE WRITE PATH IS NOT HERE. `witness(...)` is operator-only (T-PW-02); this page only reads. */

import { useEffect, useRef, useState } from "react";
import { Page, Strip } from "../components/Chrome";
import { readTransaction, readView } from "../witnessChain";
import {
  CONTRACT_ADDRESS, DEFAULT_SUBJECT, NETWORK_LABEL, UNDETERMINED_EXPLANATION,
  explorerAddressUrl, explorerTxUrl, expectedLabel, isTerminal, matchRecords, observe, parseIdList,
  parseTxHash, readableError, resultCard, safeHref, summariseTx, txFromQuery,
} from "../witnessView.js";
import type { Match, Observed, ResultCard, TxFound } from "../witnessView.js";

const POLL_MS = 4000;
/** The watch stops after this long even if no terminal status arrived - and says so. */
const WATCH_LIMIT_MS = 15 * 60 * 1000;

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
  notFound: boolean;
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
    setTrack({ hash, lifecycle, tx: null, notFound: false, error: null, done: null, match: null, matchError: null });

    const tick = async () => {
      let tx: TxFound | null = null;
      let notFound = false;
      let error: string | null = null;
      try {
        const s = summariseTx(await readTransaction(hash));
        if (!s.ok) error = s.why;
        else if (s.found) tx = s;
        else notFound = true;
      } catch (e) {
        error = readableError(e);
      }
      if (mine !== gen.current) return;
      if (tx && tx.status) lifecycle = observe(lifecycle, tx.status, Date.now());
      const terminal = !!(tx && tx.status && isTerminal(tx.status));
      const limit = Date.now() - startedAt > WATCH_LIMIT_MS;
      const done = terminal ? "terminal" : limit ? "limit" : notFound ? "terminal" : null;
      setTrack((t) => (t ? { ...t, lifecycle, tx: tx ?? t.tx, notFound, error, done: done ?? null } : t));

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
            {t.notFound && (
              <Strip tone="info">Bradbury has no transaction with this hash (it answered UNINITIALIZED). It may not have been submitted yet, or the hash is wrong.</Strip>
            )}
            {t.lifecycle.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold">Observed lifecycle</h3>
                <ol className="mt-1 text-sm list-decimal pl-5 space-y-0.5">
                  {t.lifecycle.map((o) => (
                    <li key={o.status}><span className="font-mono text-xs">{o.status}</span> <span className="text-[var(--color-ink-3)]">first seen {o.at}</span></li>
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

function Criteria() {
  const [state, setState] = useState<{ s: "loading" } | { s: "error"; why: string } | { s: "ready"; list: string[] }>({ s: "loading" });
  useEffect(() => {
    readView("supported_criteria")
      .then((v) => {
        if (Array.isArray(v) && v.every((x) => typeof x === "string")) setState({ s: "ready", list: v as string[] });
        else setState({ s: "error", why: "supported_criteria did not return a list of strings" });
      })
      .catch((e) => setState({ s: "error", why: readableError(e) }));
  }, []);
  if (state.s === "loading") return <span className="text-[var(--color-ink-3)]">read live from the contract when this page loads...</span>;
  if (state.s === "error") return <span>not read: {state.why}</span>;
  return <>{state.list.map((c, i) => <span key={c}>{i ? ", " : ""}<code className="font-mono text-xs">{c}</code></span>)}</>;
}

export default function Witness() {
  return (
    <Page>
      <div className="max-w-[46rem]">
        <h1 className="text-2xl font-semibold tracking-tight">GenLayer Evidence Witness</h1>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          An Intelligent Contract on GenLayer. Each validator independently fetches an evidence URL
          and the validators must agree on PASS or FAIL before a record is written. This page reads
          that contract and shows what it holds; it writes nothing.
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
          <Field label="Supported criteria"><Criteria /></Field>
        </dl>

        <LookUp />
        <Tracker />

        <p className="mt-10 text-xs text-[var(--color-ink-3)]">
          Reads go directly from your browser to the Bradbury RPC (rpc-bradbury.genlayer.com); there
          is no Provek server in between. Bradbury is a test network: a record here is a testnet
          fact, not a Provek score.
        </p>
      </div>
    </Page>
  );
}
