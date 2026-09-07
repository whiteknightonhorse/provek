#!/usr/bin/env python3
"""T-05 - fetch aipush's page->video map and write it where the build can read it without a
network (`web/public/data/shorts_map.json`).

WHY A SEPARATE STEP, NEVER PART OF THE BUILD ITSELF. `templates/emit.mjs`'s own header states the
rule this script would otherwise break: "no network is reached - a build that depends on a network
and a token this host happens to hold is not reproducible from a clone". The map lives outside the
repository (aipush's own public GitHub raw file) and changes over time as more shorts render, so it
cannot be a build-time fetch without making every future `npm run build` non-reproducible. This
script is the one place the network is touched; its output is a committed, ordinary data file the
build reads exactly the way it already reads `public/data/registry.json` and every passport.

THE SOURCE IS ANONYMOUS AND CREDENTIAL-FREE (ABI-5-3): a raw GitHub URL, no token, so any third
party can repeat this exact read and get the same answer we did.

TWO BLOCKS, NOT ONE, and the reasoning is the same as `scripts/watch_validation_registry.py`'s own
comment on that pattern: a transient failure (404 because aipush has not written a row yet, a
timeout, a malformed body mid-write) must not erase videos a PRIOR successful run already
validated. `measurement` holds the last fetch that actually parsed as a JSON object; `last_attempt`
holds what THIS run did, whatever that was. A run that fails leaves `measurement` exactly as it
was - never a zero standing in for "could not read it this time" (CLAUDE.md invariant 1).

VALIDATION, PER ENTRY, NEVER BY TRUSTING THE SHAPE. `not_measured` is not just for URLs the map has
not reached yet - a URL present in the map with a malformed `video_id` is *also* not a video id we
can publish, and the task's own instruction is explicit: never invent one. An entry that fails
validation is dropped from `videos`, named in `dropped`, and the page it belongs to reads `null`,
same as a URL the map has not reached yet.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "public" / "data" / "shorts_map.json"
RAW_URL = (
    "https://raw.githubusercontent.com/whiteknightonhorse/AIpush/flywheel/20260629/"
    "provek_shorts_map.json"
)
SITE = "https://provek.dev"

# The 8 pages this task closes (ADR-0011's six original templates plus the seventh admitted by
# T-77, plus the index) - read from the same manifest `templates/emit.mjs` treats as the canonical
# slug list, never a second hand-typed copy of it (L-2).
MANIFEST = ROOT / "templates" / "manifest.json"
EXPECTED_ROUTES = ["/build/"] + [
    f"/build/{slug}/"
    for slug in json.loads(MANIFEST.read_text(encoding="utf-8"))["templates"]
]
EXPECTED_URLS = [SITE + route for route in EXPECTED_ROUTES]

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def fetch(url: str = RAW_URL, timeout: int = 30) -> tuple[str, int | None, str | None]:
    """One anonymous read. Returns `(state, http_status, body)`.

    Same three-way split `src/transport/erc8004_deployment.py.fetch` uses: no client on this host,
    no answer at all (network down, timeout), or the source answered and the status was not 200 -
    which per this task's own instruction INCLUDES 404, because aipush writes the map
    incrementally and a 404 means "nothing published yet", not a defect on either side.
    """
    try:
        p = subprocess.run(
            ["curl", "-sS", "-w", "\n%{http_code}", "--max-time", str(timeout), url],
            capture_output=True, text=True, timeout=timeout + 10,
        )
    except FileNotFoundError:
        return "no_client", None, None
    except (OSError, subprocess.SubprocessError):
        return "no_answer", None, None
    raw = p.stdout.rsplit("\n", 1)
    if p.returncode != 0 or len(raw) != 2 or not raw[1].strip().isdigit():
        return "no_answer", None, None
    body, code = raw
    status = int(code.strip())
    if status != 200:
        return "source_answered_non_200", status, None
    return "ok", status, body


def validate(raw_map: dict) -> tuple[dict, list[str]]:
    """`(videos, dropped)` - `videos` keeps only entries this site will publish a video_id from;
    `dropped` names every URL that was in the map but did not qualify, so the reason is visible
    rather than a silent shrink."""
    videos: dict[str, dict] = {}
    dropped: list[str] = []
    for url, entry in raw_map.items():
        if not isinstance(entry, dict):
            dropped.append(url)
            continue
        video_id = entry.get("video_id")
        title = entry.get("title")
        if not isinstance(video_id, str) or not VIDEO_ID_RE.match(video_id):
            dropped.append(url)
            continue
        if not isinstance(title, str) or not title.strip():
            dropped.append(url)
            continue
        videos[url] = {"video_id": video_id, "title": title.strip()}
    return videos, dropped


def main() -> int:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    state, status, body = fetch()

    existing = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {
        "source_url": RAW_URL, "measurement": None, "last_attempt": None,
    }

    if state == "ok" and body is not None:
        try:
            raw_map = json.loads(body)
        except ValueError:
            state, status = "not_json", status
            raw_map = None
        else:
            if not isinstance(raw_map, dict):
                state, raw_map = "not_object", None

    if state == "ok" and body is not None and isinstance(raw_map, dict):
        videos, dropped = validate(raw_map)
        existing["measurement"] = {
            "fetched_at": now, "raw_entry_count": len(raw_map),
            "valid_entry_count": len(videos), "videos": videos, "dropped": dropped,
        }
        print(f"OK: {len(videos)} of {len(raw_map)} raw entries validated, {len(dropped)} dropped")
    else:
        print(f"NOT UPDATED: fetch state={state} status={status} - measurement left as it was "
              f"({'present' if existing['measurement'] else 'absent'})")

    existing["last_attempt"] = {"at": now, "state": state, "http_status": status}
    existing["source_url"] = RAW_URL

    have = set((existing.get("measurement") or {}).get("videos", {}))
    missing = [u for u in EXPECTED_URLS if u not in have]
    print(f"expected pages: {len(EXPECTED_URLS)}, have a video for: {len(have & set(EXPECTED_URLS))}, "
          f"waiting on: {missing}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(existing, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
