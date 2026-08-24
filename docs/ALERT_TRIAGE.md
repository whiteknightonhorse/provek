# Code-scanning triage, 2026-08-24

A dismissed alert is a claim that something is not a defect. This project exists to catch claims
stronger than the artefact behind them, so an alert closed here carries a `dismissed_reason` and a
written basis that can be checked by re-reading the file it names or re-running the command it
quotes. "We looked at it and it seemed unimportant" is the defect, not the disposition.

This file is a record of ONE triage act at one time, not a live list. The live state is
`GET /repos/whiteknightonhorse/provek/code-scanning/alerts`; where the two disagree, the API is
right and this file is stale. It is here because the basis for each closure otherwise exists only
in GitHub's alert database, which is not part of what a reader of this repository receives.

Measured 2026-08-24T11:35Z: **23 open, 0 dismissed** before; **13 open, 10 dismissed** after.

## Closed, with a basis (10)

| # | Rule | Reason | Basis, in short |
|---|------|--------|-----------------|
| 12 | `py/non-iterable-in-for-loop` | false positive | `Status` is an `Enum`; `type(Status).__name__` is `EnumMeta` and the loop yields 7 members, adding 6 transitions to a 16-entry `ALLOWED`. Verified by running it. |
| 43 | `py/non-iterable-in-for-loop` | false positive | Same cause, verified the same way: `ReadingState` iterates to 6 members. It is also in `tests/`, but the finding is wrong on its own terms. |
| 11 | `py/ineffectual-statement` | false positive | `src/transport/base.py:18` is the `...` body of a `typing.Protocol` method - the standard stub body. Deleting it leaves a method with no body. |
| 42 | `py/implicit-string-concatenation-in-list` | false positive | Deliberate line wrapping: the two fragments are one sentence, and the list element does end with a comma. |
| 40 | `py/bad-tag-filter` | used in tests | In `tests/` and imported by no product code - but **not** harmless, and the filter was tightened in this commit. See below. |
| 47 | `py/unused-global-variable` | won't fix | A deliberate prose constant documenting a past repair, unreferenced by design, in `tests/`. |
| 48, 49 | `py/unused-local-variable` | won't fix | `evidence/` is the preserved red-run corpus that invariant 5 requires be kept. Editing an artefact to satisfy a linter destroys the property that makes it evidence (D-28). |
| 6, 7 | `js/remote-property-injection`, `js/client-side-request-forgery` | won't fix | `web-1.0/` is the frozen phase-2 rollback point (`web-1.0/FROZEN.md`, D-21), and the deploy builds `web/` only, so this code is never served. |

Two of these deserve more than a table row, because in both cases the first basis written for them
was weaker than the alert.

**40 was nearly dismissed as noise, and it was pointing at a real hole in a gate.** The first basis
read "no untrusted input, so there is no sanitiser role to fail" - true, and beside the point.
`strip_tags` is not defending anything; it is the INSTRUMENT `tests/test_notes.py:184` uses to
prove that FAQ text reaches the reader. The same text also sits in the JSON-LD block inside a
`<script>`. A script tag the filter fails to remove therefore does not produce a visible failure -
it produces a PASS, read off the schema copy of a sentence that need not be on the page at all.
Measured 2026-08-24: the emitted pages use lowercase `<script>` and an exact `</script>`, so the
assertion holds today; nothing measured the generator's tag shape, so it held by luck. The filter
now carries `re.I` and tolerates whitespace in the closing tag, and `tests/notes_support.py`
records why. The alert stays dismissed as test code; it is not recorded as noise.

**6 and 7 say the frozen copy is not shipped. They do not say the live tree is clean, and it is
not.** `web-1.0/src/App.tsx:68` built its fetch path through `passportId.replace(/[:/]/g, "_")`,
which removes the separator. The live `web/src/App.tsx:281` interpolates `slugInRoute` raw, and
`route.slice(3).replace(/\/$/, "")` strips only a trailing slash, so inner `/` survives into the
path; the same value is used as an object key on line 278. The live code is a superset of what
CodeQL objected to in the frozen copy, and it is unflagged - absence of an alert on the product
path is `not_measured`, not `clean`. It is listed with the other open work below rather than left
as a remark, because a finding this triage produced itself is the one most likely to go unaddressed.

