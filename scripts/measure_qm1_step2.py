#!/usr/bin/env python3
"""Q-M1 step 2: the specification 2.7 filter, measured over a sample of the identity registry.

Step 1 measured the POND: 50,275 identities on Ethereum mainnet. It deliberately refused to call
that the answer to Q-M1, because an ERC-8004 identity is an agent record and a subject under 2.7
is a business. This module measures the FILTER RATE, and it is the input the go/no-go verdict in
`src/governance/thresholds.py` has been waiting on with `qualifying_candidates = not_measured`.

THREE PHASES, ON PURPOSE.

  --collect           reads the chain and the web. It writes one record per sampled identity and
                      NOTHING else: no verdict, no rate, no judgement.
  --probe-operators   probes ONE declared endpoint per operator, because the operator is the unit
                      the question asks about and a per-identity rate cannot represent a bulk
                      minter. Also pure recording.
  --report            reads those files and computes the counts, the rates and the bounds. It
                      makes NO network call, so it is reproducible by anyone holding them, and
                      re-running it can never quietly change the evidence it reports on.

The classification of a resolved registration file against 2.7 is done BY HAND and stored in the
sample file as a label. That division is required: an LLM may read a registration file and reason
about whether it describes a business, but the arithmetic that turns labels into a number and
compares it to a ratified threshold is code, so the number cannot be argued into existence.

WHAT THE INSTRUMENTS CAN AND CANNOT SEE, stated before the result rather than after it.
2.7 requires ALL of: an observable result of activity; at least one 2.3 operation at level >= L3;
an identity that survives redeploy (see `docs/COHORT_EXCLUSIONS.md`, which is where this project
writes the condition out). Of those three, a public registration file can speak to the first and,
by construction, to the third - an ERC-8004 identity IS an identity that survives redeploy. It
cannot speak to the second AT ALL: no registration file carries the autonomy level of an
operation, and no remote read can establish one. So this measurement counts CANDIDATES FOR INTAKE
and is an UPPER BOUND on 2.7 qualification, which is exactly what `CANDIDATES_GO` counts - the
mandate stage downstream is where the L3 condition is settled, with the subject's cooperation.
Reporting it as "qualifying subjects" would be a claim stronger than its artefact.
"""
from __future__ import annotations

import base64
import binascii
import json
import math
import pathlib
import subprocess
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLE_FILE = ROOT / "evidence" / "QM1-002-sample.json"
OPERATOR_FILE = ROOT / "evidence" / "QM1-003-operators.json"

IDENTITY_REGISTRY = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
RPC = "https://ethereum-rpc.publicnode.com"
SELECTOR_TOKEN_URI = "0xc87b56dd"       # tokenURI(uint256), the agentURI of EIP-8004
NONEXISTENT_TOKEN_ERROR = "0x7e273289"  # ERC721NonexistentToken(uint256)

POPULATION = 50275
"""MEASURED, step 1, 2026-08-19 - the highest existing agentId. Recorded in this file as an input
to the extrapolation, and it is a CEILING on the identity count rather than the count itself: it
says nothing about whether every id below it was minted. This sample measures that too."""

SAMPLE_SIZE = 100
"""ASSIGNED. The task's own figure, and it sets the resolution of the answer: one identity in the
sample is one percent, which is 503 identities once extrapolated. Against a threshold of 30 that
resolution is coarse in absolute terms and irrelevant in practice - the threshold sits at 0.06% of
the population, two orders of magnitude below what a single sample point can resolve."""

CALL_CEILING = 300
"""DECLARED IN ADVANCE, the way step 1 declared 40. The host budget is one process and a shared
disk; an uncapped sweep over a registry is how a measurement becomes an incident. Reaching the
ceiling stops the run and says so - it never truncates silently and calls the short read a result."""

Z_95 = 1.959964
"""ASSIGNED. The two-sided 95% normal quantile, used for the Wilson interval below. It is a
convention about how much sampling error to admit, not a measurement of anything."""

IPFS_GATEWAY = "https://ipfs.io/ipfs/"
"""A SUBSTITUTION, and named as one. `ipfs://` has no resolver on this host, so a public gateway
stands in. A gateway failure is therefore OUR instrument failing, not the subject's file being
absent, and it is recorded as `card_unreadable` for that reason."""

CURL_FAILURE = {6: "DNS did not resolve the host", 7: "connection refused",
                28: "timed out", 35: "TLS handshake failed", 60: "TLS certificate not trusted"}
"""A NUMBER IS NOT A REASON. `rc=35` in an evidence file is a fact nobody can act on, and the
difference between "the host does not resolve" and "the host serves no certificate" is the
difference between a subject that moved and a subject whose artefact is gone. Codes outside this
map are reported as a transport failure WITH the code, never silently as one of the named ones."""

