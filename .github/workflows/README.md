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

## Every action is pinned to a commit, and so is every pip install

All three workflows named their actions by TAG (`actions/checkout@v4`) until 2026-08-24. A tag is a
pointer its owner may repoint at any commit, so what ran here with this repository's token was
whatever somebody else's tag resolved to at the moment of the run. Every `uses:` is now a 40-hex
commit SHA with the tag beside it as a comment.

**The pins were re-derived, not copied.** A pin to the wrong commit is worse than no pin — it looks
exactly like diligence and defeats review by appearing to have passed it. Each SHA was resolved
from the action's own repository by two independent instruments that agreed: `git ls-remote` over
the git protocol, and the REST API's tag endpoint. `scripts/verify_action_pins.py` repeats that
derivation on demand and reports a lookup it could not complete as `NOT_MEASURED` rather than as a
match. `tests/test_actions_pinned.py` holds the shape — pinned, labelled, token bounded — on every
push, and drives the script's mismatch and refusal arms against a stubbed resolver so they are seen
to fire rather than merely present.

**The pip half, closed second.** The OpenSSF's `Pinned-Dependencies` count of 19 was 16 actions
plus **three `pip install` commands** — `gates.yml`'s `pytest`, `pytest-cov`, `ruff` and `mypy`
installs. Scorecard counts a pip command as pinned only under `--require-hashes`
(`checks/raw/shell_download_validate.go`), which needs a fully hash-pinned transitive requirements
set per job. Each job now installs one: `requirements/ci-tests.txt`, `ci-shipped.txt` and
`ci-lint.txt`, compiled by `pip-compile --generate-hashes` under the same Python 3.10 the jobs run,
from committed `.in` files that keep the intent separate from the resolution.

The failure mode named here when those three were still open is real and was accepted rather than
avoided: **a stale hash set turns CI red, and that is the ratchet working rather than a flake.**
The policy for moving a set — a deliberate edit, never a scheduled refresh — is D-30, which is also
where the reason this does not repeal D-26's deliberately unpinned `wrangler@4` is written out.
`scripts/verify_pip_pins.py` holds the shape on every push and `tests/test_pip_pinned.py` is
watched to fire, because a one-time edit drifts back and no other gate here can see this one go:
the door-versus-CI comparison reads any line beginning `pip install` as runner preparation.

## The files in this directory are parsed at the door

`66f61ea` went out with seven green gates behind it and turned `main` red in the same second it
landed. `--only-binary=:all: ` sat in a **plain scalar**, `: ` is how YAML spells "the key ended
here", and GitHub refused the document: the run was created and concluded in the same second
holding **zero jobs**. Nothing in the workflow failed, because nothing in it started — and a
startup failure publishes no check run at all, so `/commits/{sha}/check-runs` answered with three
successes for a commit whose gates were red.

Every gate that passed it was correct about what it measures. `scripts/verify_pip_pins.py` read all
three broken lines and reported them hash-pinned — it still does, byte for byte, after the repair.
It reads these files with a hand-written scanner, and that scanner was **more permissive than the
machine it stands in for** (L-31), which is the direction that stays silent: a stricter
approximation announces itself as a false red on a working file, a looser one waits until the real
parser refuses something the gates have blessed.

`tests/test_workflows_parse.py` now loads every `*.yml` and `*.yaml` here with `yaml.safe_load`, at
the door and in the `tests` job, through `scripts/verify_workflow_yaml.py` and
`LAW-WORKFLOWS-PARSE`. `pyyaml` entered `requirements/ci-tests.txt` to make that possible, which is
a hash set moving — so it moved by a decision (**D-32**) rather than by a convenient edit, as D-30
requires.

**The door is the load-bearing half here, which is the reverse of every other gate in this file.**
In CI this test cannot catch a broken `gates.yml` — a workflow that does not parse runs no job, so
the job holding the test never starts, and the defect deletes its own detector. What CI catches is a
broken `codeql.yml` or `scorecard.yml`, whose failure does not stop this workflow. `scripts/push.sh`
runs the suite while the push does not yet exist, which is the only place the `66f61ea` case can be
refused before it reaches `main`.

**What this does not claim.** PyYAML is not GitHub's parser, and implements YAML 1.1 where most
modern parsers implement 1.2, so a file accepted here is not thereby proven acceptable there. No
schema is checked by anything in this tree: a misspelt key, an unknown `runs-on` or a job that
cannot start all parse perfectly. What is bought is the defect that was actually paid for — a
document that is not well-formed YAML — refused before the push instead of after it. The red run,
including the original file read by both gates side by side, is
`evidence/RED-034-the-file-every-gate-read-and-no-parser-had-opened.txt`.

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
