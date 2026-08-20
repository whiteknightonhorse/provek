"""T-F7 - is there anywhere to publish yet? The ERC-8004 deployment list, read as a measurement.

WHY THIS IS AN INSTRUMENT AND NOT A LINE IN A PLAN. `docs/MEASUREMENT_QM1.md` recorded on
2026-08-20 that the Validation Registry - the registry ADR-0001 makes our distribution channel -
has no deployed address on any chain, so T-2.15b (on-chain publication) has no target to write to.
That blocker is EXTERNAL: it lifts on somebody else's schedule, with no event that reaches this
repository. An external blocker with no instrument pointed at it decays from "cannot" into
"forgot", and the decay is silent, which is the shape this whole project exists to catch.

WHAT IT READS. The deployment list published by `erc-8004/erc-8004-contracts`, anonymously, over
the same public channel any third party has - the form of ABI-5-3 that `src/collector/github.py`
already uses, and the strongest one: a reader holding nothing at all can repeat it. One request.

WHAT IT REFUSES TO CONCLUDE, AND WHY THE CONTROL IS THE LOAD-BEARING PART. That there is no
Validation Registry address because this parser found none. The document is somebody else's README
and its shape is theirs to change; a rewrite this parser no longer recognises would otherwise read
as `no_target` every time, for ever, and the one state it would hide is the state the watch exists
to catch. So the instrument carries a POSITIVE CONTROL: the Identity and Reputation registries are
deployed and are listed in that same list, and if their addresses cannot be found either, the
answer is `unreadable` rather than a zero (invariant 1).

THE CONTROL DOES NOT OVERRIDE A POSITIVE READING, and the ordering in `parse()` says so. If a
Validation Registry address IS found, that is a measurement, and reporting `unrecognised` over it
because the anchors happened to move would throw away a quantity the instrument is holding - the
defect `commitments.py` paid for once already in its `PARTIALLY READ` branch. The control protects
the NEGATIVE answer, which is the only one that can be produced by not looking properly.

WRITING IS STILL T-2.15b AND IS STILL NOT HERE. This module establishes whether a target exists.
It does not acquire one, does not hold a key and does not publish; `Erc8004Transport.publish`
continues to refuse, and now refuses citing this reading rather than a standing assumption.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

SOURCE_REPO = "erc-8004/erc-8004-contracts"
"""The reference implementation's own repository - the same source `docs/MEASUREMENT_QM1.md` read
when it recorded the blocker. Not a mirror and not an aggregator: the deployment list is a claim
whose only meaningful publisher is the project that deployed the contracts."""

RAW_URL = f"https://raw.githubusercontent.com/{SOURCE_REPO}/main/README.md"
"""PINNED TO `main` ON PURPOSE. A renamed default branch answers 404, and a 404 is reported below
as a refusal - never as a deployment list that happens to be empty."""

BLOCKED_STEP = "T-2.15b"
"""The step this reading gates - on-chain publication into the Validation Registry.

Named once, here, and read by the script that writes the record and by the gate that sweeps it. A
status file that does not say what it BLOCKS is a fact nobody can act on, and the identifier
spelled out in three places is the one that ends up meaning three different things."""

RECORD = Path("public/erc8004/validation_registry.json")
"""Where the reading is written down, relative to the repository root.

It sits beside the other artefacts this project emits and is deliberately NOT copied into
`web/public/data/`: nothing on provek.dev makes any claim about the Validation Registry, so
publishing this file would manufacture a claim with no reader rather than settle one."""

ADDRESS = re.compile(r"(?<![0-9a-fA-F])0x[0-9a-fA-F]{40}(?![0-9a-fA-F])")
"""An EVM address, BOUNDED AT BOTH ENDS - which the first draft was not.

