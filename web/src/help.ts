/** Passport clarity (phase-2 plan): unified help dictionaries for the passport's raw, machine-facing keys.
 *
 * Every entry describes the SCHEMA - what a key or a section MEANS structurally, as a fact about
 * this project's methodology - never the SUBJECT. "Declares how the collector attributed this
 * line" belongs here; "this subject uses GitHub" does not, because that is a fact about the row it
 * sits in, not about what the column means, and this dictionary is read by every passport alike.
 *
 * DATA-ORIENTED, NOT A SWITCH ON THE RENDER SIDE: a key with no entry here renders RAW - its own
 * name, no caption - rather than crashing or inventing one. This is the same "the least-effort
 * path makes the weakest claim" rule `OBS_LABEL`/`OP_LABEL` in `Passport.tsx` already hold
 * themselves to (`OBS_LABEL[key] ?? key`), applied to the two dictionaries this task adds.
 *
 * `tests/test_passport_help_covers_live_keys.py` holds both dictionaries to the ACTUAL keys the
 * pipeline emits today, read off the live registry and passports - not an invented list, so a
 * ninth key a future collector starts emitting is caught here rather than shipped as a raw,
 * uncaptioned row nobody meant to leave that way.
 */

export const SECTION_HELP: Record<string, string> = {
  self_reported: "Whatever the collector attributed to the subject's own declaration or "
    + "environment. Self-reported by construction (ABI-14-2) - never independently verified, and "
    + "never entering the score above.",
  accountability: "Who answers for this business and what stops it - deliberately outside the "
    + "ladder, which measures autonomy, not who is accountable for it.",
  service: "The subject's own order-intake channel, exactly as declared - self-reported, and "
    + "never verified beyond the one reachability check published beside it.",
  coverage: "What the human control map inspected, and what it could not reach. A map can prove "
    + "a control path exists; it can never prove that no undiscovered path exists.",
  binding: "How the subject's identity is anchored to this record, and how strong that anchor is "
    + "- a domain can be resold, a signing key can rotate.",
  task_history: "Machine-checkable acceptance criteria this project has run, by joint request of "
    + "a customer and this subject. Never on our own initiative, and never entering the score "
    + "above - a fixed-fee witnessing event is not evidence of autonomy.",
};

export const FIELD_HELP: Record<string, string> = {
  // self_reported TOP-LEVEL keys - the only ones any emitter in this tree writes
  // (src/collector/declaration.py, scripts/cohort.py). An object-valued entry (`declaration`,
  // `treasury_control`) is rendered key-by-key inside itself; this caption describes the outer key.
  source: "Which channel the collector read this subject through.",
  private: "Whether the collector could tell the repository is marked private.",
  declaration: "Provenance of the subject's own provek.json, if one was read: whether it "
    + "existed, which commit it was pinned to, and its schema version.",
  treasury_control: "The subject's own claimed treasury-control level. Self-reported, and it "
    + "never raises the treasury_control operation above or enters the projection.",

  // binding_flags (src/abs_profile/identity.py) - three values exist, ever
  transferable: "The identity can change hands without any action by the subject.",
  expirable: "The identity lapses on its own unless the subject renews it.",
  revocable: "A credential behind this identity can be rotated or replaced.",

  // coverage surfaces (src/verify/control_map.py:build_coverage) - five surfaces exist today
  github: "Commit history and authorship on the code host.",
  deployment: "Who ships a change to production.",
  server: "The running system itself, at runtime.",
  treasury: "Funds, spending rules, and who is able to move them.",
  database: "Direct access to the subject's stored data.",
};
