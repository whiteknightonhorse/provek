"""T-DEP-05 (D-86) - the site is built only from an install that matches `web/package-lock.json`.

On 2026-11-17 Dependabot auto-merged nine bumps and `web/package-lock.json` named genlayer-js
2.0.0-rc.3 and vite 8.3.8 while the `web/node_modules` every build on this host used had been
installed on 2026-10-28 (rc.2, 8.3.5). Nothing compared the two, so the door built a site from
packages the lockfile did not name. `scripts/check_web_install.py` is that comparison, and the door
(`scripts/push.sh`, step 6/9) runs it before the build.

One test per state the script reports, on fixtures under `tmp_path`: a match, a version drift, a
missing required package, a missing optional one, no install at all, an unreadable lockfile, an
unreadable installed package.json, a lockfile that names nothing. The last block reads the DOOR: the
check must stand on the `6/9` line before the build and be joined to it by `;`, because under
`set -e` the failing left side of `&&` does not stop a script.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_web_install.py"
DOOR = ROOT / "scripts" / "push.sh"


def _fixture(tmp_path: Path, lock_packages: dict, installed: dict[str, str | None]) -> Path:
    """`<tmp>/web` with a lockfile naming `lock_packages` and `node_modules` holding `installed`
    (key -> version; a package absent from `installed` is simply not on disk)."""
    web = tmp_path / "web"
    (web / "node_modules").mkdir(parents=True)
    (web / "package-lock.json").write_text(
        json.dumps({"lockfileVersion": 3, "packages": {"": {"name": "x"}, **lock_packages}}), encoding="utf-8")
    for key, version in installed.items():
        d = web / key
        d.mkdir(parents=True)
        (d / "package.json").write_text(json.dumps({"name": key, "version": version}), encoding="utf-8")
    return web


def _run(web: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(web)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def test_an_install_that_matches_the_lock_is_a_match(tmp_path):
    web = _fixture(
        tmp_path,
        {"node_modules/a": {"version": "1.0.0"}, "node_modules/b": {"version": "2.0.0-rc.3"}},
        {"node_modules/a": "1.0.0", "node_modules/b": "2.0.0-rc.3"})
    rc, out = _run(web)
    assert rc == 0, out
    assert "match: 2 packages installed as the lockfile names them (0 optional absent)" in out


def test_a_version_drift_names_both_versions_and_the_door_command(tmp_path):
    web = _fixture(
        tmp_path,
        {"node_modules/genlayer-js": {"version": "2.0.0-rc.3"}, "node_modules/ok": {"version": "1.0.0"}},
        {"node_modules/genlayer-js": "2.0.0-rc.2", "node_modules/ok": "1.0.0"})
    rc, out = _run(web)
    assert rc == 1, out
    assert "drift: 1 of 2" in out
    assert "node_modules/genlayer-js lock=2.0.0-rc.3 installed=2.0.0-rc.2" in out
    assert "node_modules/ok" not in out
    assert "Door: cd web && npm ci --ignore-scripts" in out


def test_a_required_package_that_is_missing_is_drift(tmp_path):
    web = _fixture(tmp_path, {"node_modules/need": {"version": "3.1.4"}}, {})
    rc, out = _run(web)
    assert rc == 1, out
    assert "drift: 1 of 1" in out
    assert "node_modules/need lock=3.1.4 installed=missing" in out


def test_an_optional_package_that_is_absent_is_not_drift_and_is_counted(tmp_path):
    web = _fixture(
        tmp_path,
        {"node_modules/a": {"version": "1.0.0"},
         "node_modules/fsevents": {"version": "2.3.3", "optional": True}},
        {"node_modules/a": "1.0.0"})
    rc, out = _run(web)
    assert rc == 0, out
    assert "match: 2 packages installed as the lockfile names them (1 optional absent)" in out


def test_an_optional_package_that_is_installed_at_another_version_is_still_drift(tmp_path):
    web = _fixture(
        tmp_path,
        {"node_modules/opt": {"version": "1.2.0", "optional": True}},
        {"node_modules/opt": "1.1.0"})
    rc, out = _run(web)
    assert rc == 1 and "node_modules/opt lock=1.2.0 installed=1.1.0" in out


def test_a_nested_package_is_compared_where_the_lock_puts_it(tmp_path):
    web = _fixture(
        tmp_path,
        {"node_modules/a": {"version": "1.0.0"}, "node_modules/a/node_modules/b": {"version": "9.0.0"}},
        {"node_modules/a": "1.0.0", "node_modules/a/node_modules/b": "8.0.0"})
    rc, out = _run(web)
    assert rc == 1 and "node_modules/a/node_modules/b lock=9.0.0 installed=8.0.0" in out


def test_no_node_modules_is_check_did_not_run_not_drift(tmp_path):
    web = tmp_path / "web"
    web.mkdir()
    (web / "package-lock.json").write_text(
        json.dumps({"packages": {"": {}, "node_modules/a": {"version": "1.0.0"}}}), encoding="utf-8")
    rc, out = _run(web)
    assert rc == 2, out
    assert f"not_measured: check_did_not_run - {web}/node_modules is absent" in out
    assert "drift" not in out


def test_a_lockfile_that_is_not_json_is_unreadable(tmp_path):
    web = _fixture(tmp_path, {}, {})
    (web / "package-lock.json").write_text("{ this is not json", encoding="utf-8")
    rc, out = _run(web)
    assert rc == 2, out
    assert f"not_measured: unreadable - {web}/package-lock.json:" in out


def test_a_lockfile_that_is_absent_is_unreadable(tmp_path):
    web = _fixture(tmp_path, {}, {})
    (web / "package-lock.json").unlink()
    rc, out = _run(web)
    assert rc == 2 and "not_measured: unreadable - " in out


def test_an_installed_package_json_that_is_not_json_is_unreadable_not_drift(tmp_path):
    web = _fixture(tmp_path, {"node_modules/a": {"version": "1.0.0"}}, {"node_modules/a": "1.0.0"})
    (web / "node_modules" / "a" / "package.json").write_text("not json at all", encoding="utf-8")
    rc, out = _run(web)
    assert rc == 2, out
    assert f"not_measured: unreadable - {web}/node_modules/a/package.json:" in out
    assert "drift" not in out


def test_a_lockfile_that_names_no_package_is_nothing_qualified_never_a_match(tmp_path):
    web = _fixture(tmp_path, {}, {})
    rc, out = _run(web)
    assert rc == 2, out
    assert "not_measured: nothing_qualified - the lockfile names no package" in out
    assert "match" not in out


def test_the_three_not_measured_reasons_are_three_different_lines(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    c = tmp_path / "c"
    for d in (a, b, c):
        d.mkdir()
    absent = _fixture(a, {"node_modules/x": {"version": "1.0.0"}}, {})
    (absent / "node_modules").rmdir()
    unreadable = _fixture(b, {"node_modules/x": {"version": "1.0.0"}}, {})
    (unreadable / "package-lock.json").write_text("[", encoding="utf-8")
    empty = _fixture(c, {}, {})
    lines = {_run(w)[1].strip().splitlines()[0].split(" - ")[0] for w in (absent, unreadable, empty)}
    assert lines == {"not_measured: check_did_not_run", "not_measured: unreadable", "not_measured: nothing_qualified"}


# --------------------------------------------------------------------------- the door


def site_line_problems(door: str) -> list[str]:
    """The `echo "6/9` line of `scripts/push.sh` must run the install check BEFORE the build and join
    them with `;`. Under `set -euo pipefail` a failing left side of `&&` does not stop the script
    (errexit is ignored for every command of an AND-list but the last), so `check && build` would
    print `drift:` and build anyway."""
    line = next((ln for ln in door.splitlines() if ln.startswith('echo "6/9')), None)
    if line is None:
        return ['no `echo "6/9` line']
    # Quoted text is a message, not a command (the way tests/test_door_matches_ci.py reads the door).
    code = re.sub(r"'[^']*'|\"[^\"]*\"", " ", line).split("#", 1)[0]
    problems = []
    check, build = code.find("check_web_install.py"), code.find("npm run build")
    if check < 0:
        problems.append("the 6/9 line does not run scripts/check_web_install.py")
    if build < 0:
        problems.append("the 6/9 line does not run `npm run build`")
    if check >= 0 and build >= 0:
        if check > build:
            problems.append("the install check comes after the build on the 6/9 line")
        else:
            # what joins the check to the build is what stands before the build's own subshell; the
            # `&&` inside `( cd web && npm run build )` belongs to the build, not to the join
            opens = code.find("(", check)
            joint = code[check + len("check_web_install.py"):opens if 0 <= opens < build else build]
            if "&&" in joint:
                problems.append("the install check is joined to the build by `&&`, which set -e does not stop on")
            elif ";" not in joint:
                problems.append("the install check is not joined to the build by `;`")
    return problems


def test_the_door_checks_the_install_against_the_lock_before_it_builds():
    assert site_line_problems(DOOR.read_text(encoding="utf-8")) == []


def test_the_door_check_is_able_to_fail():
    door = DOOR.read_text(encoding="utf-8")
    line = next(ln for ln in door.splitlines() if ln.startswith('echo "6/9'))
    assert "check_web_install.py" in line
    removed = door.replace("python3 scripts/check_web_install.py; ", "")
    anded = door.replace("check_web_install.py; (", "check_web_install.py && (")
    swapped = door.replace(
        line, 'echo "6/9 site";     ( cd web && npm run build >/dev/null ); python3 scripts/check_web_install.py')
    assert removed != door and anded != door and swapped != door
    assert any("does not run scripts/check_web_install.py" in p for p in site_line_problems(removed))
    assert any("`&&`" in p for p in site_line_problems(anded))
    assert any("after the build" in p for p in site_line_problems(swapped))
    # a printed excuse is not the command
    excused = door.replace(line, 'echo "6/9 site: check_web_install.py skipped";  ( cd web && npm run build >/dev/null )')
    assert any("does not run scripts/check_web_install.py" in p for p in site_line_problems(excused))


def test_a_failing_left_side_of_and_does_not_stop_a_set_e_script(tmp_path):
    """The reason the door joins with `;`: measured, not asserted."""
    for joint, stops in ((";", True), ("&&", False)):
        sh = tmp_path / f"door{stops}.sh"
        sh.write_text(f"set -euo pipefail\nfalse {joint} true\necho REACHED_THE_BUILD\n", encoding="utf-8")
        r = subprocess.run(["bash", str(sh)], capture_output=True, text=True)
        assert ("REACHED_THE_BUILD" not in r.stdout) is stops, (joint, r.stdout, r.returncode)