Unanchored, `0x[0-9a-fA-F]{40}` does not skip a 64-digit run, it TRUNCATES one. A deployment
transaction hash, a CREATE2 salt or a bytecode digest on a line naming any of the three registries
became a fabricated forty-digit address: in the validation position a false `TARGET APPEARED`
carrying an address nobody deployed, and in an anchor position a control that passes on a document
holding no deployment addresses at all. The docstring here used to claim that the 64-digit shape
was excluded, which was the opposite of what the pattern did. Found by Fable."""

ZERO_ADDRESS = "0x" + "0" * 40
"""The canonical EVM placeholder for "not set", filtered out below rather than counted.

`- **ValidationRegistry**: 0x0000...0000 (not yet deployed)` is a row that says there is NO
deployment, and reading it as one would be a placeholder taken for an artefact - L-23's shape. It
is the same judgement as `ADDRESS` above in the other direction: both refuse to let something
address-SHAPED stand in for an address."""

IDENTITY = "identityregistry"
REPUTATION = "reputationregistry"

VALIDATION = "validationregistry"
"""The spelling that means a deployment row and nothing else. A hit here is `target_present`."""

VALIDATION_LOOSE = "validation"
"""A hit HERE IS NOT A TARGET AND IS NOT AN ABSENCE EITHER - it is `not_measured`, and the third
tier is the whole answer to a question two drafts of this module got wrong in opposite directions.

DRAFT ONE matched only `validationregistry`. A registry deployed under a row reading `Validation`
alone, or `ValidationRegistryV2`, was missed - silently, for as long as the document kept the new
name, while the anchors went on matching because they are different labels and only one of them had
to change. A miss is the expensive direction: it is the state this whole component exists to catch.

DRAFT TWO matched `validation` alone and called the cost "a false TARGET APPEARED, which is a red
one reading of the document clears". Fable priced that properly by writing the text: the section
this parser reads already contains `validationRequest(...)`, `getValidationStatus`, and an event
signature carrying an `address` argument. Give any of them a concrete example address - which
documentation routinely does - and the gate orders the operator to go and schedule on-chain
publication. A red that instructs work nobody should do is not cheaper than a silence; it is a
different way of being wrong, and it recurs.

SO THE LOOSE HIT GETS ITS OWN STATE. "A line names validation beside an address and this reader
cannot tell a deployment row from an example" is neither presence nor absence, and inventing either
would be the collapse invariant 1 forbids. It reports NOT MEASURED and quotes the lines verbatim.

THE ONE ACT THAT CLEARS IT IS AN EDIT TO THIS PARSER, with a test, and the finding says only that.
An earlier wording offered "schedule the step" as an alternative exit, which clears nothing: the
record still holds the same state and the finding fires again on every sweep. There is no
acknowledgement anywhere in this design and there deliberately is not one - an acknowledgement is a
way to mark an unread instrument as read. Found by Fable."""


class TargetState(str, Enum):
    """What the deployment list said. Two of these are measurements and four are not, and the
    difference is the whole point of the module (invariant 1)."""

    NO_TARGET = "no_target"
    """Read, recognised, and it lists no Validation Registry address. A MEASURED absence."""

    TARGET_PRESENT = "target_present"
    """At least one address is listed. This is the state the watch exists for."""

    NO_CLIENT = "check_did_not_run:no_http_client"
    """`curl` could not be launched. Entirely ours, and the first thing to rule out (L-11)."""

    NO_ANSWER = "check_did_not_run:no_answer"
    """The request did not complete: no route, DNS, timeout, a truncated reply. WHOSE FAULT THAT IS
    HAS NOT BEEN ESTABLISHED, and the name says so rather than choosing. The first draft called
    every one of these `source_refused`, which asserts a fact about somebody else's server on
    evidence that a socket did not open here - L-11 exactly, in the module that quotes it."""

    SOURCE_ANSWERED_NON_200 = "check_did_not_run:source_answered_non_200"
    """The source answered and declined - 404 after a rename, 451, a 5xx. This one IS about them,
    which is why it is a separate name; the status travels in the record beside it."""

    LIST_UNRECOGNISED = "unreadable:deployment_list_not_recognised"
    """The document answered, and an anchor registry could not be found in it - so the shape this
    parser reads is gone, and an absence measured with a broken instrument is not an absence."""

    ROW_NOT_CONCLUSIVE = "unreadable:validation_row_not_conclusive"
    """A line names validation beside an address, and this reader cannot tell a deployment row from
    a code example. Deciding it either way would be inventing a measurement; a person reads the
    quoted lines and either schedules the step or tightens the parser."""

    @property
    def is_measured(self) -> bool:
        return self in (TargetState.NO_TARGET, TargetState.TARGET_PRESENT)


MEASUREMENT = "measurement"
"""The record's block for the last run that ESTABLISHED SOMETHING - or `null` if none ever has.

