"""AUD-001 (Fable, sweep of 2026-09-03) - `verifier_affiliation` is a fact about who owns a repo,
not a value intake writes once and the registry trusts forever.

THE DEFECT THIS PINS. The live registry published `verifier_affiliation: "independent"` for
`whiteknightonhorse/cryptocardhub-public` from 2026-08-25 (commit `deb1624`) until 2026-09-03, even
though its owner IS the operator - `~/orchestra/intake_cron.py:144` derives `same_owner` correctly
for that repo TODAY, but nothing re-checked a row already admitted under whatever logic was live
the moment it was written. No gate compared the stored affiliation to the owner the repo string
itself names, so a one-time intake mistake (or a since-fixed bug in intake's own logic) lived on
the public passport indefinitely.

WHY A PURE FUNCTION, NOT AN IMPORT OF `scripts/cohort.py`. That module performs a live GitHub
measurement loop at module scope (see `tests/test_cohort_l4_requires_signature.py`'s note on the
same constraint) - importing it here would hit the network as a side effect of collecting tests.
`affiliation_violations` is lifted out with `ast` instead, the same technique, so it runs as a pure
function against both the real `data/subjects.json` and synthetic, mutated copies of it.
"""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SRC = ROOT / "scripts" / "cohort.py"


def _load():
    tree = ast.parse(_SRC.read_text(encoding="utf-8"))
    fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef)
               and n.name == "affiliation_violations"), None)
    assert fn is not None, (
        "scripts/cohort.py no longer defines affiliation_violations - AUD-001's gate was removed "
        "or renamed, and this test targets nothing")
    operator = next((n.value.value for n in tree.body
                      if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "OPERATOR" for t in n.targets)),
                     None)
    assert operator, "scripts/cohort.py no longer defines OPERATOR at module scope"
    ns: dict = {"OPERATOR": operator}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(_SRC), "exec"), ns)
    return ns["affiliation_violations"], operator


VIOLATIONS, OPERATOR = _load()


def test_MUTATION_the_live_defect_shape_is_CAUGHT():
    """Reconstructs exactly what was live 2026-08-25 through 2026-09-03: the operator's own repo
    stored as "independent". The gate MUST flag it - this is the RED half of the mutational
    control the defect itself represents."""
    subjects = [{"repo": "whiteknightonhorse/cryptocardhub-public", "affiliation": "independent"}]
    assert VIOLATIONS(subjects, operator=OPERATOR) == ["whiteknightonhorse/cryptocardhub-public"]


def test_the_corrected_row_clears_the_gate():
    """The GREEN half: the same repo, fixed to same_owner, passes."""
    subjects = [{"repo": "whiteknightonhorse/cryptocardhub-public", "affiliation": "same_owner"}]
    assert VIOLATIONS(subjects, operator=OPERATOR) == []


def test_a_genuinely_independent_subject_is_not_flagged():
    """The control the other direction: an applicant who is not the operator is allowed to carry
    "independent" - the gate must not turn every non-same_owner row into a violation."""
    subjects = [{"repo": "someone-else/their-project", "affiliation": "independent"}]
    assert VIOLATIONS(subjects, operator=OPERATOR) == []


def test_owner_match_is_case_insensitive():
    """`~/orchestra/intake_cron.py:143` compares owners with `.lower()`; the gate has to agree with
    the logic it is meant to double-check, or a differently-cased owner would pass one and fail the
    other."""
    subjects = [{"repo": "WhiteKnightOnHorse/some-repo", "affiliation": "independent"}]
    assert VIOLATIONS(subjects, operator=OPERATOR) == ["WhiteKnightOnHorse/some-repo"]


def test_the_real_subjects_file_has_no_violations_today():
    """The actual fix: `data/subjects.json` as committed must already be clean, not merely
    clean-able. If this fails, the corpus itself still carries AUD-001's defect."""
    doc = json.loads((ROOT / "data" / "subjects.json").read_text(encoding="utf-8"))
    assert VIOLATIONS(doc["subjects"], operator=OPERATOR) == []


def test_module_import_refuses_to_run_on_a_bad_corpus():
    """The gate is wired into `scripts/cohort.py` at module scope (`raise SystemExit` right after
    `affiliation_violations` is defined), not left as a function nobody calls - checked here as
    source text since the module itself cannot be safely imported (see module docstring)."""
    src = _SRC.read_text(encoding="utf-8")
    assert "_bad_affiliation = affiliation_violations(_SUBJECTS)" in src
    assert "raise SystemExit(" in src.split("_bad_affiliation = affiliation_violations", 1)[1][:400]
