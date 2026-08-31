"""The agent-discovery maps (RFC 9727 api-catalog, llms.txt, llms-full.txt, and the ARD manifest
at /.well-known/ai-catalog.json) must not drift from each other, from the checked-in static files,
or from the registry/passport data they describe.

WHY THIS EXISTS. The task's own warning: "three copies of one map inevitably drift". There are, in
fact, three things that could each independently claim to know the world here - the registry, the
passports directory, and the published maps - and nothing before this file checked that they
agreed. `web/discovery.mjs` is the one generator; these tests check its OUTPUT, not that it exists,
because a generator nobody runs and a hand-edited file downstream of it look identical to a test
that only checks source code.

llms-full.txt is a second RENDER of the same `entries` input llms.txt is built from, not a second
copy of the map - so it is covered by the SAME agreement tests, not a parallel set. The ARD
manifest is a third render of the same input; it gets its own drift/shape tests below because its
own format rules (exactly one of url/data, 2-5 representativeQueries, no company-level autonomy
phrasing) have no equivalent in the other two maps.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
DISCOVERY = WEB / "discovery.mjs"
DATA_DIR = WEB / "public" / "data"
API_CATALOG = WEB / "public" / ".well-known" / "api-catalog"
LLMS_TXT = WEB / "public" / "llms.txt"
LLMS_FULL_TXT = WEB / "public" / "llms-full.txt"
AI_CATALOG = WEB / "public" / ".well-known" / "ai-catalog.json"
SITE = "https://provek.dev"


def _run_discovery(data_dir: pathlib.Path) -> dict:
    """Runs the real generator against `data_dir` and returns its parsed report.

    Deliberately NOT the full `npm run build` (vite + tsc + ssr): this only needs the registry and
    the passports directory, and paying for the whole site build on every test run would make this
    suite the kind of check that gets skipped rather than run.
    """
    result = subprocess.run(
        ["node", str(DISCOVERY), str(data_dir), SITE],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"discovery.mjs failed: {result.stderr}"
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def live_report() -> dict:
    return _run_discovery(DATA_DIR)


def test_the_generator_runs_at_all():
    assert DISCOVERY.is_file(), "web/discovery.mjs is missing"


def test_registry_and_passports_directory_agree_on_which_subjects_exist(live_report):
    """The floor under everything else: if these two disagree, no map built from either one can be
    trusted, and this must be the failure that is reported - not a confusing mismatch three steps
    downstream in the catalog or llms.txt."""
    assert live_report["registrySubjectIds"], "the registry read as having zero subjects"
    assert live_report["registrySubjectIds"] == live_report["passportIds"], (
        "registry.json and the passports/ directory disagree on what exists: "
        f"only in registry: {sorted(set(live_report['registrySubjectIds']) - set(live_report['passportIds']))}, "
        f"only on disk: {sorted(set(live_report['passportIds']) - set(live_report['registrySubjectIds']))}")


def _catalog_passport_slugs(catalog: dict) -> set[str]:
    prefix, suffix = f"{SITE}/data/passports/", ".json"
    return {
        item["href"][len(prefix):-len(suffix)]
        for item in catalog["linkset"][0]["item"]
        if item["href"].startswith(prefix) and item["href"].endswith(suffix)
    }


_LLMS_PASSPORT_LINK = re.compile(re.escape(f"({SITE}/data/passports/") + r"([^)]+)\.json\)")


def _llms_txt_passport_slugs(llms_txt: str) -> set[str]:
    return set(_LLMS_PASSPORT_LINK.findall(llms_txt))


_AI_CATALOG_PASSPORT_ID = re.compile(r"^urn:air:provek\.dev:passport:(.+)$")


def _ai_catalog_passport_slugs(catalog: dict) -> set[str]:
    slugs = set()
    for entry in catalog["entries"]:
        m = _AI_CATALOG_PASSPORT_ID.match(entry["identifier"])
        if m:
            slugs.add(m.group(1))
    return slugs


def test_api_catalog_lists_exactly_the_served_passports(live_report):
    got = _catalog_passport_slugs(live_report["apiCatalog"])
    want = set(live_report["passportIds"])
    assert got == want, f"api-catalog passport links do not match the served passports: {got ^ want}"


def test_llms_txt_lists_exactly_the_served_passports(live_report):
    got = _llms_txt_passport_slugs(live_report["llmsTxt"])
    want = set(live_report["passportIds"])
    assert got == want, f"llms.txt passport links do not match the served passports: {got ^ want}"


def test_llms_full_txt_lists_exactly_the_served_passports(live_report):
    """llms-full.txt is llms.txt plus the catalog appended - both halves must still name exactly
    the passports actually served, not a set frozen at whatever the concatenation was written
    against."""
    got = _llms_txt_passport_slugs(live_report["llmsFullTxt"])
    want = set(live_report["passportIds"])
    assert got == want, f"llms-full.txt passport links do not match the served passports: {got ^ want}"


def test_ai_catalog_lists_exactly_the_served_passports(live_report):
    got = _ai_catalog_passport_slugs(live_report["aiCatalog"])
    want = set(live_report["passportIds"])
    assert got == want, f"ai-catalog.json passport entries do not match the served passports: {got ^ want}"


def test_api_catalog_and_llms_txt_agree_with_each_other(live_report):
    """The two maps are built from the same `entries` array in the same function call - this is
    the assertion that would catch it if a future edit special-cased one map and not the other."""
    a = _catalog_passport_slugs(live_report["apiCatalog"])
    b = _llms_txt_passport_slugs(live_report["llmsTxt"])
    assert a == b, f"api-catalog and llms.txt disagree on which passports exist: {a ^ b}"


def test_all_four_maps_agree_on_which_passports_exist(live_report):
    """api-catalog, llms.txt, llms-full.txt, and ai-catalog.json are four renders of one `entries`
    array from one function call each - this is the assertion that would catch a future edit that
    special-cased one of the four and not the others."""
    a = _catalog_passport_slugs(live_report["apiCatalog"])
    b = _llms_txt_passport_slugs(live_report["llmsTxt"])
    c = _llms_txt_passport_slugs(live_report["llmsFullTxt"])
    d = _ai_catalog_passport_slugs(live_report["aiCatalog"])
    assert a == b == c == d, (
        "the four discovery maps disagree on which passports exist: "
        f"api-catalog={a}, llms.txt={b}, llms-full.txt={c}, ai-catalog.json={d}"
    )


def test_api_catalog_names_only_resources_that_exist():
    """No invented capability. The catalog may name /data/registry.json, a passport, /api/apply and
    /sitemap.xml - and nothing else - because a discovery map claiming a resource a third party
    cannot fetch is the exact defect this project marks other subjects down for."""
    catalog = json.loads(API_CATALOG.read_text(encoding="utf-8"))
    hrefs = {item["href"] for item in catalog["linkset"][0]["item"]}
    allowed_exact = {f"{SITE}/data/registry.json", f"{SITE}/api/apply", f"{SITE}/sitemap.xml"}
    passport_prefix = f"{SITE}/data/passports/"
    stray = [h for h in hrefs if h not in allowed_exact and not h.startswith(passport_prefix)]
    assert not stray, f"api-catalog names a resource outside the allowed set: {stray}"


def test_ai_catalog_names_only_resources_that_exist():
    """Same no-invented-capability rule as the RFC 9727 catalog, applied to the ARD manifest: an
    entry's `url` may point at the registry, a passport, or /api/apply - nothing else."""
    catalog = json.loads(AI_CATALOG.read_text(encoding="utf-8"))
    urls = {entry["url"] for entry in catalog["entries"]}
    allowed_exact = {f"{SITE}/data/registry.json", f"{SITE}/api/apply"}
    passport_prefix = f"{SITE}/data/passports/"
    stray = [u for u in urls if u not in allowed_exact and not u.startswith(passport_prefix)]
    assert not stray, f"ai-catalog.json names a resource outside the allowed set: {stray}"