TWO BLOCKS, BECAUSE THERE ARE TWO FACTS, and one draft of this file collapsed them with the worst
possible result. That draft refused to overwrite a measurement with a non-measurement - correct, and
it closed a false red - but the record then went on saying `no_target` inside its interval while a
run had just reported that the deployment list was unrecognisable, or that a row it could not
classify had appeared. The sweep returned ZERO FINDINGS. A green gate meaning "did not look", in the
module built to forbid exactly that, produced by the fix for the previous defect. Found by Fable.

So the interval rides the MEASUREMENT (nothing else is evidence of participation) and the gate
reports the ATTEMPT (a run that established nothing is news the same minute). Neither is derivable
from the other, and every state that used to be indistinguishable now has a place to be written."""

ATTEMPT = "last_attempt"
"""The record's block for the LAST RUN, whatever it established. Always rewritten."""


class RecordState(str, Enum):
    """How the RECORD FILE read - a separate axis from what the source said.

    `NEVER_CHECKED` is deliberately absent, for the reason `commitments.ReadState` gives: a missing
    file means the watch has not run, OR the file was removed, OR the checkout is partial, and
    collapsing those into one answer invents a measurement to fill a state.
    """

    READ = "read"
    FILE_ABSENT = "check_did_not_run:record_absent"
    NOT_JSON = "unreadable:not_json"
    NO_MEASUREMENT_KEY = "unreadable:no_measurement_key"
    """The `measurement` key is ABSENT, which is not the same as its being `null`. `null` is this
    project saying no measurement has ever been taken; absent is a record written by something that
    does not know the shape, and reading the second as the first is how "we could not look" becomes
    "it never happened". The mirrored state on the other block was named from the start, which is
    what made the asymmetry visible. Found by Fable."""
    NO_ATTEMPT = "unreadable:no_last_attempt"
    """No `last_attempt` block at all - a record from before this file had two axes, or one written
    by something else. Its measurement may still be perfectly readable, which is exactly why this
    cannot be silently tolerated: the run that established nothing would have nowhere to be."""
    NO_CHECKED_AT = "unreadable:no_checked_at"
    BAD_CHECKED_AT = "unreadable:checked_at_is_not_a_timestamp"
    """Reached from two places, which is why it is one name. Here, when the field is present and is
    not even a string; and from `src/liveness/commitments.py`, when it is a string that is not a
    time - because whether a string is a TIME is a question about an interval, and the interval is
    that module's. Two spellings of "the timestamp is unusable" would let a caller answer one of
    them and forget the other."""
    NO_STATE = "unreadable:no_state"
    UNKNOWN_STATE = "unreadable:state_not_recognised"
    """A state string no version of this module ever wrote. An older reader meeting a newer record
    must say so; guessing the closest match is how a vocabulary silently loses a distinction."""


@dataclass(frozen=True)
class DeploymentRead:
    """One reading of the deployment list."""

    state: TargetState
    validation_addresses: tuple[str, ...] = ()
    identity_addresses: tuple[str, ...] = ()
    reputation_addresses: tuple[str, ...] = ()
    http_status: int | None = None
    """None means no status was obtained at all, which is not the same as a status."""
    document_sha256: str | None = None
    validation_rows: tuple[str, ...] = ()
    """The document's own lines behind `validation_addresses`, verbatim. Carried so that a reading
    which unblocks T-2.15b arrives with the context an address alone does not have."""