ABI_STRING_HEADER_CHARS = 130
"""STRUCTURAL, not policy: `0x` plus a 32-byte offset plus a 32-byte length, in hex characters.
The shortest possible ABI-encoded `string` return, and a shorter one is malformed rather than
empty. Named because ABI-16-10 forbids a bare number at a comparison and the gate caught this one
sitting in an `if` - where a reader cannot tell a protocol constant from a tuned threshold, which
is the confusion the rule exists to prevent."""

HTTP_OK = 200
MAX_CARD_BYTES = 200_000
"""Structural. A registration file larger than this is not read into memory on a 1.5 GB host."""

# --- the states a sampled identity can be in --------------------------------------------------
#
# LAW-NOT-MEASURED, applied to a survey. The temptation in a filter measurement is a denominator
# of "everything we drew" and a numerator of "everything that matched", with every failure to read
# silently joining the non-matchers. That is the seven-instance defect in survey clothing: it
# turns an instrument failure into evidence AGAINST the subject. These five states are disjoint
# and they are counted separately all the way to the published number.
S_TOKEN_ABSENT = "token_absent"        # the chain answered: this id was never minted, or was burned
S_RPC_UNREADABLE = "rpc_unreadable"    # the chain did not answer - our instrument, not their record
S_NO_REGISTRATION = "no_registration"  # the chain answered: agentURI is empty, no file is declared
S_CARD_UNREADABLE = "card_unreadable"  # a file is declared and it does not resolve for us
S_CARD_READ = "card_read"              # we hold the registration file; a human label decides it

ALL_STATES = (S_TOKEN_ABSENT, S_RPC_UNREADABLE, S_NO_REGISTRATION, S_CARD_UNREADABLE, S_CARD_READ)

# --- labels a human may attach to a card_read record -------------------------------------------
L_CANDIDATE = "candidate"          # passes every 2.7 condition that a public artefact can carry
L_NOT_A_BUSINESS = "not_a_business"  # agent-as-a-function, copilot, demo, placeholder - 2.7 excludes
L_UNLABELLED = "unlabelled"        # collected but not yet classified - NOT a zero, NOT a rejection

_calls = {"n": 0}


def _curl(args: list[str]) -> tuple[int, str]:
    """One external call, counted against the declared ceiling. Returns (returncode, stdout)."""
    if _calls["n"] >= CALL_CEILING:
        raise SystemExit(f"declared ceiling of {CALL_CEILING} external calls reached - "
                         f"stopping honestly rather than returning a short read as a result")
    _calls["n"] += 1
    try:
        p = subprocess.run(["curl", "-s", *args], capture_output=True, text=True, timeout=40)
    except (subprocess.SubprocessError, OSError) as e:
        return -1, f"{type(e).__name__}"
    return p.returncode, p.stdout


def read_agent_uri(agent_id: int) -> tuple[str, str]:
    """Read `tokenURI(agentId)`. Returns (state, value) where value is the URI or the reason.

    THE THREE OUTCOMES ARE THREE DIFFERENT FACTS about the world and are kept apart here, at the
    point of reading, because that is the only place the difference still exists. A revert with
    ERC721NonexistentToken means the id was never minted; an empty string means the identity is
    real and declares no registration file; a transport failure means we did not ask successfully.
    """
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                       "params": [{"to": IDENTITY_REGISTRY,
                                   "data": SELECTOR_TOKEN_URI + f"{agent_id:064x}"}, "latest"]})
    rc, out = _curl(["--max-time", "25", "-X", "POST", "-H", "Content-Type: application/json",
                     "-d", body, RPC])
    if rc != 0:
        return S_RPC_UNREADABLE, f"curl rc={rc} {out[:60]}"
    try:
        got = json.loads(out or "{}")
    except json.JSONDecodeError:
        return S_RPC_UNREADABLE, "rpc returned a non-JSON body"
    if "error" in got:
        data = str(got["error"].get("data", ""))
        if data.startswith(NONEXISTENT_TOKEN_ERROR):
            return S_TOKEN_ABSENT, "ERC721NonexistentToken"
        return S_RPC_UNREADABLE, f"rpc error: {str(got['error'])[:80]}"
    raw = got.get("result") or ""
    if not raw.startswith("0x") or len(raw) < ABI_STRING_HEADER_CHARS:
        return S_RPC_UNREADABLE, "malformed ABI string return"
    payload = raw[2:]
    length = int(payload[64:128], 16)
    if length == 0:
        return S_NO_REGISTRATION, ""
    try:
        uri = bytes.fromhex(payload[128:128 + length * 2]).decode("utf-8", "replace")
    except ValueError:
        return S_RPC_UNREADABLE, "ABI string body did not decode"
    return S_CARD_READ, uri


