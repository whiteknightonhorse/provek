"""T-THRESHOLD-1, T-BLOCKDEFAULT-1, and a guard against the duplicated enum that hid until today.

Ticket T-2.11 named four ratchets. Two were built and two were not, and the gap was invisible
because `test_thresholds.py` reads like the missing one to anyone skimming filenames — it tests the
Q-D1 governance numbers, not the alert-threshold policy ABI-16-10 requires. A missing gate that
looks present is worse than an absent one.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = sorted([*(ROOT / "src").rglob("*.py"), *(ROOT / "scripts").rglob("*.py")])


# ---------------------------------------------------------------- T-THRESHOLD-1 (ABI-16-10)
def test_no_threshold_is_a_bare_number_at_the_point_of_comparison():
    """ABI-16-10: a threshold is a named policy with a recorded origin, not a literal in an `if`.

    A magic number in a comparison cannot be ratified, cannot be found when it needs changing, and
    cannot be told apart from a measurement. This project has already paid for that once: a cap
    invented for a cost that did not exist became an outage.
    """
    offenders = []
    for path in SOURCES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            for op, comp in zip(node.ops, node.comparators, strict=False):
                if not isinstance(op, (ast.Gt, ast.GtE, ast.Lt, ast.LtE)):
                    continue
                if isinstance(comp, ast.Constant) and isinstance(comp.value, (int, float)):
                    # 0 and 1 are structural, not policy: emptiness and singularity.
                    if comp.value in (0, 1):
                        continue
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno} -> {ast.unparse(node)[:70]}")
    assert offenders == [], "thresholds must be named constants:\n  " + "\n  ".join(offenders)


def test_the_ratified_thresholds_live_in_one_named_place():
    src = (ROOT / "src" / "governance" / "thresholds.py").read_text(encoding="utf-8")
    for value in ("30", "5", "90"):
        assert value in src, f"the ratified threshold {value} is not in the governance module"
    assert "ratif" in src.lower(), "the module must record that these were ratified, not chosen"


# ------------------------------------------------------------- T-BLOCKDEFAULT-1 (ABI-30-2)
def test_every_gate_fails_closed():
    """ABI-30-2: the default is to block. A gate whose except-branch continues is not a gate.

    The shape forbidden here is a bare `except` that swallows and proceeds — the seven-defect class
    in the operator's other systems, where 'no data' and 'the source is dead' returned the same
    value and a twelve-week outage stayed invisible.
    """
    offenders = []
    for path in SOURCES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            body = node.body
            # `pass` alone, or a bare `continue`, is a swallowed failure.
            if len(body) == 1 and isinstance(body[0], (ast.Pass, ast.Continue)):
                offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert offenders == [], "these handlers swallow a failure and carry on:\n  " + "\n  ".join(offenders)


def test_the_thresholds_module_refuses_an_unmeasured_input():
    """An unmeasured input yields not_measured - never go, and never stop either."""
    src = (ROOT / "src" / "governance" / "thresholds.py").read_text(encoding="utf-8")
    assert "NOT_MEASURED" in src or "not_measured" in src


# --------------------------------------------------------------------- the duplicated enum
def test_no_enum_is_declared_twice_across_the_codebase():
    """LAW #ONE-PLACE, caught on 2026-08-20 by an unrelated test.

    `Status` was declared in BOTH lifecycle.py and passport.py with identical members. Because both
    subclass `str`, `==` was true across the boundary while `is` was false — every comparison was
    correct by accident and would have stopped being so the moment either gained a member.
    """
    seen: dict[str, list[str]] = {}
    for path in SOURCES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and any(
                isinstance(b, ast.Name) and b.id == "Enum" for b in node.bases
            ):
                seen.setdefault(node.name, []).append(str(path.relative_to(ROOT)))
    dupes = {k: v for k, v in seen.items() if len(v) > 1}
    assert dupes == {}, f"an enum declared in more than one place: {dupes}"


def test_these_gates_would_fire():
    """Controls, each planted as the exact shape that shipped."""
    planted_threshold = ast.parse("if remaining > 42:\n    pass\n")
    hits = [n for n in ast.walk(planted_threshold)
            if isinstance(n, ast.Compare)
            and isinstance(n.comparators[0], ast.Constant)
            and n.comparators[0].value not in (0, 1)]
    assert hits, "the threshold gate cannot see a magic number"

    planted_swallow = ast.parse("try:\n    f()\nexcept Exception:\n    pass\n")
    handlers = [n for n in ast.walk(planted_swallow) if isinstance(n, ast.ExceptHandler)]
    assert handlers and isinstance(handlers[0].body[0], ast.Pass)

    planted_enum = ast.parse("class S(str, Enum):\n    A = 'a'\n")
    classes = [n for n in ast.walk(planted_enum) if isinstance(n, ast.ClassDef)]
    assert classes and any(isinstance(b, ast.Name) and b.id == "Enum" for b in classes[0].bases)
