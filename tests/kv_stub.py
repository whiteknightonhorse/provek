#!/usr/bin/env python3
"""A stand-in for `npx wrangler kv ...`, so the operator's sweep can be RUN rather than read.

WHY IT EXISTS. The sweep in `docs/INTAKE_OPERATIONS.md` is the only instrument that finds a
submission nobody has followed up, and until T-A2-3 nothing in this repository could make it fail.
A gate that greps the document for `delivered` would pass over a filter that matches the wrong
thing, prints every state under one label, or reports a refused read as a clean record - which are
exactly the defects that gate is filed under. So the block is extracted from the document, put on a
PATH in front of this file under the name `npx`, and its output is asserted
(`tests/test_intake_sweep_distinguishes_its_states.py`).

WHAT IT IS NOT. It is not `wrangler`, and it is not Workers KV. It answers the two subcommands the
sweep issues, in the shapes Cloudflare's own output has, and it can refuse - which is the half a
live namespace could not be asked to perform on demand. Whether the real `wrangler` refuses in
these shapes is `not_measured` here and is named in the gate's docstring rather than assumed.

THE FIXTURE, read from `$KV_STUB_FIXTURE`:

    {"list": "refuse" | "malformed" | null,
     "keys": {"<key>": {"value": "<stored bytes>"} | {"refuse": true}},
     "log":  "<path each invocation is appended to>"}

`refuse` is exit 1 with a message on stderr, which is what a CLI failure looks like to a shell.
An invocation this file does not recognise exits 64 rather than 0: a stub that silently succeeds on
a command it did not understand would make the sweep look well behaved for calls it never served.
"""
from __future__ import annotations

import json
import os
import sys

FIXTURE = os.environ.get("KV_STUB_FIXTURE")


def main(argv: list[str]) -> int:
    if not FIXTURE:
        sys.stderr.write("kv_stub: KV_STUB_FIXTURE is not set - this stub has nothing to answer "
                         "from, and answering anything would be an invention\n")
        return 64
    with open(FIXTURE, encoding="utf-8") as fh:
        fixture = json.load(fh)

    log = fixture.get("log")
    if log:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(" ".join(argv) + "\n")

    # `npx wrangler kv key list|get ...`
    if argv[:4] != ["wrangler", "kv", "key", "list"] and argv[:4] != ["wrangler", "kv", "key", "get"]:
        sys.stderr.write(f"kv_stub: unrecognised invocation {argv!r}\n")
        return 64
    verb = argv[3]

    if verb == "list":
        state = fixture.get("list")
        if state == "refuse":
            sys.stderr.write("kv_stub: the namespace could not be listed\n")
            return 1
        if state == "malformed":
            sys.stdout.write("<html>not json at all</html>\n")
            return 0
        sys.stdout.write(json.dumps([{"name": k} for k in fixture.get("keys", {})]) + "\n")
        return 0

    key = argv[4] if len(argv) > 4 else ""
    entry = fixture.get("keys", {}).get(key)
    if entry is None:
        sys.stderr.write(f"kv_stub: no such key {key!r}\n")
        return 1
    if entry.get("refuse"):
        sys.stderr.write(f"kv_stub: the read of {key!r} was refused\n")
        return 1
    sys.stdout.write(entry["value"] + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
