/** Types for `witnessView.js`. Plain JavaScript so the gate runs the bytes the bundle ships. */
export declare const CONTRACT_ADDRESS: string;
export declare const CHAIN_ID: number;
export declare const NETWORK_LABEL: string;
export declare const EXPLORER_BASE: string;
export declare const DEFAULT_SUBJECT: string;
export declare const TERMINAL_STATUSES: string[];
export declare const KNOWN_STATUSES: string[];
export declare const UNDETERMINED_EXPLANATION: string;
export declare function parseTxHash(input: unknown): string | null;
export declare function txFromQuery(search: unknown): string | null;
export declare function explorerTxUrl(hash: string): string;
export declare function explorerAddressUrl(address: string): string;
export declare function parseIdList(raw: unknown): { ok: true; ids: string[] } | { ok: false; why: string };
export type ResultCard =
  | { ok: false; why: string }
  | {
      ok: true; witnessId: string; recognised: boolean;
      subject_id: string | null; criterion: string | null; evidence_url: string | null;
      expected: string | null; result: string | null; evidence_digest: string | null;
      checked_at: string | null; observation: string | null;
    };
export declare function resultCard(witnessId: string, raw: unknown): ResultCard;
export declare function safeHref(url: unknown): string | null;
export declare function expectedLabel(card: { expected: string | null }): string;
export declare function readableError(err: unknown): string;
export type Observed = { status: string; at: string };
export declare function observe(lifecycle: Observed[], statusName: unknown, atMs: number): Observed[];
export declare function isTerminal(statusName: unknown): boolean;
export type WitnessCall = { subject_id: string; criterion: string; evidence_url: string; expected: string };
export type TxFound = {
      ok: true; found: true; status: string | null; consensusResult: string | null;
      execution: string | null; sender: string | null; recipient: string | null;
      forThisContract: boolean; succeeded: boolean; settledButFailed: boolean;
      createdAt: string | null; call: WitnessCall | null;
    };
export type TxSummary = { ok: false; why: string } | { ok: true; found: false } | TxFound;
export declare function summariseTx(tx: unknown, contractAddress?: string): TxSummary;
export declare function callOf(tx: unknown): WitnessCall | null;
export type Match =
  | { kind: "no_call" } | { kind: "none" }
  | { kind: "one"; card: Extract<ResultCard, { ok: true }> }
  | { kind: "several"; cards: Extract<ResultCard, { ok: true }>[] };
export declare function matchRecords(call: WitnessCall | null, cards: ResultCard[]): Match;
export declare const NOT_INDEXED_GRACE_MS: number;
export declare const WATCH_LIMIT_MS: number;
export type TrackStepResult = {
  lifecycle: Observed[]; tx: TxFound | null; notFound: "not_indexed_yet" | "absent" | null;
  notIndexedSeconds: number | null; error: string | null; done: "terminal" | "limit" | null;
};
export declare function trackStep(
  prev: { startedAt: number; lifecycle: Observed[] }, read: TxSummary, nowMs: number, limitMs?: number,
): TrackStepResult;
