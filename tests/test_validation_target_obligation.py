"""T-F7 - a blocked step keeps a sentinel, and the sentinel is red on good news
(LAW-BLOCKED-STEP-HAS-A-SENTINEL).

WHAT IS BEING GUARDED. T-2.15b cannot be scheduled because the ERC-8004 Validation Registry is not
deployed - measured on 2026-08-20 and written into `docs/MEASUREMENT_QM1.md`. That is an EXTERNAL
blocker: it lifts on somebody else's schedule and nothing about it reaches this repository. A
"cannot" that nobody re-checks is indistinguishable, after a few weeks, from a "forgot".

THE TWO WAYS THIS CAN GO WRONG ARE OPPOSITE, and both are covered below.

  Silently late  - nobody runs the watch, and the record ages until nothing means anything. That is
                   the obligation's own interval, and it goes red with no commit and no event.
  Silently clean - the watch runs, the document has been rewritten into a shape this parser no
                   longer reads, and `no_target` comes back for ever from an instrument that is no
                   longer looking at anything. That is the false green, it is the more dangerous of
                   the two because it looks like health, and the anchors are what refuse it.

THIS SUITE DOES NOT SKIP (L-16). The state it exists to speak in - nobody has re-checked, or the
source has changed shape - is a state in which everything imports and every assertion is armed.
"""
from __future__ import annotations

import contextlib
import http.server
import importlib.util
import json
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.liveness import commitments as C
from src.liveness.obligations import MAX_AGE, Interval
from src.transport import erc8004_deployment as D

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 8, 20, 12, tzinfo=timezone.utc)

IDENTITY_ADDRESS = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
REPUTATION_ADDRESS = "0x8004BAa17C55a88189AE136b182e5fdA19dE9b63"
INVENTED_ADDRESS = "0x8004" + "c" * 36
"""NOT a real address and deliberately so: no test here may read as a claim that a Validation
Registry has been deployed at some address. It is 40 hex digits because that is what an address is,
and it is invented because what is being exercised is the parser."""

# --- lifted verbatim from the document of 2026-08-20 -------------------------------------------
#
# sha256 0fa22248188fc2455c0c7c5e31836f09a92cfeb34e27f61e778d1d9e276fb3cb, recorded in
# public/erc8004/validation_registry.json beside the reading it produced.
#
# THESE ARE THE TRAPS AND NOT THE DOCUMENT. The whole 25 KB README is not copied here: it is
# somebody else's text, it would go stale on their next commit, and a frozen copy proves nothing
# about the file the watch actually reads. What is copied is every shape in it that could make the
# parser answer wrongly - three places that say "validation" with no address anywhere near a
# deployment, and the two anchor rows. The claim this fixture supports is "these shapes are
# handled"; the claim about the REAL document is `test_the_recorded_reading_is_of_the_real_source`
# below, which reads the artefact the parser produced from it.
REAL_SHAPES = f"""\
#### Ethereum Mainnet
- **IdentityRegistry**: [`{IDENTITY_ADDRESS}`](https://etherscan.io/address/{IDENTITY_ADDRESS})
- **ReputationRegistry**: [`{REPUTATION_ADDRESS}`](https://etherscan.io/address/{REPUTATION_ADDRESS})

- **Validation Registry**: hooks for validator smart contracts to publish validation results.

### Validation Registry

> The **Validation Registry** portion of the ERC-8004 spec is **still under active update and
> discussion with the TEE community**.

- `validationRequest(validatorAddress, agentId, requestURI, requestHash)`
- Read functions: `getValidationStatus`, `getSummary`, `getAgentValidations`

└── ValidationRegistryUpgradeable.sol   - Validation request/response (upgradeable)
"""


def _watch(*, checked_days_ago: float = 0.0, target: D.TargetState = D.TargetState.NO_TARGET,
           record: D.RecordState = D.RecordState.READ,
           addresses: tuple[str, ...] = ()) -> C.TargetWatch:
    return C.TargetWatch(record, checked_at=NOW - timedelta(days=checked_days_ago),
                         target=target, addresses=addresses)


def _cohort() -> C.CohortRun:
    """A clean first obligation, so the assertions here stay about the second one."""
    return C.CohortRun(C.ReadState.READ, generated_at=NOW,
                       earliest_valid_until=NOW + timedelta(days=30), rows=8)


def _findings(watch: C.TargetWatch, now: datetime = NOW) -> list[str]:
    return C.findings(_cohort(), now, watch)


# --- the parser answers, and refuses to answer ------------------------------------------------

def test_the_real_shapes_of_the_document_do_not_produce_a_false_target():
    """Three lines in that README say "Validation Registry" and none of them is a deployment.

    A parser that searched for the words alone - the obvious first draft - would report a target on
    a sentence describing the section, on a heading, and on a filename in a source tree, and the
    project would have gone off to schedule T-2.15b against nothing at all.
    """
    read = D.parse(REAL_SHAPES)
    assert read.state is D.TargetState.NO_TARGET, read
    assert read.validation_addresses == ()
    assert read.identity_addresses == (IDENTITY_ADDRESS,)
    assert read.reputation_addresses == (REPUTATION_ADDRESS,)


def test_an_address_beside_the_label_is_found_in_every_spelling_reported():
    """The state the watch exists for, in the shapes a deployment list is written in.

    A LIMIT RATHER THAN A PROOF: these are spellings somebody has actually used, so they are
    evidence that these are handled and not a demonstration that the parser is right about markdown
    in general. The parser reads a LABEL AND AN ADDRESS ON ONE LINE, and where that assumption
    fails it fails to `LIST_UNRECOGNISED` - see the anchors test below, which is the half that
    matters.
    """
    anchors = (f"- **IdentityRegistry**: `{IDENTITY_ADDRESS}`\n"
               f"- **ReputationRegistry**: `{REPUTATION_ADDRESS}`\n")
    for name, line in {
        "the document's own style": f"- **ValidationRegistry**: [`{INVENTED_ADDRESS}`](https://e/x)",
        "two words": f"- **Validation Registry**: `{INVENTED_ADDRESS}`",
        "a table row": f"| ValidationRegistry | {INVENTED_ADDRESS} | mainnet |",
        "snake case": f'validation_registry = "{INVENTED_ADDRESS}"',
        "lower case": f"validationregistry: {INVENTED_ADDRESS.lower()}",
    }.items():
        read = D.parse(anchors + line + "\n")
        assert read.state is D.TargetState.TARGET_PRESENT, f"missed a target: {name}"
        assert len(read.validation_addresses) == 1, f"{name}: {read.validation_addresses}"


