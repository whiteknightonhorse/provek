"""T-2.5 - Human Control Map (ABI-7-1..7-5).

WHAT THE MAP PROVES AND WHAT IT NEVER PROVES. It proves that a path EXISTS. It can never prove
that no undiscovered path exists - that is impossible in principle (unimplementable register U-3).
So the map MUST publish its own COVERAGE: what was inspected, what was out of reach, and what an
undiscovered path would look like. A checker that silently skips what it cannot inspect reports
success on what it never examined (operator's law, brief Appendix B item 4).

ABI-7-4 requires distinguishing TWO capabilities, and the distinction is load-bearing:
  improve_or_fix              - a human can repair and improve. Does NOT contradict autonomy;
  operate_redirect_or_extract - a human can operate, redirect and extract value.
                                THIS is what limits autonomy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Surface(str, Enum):
    PRIVATE_KEY = "private_key"
    API_KEY = "api_key"
    ADMIN_ACCOUNT = "admin_account"
    DATABASE = "database"
    SERVER = "server"
    DEPLOYMENT = "deployment"
    GITHUB = "github"
    SMART_CONTRACT = "smart_contract"
    TREASURY = "treasury"
    CLOUD = "cloud"
    OTHER = "other"


class Capability(str, Enum):
    IMPROVE_OR_FIX = "improve_or_fix"
    OPERATE_REDIRECT_EXTRACT = "operate_or_redirect_or_extract"


@dataclass(frozen=True)
class ControlPath:
    surface: Surface
    capability: Capability
    recorded: bool          # is USE of the path recorded - this is what separates L4 from L3


@dataclass(frozen=True)
class Coverage:
    """Without coverage the map is INVALID. Not decoration - a condition of its meaning."""
    inspected: list[Surface]
    out_of_reach: dict[str, str]        # surface -> REASON it was unreachable
    unknown_shape: str                  # what an undiscovered path would look like

    def is_valid(self) -> bool:
        return bool(self.inspected) and bool(self.unknown_shape)


@dataclass(frozen=True)
class ControlMap:
    paths: list[ControlPath] = field(default_factory=list)
    coverage: Coverage | None = None

    def is_valid(self) -> bool:
        """A map without coverage is not a map (ABI-7-5)."""
        return self.coverage is not None and self.coverage.is_valid()

    def limits_autonomy(self) -> list[ControlPath]:
        """Paths that LIMIT autonomy. The ability to repair is not one of them."""
        return [p for p in self.paths
                if p.capability is Capability.OPERATE_REDIRECT_EXTRACT]

    def implied_level_cap(self) -> int:
        """The ceiling the map imposes on the L ladder.

        No limiting path        -> L5 reachable.
        Limiting but RECORDED   -> ceiling L4.
        Limiting and unrecorded -> ceiling L3.
        """
        limiting = self.limits_autonomy()
        if not limiting:
            return 5
        return 4 if all(p.recorded for p in limiting) else 3
