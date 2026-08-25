"""LAW-DEPLOY-LABEL-TRUE - the label is proved against the LIVE site, and the proof can go red.

WHAT THIS SUITE IS DEFENDING. `verify_live.sh` measures liveness: eight addresses and the codes
they must answer. Every one of those codes is answered just as well by last week's deployment, so
a publish that reported success and landed nowhere reads GREEN through the whole deploy script -
the founding shape of this project's own defect, inside the instrument meant to catch it. The stamp
closes it by putting a name in the upload and reading that name back off provek.dev.

THE ROUND TRIP IS THE POINT, AND IT IS WHY BOTH HALVES ARE IN ONE SCRIPT. The writer and the reader
must agree on one filename; a filename in two places would drift (L-2), and the drift would show up
as a check reading an address nobody writes - green forever, over nothing. So `test_the_round_trip`
below stamps a directory, SERVES THAT DIRECTORY, and verifies against it. NO ASSERTION IN THIS FILE
NAMES THE FILENAME - the round trip counts what was written rather than looking for a name, so if
the constant in the script changed, the tests would still pass and the drift would be impossible.
(This sentence is the only place the requirement is stated in prose; the first draft of it claimed
"nothing in this file names deploy-label.txt" while naming it, which is the same defect one level
up. Found by Fable.)

THE STUB IS ALSO THE POINT. A test that reached provek.dev would pass or fail on the state of a
deployment rather than on the logic of the script, and would go yellow-and-skipped on a host with
no route out - the exact shape (L-16) that lets a defect ship. Nothing here leaves loopback.
"""
from __future__ import annotations

import functools
import http.server
import os
import pathlib
import subprocess
import threading

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "deploy_stamp.sh"


class _Origin:
    """Serves a directory over loopback, or answers a fixed code for everything."""

    def __init__(self, directory: pathlib.Path | None, code: int | None = None) -> None:
        if directory is not None:
            handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                        directory=str(directory))
        else:
            class handler(http.server.BaseHTTPRequestHandler):  # noqa: N801
                def do_GET(self):  # noqa: N802
                    self.send_error(code)

                def log_message(self, *a):
                    pass

        self.server = http.server.HTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


def _run(*args: str) -> subprocess.CompletedProcess:
    # The propagation window in `verify` is real seconds. These tests assert the VERDICT -- that a
    # wrong label is refused -- and making each one sit through the production window turns a
    # fast suite into one people learn to skip, which is how gates die. The window is exercised
    # by its own test below; everywhere else it is collapsed.
    env = dict(os.environ)
    env.setdefault("DEPLOY_LABEL_TRIES", "2")
    env.setdefault("DEPLOY_LABEL_SLEEP_S", "0")
    return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True,
                          timeout=120, env=env)


def test_the_round_trip_confirms_the_deployment_that_is_live(tmp_path):
    """Stamp a build, serve it, read the name back. The two halves must agree without being told."""
    upload = tmp_path / "dist"
    upload.mkdir()
    stamped = _run("stamp", "dirty-b0038e327194", str(upload))
    assert stamped.returncode == 0, stamped.stderr
    # Asserted by COUNT and not by name: naming the file here would be the second copy of the
    # constant that this script exists to avoid having.
    written = list(upload.iterdir())
    assert len(written) == 1, written

    with _Origin(upload) as origin:
        done = _run("verify", "dirty-b0038e327194", origin.base)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "LABEL CONFIRMED" in done.stdout


def test_a_stale_deployment_is_red_and_names_both_labels(tmp_path):
    """THE CASE THE STAMP WAS WRITTEN FOR: the publish reported success and landed nowhere.

    Every address `verify_live.sh` reads answers correctly here - the old upload is a working site.
    Only the name distinguishes it, which is why the name is the measurement.
    """
    upload = tmp_path / "dist"
    upload.mkdir()
    _run("stamp", "0538a90", str(upload))          # what is actually live: last week's deploy
    with _Origin(upload) as origin:
        done = _run("verify", "ebe9230", origin.base)   # what this run believes it published
    assert done.returncode != 0
    assert "WRONG DEPLOYMENT IS LIVE" in done.stdout
    assert "0538a90" in done.stdout and "ebe9230" in done.stdout


def test_an_upload_with_no_label_at_all_is_red_and_is_not_called_a_mismatch(tmp_path):
    """A 404 means no labelled deployment was ever published here - a different fact from a stale
    one, and it sends the operator to a different place."""
    with _Origin(None, code=404) as origin:
        done = _run("verify", "0538a90", origin.base)
    assert done.returncode != 0
    assert "LABEL NOT CONFIRMED" in done.stdout
    assert "404" in done.stdout
    assert "landed nowhere" in done.stdout
    assert "WRONG DEPLOYMENT IS LIVE" not in done.stdout


