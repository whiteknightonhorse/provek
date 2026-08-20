"""Evidence taxonomy (ABI-5-4): the class states who can forge it and at what cost.

Mixing classes inside one number without disclosing the mix is FORBIDDEN - otherwise the score
says the same thing about a self-report as it does about a cryptographic signature.
"""
from __future__ import annotations

from enum import Enum


class EvidenceClass(str, Enum):
    SELF_REPORTED = "self_reported"                       # the subject, for free
    PLATFORM_OBSERVED = "platform_observed"               # the subject, at the cost of sustained theatre
    THIRD_PARTY_ATTESTED = "third_party_attested"         # requires collusion with a third party
    CRYPTOGRAPHICALLY_BOUND = "cryptographically_bound"   # requires compromising a key


FORGERY_COST = {
    EvidenceClass.SELF_REPORTED: 0,
    EvidenceClass.PLATFORM_OBSERVED: 1,
    EvidenceClass.THIRD_PARTY_ATTESTED: 2,
    EvidenceClass.CRYPTOGRAPHICALLY_BOUND: 3,
}

SCORABLE = frozenset({
    EvidenceClass.PLATFORM_OBSERVED,
    EvidenceClass.THIRD_PARTY_ATTESTED,
    EvidenceClass.CRYPTOGRAPHICALLY_BOUND,
})
"""SELF_REPORTED never enters the score - it lives in a separate passport branch (ABI-14-2)."""
