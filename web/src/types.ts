/** Shapes of the artefacts the validator publishes.
 *
 * These mirror the machine record exactly. Decision D-10: the human surface reads the same JSON a
 * machine reads, so the page can never drift from the record we ask people to trust. If a field is
 * missing here, it is missing in the artefact - we do not synthesise it for display. */

export type AbsentReason =
  | "nothing_qualified"
  | "check_did_not_run"
  | "unreadable"
  | "no_evidence_in_window"
  | "apparatus_absent";

export interface Operation {
  operation: string;
  /** Either "L0".."L5", or an absent reason. Never a number, never blank. */
  level: string;
  measured: boolean;
  /** Computed by the scorer, armed by a law, and dropped at the boundary until 2026-08-20
   *  (Fable, R3). null when the operation was not measured: confidence is a property of a
   *  measurement, and the word "measured" beside `measured: false` is a contradiction. */
  confidence: "measured" | "inferred" | null;
  limiters_applied: string[];
}

export interface Coverage {
  inspected: string[];
  out_of_reach: Record<string, string>;
  unknown_shape: string;
}

export interface Passport {
  schema_version: string;
  subject_id: string;
  binding_strength: "strong" | "weak";
  binding_flags: string[];
  issued_at: string;
  valid_until: string;
  status: string;
  provenance: {
    protocol_version: string;
    profile_version: string;
    evidence_window_days: number;
  };
  verified: {
    operations: Operation[];
    /** null means NOT MEASURED. It is never a zero. */
    projection: number | null;
    projection_absent_reason: AbsentReason | null;
    /** The measured quantities a level was built from. Publishing them is what makes
     *  "the evidence behind every number" a true sentence rather than an aspiration. */
    observations: Record<string, Observation | string | null>;
    control_map_valid: boolean;
    control_map_cap: number | null;
    coverage: Coverage;
  };
  self_reported: Record<string, unknown>;
  accountability: {
    emergency_stop: Fact;
    claims_addressee: Fact;
    insurance: Fact;
    dispute_path: Fact;
  };
  /** Phase 2 - the subject's own order-intake channel (specification 4.2-bis point 1). Same
   *  guarantee as `accountability`: self-declared, `confidence` is always "assumed", and it plays
   *  no part in `verified` above - reading it can never change the score. */
  service: {
    order_url: Fact;
    offering: Fact;
    pricing_url: Fact;
    terms_url: Fact;
  };
  /** Phase 2 - PLATFORM_OBSERVED reachability of `service.order_url` (specification 4.2-bis point
   *  2). `declared` answers "was there a URL to even try"; the rest of the shape is `Fact`'s own
   *  four worlds for whatever the GET found - `value` is the reachable boolean (or null if the
   *  check never had anything to check, or could not run), `confidence` is "measured" here (this
   *  collector performed the observation itself), never "assumed". */
  service_endpoint: Fact & { declared: boolean; checked_at: string | null };
  /** Phase 2 - WitnessRecord v0 entries for this subject (specification 4.2-bis point 4, the
   *  D-05 slot), in the order they were run. Outside `verified` for the same reason `service` is:
   *  a fixed-fee witnessing event is not evidence of autonomy. Each entry is DISPLAY-ORIENTED -
   *  the full record (criterion, evidence_digest) lives only at its own `url`, never duplicated
   *  in full here. Empty for a subject nobody has jointly asked to witness yet - not a missing
   *  field, an honest empty history. */
  task_history: TaskHistoryEntry[];
  mandate_ref: string | null;
  verifier_affiliation: string;
  disclaimer: string;
}

