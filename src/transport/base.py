"""Transport contract. The only place allowed to know how publication happens.

WHY A SEPARATE LAYER. ERC-8004 is in **Draft** status and may change. If the methodology fused
with it, a change to the standard would become a rewrite of the product. Hence: a thin adapter, a
transport-independent methodology, and a SECOND transport that exists precisely so the
independence is demonstrable rather than promised.
"""
from __future__ import annotations

from typing import Protocol


class Transport(Protocol):
    """Publishes a passport and its projection. The projection may be ABSENT - that is not a zero."""

    def publish(self, subject_id: str, passport: dict, projection: int | None) -> str:
        """Return a reference to what was published. Absence is passed through as None."""
        ...