def test_an_origin_that_cannot_be_reached_is_unreadable_and_says_so(tmp_path):
    """Invariant 1 at the last mile: "we could not ask" is not "the wrong thing is live".

    `curl -w '%{http_code}'` prints 000 when no exchange happened; read as a code that is not 200,
    a dead network would be reported as a bad deployment and the operator would go looking at
    Cloudflare for a fault on this host.
    """
    origin = _Origin(None, code=500)
    with origin:
        dead = origin.base           # bound, then shut down: a port nothing listens on
    done = _run("verify", "0538a90", dead)
    assert done.returncode != 0
    assert "UNREADABLE" in done.stdout
    assert "connection was refused" in done.stdout
    assert "WRONG DEPLOYMENT IS LIVE" not in done.stdout
    assert "LABEL NOT CONFIRMED" not in done.stdout


@pytest.mark.parametrize("args", [
    (),                        # no subcommand and no label
    ("verify",),               # a comparison with nothing to compare against
    ("stamp",),                # a stamp with nothing to write
    ("stamp", "0538a90"),      # a label with nowhere to put it
])
def test_a_check_that_cannot_run_refuses_instead_of_passing(args):
    """THE FAILURE MODE AN OPTIONAL CHECK WOULD HAVE: absent reading as satisfied.

    If a missing label exited 0, then `deploy.sh` dropping the argument - by an edit, a typo, or a
    variable that came back empty - would look exactly like a confirmed deployment, forever and
    silently. That is why the label is required rather than defaulted.
    """
    done = _run(*args)
    assert done.returncode != 0
    assert "REFUSED" in done.stderr


def test_the_stamp_refuses_a_directory_that_is_not_there(tmp_path):
    """Otherwise the upload goes out unlabelled and the verify below it fails for the wrong reason."""
    done = _run("stamp", "0538a90", str(tmp_path / "no-such-dist"))
    assert done.returncode != 0
    assert "REFUSED" in done.stderr


def test_a_broken_origin_is_not_reported_as_an_unlabelled_one():
    """A 5xx is a live origin in trouble; a 404 is an upload with no label. Different places to go.

    Both were one message until Fable pointed out that the 404 diagnosis - "the publish landed
    nowhere" - was being printed over a 503 as well, which sends the operator to Cloudflare's
    deployment list to look for something that is not the fault.
    """
    with _Origin(None, code=503) as origin:
        done = _run("verify", "0538a90", origin.base)
    assert done.returncode != 0
    assert "LABEL NOT CONFIRMED" in done.stdout
    assert "503" in done.stdout
    assert "unmeasured" in done.stdout
    assert "landed nowhere" not in done.stdout


def test_the_code_and_the_body_come_from_one_exchange():
    """The defect this replaced: two requests, and the second one's exit status never read.

    An origin that answers once and then stops serving is exactly the window that existed. The
    first version fetched the body here, then fetched the code from a dead socket, got `000`, and
    announced a verdict ABOUT THE SITE - the refusal of the instrument laundered into a finding,
    which is the failure the header of the script spends a paragraph forbidding.
    """
    served: list[str] = []

    class handler(http.server.BaseHTTPRequestHandler):  # noqa: N801
        def do_GET(self):  # noqa: N802
            served.append(self.path)
            body = b"0538a90\n"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        done = _run("verify", "0538a90", f"http://127.0.0.1:{server.server_address[1]}")
    finally:
        server.shutdown()
        server.server_close()

    assert done.returncode == 0, done.stdout + done.stderr
    assert len(served) == 1, f"the label was fetched {len(served)} times, not once: {served}"


def test_the_propagation_window_is_actually_used_and_its_size_is_stated(tmp_path):
    """A wrong label is refused only after the window, and the refusal says how long it waited.

    Measured 2026-08-25: `verify` read the old label, printed WRONG DEPLOYMENT IS LIVE, and the
    edge served the new one seconds later -- the deployment had been in Production the whole time.
    A false red costs what a false green costs: it teaches the next reader that this gate is noise.

    This keeps the window honest in both directions. Remove the retry and the refusal stops naming
    one, so this turns red. Widen it until a real mismatch is waited out forever, and the number
    it was widened to is printed in the failure where a person will see it.
    """
    upload = tmp_path / "dist"
    upload.mkdir()
    _run("stamp", "aaaaaaa", str(upload))
    with _Origin(upload) as origin:
        env = dict(os.environ, DEPLOY_LABEL_TRIES="3", DEPLOY_LABEL_SLEEP_S="0")
        r = subprocess.run(["bash", str(SCRIPT), "verify", "bbbbbbb", origin.base],
                           capture_output=True, text=True, timeout=120, env=env)
    assert r.returncode != 0, "a label that never matched was accepted"
    out = r.stdout + r.stderr
    assert "WRONG DEPLOYMENT IS LIVE" in out
    assert "Read 3 time(s)" in out, (
        "the refusal does not report THREE reads. It must report what it performed, not what "
        "was configured: written the other way, disabling the retry left this green. "
        f"edge catching up: {out[-300:]}")