def test_ai_catalog_entries_carry_url_never_data():
    """ABI ruling: exactly one of url/data, and it must always be url - inlining a copy of a
    document this generator already serves at a URL would be the second copy LAW #ONE-PLACE
    forbids."""
    catalog = json.loads(AI_CATALOG.read_text(encoding="utf-8"))
    assert catalog["entries"], "ai-catalog.json has no entries"
    for entry in catalog["entries"]:
        assert "url" in entry, f"entry missing url: {entry['identifier']}"
        assert "data" not in entry, f"entry carries inline data, never allowed: {entry['identifier']}"


def test_ai_catalog_entries_have_two_to_five_representative_queries():
    catalog = json.loads(AI_CATALOG.read_text(encoding="utf-8"))
    for entry in catalog["entries"]:
        n = len(entry.get("representativeQueries", []))
        assert 2 <= n <= 5, f"{entry['identifier']} has {n} representativeQueries, want 2-5"


_FORBIDDEN_COMPANY_LEVEL_QUERY = re.compile(
    r"what autonomy level does .+ have", re.IGNORECASE)


def test_ai_catalog_never_asks_what_autonomy_level_a_company_has():
    """ABI-2-3: the level this project assigns belongs to one OPERATION, never to the company that
    runs it. A representativeQuery phrased as "what autonomy level does company X have" would make
    the catalog itself the overclaim this project marks other subjects down for making."""
    catalog = json.loads(AI_CATALOG.read_text(encoding="utf-8"))
    offenders = [
        (entry["identifier"], q)
        for entry in catalog["entries"]
        for q in entry.get("representativeQueries", [])
        if _FORBIDDEN_COMPANY_LEVEL_QUERY.search(q)
    ]
    assert not offenders, f"forbidden company-level autonomy phrasing found: {offenders}"


