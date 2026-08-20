# CI workflows

Three workflows. One is ours judging ourselves; two are third parties judging us.

## `gates.yml` — our own suite, taken out of the pusher's hands

Five jobs, mirroring `scripts/push.sh` so that the checks stop depending on who pushes:

| job | what fails the build |
|---|---|
| `ratchets` | a module with no ABI requirement; a law with no armed gate; Cyrillic on the GitHub surface |
| `tests` | any test failing, or coverage under 70% |
| `shipped` | the site failing to build; a dangling link in a page the build emitted |
| `lint` | ruff findings (mypy is advisory — see below) |
| `secrets` | a secret-shaped string anywhere in the tree |

The table said **four** and omitted `shipped` from the day that job was added — the one job that
judges what a reader actually receives, missing from the list of what fails the build, in the
document describing the list. Left as a note because it is the same shape as everything below it:
a description that stopped matching its artefact and stayed convincing.

### "Mirroring `scripts/push.sh`" is now measured rather than asserted

That claim has been false twice. CI ran `ruff` and the door did not, which turned `main` red four
times; fixing the instance left the mechanism, and writing the two lists out side by side then
found two more — the door built no site and enforced no coverage floor.

`tests/test_door_matches_ci.py` holds the correspondence as a table and checks it in both
directions, so a job added here without a counterpart at the door is a red build, and so is a row
describing a step that no longer exists. It compares a declared correspondence, not semantics: it
proves the door runs `pytest` with the same coverage floor, not that both runs see the same tree.

**And it mirrors `gates.yml` only.** `codeql.yml` and `scorecard.yml` also run on push to `main`
and can go red there; the door cannot run either — CodeQL is not installable on the audit host —
so they are declared as unmirrored with that reason rather than quietly counted as covered. The
sentence at the top of this file says *three workflows*; that number is now asserted by the same
test, because a fourth workflow file would otherwise be invisible to everything described here
while being perfectly able to fail the build.

### Why the ratchets are the important part

The other three jobs are standard hygiene. The ratchets are what make this project's own laws
falsifiable: scope sprawl, dangling rules and language drift all become red builds rather than
things somebody notices later.

## `codeql.yml` — GitHub's static analysis, both languages

Python and TypeScript, `security-and-quality` queries, findings in code scanning. It exists because
`gates` is this project grading its own homework: every rule in it was written by the same hands as
the code. CodeQL's queries were not.

## `scorecard.yml` — OpenSSF Scorecard, published to their API

Supply-chain posture against the OpenSSF's rubric — token permissions, action pinning, branch
protection, dependency freshness, release signing. `publish_results: true` is the load-bearing
setting: it sends the result to the OpenSSF, so the badge in the root `README.md` is served from
**their** copy of the number rather than ours.

Expect the score to be middling and expect that to be accurate. Several checks describe practices
this repository has not adopted; a low true number is worth more than a high tuned one.

## Standing caveats

**The badges state that a check RAN, not that the code is clean.** A green `codeql` badge means the
analysis completed, not that it found nothing — findings live in the Security tab, and a badge that
implied otherwise would be a claim stronger than its artefact.

### `mypy` is advisory until **2026-10-15**, and the deadline is armed

The reasoning is unchanged: the codebase has no type-checking baseline, and a gate that fails on
day one gets disabled by whoever meets it. What changed is that the promise is now executable.

This section used to end "it becomes blocking once a clean baseline exists — and that promise is
recorded here rather than left as an intention." Recording it **is** leaving it as an intention.
Nothing measured the condition, nothing would fire when it was met, and nothing would notice if it
never was — a rule living only in prose (L-7), four lines above a section kept as a warning about
exactly that. Three things hold it now:

- **The condition fires where it can be measured.** The `mypy` step separates three states instead
  of collapsing them with `|| true`: a clean run **fails** the build and says to make the step
  blocking and add mypy to `scripts/push.sh`; type errors print a count and pass; mypy failing to
  start is `not_measured` and fails. That last state is why `|| true` had to go — an instrument
  that could not run printed precisely what a clean baseline prints, so the one reading that could
  end the advisory state was indistinguishable from a crash.
- **The condition cannot be measured locally, and is not faked.** mypy is not installed on the
  audit host, so a local "zero errors" would be the instrument's absence wearing the shape of a
  result (L-1, and L-11's sharper form). The reading is taken only in CI, which installs it.
- **The advisory state expires on its own.** `tests/test_door_matches_ci.py` goes red once the date
  passes, and it runs both at the door and on this workflow's daily `schedule:` — so it fires in
  the world where nobody pushes, which is the world where a forgotten promise survives (L-19). The
  date is 56 days from 2026-08-20, chosen to land inside the sixty after which GitHub disables a
  public repository's schedule: a deadline past that is unreachable by the clock in the exact state
  it exists for.

**The baseline, measured 2026-08-20:** `mypy src --ignore-missing-imports` reports **28 errors
across 7 files**, nearly all of them `None` reaching a comparison or an attribute access. That is
not an incidental backlog — it is invariant 1's own defect class, which is the argument for an
expiry rather than an indefinite advisory. The count is recorded so the next reader can tell a
baseline that is nearly clean from one that is not.

The date can be moved. Doing so requires ratifying it in `DECISIONS.md` with the count that
justifies it, which is a decision; drift is what the deadline removes, not deliberate extension.

## A dated condition that expired, kept as a record

This file used to say Actions minutes were exhausted until **2026-09-01** and that the workflows
therefore did not run. The escape clause in that same note is what happened: the repository went
public on 2026-08-20, Actions are free for public repositories, and the condition is gone. Measured
rather than assumed — `/repos/whiteknightonhorse/provek/actions/runs` reported 18 completed runs of
`gates`, all `success`.

It is written down instead of deleted because a stale condition in a CI document is how a pipeline
comes to be described as dead while it is running, and the next person to read a confident date in
here should know this one was wrong.
