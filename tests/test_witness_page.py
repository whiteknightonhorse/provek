"""T-PW-01 - the GenLayer Evidence Witness page (`/witness/`): helpers, emitted artefact, pins.

Three things are proven here, each against the thing a reader actually receives:

1. THE HELPERS (`web/src/witnessView.js`) are run under Node by `tests/witness_view_probe.mjs`
   against `tests/fixtures/witness_bradbury_reads.json` - responses captured from the live Bradbury
   RPC on 2026-10-12 (`evidence/MEASURED-015-*`), not hand-typed. No live network in this file.
2. THE EMITTED PAGE: `web/dist/witness/index.html` exists, says "GenLayer Evidence Witness", names the
   deployed contract and carries NO record value - every record on that page comes from an RPC
   response in the reader's browser, so the static HTML holding one would be a fabrication.
3. THE PINS: `genlayer-js` is an exact version in `package.json` and the lockfile agrees; the
   contract constants equal `deployment.json`; no forwarding function exists (the RPC allows a
   browser origin, measured) and the page footer says so.

The red run (invariant 5) is `evidence/RED-063-*`.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .notes_support import DIST

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "witness_view_probe.mjs"
FIXTURE = json.loads((ROOT / "tests" / "fixtures" / "witness_bradbury_reads.json").read_text(encoding="utf-8"))
DEPLOYMENT = json.loads(
    (ROOT / "integrations" / "genlayer-witness" / "deploy" / "deployment.json").read_text(encoding="utf-8")
)


def probe(scenario: str):
    p = subprocess.run(["node", str(PROBE), scenario], capture_output=True, text=True, timeout=60, check=False)
    assert p.returncode == 0, f"probe {scenario!r} exited {p.returncode}: {p.stderr}"
    out = json.loads(p.stdout)
    assert out["scenario"] == scenario
    return out["result"]


# ---------------------------------------------------------------- the fixture is a real capture

def test_the_fixture_is_the_contracts_own_answer_for_a_deployed_record():
    live = {r["witness_id"]: r for r in DEPLOYMENT["live_records"]}
    for key in ("get_result_pass", "get_result_fail"):
        wid, resp = FIXTURE[key]["witness_id"], FIXTURE[key]["response"]
        rec = live[wid]
        for f in ("subject_id", "criterion", "evidence_url", "expected", "result", "evidence_digest",
                  "checked_at", "observation"):
            assert resp[f] == rec[f], f"{key}.{f}: fixture {resp[f]!r} != deployment.json {rec[f]!r}"
    assert json.loads(FIXTURE["list_by_subject_raw"]) == [r["witness_id"] for r in DEPLOYMENT["live_records"]]


# ---------------------------------------------------------------- helpers

def test_constants_equal_the_deployment_record():
    c = probe("constants")
    assert c["addr"] == DEPLOYMENT["contract_address"]
    assert c["chain"] == DEPLOYMENT["chain_id"] == 4221
    assert c["subject"] == "git:whiteknightonhorse/provek"


def test_the_chain_object_both_consumers_build_has_the_deployment_records_id_and_http_rpc():
    c = probe("chain")
    assert c["id"] == DEPLOYMENT["chain_id"]
    assert c["http"] == [DEPLOYMENT["rpc_url"]] and c["rpc_url"] == DEPLOYMENT["rpc_url"]
    # the installed RC preset names another URL, which is WHY the helper exists: one source, never two
    assert c["preset_http"] != c["http"]
    assert c["name"] == c["preset_name"]
    assert c["refused"] == "the genlayer-js preset is not chain 4221"


def test_both_consumers_get_the_chain_from_the_one_helper():
    page = (ROOT / "web" / "src" / "witnessChain.ts").read_text(encoding="utf-8")
    relay = (ROOT / "web" / "functions" / "_lib" / "witnessRelay.js").read_text(encoding="utf-8")
    assert "bradburyChain(chains.testnetBradbury)" in page and "bradburyChain(gl.testnetBradbury)" in relay
    for src in (page, relay):
        assert "chain: chains.testnetBradbury" not in src and "chain: testnetBradbury" not in src


def test_a_result_card_is_exactly_what_get_result_returned():
    for key, verdict in (("get_result_pass", "PASS"), ("get_result_fail", "FAIL")):
        card = probe({"get_result_pass": "pass_card", "get_result_fail": "fail_card"}[key])
        resp = FIXTURE[key]["response"]
        assert card["ok"] and card["recognised"] and card["result"] == verdict
        assert card["witnessId"] == FIXTURE[key]["witness_id"]
        for f, v in resp.items():
            assert card[f] == v


def test_a_missing_field_is_null_not_an_empty_string_and_a_non_object_is_refused():
    c = probe("card_missing_field")
    assert c["ok"] and c["result"] == "PASS" and c["criterion"] is None and c["observation"] is None
    assert probe("card_not_object")["ok"] is False


def test_a_result_other_than_pass_or_fail_is_carried_through_and_flagged():
    c = probe("card_unrecognised_result")
    assert c["result"] == "MAYBE" and c["recognised"] is False


def test_the_id_list_parser_separates_empty_from_unreadable():
    ok = probe("id_list")
    assert ok["ok"] and len(ok["ids"]) == 3
    empty = probe("id_list_empty")
    assert empty == {"ok": True, "ids": []}
    for bad in ("id_list_garbage", "id_list_wrong_shape", "id_list_not_string"):
        assert probe(bad)["ok"] is False, bad


def test_an_empty_expected_value_is_named_not_blanked():
    assert "no expected value" in probe("expected_empty")
    assert probe("expected_missing") == "not returned"


def test_only_http_links_are_made_from_an_evidence_url():
    assert probe("href_https") == "https://provek.dev/"
    assert probe("href_javascript") is None


def test_the_real_unknown_id_rpc_error_is_decoded_to_the_contracts_message():
    assert probe("error_unknown_id") == "The contract answered: unknown witness_id 'nope'"
    assert probe("error_plain") == "Failed to fetch"
    assert probe("error_long") <= 303


def test_tx_hash_parsing_does_not_repair_malformed_input():
    assert probe("hash_ok") == "0x" + "ab" * 32
    assert probe("hash_padded") == "0x" + "AB" * 32
    assert probe("hash_short") is None
    assert probe("hash_no_prefix") is None
    assert probe("hash_from_query") == "0xabc"
    assert probe("hash_from_empty_query") is None


def test_explorer_paths():
    assert probe("explorer_tx") == "https://scan.bradbury.genlayer.com/tx/0xabc"
    assert probe("explorer_address") == DEPLOYMENT["explorer_url"]


def test_the_lifecycle_lists_each_status_once_in_the_order_it_was_seen():
    seq = probe("observe_sequence")
    assert [o["status"] for o in seq] == ["PENDING", "PROPOSING", "ACCEPTED", "FINALIZED"]
    assert probe("observe_ignores_empty") == []


def test_exactly_the_stated_statuses_end_the_watch():
    t = probe("terminal")
    assert {s for s, end in t.items() if end} == {
        "FINALIZED", "UNDETERMINED", "CANCELED", "VALIDATORS_TIMEOUT", "LEADER_TIMEOUT"}
    assert len(t) == 13  # every status docs.genlayer.com lists for consensus v0.6


def test_a_finalized_tx_succeeds_only_because_execution_returned():
    s = probe("tx_finalized")
    assert s["found"] and s["status"] == "FINALIZED" and s["succeeded"] and s["forThisContract"]
    assert s["execution"] == "FINISHED_WITH_RETURN"
    assert s["call"]["criterion"] == "artifact_hash"


def test_accepted_with_a_failed_execution_is_not_success():
    s = probe("tx_accepted_but_failed")
    assert s["status"] == "ACCEPTED" and s["succeeded"] is False and s["settledButFailed"] is True


def test_undetermined_is_not_success_and_its_explanation_names_the_cause():
    s = probe("tx_undetermined")
    assert s["status"] == "UNDETERMINED" and s["succeeded"] is False and s["settledButFailed"] is False
    text = probe("undetermined_text")
    assert "could not agree" in text and "evidence URL was unavailable" in text and "no record was written" in text


def test_an_unknown_hash_is_not_found_not_pending():
    assert probe("tx_unknown") == {"ok": True, "found": False}
    assert probe("tx_not_object")["ok"] is False


def test_a_tx_to_another_contract_is_not_this_contracts_success():
    s = probe("tx_other_contract")
    assert s["succeeded"] is True and s["forThisContract"] is False


def test_the_call_is_read_from_the_decoded_witness_call_only():
    assert probe("call_of_finalized")["subject_id"] == "git:whiteknightonhorse/provek"
    assert probe("call_of_wrong_method") is None


def test_record_matching_returns_one_none_or_several_and_never_guesses():
    assert probe("match_one") == "one:" + FIXTURE["get_result_pass"]["witness_id"]
    assert probe("match_none") == "none"
    assert probe("match_several") == "several"
    assert probe("match_no_call") == "no_call"


def test_a_just_submitted_hash_is_not_called_nonexistent_while_bradbury_has_not_indexed_it():
    """A1.1: the relay returns a hash Bradbury may not know for a few seconds. UNINITIALIZED inside
    the first 60 s is 'not indexed yet', the 4 s cadence goes on, and the lifecycle reaches FINALIZED."""
    r = probe("track_not_indexed_then_finalized")
    assert r["statuses"][-1] == "FINALIZED" and r["last"]["done"] == "terminal"
    assert r["polls"] == 8, "the watch stopped before the lifecycle reached FINALIZED"
    assert [e["notFound"] for e in r["log"][:2]] == ["not_indexed_yet", "not_indexed_yet"]
    assert r["log"][1]["seconds"] == 4 and r["log"][0]["done"] is None and r["log"][1]["done"] is None


def test_sixty_seconds_of_uninitialized_ends_the_watch_as_absent():
    r = probe("track_uninitialized_for_60s")
    assert r["last"]["notFound"] == "absent" and r["last"]["done"] == "terminal"
    assert r["last"]["at_s"] == 60 and r["statuses"] == []
    assert probe("track_uninitialized_for_58s")["last"]["done"] is None  # 56 s is still inside the grace


def test_a_status_that_recurs_after_an_appeal_is_listed_again_and_the_page_keys_on_position():
    r = probe("track_appeal_recurrence")
    assert r["statuses"] == ["PENDING", "COMMITTING", "APPEAL_COMMITTING", "COMMITTING", "FINALIZED"]
    page = (ROOT / "web" / "src" / "pages" / "Witness.tsx").read_text(encoding="utf-8")
    assert "key={`${i}-${o.status}`}" in page and "key={o.status}" not in page


def test_the_nav_says_genlayer_evidence_witness_everywhere():
    chrome = (ROOT / "web" / "src" / "components" / "Chrome.tsx").read_text(encoding="utf-8")
    assert 'link("/witness/", "GenLayer Evidence Witness"' in chrome
    assert '"GenLayer Witness"' not in chrome


def test_the_helper_docstring_names_the_real_test_file():
    src = (ROOT / "web" / "src" / "witnessView.js").read_text(encoding="utf-8")
    assert "test_witness_page_helpers" not in src and "tests/test_witness_page.py" in src


def test_the_form_shows_the_relays_own_message_for_400_429_and_502_and_follows_only_a_real_hash():
    h = "0x" + "ab" * 32
    assert probe("relay_202") == {"ok": True, "hash": h}
    assert probe("track_url") == f"/witness/?tx={h}"
    assert probe("relay_202_without_hash")["ok"] is False
    for case, status, text in (
        ("relay_400", 400, "evidence_url: evidence_url must name a host"),
        ("relay_429", 429, "Rate limit reached: at most 3 requests per client per hour. Try again in 2670 seconds."),
        ("relay_502", 502, "The GenLayer network refused the request: boom"),
    ):
        r = probe(case)
        assert r == {"ok": False, "status": status, "message": text}, case
    assert "without a message" in probe("relay_503_not_json")["message"]


def test_the_form_source_posts_to_the_relay_and_carries_the_required_texts():
    page = (ROOT / "web" / "src" / "pages" / "Witness.tsx").read_text(encoding="utf-8")
    assert '"/api/witness-submit"' in page and 'method: "POST"' in page
    for text in (
        "Request a check",
        "Requests are signed by the Provek operator key through a rate-limited relay because the contract",
        "only accepts the operator as caller; results are produced by GenLayer validators and read",
        "directly from the chain.",
        "sha256 of the exact bytes at the URL, 64 hex",
        "Submissions are temporarily disabled",
    ):
        assert text in page, text
    # the digest field exists only for artifact_hash, and the criteria come from the contract, not a literal list
    assert 'needsExpected = chosen === "artifact_hash"' in page and "{needsExpected && (" in page
    assert 'readView("supported_criteria")' in page and 'value="url_reachable"' not in page


# ---------------------------------------------------------------- pins

def test_genlayer_js_is_pinned_to_an_exact_version_and_the_lockfile_agrees():
    pkg = json.loads((ROOT / "web" / "package.json").read_text(encoding="utf-8"))
    ver = pkg["dependencies"]["genlayer-js"]
    assert re.fullmatch(r"\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?", ver), f"genlayer-js must be an exact version, got {ver!r}"
    lock = json.loads((ROOT / "web" / "package-lock.json").read_text(encoding="utf-8"))
    assert lock["packages"][""]["dependencies"]["genlayer-js"] == ver
    assert lock["packages"]["node_modules/genlayer-js"]["version"] == ver


def test_no_forwarding_function_exists_because_the_rpc_allows_a_browser_origin():
    assert not (ROOT / "web" / "functions" / "api" / "witness-rpc.js").exists()
    measured = sorted((ROOT / "evidence").glob("MEASURED-*-pw01-bradbury-reads.txt"))
    assert measured, "the CORS measurement that justifies having no forwarder is missing"
    assert "access-control-allow-origin: *" in measured[-1].read_text(encoding="utf-8")


def test_the_web_code_holds_no_secret_and_no_write_call():
    for f in ("witnessView.js", "witnessChain.ts"):
        src = (ROOT / "web" / "src" / f).read_text(encoding="utf-8")
        assert "writeContract" not in src and "privateKey" not in src and "createAccount" not in src
    page = (ROOT / "web" / "src" / "pages" / "Witness.tsx").read_text(encoding="utf-8")
    assert "writeContract" not in page and "createAccount" not in page


# ---------------------------------------------------------------- the emitted artefact

PAGE = DIST / "witness" / "index.html"


def _page() -> str:
    assert PAGE.is_file(), (
        f"{PAGE} is absent - the site was not built, or /witness/ was not emitted. "
        "That is 'check_did_not_run' or a missing route, never a clean result."
    )
    return PAGE.read_text(encoding="utf-8")


def test_witness_route_is_emitted_titled_and_named_for_genlayer():
    html = _page()
    assert "<title>GenLayer Evidence Witness - Provek</title>" in html
    assert "<h1" in html and "GenLayer Evidence Witness" in html
    assert 'rel="canonical" href="https://provek.dev/witness/"' in html


def test_the_emitted_page_names_the_contract_network_and_explorer():
    html = _page()
    assert DEPLOYMENT["contract_address"] in html
    assert "GenLayer testnet Bradbury Phase 2 (chain 4221)" in html
    assert DEPLOYMENT["explorer_url"] in html
    assert "Reads go directly from your browser to the Bradbury Phase 2 RPC (" + DEPLOYMENT["rpc_url"].removeprefix("https://") + ")" in html
    assert "Redeployed on Bradbury Phase 2 on 2026-10-28 after GenLayer reset the testnet on 2026-10-24" in html
    assert "previous_deployments" in html and "while it still answers" not in html


def test_the_emitted_page_carries_no_record_value():
    """Every record on this page comes from an RPC response in the reader's session. A witness id,
    an evidence digest or a PASS/FAIL badge in the STATIC html would be data nobody read."""
    html = _page()
    for r in DEPLOYMENT["live_records"]:
        assert r["witness_id"] not in html
        assert r["evidence_digest"] not in html
    assert not re.search(r">\s*(PASS|FAIL)\s*<", html)


def test_the_page_is_in_the_sitemap_and_the_nav_and_never_called_a_witness_record():
    sitemap = (DIST / "sitemap.xml").read_text(encoding="utf-8")
    assert "<loc>https://provek.dev/witness/</loc>" in sitemap
    for other in ("method/index.html", "registry/index.html", "index.html"):
        assert 'href="/witness/"' in (DIST / other).read_text(encoding="utf-8"), other
    assert "/w/" in _page()  # the disambiguation sentence names the other thing


def test_the_page_prerenders_once_and_has_unique_ids():
    html = _page()
    ids = re.findall(r'\sid="([^"]+)"', html)
    assert len(ids) == len(set(ids)), sorted({i for i in ids if ids.count(i) > 1})


def test_the_emitted_page_has_the_request_form_and_the_relay_note_but_no_enabled_state():
    html = _page()
    assert "Request a check" in html and "rate-limited relay" in html
    assert "temporarily disabled" not in html  # relay state is read in the browser, never baked in


def test_the_chain_client_is_not_in_the_entry_bundle():
    """genlayer-js brings viem. It loads on first lookup (dynamic import), never with the page."""
    entry = re.findall(r'<script type="module"[^>]* src="(/assets/[^"]+)"', (DIST / "witness" / "index.html").read_text(encoding="utf-8"))
    assert entry, "no module entry script found in /witness/ html"
    body = (DIST / entry[0].lstrip("/")).read_text(encoding="utf-8")
    assert "gen_call" not in body, "the chain client was bundled into the entry chunk"
    assert "import(" in body