def fetch_card(uri: str) -> tuple[bool, str, str]:
    """Resolve a registration file. Returns (ok, body_or_empty, reason).

    `ok=False` NEVER means "the agent is not a business". It means we could not read the file, and
    the caller keeps that in a separate bucket all the way to the report.
    """
    # THE agentURI IS NOT ALWAYS A URI, AND THE FIRST VERSION OF THIS READER SAID SO WRONGLY.
    # A run of identities stores the registration document ITSELF in the tokenURI slot - a bare
    # JSON object, no `data:` prefix, no scheme. The reader split on ":", found `{"name"` where a
    # scheme should be, and filed five readable documents as `unsupported scheme`. That is L-10
    # exactly: an instrument that cannot see a quantity reporting its absence, and it would have
    # moved five identities out of the classified set and into the unknown band, widening the
    # published uncertainty with our own defect. Content in a slot meant for a pointer is still
    # content.
    stripped = uri.strip()
    if stripped.startswith("{"):
        return True, stripped, "inline document (agentURI holds the file, not a pointer to it)"
    scheme = uri.split(":", 1)[0].lower() if ":" in uri else ""
    if uri.startswith("data:"):
        head, _, b64 = uri.partition(",")
        if "base64" not in head:
            return True, urllib.parse.unquote(b64), "inline data URI"
        try:
            return True, base64.b64decode(b64 + "===").decode("utf-8", "replace"), "inline data URI"
        except (binascii.Error, ValueError):
            return False, "", "inline data URI did not base64-decode"
    if scheme == "ipfs":
        target = IPFS_GATEWAY + uri[len("ipfs://"):]
    elif scheme in ("http", "https"):
        target = uri
    else:
        return False, "", f"unsupported scheme {scheme[:12] or '(none)'} - our reader, not their file"

    rc, out = _curl(["-L", "--max-time", "12", "--connect-timeout", "6",
                     "--max-filesize", str(MAX_CARD_BYTES),
                     "-w", "\n%{http_code}", target])
    if rc != 0:
        return False, "", f"{CURL_FAILURE.get(rc, 'transport failure')} (curl rc={rc})"
    body, _, code = out.rpartition("\n")
    if code.strip() != str(HTTP_OK):
        return False, "", f"http {code.strip() or '(none)'}"
    return True, body, f"http {HTTP_OK}"


def host_of(uri: str) -> str:
    """The host an agentURI points at, or a named non-host.

    TWO THINGS ARE NOT HOSTS AND WERE BOTH COUNTED AS ONE. An inline document points at nobody,
    and an `ipfs://` CID is a CONTENT HASH - the same bytes are served by every gateway and by
    none in particular, so it identifies a file and never an operator. Counting either in a tally
    of hosts inflates the operator picture by exactly the rows that carry no operator information,
    which is the defect this function's first version committed twice over.
    """
    if not uri.strip().startswith(("http://", "https://", "ipfs://")):
        return "(inline)"
    if uri.startswith("ipfs://"):
        return "(content-addressed)"
    return urllib.parse.urlparse(uri).netloc[:80]


def _first_endpoint(d: dict) -> str:
    """The first declared service endpoint, or "". Stored so the OPERATOR probe is reproducible.

    Structural and ASCII, so it can be committed without carrying wild prose onto an English-only
    surface - and without it the operator-level probe would be reproducible only on the host that
    still holds the raw bodies, which is the same defect as a passport nobody can recompute.
    """
    gettable, other = [], []
    for key in ("services", "capabilities", "endpoints", "skills"):
        v = d.get(key)
        items = list(v.values()) if isinstance(v, dict) else v
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, str) and item.startswith("http"):
                gettable.append(item)
            elif isinstance(item, dict):
                for field in ("endpoint", "url", "uri", "href"):
                    got = item.get(field)
                    if isinstance(got, str) and got.startswith("http"):
                        method = str(item.get("method", "GET")).upper()
                        (gettable if method == "GET" else other).append(got)
                        break
    # A DECLARED METHOD IS DATA, AND IGNORING IT MANUFACTURED A FAILURE. The first version took the
    # first endpoint in `capabilities` whatever its method, so for one operator it chose a POST-only
    # critique endpoint; the GET probe came back HTTP 400, and that read as "this operator serves
    # nothing" when the card had said `"method": "POST"` in the same object and carried a top-level
    # `url` a GET is meant for. An instrument that selects the one endpoint it cannot read, then
    # reports the result as the subject's silence, is L-10 with the evidence to avoid it in hand.
    if gettable:
        return gettable[0][:200]
    url = d.get("url")
    if isinstance(url, str) and url.startswith("http"):
        return url[:200]
    return other[0][:200] if other else ""