export interface RegistryRow {
  subject_id: string;
  status: string;
  projection: number | null;
  projection_absent_reason: AbsentReason | null;
  protocol_version: string;
  valid_until: string;
  passport_ref: string;
  /** Read from the artefact, never printed by the template (Fable, R4). The interface used to
   *  assert `affiliated` on every row, which is true for eight rows and libel on the ninth. */
  verifier_affiliation: string;
  /** Phase 2 (specification 4.2-bis). The subject's declared `order_url`, or `null` if never
   *  declared - read straight off the row, never re-derived from a passport fetch the registry
   *  page does not make. */
  service_url: string | null;
  /** The LATEST anonymous GET result against `service_url`, or `null` when no URL was declared or
   *  the check has never run. Never a proxy for the score. */
  service_reachable: boolean | null;
  /** WHEN THIS ROW WAS ACTUALLY MEASURED (T-76 ruling, Fable, 2026-09-05) - the passport's own
   *  `issued_at`, distinct from the registry document's single `generated_at`. A row carried
   *  forward unread (budget exhausted, or a `PROVEK_ONLY` run naming a different subject) keeps
   *  its OLD `issued_at` while every other row in the same file gets a fresh one; a page that
   *  prints only `generated_at` reports a carried-forward row as measured today, which is the
   *  same anonymity-adjacent lie ABI-5-3 was written against, moved from "who read it" to "when".
   *  `null` only for a row published before this field existed. */
  issued_at: string | null;
}

export interface Registry {
  generated_at: string;
  disclaimer: string;
  count: number;
  subjects: RegistryRow[];
}

/** Schema 2.0.0. A value, or the reason none was established - never a bare null.
 *
 * `measured: true, value: null` is the honest "there is none": someone looked. `measured: false`
 * means nobody did, and says which of the three reasons applies. Under 1.0.0 both were the same
 * null and the front door rendered them inconsistently - which is how the defect was found. */
export interface Fact {
  value: string | boolean | null;
  measured: boolean;
  reason: string | null;
  /** Which register a measured value belongs to. `assumed` is the honest one for this block:
   *  who answers a claim is not observable from outside, so a completed check establishes what
   *  the subject SAYS, never what we verified. */
  confidence: "measured" | "inferred" | "assumed" | null;
}

/** Phase 2 - WitnessRecord v0's projection onto a passport (specification 4.2-bis point 4). The
 *  full record - `criterion`, `evidence_digest` - lives only at `url`; this is deliberately not
 *  the whole schema, the same "one canonical document per fact" reasoning `mandate_ref` already
 *  follows by pointing at a document rather than embedding it. */
export interface TaskHistoryEntry {
  witness_id: string;
  criterion_type: string;
  result: "PASS" | "FAIL";
  checked_at: string;
  url: string;
}

/** The pipeline's slug, and deliberately the same derivation.
 *
 * `git:whiteknightonhorse/APIbase` -> `git_whiteknightonhorse_APIbase`. The passport JSON is
 * written under this name by `FileTransport`, so a page URL and its machine record cannot drift
 * apart: one rule, two consumers. */
export function slug(subjectId: string): string {
  return subjectId.replace(/[:/]/g, "_");
}

/** Status BY TIME, computed at read time — and it has to be (A2).
 *
 * `Passport.effective_status` implements ABI-15-5 in Python: a verified record lapses to `stale`
 * on its own, with no event. The web never computed it, so a static registry generated today would
 * go on saying `verified` for ever. On 2026-09-19 every current row lapses in the machine sense
 * while the page kept the older word — "no news" and "expired" rendered identically, which is the
 * founding defect in its temporal form.
 *
 * DESIGN rule 3 says nothing is computed for display. This is the recorded carve-out: staleness is
 * DEFINED as a read-time computation. A value that expires cannot be baked into the artefact that
 * expires with it. */
export function effectiveStatus(status: string, validUntil: string, now: Date = new Date()): string {
  if (status !== "verified") return status;
  return now >= new Date(validUntil) ? "stale" : "verified";
}

export function daysUntil(validUntil: string, now: Date = new Date()): number {
  return Math.ceil((new Date(validUntil).getTime() - now.getTime()) / 86_400_000);
}