@dataclass(frozen=True)
class RecordRead:
    """One reading of the record file. `checked_at_raw` is left AS A STRING on purpose.

    Whether that string is a time is a question about an interval, and the interval belongs to
    `src/liveness/commitments.py`. Parsing it here as well would put the same rule in two places,
    and the copy that drifts is always the one nobody is watching (L-2).
    """

    state: RecordState
    checked_at_raw: str | None = None
    """When the last MEASUREMENT was taken. None also means "none ever has been", which is a real
    state of a record whose only runs all failed - and is not the same as an unreadable field."""
    target: TargetState | None = None
    validation_addresses: tuple[str, ...] = ()
    validation_rows: tuple[str, ...] = ()
    source_url: str | None = None
    """Read back so a finding can send its reader to the document rather than to this file. It is
    taken from the RECORD and not from `RAW_URL`, because what a reader has to open is the thing
    that was actually read - a constant that has moved since would send them somewhere else."""
    attempt_at_raw: str | None = None
    attempt_rows: tuple[str, ...] = ()
    attempt: TargetState | None = None
    """WHAT THE LAST RUN ESTABLISHED, WHICH MAY BE NOTHING. Separate from `target` because a run
    that established nothing must not overwrite a measurement AND must not pass in silence: the
    draft that had only one of these fields chose, and whichever it chose, the other fact was lost.
    """


def _key(line: str) -> str:
    """The line with everything but letters and digits removed, lowercased.

    So `- **IdentityRegistry**: [0x8004...]` and `| Validation Registry | 0x8004... |` and
    `validation_registry = "0x8004..."` all reduce to a string containing the same label. Hex
    digits are a-f, so no address can spell a label into existence.

    NAMED LIMIT: this is a LABEL-AND-ADDRESS-ON-ONE-LINE reader. A deployment list that puts the
    label in a column header, or splits it from its address across lines, reads as no label at all.
    """
    return re.sub(r"[^a-z0-9]", "", line.lower())


def _rows_for(document: str, label: str,
              unless: tuple[str, ...] = ()) -> tuple[tuple[str, str], ...]:
    """Distinct `(address, line)` pairs whose line also carries `label`, in order of appearance.

    DISTINCT CASE-INSENSITIVELY, keeping the first spelling seen. An EVM address is a number; the
    mixed case is EIP-55's checksum display and not part of it, and the real document already
    carries one registry twice because a single explorer link is lowercased. Counting that as two
    deployments inflates the control and prints the same address twice in a finding.

    THE LINE IS KEPT because an address alone does not say WHICH CHAIN it is on - the document puts
    that in a heading above the row - and a finding that hands the operator a bare address invites
    scheduling T-2.15b against a testnet or a deprecated section. The line is not parsed for a
    chain; it is carried verbatim into the record so a person reads the document's own words.

    `unless` NAMES LABELS THAT MAKE A LINE UNATTRIBUTABLE. A row reading
    `- **IdentityRegistry**: 0x8004A1... (read by the Validation Registry)` names two registries and
    one address and says nothing about which owns it - so the strict target match excludes it, and
    the gate does not print `TARGET APPEARED` over the Identity Registry's own address and send
    somebody off to schedule T-2.15b against it. The live document already carries that phrase in
    prose in three places; one of them gaining an address is all it would have taken. Found by
    Fable, in the tier that had just been made strict to prevent this very class of thing.
    """
    seen: dict[str, tuple[str, str]] = {}
    for line in document.splitlines():
        found = [a for a in ADDRESS.findall(line) if a.lower() != ZERO_ADDRESS]
        key = _key(line)
        if not found or label not in key or any(u in key for u in unless):
            continue
        for a in found:
            seen.setdefault(a.lower(), (a, line.strip()))
    return tuple(seen.values())


