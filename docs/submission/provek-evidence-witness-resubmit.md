# Provek Evidence Witness: resubmission

The Portal steward returned the Intelligent Contract submission on 2026-10-23. The reason, as recorded in
`DECISIONS.md` D-76: "A leader could report `fetch="error"` for a URL that served a real body; a wrong `expected`
made both sides say FAIL, the validator agreed, and the record stored the leader's false fetch state."

## The fix

The validator now agrees only if every field the record would store is equal to its own observation: URL, fetch
state, status, verdict, observation text and evidence digest (T-GLR-01, D-76). The record is written from the same
function that produced the compared tuple, so a forged leader observation no longer passes validation.

## Tests that reproduce the case

In `integrations/genlayer-witness/tests/direct/test_provek_evidence_witness.py`:

- `test_validator_rejects_a_forged_error_for_a_wrong_expected`
- `test_validator_rejects_a_forged_error_for_an_oversized_body`
- `test_validator_rejects_a_forged_error_for_url_reachable`
- `test_validator_rejects_a_forged_status_and_fetch_state`
- `test_validator_rejects_a_forged_url`
- `test_record_is_built_from_bound`

`test_url_reachable_does_not_bind_the_body` shows the honest path still agrees on a dynamic page.

## Evidence

- Contract, redeployed on Bradbury Phase 2 on 2026-10-28:
  https://scan.bradbury.genlayer.com/address/0x99C23e1794ed35b429161fBEB00967D0c81DC491
- Three live records, all FINALIZED (PASS `artifact_hash`, PASS `url_reachable`, FAIL `artifact_hash`):
  `evidence/MEASURED-017-glr-05-bradbury-phase2-deploy-and-three-records.txt`
- CI run of the merge commit: <CI_RUN_URL>
- Contract file in the mirror repository `whiteknightonhorse/provek-genlayer-witness`:
  `contracts/provek_evidence_witness.py`, at the bytes deployed from Provek commit
  `11474b4cfc94dada3a3e5301d19d1262713027ac`.
