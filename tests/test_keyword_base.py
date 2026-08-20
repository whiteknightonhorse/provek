"""T-C3 - the keyword base admits no key without a source, and no zero without a measurement.

WHAT THIS GUARDS. `seo/keywords.csv` is a capture, not a list somebody typed. Two ways it could
quietly stop being one:

  1. a row arrives with no source, or with a source that is not in the manifest - the base becomes
     an assertion, and this project's whole subject is claims that outrun their artefact;
  2. an unmeasured demand is written as `0`. Zero impressions and "the instrument was not asked"
     are different states of the world, and one field holding both is the defect the operator's
     systems have paid for seven times (project law L-1, specification 2.9).

The third guard is the one L-10 bought: a source whose CONTROL came back blind may contribute no
keys and no zeros. `bing_serp_related` is exactly that case - the result page answers HTTP 200 and
carries organic results, but yields no related-search items to our reader, so its emptiness is a
statement about the client rather than about Bing.

THE RED RUN IS KEPT: `evidence/RED-004-keyword-source.txt`.
"""
from __future__ import annotations

import csv
import json
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEO = ROOT / "seo"
KEYS_CSV = SEO / "keywords.csv"
REJECTS_CSV = SEO / "keywords_rejected.csv"
MANIFEST = SEO / "sources.json"
DOC = SEO / "KEYWORD_BASE.md"

DEMAND_STATES = {"measured", "nothing_qualified", "check_did_not_run", "unreadable"}
SOURCE_STATES = {"ok", "nothing_qualified", "check_did_not_run", "unreadable",
                 "api_error", "transport_error", "unparseable", "not_configured"}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MIN_SOURCES_WITH_KEYS = 2
"""Every per-row assertion below is vacuously true on an empty file. A base that yielded keys from
one source only is a capture that half failed, and it must not pass silently."""


def rows(path: pathlib.Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="module")
def keys() -> list[dict]:
    return rows(KEYS_CSV)


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_the_base_exists_and_is_not_empty(keys, manifest):
    assert KEYS_CSV.exists() and REJECTS_CSV.exists() and MANIFEST.exists() and DOC.exists()
    assert keys, "the keyword base is EMPTY - every row-level check below would pass vacuously"
    contributing = {s for s, v in manifest["sources"].items() if v["keys_admitted"]}
    assert len(contributing) >= MIN_SOURCES_WITH_KEYS, (
        f"only {sorted(contributing)} yielded keys; a base standing on one source is a capture "
        f"that half failed")


def test_no_key_without_a_source(keys, manifest):
    """The task's own acceptance criterion, as a machine check."""
    known = set(manifest["sources"])
    for i, r in enumerate(keys, 2):
        assert r["source_id"].strip(), f"row {i}: key {r['key']!r} has NO source"
        assert r["source_id"] in known, f"row {i}: source {r['source_id']!r} is not in the manifest"
        assert r["source_locator"].strip(), (
            f"row {i}: key {r['key']!r} names a source but no address inside it")
        assert ISO_DATE.match(r["captured_at"]), f"row {i}: capture date {r['captured_at']!r}"


def test_demand_never_confuses_zero_with_unmeasured(keys):
    """LAW-NOT-MEASURED, applied to this artefact.

    `measured` carries a positive number. Every other state carries an EMPTY cell - never `0`,
    which would read as measured demand of zero."""
    for i, r in enumerate(keys, 2):
        state = r["demand_state"]
        assert state in DEMAND_STATES, f"row {i}: unknown demand state {state!r}"
        exact, broad = r["impressions_exact"], r["impressions_broad"]
        if state == "measured":
            assert exact.isdigit() and int(exact) > 0, (
                f"row {i}: {r['key']!r} is `measured` with impressions {exact!r} - a measured "
                f"zero is not a measurement, it is `nothing_qualified`")
            assert broad.isdigit(), f"row {i}: broad impressions {broad!r}"
        else:
            assert exact == "" and broad == "", (
                f"row {i}: {r['key']!r} is `{state}` yet carries impressions {exact!r}/{broad!r} - "
                f"an unmeasured quantity must be absent, not zero")
        assert (r["demand_source_id"] == "") == (state == "check_did_not_run"), (
            f"row {i}: `{state}` with demand source {r['demand_source_id']!r} - a reading names "
            f"the instrument that took it, and only an unrun check has none")


