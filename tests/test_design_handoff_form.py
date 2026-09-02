"""T-20-design-handoff: the landing/registry copy the phase-2 ruling logged as a follow-up task,
separate from the order-channel mechanism itself (D-46/D-47, already done). Form only - no new
predicate, no new schema field. Checked over the EMITTED HTML, since that is what a reader (and
`test_registry_corrections.py`'s own discipline) actually receives.

The one thing this handoff adds that the rest of the site does not otherwise have a rule against
is a single fabricated table-row-shaped example on `/registry/`, labelled as a sample. D-04 forbids
inventing a company in the registry; this checks the fabrication never becomes one - it must not be
a link, and it must never appear in the data the registry is actually built from.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOME_PAGE = ROOT / "web" / "dist" / "index.html"
REGISTRY_PAGE = ROOT / "web" / "dist" / "registry" / "index.html"
REGISTRY_JSON = ROOT / "public" / "registry" / "registry.json"
LANDING_SRC = ROOT / "web" / "src" / "pages" / "Landing.tsx"
REGISTRY_SRC = ROOT / "web" / "src" / "pages" / "Registry.tsx"

emitted = pytest.mark.skipif(
    not (HOME_PAGE.exists() and REGISTRY_PAGE.exists()),
    reason="site not built in this checkout",
)


def _main_text(html_path: Path) -> str:
    html = html_path.read_text(encoding="utf-8")
    body = html.split("<script>window.__PROVEK__", 1)[0]
    m = re.search(r"<main\b.*?</main>", body, re.S)
    assert m, f"{html_path} has no <main>"
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(0))).strip()


@emitted
def test_home_states_the_two_phases_in_order():
    text = _main_text(HOME_PAGE)
    assert "Step 1" in text and "Get verified" in text
    assert "Step 2" in text and "Take orders" in text
    assert "Order from a verified agent" in text


@emitted
def test_home_never_ships_the_order_link_without_its_honest_fallback():
    """The callout is load-bearing, not decoration (design handoff §3): if it ever ships without
    the fallback while zero subjects are order-eligible, the homepage advertises a marketplace
    that does not exist for anyone who clicks through. Today (all `service_url` null) the fallback
    must be present; this also proves the two ship together rather than the link alone."""
    reg = json.loads(REGISTRY_JSON.read_text())
    anyone_eligible = any(s.get("service_url") and s.get("service_reachable") for s in reg["subjects"])
    text = _main_text(HOME_PAGE)
    assert "Order from a verified agent" in text, "the rail link itself is missing"
    if not anyone_eligible:
        assert "No listing takes orders yet" in text, (
            "nobody qualifies today but the honest fallback is not on the page")


@emitted
def test_registry_subheadline_states_both_phases():
    text = _main_text(REGISTRY_PAGE)
    assert "what could be established about each" in text
    assert "once verified, where you can order from them" in text


@emitted
def test_registry_order_column_explains_itself():
    html = REGISTRY_PAGE.read_text(encoding="utf-8")
    assert re.search(r'<th[^>]*>\s*Order\s*<a[^>]*href="/method/#the-order-link"', html), (
        "the Order header carries no inline link to how it is decided")


@emitted
def test_registry_sample_row_is_fenced_off_and_inert():
    text = _main_text(REGISTRY_PAGE)
    assert "What an earned listing looks like" in text
    assert "sample, not a real subject" in text
    assert "example-agent" in text

    html = REGISTRY_PAGE.read_text(encoding="utf-8")
    i = html.find("example-agent")
    assert i != -1
    around = html[max(0, i - 400) : i + 400]
    # The fake "Order" mark must never be a pressable/navigable control - it is shown, not offered.
    assert not re.search(r"<a\b[^>]*>\s*Order", around), (
        "the sample row's Order mark is a real link, not an inert illustration")


def test_sample_subject_never_appears_in_the_real_registry_data():
    reg = json.loads(REGISTRY_JSON.read_text())
    ids = {s["subject_id"] for s in reg["subjects"]}
    assert "example-agent" not in ids
    assert "git:example-org/example-agent" not in ids
    raw = REGISTRY_JSON.read_text()
    assert "example-agent" not in raw, "the sample leaked into the data the registry is built from"


def test_apply_and_passport_copy_is_left_alone():
    """The handoff explicitly does not touch Apply.tsx's or the passport page's existing
    order-predicate copy - it must not be duplicated or contradicted here."""
    apply_src = (ROOT / "web" / "src" / "pages" / "Apply.tsx").read_text(encoding="utf-8")
    assert "#the-order-link" in apply_src, "Apply.tsx's own order-link explainer moved or vanished"


def test_the_two_source_files_touched_are_the_ones_the_handoff_named():
    landing = LANDING_SRC.read_text(encoding="utf-8")
    registry = REGISTRY_SRC.read_text(encoding="utf-8")
    assert "Get verified" in landing and "Take orders" in landing
    assert "how it is decided" in registry
