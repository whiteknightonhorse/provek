"""T-2.9 - file transport. It exists to make transport-independence PROVABLE.

This is not a stub and not a placeholder for ERC-8004. It is the second transport on which
`T-TRANSPORT-2` shows that the same methodology prints the same result into two different
environments. While it works, the standard's Draft status is not a risk to the product: what
would fall is distribution, not the product.
"""
from __future__ import annotations

import json
from pathlib import Path


class FileTransport:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def publish(self, subject_id: str, passport: dict, projection: int | None) -> str:
        safe = subject_id.replace(":", "_").replace("/", "_")
        p = self.root / f"{safe}.json"
        p.write_text(json.dumps(
            {"subject_id": subject_id, "projection": projection, "passport": passport},
            ensure_ascii=False, indent=2), encoding="utf-8")
        return p.as_posix()
