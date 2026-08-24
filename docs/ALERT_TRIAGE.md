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

## Second triage act, 2026-08-24 (T-S4)

The section above is the first act and is left exactly as it was written. This is the second, and
it is separated rather than merged because a triage record that is edited in place stops being a
record of when anything was known.

Measured before this act: **10 open, 10 dismissed** — down from the 13 the first act left, because
`#28`, `#38` and `#50` (`PinnedDependenciesID`) closed on their own. The first act predicted that
and refused to record it: *"what closes a code-scanning alert is the SCAN, which runs after the
push"*, so they were carried as `not_measured` rather than as clean. The scan has since run and
they are `fixed`. The prediction was right and it was correctly not treated as a measurement.

**Addressed by work, not by disposition (4).** `#8` `existsSync` in `web/prerender.mjs`, `#9` `ref`
in `scripts/cohort.py`, `#10` `TOKEN_HOLDER` in `scripts/measure_qm2.py` — all three removed. In
`cohort.py` the CALL is kept and only the binding dropped: `transport.publish(...)` is a side
effect that puts the machine record where the registry row points, and deleting the statement
along with its unread name would have unpublished eight passports to satisfy a linter. `#29`
`SecurityPolicyID` is answered by `SECURITY.md`, below.

Each of these four closes on the next scan, and the same rule the first act applied to the pip
alerts applies here: until `GET /code-scanning/alerts?state=open` no longer lists them, they are
`not_measured`, not `clean`. The edit that should close an alert is not the instrument that does.

**`#51` `py/bad-tag-filter` — dismissed `used in tests`, and it is NOT `#40` coming back.**

That reading was the obvious one and it is wrong. The scan that ran after `b44db01` reported `#40`
`fixed` at `2026-08-24T11:59:23Z` and opened `#51` two seconds earlier on the line that replaced
it, so the pair looks exactly like one alert re-raised over an edit. The messages settle it:

| | message |
|---|---|
| `#40` | `This regular expression does not match upper case <SCRIPT> tags.` |
| `#51` | `This regular expression does not match script end tags like </script\t\n bar>.` |

Different defects. `re.I` closed the first; the second is the NEXT corner case in the same query's
list, and `\s*` never covered it. A browser ends a script element at `</script foo="bar">` and the
filter did not — so the escape `#40` was tightened against was still open in a second spelling,
and `strip_tags` is the instrument `tests/test_notes.py` uses to prove FAQ text reaches the reader.
A script it fails to remove produces a PASS read off the JSON-LD copy of a sentence that need not
be on the page at all. That is the whole reason `#40` was not closed as noise, and it applies here
unchanged.

The filter now matches `</script(?=[\s/>])[^>]*>`, and `style` and `svg` get the same edit — they
carry the identical hole and no alert, and absence of an alert is `not_measured`, not `clean`. The
lookahead is load-bearing: `</script[^>]*>` alone would also eat `</scriptfoo>`, which is not an
end tag in any parser, and a filter that removes MORE than its name says would delete page text
and then report the page as not containing it — the same instrument defect pointed the other way.

**What is not claimed: that this edit satisfies the query.** Whether CodeQL accepts a lookahead
cannot be measured from this host. So `#51` is closed by DISMISSAL on the basis that it is
test-only instrument code with no untrusted input and no product import — `#40`'s basis, for
`#40`'s reasons — and the tightening is recorded beside it as a repair, not as the closure. A
future scan is the only thing that can settle whether the query is content.

**`SECURITY.md`, and the channel in it was measured before it was published.**

`#29` is answered by a file, but a security policy naming a channel that accepts nothing is a
claim stronger than its artefact — this project's founding defect, in the one document whose whole
job is to be relied on in an emergency. Private vulnerability reporting was **off** for this
repository. It was enabled with the token `scripts/push.sh` uses and then read back:

```
PUT  /repos/whiteknightonhorse/provek/private-vulnerability-reporting  -> HTTP 204
GET  /repos/whiteknightonhorse/provek/private-vulnerability-reporting  -> HTTP 200 {"enabled": true}
```

The `GET` is the reading that settles it; the `204` alone would have been a report by the
instrument about itself. An anonymous `GET` of the advisory form answers `302` to a login page,
and that is recorded in `SECURITY.md` as the non-measurement it is rather than offered as
confirmation — it says the same thing whether the feature is on or off, which is L-11 exactly: a
status code encoding the asker's identity rather than the resource's state.

The second channel is a **named gap**. No email address, key or form belonging to the operator
appears in this repository or on `provek.dev`, so a reporter without a GitHub account has nowhere
measured to go. `SECURITY.md` says so and gives the least-bad interim route rather than inventing
an address, and that section stays `not_measured` until the operator supplies a channel and it is
confirmed to receive mail.