/** THE BUTTON'S PREDICATE, AS CODE - not a page's own opinion, and never redecided per surface.
 *
 * `verified (by time) AND service.order_url declared AND service_endpoint.reachable == true`,
 * within the current validity window - exactly the rule specification 4.2-bis point 3 states, and
 * the one every surface that can show an "Order" link (`/registry/`, the landing page's registry
 * rail, the passport page itself) calls, rather than re-deriving it from the same three facts a
 * second way. Returns the URL to link to, or `null` - the caller never has to re-check `null`
 * against a separate boolean, because a truthy return already proved the predicate held.
 *
 * `stale` and `unverified` (and every other non-`verified` status) return `null` unconditionally,
 * even if a URL happens to be declared and was once reachable: a lapsed passport is not one this
 * project stands behind today, and the button's whole point is that continuous verification has
 * an observable price for the subject. */
export function orderLinkUrl(
  status: string,
  validUntil: string,
  serviceUrl: string | null,
  serviceReachable: boolean | null,
  now: Date = new Date(),
): string | null {
  if (effectiveStatus(status, validUntil, now) !== "verified") return null;
  if (serviceUrl === null) return null;
  if (serviceReachable !== true) return null;
  return serviceUrl;
}

/** The complement of `orderLinkUrl`: why the button is ABSENT, in the same three-way order the
 *  predicate checks them in. Never called when `orderLinkUrl` returns non-null - a reason and a
 *  link are never shown together, so this only has to explain a `null`. */
export function orderAbsentReason(
  status: string,
  validUntil: string,
  serviceUrl: string | null,
  serviceReachable: boolean | null,
  now: Date = new Date(),
): string {
  const eff = effectiveStatus(status, validUntil, now);
  if (eff === "stale") return "passport expired";
  if (eff !== "verified") return "not verified";
  if (serviceUrl === null) return "order channel not declared";
  return serviceReachable === null ? "order channel not yet checked" : "order channel not reachable";
}

export interface Observation {
  /** `identity_window_closed` is a boolean by construction (src/collector/github.py) - the
   *  other six measured fields are counts or shares (numbers). Declaring this as `number | null`
   *  was itself stale relative to the artefact it claims to mirror (D-10): nothing here checked
   *  that a boolean could reach a renderer built only for a number. */
  value: number | boolean | null;
  measured: boolean;
  absent_reason: string | null;
}

/** AI agent templates (ADR-0011, D-57, `/build/`). Mirrors exactly what `templates/emit.mjs`
 *  produces from a `SKILL.md` and its witnessed dry-run record - the same D-10 discipline every
 *  other type in this file holds itself to: the human surface reads the artefact a machine reads,
 *  never a second description of it. */
export interface TemplateSection {
  heading: string;
  html: string;
}

export interface TemplateDryRun {
  date: string;
  tool: string;
  outcome: string;
  /** The one computed figure this surface may show: `Dry run · <date> · <tool> · <outcome>`. */
  line: string;
}

export interface TemplateFaqEntry {
  q: string;
  a: string;
}

export interface Template {
  slug: string;
  title: string;
  description: string;
  license: string;
  compatibility: string;
  businessOperation: string;
  forWhom: string;
  humanRemainsFor: string;
  requires: string;
  derivedFrom: string | null;
  sections: TemplateSection[];
  /** Three fixed questions, answered in this template's own words (SPEC 3.7) - rendered visibly
   *  on the page and mirrored into a `FAQPage` JSON-LD block. */
  faq: TemplateFaqEntry[];
  /** The whole SKILL.md file, byte-identical to the source and to the raw sibling served at
   *  `/build/<slug>/SKILL.md` - `LAW-COPY-IS-THE-ARTEFACT`. */
  raw: string;
  bodySha256: string;
  datePublished: string;
  dateModified: string;
  dryRun: TemplateDryRun;
}

/** The landing page's projection of a template (T-03, D-59): enough to name it and link to it,
 *  never the whole artefact - `raw` alone is a full `SKILL.md`, and the landing is not `/build/`.
 *  Inlined under its own `window.__PROVEK__` key so the byte budget that keeps the first screen
 *  small is never spent on seven files' worth of markdown a reader has not asked to build yet. */
export type TemplateSummary = Pick<Template, "slug" | "title" | "businessOperation">;
