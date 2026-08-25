"""The pipeline's output and what the site serves must be the same bytes.

`scripts/cohort.py` wrote `public/`. The site and `web/prerender.mjs` read `web/public/data/`.
Both trees are tracked and both are judged -- by different tests -- and until 2026-08-25 NOTHING
copied one to the other: a human did, by hand, after every run. One artefact with two homes and no
writer. Left alone it would have let automated intake publish a verdict into a file that no reader
is ever served, while every test kept passing.

These tests do not check that the copying code exists. They check the bytes, which is the only
thing a reader receives.
"""
import hashlib
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
EMITTED = ROOT / "public"
SERVED = ROOT / "web" / "public" / "data"


def _sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_the_registry_the_site_serves_is_the_registry_the_pipeline_emitted():
    a, b = EMITTED / "registry" / "registry.json", SERVED / "registry.json"
    assert a.is_file() and b.is_file(), "one of the two registries is missing entirely"
    assert _sha(a) == _sha(b), (
        "the served registry differs from the emitted one: a verdict was published into a file "
        "nobody is served, or the served file was edited without the pipeline")


def test_every_emitted_passport_is_served_byte_for_byte():
    emitted = {p.name: _sha(p) for p in (EMITTED / "passports").glob("*.json")}
    served = {p.name: _sha(p) for p in (SERVED / "passports").glob("*.json")}
    assert emitted, "the pipeline emitted no passports at all"
    assert set(emitted) == set(served), (
        f"only emitted: {sorted(set(emitted) - set(served))}; "
        f"only served: {sorted(set(served) - set(emitted))}")
    differing = [n for n in emitted if emitted[n] != served[n]]
    assert not differing, f"served under the same name but different bytes: {sorted(differing)}"


def test_the_registry_lists_exactly_the_passports_that_are_served():
    """A row pointing at a document that is not there is worse than a missing row."""
    import json
    reg = json.loads((SERVED / "registry.json").read_text(encoding="utf-8"))
    listed = {s["subject_id"].replace(":", "_").replace("/", "_") + ".json" for s in reg["subjects"]}
    served = {p.name for p in (SERVED / "passports").glob("*.json")}
    assert listed == served, (
        f"listed but not served: {sorted(listed - served)}; "
        f"served but not listed: {sorted(served - listed)}")
