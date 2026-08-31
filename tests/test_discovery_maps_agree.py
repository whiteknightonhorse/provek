"""The agent-discovery maps (RFC 9727 api-catalog + llms.txt) must not drift from each other, from
the checked-in static files, or from the registry/passport data they describe.

WHY THIS EXISTS. The task's own warning: "three copies of one map inevitably drift". There are, in
fact, three things that could each independently claim to know the world here - the registry, the
passports directory, and the two published maps - and nothing before this file checked that they
agreed. `web/discovery.mjs` is the one generator; these tests check its OUTPUT, not that it exists,
because a generator nobody runs and a hand-edited file downstream of it look identical to a test
that only checks source code.
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


def test_api_catalog_lists_exactly_the_served_passports(live_report):
    got = _catalog_passport_slugs(live_report["apiCatalog"])
    want = set(live_report["passportIds"])
    assert got == want, f"api-catalog passport links do not match the served passports: {got ^ want}"


def test_llms_txt_lists_exactly_the_served_passports(live_report):
    got = _llms_txt_passport_slugs(live_report["llmsTxt"])
    want = set(live_report["passportIds"])
    assert got == want, f"llms.txt passport links do not match the served passports: {got ^ want}"


def test_api_catalog_and_llms_txt_agree_with_each_other(live_report):
    """The two maps are built from the same `entries` array in the same function call - this is
    the assertion that would catch it if a future edit special-cased one map and not the other."""
    a = _catalog_passport_slugs(live_report["apiCatalog"])
    b = _llms_txt_passport_slugs(live_report["llmsTxt"])
    assert a == b, f"api-catalog and llms.txt disagree on which passports exist: {a ^ b}"


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


def test_checked_in_files_match_a_fresh_run_of_the_generator(live_report):
    """The published bytes ARE the generator's output, not a copy someone touched up by hand."""
    assert API_CATALOG.is_file(), "web/public/.well-known/api-catalog is missing"
    assert LLMS_TXT.is_file(), "web/public/llms.txt is missing"
    fresh_catalog = json.dumps(live_report["apiCatalog"], indent=2) + "\n"
    assert API_CATALOG.read_text(encoding="utf-8") == fresh_catalog, (
        "the checked-in api-catalog is not what web/discovery.mjs produces right now")
    assert LLMS_TXT.read_text(encoding="utf-8") == live_report["llmsTxt"], (
        "the checked-in llms.txt is not what web/discovery.mjs produces right now")


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
    proven capable of catching the thing it exists to catch."""
    scratch = tmp_path / "data"
    shutil.copytree(DATA_DIR, scratch)
    victims = sorted((scratch / "passports").glob("*.json"))
    assert victims, "fixture setup found no passports to drop"
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
    assert missing == {victims[0].stem}, f"wrong passport reported missing: {missing}"

    # And the drift is visible in the generated catalog too, not just in the raw id lists.
    assert victims[0].stem not in _catalog_passport_slugs(drifted["apiCatalog"])

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
