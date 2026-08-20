#!/usr/bin/env python3
"""T-F7 - perform the Validation Registry check and write down what it found.

WHAT IT DOES. One anonymous read of the ERC-8004 deployment list, classified by
`src/transport/erc8004_deployment.py`, written to `public/erc8004/validation_registry.json`. That
record is the evidence the liveness obligation `validation_target_watch` is swept against
(`src/liveness/commitments.py`); this script is the act that satisfies it, and the remedy the
finding names when it has not been performed.

IT ALWAYS WRITES, AND IT WRITES TWO BLOCKS, WHICH TOOK THREE DRAFTS TO ARRIVE AT.

Draft one wrote whatever the latest run established, over the top. Trace the remedy on a day when
raw.githubusercontent is 5xx: the operator meets a `SILENCE` finding, runs the remedy exactly as
printed, and the run replaces `no_target` with a non-measurement, turns two assertions about the
real tree red, and leaves a dirty file that `./scripts/push.sh` - step three of the same remedy -
then refuses to send. A false red at the moment somebody performs the habit, with the recovery step
written down nowhere.

Draft two refused to overwrite a measurement, and was worse. The record went on saying `no_target`
inside its interval while a run had just reported that the deployment list was unrecognisable - and
`sweep()` returned NOTHING. A green gate meaning "did not look", for up to twenty-three days, in
the module built to forbid precisely that, introduced by the fix for draft one. The only witness
was the stdout of a script nothing runs on a clock.

Both drafts were choosing which of two facts to keep. There are two facts, so there are two blocks:
`measurement` holds the last run that ESTABLISHED something and is what the interval rides, so a
failed run never advances the clock; `last_attempt` holds what the last run did, whatever that was,
and is what the gate reports the same minute. A record whose runs have all failed carries
`measurement: null`, which is a readable statement that no measurement has ever been taken - not a
missing field, and not a stale answer wearing a fresh timestamp. Both defects found by Fable, one
round apart, the second inside the fix for the first.

THE EXIT CODE IS NON-ZERO ON GOOD NEWS TOO. `target_present` means the external blocker on T-2.15b
has lifted, and that demands a decision from a person - it is not a state to pass through quietly.
A blocker that lifts silently is how "cannot" becomes "forgot", which is the whole reason this
script exists.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# The repository root, wherever this clone happens to live - the same reason `scripts/cohort.py`
# gives: an absolute path would make the check runnable on one machine, and a check anyone can
# repeat is the only kind worth citing.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.transport.erc8004_deployment import (  # noqa: E402
    ATTEMPT,
    BLOCKED_STEP,
    MEASUREMENT,
    RAW_URL,
    RECORD,
    SOURCE_REPO,
    TargetState,
    read_source,
)

ROOT = Path(__file__).resolve().parents[1]

READING = {
    TargetState.NO_TARGET:
        "The deployment list was read and recognised, and it carries no Validation Registry "
        "address.",
    TargetState.TARGET_PRESENT:
        "The deployment list carries a Validation Registry address.",
    TargetState.NO_CLIENT:
        "No HTTP client could be launched here, so no request was made. Entirely ours.",
    TargetState.NO_ANSWER:
        "The request did not complete and no status was obtained. Whose failure that is has not "
        "been established.",
    TargetState.SOURCE_ANSWERED_NON_200:
        "The source answered and declined; the status is beside this line.",
    TargetState.ROW_NOT_CONCLUSIVE:
        "A line names validation beside an address and this reader cannot tell a deployment row "
        "from a code example. The lines are below; a person settles it, not another run.",
    TargetState.LIST_UNRECOGNISED:
        "The document answered, and an anchor registry could not be found in it - both of them ARE "
        "deployed and listed. The shape this parser reads is gone, so an absence measured here "
        "would be an absence measured with a broken instrument.",
}
"""A gloss on the state, for whoever opens the file. IT CARRIES NO INSTRUCTIONS, and the first
draft's copies did - the same "name the risk, correct the documents" sentence lived here and in
`commitments._target_findings`, already diverging, with the weaker of the two serialised into the
artefact (L-2). What to DO about a reading belongs to the finding, in one place. Nothing reads this
key back; it is written for a person, and saying so is the difference between that and a payload
for a consumer that does not exist."""


def _measurement(read, now: datetime) -> dict:
    """The block for a run that established something. Only ever built from such a run."""
    return {
        "checked_at": now.isoformat(),
        "state": read.state.value,
        "http_status": read.http_status,
        "reading": READING[read.state],
        "validation_registry_addresses": list(read.validation_addresses),
        # The document's own rows behind those addresses. An address does not say which chain it is
        # on - the document puts that in a heading - and an operator handed a bare address could
        # schedule T-2.15b against a testnet.
        "validation_registry_rows": list(read.validation_rows),
        # The positive control, published rather than kept private: a reader can see that the
        # instrument found the two registries that ARE deployed before believing it about the one
        # that is not.
        "anchors": {
            "identity_registry_addresses": list(read.identity_addresses),
            "reputation_registry_addresses": list(read.reputation_addresses),
        },
        "document_sha256": read.document_sha256,
    }


CARRIED = "carried"
BLOCKED_WRITE = "blocked"


def _held_measurement(path: Path) -> tuple[str, object]:
    """What to do with the measurement already on disk. Returns `(CARRIED, block)` or
    `(BLOCKED_WRITE, reason)`.

    CARRIED FORWARD VERBATIM, INCLUDING WHEN IT IS MALFORMED. Read as raw JSON rather than rebuilt
    from `read_record`, which keeps only what the gate needs: reconstructing it would quietly drop
    the anchors and the digest, and a measurement that loses its own positive control on the way
    past a failed run is not the measurement it claims to be. A block that is present and broken is
    carried too - the gate has names for its shapes, and they are true.

    AND WHERE IT CANNOT BE CARRIED, NOTHING IS WRITTEN. A draft of this returned None whenever the
    block was not a clean dict, and `main()` then wrote `measurement: null`, whose meaning is "no
    measurement has ever been taken". So one failed run over a record that was merely unreadable -
    corrupt JSON, an epoch integer where a timestamp belongs, or the previous revision's one-block
    shape - turned `NOT ASSESSED: could not be read` into `SILENCE: has never presented evidence of
    participation ... a FINDING, not missing data`. Upgrading "we could not look" into "it never
    happened" is invariant 1 with the sign flipped, and it is the exact collapse
    `Obligation.evidence_unreadable` was added to prevent. Found by Fable.

    The refusal is safe where the first draft's was not: the file is left BYTE-IDENTICAL, so the
    tree stays clean and `./scripts/push.sh` - the last step of the remedy that printed this - has
    nothing to refuse.
    """
    if not path.exists():
        return CARRIED, None                      # nothing held; "never measured" is simply true
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return BLOCKED_WRITE, f"it could not be read ({type(exc).__name__})"
    if not isinstance(doc, dict):
        return BLOCKED_WRITE, "its top level is not an object"
    if MEASUREMENT not in doc:
        return BLOCKED_WRITE, (f"it carries no `{MEASUREMENT}` key - an older shape, or something "
                               "else wrote it")
    return CARRIED, doc[MEASUREMENT]


def main() -> int:
    read = read_source()
    now = datetime.now(timezone.utc)
    path = ROOT / RECORD

    print(f"{read.state.value} (HTTP {read.http_status})")
    print(READING[read.state])
    for row in read.validation_rows:
        print(f"  {row}")

    # THE RUN ALWAYS GOES INTO THE RECORD; ONLY A RUN THAT MEASURED SOMETHING TOUCHES THE CLOCK.
    if read.state.is_measured:
        measurement = _measurement(read, now)
    else:
        verdict, held = _held_measurement(path)
        if verdict is BLOCKED_WRITE:
            print(f"NOT WRITTEN: this run established nothing and {RECORD.as_posix()} could not be "
                  f"read well enough to carry its measurement forward - {held}. Writing would "
                  "replace 'we could not read this' with 'this never happened'. The file is "
                  "untouched, so the tree stays clean and the gate goes on naming the state it "
                  "actually found.")
            return 1
        measurement = held
        where = (f"{measurement['state']} of {measurement['checked_at']}"
                 if isinstance(measurement, dict) else "none ever taken")
        print(f"MEASUREMENT NOT ADVANCED: this run established nothing, so the interval still "
              f"rides the last one ({where}) and the gate reports this attempt instead.")

    record = {
        "generated_by": "scripts/watch_validation_registry.py",
        "blocks": BLOCKED_STEP,
        "source_repo": SOURCE_REPO,
        "source_url": RAW_URL,
        ATTEMPT: {"at": now.isoformat(), "state": read.state.value,
                  "http_status": read.http_status, "reading": READING[read.state],
                  # The lines this run could not classify travel with THIS run, because the finding
                  # that quotes them is about this run. Taking them from the measurement block
                  # printed "lines the record does not carry" in the only case that reaches it.
                  "validation_registry_rows": list(read.validation_rows)},
        MEASUREMENT: measurement,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"written to {RECORD.as_posix()}")
    # NO_TARGET is the only state with nothing for anybody to act on. `target_present` needs a
    # decision and every other state needs the check re-run, so both are a non-zero exit.
    return 0 if read.state is TargetState.NO_TARGET else 1


if __name__ == "__main__":
    raise SystemExit(main())
