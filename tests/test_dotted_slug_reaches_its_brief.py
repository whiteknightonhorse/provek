"""T-IN-06 - a repository named `a.b` reaches its own brief and badge.

`slugOf` keeps the `.`, so `git:o/r.name` has the passport `/p/git_o_r.name/`. The slug rule used to
refuse the dot, leaving that subject with a page and no brief or badge. WHAT IS RUN: the guard
`isSafeSlug`, under Node, through `tests/slug_probe.mjs` (the same bytes the bundle ships). WHAT IS
READ AS SOURCE: the Functions' own `SLUG` copies, held identical to the guard by
`tests/test_slug_rule_is_one_place.py` - there is no harness that executes `brief.js` end to end.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "slug_probe.mjs"


def probe(slugs: list) -> list[dict]:
    done = subprocess.run(["node", str(PROBE), json.dumps(slugs)], capture_output=True, text=True,
                          timeout=60)
    assert done.returncode == 0, f"slug_probe exited {done.returncode}: {done.stderr}"
    return json.loads(done.stdout)


def test_a_dotted_repository_slug_is_safe() -> None:
    assert probe(["git_o_r.name"])[0]["safe"] is True


def test_two_dots_in_a_row_are_not() -> None:
    assert probe(["a..b"])[0]["safe"] is False


def test_the_slug_the_emitter_makes_from_a_dotted_id_is_safe() -> None:
    """`slugOf` is `id.replace(/[:/]/g, "_")`; derive it the way the emitter does, not by hand."""
    import re
    slug = re.sub(r"[:/]", "_", "git:owner/repo.name")
    assert slug == "git_owner_repo.name"
    assert probe([slug])[0]["safe"] is True
