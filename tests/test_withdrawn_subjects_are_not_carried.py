"""T-IN-07 / D-72 - a subject under `withdrawn` in data/subjects.json is not carried, not
published, not given a page, and cannot be listed twice.

`scripts/cohort.py` measures at module scope, so its pure parts are lifted with `ast` (the technique
of tests/test_cohort_previous_rows_isotime.py); the two import-time refusals are run for real in a
scratch tree whose `scripts/cohort.py` is a copy, and refuse before any network call.
"""
import ast
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

from src.abs_profile.isotime import parse_iso_ts
from src.registry.public_registry import Row

ROOT = Path(__file__).resolve().parents[1]
COHORT = ROOT / "scripts" / "cohort.py"
PROBE = ROOT / "tests" / "withdrawn_probe.mjs"
GONE = "acme/gone"


def _load(*names, **extra):
    tree = ast.parse(COHORT.read_text(encoding="utf-8"))
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {f.name for f in fns} == set(names), f"scripts/cohort.py lost one of {names}"
    ns = {"json": json, "Row": Row, "parse_iso_ts": parse_iso_ts, "datetime": datetime,
          "Path": Path, **extra}
    exec(compile(ast.Module(body=fns, type_ignores=[]), str(COHORT), "exec"), ns)
    return ns


def _row(sid):
    return {"subject_id": sid, "status": "verified", "projection": 40,
            "projection_absent_reason": None, "protocol_version": "1.0.0",
            "valid_until": "2026-12-01T00:00:00+00:00", "passport_ref": f"ref/{sid}",
            "verifier_affiliation": "independent"}


def test_the_carried_set_excludes_a_withdrawn_row_and_says_so(tmp_path, capsys):
    (tmp_path / "registry").mkdir()
    rows = [_row("git:acme/one"), _row(f"git:{GONE}"), _row("git:acme/two")]
    (tmp_path / "registry" / "registry.json").write_text(
        json.dumps({"generated_at": "2026-10-01T00:00:00+00:00", "subjects": rows}))
    helpers = _load("withdrawn_subject_ids")
    ns = _load("previous_rows", out=tmp_path, WITHDRAWN=[{"repo": GONE}],
               withdrawn_subject_ids=helpers["withdrawn_subject_ids"])
    carried = ns["previous_rows"]()
    assert sorted(carried) == ["git:acme/one", "git:acme/two"]
    assert f"withdrawn, not carried: git:{GONE}" in capsys.readouterr().out


def test_the_run_removes_only_the_withdrawn_passport_files(tmp_path):
    a, b = tmp_path / "public", tmp_path / "served"
    for d in (a, b):
        d.mkdir()
        (d / "git_acme_gone.json").write_text("{}")
        (d / "git_acme_one.json").write_text("{}")
    helpers = _load("withdrawn_subject_ids", "remove_withdrawn_passports")
    removed = helpers["remove_withdrawn_passports"]([{"repo": GONE}], [a, b])
    assert sorted(p.name for p in removed) == ["git_acme_gone.json"] * 2
    for d in (a, b):
        assert [p.name for p in d.iterdir()] == ["git_acme_one.json"]
    assert helpers["remove_withdrawn_passports"]([{"repo": GONE}], [a, b]) == []   # idempotent


def test_a_repo_in_both_lists_is_named():
    v = _load("withdrawn_violations")["withdrawn_violations"]
    assert v([{"repo": "acme/one"}, {"repo": GONE}], [{"repo": GONE}]) == [GONE]
    assert v([{"repo": "acme/one"}], [{"repo": GONE}]) == []


def _subject(repo):
    return {"repo": repo, "affiliation": "independent", "source": "test"}


