# CI workflows

Three workflows. One is ours judging ourselves; two are third parties judging us.

## `gates.yml` — our own suite, taken out of the pusher's hands

Four jobs, mirroring `scripts/push.sh` so that the checks stop depending on who pushes:

| job | what fails the build |
|---|---|
| `ratchets` | a module with no ABI requirement; a law with no armed gate; Cyrillic on the GitHub surface |
| `tests` | any test failing, or coverage under 70% |
| `lint` | ruff findings |
| `secrets` | a secret-shaped string anywhere in the tree |

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

`mypy` is advisory (`|| true`): the codebase has no type-checking baseline yet, and a gate that
fails on day one gets disabled by whoever meets it. It becomes blocking once a clean baseline
exists — and that promise is recorded here rather than left as an intention.

## A dated condition that expired, kept as a record

This file used to say Actions minutes were exhausted until **2026-09-01** and that the workflows
therefore did not run. The escape clause in that same note is what happened: the repository went
public on 2026-08-20, Actions are free for public repositories, and the condition is gone. Measured
rather than assumed — `/repos/whiteknightonhorse/provek/actions/runs` reported 18 completed runs of
`gates`, all `success`.

It is written down instead of deleted because a stale condition in a CI document is how a pipeline
comes to be described as dead while it is running, and the next person to read a confident date in
here should know this one was wrong.
