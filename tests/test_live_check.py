"""T-DL-02: scripts/live_check.py against a local http.server and a fixture git repository.

One failing and one passing case per check and per row kind; `could not run` when the base is
unreachable; the source holds no request method other than GET.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "live_check.py"
spec = importlib.util.spec_from_file_location("live_check", SCRIPT)
lc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lc)

FILES = {"a.txt": b"alpha\n", "b.txt": b"bravo\n", "readme.md": b"# mirror\n"}


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
                          env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                                "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin", "HOME": str(cwd)}).stdout.strip()


@pytest.fixture()
def world(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "web" / "public").mkdir(parents=True)
    for n, b in FILES.items():
        (repo / "web" / "public" / n).write_bytes(b)
    (repo / "README.md").write_text("# readme\n")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "one")
    rev = _git(repo, "rev-parse", "HEAD")
    # a "remote" on disk standing in for github.com
    remote = tmp_path / "gh" / "own" / "proj.git"
    _git(tmp_path, "clone", "-q", "--bare", str(repo), str(remote))
    _git(remote, "branch", "side", "main")

    state = {"rev": rev, "pages": {}, "api": {}}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path == "/deploy-label.txt":
                code, hdr, body = 200, {}, (state["rev"][:7] + "\n").encode()
            elif self.path.startswith("/api/"):
                code, hdr, body = 200, {}, json.dumps(state["api"]).encode()
            elif self.path in state["pages"]:
                code, hdr, body = state["pages"][self.path]
            else:
                code, hdr, body = 404, {}, b"nope"
            self.send_response(code)
            for k, v in hdr.items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    state["pages"] = {f"/{n}": (200, {}, b) for n, b in FILES.items()}
    state["pages"]["/sitemap.xml"] = (200, {}, f"<urlset><url><loc>{base}/a.txt</loc></url></urlset>".encode())
    state["api"] = {"description": "Evidence, not claims - a validator"}

    monkeypatch.setattr(lc, "ROOT", repo)
    monkeypatch.setattr(lc, "GITHUB_GIT", f"file://{tmp_path}/gh/")
    monkeypatch.setattr(lc, "GITHUB_API", base + "/api/")
    w = type("W", (), {})()
    w.repo, w.rev, w.base, w.state, w.tmp, w.srv = repo, rev, base, state, tmp_path, srv

    def run(rows="", excludes="", extra=(), capsys=None, base_url=None):
        claims = tmp_path / "claims.tsv"
        claims.write_text(rows)
        exc = tmp_path / "excl.tsv"
        exc.write_text(excludes)
        rc = lc.main(["--base", base_url or base, "--claims", str(claims), "--excludes", str(exc), *extra])
        return rc, capsys.readouterr().out

    w.run = run
    yield w
    srv.shutdown()


def row(*cols):
    return "\t".join(cols) + "\n"


def test_all_green(world, capsys):
    rc, out = world.run(capsys=capsys)
    assert rc == 0 and out.rstrip().endswith("live-check: ok")


# label -------------------------------------------------------------------------------------
def test_label_equals_rev_passes(world, capsys):
    rc, out = world.run(extra=["--rev", world.rev], capsys=capsys)
    assert rc == 0, out


def test_label_differs_from_rev_fails(world, capsys):
    (world.repo / "x").write_text("x")
    _git(world.repo, "add", "-A")
    _git(world.repo, "commit", "-q", "-m", "two")
    rc, out = world.run(extra=["--rev", "HEAD"], capsys=capsys)
    assert rc == 1 and "FAIL label deploy-label.txt" in out


def test_label_names_unknown_commit_is_could_not_run(world, capsys):
    world.state["rev"] = "deadbeef" * 5
    rc, out = world.run(capsys=capsys)
    assert rc == 2 and "could not run" in out


# files -------------------------------------------------------------------------------------
def test_files_differing_body_fails(world, capsys):
    world.state["pages"]["/b.txt"] = (200, {}, b"changed\n")
    rc, out = world.run(capsys=capsys)
    assert rc == 1 and "FAIL files /b.txt" in out and out.rstrip().endswith("1 failure(s)")


def test_files_missing_live_fails(world, capsys):
    del world.state["pages"]["/b.txt"]
    rc, out = world.run(capsys=capsys)
    assert rc == 1 and "FAIL files /b.txt: live answered 404" in out


def test_exclude_with_writer_removes_the_path(world, capsys):
    world.state["pages"]["/b.txt"] = (200, {}, b"changed\n")
    rc, out = world.run(excludes="/b.txt\tweb/gen.mjs:12 rewrites it\n", capsys=capsys)
    assert rc == 0, out


def test_exclude_without_file_line_is_a_failure(world, capsys):
    world.state["pages"]["/b.txt"] = (200, {}, b"changed\n")
    rc, out = world.run(excludes="/b.txt\tbecause\n", capsys=capsys)
    assert rc == 1 and "FAIL excludes /b.txt" in out and "FAIL files /b.txt" in out


# sitemap -----------------------------------------------------------------------------------
def test_sitemap_url_not_200_fails(world, capsys):
    world.state["pages"]["/sitemap.xml"] = (
        200, {}, f"<urlset><loc>{world.base}/a.txt</loc><loc>{world.base}/gone/</loc></urlset>".encode())
    rc, out = world.run(capsys=capsys)
    assert rc == 1 and "FAIL sitemap" in out and "/gone/: answered 404" in out


# claims: one failing and one passing case per kind ---------------------------------------
CASES = {
    "has": (row("r", "/a.txt", "has", "alpha"), row("r", "/a.txt", "has", "zulu")),
    "lacks": (row("r", "/a.txt", "lacks", "zulu"), row("r", "/a.txt", "lacks", "alpha")),
    "lacks*": (row("r", "*", "lacks", "zulu"), row("r", "*", "lacks", "alpha")),
    "status": (row("r", "/a.txt", "status", "200"), row("r", "/a.txt", "status", "404")),
    "same": (row("r", "/readme.md", "same", "web/public/readme.md"), row("r", "/a.txt", "same", "web/public/b.txt")),
    "head": (row("r", "gh:own/proj", "head", "rev"), None),
    "heads": (row("r", "gh:own/proj", "heads", "main,side"), row("r", "gh:own/proj", "heads", "main")),
    "about": (row("r", "gh:own/proj", "about", "Evidence, not claims"), row("r", "gh:own/proj", "about", "Other words")),
}


@pytest.mark.parametrize("kind", sorted(CASES))
def test_row_kind_passes(world, capsys, kind):
    good, _ = CASES[kind]
    rc, out = world.run(rows=good, capsys=capsys)
    assert rc == 0, out


@pytest.mark.parametrize("kind", sorted(k for k in CASES if CASES[k][1]))
def test_row_kind_fails(world, capsys, kind):
    _, bad = CASES[kind]
    rc, out = world.run(rows=bad, capsys=capsys)
    assert rc == 1 and "FAIL claims r:" in out, out


def test_header_row(world, capsys):
    world.state["pages"]["/a.txt"] = (200, {"Content-Type": "text/markdown; charset=utf-8"}, b"alpha\n")
    rc, out = world.run(rows=row("r", "/a.txt", "header", "content-type: text/markdown", "text/markdown"), capsys=capsys)
    assert rc == 0, out
    rc, out = world.run(rows=row("r", "/a.txt", "header", "content-type: text/html"), capsys=capsys)
    assert rc == 1 and "FAIL claims r" in out


def test_head_row_fails_when_main_is_not_the_rev(world, capsys):
    (world.repo / "x").write_text("x")
    _git(world.repo, "add", "-A")
    _git(world.repo, "commit", "-q", "-m", "two")
    rc, out = world.run(rows=row("r", "gh:own/proj", "head", "rev"), extra=["--rev", "HEAD"], capsys=capsys)
    # the label (one commit behind) already fails, and so does the remote main
    assert rc == 1 and "FAIL claims r: own/proj main is" in out


def test_full_url_on_a_foreign_host_is_refused(world, capsys):
    rc, out = world.run(rows=row("r", "https://example.com/x", "has", "x"), capsys=capsys)
    assert rc == 1 and "FAIL claims r" in out and "not one of the allowed hosts" in out


def test_a_wrong_row_in_a_copy_gives_fail_and_exit_1(world, capsys):
    rc, out = world.run(rows=row("wrong", "/a.txt", "has", "text that is not there"), capsys=capsys)
    assert rc == 1 and "live-check: FAIL claims wrong:" in out


# could not run -----------------------------------------------------------------------------
def test_unreachable_base_is_could_not_run(world, capsys):
    rc, out = world.run(capsys=capsys, base_url="http://127.0.0.1:1")
    assert rc == 2 and out.startswith("live-check: could not run:")


# GET only ----------------------------------------------------------------------------------
def test_source_holds_no_request_method_other_than_get():
    src = SCRIPT.read_text(encoding="utf-8")
    assert re.findall(r"method\s*=\s*[\"'](\w+)[\"']", src) == ["GET"]
    assert not re.search(r"[\"'](POST|PUT|DELETE|PATCH)[\"']", src)
    assert not re.search(r"\bdata\s*=", src), "a request body would make urllib send a POST"