def card_shape(body: str) -> dict:
    """Structural facts about a registration file. NO free text is carried out of this function.

    Wild registration files hold arbitrary prose in arbitrary languages, and the GitHub surface of
    this repository is English-only by operator ruling. So the committed evidence keeps counts and
    the URI - enough for a third party to refetch and disagree - and not the prose itself.
    """
    try:
        d = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return {"parsed": False}
    if not isinstance(d, dict):
        return {"parsed": False}
    # COUNT EVERY CONTAINER SHAPE, NOT THE ONE WE EXPECTED. The first version counted `endpoints`
    # only when it was a list and did not look at `services` at all. FREAK #923 declares its three
    # endpoints as a DICT, Signalbound declares twenty-two `services`, Normies two - and all of
    # them were recorded as `endpoints: 0`. The committed evidence file was therefore blind to the
    # single field the contested labels turn on, and blind in the direction of the conclusion:
    # every row we called "nothing declared" would have read as nothing declared to a checker too.
    # An instrument that cannot see a quantity reporting it as zero is L-10, and pointing it at
    # our own evidence is worse than pointing it at the chain.
    def _count(value: object) -> int:
        if isinstance(value, (list, dict)):
            return len(value)
        return 0

    return {"parsed": True, "first_endpoint": _first_endpoint(d),
            "type_is_eip8004": str(d.get("type", "")).endswith("#registration-v1"),
            "has_name": bool(str(d.get("name", "")).strip()),
            "description_chars": len(str(d.get("description", "") or "")),
            "skills": _count(d.get("skills")),
            "endpoints": _count(d.get("endpoints")),
            "services": _count(d.get("services")),
            "capabilities": _count(d.get("capabilities")),
            "registrations": _count(d.get("registrations")),
            "keys": sorted(k for k in d if isinstance(k, str))[:24]}


def sample_ids() -> list[int]:
    """Systematic sample: evenly spaced across the whole id space, no seed, fully reproducible.

    WHY SYSTEMATIC AND NOT RANDOM. agentIds are assigned incrementally, so the id axis is the time
    axis. An evenly spaced sample covers the registry's whole history in proportion, and it needs
    no seed to be reproducible by a reader - `round(k * 50275 / 100)` is the entire method.

    THE RISK IT CARRIES, named rather than left for someone else to find: systematic sampling
    aliases against periodic structure. If identities were minted in runs whose period shares a
    factor with the stride of 503, such a run would be over- or under-represented. Batch mints in
    this registry are far shorter than the stride, so the exposure is small - but it is a property
    of the design, not an absence of one.
    """
    return [round(k * POPULATION / SAMPLE_SIZE) for k in range(1, SAMPLE_SIZE + 1)]


