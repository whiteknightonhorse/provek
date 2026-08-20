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
    emergency_stop: boolean | null;
    claims_addressee: string | null;
    insurance: string | null;
    dispute_path: string | null;
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
}

export interface Registry {
  generated_at: string;
  disclaimer: string;
  count: number;
  subjects: RegistryRow[];
}