def parse(document: str, http_status: int | None = 200) -> DeploymentRead:
    """Classify a deployment list. Pure: no clock, no network, no filesystem.

    WHAT THE ANCHORS ESTABLISH, EXACTLY, and it is less than "we are reading the deployment list".
    They establish that this document still names both registries that ARE deployed beside
    addresses. A document that has moved its list elsewhere while keeping two deprecated rows would
    pass them; so would one whose list is intact under labels this parser reads. What they rule out
    is the case that actually happens to a parser - the document being replaced, emptied, moved
    behind an error page, or restructured past the shape it reads - and in every one of those the
    answer becomes `unreadable` instead of a confident absence. The residue is named here rather
    than left for a reader to discover, because the four documents describing this control said
    "converts the failure into a red" and that was a stronger claim than the code. Found by Fable.
    """
    digest = hashlib.sha256(document.encode("utf-8")).hexdigest()
    identity = tuple(a for a, _ in _rows_for(document, IDENTITY))
    reputation = tuple(a for a, _ in _rows_for(document, REPUTATION))
    named = _rows_for(document, VALIDATION, unless=(IDENTITY, REPUTATION))
    loose = _rows_for(document, VALIDATION_LOOSE)

    # ORDER IS THE ARGUMENT, AND IT IS FOUR DEEP.
    #
    # 1. A row spelled `ValidationRegistry`, naming no other registry, beside an address IS a
    #    measurement and outranks everything: reporting `unreadable` over it because the anchors
    #    moved would discard a reading the instrument is holding.
    # 2. THE ANCHORS COME NEXT, AND AN EARLIER DRAFT HAD THEM LAST. With the maybe-tier above them,
    #    a document restructured past this parser - the exact state RED-015 exists for - reported
    #    `validation_row_not_conclusive` as soon as it contained one API example, telling the reader
    #    to go and classify a line when the true state was "the deployment list has gone". Both are
    #    `not_measured`, so the class survived and the instruction did not; the anchor failure was
    #    in the DeploymentRead and was thrown away at the moment the state was named. Found by
    #    Fable, in the ordering introduced one round earlier.
    # 3. Then the honest maybe.
    # 4. And absence last, because absence is the only answer that can be produced by not looking.
    if named:
        state, rows = TargetState.TARGET_PRESENT, named
    elif not identity or not reputation:
        # The rows are kept and the ADDRESSES are not: under this state nothing was attributed to a
        # Validation Registry, and a field called `validation_addresses` holding them would assert
        # more than its content. The lines still travel, so the reader is not sent to look twice.
        state, rows = TargetState.LIST_UNRECOGNISED, loose
    elif loose:
        state, rows = TargetState.ROW_NOT_CONCLUSIVE, loose
    else:
        state, rows = TargetState.NO_TARGET, ()
    attributed = () if state is TargetState.LIST_UNRECOGNISED else tuple(a for a, _ in rows)
    return DeploymentRead(state, attributed, identity, reputation,
                          http_status, digest, tuple(ln for _, ln in rows))


