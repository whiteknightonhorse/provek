# ADR-0005. Weak-signal limiters live in CODE, not in a comment

**Date:** 2026-08-19. **Status:** accepted. **Basis:** Fable ruling.

## Problem
The signal "share of signed commits + number of authors" mixes evidence classes: "this KEY signed"
is cryptographically bound, while "the key belongs to an agent rather than a human" is the
subject's self-report, and forging it is cheap - the subject owns all of its own keys.

## Decision - three limiters, implemented in code
* **O1** a mixed signal yields `confidence=INFERRED`, never `MEASURED`;
* **O2** the signal ALONE does not justify L3+; without a runtime trace of initiation the ceiling
  is L2;
* **O3** the signal is stronger at REFUTING: a contradiction lowers a claimed level, while
  agreement only weakly supports it.

Every downgrade is RECORDED in `limiters_applied` - a downgrade without a recorded reason is
indistinguishable from a computation error.

## Why not a docstring
A note saying "approximation" is necessary but insufficient: **a rule written only in a comment is
not enforced.** This project has already come close to paying for that.

## Observable consequence
After the limiters landed, the incubator's own passport dropped from L3 to **L2** on
`development_initiation`. The methodology became stricter towards itself - which is the point.