def test_keys_are_normalised_and_unique(keys):
    seen: set[str] = set()
    for i, r in enumerate(keys, 2):
        k = r["key"]
        assert k == k.strip().lower() and "  " not in k, f"row {i}: {k!r} is not normalised"
        assert k.isascii(), f"row {i}: {k!r} is not ASCII; the repository surface is English-only"
        assert k not in seen, f"row {i}: {k!r} appears twice"
        seen.add(k)


def test_a_blind_source_contributes_nothing(manifest):
    """L-10: a source whose control could not see presence may not report absence either.

    TWO GUARDS, ON PURPOSE. The first reads the control's verdict, which is prose - reword it and
    the guard disarms itself. The second is structural and cannot be reworded away: a source that
    is not `ok` contributed no keys, and a source that contributed keys is `ok`."""
    for sid, s in manifest["sources"].items():
        assert s["state"] in SOURCE_STATES, f"{sid}: unknown state {s['state']!r}"
        if s["control"]["verdict"].startswith("BLIND"):
            assert s["state"] in {"unreadable", "check_did_not_run"}, (
                f"{sid}: control is blind, so its state may not be a finding about the world")
            assert s["keys_admitted"] == 0, (
                f"{sid}: control is blind yet {s['keys_admitted']} keys were admitted from it")
        assert (s["state"] == "ok") or s["keys_admitted"] == 0, (
            f"{sid}: state is {s['state']!r} and yet it contributed {s['keys_admitted']} keys")
        # THE THIRD GUARD ties both of the above to the control's own READING rather than to
        # anybody's summary of it. Without it, a source whose control returned nothing could still
        # carry the verdict "instrument sees presence", state `ok`, and a thousand keys.
        returned = s["control"].get("returned")
        if isinstance(returned, int) and returned == 0:
            assert s["state"] != "ok" and s["keys_admitted"] == 0, (
                f"{sid}: the control returned nothing, so this source may not be `ok` and may not "
                f"have contributed {s['keys_admitted']} keys")


def test_a_duplicate_reject_names_a_key_that_is_in_the_base(keys, manifest):
    """`duplicate` means "already in the base". When the row it duplicated is later dropped by
    another rule, that sentence stops being true and the reject file lies about its own rule.

    Twenty rows did exactly that: their twins left the base as `false_friend` while the shadows
    stayed labelled `duplicate`. Found by refutation, not by this suite - which is why it is here."""
    present = {r["key"] for r in keys}
    orphans = [r["key_escaped"] for r in rows(REJECTS_CSV)
               if r["rule"] == "duplicate" and r["key_escaped"] not in present]
    assert not orphans, (
        f"{len(orphans)} rows are rejected as duplicates of a key the base does not hold: "
        f"{orphans[:5]}")


def test_every_reading_names_an_instrument_the_manifest_knows(keys, manifest):
    known = set(manifest["sources"])
    for i, r in enumerate(keys, 2):
        if r["demand_source_id"]:
            assert r["demand_source_id"] in known, (
                f"row {i}: reading attributed to {r['demand_source_id']!r}, which is not a source")


def test_rejections_are_counted_by_rule(manifest):
    """"How many were dropped and by which rule" is part of the artefact, not of a chat message."""
    rejects = rows(REJECTS_CSV)
    allowed = set(manifest["rule_order"])
    for i, r in enumerate(rejects, 2):
        assert r["rule"] in allowed, f"reject row {i}: unknown rule {r['rule']!r}"
        assert r["source_id"].strip(), f"reject row {i}: dropped key with no source"
        assert r["key_escaped"].isascii(), (
            f"reject row {i}: non-ASCII reached a tracked file; rejects are stored escaped so "
            f"that a non-English key stays auditable without failing the language ratchet")
    by_rule: dict[str, int] = {}
    for r in rejects:
        by_rule[r["rule"]] = by_rule.get(r["rule"], 0) + 1
    assert by_rule == manifest["rejected_by_rule"], "the manifest's rule counts are not the file's"
    assert manifest["totals"]["rejected"] == len(rejects)