def test_a_document_whose_shape_is_gone_is_unreadable_and_not_an_absence():
    """THE FALSE GREEN THIS INSTRUMENT IS BUILT AGAINST, and the only reason for the anchors.

    Absence is the answer this watch returns almost every time, so absence is the answer that can
    be produced by not looking properly - for ever, silently, in exactly the state where a real
    deployment would be missed. The Identity and Reputation registries ARE deployed and ARE in that
    list; if neither can be found, the parser is no longer reading a deployment list and says so.
    """
    for name, doc in {
        "empty": "",
        "a page that is not the list": "# ERC-8004\n\nSee the docs for deployment addresses.\n",
        "the list restructured past this reader": "| Chain | Identity | Reputation |\n"
                                                  f"| Mainnet | {IDENTITY_ADDRESS} "
                                                  f"| {REPUTATION_ADDRESS} |\n",
    }.items():
        read = D.parse(doc)
        assert read.state is D.TargetState.LIST_UNRECOGNISED, f"read as an absence: {name}"
        assert read.state.is_measured is False


def test_one_anchor_is_not_enough_because_one_can_be_renamed():
    """Both anchors are required - the test is `not identity OR not reputation`, not "neither".

    Either registry could be renamed on its own, and a control that survives on the half that did
    not move is a control that has stopped controlling. Two documents described this as "if neither
    can be found", which is a weaker rule than the code holds; asserting the OR is what keeps the
    prose from drifting back to it.
    """
    only_identity = f"- **IdentityRegistry**: `{IDENTITY_ADDRESS}`\n"
    only_reputation = f"- **ReputationRegistry**: `{REPUTATION_ADDRESS}`\n"
    assert D.parse(only_identity).state is D.TargetState.LIST_UNRECOGNISED
    assert D.parse(only_reputation).state is D.TargetState.LIST_UNRECOGNISED


def test_a_renamed_target_row_is_never_reported_as_an_absence():
    """THE MISS THE ANCHORS CANNOT CATCH, and the third tier is the answer to it.

    The anchors go on matching while the target row is renamed - they are different labels, and
    only one of them has to change. A row still spelled `ValidationRegistry`, with any suffix, is a
    deployment. A row that only says `Validation` might be one; this reader cannot tell, and the
    one thing it may not do is call it nothing.
    """
    anchors = (f"- **IdentityRegistry**: `{IDENTITY_ADDRESS}`\n"
               f"- **ReputationRegistry**: `{REPUTATION_ADDRESS}`\n")
    for name, line in {
        "a version suffix": f"- **ValidationRegistryV2**: `{INVENTED_ADDRESS}`",
        "the proxy": f"- **ValidationRegistryUpgradeable**: `{INVENTED_ADDRESS}`",
        "two words": f"| Validation Registry | {INVENTED_ADDRESS} |",
    }.items():
        assert D.parse(anchors + line + "\n").state is D.TargetState.TARGET_PRESENT, name

    for name, line in {
        "the word alone": f"| Validation | {INVENTED_ADDRESS} |",
        "a deprecated helper": f"| Validation helper (do not use) | {INVENTED_ADDRESS} |",
    }.items():
        read = D.parse(anchors + line + "\n")
        assert read.state is D.TargetState.ROW_NOT_CONCLUSIVE, name
        assert read.state.is_measured is False
        assert read.validation_rows and INVENTED_ADDRESS in read.validation_rows[0], name


def test_a_row_naming_two_registries_is_not_attributed_to_either():
    """THE STRICT TIER FIRED ON PROSE TOO, and it carried the Identity Registry's own address.

    `_key` strips punctuation, so `- **IdentityRegistry**: 0x8004A1... (read by the Validation
    Registry)` matched `validationregistry` and the gate would have printed `TARGET APPEARED` over
    an address that is the ANCHOR's, ordering somebody to schedule T-2.15b against the Identity
    Registry. The live document already carries that phrase in prose in three places. A line naming
    two registries and one address says nothing about which owns it, so it is not a target - and it
    is not nothing either. Found by Fable, in the tier made strict to prevent this class of thing.
    """
    line = f"- **IdentityRegistry**: `{IDENTITY_ADDRESS}` (read by the Validation Registry)\n"
    read = D.parse(line + f"- **ReputationRegistry**: `{REPUTATION_ADDRESS}`\n")
    assert read.state is not D.TargetState.TARGET_PRESENT, "an anchor's address read as a target"
    assert read.state is D.TargetState.ROW_NOT_CONCLUSIVE

    # The address IS still carried, and that is right: the line is quoted for a person to read and
    # the address is in it. What must not happen is its being PRESENTED as a deployment - so the
    # finding is the one that says "I could not tell", never the one that says "go and schedule".
    watch = C.TargetWatch(D.RecordState.READ, checked_at=NOW, target=D.TargetState.NO_TARGET,
                          attempt=read.state, attempt_at=NOW,
                          attempt_rows=read.validation_rows)
    joined = " ".join(_findings(watch))
    assert "TARGET APPEARED" not in joined, joined
    assert IDENTITY_ADDRESS in joined, "the line it could not classify was not shown to the reader"


def test_a_lost_deployment_list_outranks_a_line_the_parser_cannot_classify():
    """THE ORDERING, AND AN EARLIER DRAFT HAD IT THE OTHER WAY.

    With the maybe-tier above the anchors, a document restructured past this parser - the exact
    state RED-015 exists for - reported `validation_row_not_conclusive` the moment it contained one
    API example, and told the reader to go and classify a line when the true state was "the
    deployment list has gone". Both are `not_measured`, so the class survived and the instruction
    did not: the anchor failure was in the DeploymentRead and was discarded as the state was named.
    """
    restructured = ("| Chain | Identity | Reputation |\n"
                    f"| Mainnet | {IDENTITY_ADDRESS} | {REPUTATION_ADDRESS} |\n"
                    f"`validationRequest({INVENTED_ADDRESS}, 42, uri, hash)`\n")
    read = D.parse(restructured)
    assert read.state is D.TargetState.LIST_UNRECOGNISED, read.state
    # The lines it could not classify are still carried, so the reader is not asked to go and find
    # them again - what changed is which finding is raised, not what was seen.
    assert read.validation_rows, "the rows were dropped along with the state"