def collect(raw_dir: pathlib.Path) -> int:
    """Phase one. Read the chain and the web; write one record per identity. No verdict is formed."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "qm1_step2_cards.jsonl"
    previous = {r["id"]: r for r in _load_records()} if SAMPLE_FILE.exists() else {}

    records, raw_lines = [], []
    for agent_id in sample_ids():
        state, value = read_agent_uri(agent_id)
        rec = {"id": agent_id, "state": state, "uri": "", "detail": value,
               "label": L_UNLABELLED, "rationale": ""}
        if state == S_CARD_READ:
            uri = value
            rec["uri"] = uri[:160]
            # The host is extracted and stored because CONCENTRATION is a property of the
            # population that a per-identity count cannot show: a registry of 50,275 identities
            # whose files sit behind a handful of hostnames is a different market from one with
            # 50,275 operators, and the go/no-go question is about operators.
            rec["host"] = host_of(uri)
            ok, body, reason = fetch_card(uri)
            rec["detail"] = reason
            if not ok:
                rec["state"] = S_CARD_UNREADABLE
            else:
                rec["shape"] = card_shape(body)
                raw_lines.append(json.dumps({"id": agent_id, "uri": uri, "body": body[:20000]}))
        # A label already given by hand survives a re-collection: the human read is evidence too,
        # and silently discarding it would make every re-run cost the classification again.
        prior = previous.get(agent_id)
        if prior and prior.get("label", L_UNLABELLED) != L_UNLABELLED:
            rec["label"], rec["rationale"] = prior["label"], prior.get("rationale", "")
        records.append(rec)
        print(f"  {agent_id:>6}  {rec['state']:<17} {rec['detail'][:60]}", file=sys.stderr)

    raw_path.write_text("\n".join(raw_lines) + "\n", encoding="utf-8")
    SAMPLE_FILE.write_text(json.dumps(
        {"population_ceiling": POPULATION, "sample_size": SAMPLE_SIZE,
         "identity_registry": IDENTITY_REGISTRY, "rpc": RPC,
         "external_calls_used": _calls["n"], "call_ceiling": CALL_CEILING,
         "records": records}, indent=1) + "\n", encoding="utf-8")
    print(f"\ncollected {len(records)} records using {_calls['n']} of {CALL_CEILING} calls",
          file=sys.stderr)
    print(f"registration files for hand classification: {raw_path}", file=sys.stderr)
    return 0


# --- the states an OPERATOR probe can be in ----------------------------------------------------
#
# THE SAME THREE-WAY SPLIT AS THE IDENTITY LEVEL, and it is here because the first version of this
# phase did not have it. That version counted `http 200` as live and let everything else fall into
# an unnamed remainder, so a POST-only endpoint we had queried with GET and a host that never
# replied both read as "this operator serves nothing". That is LAW-SURVEY-ABSENCE broken by the
# very phase written to satisfy it, and L-23 broken by its own author in the commit that wrote it.
OP_LIVE = "live"                    # answered, with a body: an artefact a third party can observe
OP_NO_ARTEFACT = "no_artefact"      # answered authoritatively, and there was nothing there
OP_NOT_MEASURED = "not_measured"    # we did not obtain an answer, or asked the wrong way
OP_STATES = (OP_LIVE, OP_NO_ARTEFACT, OP_NOT_MEASURED)

HTTP_CLIENT_ERROR = 400
HTTP_SERVER_ERROR = 500


def operator_state(o: dict) -> str:
    """Classify one operator probe. A refusal aimed at OUR request is never the subject's silence.

    `http 404` is the operator answering that nothing is there - measured. `http 400`/`405` is the
    operator rejecting the request WE made, which says nothing about what a correct request would
    return. A 5xx and a transport failure are refusals to answer at all.
    """
    if o["bytes"] is None:
        return OP_NOT_MEASURED
    code = o["result"].removeprefix("http ").strip()
    if not code.isdigit():
        return OP_NOT_MEASURED
    status = int(code)
    if status == HTTP_OK:
        # A 200 WITH AN EMPTY BODY IS NOT AN ARTEFACT - the same rule `apply_soft_404_rule` applies
        # one phase earlier, which this function had unlearned until it was pointed out.
        return OP_LIVE if o["bytes"] > 0 else OP_NO_ARTEFACT
    if status >= HTTP_SERVER_ERROR:
        return OP_NOT_MEASURED
    if status == HTTP_CLIENT_ERROR or status == 405:  # noqa: PLR1714 - two distinct reasons
        return OP_NOT_MEASURED
    return OP_NO_ARTEFACT


def tally_operators(ops: list[dict]) -> dict[str, int]:
    """Count operator probes into the three disjoint states. Deterministic; no network."""
    counts = dict.fromkeys(OP_STATES, 0)
    for o in ops:
        counts[operator_state(o)] += 1
    return counts


def probe_operators() -> int:
    """Phase three: probe ONE declared endpoint per operator, because the operator is the unit.

    WHY THIS PHASE EXISTS, and it is a correction rather than an extension. The per-identity rate
    published by `--report` structurally CANNOT count a bulk-minted business: an operator whose
    entire registry presence is ten thousand member rows contributes ten thousand rows that are
    each correctly labelled "not a business in its own right", and therefore contributes ZERO
    candidates - when the honest answer is one. Fable refuted the first draft of this measurement
    on exactly that, and the refutation held: the document had reached for the precedent that
    excluded `realestate`, which excludes a subject for OVERLAPPING one already counted, and here
    nothing was counted for them to overlap.

    So this phase asks the 2.7 question at the operator level, and it asks it by MEASUREMENT
    rather than by reading the card: does the operator's own declared endpoint return anything?
    "The card declares a service" is a claim; "the endpoint answered with N bytes" is an artefact.
    That distinction is the entire product, and applying it to ourselves is not optional.
    """
    records = _load_records()
    first: dict[str, dict] = {}
    for r in records:
        endpoint = r.get("shape", {}).get("first_endpoint")
        if endpoint and r.get("host") and r["host"] not in first:
            first[r["host"]] = {"operator": r["host"], "from_agent_id": r["id"],
                                "endpoint": endpoint}
    rows = []
    for op in first.values():
        rc, out = _curl(["-L", "--max-time", "15", "--connect-timeout", "8",
                         "--max-filesize", str(MAX_CARD_BYTES), "-w", "\n%{http_code}",
                         op["endpoint"]])
        if rc != 0:
            op["result"] = CURL_FAILURE.get(rc, f"transport failure rc={rc}")
            op["bytes"] = None      # None, not 0: we did not get a body, we did not get zero bytes
        else:
            body, _, code = out.rpartition("\n")
            op["result"] = f"http {code.strip()}"
            op["bytes"] = len(body)
        rows.append(op)
        print(f"  {op['operator']:<24} {op['result']:<12} {op['bytes']} bytes", file=sys.stderr)

    OPERATOR_FILE.write_text(json.dumps({"external_calls_used": _calls["n"],
                                     "operators": rows}, indent=1)
                             + "\n", encoding="utf-8")
    print(f"\n{len(rows)} operators probed using {_calls['n']} calls -> {OPERATOR_FILE}",
          file=sys.stderr)
    return 0


def _load_records() -> list[dict]:
    return json.loads(SAMPLE_FILE.read_text(encoding="utf-8"))["records"]


def wilson_interval(successes: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Both ends of the Wilson score interval for a proportion.

    Wilson rather than the normal approximation because the proportion here sits AT zero, where
    the normal interval produces a lower bound below zero and a coverage that is not the coverage
    it advertises. The finite-population correction is sqrt((N-n)/(N-1)) = 0.999 at n=100 of
    N=50,275, so it is omitted - named, not forgotten.

    BOTH ENDS, because the first version returned only the lower one and called it "the
    conservative floor". At zero successes the lower end is identically zero: it admits no
    sampling error, because there is none available downward. The only end carrying information
    about a zero count is the UPPER one - 0 of 100 is consistent with a rate near 3.6%, which is
    ~1,800 identities and far above the threshold of 30. Publishing the tail that cannot move and
    calling it conservatism is a false precision, and it is the reason this returns a pair.
    """
    if n == 0:
        raise ValueError("a proportion over an empty sample is not a small proportion, it is none")
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z / denom * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, centre - half), min(1.0, centre + half)


