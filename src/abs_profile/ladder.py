"""LAW-LADDER-NAMING - L0..L5 measures the AUTONOMY OF A SUBJECT; P0..P5 are OUR agents' permissions.

ABI-2-2 defines a ladder of observable states. The operator's "AI Agent Fleet" document defines
its OWN L0-L5 with a different meaning (OBSERVE..SELF-OPTIMIZING). One name for two quantities is
the same defect class as "one return value, two states of the world", so permissions are named P
in this project.

ABI-2-3: the level is assigned to an OPERATION, never to a company as a whole. A single scalar
for a company is a marketing number, and this product exists to replace marketing numbers.
ABI-2-4: the ladder does NOT measure decision quality, profitability, desirability of autonomy,
reliability, or the presence of an accountable party.
Operator ruling A-5: the ladder is MONOTONIC - L5 is the top, not a red flag.
"""
from __future__ import annotations

from enum import IntEnum


class L(IntEnum):
    """Autonomy of a subject's operation. Higher = more autonomous (A-5, monotonic)."""
    L0 = 0  # a human performs it; the agent drafts or advises
    L1 = 1  # the agent performs it; a human approves EACH instance
    L2 = 2  # the agent performs it; a human approves BY EXCEPTION
    L3 = 3  # the agent performs and decides; a human may intervene but routinely does not
    L4 = 4  # intervention requires a privileged path, and that path is RECORDED
    L5 = 5  # no human control path EXISTS for this operation


class P(IntEnum):
    """Permissions of OUR agents. Indices map 1:1 to the fleet catalogue - numeric configs survive."""
    P0 = 0  # observe
    P1 = 1  # recommend
    P2 = 2  # prepare
    P3 = 3  # execute low-risk
    P4 = 4  # autonomous
    P5 = 5  # self-optimizing


NOT_MEASURED_BY_LADDER = (
    "decision quality", "profitability", "desirability of autonomy",
    "reliability", "presence of an accountable party",
)

# --- LEVEL-ASSIGNMENT POLICY -------------------------------------------------------------------
# ABI-16-10, and these were literals inside comparisons until 2026-08-20 (T-THRESHOLD-1 found them
# on the day it was written). A magic number at the point of comparison cannot be ratified, cannot
# be found when it needs changing, and cannot be told apart from a measurement. This project has
# already paid for that shape once, in another system, where a cap invented for a cost that did not
# exist became the outage.
#
# ASSIGNED, NOT MEASURED, and labelled so. There is no experiment behind them: they are a stated
# reading of what commit evidence can support, awaiting the operator's ratification the way the
# go/no-go numbers were. Until ratified they are the author's proposal, and saying that here is the
# difference between a policy and a leftover.

SOLE_AUTHOR = 1
"""ASSIGNED. One distinct author is the strongest signal a repository can give that no human
rota is behind the commits. It is not proof - attack T1 is unimplementable - which is why a level
built on it is capped and marked `inferred`.

WHAT COUNTS AS AN AUTHOR - RATIFIED BY THE OPERATOR 2026-08-25. Accounts the platform classifies
as bots are EXCLUDED from this count. The rule follows from the sentence above rather than
softening it: this constant claims to detect a HUMAN rota, and a dependency bot's commit is not
evidence of one. Counting it made the signal assert people from commits no person wrote, and cost
a subject a level for adding automation - an inverted incentive in the instrument that sells
autonomy measurement.

It was ratified on evidence that it is not self-serving: applying it changes NEITHER of the
operator's own scores. provek stays L3 (a second identity remains after the bot is removed) and
APIbase stays L3 (its second account is typed `User`). A rule that rescued our own number would
have deserved more suspicion, not less.

THE RESIDUAL HOLES, NAMED RATHER THAN DISCOVERED LATER:
* Automation running on ordinary user accounts (`apibase-dispatch`, `provek-dispatch`) still
  counts as a human. This error points DOWN - it understates autonomy, never overstates it -
  which is the correct direction for a gate to be wrong in.
* Identity resolution is separately defective and NOT addressed here: the collector reads
  `login` and falls back to the commit e-mail, so three different names sharing one address
  collapse into one author while one person with a linked account and one without split into
  two. Measured on provek 2026-08-25. It is left open deliberately - fixing it could RAISE the
  operator's own scores, so it needs its own control and its own ruling, not a quiet edit by the
  interested party.
* Hiding a second human behind a self-installed GitHub App remains possible, but requires
  repository-admin rights, which is attack T1 above - already acknowledged as unmeasurable."""

SIGNED_SHARE_FOR_L4 = 0.9
"""ASSIGNED. The share of commits carrying a verified signature required before a sole-author
repository may reach L4. Below it the evidence is consistent with a human committing by hand."""

FEW_AUTHORS_FOR_L3 = 2
"""ASSIGNED. Above one author but few enough that a machine-led process remains the simplest
explanation."""

SMALL_TEAM_FOR_L3 = 3
"""ASSIGNED. The cohort's own reading of the same question, and DELIBERATELY DIFFERENT from
FEW_AUTHORS_FOR_L3 above: `pipeline.verify` weighs signatures as well, the cohort does not, so the
cohort needs a wider band to reach the same conclusion from less. Two numbers because there are two
procedures - not because one of them drifted."""