def test_the_manifest_counts_what_the_files_hold(keys, manifest):
    assert manifest["totals"]["keys"] == len(keys)
    demand: dict[str, int] = {}
    from_rows: dict[str, int] = {}
    for r in keys:
        from_rows[r["source_id"]] = from_rows.get(r["source_id"], 0) + 1
        demand[r["demand_state"]] = demand.get(r["demand_state"], 0) + 1
    assert demand == manifest["demand_states"], (
        "the manifest's demand tally is not the file's - and the demand tally is where an "
        "`unreadable` row would be quietly promoted to a measured one")
    for r in keys:
        for other in filter(None, r["corroborated_by"].split(";")):
            assert other in manifest["sources"], f"{r['key']!r}: corroborator {other!r} is unknown"
    for sid, s in manifest["sources"].items():
        assert s["keys_admitted"] == from_rows.get(sid, 0), (
            f"{sid}: manifest says {s['keys_admitted']} keys, the file holds {from_rows.get(sid, 0)}")
    totals = manifest["totals"]
    assert totals["sources_configured"] == len(manifest["sources"])
    assert totals["sources_that_yielded_keys"] == sum(1 for v in from_rows.values() if v)
    assert totals["keys_corroborated_by_a_second_source"] == sum(
        1 for r in keys if r["corroborated_by"]), (
        "a total nobody recomputes is a number that drifts on the next pass")


def test_the_late_rules_account_for_every_row_they_hold(manifest):
    """The pass that applies a rule written after the capture must add up.

    A rule invented late can only be trusted if its whole population is accounted for: rows it took
    out of the base, plus rejects it re-judged, and nothing else — those rules did not exist while
    the capture ran, so no row can carry one for any other reason. This is also the regression
    guard the accumulation fix did not have: a pass that overwrites its own record instead of
    adding to it fails here, where before it stayed green."""
    p = manifest["refilter_pass"]
    by_rule: dict[str, int] = {}
    for r in rows(REJECTS_CSV):
        by_rule[r["rule"]] = by_rule.get(r["rule"], 0) + 1
    for rule in p["rules_added_after_the_capture"]:
        expected = (p["rows_moved_out_of_the_base"].get(rule, 0)
                    + p["duplicate_rejects_reclassified"].get(rule, 0))
        assert by_rule.get(rule, 0) == expected, (
            f"{rule}: the reject file holds {by_rule.get(rule, 0)} rows and the pass claims "
            f"{expected} — a rule that cannot account for its own population is not a rule")


def test_a_renamed_key_kept_no_reading_from_its_old_self(keys, manifest):
    """A reading belongs to the string it was taken for. Normalisation that changes the string
    therefore invalidates the reading — the row must fall to `check_did_not_run`, which is a state,
    not a blank."""
    renamed = {r["after"] for r in manifest["refilter_pass"]["keys_renamed_by_normalisation"]}
    for r in keys:
        if r["key"] in renamed:
            assert r["demand_state"] == "check_did_not_run" and not r["demand_source_id"], (
                f"{r['key']!r} was renamed and still carries a reading taken for another string")


MEASURED_BLOCK = re.compile(r"<!-- MEASURED:BEGIN -->\s*```json\s*(.*?)```\s*<!-- MEASURED:END -->",
                            re.S)


def test_the_document_prints_the_numbers_the_files_hold(manifest):
    """L-3, one step upstream: a document that quotes a measurement drifts from it silently.

    The prose in `KEYWORD_BASE.md` is for people; this block is the same numbers for a machine, and
    it must equal the manifest exactly."""
    m = MEASURED_BLOCK.search(DOC.read_text(encoding="utf-8"))
    assert m, "KEYWORD_BASE.md carries no MEASURED block - its numbers answer to nothing"
    printed = json.loads(m.group(1))
    for field in ("totals", "demand_states", "rejected_by_rule"):
        assert printed[field] == manifest[field], (
            f"{field}: the document says {printed[field]} and the capture says {manifest[field]}")
