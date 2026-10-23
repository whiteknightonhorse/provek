"""D-70 - the verifier's own GitHub owners are one file, and the gate reads the file.

`scripts/cohort.py` measures live at import, so the file is exercised the way the sibling tests
do: the two functions and the loading statement are lifted with `ast` and run against a copy of
the file in a temporary directory.
"""
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SRC = ROOT / "scripts" / "cohort.py"
_FILE = ROOT / "data" / "operator_owners.json"
_LOGIN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")


def _gate(owners_file: Path):
    """The names `cohort.py` derives from the file, evaluated against `owners_file`."""
    tree = ast.parse(_SRC.read_text(encoding="utf-8"))
    keep = [n for n in tree.body
            if (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_OWNERS_DOC"
                                                  for t in n.targets))
            or (isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") == "OPERATOR_OWNERS")
            or (isinstance(n, ast.FunctionDef) and n.name == "affiliation_violations")]
    assert len(keep) == 3, "cohort.py no longer loads OPERATOR_OWNERS from the file"
    # point the loader at the temporary copy: ROOT/"data"/"operator_owners.json" -> owners_file
    src = ast.unparse(ast.Module(body=keep, type_ignores=[]))
    src = src.replace("Path(__file__).resolve().parents[1] / 'data' / 'operator_owners.json'",
                      "OWNERS_FILE")
    assert "OWNERS_FILE" in src
    ns: dict = {"json": json, "Path": Path, "OWNERS_FILE": owners_file}
    exec(compile(src, str(_SRC), "exec"), ns)
    return ns


def test_the_owner_list_is_read_from_the_file_and_not_a_literal(tmp_path):
    f = tmp_path / "operator_owners.json"
    f.write_text(json.dumps({"owners": ["Some-Org"]}), encoding="utf-8")
    ns = _gate(f)
    assert ns["OPERATOR_OWNERS"] == frozenset({"some-org"})
    subjects = [{"repo": "some-org/a", "affiliation": "independent"},
                {"repo": "defycard-com/b", "affiliation": "independent"}]
    assert ns["affiliation_violations"](subjects) == ["some-org/a"]


def test_the_shipped_file_names_both_owners():
    owners = json.loads(_FILE.read_text(encoding="utf-8"))["owners"]
    assert {o.lower() for o in owners} >= {"whiteknightonhorse", "defycard-com"}


def test_the_list_has_no_duplicates_and_only_valid_github_logins():
    owners = json.loads(_FILE.read_text(encoding="utf-8"))["owners"]
    assert owners, "the list is empty"
    lowered = [o.lower() for o in owners]
    assert len(lowered) == len(set(lowered)), "duplicate owner: " + repr(owners)
    assert [o for o in owners if not _LOGIN.match(o)] == []


def test_an_empty_list_is_refused_at_import():
    src = _SRC.read_text(encoding="utf-8")
    tail = src.split("OPERATOR_OWNERS: frozenset[str]", 1)[1][:400]
    assert "if not OPERATOR_OWNERS:" in tail and "raise SystemExit(" in tail