def test_prose_that_merely_mentions_validation_is_not_reported_as_a_target():
    """THE MIRROR, AND IT IS WHY THE LOOSE HIT IS NOT `target_present`.

    The draft that matched `validation` alone priced a false positive as "a red one reading clears".
    The section this parser reads already contains `validationRequest(...)`, `getValidationStatus`
    and an event signature taking an `address`; documentation routinely gives those concrete
    example values, and the gate would then have ordered the operator to go and schedule on-chain
    publication against a line in a code sample. A red that instructs work nobody should do is not
    cheaper than a silence. Every line below was written by Fable as text that document plausibly
    grows, and none of them may read as a deployment.
    """
    anchors = (f"- **IdentityRegistry**: `{IDENTITY_ADDRESS}`\n"
               f"- **ReputationRegistry**: `{REPUTATION_ADDRESS}`\n")
    for name, line in {
        "an example call": f'`validationRequest({INVENTED_ADDRESS}, 42, "ipfs://Qm", 0x00)`',
        "an event signature": f"ValidationRequest(address indexed validator = {INVENTED_ADDRESS})",
        "a return value": f"`getValidationStatus(...)` -> `(validator: {INVENTED_ADDRESS}, ...)`",
        "a deploy script": f"forge script Deploy --sig 'run(address)' {INVENTED_ADDRESS}  # validation",
        "an audit note": f"Validation logic was audited; the multisig is {INVENTED_ADDRESS}",
    }.items():
        state = D.parse(anchors + line + "\n").state
        assert state is not D.TargetState.TARGET_PRESENT, f"prose read as a deployment: {name}"
        assert state is D.TargetState.ROW_NOT_CONCLUSIVE, name


def test_the_inconclusive_row_is_reported_as_neither_and_quotes_what_it_saw():
    """A finding whose reader cannot see what the instrument saw cannot settle it, and this is the
    one state that is settled by a person rather than by another run. Both exits are named, and the
    second - tightening the parser - is a legitimate answer rather than an admission."""
    watch = C.TargetWatch(D.RecordState.READ, checked_at=NOW,
                          target=D.TargetState.ROW_NOT_CONCLUSIVE,
                          addresses=(INVENTED_ADDRESS,),
                          attempt=D.TargetState.ROW_NOT_CONCLUSIVE, attempt_at=NOW,
                          attempt_rows=(f"| Validation | {INVENTED_ADDRESS} |",),
                          source_url="https://example.invalid/README.md")
    out = _findings(watch)
    joined = " ".join(out)
    assert any(f.startswith("NOT MEASURED") for f in out), out
    assert INVENTED_ADDRESS in joined, "the line it could not classify is not quoted"
    assert "https://example.invalid/README.md" in joined, "the reader is not sent to the document"
    assert "src/transport/erc8004_deployment.py" in joined, "the second way out is not named"
    assert "TARGET APPEARED" not in joined, "a maybe was promoted to a finding of fact"


def test_a_placeholder_address_is_not_a_deployment():
    """`0x0000…0000` is how EVM writes "not set". Reading it as a target would be a placeholder
    taken for an artefact, and would raise TARGET APPEARED on a row saying the opposite."""
    anchors = (f"- **IdentityRegistry**: `{IDENTITY_ADDRESS}`\n"
               f"- **ReputationRegistry**: `{REPUTATION_ADDRESS}`\n")
    doc = anchors + f"- **ValidationRegistry**: `{D.ZERO_ADDRESS}` (not yet deployed)\n"
    assert D.parse(doc).state is D.TargetState.NO_TARGET


def test_a_sixty_four_digit_hash_is_not_truncated_into_an_address():
    """The pattern is bounded at both ends, and unbounded it did not skip a hash - it CUT one down
    to forty digits. A deployment tx hash or a bytecode digest on a line naming a registry became a
    fabricated address: a false TARGET APPEARED carrying something nobody deployed, or an anchor
    passing on a document with no deployment addresses in it at all."""
    doc = ("- **IdentityRegistry** deployed in tx 0x" + "a" * 64 + "\n"
           "- **ReputationRegistry** bytecode 0x" + "b" * 64 + "\n"
           "- **ValidationRegistry** salt 0x" + "c" * 64 + "\n")
    read = D.parse(doc)
    assert read.validation_addresses == (), read.validation_addresses
    assert read.identity_addresses == () and read.reputation_addresses == ()
    assert read.state is D.TargetState.LIST_UNRECOGNISED


def test_a_found_address_outranks_the_control_that_protects_an_absence():
    """The ordering in `parse()`, asserted rather than left to reading.

    If the anchors are gone AND a validation address is present, the address is a measurement the
    instrument is holding. Reporting `unrecognised` over it would throw away a reading that was
    taken - the same defect `commitments.py` paid for in its PARTIALLY READ branch, and it would
    discard the one reading that changes what this project does next.
    """
    read = D.parse(f"- ValidationRegistry: {INVENTED_ADDRESS}\n")
    assert read.state is D.TargetState.TARGET_PRESENT
    assert read.identity_addresses == () and read.reputation_addresses == ()


def test_the_same_address_in_two_cases_is_one_deployment():
    """The real document lowercases one explorer link. Counting a checksum spelling as a second
    deployment inflates the control and prints the same address twice in a finding."""
    doc = (f"- **IdentityRegistry**: {IDENTITY_ADDRESS}\n"
           f"- **IdentityRegistry**: {IDENTITY_ADDRESS.lower()}\n"
           f"- **ReputationRegistry**: {REPUTATION_ADDRESS}\n")
    assert D.parse(doc).identity_addresses == (IDENTITY_ADDRESS,)


def test_a_failed_request_is_not_a_deployment_list_with_nothing_in_it():
    """§2.9 at the top of the instrument: nothing that failed to read yields an absence.

    `read_source` is exercised through a URL that cannot resolve rather than by patching `fetch`,
    so what is checked is the real path from a failed request to the state that comes out of it.
    `.invalid` is reserved by RFC 2606 and must not resolve, so this is a DNS failure by
    construction rather than a request that might reach somebody.
    """
    read = D.read_source("https://invalid.invalid./no-such-document")
    assert read.state is D.TargetState.NO_ANSWER
    assert read.state.is_measured is False
    assert read.validation_addresses == ()


def test_our_own_failure_is_not_recorded_as_the_source_refusing():
    """L-11 AT THE TOP OF THE INSTRUMENT, and the single name this replaced broke it.

    Every failure used to become `check_did_not_run:source_refused` - a claim about somebody else's
    server, made on the evidence that a socket did not open here. A missing client, a timeout and a
    404 are three different facts and only the last of them is about them. The state's VALUE is
    what matters, because that string is what travels into the record, the finding, and the message
    `Erc8004Transport.publish` raises; a docstring saying "this reader" does not follow it there.
    """
    assert "source" not in D.TargetState.NO_CLIENT.value
    assert "source" not in D.TargetState.NO_ANSWER.value
    assert "source" in D.TargetState.SOURCE_ANSWERED_NON_200.value
    for state in (D.TargetState.NO_CLIENT, D.TargetState.NO_ANSWER,
                  D.TargetState.SOURCE_ANSWERED_NON_200):
        assert state.is_measured is False, state



