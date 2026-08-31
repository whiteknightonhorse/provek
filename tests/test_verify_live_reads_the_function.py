"""T-H1 - the deploy check, proved able to go red on a dead intake.

WHAT THIS IS FOR. `scripts/verify_live.sh` exists because the previous live check read five static
addresses and called that a confirmed deployment, while `GET https://provek.dev/api/apply` answered
404 through every one of those confirmations - the Pages Function was never published, and the form
on `/apply/` invited a submission that could not succeed on any input. A check that cannot go red
over that is not a check, so this suite drives the script against a stub origin and proves each of
the three answers it must be able to give:

    405 -> green            the Function is published and routed
    404 -> red, NAMED       static assets only, which is the defect T-H1 found
    no origin -> UNREADABLE not a code, not a pass, and not confused with either of the above

THE STUB IS THE POINT. A test that reached provek.dev would pass or fail on the state of a
deployment rather than on the logic of the script, and would go yellow-and-skipped on a host with
no route out - which is exactly the shape (L-16) that let the defect ship. Nothing here touches the
network beyond loopback, so it is armed in CI, in a clone, and on an aeroplane.
"""
from __future__ import annotations

import http.server
import pathlib
import re
import subprocess
import threading

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "verify_live.sh"


def _checks_from_script() -> dict[str, int]:
    """The address list, READ OUT OF THE SCRIPT instead of copied beside it.

    This was a second hand-maintained copy of `CHECKS`, and it drifted the first time an address
    was added: T-C4 published the note surface, put the two routes in the script, and every test in
    this file went on describing the six-address world it had been written against. The suite was
    green about a script it no longer matched, which is the state where a live check stops being
    the thing the suite says it is.

    L-20's rule is that the finding in such a divergence is the ABSENCE OF THE COMPARISON and not
    the value that differed - patching the literal here would have returned the file to the day
    before the drift and left the mechanism standing. So the comparison is now the definition:
    there is one list, in the script, and a route added there arrives in this fixture whether or
    not anybody remembers this file exists.
    """
    body = SCRIPT.read_text(encoding="utf-8")
    m = re.search(r"^CHECKS=\(\n(.*?)^\)", body, re.S | re.M)
    if not m:
        raise AssertionError(f"{SCRIPT.name}: no CHECKS=( ... ) array to read")
    out: dict[str, int] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        path, _, code = line.strip('"').rpartition(":")
        out[path] = int(code)
    # A PARSER THAT RETURNS NOTHING MUST NOT READ AS "every address is fine". An empty dict would
    # make every assertion below vacuous and the whole suite would pass by measuring no addresses
    # at all - invariant 1, in the fixture rather than in a counter.
    if not out:
        raise AssertionError(f"{SCRIPT.name}: CHECKS parsed to zero addresses")
    return out


HEALTHY = _checks_from_script()


class _Origin:
    """A stub origin that answers a fixed code per path and REMEMBERS THE METHOD IT WAS ASKED.

    The method log is not decoration. `onRequestPost` on the real endpoint writes a durable KV
    record and pages the operator; if this script ever probed with a POST, every deployment would
    manufacture an applicant nobody applied for. That is asserted below rather than trusted to the
    reading of a `-w` flag."""

    def __init__(self, codes: dict[str, int]) -> None:
        self.codes = codes
        self.methods: list[str] = []
        origin = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def _answer(self) -> None:
                origin.methods.append(self.command)
                # An unlisted path is 404 - the same answer a real static-only deployment gives to
                # /api/apply, which is what makes the 404 case below a faithful stand-in.
                self.send_response(origin.codes.get(self.path, 404))
                self.end_headers()

            do_GET = _answer
            do_POST = _answer
            do_HEAD = _answer

            def log_message(self, *args: object) -> None:
                """Silence. pytest capturing the stub's access log tells the reader nothing."""

        self.server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.server.server_port}"

    def __enter__(self) -> _Origin:
        self.thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def _run(base: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(SCRIPT), base], capture_output=True, text=True, timeout=120)


def test_a_published_function_reads_green():
    with _Origin(dict(HEALTHY)) as origin:
        run = _run(origin.base)
    assert run.returncode == 0, run.stdout + run.stderr
    assert "LIVE READING GREEN" in run.stdout


def test_the_probe_never_writes():
    """GET and nothing else. A POST would be a health check that creates an intake record."""
    with _Origin(dict(HEALTHY)) as origin:
        _run(origin.base)
        seen = set(origin.methods)
    assert seen == {"GET"}, f"the live check used {sorted(seen)} - only GET is effect-free here"


def test_a_static_only_deployment_reads_RED_and_is_named():
    """THE ONE THIS FILE WAS WRITTEN FOR. Five 200s and a 404 on the endpoint: the exact state
    provek.dev was in on 2026-08-21 and 2026-08-24, under the words DEPLOY CONFIRMED."""
    codes = dict(HEALTHY)
    codes["/api/apply"] = 404
    with _Origin(codes) as origin:
        run = _run(origin.base)
    assert run.returncode != 0, "a dead intake passed the deploy check - the T-H1 defect, restored"
    assert "/api/apply" in run.stdout
    assert "NOT published" in run.stdout, "red is not enough; the operator must be told what 404 means"


def test_a_broken_page_still_reads_RED():
    """The five static addresses did not stop being checked when the sixth was added."""
    codes = dict(HEALTHY)
    codes["/registry/"] = 500
    with _Origin(codes) as origin:
        run = _run(origin.base)
    assert run.returncode != 0
    assert "/registry/" in run.stdout