def _scratch(tmp_path, doc):
    """A tree whose cohort.py is a copy; it must refuse at import, before any network call."""
    (tmp_path / "scripts").mkdir()
    (tmp_path / "data").mkdir()
    shutil.copy(COHORT, tmp_path / "scripts" / "cohort.py")
    shutil.copy(ROOT / "data" / "operator_owners.json", tmp_path / "data")
    (tmp_path / "data" / "subjects.json").write_text(json.dumps(doc))
    os.symlink(ROOT / "src", tmp_path / "src")
    env = {k: v for k, v in os.environ.items() if k != "PROVEK_GITHUB_TOKEN"}
    return subprocess.run([sys.executable, str(tmp_path / "scripts" / "cohort.py")], cwd=tmp_path,
                          capture_output=True, text=True, timeout=60, env=env)


def test_both_lists_naming_one_repo_is_a_systemexit_at_import(tmp_path):
    entry = {"repo": GONE, "at": "t", "reason": "r", "by": "subject"}
    done = _scratch(tmp_path, {"subjects": [_subject(GONE)], "withdrawn": [entry]})
    assert done.returncode != 0
    assert "both a subject and withdrawn" in done.stderr and GONE in done.stderr


def test_a_file_without_the_withdrawn_key_is_refused(tmp_path):
    done = _scratch(tmp_path, {"subjects": [_subject("acme/one")]})
    assert done.returncode != 0
    assert "no `withdrawn` list" in done.stderr


def _withdraw_module():
    spec = importlib.util.spec_from_file_location(
        "withdraw_subject", ROOT / "scripts" / "withdraw_subject.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_withdraw_moves_the_row_and_refuses_twice(tmp_path, capsys):
    f = tmp_path / "subjects.json"
    f.write_text(json.dumps({"subjects": [_subject("acme/one"), _subject(GONE)], "withdrawn": []}))
    mod = _withdraw_module()
    assert mod.main([GONE, "--reason", "owner asked", "--by", "subject", "--file", str(f)]) == 0
    doc = json.loads(f.read_text())
    assert [s["repo"] for s in doc["subjects"]] == ["acme/one"]
    (w,) = doc["withdrawn"]
    assert (w["repo"], w["reason"], w["by"]) == (GONE, "owner asked", "subject")
    assert datetime.fromisoformat(w["at"]).tzinfo is not None
    out = capsys.readouterr().out
    assert "python3 scripts/cohort.py" in out and "push.sh" in out
    before = f.read_text()
    with pytest.raises(SystemExit, match="already withdrawn"):
        mod.main([GONE, "--reason", "again", "--by", "operator", "--file", str(f)])
    with pytest.raises(SystemExit, match="not a subject"):
        mod.main(["acme/nobody", "--reason", "x", "--by", "operator", "--file", str(f)])
    assert f.read_text() == before


def _routes(payload):
    try:
        done = subprocess.run(["node", str(PROBE)], cwd=ROOT, input=json.dumps(payload),
                              capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        raise AssertionError("`node` is not on PATH, so the route list cannot be held") from None
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def test_the_page_route_list_has_no_withdrawn_subject():
    registry = {"subjects": [{"subject_id": "git:acme/one"}, {"subject_id": f"git:{GONE}"}]}
    payload = {"registry": registry, "passports": ["git_acme_one", "git_acme_gone"],
               "subjects_doc": {"withdrawn": [{"repo": GONE}]}}
    assert _routes(payload) == ["/p/git_acme_one/"]
    payload["subjects_doc"] = {"withdrawn": []}      # control: not withdrawn, the page is routed
    assert _routes(payload) == ["/p/git_acme_one/", "/p/git_acme_gone/"]


def test_the_two_public_sentences_are_on_the_pages():
    apply_src = (ROOT / "web" / "src" / "pages" / "Apply.tsx").read_text(encoding="utf-8")
    assert "Removal:" in apply_src
    assert "Git history and third-party caches keep what was" in apply_src
    reg_src = (ROOT / "web" / "src" / "pages" / "Registry.tsx").read_text(encoding="utf-8")
    assert "A withdrawn subject is not listed" in reg_src and "corrections log" in reg_src