@contextlib.contextmanager
def _serving(status: int, body: str):
    """A local HTTP server that answers once with `status`. No network, no third party.

    Needed because two of the three failure states could otherwise only be reached by hand: the
    non-200 branch has no offline route through `fetch()` at all, and a test that constructs the
    state itself proves the enum exists, not that the code produces it.
    """
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):                                    # noqa: N802 - the stdlib's name
            payload = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):                        # keep pytest's output readable
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/README.md"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_each_failure_state_is_produced_by_the_real_fetch_and_not_only_declared(monkeypatch):
    """ARMED, WHICH THE FIRST DRAFT WAS NOT. Two of the three states this fix introduced were
    reachable only by hand: folding `except FileNotFoundError` back into the `OSError` branch -
    deleting the whole distinction the fix was made for - left the entire suite passing. A repair
    is not landed until something fails without it (L-21), and that was L-21 committed inside the
    fix for L-11.

    All three are driven through `fetch()` itself: no client, by emptying PATH so the real
    `subprocess.run` cannot find `curl`; no answer, against a name RFC 2606 reserves as
    unresolvable; a declining source, against a local server that answers 503 - which needs no
    network and so cannot go red for somebody else's reason.
    """
    monkeypatch.setenv("PATH", "")
    failure, status, doc = D.fetch("https://example.invalid/x", timeout=30)
    assert failure is D.TargetState.NO_CLIENT, "an absent client was not ruled out by name"
    assert status is None and doc is None
    monkeypatch.undo()

    failure, status, doc = D.fetch("https://invalid.invalid./x", timeout=30)
    assert failure is D.TargetState.NO_ANSWER and status is None and doc is None

    with _serving(503, "service unavailable") as url:
        failure, status, doc = D.fetch(url, timeout=30)
    assert failure is D.TargetState.SOURCE_ANSWERED_NON_200, "a declining source was not named"
    assert status == 503, "the status a reader needs was not carried out of fetch()"
    assert doc is None, "a body arrived with a non-200 and was within reach of the parser"


def test_a_two_hundred_is_read_and_classified_end_to_end():
    """The other side of the same instrument: `fetch` -> `parse` -> a state, over a real socket.
    Without it the 200 path is exercised only against the live document, so a break in the plumbing
    would present as somebody else's outage rather than as a defect here."""
    anchors = (f"- **IdentityRegistry**: `{IDENTITY_ADDRESS}`\n"
               f"- **ReputationRegistry**: `{REPUTATION_ADDRESS}`\n")
    with _serving(200, anchors) as url:
        read = D.read_source(url)
    assert read.state is D.TargetState.NO_TARGET
    assert read.identity_addresses == (IDENTITY_ADDRESS,)
    assert read.http_status == 200


# --- the obligation, and what it says when nobody performs it ----------------------------------

def test_the_obligation_is_declared_and_names_a_consumer():
    """Declared, and not the fifth sleeping state.

    The consumer assertion is not a spelling check: `NO CONSUMER` is what `Registry.sweep` prints
    when the field is None, so a declaration that forgot one fails here rather than reading as a
    clean sweep. The expected evidence has to name the act that produces it, because that string is
    what a reader is shown when the component has never presented any.
    """
    reg = C.declare(_cohort(), _watch(checked_days_ago=999))
    out = reg.sweep(NOW)
    assert not any("NO CONSUMER" in f for f in out), out
    assert any("SILENCE" in f and C.WATCH_COMPONENT in f for f in out), out
    assert "scripts/watch_validation_registry.py" in C.WATCH_EXPECTED_EVIDENCE
    assert C.WATCH_CONSUMER.startswith("src/transport/erc8004.py")


def test_both_obligations_are_in_one_registry_and_neither_is_lost():
    """A registry holding one obligation and a registry holding two sweep to the same empty list
    when both are clean, so the count is asserted where it can be seen: in the findings each
    produces when it is NOT clean."""
    out = C.findings(_cohort(), NOW, _watch(checked_days_ago=999))
    assert any(C.WATCH_COMPONENT in f for f in out), out
    stale_cohort = C.CohortRun(C.ReadState.READ, generated_at=NOW - timedelta(days=999),
                               earliest_valid_until=NOW - timedelta(days=969), rows=8)
    out = C.findings(stale_cohort, NOW, _watch(checked_days_ago=999))
    assert any(C.COMPONENT in f for f in out) and any(C.WATCH_COMPONENT in f for f in out), out


def test_a_missed_interval_is_a_named_finding_carrying_ITS_OWN_remedy():
    """The remedy is routed by component. A single remedy attached to everything beginning with
    SILENCE - the shape this module had with one obligation - would tell a reader whose watch had
    gone quiet to re-run the cohort and ask the operator to deploy the site (L-9)."""
    late = MAX_AGE[Interval.WHILE_BLOCKED].days + 1
    out = _findings(_watch(checked_days_ago=late))
    joined = " ".join(out)
    assert "SILENCE" in joined and C.WATCH_COMPONENT in joined, out
    assert "scripts/watch_validation_registry.py" in joined, out
    assert "scripts/cohort.py" not in joined, "the cohort's remedy was attached to the watch"


def test_a_check_inside_the_interval_reports_nothing():
    assert _findings(_watch(checked_days_ago=MAX_AGE[Interval.WHILE_BLOCKED].days - 1)) == []


def test_the_interval_is_a_reference_to_the_habit_and_not_a_number():
    """Algebra, and named as algebra. Nothing in the world sets this deadline - a blocked step
    misses no lapse by being found late - so the alternative to deriving it from the one habit this
    repository has is inventing a round number and stating it as though it had been measured."""
    assert MAX_AGE[Interval.WHILE_BLOCKED] is MAX_AGE[Interval.BEFORE_REISSUE]


# --- absence keeps its own name (invariant 1) --------------------------------------------------

def test_a_check_that_did_not_run_does_not_report_that_there_is_no_target():
    """The record reads perfectly and says the instrument failed. Those are separate axes and the
    finding has to speak on the second one without touching the first.

    All four non-measurements are exercised, not one of them: a table that walked only the state
    somebody happened to report is a control that stops at yesterday's finding (L-13).
    """
    for state in (D.TargetState.NO_CLIENT, D.TargetState.NO_ANSWER,
                  D.TargetState.SOURCE_ANSWERED_NON_200, D.TargetState.LIST_UNRECOGNISED):
        out = _findings(_watch(target=state))
        assert any(f.startswith("NOT MEASURED") for f in out), (state, out)
        assert any(state.value in f for f in out), (state, out)
        assert not any("SILENCE" in f for f in out), "the watch ran on the day it says it did"
        assert any("scripts/watch_validation_registry.py" in f for f in out), "no remedy on a red"