**The finding this file raised against itself is closed.** The first act ended by noting that
`web/src/App.tsx:281` interpolated an unvalidated route substring into a fetch path, unflagged by
any scanner, and that *"a finding this triage produced itself is the one most likely to go
unaddressed"*. It is now guarded by `web/src/slug.js`, held by `LAW-SLUG-JUDGED-BEFORE-FETCH`, and
the gate RUNS the rule under Node over an adversarial corpus rather than matching patterns against
its source. Six mutations, each with a distinct failure set, are in
`evidence/RED-032-a-slug-that-walked-out-of-the-passport-directory.txt`.

The disposition chosen was the slug pattern, not the guard on `known` that this file offered as the
first option. Guarding on a matched registry subject fails invariant 1 in the state that matters:
an unmatched slug would never be fetched, never resolve, and sit under a skeleton for ever, so
"the registry has not loaded yet" and "no such subject" would render identically. A refused slug
therefore gets a state of its own — `invalid`, the fifth — and a dead end that says nothing about
the registry, because nothing was asked of it.

**Still open after this act (5), all of them the operator's:** `#30` `FuzzingID`, `#31`
`DependencyUpdateToolID`, `#32` `CodeReviewID`, `#33` `MaintainedID`, `#34` `CIIBestPracticesID`.
Unchanged from the first act and left for the same reason: they are process-maturity metrics
answered by changing how the project is run, and `#32` in particular would close the only door
outward this project has.

## Two corrections to the record

`TokenPermissionsID` was carried into this task as one of five open highs. It was already **fixed**
at 2026-08-24T11:11:02Z, by the commit that bounded the workflow token - alert `#14`, state
`fixed`. Nothing was closed for it here because there was nothing open.

The endpoint itself changed state. A previous attempt recorded `code-scanning/alerts/6` as HTTP 401
and correctly wrote the alert's state down as `unreadable` rather than as closed or as zero. With
the token that `scripts/push.sh` uses, the endpoint answers 200 and the alert was readable and
writable. The earlier reading was a true fact about credentials, not about the repository.

## Third triage act, 2026-08-24 (T-S5) — one alert, closed by repair rather than by disposition

Measured before this act: **6 open, 11 dismissed**. Five of the six are the operator's process
metrics the second act left (`#30`–`#34`), unchanged and left again for the same reason. The sixth
is new.

**`#53` `py/uninitialized-local-variable`, `tests/test_passport_slug_is_judged_before_it_is_fetched.py:95`**
— *"Local variable `done` may be used before it is initialized."* Raised at `2026-08-24T16:08:29Z`
by the scan that ran after the second act shipped, on the file that act had just added.

**It is unreachable today, and that was measured rather than argued.** Two readings, because the
first alone is a claim about somebody else's code:

```
$ python3 -c "import pytest,inspect; print(inspect.signature(pytest.fail))"
(reason: 'str' = '', pytrace: 'bool' = True) -> 'NoReturn'          # and it raises Failed(BaseException)

$ PATH=/tmp/nonode python3 -m pytest tests/test_passport_slug_is_judged_before_it_is_fetched.py -x -q
E  Failed: `node` is not on PATH, so the only gate that RUNS the slug guard could not run. ...
tests/test_passport_slug_is_judged_before_it_is_fetched.py:90: Failed      # line 95 was never reached
```

The second is the one that settles it: the branch was **executed** with `node` off `PATH`, not
reasoned about. So `dismissed: false positive` was available and would have been TRUE.

**It was repaired anyway, and the reason is not tidiness.** `pytest.fail` terminates by virtue of a
`NoReturn` annotation on a third-party function — a fact that is nowhere near the line relying on
it. `done.returncode` on line 95 is therefore guarded by something invisible at the point of use,
and CodeQL is not the only reader that cannot see it. Swap that call for anything that returns and
the helper stops reporting *"the instrument was absent"* and starts raising `NameError` on `done`:
an instrument reporting a state other than the one it found — invariant 1, inside the gate whose
whole job is to hold invariant 1. The alert was **right about the shape and wrong about today's
reachability**, and only the first half is worth acting on. The handler now ends in
`raise AssertionError(...) from None`; the message is unchanged.

**The tree's own form was measured, not assumed.** Both sibling probes —
`tests/test_intake_survives_a_failed_writeback.py:89` and
`tests/test_intake_sweep_distinguishes_its_states.py:118` — already raise, and neither carries an
alert. Absence of an alert is `not_measured`, not `clean`, so the tree was scanned for the shape
itself rather than for the flag:

