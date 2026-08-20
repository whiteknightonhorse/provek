"""LAW-GRANTED-CHANNEL-ONLY — a subject is read the way an external subject would grant it.

Master specification 10.2 (revision 1.3), and ADR-0006 in this repository: access to the operator's
own systems goes through the SAME CHANNEL an external subject would use - a scoped read-only token.
Reading through host privilege is FORBIDDEN, because a methodology that reads its subject as root
cannot be reproduced by a third party (ABI-5-3).

Until 2026-08-20 two emitters opened with a regex over token shapes, executed as root, against a
NEIGHBOURING project's private file. The letter of ADR-0006 covers reading the subject; those calls
harvested the credential instead, which lands in the same place: the token was extracted rather
than granted, and no third party can reproduce the pipeline. Every passport published before that
date descends from it.

This test parses the AST rather than grepping the text, because the fix leaves the forbidden call
QUOTED in a docstring that explains it - and a text search cannot tell an explanation from an
instruction. A grep-based version of this gate would have failed on its own documentation, which
is how a gate gets weakened until it passes.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCES = sorted([*(ROOT / "src").rglob("*.py"), *(ROOT / "scripts").rglob("*.py")])
PRIVILEGE = ("sudo", "doas", "pkexec", "su")


def _privileged_calls(tree: ast.AST) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for arg in ast.walk(node):
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                word = arg.value.strip().split("/")[-1]
                if word in PRIVILEGE:
                    found.append(f"line {node.lineno}: {ast.unparse(node)[:90]}")
                    break
    return found


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.name)
def test_no_module_reads_through_host_privilege(path: pathlib.Path):
    found = _privileged_calls(ast.parse(path.read_text(encoding="utf-8")))
    assert found == [], f"{path.relative_to(ROOT)} escalates privilege: {found}"


def test_the_gate_fires_on_the_call_that_shipped():
    """A control. This is verbatim what both emitters ran before 2026-08-20."""
    planted = ast.parse(
        'import subprocess\n'
        'tok = subprocess.run(["sudo", "grep", "-ohE", "gh[pous]_[A-Za-z0-9_]+",\n'
        '                      "/home/audiobook2/.claude/gh.env"],\n'
        '                     capture_output=True, text=True).stdout\n'
    )
    assert _privileged_calls(planted), "the gate cannot see the call it exists to forbid"


def test_the_gate_does_not_fire_on_an_explanation_of_it():
    """The fix keeps the forbidden call quoted in a docstring. A grep would convict the fix."""
    doc = ast.parse('def f():\n    """We used to run: subprocess.run(["sudo", "grep", ...])."""\n')
    assert _privileged_calls(doc) == []


def test_no_emitter_REQUIRES_a_credential():
    """The channel must be reproducible by a reader who holds nothing.

    Fable's remedy for V1 was a hand-issued scoped read-only token. Measurement found a stricter
    answer: every call this pipeline makes is a public read that returns 200 unauthenticated, and a
    full cohort costs 24 of the 60 anonymous requests GitHub allows per hour. A scoped token makes
    the pipeline reproducible by whoever the operator grants one; no token makes it reproducible by
    anyone, which is what ABI-5-3 actually asks.

    So this asserts the ABSENCE of a requirement. An emitter that exits when a credential is
    missing has re-introduced the gate that V1 was about.
    """
    for name in ("cohort.py", "measure_qm2.py"):
        src = (ROOT / "scripts" / name).read_text(encoding="utf-8")
        assert "optional_token()" in src, f"{name} must obtain its token through the optional path"
        assert "raise SystemExit" not in src.split("def optional_token")[1].split("\n\n\n")[0], (
            f"{name} must not refuse to run without a credential")


def test_the_collector_works_with_no_token_at_all():
    """The default argument is the whole claim: `collect_github(name)` must be a valid call."""
    import inspect

    from src.collector.github import _api, access_channel, collect_github

    assert inspect.signature(collect_github).parameters["token"].default is None
    assert inspect.signature(_api).parameters["token"].default is None
    assert access_channel(None) == "anonymous"
    assert access_channel("ghp_x") == "granted_token"