def test_an_absent_record_is_not_reported_as_a_missed_check(tmp_path: Path):
    """Both halves, and the second is the one that is easy to get wrong: reporting NOT MEASURED is
    not enough while the line beside it still calls the component silent.

    The remedy is asserted here because a fresh clone is the state with the LEAST context: whoever
    meets it has nothing else in the tree telling them what the watch is or how to run it, and the
    record-file findings carried no remedy at all in the first draft.
    """
    out = C.sweep(NOW, root=tmp_path)
    assert any(D.RecordState.FILE_ABSENT.value in f for f in out), out
    assert any(f.startswith("NOT ASSESSED") and C.WATCH_COMPONENT in f for f in out), out
    assert not any("SILENCE" in f and C.WATCH_COMPONENT in f for f in out), out
    assert any("scripts/watch_validation_registry.py" in f for f in out), out


def test_a_record_that_is_not_json_is_unreadable_rather_than_absent(tmp_path: Path):
    p = tmp_path / D.RECORD
    p.parent.mkdir(parents=True)
    p.write_text("{not json", encoding="utf-8")
    watch = C.read_watch(p)
    assert watch.record is D.RecordState.NOT_JSON
    assert watch.checked_at is None and watch.target is None


def _record(*, measurement: dict | None = ..., attempt: str = "no_target",
            attempt_at: str | None = None, source_url: str = "https://example.invalid/README.md"):
    """A record in the shape the script writes: an attempt block always, a measurement or null."""
    if measurement is ...:
        measurement = {"checked_at": NOW.isoformat(), "state": "no_target",
                       "validation_registry_addresses": [], "validation_registry_rows": []}
    return {"blocks": C.BLOCKED_STEP, "source_url": source_url,
            D.ATTEMPT: {"at": attempt_at or NOW.isoformat(), "state": attempt},
            D.MEASUREMENT: measurement}


def _written(tmp_path: Path, doc: dict) -> Path:
    p = tmp_path / D.RECORD
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def test_a_timestamp_that_was_read_is_kept_when_the_rest_of_the_record_was_not(tmp_path: Path):
    """`checked_at` parsed and `state` did not. The interval IS assessable on a quantity the
    instrument is holding, and reporting it as unknown would discard a measurement that was
    taken - the same rule the cohort's PARTIALLY READ branch was rewritten to obey."""
    p = _written(tmp_path, _record(measurement={
        "checked_at": (NOW - timedelta(days=400)).isoformat(),
        "state": "a state no version of this ever wrote"}))
    watch = C.read_watch(p)
    assert watch.record is D.RecordState.UNKNOWN_STATE
    assert watch.checked_at is not None
    out = _findings(watch)
    assert any(f.startswith("PARTIALLY READ") for f in out), out
    assert any("SILENCE" in f and C.WATCH_COMPONENT in f for f in out), out
    assert not any("NOT ASSESSED" in f and C.WATCH_COMPONENT in f for f in out), out


def test_a_checked_at_that_is_not_a_timestamp_keeps_its_own_name(tmp_path: Path):
    p = _written(tmp_path, _record(measurement={"checked_at": "yesterday", "state": "no_target"}))
    watch = C.read_watch(p)
    assert watch.record is D.RecordState.BAD_CHECKED_AT
    assert watch.record is not D.RecordState.NO_CHECKED_AT, "a bad field is not a missing one"


def test_every_record_failure_has_its_own_name_and_none_of_them_is_a_default(tmp_path: Path):
    """The vocabulary, walked. Members with no test at all are L-21's shape one level down -
    present, documented, and never shown to work."""
    cases = [
        (D.RecordState.NO_CHECKED_AT, _record(measurement={"state": "no_target"})),
        (D.RecordState.BAD_CHECKED_AT, _record(measurement={"checked_at": 1755000000,
                                                            "state": "no_target"})),
        (D.RecordState.NO_STATE, _record(measurement={"checked_at": NOW.isoformat()})),
        (D.RecordState.UNKNOWN_STATE, _record(measurement={"checked_at": NOW.isoformat(),
                                                           "state": "sort of fine"})),
        (D.RecordState.READ, _record()),
        (D.RecordState.READ, _record(measurement=None)),
    ]
    for expected, doc in cases:
        assert C.read_watch(_written(tmp_path, doc)).record is expected, doc

    # NO LAST_ATTEMPT BLOCK AT ALL is its own state, and it has to be: a record from before the two
    # axes existed reads perfectly as a measurement, so tolerating it silently would give the run
    # that established nothing nowhere to be - which is the whole defect the second block closes.
    stale_shape = {"checked_at": NOW.isoformat(), "state": "no_target"}
    assert C.read_watch(_written(tmp_path, stale_shape)).record is D.RecordState.NO_ATTEMPT

    # A field that is present and of the wrong type is not a field that is missing - the epoch
    # integer above read as `no_checked_at` until Fable pointed at the sibling state.
    assert D.RecordState.BAD_CHECKED_AT is not D.RecordState.NO_CHECKED_AT


def test_a_run_that_established_nothing_does_not_leave_the_gate_GREEN(tmp_path: Path):
    """THE WORST DEFECT THIS COMPONENT HAS HAD, and it was introduced by a fix.

    The draft before this one refused to overwrite a measurement with a non-measurement - right, and
    it closed a false red. But the record then went on saying `no_target` inside its interval while
    the last run had reported that the deployment list was unrecognisable, or that a row it could
    not classify had appeared, and `sweep()` returned NOTHING. A green gate meaning "did not look",
    for up to the whole interval, in the module written to forbid exactly that. The only witness was
    the stdout of a script nothing runs on a clock.

    Every non-measurement is walked, because the draft was green for all of them.
    """
    for state in (D.TargetState.NO_CLIENT, D.TargetState.NO_ANSWER,
                  D.TargetState.SOURCE_ANSWERED_NON_200, D.TargetState.LIST_UNRECOGNISED,
                  D.TargetState.ROW_NOT_CONCLUSIVE):
        watch = C.read_watch(_written(tmp_path, _record(attempt=state.value)))
        assert watch.checked_at is not None, "the measurement is still there, and still rides"
        assert watch.target is D.TargetState.NO_TARGET
        out = _findings(watch)
        assert out, f"GREEN after a run that established {state.value}"
        assert any(state.value in f for f in out), (state, out)
        assert any(f.startswith("NOT MEASURED") for f in out), (state, out)