def test_ai_catalog_has_specversion_and_host():
    catalog = json.loads(AI_CATALOG.read_text(encoding="utf-8"))
    assert catalog.get("specVersion"), "ai-catalog.json is missing specVersion"
    assert isinstance(catalog.get("host"), dict) and catalog["host"], (
        "ai-catalog.json is missing a host object")


def test_checked_in_files_match_a_fresh_run_of_the_generator(live_report):
    """The published bytes ARE the generator's output, not a copy someone touched up by hand."""
    assert API_CATALOG.is_file(), "web/public/.well-known/api-catalog is missing"
    assert LLMS_TXT.is_file(), "web/public/llms.txt is missing"
    assert LLMS_FULL_TXT.is_file(), "web/public/llms-full.txt is missing"
    assert AI_CATALOG.is_file(), "web/public/.well-known/ai-catalog.json is missing"
    fresh_catalog = json.dumps(live_report["apiCatalog"], indent=2) + "\n"
    assert API_CATALOG.read_text(encoding="utf-8") == fresh_catalog, (
        "the checked-in api-catalog is not what web/discovery.mjs produces right now")
    assert LLMS_TXT.read_text(encoding="utf-8") == live_report["llmsTxt"], (
        "the checked-in llms.txt is not what web/discovery.mjs produces right now")
    assert LLMS_FULL_TXT.read_text(encoding="utf-8") == live_report["llmsFullTxt"], (
        "the checked-in llms-full.txt is not what web/discovery.mjs produces right now")
    fresh_ai_catalog = json.dumps(live_report["aiCatalog"], indent=2) + "\n"
    assert AI_CATALOG.read_text(encoding="utf-8") == fresh_ai_catalog, (
        "the checked-in ai-catalog.json is not what web/discovery.mjs produces right now")


def test_robots_txt_content_signal_is_the_ratified_value():
    """Fable's ruling fixed these three values; nothing here may change them."""
    text = (WEB / "public" / "robots.txt").read_text(encoding="utf-8")
    assert "Content-Signal: search=yes, ai-input=yes, ai-train=no" in text
    assert "The registry and every passport are meant to be found and quoted." in text, (
        "the pre-existing comment must survive this edit, not be replaced by it")


def test_headers_file_declares_the_link_relations():
    text = (WEB / "public" / "_headers").read_text(encoding="utf-8")
    assert 'rel="alternate"' in text and "/data/registry.json" in text
    assert 'rel="api-catalog"' in text and "/.well-known/api-catalog" in text


def test_headers_file_declares_llms_full_and_ai_catalog():
    text = (WEB / "public" / "_headers").read_text(encoding="utf-8")
    assert "/llms-full.txt" in text and "text/plain" in text
    assert "/.well-known/ai-catalog.json" in text
    assert "Access-Control-Allow-Origin: *" in text, (
        "the ARD manifest must be served CORS-open so an agent can fetch it cross-origin")


# --- PROOF THAT THE CHECK CAN ACTUALLY GO RED -------------------------------------------------
#
# Every assertion above runs against real, currently-consistent data, which is exactly the shape
# of test that a real drift would leave passing (L-16, "the finding is the absence of a check that
# CAN fail"). This section manufactures the drift on a throwaway copy of the data - never on
# `web/public/data`, which other work is actively editing - and proves the comparison used above
# actually distinguishes the broken case from the healthy one.