def apply_soft_404_rule(records: list[dict]) -> None:
    """A 200 IS NOT AN ARTEFACT. Demote a "read" whose body is not a JSON object to unreadable.

    One host answered every request with its single-page-app shell - HTTP 200, `text/html`, no
    registration file anywhere in it. The collector recorded exactly what happened (a body
    arrived, and it did not parse as a JSON object); this is where that becomes a judgement,
    because the collector's job is to record and the report's job is to decide.

    The demotion is to UNREADABLE and never to `not_a_business`. That direction is the whole
    point: a soft 404 counted as a read file would put four HTML error pages in front of a human
    to classify as businesses, and whatever they were then labelled would be a measurement of a
    web server's error page rather than of the market.
    """
    for r in records:
        if r["state"] == S_CARD_READ and not r.get("shape", {}).get("parsed"):
            r["state"] = S_CARD_UNREADABLE
            r["detail"] = f"{r['detail']} but the body is not a JSON object (soft 404)"


def tally(records: list[dict]) -> dict:
    """Count the sample into disjoint buckets. Raises on a state it cannot classify.

    THE TWO CATEGORIES OF ABSENCE ARE SEPARATED HERE, in the arithmetic, not in a footnote under
    it. `unknown` is every identity we FAILED TO READ. `nothing_qualified` is every identity we
    DID read and which does not describe a business. Collapsing them would answer a question
    nobody asked - and would answer it in whichever direction happened to be convenient.
    """
    counts = {s: 0 for s in ALL_STATES}
    for r in records:
        if r["state"] not in counts:
            raise ValueError(f"unknown state {r['state']!r} on id {r['id']} - a state the report "
                             f"cannot classify is not a state it may ignore")
        counts[r["state"]] += 1
    if sum(counts.values()) != len(records):
        raise ValueError("the states do not partition the sample")

    read = [r for r in records if r["state"] == S_CARD_READ]
    unlabelled = [r for r in read if r.get("label", L_UNLABELLED) == L_UNLABELLED]
    candidates = [r for r in read if r.get("label") == L_CANDIDATE]
    not_business = [r for r in read if r.get("label") == L_NOT_A_BUSINESS]
    return {"counts": counts, "n": len(records),
            "candidates": len(candidates), "not_business": len(not_business),
            "unlabelled": len(unlabelled),
            "unknown": counts[S_RPC_UNREADABLE] + counts[S_CARD_UNREADABLE] + len(unlabelled),
            "nothing_qualified": (counts[S_TOKEN_ABSENT] + counts[S_NO_REGISTRATION]
                                  + len(not_business))}


def report() -> int:
    """Phase two. Arithmetic only, from the recorded states. This is the deterministic verdict."""
    if not SAMPLE_FILE.exists():
        sys.stderr.write(f"no sample at {SAMPLE_FILE} - run --collect first. This is "
                         f"'the measurement has not run', not 'the rate is zero'\n")
        return 1
    records = _load_records()
    apply_soft_404_rule(records)
    try:
        t = tally(records)
    except ValueError as e:
        sys.stderr.write(f"{e}\n")
        return 1
    n, counts = t["n"], t["counts"]
    unknown, nothing_qualified = t["unknown"], t["nothing_qualified"]
    candidates, not_business, unlabelled = t["candidates"], t["not_business"], t["unlabelled"]

    print("=== Q-M1 step 2: the specification 2.7 filter, measured ===")
    print(f"population ceiling (step 1, measured): {POPULATION} agentIds")
    print(f"sample: {n} ids, systematic, stride {POPULATION / SAMPLE_SIZE:.2f}, "
          f"ids {records[0]['id']}..{records[-1]['id']}")
    print()
    print("what the instruments returned, per identity:")
    for s in ALL_STATES:
        print(f"  {s:<18} {counts[s]:>4}")
    print()
    print("hand classification of the registration files that resolved:")
    print(f"  {L_CANDIDATE:<18} {candidates:>4}   passes every 2.7 condition a public file carries")
    print(f"  {L_NOT_A_BUSINESS:<18} {not_business:>4}   read, and 2.7 excludes it")
    print(f"  {L_UNLABELLED:<18} {unlabelled:>4}   collected, not yet classified - not a rejection")
    print()
    print("THE TWO ABSENCES, kept apart (specification 2.9, law L-1):")
    print(f"  unreadable          {unknown:>4}   we did not obtain the evidence")
    print(f"  nothing_qualified   {nothing_qualified:>4}   we obtained it and nothing there qualifies")
    print()

    if candidates + not_business == 0:
        print("VERDICT INPUT: not_measured - no registration file was both read and classified.")
        return 0

    lo_rate = candidates / n                       # every unread identity assumed to fail
    hi_rate = (candidates + unknown) / n           # every unread identity assumed to pass
    w_lo, w_hi = wilson_interval(candidates, n)

    print("RATE, with the unreadable band shown rather than resolved:")
    print(f"  lower  {lo_rate * 100:6.2f}%  every unreadable identity counted as NOT a candidate")
    print(f"  upper  {hi_rate * 100:6.2f}%  every unreadable identity counted as a candidate")
    print(f"  sampling error on the lower rate (Wilson 95%): {w_lo * 100:.2f}% to {w_hi * 100:.2f}%")
    print()
    print("EXTRAPOLATION to the population:")
    print(f"  point estimate            {round(lo_rate * POPULATION):>7} external candidate identities")
    print(f"  sampling error alone      {round(w_lo * POPULATION):>7} to {round(w_hi * POPULATION)} "
          f"(the unreadable all counted against)")
    print(f"  unreadable counted for    {round(hi_rate * POPULATION):>7}")
    print()
    print("WHAT THIS NUMBER IS: identities whose public registration file describes a business "
          "operation with an observable result - CANDIDATES FOR INTAKE.")
    print("WHAT IT IS NOT: the count of subjects qualifying under 2.7. The 2.3 operation at level "
          ">= L3 is `not_measured` for every row and cannot be read remotely, so this is a CEILING "
          "on qualification and the mandate stage is where it is settled.")
    print()
    _print_concentration(records)
    _print_operators(records)
    _print_verdict_at_both_ends(round(lo_rate * POPULATION), round(hi_rate * POPULATION))
    return 0


