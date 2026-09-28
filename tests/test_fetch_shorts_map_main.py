"""T-HY-02 (REPO-hygiene-0928.ruling-1.md, code-scanning alert #80) - `main()` had no test of its
own before this file; `test_build_shorts_map_matches.py` reads the committed
`web/public/data/shorts_map.json` but never calls `main()`.

Both cases below exercise the branch alert #80 was raised against: a `fetch()` that does not
answer `("ok", 200, <body>)`. `raw_map` is a name the function only ever assigns inside the
`state == "ok" and body is not None` block, so a case where that block is skipped entirely - the
first one here, `body=None` - is exactly the path where CodeQL could not prove `raw_map` was bound
before the guard at the line that used to read `state == "ok" and body is not None and
isinstance(raw_map, dict)`. The second case enters the block, fails to parse, and falls out with
`raw_map` reset to `None` rather than never assigned - a different route to the same "not a dict"
outcome. Both must leave a pre-existing `measurement` exactly as it was (CLAUDE.md invariant 1): a
failed fetch is not the same fact as an empty one.
"""
from __future__ import annotations

import json

import scripts.fetch_shorts_map as fetch_shorts_map

SEEDED_MEASUREMENT = {
    "fetched_at": "2026-01-01T00:00:00Z",
    "raw_entry_count": 1,
    "valid_entry_count": 1,
    "videos": {"https://provek.dev/build/": {"video_id": "abcdefghijk", "title": "t"}},
    "dropped": [],
}


def _seed(out_path, measurement):
    out_path.write_text(
        json.dumps({
            "source_url": "https://example.invalid/map.json",
            "measurement": measurement,
            "last_attempt": {"at": "2025-12-31T00:00:00Z", "state": "ok", "http_status": 200},
        }),
        encoding="utf-8",
    )


def test_main_leaves_measurement_untouched_when_the_source_answers_non_200(monkeypatch, tmp_path):
    out = tmp_path / "shorts_map.json"
    _seed(out, SEEDED_MEASUREMENT)
    monkeypatch.setattr(fetch_shorts_map, "ROOT", tmp_path)
    monkeypatch.setattr(fetch_shorts_map, "OUT", out)
    monkeypatch.setattr(fetch_shorts_map, "fetch", lambda: ("source_answered_non_200", 503, None))

    assert fetch_shorts_map.main() == 0

    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["measurement"] == SEEDED_MEASUREMENT
    assert written["last_attempt"]["state"] == "source_answered_non_200"
    assert written["last_attempt"]["http_status"] == 503


def test_main_leaves_measurement_untouched_when_the_body_is_not_json(monkeypatch, tmp_path):
    out = tmp_path / "shorts_map.json"
    _seed(out, SEEDED_MEASUREMENT)
    monkeypatch.setattr(fetch_shorts_map, "ROOT", tmp_path)
    monkeypatch.setattr(fetch_shorts_map, "OUT", out)
    monkeypatch.setattr(fetch_shorts_map, "fetch", lambda: ("ok", 200, b"not json"))

    assert fetch_shorts_map.main() == 0

    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["measurement"] == SEEDED_MEASUREMENT
    assert written["last_attempt"]["state"] == "not_json"
    assert written["last_attempt"]["http_status"] == 200
