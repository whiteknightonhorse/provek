"""T-2.4 - repository vs runtime divergence. The one attack (T4) the MVP detects with confidence.

"Measure the SHIPPED artefact" is an operator law paid for more than once: a file in the repo, a
registry row and an exit code are not what the consumer receives (ABI-5-1, ABI-16-5).

Three outcomes, and they are DIFFERENT (ABI-33-4). Collapsing them is forbidden:
  MATCH        - what is deployed matches what is committed;
  DIVERGED     - it does not: the audited thing is not the running thing. A VIOLATION;
  NOT_MEASURED - we could not read one side. NOT a violation.
"""
from __future__ import annotations

from enum import Enum


class Divergence(str, Enum):
    MATCH = "match"
    DIVERGED = "diverged"
    NOT_MEASURED = "not_measured"


def compare(repo_digest: str | None, deployed_digest: str | None) -> Divergence:
    """Compare the committed tree digest against the deployed artefact digest.

    A missing side yields NOT_MEASURED, never DIVERGED: accusing a subject of divergence because
    we could not read its runtime is a verifier punishing someone for its own blindness.
    """
    if not repo_digest or not deployed_digest:
        return Divergence.NOT_MEASURED
    return Divergence.MATCH if repo_digest == deployed_digest else Divergence.DIVERGED