## Still open, each with an addressee (13)

**Real, unfixed, named rather than silently carried:**

- `#8` unused import `existsSync` in `web/prerender.mjs` - measured: the name occurs once, on the
  import line. `#9` `ref` in `scripts/cohort.py:193` and `#10` `TOKEN_HOLDER` in
  `scripts/measure_qm2.py:50`, both assigned and never read.
- `#28`, `#38`, `#50` `PinnedDependenciesID` - three unpinned `pip install` lines in `gates.yml`.
  An earlier commit pinned every **action** to a commit and closed 21 of these; pip was not in its
  scope, and `#50` was raised by the scan that ran after it. **Fixed in the tree by D-30** - all
  three now install hash-checked sets under `--require-hashes` - and still counted as open here,
  because what closes a code-scanning alert is the SCAN, which runs after the push. Listing them as
  closed on the strength of the edit that should close them would be a claim about an instrument
  that has not yet reported (invariant 1). The reading that settles it is
  `GET /code-scanning/alerts?state=open`; until it is taken, these three are `not_measured`, not
  `clean`.
- `#29` `SecurityPolicyID` - no `SECURITY.md` exists in the tree or in `.github/`. Closes by work.
- **No alert number, raised by this triage:** `web/src/App.tsx:281` fetches a path built from an
  unvalidated route substring (see above). Closes when the fetch is guarded on `known` - for a
  matched subject `slugInRoute` already equals the sanitised `subject_id` by the comparison on
  line 272 - or by validating the slug against `^[A-Za-z0-9_-]+$` before it reaches the path.
  Low severity today: same-origin static hosting, self-generated links, and a computed key in an
  object literal does not touch the prototype. Listed because it is unflagged, not because it is
  urgent.

**Executed in part, and the rest is blocked on a decision:**

- `#13` `BranchProtectionID` - `main` was unprotected. Force pushes and branch deletion are now
  blocked, `enforce_admins` included, which makes invariant 8 a machine guarantee instead of a
  convention. The rest of what Scorecard scores - required reviews, required status checks - is
  **not** applied and is not an oversight: both reject the direct push that `scripts/push.sh`
  performs, so applying them would close the only door outward this project has. That is the same
  question as `#32` below, and it belongs to the operator.

**Operator decisions, not an agent's (5).** These are process-maturity metrics, not defects in
code, and each would be answered by changing how the project is run:

- `#33` `MaintainedID`, `#32` `CodeReviewID`, `#31` `DependencyUpdateToolID` - the three named in
  the task as the operator's.
- `#30` `FuzzingID`, `#34` `CIIBestPracticesID` - the same family, at medium and low. Left open on
  the same reasoning rather than closed on an agent's initiative.

Their "high" severity sits beside real findings and flattens the scale, but that is an argument for
the operator deciding them, not for an agent dismissing them.

**No date is attached to any of the open items, and that is a gap rather than an omission.** The
task asked for the branch-protection work to be done or given a deadline; the half that could be
done was done, and the half that remains is a decision about how this project is run. An agent
writing a date against somebody else's decision would be recording a commitment it cannot keep or
enforce - the same defect as a dismissal without a basis, pointed at the calendar. The dates belong
with the decisions, in `DECISIONS.md`, when the operator takes them.

## Two corrections to the record

`TokenPermissionsID` was carried into this task as one of five open highs. It was already **fixed**
at 2026-08-24T11:11:02Z, by the commit that bounded the workflow token - alert `#14`, state
`fixed`. Nothing was closed for it here because there was nothing open.

The endpoint itself changed state. A previous attempt recorded `code-scanning/alerts/6` as HTTP 401
and correctly wrote the alert's state down as `unreadable` rather than as closed or as zero. With
the token that `scripts/push.sh` uses, the endpoint answers 200 and the alert was readable and
writable. The earlier reading was a true fact about credentials, not about the repository.