def _print_operators(records: list[dict]) -> None:
    """The same 2.7 question asked at the OPERATOR level, where a bulk minter is one entity.

    THE PER-IDENTITY RATE ABOVE CANNOT COUNT A BULK-MINTED BUSINESS, and printing it alone was the
    defect Fable refuted: ten thousand rows each correctly labelled "not a business in its own
    right" sum to zero candidates, when the honest answer for that operator is one. The rows and
    the operators are two different questions and both are printed, because answering the easy one
    and letting a reader assume it was the hard one is how a measurement misleads without lying.

    NOT EXTRAPOLATED, and the missing phase is named rather than implied: a sample of identities is
    not a sample of operators, so nothing here scales to the population.
    """
    if not OPERATOR_FILE.exists():
        print()
        print("OPERATOR LEVEL: not_measured - run --probe-operators. This is 'the probe has not "
              "run', not 'no operator qualifies'.")
        return
    ops = json.loads(OPERATOR_FILE.read_text(encoding="utf-8"))["operators"]
    probed = {o["operator"] for o in ops}
    # THE HOSTS THE PROBE COULD NOT REACH ARE NAMED, not omitted. Four of the eight hosts declared
    # no endpoint we could extract - three because no registration file was obtained from them at
    # all, one because its file was a soft 404. Printing only the probed four would show "4
    # operators, 2 live" over a denominator the reader would take for the whole set, which is the
    # same absence collapse this file exists to refuse, committed one level up from the rows.
    unprobed = sorted({r["host"] for r in records
                       if r.get("host") and r["host"] not in ("(inline)", "(content-addressed)")
                       and r["host"] not in probed})
    print()
    print("OPERATOR LEVEL - one declared endpoint probed per operator (the 2.7 'observable result "
          "of activity' condition, measured rather than read off the card):")
    for o in ops:
        # `bytes` is None when no body was obtained. It is NOT 0: "the endpoint returned nothing"
        # and "we never got a reply" are the two states this whole document exists to separate.
        size = "no body obtained" if o["bytes"] is None else f"{o['bytes']} bytes"
        print(f"  {o['operator']:<26} {o['result']:<26} {size:<18} {operator_state(o)}")
    counts = tally_operators(ops)
    print(f"  {counts[OP_LIVE]} live, {counts[OP_NO_ARTEFACT]} answered without an artefact, "
          f"{counts[OP_NOT_MEASURED]} not_measured of {len(ops)} probed.")
    if unprobed:
        print(f"  NOT PROBED, and therefore not_measured rather than not live - {len(unprobed)} "
              f"of {len(ops) + len(unprobed)} hosts declared no endpoint we could extract:")
        for h in unprobed:
            print(f"    {h}")
        print("    (their registration files were never obtained, so the absence of an endpoint "
              "here is OUR gap and not their silence)")
    print("  The count of operators IN THE POPULATION is not_measured: a sample of identities is "
          "not a sample of operators, and no number here may be multiplied by the stride.")