def test_a_passport_dropped_from_disk_is_detected_as_drift(tmp_path):
    """Delete one passport from a COPY of the data and show that the registry/disk comparison this
    suite relies on goes from agreeing to disagreeing - the mechanism the tests above depend on,
    proven capable of catching the thing it exists to catch. Checked on all four maps: dropping one
    passport must vanish it from the RFC 9727 catalog, from llms.txt, from llms-full.txt (which
    embeds that same catalog), and from the ARD manifest - not just from the raw id lists."""
    scratch = tmp_path / "data"
    shutil.copytree(DATA_DIR, scratch)
    victims = sorted((scratch / "passports").glob("*.json"))
    assert victims, "fixture setup found no passports to drop"
    victim_slug = victims[0].stem
    victims[0].unlink()

    healthy = _run_discovery(DATA_DIR)
    drifted = _run_discovery(scratch)

    assert healthy["registrySubjectIds"] == healthy["passportIds"], (
        "sanity check failed: the real tree is not even consistent before the mutation")
    assert drifted["registrySubjectIds"] != drifted["passportIds"], (
        "dropping a passport file did not register as drift - the comparison cannot fail, "
        "which means it was never really checking anything"
    )
    missing = set(drifted["registrySubjectIds"]) - set(drifted["passportIds"])
    assert missing == {victim_slug}, f"wrong passport reported missing: {missing}"

    # And the drift is visible in every generated map, not just in the raw id lists.
    assert victim_slug not in _catalog_passport_slugs(drifted["apiCatalog"])
    assert victim_slug not in _llms_txt_passport_slugs(drifted["llmsTxt"])
    assert victim_slug not in _llms_txt_passport_slugs(drifted["llmsFullTxt"]), (
        "llms-full.txt still names the dropped passport - it must be a live render of the "
        "current entries, not a stale copy")
    assert victim_slug not in _ai_catalog_passport_slugs(drifted["aiCatalog"]), (
        "ai-catalog.json still names the dropped passport")


def test_the_checked_in_ai_catalog_would_have_caught_a_hand_edited_removal(tmp_path):
    """Mutate the PUBLISHED file directly (not the generator's input) and show the
    generator-vs-checked-in comparison used by `test_checked_in_files_match_a_fresh_run_of_the_generator`
    actually distinguishes hand-edited drift from a fresh, correct render."""
    catalog = json.loads(AI_CATALOG.read_text(encoding="utf-8"))
    assert len(catalog["entries"]) > 2, "fixture assumption failed: expected more than registry+apply"
    # Drop exactly one passport entry by hand, on an in-memory copy - never on the checked-in file.
    passport_entries = [e for e in catalog["entries"] if e["identifier"].startswith(
        "urn:air:provek.dev:passport:")]
    dropped = passport_entries[0]
    mutated_entries = [e for e in catalog["entries"] if e is not dropped]
    mutated_bytes = json.dumps({**catalog, "entries": mutated_entries}, indent=2) + "\n"

    fresh = _run_discovery(DATA_DIR)
    fresh_bytes = json.dumps(fresh["aiCatalog"], indent=2) + "\n"

    assert AI_CATALOG.read_text(encoding="utf-8") == fresh_bytes, (
        "sanity check failed: the checked-in file was already not what the generator produces")
    assert mutated_bytes != fresh_bytes, (
        "hand-removing one entry did not change the bytes compared against the fresh generator "
        "run - the equality check in test_checked_in_files_match_a_fresh_run_of_the_generator "
        "cannot fail, which means it was never really checking anything"
    )


def test_the_BUILT_robots_txt_carries_what_the_source_says() -> None:
    """The source file is not what a reader receives, and for one build this was literally true.

    `web/prerender.mjs` used to rewrite `dist/robots.txt` from a hardcoded string of its own,
    running AFTER vite had copied `public/robots.txt` into the build. So a Content-Signal added to
    the source was silently dropped from every deploy, and the test above - which reads the SOURCE
    - stayed green the whole time. That is this project's own law failing on this project: measure
    the served artefact, not the repository file.

    The build is what push.sh step 6 produces, which is why step 7 runs after it.
    """
    built = WEB / "dist" / "robots.txt"
    assert built.is_file(), (
        "web/dist/robots.txt is absent, so this gate measured nothing. Run `npm run build` in web/ "
        "- scripts/push.sh does exactly that before the suite, for this reason. A skip here would "
        "be a gate present but not armed."
    )
    source = (WEB / "public" / "robots.txt").read_text(encoding="utf-8").strip()
    text = built.read_text(encoding="utf-8")
    missing = [ln for ln in source.splitlines() if ln.strip() and ln not in text]
    assert not missing, (
        "the built robots.txt has dropped lines that the source declares, so what the site serves "
        "is not what the repository says:\n  " + "\n  ".join(missing)
    )
    assert "Sitemap:" in text, (
        "the built robots.txt names no sitemap. That line is generated rather than stored because "
        "it depends on SITE, so its absence means the generator stopped running - not that the "
        "source changed."
    )
