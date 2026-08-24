# Security policy

## Reporting a vulnerability

**Use GitHub's private vulnerability reporting:**
<https://github.com/whiteknightonhorse/provek/security/advisories/new>

That form is the reporting channel for this repository. It opens a private advisory visible to the
maintainer and to you, and nothing about it is public until an advisory is published.

**The channel was measured, not assumed.** Private vulnerability reporting was off for this
repository until 2026-08-24, and a policy naming a form that does not accept submissions is exactly
the defect this project exists to find - a claim stronger than the artefact behind it. It was
enabled and then read back:

```
PUT  /repos/whiteknightonhorse/provek/private-vulnerability-reporting  -> HTTP 204
GET  /repos/whiteknightonhorse/provek/private-vulnerability-reporting  -> HTTP 200 {"enabled": true}
```

The reading taken 2026-08-24 is `enabled: true`, and the `GET` is the reading that settles it.
An anonymous `GET https://github.com/whiteknightonhorse/provek/security/advisories/new` answers
`302` to a login page, which is a fact about the client and not about the form: it says the same
thing whether the feature is on or off, so it is recorded here as the non-measurement it is rather
than offered as confirmation. If you find the form refuses you while signed in, that is itself a
report worth making - by the route below.

## If you have no GitHub account

**There is no second channel published today, and that is a gap rather than a decision.** No email
address, key or form belonging to this project's operator appears anywhere in this repository or on
`provek.dev`; nothing was measured that a reporter could use, and inventing an address here would
put a contact into a security policy that nobody is reading. This section is `not_measured` until
the operator supplies a channel and it has been confirmed to receive mail.

Until then the honest instruction is: open a normal public issue saying only that you have
something to report and asking for a private channel - no details, no reproduction steps. That
leaks the existence of a finding, which is a real cost, and it is smaller than a report that
reaches nobody.

## Scope

This repository is the verification and reputation layer described in `SPEC.md`, plus the static
site served at `provek.dev` and the one Cloudflare Pages Function behind `/api/apply`.

Findings that are in scope and worth reporting even though they are not exploits:

- **a published claim stronger than the artefact behind it** - a passport, registry row, README
  line or page that asserts something the evidence does not support. This is the defect class the
  whole project is built to detect, so an instance of it in our own output is the most serious
  thing you can find here, ranked above most memory-safety-style bugs;
- **a counter, status or field that folds "nothing qualified", "the check did not run" and
  "unreadable" into one value** (invariant 1 in `CLAUDE.md`);
- **a gate that reports success without asserting anything** - a test that cannot fail, a skipped
  suite counted among the armed, a check whose green and broken states are indistinguishable.

Out of scope, and named so a reporter does not spend time on them:

- `web-1.0/` is a frozen rollback point (`web-1.0/FROZEN.md`, D-21). The deploy builds `web/`
  only, so nothing under `web-1.0/` is served. Two CodeQL alerts against it are dismissed on that
  basis in `docs/ALERT_TRIAGE.md`;
- `evidence/` is a preserved corpus of red runs that invariant 5 requires be kept unedited.
  Lint findings inside it are not defects; editing an artefact to satisfy a linter destroys the
  property that makes it evidence (D-28);
- **money never moves through this project** (A-6, a permanent non-goal). There is no payment
  path, no wallet and no custody, so there is nothing there to find.

## What this policy does not promise

No response time, no severity rubric and no bounty. This is a small project with no staffed rota,
and a service level nobody measures is the kind of sentence it exists to object to. What is
promised is narrower and checkable: a report that arrives through the form above is read, and a
finding accepted here is written down with its basis in the repository, in the form the other
dismissals in `docs/ALERT_TRIAGE.md` already take.

## Handling of the operator's private repositories

Four registry rows read `unreadable` because the subjects are private repositories that this
project is not permitted to open. That is a true measurement, not a gap to be closed, and a report
proposing that we read them is out of scope by construction.
