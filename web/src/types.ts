/** Shapes of the artefacts the validator publishes.
 *
 * These mirror the machine record exactly. Decision D-10: the human surface reads the same JSON a
 * machine reads, so the page can never drift from the record we ask people to trust. If a field is
 * missing here, it is missing in the artefact - we do not synthesise it for display. */

export type AbsentReason = "nothing_qualified" | "check_did_not_run" | "unreadable";

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
