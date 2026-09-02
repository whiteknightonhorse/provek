"""Phase 2 - the subject's OWN accountability declaration (`provek.json`), ratified design.

WHAT THIS READS. A subject may publish `provek.json` at the root of its repository, declaring who
answers a claim, whether an emergency stop exists, whether insurance exists, and where a dispute
goes (schema 1.0.0 - see the four `accountability` sub-fields below). This is entirely SELF-
DECLARED: nothing here is independently verified, so every value this module produces carries
`confidence="assumed"` and NEVER `"measured"` (ABI-14-2, ABI-14-3). It does not raise a ladder
level, does not enter `verified`, and does not enter the projection - the accountability block sits
outside the score by construction (see `Accountability`'s own docstring in `src/passport/passport.py`).

PINNED TO A COMMIT ALREADY MEASURED. `head_sha` is never looked up here - it is handed in from
whichever base collector already read the subject (`src.collector.github.collect_github` or
`src.collector.repo.collect`), because a second call to `/repos/{full}/commits` would spend the
`api.github.com` budget a second time for a fact already on hand. Reading through
`raw.githubusercontent.com` instead spends NO budget at all - measured in phase 0 by comparing the
rate-limit headers before and after such a request - which is also why this collector goes through
`raw.githubusercontent.com` rather than the contents API. When no `head_sha` is available the read
falls back to the `HEAD` ref (raw.githubusercontent.com resolves it to the default branch) and is
marked not pinned.

FOUR WORLDS PER FIELD - collapsing any two reproduces the exact defect LAW-NOT-MEASURED exists to
forbid:
  1. declared with a value                                   -> measured=True,  value=X,   assumed
  2. declared explicitly ABSENT (`exists: false`, `type: "none"`) -> measured=True, value=None, assumed
  3. the file does not exist (404), OR the field is simply omitted -> reason=NotMeasured.NOT_DECLARED
  4. network failure, a non-404 error, broken JSON, or a document that does not match the schema
     -> Fact.unreadable(), with a note

World 3 and world 4 are DIFFERENT CLAIMS: 3 says the channel was read and the subject said nothing;
4 says the channel could not be read at all. A malformed field invalidates the WHOLE declaration
(never silently truncated, never partially trusted) because a document that misstates its own shape
in one place cannot be trusted anywhere else in it.

REDACTION IS MANDATORY on every string this module emits, before it can reach an artefact - reusing
`src.collector.github.redact`, the one place secret patterns are defined (LAW #ONE-PLACE).
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from urllib.parse import urlparse

from src.abs_profile.measured import NotMeasured
from src.collector.github import RateLimited, redact
from src.collector.reachability import SSRFRefused, resolve_public_ip
from src.passport.passport import Accountability, Fact, Service

RAW_HOST = "https://raw.githubusercontent.com"

FIELD_MAX_CHARS = 500
"""ASSIGNED. A declaration string longer than this is not truncated - the whole declaration is
treated as an invalid schema instead (the ratified boundary: 'exceeding it invalidates the
declaration, not silently truncates it'). Long enough for a legal name, a postal address, or a
one-line dispute-resolution clause; a document that needs more than that per field is not
plausibly describing one of these four facts, and treating it as one would let a subject smuggle
an essay - or an attack payload - into a field the UI renders as a short label."""

FORBIDDEN_CHARS = re.compile(r"[\[\]`]")
"""D-43. Angle brackets are not this boundary's problem - `NEVER_UNESCAPED` in
`web/html_to_markdown.mjs` already keeps `<`/`>` escaped wherever a declaration's text reaches a
rendered page. But markdown has its OWN injection surface that brackets do not touch: a value of
`[urgent: verify here](https://evil)` carries no angle bracket at all and still becomes a live link
the moment it is written into a `.md` file, because a markdown READER, not this converter, is what
turns `[text](url)` into a hyperlink. `web/markdown.mjs` writes `/p/<slug>/index.md` by interpolating
passport fields directly into template strings with no escaping step of its own (Fable's ruling,
D-43) - the one place in this project where our own markdown and a subject's declared text are
already mixed by the time anything downstream could tell them apart.

So this boundary - the only place ALL FOUR declared string fields already pass through, by the same
mechanism that enforces `FIELD_MAX_CHARS` - refuses `[`, `]` and a backtick outright, with the same
consequence as an oversized field: the WHOLE declaration is invalid, never silently stripped of the
offending character. A legal name, a postal address or a one-line dispute clause has no honest use
for any of the three; a document that needs one is not plausibly describing one of these four
facts."""

CLAIMS_ADDRESSEE_TYPES = {"legal_entity", "natural_person", "none"}
DISPUTE_PATH_TYPES = {"contact", "arbitration", "courts"}


@dataclass(frozen=True)
class DeclarationResult:
    """What was read, and how to fold it into a passport - kept apart from `Accountability` so the
    fetch is testable without constructing a passport, and so the declaration's OWN provenance
    (`self_reported["declaration"]`) does not need to be reverse-engineered out of four `Fact`s.
    """
    accountability: Accountability
    service: Service
    """Phase 2 - the subject's self-declared order-intake channel (spec 4.2-bis point 1). SAME
    kind of block as `accountability`: self-declared, `assumed`, never enters `verified` or the
    projection - see `Service`'s own docstring in `src/passport/passport.py`."""
    present: bool | None
    """Did `provek.json` exist and parse as a valid declaration? `None` only when the read attempt
    itself failed (world 4) - existence is then genuinely unknown, not a `False` masquerading as a
    finding. A stated `True`/`False` means the read completed either way (worlds 1-3)."""
    pinned_sha: str | None
    """The `head_sha` this read was pinned to, passed straight through from the base collector -
    independent of whether the fetch below succeeded. `None` has exactly one meaning: the base
    collector had not measured a head_sha for this subject when this ran."""
    schema_version: str | None
    treasury_claimed_level: str | None
    treasury_statement: str | None
    notes: list[str] = field(default_factory=list)

    def self_reported_declaration(self) -> dict:
        """Provenance of the declaration document ITSELF, for `self_reported["declaration"]`."""
        return {"present": self.present, "pinned_sha": self.pinned_sha,
                "schema_version": self.schema_version}


def _unreadable(pinned_sha: str | None, note: str) -> DeclarationResult:
    u = Fact.unreadable()
    return DeclarationResult(Accountability(u, u, u, u), Service(u, u, u, u), present=None,
                             pinned_sha=pinned_sha, schema_version=None,
                             treasury_claimed_level=None, treasury_statement=None, notes=[note])


def _not_declared(pinned_sha: str | None) -> DeclarationResult:
    absent = Fact(measured=False, reason=NotMeasured.NOT_DECLARED)
    return DeclarationResult(Accountability(absent, absent, absent, absent),
                             Service(absent, absent, absent, absent), present=False,
                             pinned_sha=pinned_sha, schema_version=None,
                             treasury_claimed_level=None, treasury_statement=None)


_GITHUB_REMOTE = re.compile(
    r"^(?:https://github\.com/|git@github\.com:)([^/\s]+/[^/\s]+?)(?:\.git)?/?$")


def github_full_name(remote: str) -> str | None:
    """`owner/repo` if `remote` is a GitHub remote URL, else `None`.

    `src/pipeline.py` clones an arbitrary git `remote` (a local path in its own tests), which is
    not the `owner/repo` slug `raw.githubusercontent.com` needs and often is not GitHub at all.
    Declaring a subject's own accountability only makes sense for a subject we can name a
    `provek.json` location for - anything else skips the read entirely rather than guessing one.
    """
    m = _GITHUB_REMOTE.match(remote.strip())
    return m.group(1) if m else None


def _fetch_raw(full_name: str, ref: str) -> tuple[int, str]:
    """One GET to `raw.githubusercontent.com` - no `api.github.com` budget spent (phase 0)."""
    url = f"{RAW_HOST}/{full_name}/{ref}/provek.json"
    p = subprocess.run(["curl", "-s", "-w", "\n%{http_code}", url],
                       capture_output=True, text=True, timeout=30)
    parts = p.stdout.rsplit("\n", 1)
    if len(parts) != 2:
        return 0, ""
    body, code = parts
    return (int(code) if code.isdigit() else 0), body


def _bounded_str(v: object) -> str | None:
    """A string within `FIELD_MAX_CHARS` and free of `[`, `]` and a backtick (D-43), `None` if the
    key was absent or blank, or raises - the raise is the signal that turns the WHOLE declaration
    invalid, per the ratified boundary above. A blank string is treated the same as an omitted key
    rather than as a malformed one: it is not a shape violation, only an empty answer, and the
    schema check exists to catch the former."""
    if v is None:
        return None
    if not isinstance(v, str) or len(v) > FIELD_MAX_CHARS:
        raise ValueError("field is not a string within the length ceiling")
    if FORBIDDEN_CHARS.search(v):
        raise ValueError("field contains a character reserved for markdown syntax ([, ], `)")
    return v.strip() or None


def _join(parts: list[str]) -> str:
    return " — ".join(p for p in parts if p)


def _fact_from_field(block: object, kind: str) -> Fact:
    """One accountability field -> one `Fact`, per the four worlds. Raises `ValueError` on
    anything that does not match the field's shape; the caller turns that into the whole
    declaration's `unreadable` branch (world 4) rather than a partial one."""
    if block is None:
        return Fact(measured=False, reason=NotMeasured.NOT_DECLARED)
    if not isinstance(block, dict):
        raise ValueError(f"{kind} is not an object")

    if kind == "claims_addressee":
        t = block.get("type")
        if t not in CLAIMS_ADDRESSEE_TYPES:
            raise ValueError("claims_addressee.type is not one of the declared values")
        if t == "none":
            return Fact.none_found()
        name, contact = _bounded_str(block.get("name")), _bounded_str(block.get("contact"))
        label = _join([name or t.replace("_", " "), f"({contact})" if contact else ""])
        return Fact.of(redact(label))

    if kind == "emergency_stop":
        exists = block.get("exists")
        if not isinstance(exists, bool):
            raise ValueError("emergency_stop.exists is not a boolean")
        if not exists:
            return Fact.none_found()
        holder, mechanism = _bounded_str(block.get("holder")), _bounded_str(block.get("mechanism"))
        label = _join([holder or "", mechanism or ""])
        return Fact.of(redact(label) if label else True)

    if kind == "insurance":
        exists = block.get("exists")
        if not isinstance(exists, bool):
            raise ValueError("insurance.exists is not a boolean")
        return Fact.of(True) if exists else Fact.none_found()

    if kind == "dispute_path":
        t = block.get("type")
        if t not in DISPUTE_PATH_TYPES:
            raise ValueError("dispute_path.type is not one of the declared values")
        detail = _bounded_str(block.get("detail"))
        return Fact.of(redact(_join([t, f"({detail})" if detail else ""])))

    raise AssertionError(kind)  # unreachable - every call site below names a real field


_FIELDS = ("claims_addressee", "emergency_stop", "insurance", "dispute_path")


def _https_url(v: object, *, required: bool) -> Fact:
    """One URL-shaped `service` field (spec 4.2-bis point 1). Raises `ValueError` - turning the
    WHOLE declaration invalid via the caller's `except`, same as every other malformed field in
    this module - if `required` and the field is missing or blank, or if a present value is not a
    syntactically valid https URL, or resolves (right now, at declaration time) to a private or
    reserved address (LAW #ONE-PLACE with `src/collector/reachability.py`'s own re-check at
    probe time: one resolve-and-classify routine, so the private-address rule cannot drift between
    "this declaration is invalid" and "this URL is unreachable").

    `pricing_url` and `terms_url` are optional and share the exact same shape as `order_url` - the
    specification names only `order_url` as https-and-required, but a URL field that were allowed
    to be `http://` or a bare string would be a second, weaker gate sitting beside the one the
    other two already pass, which is the inconsistency L-2 exists to forbid.
    """
    s = _bounded_str(v)
    if s is None:
        if required:
            raise ValueError("a required URL field is missing or blank")
        return Fact(measured=False, reason=NotMeasured.NOT_DECLARED)
    parsed = urlparse(s)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("field is not a valid https URL")
    try:
        resolve_public_ip(parsed.hostname)
    except SSRFRefused as e:
        raise ValueError(f"field resolves to a disallowed address: {e}") from e
    return Fact.of(redact(s))


def _service_from_block(block: object) -> Service:
    """`service` (schema 1.1.0, spec 4.2-bis point 1). Absent block -> every field `not_declared`,
    exactly the shape `_not_declared()` already gives `accountability` for a 404 - `service` is a
    sibling block subject to the identical four worlds, not a special case."""
    if block is None:
        absent = Fact(measured=False, reason=NotMeasured.NOT_DECLARED)
        return Service(absent, absent, absent, absent)
    if not isinstance(block, dict):
        raise ValueError("service is not an object")
    order_url = _https_url(block.get("order_url"), required=True)
    offering_raw = _bounded_str(block.get("offering"))
    offering = (Fact.of(redact(offering_raw)) if offering_raw is not None
               else Fact(measured=False, reason=NotMeasured.NOT_DECLARED))
    pricing_url = _https_url(block.get("pricing_url"), required=False)
    terms_url = _https_url(block.get("terms_url"), required=False)
    return Service(order_url=order_url, offering=offering, pricing_url=pricing_url,
                   terms_url=terms_url)



def collect_declaration(full_name: str, head_sha: str | None) -> DeclarationResult:
    """Read `provek.json` from `full_name` ('owner/repo'), pinned to `head_sha` when the base
    collector measured one - reading the default branch (`HEAD`) and marking it not pinned
    otherwise. Every failure mode folds into one of the four worlds above, with ONE exception: a rate limit
    is not a world here, it is our budget, and it raises `RateLimited` (see below).
    """
    ref = head_sha if head_sha is not None else "HEAD"
    try:
        code, body = _fetch_raw(full_name, ref)
    except Exception as e:  # network failure of any shape - world 4
        return _unreadable(head_sha, redact(f"declaration fetch failed: {e}"))

    if code == 404:
        return _not_declared(head_sha)
    # ONE-PLACE with `src/collector/github.py`: budget exhaustion is never `unreadable`. This
    # reader talks to raw.githubusercontent.com rather than the API, so it has its own budget - but
    # the distinction it must preserve is identical. Folding a 429 into world 4 would print OUR
    # throttling as the subject having no declaration to read.
    if code == 429:
        raise RateLimited(
            f"raw.githubusercontent.com rate limit reached reading the declaration for "
            f"{full_name} (HTTP {code})")
    if code != 200:
        return _unreadable(head_sha, redact(f"declaration fetch HTTP {code}"))

    try:
        doc = json.loads(body)
    except Exception:
        return _unreadable(head_sha, "declaration is not valid JSON")

    if not isinstance(doc, dict) or not isinstance(doc.get("provek_declaration"), str):
        return _unreadable(head_sha, "declaration is missing a valid provek_declaration tag")
    schema_version = doc["provek_declaration"]

    acc_block = doc.get("accountability")
    if acc_block is not None and not isinstance(acc_block, dict):
        return _unreadable(head_sha, "accountability is not an object")
    acc_block = acc_block or {}

    service_block = doc.get("service")

    try:
        facts = {k: _fact_from_field(acc_block.get(k), k) for k in _FIELDS}
        service = _service_from_block(service_block)
    except ValueError as e:
        return _unreadable(head_sha, redact(f"invalid declaration schema: {e}"))

    treasury_level = treasury_statement = None
    ops = doc.get("operations")
    if ops is not None:
        if not isinstance(ops, dict):
            return _unreadable(head_sha, "operations is not an object")
        tc = ops.get("treasury_control")
        if tc is not None:
            if not isinstance(tc, dict):
                return _unreadable(head_sha, "operations.treasury_control is not an object")
            try:
                treasury_level = _bounded_str(tc.get("declared_level"))
                treasury_statement = _bounded_str(tc.get("statement"))
            except ValueError:
                return _unreadable(head_sha, "operations.treasury_control field exceeds the "
                                             "length ceiling")
            if treasury_level is not None:
                treasury_level = redact(treasury_level)
            if treasury_statement is not None:
                treasury_statement = redact(treasury_statement)

    return DeclarationResult(
        Accountability(emergency_stop=facts["emergency_stop"],
                      claims_addressee=facts["claims_addressee"],
                      insurance=facts["insurance"],
                      dispute_path=facts["dispute_path"]),
        service,
        present=True, pinned_sha=head_sha, schema_version=schema_version,
        treasury_claimed_level=treasury_level, treasury_statement=treasury_statement)


def apply_declaration(full_name: str, head_sha: str | None,
                      claims: dict | None) -> tuple[Accountability, Service, dict]:
    """Read the declaration and fold it into a passport's accountability block, service block and
    self-reported branch in one call - the shape all THREE emitters (`src/pipeline.py`,
    `scripts/cohort.py`, `scripts/measure_qm2.py`) use, so the mapping cannot drift between them
    (LAW #ONE-PLACE).

    Never mutates `claims`; returns a new dict. The treasury claim is added ONLY when the subject
    actually declared a level - an omitted key is the honest rendering of "said nothing", never a
    placeholder (`claimed_level` never enters `verified` or the projection; see the module and
    `Accountability` docstrings for why). `service` is returned separately, exactly like
    `accountability` - it is a `Passport`-level field, not something folded into `claims`
    (self_reported).
    """
    result = collect_declaration(full_name, head_sha)
    merged = dict(claims or {})
    merged["declaration"] = result.self_reported_declaration()
    if result.treasury_claimed_level is not None:
        treasury: dict = {"claimed_level": result.treasury_claimed_level}
        if result.treasury_statement is not None:
            treasury["statement"] = result.treasury_statement
        merged["treasury_control"] = treasury
    return result.accountability, result.service, merged