def test_an_unreachable_origin_is_UNREADABLE_and_not_a_code():
    """Invariant 1 in its operational form. `curl -w '%{http_code}'` prints `000` when no HTTP
    exchange happened; read as a code that is merely "not 200", indistinguishable from a site that
    answered badly. The two send the operator to different places - one to Cloudflare, one to this
    host's own network - so they may not collapse into one line."""
    with _Origin(dict(HEALTHY)) as origin:
        dead = origin.base  # bound, then torn down on exit: nothing is listening on this port now
    run = _run(dead)
    assert run.returncode != 0, "an address we could not read must never pass"
    assert "UNREADABLE" in run.stdout
    assert "connection was refused" in run.stdout, "a curl exit number is not a reason (L-23)"
    # THE SEARCH IS THE ADDRESS LINES, NOT THE WHOLE TRANSCRIPT, and the narrowing is a bug fix
    # rather than a convenience. The banner echoes the base URL, and the stub binds an ephemeral
    # port: roughly 55 of the ~28000 ports in this host's range contain the digits `000`, so
    # `assert "000" not in run.stdout` failed about one run in five hundred while the script was
    # behaving perfectly - a flake in the test written to prove that the instrument's refusal is
    # never dressed up as a measurement, caused by reading something that was not a measurement as
    # one. Found by Fable.
    addresses = [ln for ln in run.stdout.splitlines() if ln.startswith("  /")]
    assert addresses, "the run printed no address lines at all"
    assert not any("000" in ln for ln in addresses), \
        "the refusal of the instrument was reported as an HTTP code"


@pytest.mark.parametrize("path", sorted(HEALTHY))
def test_every_address_is_actually_visited(path: str):
    """A list the script carries but never walks would pass all of the above. Break one address at
    a time and require the run to notice that one."""
    codes = dict(HEALTHY)
    codes[path] = 418
    with _Origin(codes) as origin:
        run = _run(origin.base)
    assert run.returncode != 0, f"{path} is in the list and is not read"
    assert "418" in run.stdout


# THE FLOOR UNDER THE DERIVED LIST.
#
# Reading `HEALTHY` out of the script (above) ended the drift between two copies, and on its own it
# would have bought that at a price nobody stated: a derived fixture shrinks with its source. Delete
# an address from `CHECKS` and `HEALTHY` loses it too, every assertion in this file goes on passing,
# and the deploy gate quietly reads less of the site than it did the day before - the same silence
# that let `/api/apply` answer 404 through four confirmed deployments.
#
# This is a FLOOR and not a second mirror of the list, and the difference is what keeps it from
# being the drift again: adding an address does not touch it, so it never goes stale on growth. It
# fires in one direction only, when something load-bearing stops being read at all.
#
# IT COVERED HALF THE LIST ON ITS FIRST DRAFT, and the half it left out was the worse one. Four
# addresses were pinned - the two note routes, `/api/apply` and `/` - so `/apply/`, `/registry/`,
# `/method/` and `/phase-2/` could still be deleted from the script with the whole suite green.
# `/apply/` is the page carrying the intake form, which is the entire reason `/api/apply` is
# checked at all: the endpoint was pinned and the page a person actually visits to reach it was
# not. Found by Fable, refuting the change that introduced the floor.
#
# Every address the script checks is pinned now. That is not the drifting copy this file started
# with, because the direction is what matters: an address ADDED to the script needs no edit here
# and cannot make this stale, while an address REMOVED must be argued for in this dict. Deleting
# one from a deploy gate should cost somebody a sentence.
REQUIRED = {
    "/": 200,                                            # the origin talks to us at all
    "/apply/": 200,                                      # the page the intake form lives on
    "/registry/": 200,                                   # the product's front door
    "/method/": 200,                                     # the methodology the verdicts cite
    "/phase-2/": 200,                                    # specified and not built, and says so
    "/api/apply": 405,                                   # T-H1: the half of the site that is code
    "/method/notes/": 200,                               # T-C4: the note index
    "/method/notes/not-measured-is-not-zero/": 200,      # T-C4: the first published capture
    "/badge/git_whiteknightonhorse_provek.svg": 200,     # task 7: the embeddable badge Function
    "/p/git_whiteknightonhorse_provek/brief": 200,       # task 7: the short client-facing page
}


def test_the_address_list_cannot_silently_shrink():
    """An address removed from the script is a smaller deploy gate, and must not be a green suite."""
    missing = sorted(REQUIRED.keys() - HEALTHY.keys())
    assert not missing, (
        f"{SCRIPT.name} no longer checks {missing}. Removing an address shrinks what a "
        f"'DEPLOY CONFIRMED' covers; if that is intended, this floor is the place to argue it."
    )


def test_the_floor_pins_the_code_and_not_only_the_path():
    """`/api/apply` present but expected to answer 200 would be the T-H1 defect with the address
    still in the list - a static 404 page answering 200 is exactly what it looked like."""
    # `HEALTHY.get(p)` and not `HEALTHY[p]`: a path absent from the script is the test above's
    # finding, and indexing it here raised KeyError instead - an ERROR where an assertion belongs.
    # A crash and a failed assertion are not the same report, and the crash arrived with a stack
    # trace about a dict rather than a sentence about a deploy gate.
    wrong = {p: (HEALTHY.get(p), c) for p, c in REQUIRED.items()
             if p in HEALTHY and HEALTHY[p] != c}
    assert not wrong, f"{SCRIPT.name} expects the wrong code for {wrong} (got, wanted)"