def fetch(url: str = RAW_URL, timeout: int = 60) -> tuple[TargetState | None, int | None, str | None]:
    """One anonymous read. Returns `(failure_state, http_status, document)`.

    On success the failure state is None. On failure it is the state that says WHOSE failure it
    was, as far as that was established: no client here, no answer at all with the cause unknown,
    or the source answering and declining. Three names instead of one, because the single name this
    replaced - `source_refused` - asserted a fact about somebody else's server on the evidence that
    a socket had not opened on ours (L-11).
    """
    try:
        p = subprocess.run(["curl", "-sS", "-w", "\n%{http_code}", url],
                           capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return TargetState.NO_CLIENT, None, None
    except (OSError, subprocess.SubprocessError):
        return TargetState.NO_ANSWER, None, None
    raw = p.stdout.rsplit("\n", 1)
    if p.returncode != 0 or len(raw) != 2 or not raw[1].strip().isdigit():
        return TargetState.NO_ANSWER, None, None
    body, code = raw
    status = int(code.strip())
    if status != 200:
        return TargetState.SOURCE_ANSWERED_NON_200, status, None
    return None, status, body


def read_source(url: str = RAW_URL) -> DeploymentRead:
    """Fetch and classify. The only function here that touches the network."""
    failure, status, document = fetch(url)
    if failure is not None or document is None:
        return DeploymentRead(failure or TargetState.NO_ANSWER, http_status=status)
    return parse(document, status)


def read_record(path: Path) -> RecordRead:
    """Read the written-down reading. Every failure keeps its own name; nothing defaults."""
    if not path.exists():
        return RecordRead(RecordState.FILE_ABSENT)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return RecordRead(RecordState.NOT_JSON)
    if not isinstance(doc, dict):
        return RecordRead(RecordState.NOT_JSON)

    url = doc.get("source_url")
    source = url if isinstance(url, str) else None

    # THE ATTEMPT BLOCK FIRST, because it is the one a broken measurement must not be able to hide.
    attempt_block = doc.get(ATTEMPT)
    if not isinstance(attempt_block, dict) or not isinstance(attempt_block.get("state"), str):
        return RecordRead(RecordState.NO_ATTEMPT, source_url=source)
    try:
        attempt = TargetState(attempt_block["state"])
    except ValueError:
        return RecordRead(RecordState.UNKNOWN_STATE, source_url=source)
    at = attempt_block.get("at")
    attempt_at = at if isinstance(at, str) else None
    listed = attempt_block.get("validation_registry_rows")
    attempt_rows = (tuple(x for x in listed if isinstance(x, str))
                    if isinstance(listed, list) else ())

    if MEASUREMENT not in doc:
        return RecordRead(RecordState.NO_MEASUREMENT_KEY, source_url=source,
                          attempt=attempt, attempt_at_raw=attempt_at, attempt_rows=attempt_rows)
    block = doc[MEASUREMENT]
    if block is None:
        # NO MEASUREMENT HAS EVER BEEN TAKEN. That is a readable record of a real state - every run
        # so far failed - and it is not an unreadable field. The obligation reads `last_seen` as
        # None with the unreadable flag DOWN, which prints "has never presented evidence", which is
        # exactly true of it.
        return RecordRead(RecordState.READ, source_url=source, attempt=attempt,
                          attempt_at_raw=attempt_at)
    if not isinstance(block, dict) or "checked_at" not in block:
        return RecordRead(RecordState.NO_CHECKED_AT, source_url=source,
                          attempt=attempt, attempt_at_raw=attempt_at, attempt_rows=attempt_rows)
    if not isinstance(block["checked_at"], str):
        # A FIELD THAT IS THERE AND WRONG IS NOT A FIELD THAT IS MISSING. An epoch integer read as
        # `no_checked_at` in a module whose sibling state exists to make exactly that distinction.
        # Found by Fable.
        return RecordRead(RecordState.BAD_CHECKED_AT, source_url=source,
                          attempt=attempt, attempt_at_raw=attempt_at, attempt_rows=attempt_rows)
    raw = block["checked_at"]
    if not isinstance(block.get("state"), str):
        return RecordRead(RecordState.NO_STATE, checked_at_raw=raw, source_url=source,
                          attempt=attempt, attempt_at_raw=attempt_at, attempt_rows=attempt_rows)
    try:
        target = TargetState(block["state"])
    except ValueError:
        return RecordRead(RecordState.UNKNOWN_STATE, checked_at_raw=raw, source_url=source,
                          attempt=attempt, attempt_at_raw=attempt_at, attempt_rows=attempt_rows)

    def _strings(key: str) -> tuple[str, ...]:
        got = block.get(key)
        return tuple(s for s in got if isinstance(s, str)) if isinstance(got, list) else ()

    return RecordRead(RecordState.READ, checked_at_raw=raw, target=target,
                      validation_addresses=_strings("validation_registry_addresses"),
                      validation_rows=_strings("validation_registry_rows"),
                      source_url=source, attempt=attempt, attempt_at_raw=attempt_at, attempt_rows=attempt_rows)