def test_good_news_in_the_ATTEMPT_block_is_not_a_green_gate(tmp_path: Path):
    """THE MIRROR OF THE PREVIOUS ROUND'S DEFECT, and it was asserted as intended.

    The attempt loop reports only NON-measurements, and `TARGET APPEARED` was keyed on the
    measurement block alone - so a record whose most recent line said `target_present` swept CLEAN.
    The attempt axis carried bad news and not good news, and good news is the entire reason this
    component exists. The test above it walked every non-measured attempt "because the draft was
    green for all of them"; the mirror discipline - walk every MEASURED attempt - was the one not
    applied, and it was where the hole was. Found by Fable.
    """
    watch = C.read_watch(_written(tmp_path, _record(
        attempt="target_present", attempt_at=NOW.isoformat(),
        measurement={"checked_at": (NOW - timedelta(days=3)).isoformat(), "state": "no_target",
                     "validation_registry_addresses": [], "validation_registry_rows": []})))
    out = _findings(watch)
    assert out, "GREEN while the record's own most recent line says the registry deployed"
    joined = " ".join(out)
    assert any(f.startswith("TARGET APPEARED") for f in out), out
    assert any(f.startswith("BLOCKS DISAGREE") for f in out), out
    assert C.BLOCKED_STEP in joined


def test_the_two_blocks_are_reconciled_rather_than_trusted_separately(tmp_path: Path):
    """A second source of truth with no comparison between them is the defect the cohort obligation
    already carries `SHIPPED AHEAD OF THE RUN` for. Three shapes no single run can produce."""
    cases = {
        "an attempt newer than the measurement it should have written":
            _record(attempt="no_target", attempt_at=NOW.isoformat(),
                    measurement={"checked_at": (NOW - timedelta(days=2)).isoformat(),
                                 "state": "no_target"}),
        "blocks that disagree about what was seen":
            _record(attempt="target_present", attempt_at=NOW.isoformat(),
                    measurement={"checked_at": NOW.isoformat(), "state": "no_target"}),
        "a measured attempt over no measurement at all":
            _record(attempt="no_target", measurement=None),
    }
    for name, doc in cases.items():
        out = _findings(C.read_watch(_written(tmp_path, doc)))
        assert any(f.startswith("BLOCKS DISAGREE") for f in out), (name, out)


def test_a_measuring_run_reports_nothing_extra():
    """The other half of the rule above: an attempt that DID measure is not news, and a gate that
    spoke on every run would be one nobody reads."""
    watch = C.TargetWatch(D.RecordState.READ, checked_at=NOW, target=D.TargetState.NO_TARGET,
                          attempt=D.TargetState.NO_TARGET, attempt_at=NOW)
    assert _findings(watch) == []


def test_a_record_whose_runs_have_all_failed_says_so_rather_than_nothing(tmp_path: Path):
    """A fresh clone whose first run could not read the source. `measurement: null` is a readable
    statement that no measurement has ever been taken - which is neither a missing field nor an
    answer, and the obligation is entitled to call it never-presented because it is."""
    watch = C.read_watch(_written(tmp_path, _record(
        measurement=None, attempt=D.TargetState.NO_ANSWER.value)))
    assert watch.record is D.RecordState.READ, "the file read fine; it is the world that did not"
    assert watch.checked_at is None and watch.target is None
    out = _findings(watch)
    assert any(D.TargetState.NO_ANSWER.value in f for f in out), out
    assert any("never presented evidence" in f and C.WATCH_COMPONENT in f for f in out), out


def test_a_utc_timestamp_spelled_with_a_trailing_Z_is_a_timestamp():
    """Python 3.10 - which pyproject pins and CI installs - rejects `Z` in `fromisoformat`, and it
    is the commonest ISO spelling of UTC there is. Reading it as unusable would report our own
    interpreter's limit as a defect in the artefact."""
    assert C._parse_ts("2026-08-20T21:59:41Z") == datetime(2026, 8, 20, 21, 59, 41,
                                                           tzinfo=timezone.utc)


# --- the state the watch exists for ------------------------------------------------------------

def test_a_target_appearing_stops_the_build_and_says_what_to_do():
    """THE ASSERTION THE WHOLE COMPONENT IS FOR, and the one that proves it can fire.

    Good news is a red on purpose. When the registry deploys, every document in this repository
    that says NOT DEPLOYED becomes a claim stronger than its artefact, T-2.15b becomes schedulable,
    and the unaudited-contract risk becomes a decision somebody has to take rather than a line in a
    plan. None of that happens if the reading passes silently.
    """
    out = _findings(_watch(target=D.TargetState.TARGET_PRESENT, addresses=(INVENTED_ADDRESS,)))
    joined = " ".join(out)
    assert any(f.startswith("TARGET APPEARED") for f in out), out
    assert INVENTED_ADDRESS in joined, "the finding must carry the address it found"
    assert C.BLOCKED_STEP in joined, "the finding must name the step that is unblocked"
    assert "docs/MEASUREMENT_QM1.md" in joined, "the document that would now be wrong is not named"
    assert "chain" in joined, "a bare address invites scheduling the step against a testnet"


def test_a_target_that_was_read_is_not_silenced_by_a_timestamp_that_was_not(tmp_path: Path):
    """THE FINDING MUST SURVIVE THE OTHER AXIS FAILING, and the first draft's did not.

    `checked_at` and `state` fail independently. A record whose timestamp does not parse still
    holds what the deployment list said - and on Python 3.10 a `Z`-terminated timestamp was exactly
    that record. The draft returned after reporting the record problem, so the one finding this
    component exists to raise was suppressed by an unrelated field, beneath a sentence claiming
    that what the list said "WAS NOT ESTABLISHED" while the instrument was holding it.
    """
    watch = C.read_watch(_written(tmp_path, _record(
        attempt="target_present",
        measurement={"checked_at": "20 August 2026", "state": "target_present",
                     "validation_registry_addresses": [INVENTED_ADDRESS],
                     "validation_registry_rows": [f"| Mainnet | {INVENTED_ADDRESS} |"]})))
    assert watch.checked_at is None and watch.target is D.TargetState.TARGET_PRESENT

    out = _findings(watch)
    assert any(f.startswith("TARGET APPEARED") for f in out), out
    assert any(f.startswith("PARTIALLY READ") for f in out), out
    assert not any("NOR what it said" in f for f in out), (
        "the finding asserted that nothing was established about a state it was holding")


def test_the_refusal_to_publish_cites_the_reading_rather_than_a_standing_claim():
    """The consumer, exercised. Without this the obligation names a consumer that never runs, which
    is `produces_result_nobody_reads` dressed up as a declaration (ABI-16-3)."""
    import pytest

    from src.transport.erc8004 import Erc8004Transport, RegistryConfig
    with pytest.raises(NotImplementedError) as e:
        Erc8004Transport(RegistryConfig()).publish("erc8004:1", {}, 80)
    message = str(e.value)
    assert C.BLOCKED_STEP in message
    held = json.loads((ROOT / D.RECORD).read_text(encoding="utf-8"))[D.MEASUREMENT]
    assert held["state"] in message, "the refusal does not carry the state that was measured"
    assert held["checked_at"] in message, "the refusal does not carry the date it was measured"


