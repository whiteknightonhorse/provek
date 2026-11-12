"""Live check: provek.dev and the public GitHub repositories say what the deployed commit says.

scripts/verify_live.sh proves status codes. This script adds the CONTENT check (DOCS-LAW-PA-1112
ruling-1, card T-DL-02): one script, one rows file, no browser, no model call. GET requests and
`git ls-remote` only - `/api/apply` creates an intake record on POST, so nothing here may POST (the
test reads this file and refuses any other request method).

Run as `python3 -I scripts/live_check.py [--base URL] [--rev REV] [--quiet]`.

Output: one `live-check: FAIL <check> <id>: <detail>` line per failure; the last line is
`live-check: ok`, `live-check: <N> failure(s)` or `live-check: could not run: <why>`.
Exit 0 / 1 / 2. "Could not run" is its own state, never a pass and never a failure of the site.

Checks: label, files (web/public of the rev against the live bytes, minus
scripts/live_check_excludes.tsv), sitemap (every <loc> answers 200), claims (scripts/live_claims.tsv).

Claims file: TAB-separated `id, target, kind, text, [accept]`; `#` starts a comment line.
  target: a site path `/...`; a full https URL (allowed hosts only); `*` (every sitemap URL);
          `gh:<owner>/<repo>`.
  kind:   has / lacks (text in / not in the body; with target `*` on no sitemap page),
          status (text = code), header (text = `name: value`, value is a substring),
          same (body sha256 == sha256 of `git show <rev>:<text>`),
          head (`git ls-remote` main == rev when text is `rev`, or == HEAD of the local directory text),
          heads (the branch set of the repo is exactly the comma list in text),
          about (the repo description from api.github.com contains text).
  accept: optional Accept header of the request.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ALLOWED_HOSTS = frozenset({"provek.dev", "raw.githubusercontent.com", "api.github.com", "github.com"})
GITHUB_GIT = "https://github.com/"             # + owner/repo + .git
GITHUB_API = "https://api.github.com/repos/"   # + owner/repo
DEFAULT_BASE = "https://provek.dev"
# The default `Python-urllib` agent is refused by the edge with 403; a check that cannot read the
# site would report every page as broken.
USER_AGENT = "provek-live-check/1"
TIMEOUT_S = 30
ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = "web/public"
# Row shape of live_claims.tsv: id, target, kind, text are required, accept is optional.
ROW_REQUIRED_COLS = 4
ROW_MAX_COLS = 5
KINDS = ("has", "lacks", "status", "header", "same", "head", "heads", "about")


class CouldNotRun(Exception):
    pass


class Refused(Exception):
    """A URL outside the allowed hosts: refused before any socket opens."""


class Fetched:
    def __init__(self, status: int, headers, body: bytes):
        self.status, self.headers, self.body = status, headers, body

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


class Checker:
    def __init__(self, base: str, rev_arg: str | None, root: Path):
        self.base = base.rstrip("/")
        self.root = root
        self.rev_arg = rev_arg
        self.allowed = set(ALLOWED_HOSTS) | {urllib.parse.urlsplit(self.base).hostname or ""}
        self.failures: list[str] = []
        self.cache: dict = {}
        self.rev: str | None = None
        self.counts = {"files": 0, "urls": 0, "rows": 0}

    # -- plumbing ---------------------------------------------------------------------------
    def fail(self, check: str, ident: str, detail: str) -> None:
        self.failures.append(f"live-check: FAIL {check} {ident}: {detail}")

    def _opener(self):
        checker = self

        class Guard(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                checker._guard(newurl)
                return super().redirect_request(req, fp, code, msg, headers, newurl)

        return urllib.request.build_opener(Guard)

    def _guard(self, url: str) -> None:
        host = urllib.parse.urlsplit(url).hostname or ""
        if host not in self.allowed:
            raise Refused(f"host {host!r} is not one of the allowed hosts")

    def get(self, url: str, accept: str = "") -> Fetched:
        """GET and nothing else. HTTP error codes come back as a Fetched; a network failure raises URLError."""
        key = (url, accept)
        if key in self.cache:
            return self.cache[key]
        self._guard(url)
        headers = {"User-Agent": USER_AGENT}
        if accept:
            headers["Accept"] = accept
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with self._opener().open(req, timeout=TIMEOUT_S) as r:
                out = Fetched(r.status, r.headers, r.read())
        except urllib.error.HTTPError as e:
            out = Fetched(e.code, e.headers, e.read())
        self.cache[key] = out
        return out

    def url_of(self, target: str) -> str:
        return self.base + target if target.startswith("/") else target

    def git(self, *args: str, binary: bool = False, cwd: Path | None = None):
        try:
            p = subprocess.run(["git", *args], cwd=str(cwd or self.root), capture_output=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise CouldNotRun(f"git {args[0]} did not run: {e}") from None
        out = p.stdout if binary else p.stdout.decode("utf-8", errors="replace")
        return p.returncode, out

    def resolve(self, rev: str) -> str | None:
        rc, out = self.git("rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
        return out.strip() if rc == 0 and out.strip() else None

    def ls_remote(self, repo: str, *refs: str, heads: bool = False) -> dict[str, str]:
        opts = ["--heads"] if heads else []
        rc, out = self.git("ls-remote", *opts, GITHUB_GIT + repo + ".git", *refs)
        if rc != 0:
            raise CouldNotRun(f"git ls-remote {repo} failed")
        res = {}
        for line in out.splitlines():
            sha, _, ref = line.partition("\t")
            res[ref] = sha
        return res

    # -- checks -----------------------------------------------------------------------------
    def check_label(self) -> None:
        try:
            r = self.get(self.base + "/deploy-label.txt")
        except urllib.error.URLError as e:
            raise CouldNotRun(f"{self.base} unreachable: {e.reason}") from None
        except (OSError, Refused) as e:
            raise CouldNotRun(f"{self.base} unreadable: {e}") from None
        label = r.text.strip()
        if r.status != 200 or not label:
            if not self.rev_arg:
                raise CouldNotRun(f"/deploy-label.txt answered {r.status}; no --rev given")
            self.fail("label", "deploy-label.txt", f"answered {r.status}, no label")
            self.rev = self.resolve(self.rev_arg)
            return
        label_full = self.resolve(label)
        if self.rev_arg:
            self.rev = self.resolve(self.rev_arg)
            if self.rev is None:
                raise CouldNotRun(f"--rev {self.rev_arg} is not a commit of this repository")
            if label_full is None:
                self.fail("label", "deploy-label.txt", f"label {label!r} names no commit git cat-file finds")
            elif label_full != self.rev:
                self.fail("label", "deploy-label.txt", f"live label {label} is not {self.rev[:12]}")
        else:
            if label_full is None:
                raise CouldNotRun(f"live label {label!r} names no commit in this repository")
            self.rev = label_full

    def excludes(self, path: Path) -> set[str]:
        out: set[str] = set()
        if not path.is_file():
            return out
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip() or line.startswith("#"):
                continue
            cols = line.split("\t")
            p, reason = cols[0], (cols[1] if len(cols) > 1 else "")
            if not re.search(r"\S+:\d+", reason):
                self.fail("excludes", p or f"line{n}", "the reason must name the writer with file:line")
                continue
            out.add(p)
        return out

    def check_files(self, excl: set[str]) -> None:
        rc, out = self.git("ls-tree", "-r", "--name-only", self.rev, "--", PUBLIC_DIR)
        if rc != 0:
            raise CouldNotRun(f"git ls-tree {self.rev[:12]} failed")
        for path in out.splitlines():
            rel = path[len(PUBLIC_DIR):]
            if rel in excl or path in excl:
                continue
            self.counts["files"] += 1
            rc, want = self.git("show", f"{self.rev}:{path}", binary=True)
            try:
                r = self.get(self.base + urllib.parse.quote(rel))
            except (urllib.error.URLError, OSError) as e:
                self.fail("files", rel, f"unreadable: {getattr(e, 'reason', e)}")
                continue
            if r.status != 200:
                self.fail("files", rel, f"live answered {r.status}")
            elif hashlib.sha256(r.body).hexdigest() != hashlib.sha256(want).hexdigest():
                self.fail("files", rel, f"live sha256 {hashlib.sha256(r.body).hexdigest()[:12]} "
                                        f"!= {self.rev[:12]} sha256 {hashlib.sha256(want).hexdigest()[:12]}")

    def sitemap_urls(self) -> list[str]:
        r = self.get(self.base + "/sitemap.xml")
        if r.status != 200:
            self.fail("sitemap", "sitemap.xml", f"answered {r.status}")
            return []
        return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", r.text)

    def check_sitemap(self, urls: list[str]) -> None:
        for u in urls:
            self.counts["urls"] += 1
            try:
                r = self.get(u)
            except Refused as e:
                self.fail("sitemap", u, str(e))
                continue
            except (urllib.error.URLError, OSError) as e:
                self.fail("sitemap", u, f"unreadable: {getattr(e, 'reason', e)}")
                continue
            if r.status != 200:
                self.fail("sitemap", u, f"answered {r.status}")

    def check_claims(self, path: Path, sitemap: list[str]) -> None:
        if not path.is_file():
            raise CouldNotRun(f"{path} does not exist")
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip() or line.startswith("#"):
                continue
            cols = line.split("\t")
            if len(cols) < ROW_REQUIRED_COLS or cols[2] not in KINDS:
                self.fail("claims", cols[0] or f"line{n}", "malformed row (id, target, kind, text, [accept])")
                continue
            ident, target, kind, text = cols[:ROW_REQUIRED_COLS]
            accept = cols[ROW_REQUIRED_COLS] if len(cols) >= ROW_MAX_COLS else ""
            self.counts["rows"] += 1
            try:
                self.row(ident, target, kind, text, accept, sitemap)
            except Refused as e:
                self.fail("claims", ident, str(e))
            except (urllib.error.URLError, OSError) as e:
                self.fail("claims", ident, f"unreadable: {getattr(e, 'reason', e)}")

    def row(self, ident, target, kind, text, accept, sitemap) -> None:
        if target.startswith("gh:"):
            return self.row_github(ident, target[3:], kind, text)
        if target == "*":
            if kind != "lacks":
                return self.fail("claims", ident, "target * is only for lacks")
            for u in sitemap:
                r = self.get(u, accept)
                if text in r.text:
                    self.fail("claims", ident, f"{u} still says {text!r}")
            return
        r = self.get(self.url_of(target), accept)
        if kind == "status":
            if str(r.status) != text:
                self.fail("claims", ident, f"{target} answered {r.status}, want {text}")
        elif kind == "has":
            if text not in r.text:
                self.fail("claims", ident, f"{target} lacks {text!r}")
        elif kind == "lacks":
            if text in r.text:
                self.fail("claims", ident, f"{target} still says {text!r}")
        elif kind == "header":
            name, _, value = text.partition(":")
            got = r.headers.get(name.strip(), "")
            if value.strip().lower() not in got.lower():
                self.fail("claims", ident, f"{target} header {name.strip()} is {got!r}, want {value.strip()!r}")
        elif kind == "same":
            rc, want = self.git("show", f"{self.rev}:{text}", binary=True)
            if rc != 0:
                self.fail("claims", ident, f"{text} is not in {self.rev[:12]}")
            elif r.status != 200:
                self.fail("claims", ident, f"{target} answered {r.status}")
            elif hashlib.sha256(r.body).hexdigest() != hashlib.sha256(want).hexdigest():
                self.fail("claims", ident, f"{target} differs from {self.rev[:12]}:{text}")
        else:
            self.fail("claims", ident, f"kind {kind} needs a gh: target")

    def row_github(self, ident, repo, kind, text) -> None:
        if kind == "head":
            main = self.ls_remote(repo, "refs/heads/main").get("refs/heads/main")
            if text == "rev":
                want = self.rev
            else:
                rc, out = self.git("rev-parse", "HEAD", cwd=self.root / text)
                want = out.strip() if rc == 0 else None
            if main is None or want is None:
                self.fail("claims", ident, f"main of {repo} or the wanted commit is not readable")
            elif main != want:
                self.fail("claims", ident, f"{repo} main is {main[:12]}, want {want[:12]}")
        elif kind == "heads":
            got = sorted(r[len("refs/heads/"):] for r in self.ls_remote(repo, heads=True))
            want = sorted(x.strip() for x in text.split(",") if x.strip())
            if got != want:
                self.fail("claims", ident, f"{repo} branches are {got}, want {want}")
        elif kind == "about":
            r = self.get(GITHUB_API + repo)
            if r.status != 200:
                return self.fail("claims", ident, f"api.github.com answered {r.status}")
            desc = json.loads(r.text).get("description") or ""
            if text not in desc:
                self.fail("claims", ident, f"description of {repo} is {desc[:80]!r}, want it to contain {text!r}")
        else:
            self.fail("claims", ident, f"kind {kind} does not take a gh: target")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="live_check.py")
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--rev")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--claims", default=None, help="rows file (default scripts/live_claims.tsv)")
    ap.add_argument("--excludes", default=None, help="excludes file (default scripts/live_check_excludes.tsv)")
    a = ap.parse_args(argv)
    c = Checker(a.base, a.rev, ROOT)
    try:
        c.check_label()
        excl = c.excludes(Path(a.excludes) if a.excludes else ROOT / "scripts" / "live_check_excludes.tsv")
        c.check_files(excl)
        sitemap = c.sitemap_urls()
        c.check_sitemap(sitemap)
        c.check_claims(Path(a.claims) if a.claims else ROOT / "scripts" / "live_claims.tsv", sitemap)
    except CouldNotRun as e:
        print(f"live-check: could not run: {e}")
        return 2
    except (urllib.error.URLError, OSError) as e:
        print(f"live-check: could not run: {getattr(e, 'reason', e)}")
        return 2
    for line in c.failures:
        print(line)
    if c.failures:
        print(f"live-check: {len(c.failures)} failure(s)")
        return 1
    if not a.quiet:
        print(f"live-check: {c.counts['files']} files, {c.counts['urls']} sitemap urls, "
              f"{c.counts['rows']} rows at {c.rev[:12]}")
    print("live-check: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
