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
