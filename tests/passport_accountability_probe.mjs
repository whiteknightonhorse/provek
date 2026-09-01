// D-43. `web/markdown.mjs:buildPassportMarkdown` is the OTHER assembler that writes a published
// artefact from passport data - `/p/<slug>/index.md` - and it does not go through
// `web/html_to_markdown.mjs` at all: no `stripTags`, no `NEVER_UNESCAPED`, no `decode`. Today it
// does not read `passport.accountability` either, so this probe is currently a vacuous pass - the
// hostile payload below cannot reach the output because nothing in the function looks at it. It is
// wired up anyway (Fable's ruling) so that the day someone DOES add
// `${p.accountability.claims_addressee.value}` to the template, this probe starts exercising a
// real interpolation and fails in the gate that runs on every push, not in production on
// provek.dev. Not a defence today; a tripwire for a defect that does not exist yet.
import { buildPassportMarkdown } from "../web/markdown.mjs";

// A hostile subject's declared name, shaped the way `src/collector/declaration.py` would have
// produced it BEFORE this same ruling's `FORBIDDEN_CHARS` check started refusing it outright - the
// two payloads below are exactly what that check now rejects at the source, kept here to prove the
// OTHER assembler would also have been safe had one slipped through some future second reader.
const HOSTILE_SCRIPT = "<script>alert(1)</script>";
const HOSTILE_LINK = "[urgent: verify here](https://evil.example)";

function hostilePassport(hostileValue) {
  return {
    subject_id: "git:whiteknightonhorse/example",
    status: "verified",
    issued_at: "2026-09-01T00:00:00Z",
    valid_until: "2026-10-01T00:00:00Z",
    access_channel: "public",
    verifier_affiliation: "independent",
    disclaimer: "Self-reported facts are marked as such.",
    verified: {
      projection: 42,
      projection_absent_reason: null,
      operations: [
        { operation: "deployment", level: "L2", measured: true, confidence: "measured",
          limiters_applied: [] },
      ],
    },
    // NOT YET READ by buildPassportMarkdown - see the module docstring above.
    accountability: {
      emergency_stop: { measured: false, value: null, confidence: null, reason: "check_did_not_run" },
      claims_addressee: { measured: true, value: hostileValue, confidence: "assumed", reason: null },
      insurance: { measured: false, value: null, confidence: null, reason: "check_did_not_run" },
      dispute_path: { measured: false, value: null, confidence: null, reason: "check_did_not_run" },
    },
  };
}

const out = {
  script: buildPassportMarkdown(hostilePassport(HOSTILE_SCRIPT)),
  link: buildPassportMarkdown(hostilePassport(HOSTILE_LINK)),
};
process.stdout.write(JSON.stringify(out, null, 1));