```
python3 - <<'EOF'
import ast, pathlib
TERM = (ast.Raise, ast.Return, ast.Continue, ast.Break)
for p in sorted(pathlib.Path('.').rglob('*.py')):
    if '.git' in p.parts: continue
    for n in ast.walk(ast.parse(p.read_text(encoding='utf-8'))):
        if isinstance(n, ast.Try) and any(isinstance(s, ast.Assign) for s in n.body):
            for h in n.handlers:
                if not isinstance(h.body[-1], TERM):
                    print(f'{p}:{h.lineno} ends in {ast.unparse(h.body[-1]).split("(")[0]}')
EOF
```

Before the repair it printed exactly one line — the flagged handler. After, it prints nothing. The
flagged file was the only instance in the tree, and the repair aligns it with the two siblings
rather than inventing a house style for the occasion.

**`used in tests` was available here and is not used.** `#40`, `#47`, `#48`, `#49` and `#51` were
closed on test-code bases, so the precedent existed. It does not apply to a finding about whether a
gate reports the state it measured: that a defect sits in `tests/` says where it is, not whether the
instrument lies. The distinction is the same one the first act drew when `#40` was nearly dismissed
as noise and was pointing at a real hole.

**What is not claimed: that this edit closes the alert.** The rule both earlier acts applied applies
unchanged — what closes a code-scanning alert is the SCAN, which runs after the push, and the edit
that should close one is not the instrument that does. Until
`GET /code-scanning/alerts?state=open` no longer lists `#53`, it is `not_measured`, not `clean`.

**Still open after this act (5), all of them the operator's:** `#30`, `#31`, `#32`, `#33`, `#34` —
the same five, untouched for the third time running.

## Fourth triage act, 2026-08-24 (T-S9) — one closure the task named already done, one new dismissal

Measured before this act: **5 open, 12 dismissed**. `#30`–`#34`, the operator's five, unchanged.

**The task named `web/src/App.tsx:281` as still raw, and it was not.** The closure condition it
quoted — fetch only for `known`, or validate the slug against `^[A-Za-z0-9_-]+$` — is the second
act's own text, describing the finding that act raised and then closed the same day with
`web/src/slug.js` and `LAW-SLUG-JUDGED-BEFORE-FETCH` (commit `e706938`). Re-reading the source
before re-fixing it: `isSafeSlug` is imported and called on line 307, and `e706938` is an ancestor
of both `HEAD` and the commit `provek.dev/deploy-label.txt` named live before this act (`829a6bf`),
so the guard was already shipped, not merely committed. Confirmed a second way rather than trusted
from history — a stale task description is exactly the gap invariant 1 exists to catch — by pulling
the live bundle and finding the pattern in it:

```
$ curl -s https://provek.dev/assets/index-DyfCrMjR.js | grep -o '\[A-Za-z0-9_-\]'
[A-Za-z0-9_-]
```

No source change follows from this. The deploy this task still owes is not a repair; it carries
`HEAD` forward from `829a6bf` so `deploy-label.txt` reads the commit this act produced, per the
task's own done-condition.

**`#54` `py/implicit-string-concatenation-in-list`, `evidence/RED-036-generator.py:183`** — raised
at `2026-08-24T21:51:54Z`, on a four-line Python string that is the `-e` script argument to `node`
inside `run([...])`. Read before disposing of it, because a missing comma there is a live category
(`#42`'s file had one) and D-28 forbids repairing `evidence/` either way: the four literals were
executed as `node` would execute them, unedited —

```
$ node --input-type=module -e "import {loadNotes, NOTE_CEILING, NOTE_STEP} from './web/notes/emit.mjs';console.log(...);try { loadNotes(); ... } catch (e) { ...; process.exit(3); }"
ceiling=3 step={"ceiling":7,"open":false,"state":"nothing_qualified",...}
BUILD RETURNED - the ceiling did not refuse
exit=0
```

— one coherent program: import, then log, then try/catch, in the order the source lines run. A
comma inserted at any of the three joins would split `run()`'s fourth list element into more argv
entries; `node -e <script> <extra>` does not concatenate trailing arguments back into the script,
it exposes them on `process.argv` instead, so the probe would stop running the try/catch it needs
and CodeQL's own recommendation (`+` for deliberate joins) would have to reach across a subprocess
boundary it cannot see past. Same class as `#42`, verified by running rather than by resemblance to
its table row. Dismissed `false positive`, comment on the alert points here rather than repeating
the run above past the 280-character cap.

**Still open after this act (5), all the operator's:** `#30`, `#31`, `#32`, `#33`, `#34` — unchanged
for the fourth act running.
