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


# ---------------------------------------------------------------------------------- LAW #ONE-PLACE
# The reasons below are facts about what THIS CODEBASE has built - no pipeline here has ever
# implemented a deployment collector, a treasury collector, or a database channel - identical for
# every subject regardless of which of the three emitters (src/pipeline.py, scripts/cohort.py,
# scripts/measure_qm2.py) is doing the measuring. Until this fix each emitter hand-rolled its own
# `out_of_reach` dict: the wording for "server" drifted ("runtime not presented" vs "runtime not
# presented by the subject"), and two of the four call sites omitted the `deployment` key from
# `out_of_reach` altogether while still marking `deployment` not_measured in the score - a map
# silently under-reporting what it could not see (Fable, 2026-09-01).
DEPLOYMENT_NOT_COLLECTED = "collector not implemented"
TREASURY_OUT_OF_SCOPE = "outside MVP scope"
SERVER_RUNTIME_NOT_PRESENTED = "runtime not presented by the subject"
DATABASE_NO_CHANNEL_ACCESS = "no access through the chosen channel"
STANDARD_UNKNOWN_SHAPE = "privileged access through a CI secret or account recovery"


def build_coverage(*, github_inspected: bool) -> Coverage:
    """The one coverage map every emitter in this tree publishes.

    Parameterized by the single thing that genuinely differs from subject to subject: whether
    GitHub itself answered this reader. Everything else in the map is a fact about the
    methodology, not the subject, so it is built here once rather than copied into every caller
    that constructs a `Coverage`.
    """
    out_of_reach = {
        "deployment": DEPLOYMENT_NOT_COLLECTED,
        "server": SERVER_RUNTIME_NOT_PRESENTED,
        "treasury": TREASURY_OUT_OF_SCOPE,
        "database": DATABASE_NO_CHANNEL_ACCESS,
    }
    if github_inspected:
        inspected = [Surface.GITHUB]
    else:
        # Nothing was read, so nothing was inspected, and github itself joins the unreachable
        # surfaces with the reason (Fable, B2): a map that still claimed "Inspected: github" after
        # a 404 asserted an inspection that never happened.
        inspected = []
        out_of_reach["github"] = "the repository did not answer a reader holding no credential"
    return Coverage(inspected=inspected, out_of_reach=out_of_reach,
                    unknown_shape=STANDARD_UNKNOWN_SHAPE)