# --- and the readings that are about the world -------------------------------------------------

_WATCH_SCRIPT = None


def _script():
    """The watch script, loaded as a module ONCE. It is a script rather than a package member, and
    the behaviour under test lives in `main()` - so it is imported by path rather than
    reimplemented, and the caller monkeypatches what it needs.

    Loaded once because executing it inserts the repository root into `sys.path`, which
    `monkeypatch` does not undo: a fresh exec per test left four copies of the same entry behind.
    Nothing in the module holds mutable state between calls, so one load serves every caller.
    """
    global _WATCH_SCRIPT
    if _WATCH_SCRIPT is None:
        spec = importlib.util.spec_from_file_location(
            "watch_validation_registry", ROOT / "scripts" / "watch_validation_registry.py")
        _WATCH_SCRIPT = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_WATCH_SCRIPT)
    return _WATCH_SCRIPT


def test_performing_the_remedy_on_a_bad_network_day_does_not_break_the_tree(monkeypatch,
                                                                           tmp_path: Path):
    """THE FALSE RED AT THE MOMENT THE HABIT IS OBEYED, which the first draft shipped.

    The script used to overwrite the record with whatever the latest run established, including
    nothing. Trace it: an agent meets `SILENCE`, runs the remedy exactly as printed on a day the
    source is 5xx, and the good `no_target` reading is replaced by a non-measurement - which turns
    the two assertions about the real tree red and leaves a dirty file `./scripts/push.sh`, step
    three of that same remedy, then refuses to send. A false red teaches walking past a gate
    exactly as a false green does (L-5), and this one fired on the person doing the right thing.

    So the MEASUREMENT survives verbatim - anchors, digest and all - while the ATTEMPT is written
    beside it, which is what stops the gate reading clean. Rebuilding the measurement rather than
    copying it would drop the anchors, and a measurement that loses its own positive control on the
    way past a failed run is not the measurement it claims to be.
    """
    watch_script = _script()
    record = tmp_path / D.RECORD
    record.parent.mkdir(parents=True)
    record.write_text((ROOT / D.RECORD).read_text(encoding="utf-8"), encoding="utf-8")
    before = json.loads(record.read_text(encoding="utf-8"))[D.MEASUREMENT]

    monkeypatch.setattr(watch_script, "ROOT", tmp_path)
    monkeypatch.setattr(watch_script, "read_source",
                        lambda: D.DeploymentRead(D.TargetState.NO_ANSWER))
    assert watch_script.main() == 1
    after = json.loads(record.read_text(encoding="utf-8"))
    assert after[D.MEASUREMENT] == before, "a run that established nothing moved the measurement"
    assert after[D.ATTEMPT]["state"] == D.TargetState.NO_ANSWER.value, (
        "the run that established nothing left no trace, so the gate would read clean")
    assert C.read_watch(record).checked_at is not None, "the interval lost the reading it rides"
    assert _findings(C.read_watch(record)), "the gate is GREEN after a run that measured nothing"


def test_a_failure_IS_written_when_there_is_no_measurement_to_protect(monkeypatch, tmp_path: Path):
    """The other half, and without it the rule above would hide the state instead of keeping it.

    On a fresh clone, or after a previous run that also failed, there is nothing to preserve - and
    leaving the record absent would turn "we tried and could not read the source" into "nobody has
    ever looked", which is one value for two states of the world.
    """
    watch_script = _script()
    monkeypatch.setattr(watch_script, "ROOT", tmp_path)
    monkeypatch.setattr(watch_script, "read_source",
                        lambda: D.DeploymentRead(D.TargetState.SOURCE_ANSWERED_NON_200,
                                                 http_status=503))
    assert watch_script.main() == 1
    written = json.loads((tmp_path / D.RECORD).read_text(encoding="utf-8"))
    assert written[D.ATTEMPT]["state"] == D.TargetState.SOURCE_ANSWERED_NON_200.value
    assert written[D.ATTEMPT]["http_status"] == 503
    assert written[D.MEASUREMENT] is None, (
        "a run that measured nothing wrote itself into the measurement block")


def test_a_failed_run_never_replaces_an_unreadable_record_with_a_claim_about_it(monkeypatch,
                                                                                tmp_path: Path):
    """"WE COULD NOT LOOK" MUST NOT BE UPGRADED INTO "IT NEVER HAPPENED", which is what the draft
    before this one did on its way past a record it could not parse.

    `_held_measurement` returned None for anything that was not a clean dict, and `main()` then
    wrote `measurement: null` - whose meaning is "no measurement has ever been taken". So one
    failed run over a merely unreadable record turned `NOT ASSESSED: could not be read` into
    `SILENCE: has never presented evidence of participation ... a FINDING, not missing data`. That
    is invariant 1 with the sign flipped, and the third input below is not hypothetical: it is the
    record shape this repository itself carried an hour before. Found by Fable.

    The refusal is safe where the first draft's was not, and that is asserted too: the file is left
    byte-identical, so the tree stays clean and `push.sh` has nothing to refuse.
    """
    watch_script = _script()
    monkeypatch.setattr(watch_script, "ROOT", tmp_path)
    monkeypatch.setattr(watch_script, "read_source",
                        lambda: D.DeploymentRead(D.TargetState.NO_ANSWER))
    record = tmp_path / D.RECORD
    record.parent.mkdir(parents=True)

    # UNTOUCHABLE: nothing here can be carried forward, so nothing may be written over it.
    for name, text in {
        "not JSON": "{not json",
        "the previous revision's one-block shape":
            json.dumps({"checked_at": NOW.isoformat(), "state": "no_target"}),
    }.items():
        record.write_text(text, encoding="utf-8")
        assert watch_script.main() == 1, name
        assert record.read_text(encoding="utf-8") == text, f"the record was rewritten: {name}"
        out = _findings(C.read_watch(record))
        assert not any("never presented evidence" in f for f in out), (
            f"an unreadable record was upgraded into a claim that nothing ever happened: {name}")

    # CARRIED VERBATIM, INCLUDING WHEN BROKEN. A block that is present and malformed has a name of
    # its own in the gate, and that name is true; rebuilding or dropping it would lose the state.
    broken = {"checked_at": 1755000000, "state": "no_target"}
    record.write_text(json.dumps(_record(measurement=broken)), encoding="utf-8")
    assert watch_script.main() == 1
    after = json.loads(record.read_text(encoding="utf-8"))
    assert after[D.MEASUREMENT] == broken, "a malformed measurement was rebuilt or discarded"
    assert after[D.ATTEMPT]["state"] == D.TargetState.NO_ANSWER.value
    out = _findings(C.read_watch(record))
    assert not any("never presented evidence" in f for f in out), out
    assert C.read_watch(record).record is D.RecordState.BAD_CHECKED_AT