def _print_concentration(records: list[dict]) -> None:
    """Where the declared registration files live.

    THIS IS THE FINDING THE PER-IDENTITY RATE CANNOT CARRY. Q-M1 asks how many BUSINESSES exist,
    and the registry's unit is an identity. If one operator mints ten thousand identities for one
    collection, the identity count answers a question nobody asked. Host is a weak proxy for
    operator - two hosts may be one company and one host may resell to many - so this is printed
    as an observation with its proxy named, and it is NOT extrapolated: estimating how many
    DISTINCT operators exist in a population from a sample is a species-richness problem, and
    multiplying a sample count by 503 is not an estimator of it.
    """
    hosts: dict[str, int] = {}
    for r in records:
        h = r.get("host")
        if h:
            hosts[h] = hosts.get(h, 0) + 1
    if not hosts:
        return
    print("WHERE THE DECLARED FILES LIVE (host as a weak proxy for operator, not extrapolated):")
    for h, c in sorted(hosts.items(), key=lambda kv: -kv[1]):
        print(f"  {c:>4}  {h}")
    # `(inline)` IS NOT A HOST, and counting it as one inflated the operator bound by exactly one
    # in the first draft of this report - which reached the document as "10 distinct hosts" over a
    # denominator that had folded the inline records in beside them. An identity carrying its own
    # document points at nobody, and it says nothing about who operates it.
    inline = hosts.pop("(inline)", 0)
    cid = hosts.pop("(content-addressed)", 0)
    print(f"  ({inline} inline, {cid} content-addressed - neither names an operator)")
    # NOT A BOUND IN EITHER DIRECTION, which is a correction of this line's first version. It
    # called the host count "a LOWER BOUND on operators" three lines under the docstring admitting
    # two hosts may be one company - and if that is true, distinct hosts do not bound operators
    # from below. It is a count of hosts. That is all it is, and it is worth printing because the
    # concentration is visible in it, not because it bounds anything.
    print(f"  distinct hosts in the sample: {len(hosts)} across {sum(hosts.values())} files - "
          f"a count of HOSTS, which bounds the operator count in neither direction: one company "
          f"may serve several hosts and one host may serve several companies")


def _print_verdict_at_both_ends(low: int, high: int) -> None:
    """Run the RATIFIED go/no-go code at both ends of the unreadable band.

    The verdict is not argued here and it is not restated here; it is computed by
    `src.governance.thresholds.evaluate`, the same function that will decide it in production,
    from the thresholds the operator ratified on 2026-08-19. Running it at BOTH ends is the point:
    if the two ends disagree the band must be narrowed before anyone decides, and if they agree
    then the band - however wide - does not bind, and narrowing it would be work that changes
    nothing.
    """
    sys.path.insert(0, str(ROOT))
    from src.abs_profile.measured import Measurement, NotMeasured
    from src.governance import thresholds as th

    unmeasured = Measurement(absent=NotMeasured.CHECK_DID_NOT_RUN)
    print()
    print("GO/NO-GO, computed by src/governance/thresholds.py at BOTH ends of the band:")
    reached = []
    for label, value in (("lower", low), ("upper", high)):
        verdict, why = th.evaluate(th.Inputs(qualifying_candidates=Measurement(value=value),
                                             mandates_granted=unmeasured,
                                             days_since_clock_start=unmeasured))
        reached.append(verdict)
        print(f"  {label:<6} {value:>7} candidates -> {verdict.value.upper():<12} {why}")

    # READ FROM THE VERDICTS, NOT ASSERTED BESIDE THEM. This sentence said "neither end is GO and
    # neither is STOP" as a fixed string, three lines under the loop that computes whether that is
    # true. It was correct on the day it was written, which is precisely the property that makes a
    # hardcoded conclusion dangerous: it survives the change that falsifies it.
    terminal = {th.Verdict.GO, th.Verdict.STOP}
    if terminal.isdisjoint(reached):
        # WHAT BINDS DIFFERS BY END, and saying "the mandate stage binds" for both was wrong at
        # the lower one: below CANDIDATES_REVISIT the mandate gate is never reached, and what
        # `thresholds.py` actually demands there is the second-window growth measurement. A fixed
        # sentence under a loop that computes two different verdicts is the same defect as a fixed
        # conclusion beside a computed one - it just hid behind being half true.
        binds = {th.Verdict.REVISIT: "a second-window growth measurement",
                 th.Verdict.NOT_MEASURED: "the unmeasured mandate and clock inputs"}
        print("  No end of the band is GO or STOP, so the band's WIDTH does not bind the decision.")
        for label, verdict in zip(("lower", "upper"), reached, strict=True):
            print(f"    at the {label} end, what binds is {binds.get(verdict, 'see the reason above')}")
    elif reached[0] == reached[1]:
        print(f"  Both ends agree on {reached[0].value.upper()}: the unreadable band does not "
              f"affect the decision and the verdict stands on the measurement as it is.")
    else:
        print(f"  THE ENDS DISAGREE ({reached[0].value.upper()} vs {reached[1].value.upper()}): "
              f"the unreadable band is load-bearing and MUST be narrowed before anyone decides.")


def main(argv: list[str]) -> int:
    if "--probe-operators" in argv:
        return probe_operators()
    if "--collect" in argv:
        i = argv.index("--raw-dir") if "--raw-dir" in argv else -1
        raw = pathlib.Path(argv[i + 1]) if i >= 0 else pathlib.Path.home() / "orchestra"
        return collect(raw)
    return report()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
