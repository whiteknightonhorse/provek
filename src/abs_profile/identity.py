"""Subject identity (ABI-12-7) - an ABSTRACTION of the profile, not a borrowed type.

Two normative requirements: it survives redeployment, and it cannot be trivially assumed by
another party. The ERC-8004 Identity Registry is the PRIMARY BINDING of this abstraction, not its
definition (revision 1.1: a hard binding blocked the first cohort and gutted the
transport-independence test).

Revision 1.2, after the control refutation: bindings are NOT equally strong, and that must be
VISIBLE. A domain expires and can be bought by someone else - once expired, the identity is
trivially assumed, which directly violates the second requirement. So binding strength is an
explicit passport field, never an assumption.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BindingKind(str, Enum):
    ERC8004 = "erc8004"   # ownership of an ERC-721 token
    GIT = "git"           # remote plus signing key
    DNS = "dns"           # domain plus a well-known signature


class Strength(str, Enum):
    STRONG = "strong"
    WEAK = "weak"


TRANSFERABLE, EXPIRABLE, REVOCABLE = "transferable", "expirable", "revocable"

_PROPS = {
    BindingKind.ERC8004: (Strength.STRONG, [TRANSFERABLE]),
    BindingKind.GIT: (Strength.WEAK, [REVOCABLE]),                # keys rotate, remotes migrate
    BindingKind.DNS: (Strength.WEAK, [EXPIRABLE, TRANSFERABLE]),  # domains expire and get resold
}


@dataclass(frozen=True)
class Binding:
    kind: BindingKind
    locator: str

    @property
    def strength(self) -> Strength:
        return _PROPS[self.kind][0]

    @property
    def flags(self) -> list[str]:
        return list(_PROPS[self.kind][1])

    def as_subject_id(self) -> str:
        return f"{self.kind.value}:{self.locator}"


def continuity_preserved(old: Binding, new: Binding, cross_signature: bool) -> bool:
    """Rebinding preserves accumulated reputation ONLY through a cross-signature.

    Without it, this is a new identity with no history - which also closes part of attack T10
    (reputation laundering by re-registration).
    """
    return bool(cross_signature)