def test_a_record_that_is_json_but_not_an_object_is_unreadable(tmp_path: Path):
    """`json.loads` succeeds on a list, a number and a string. A declared state nobody exercises is
    the L-21 shape at the vocabulary level, and this one guards the first line of the reader."""
    p = tmp_path / D.RECORD
    p.parent.mkdir(parents=True, exist_ok=True)
    for text in ("[]", "42", '"no_target"'):
        p.write_text(text, encoding="utf-8")
        assert C.read_watch(p).record is D.RecordState.NOT_JSON, text


def test_an_attempt_state_this_reader_does_not_know_is_named_rather_than_guessed(tmp_path: Path):
    """An older reader meeting a newer record must say so. Guessing the closest match is how a
    vocabulary silently loses a distinction, and the attempt block is now the one the gate reports
    from - so an unrecognised state there is the one that would be quietly dropped."""
    watch = C.read_watch(_written(tmp_path, _record(attempt="a state no version ever wrote")))
    assert watch.record is D.RecordState.UNKNOWN_STATE
    assert watch.attempt is None
    out = _findings(watch)
    assert any(f.startswith(("NOT MEASURED", "PARTIALLY READ")) for f in out), out


def test_an_absent_measurement_key_is_not_the_same_as_a_null_one(tmp_path: Path):
    """`null` is this project saying no measurement has ever been taken; an ABSENT key is a record
    written by something that does not know the shape. The mirrored state on the other block was
    named from the start, which is what made the asymmetry visible."""
    doc = _record()
    doc.pop(D.MEASUREMENT)
    assert C.read_watch(_written(tmp_path, doc)).record is D.RecordState.NO_MEASUREMENT_KEY
    assert C.read_watch(_written(tmp_path, _record(measurement=None))).record is D.RecordState.READ


def test_a_measurement_is_written_and_only_no_target_exits_zero(monkeypatch, tmp_path: Path):
    """The exit code is what a caller in a task cycle reads. `no_target` is the only state with
    nothing for anybody to act on; `target_present` is good news and still needs a decision."""
    watch_script = _script()
    monkeypatch.setattr(watch_script, "ROOT", tmp_path)
    monkeypatch.setattr(watch_script, "read_source",
                        lambda: D.DeploymentRead(D.TargetState.NO_TARGET,
                                                 identity_addresses=(IDENTITY_ADDRESS,),
                                                 reputation_addresses=(REPUTATION_ADDRESS,)))
    assert watch_script.main() == 0
    got = json.loads((tmp_path / D.RECORD).read_text(encoding="utf-8"))
    assert got[D.MEASUREMENT]["state"] == "no_target"
    assert got[D.ATTEMPT]["state"] == "no_target"

    monkeypatch.setattr(watch_script, "read_source",
                        lambda: D.DeploymentRead(D.TargetState.TARGET_PRESENT,
                                                 validation_addresses=(INVENTED_ADDRESS,),
                                                 validation_rows=("| Sepolia | 0x… |",)))
    assert watch_script.main() == 1, "good news passed through with a zero exit"
    written = json.loads((tmp_path / D.RECORD).read_text(encoding="utf-8"))
    assert written[D.MEASUREMENT]["validation_registry_rows"] == ["| Sepolia | 0x… |"]


def test_the_recorded_reading_is_of_the_real_source_and_is_a_measurement():
    """The artefact in the tree, read as it stands.

    This is where the claim about the REAL document lives: the record was produced by this parser
    from the whole 25 KB of it, the anchors it found are published in the record beside the answer,
    and a reader can recompute both. `checked_at` is the date the task was asked to write down.
    """
    whole = json.loads((ROOT / D.RECORD).read_text(encoding="utf-8"))
    assert whole["blocks"] == C.BLOCKED_STEP
    assert whole["source_repo"] == D.SOURCE_REPO
    # The last run and the last measurement are the same run here, and both are asserted: a record
    # whose attempt block had drifted from its measurement would mean the tree is carrying a
    # reading no recent run produced.
    assert whole[D.ATTEMPT]["state"] == D.TargetState.NO_TARGET.value, whole[D.ATTEMPT]
    record = whole[D.MEASUREMENT]
    assert record["state"] == D.TargetState.NO_TARGET.value, record["state"]
    assert record["checked_at"] == whole[D.ATTEMPT]["at"]
    assert record["validation_registry_addresses"] == []
    assert record["validation_registry_rows"] == []
    assert record["http_status"] == 200
    # The positive control has to be visible in the artefact, or a reader cannot tell this reading
    # from one taken with an instrument that had stopped looking.
    assert record["anchors"]["identity_registry_addresses"], record["anchors"]
    assert record["anchors"]["reputation_registry_addresses"], record["anchors"]

    # AND THE ARTEFACT MUST HAVE COME OUT OF THE CODE THAT SHIPS. The committed record was written
    # by a pre-dedup version of the parser and kept the same address twice in both anchor lists -
    # the exact inflated control the dedup was added to stop emitting, published in the deliverable
    # while an assertion that the lists were merely non-empty called it clean. A bug inherited by
    # an artefact from the code that produced it, read afterwards as though a person wrote it
    # (L-26). Found by Fable.
    for role, listed in record["anchors"].items():
        lowered = [a.lower() for a in listed]
        assert len(lowered) == len(set(lowered)), f"{role} counts one address twice: {listed}"


def test_the_incubator_is_meeting_its_own_watch_obligation():
    """A TIME BOMB, deliberately. It reads the tree at the real clock, and when it fails nothing is
    broken - the blocked step has simply gone unchecked for longer than the interval, which is the
    finding rather than the accident. The way past it is to run the watch.

    ASSERTED ON THE WHOLE SWEEP AND NOT ON A FILTERED SUBSET. The first draft filtered for findings
    naming this component and thereby excluded two of its own: `NOT MEASURED: the watch record at
    …` and `PARTIALLY READ: the watch record at …` carry the record's path rather than the
    component's name, so the time bomb had a hole exactly where the record goes missing - the
    fresh-clone state. A filter that has to enumerate the findings it is looking for is a control
    that stops at the ones somebody has already thought of (L-13). The sister suite asserts the
    same emptiness for the cohort; that is one measurement checked from both sides rather than a
    rule written twice, and either failing names the component in its own message.
    """
    out = C.sweep(datetime.now(timezone.utc))
    assert out == [], "\n".join(out)
