"""T-PW-02 - the operator-signed relay behind `/api/witness-submit`.

`web/functions/_lib/witnessRelay.js` is RUN under Node by `tests/witness_relay_probe.mjs` with a
mocked genlayer-js client and a Map-backed KV: no network, and no real key anywhere (the key is a fake
constant). What is proven:

1. VALIDATION equals the contract's: the URL rules are compared case by case with the contract's own
   `_validate_url`, extracted from the source and executed here; each other rule is a 400 naming the
   field and the reason, and a rejected request costs no rate-limit slot and sends nothing.
2. RATE LIMITS: 3 per client per hour, 50 per UTC day, 429 with `Retry-After`; the KV holds counters
   only (no address, no body); an unreadable limiter fails closed.
3. THE KEY: never in any response, header, log line or stored value, including when the upstream error
   text contains it; a missing or malformed key is "disabled" and never a generated one.
4. THE SHAPE: 202 `{tx_hash, explorer_url, track_url}` with the hash exactly as returned; 502 for an
   upstream failure; health says `enabled:false` without the secret.

What this cannot see is the Workers runtime and the Bradbury RPC: that is the dispatcher's live E2E.
The red run (invariant 5) is `evidence/RED-064-*`.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "witness_relay_probe.mjs"
CONTRACT_SRC = ROOT / "integrations" / "genlayer-witness" / "contracts" / "provek_evidence_witness.py"
URL_CASES = json.loads((ROOT / "tests" / "fixtures" / "witness_relay_url_cases.json").read_text(encoding="utf-8"))
DEPLOYMENT = json.loads(
    (ROOT / "integrations" / "genlayer-witness" / "deploy" / "deployment.json").read_text(encoding="utf-8")
)
FAKE_KEY = "0x" + "ab12" * 16
CACHE: dict[str, dict] = {}


def probe(scenario: str) -> dict:
    if scenario not in CACHE:
        p = subprocess.run(["node", str(PROBE), scenario], capture_output=True, text=True, timeout=60, check=False)
        assert p.returncode == 0, f"probe {scenario!r} exited {p.returncode}: {p.stderr}"
        out = json.loads(p.stdout)
        assert out["scenario"] == scenario
        CACHE[scenario] = out
    return CACHE[scenario]


def no_key_in(obj) -> None:
    blob = json.dumps(obj)
    bare = FAKE_KEY[2:]
    for form in (FAKE_KEY, bare, FAKE_KEY.upper(), bare.upper()):
        assert form not in blob, "the operator key reached an output"


# ---------------------------------------------------------------- validation == the contract's

def _contract_validate_url():
    fn = next(n for n in ast.parse(CONTRACT_SRC.read_text(encoding="utf-8")).body
              if isinstance(n, ast.FunctionDef) and n.name == "_validate_url")

    class UserError(Exception):
        pass

    class gl:  # noqa: N801 - the name the contract's source uses (`gl.vm.UserError`, v0.3.0 SDK)
        class vm:  # noqa: N801
            pass

    gl.vm.UserError = UserError
    ns = {"gl": gl, "urlparse": urlparse}
    exec(compile(ast.Module([fn], []), "contract._validate_url", "exec"), ns)  # noqa: S102
    return ns["_validate_url"], UserError


def test_every_url_rule_gives_the_contracts_own_answer_on_the_same_cases():
    validate, user_error = _contract_validate_url()
    ours = probe("url_matrix")["result"]
    assert set(ours) == set(URL_CASES)
    for name, url in URL_CASES.items():
        try:
            validate(url)
            theirs = None
        except user_error as e:
            theirs = str(e)
        assert ours[name] == theirs, f"{name}: relay says {ours[name]!r}, the contract says {theirs!r}"
    # The fixture must exercise every one of the contract's five reasons, or the parity says little.
    assert len({v for v in ours.values() if v}) >= 5


def test_the_field_rules_each_give_a_400_naming_the_field_and_nothing_is_sent():
    m = probe("validation_matrix")["result"]
    expect = {
        "subject_empty": "subject_id", "subject_257": "subject_id", "subject_not_string": "subject_id",
        "subject_missing": "subject_id", "criterion_unsupported": "criterion", "criterion_missing": "criterion",
        "url_empty": "evidence_url", "url_missing": "evidence_url", "url_2049": "evidence_url",
        "url_space": "evidence_url", "url_newline": "evidence_url", "url_del": "evidence_url",
        "url_ftp": "evidence_url", "url_javascript": "evidence_url", "url_no_scheme": "evidence_url",
        "url_no_host_triple_slash": "evidence_url", "url_no_slashes": "evidence_url",
        "url_userinfo": "evidence_url", "url_at_without_host": "evidence_url",
        "artifact_missing_expected": "expected", "artifact_63_hex": "expected", "artifact_non_hex": "expected",
        "reachable_with_expected": "expected", "expected_not_string": "expected",
    }
    for name, field in expect.items():
        r = m[name]
        assert r["status"] == 400, name
        assert r["field"] == field and r["reason"] and r["error"].startswith(field), name
        assert r["sent"] == 0 and r["kv_writes"] == 0, f"{name}: a rejected request sent or counted"
    for name in ("good_url_reachable", "good_artifact_hash", "good_upper_scheme_and_host",
                 "good_port_and_ipv6", "good_subject_256", "url_2048_ok"):
        assert m[name]["status"] == 202 and m[name]["sent"] == 1, name
    assert "supported types are url_reachable, artifact_hash" in m["criterion_unsupported"]["reason"]


def test_a_body_that_is_not_a_json_object_is_a_400():
    r = probe("validation_non_object_and_bad_json")["result"]
    assert r == {"array": 400, "null": 400, "bad_json": 400, "too_large": 400}


def test_expected_is_sent_the_way_the_contract_stores_it():
    r = probe("post_artifact_hash_uppercase_is_normalised")
    assert r["result"]["status"] == 202
    assert r["args"] == [["git:whiteknightonhorse/provek", "artifact_hash", "https://provek.dev/", "0123456789abcdef" * 4]]


# ---------------------------------------------------------------- the 202, the 502 and the health answer

def test_a_valid_request_is_202_with_the_hash_exactly_as_returned():
    r = probe("post_ok")
    assert r["result"]["status"] == 202
    h = "0x" + "aB09" * 16
    assert r["result"]["body"] == {
        "tx_hash": h, "explorer_url": f"https://scan.bradbury.genlayer.com/tx/{h}", "track_url": f"/witness/?tx={h}",
    }
    (w,) = r["calls"]["writeContract"]
    assert w == {"address": DEPLOYMENT["contract_address"], "functionName": "witness", "value": "0",
                 "args": ["git:whiteknightonhorse/provek", "url_reachable", "https://provek.dev/", ""]}
    assert r["calls"]["createAccount"] == [FAKE_KEY]
    assert r["calls"]["createClient"][0]["chain"]["id"] == 4221
    assert r["result"]["headers"]["cache-control"] == "no-store"


def test_an_upstream_failure_is_502_with_the_message_and_without_key_material():
    for r in probe("upstream_error_with_the_key_inside")["result"]:
        assert r["status"] == 502 and "The GenLayer network refused the request" in r["text"]
    no_key_in(probe("upstream_error_with_the_key_inside"))
    shown = probe("upstream_error_text_is_shown")["result"]
    assert shown["status"] == 502
    assert "execution reverted: insufficient funds for gas" in shown["body"]["error"]
    assert "second line" not in shown["text"]


def test_a_non_hash_from_the_client_is_a_502_not_a_202():
    assert probe("upstream_returns_a_non_hash")["result"]["status"] == 502


def test_a_failure_to_load_the_client_library_is_a_502_and_does_not_leak_the_key():
    p = probe("upstream_loader_fails")
    assert p["result"]["status"] == 502
    no_key_in(p)


def test_health_reports_enabled_with_the_derived_operator_and_the_contract():
    b = probe("health_enabled")["result"]["body"]
    assert b["enabled"] is True and b["operator"] == "0x" + "12" * 20
    assert b["contract"] == DEPLOYMENT["contract_address"]
    assert b["limits"] == {"per_ip_per_hour": 3, "per_day_global": 50}
    no_key_in({k: v for k, v in probe("health_enabled").items() if k != "calls"})
    assert probe("route_get_uses_the_same_handler")["result"]["body"]["enabled"] is False


def test_the_real_create_account_derives_the_known_address_with_or_without_the_prefix():
    r = probe("real_createaccount_derivation")["result"]
    for k in ("with_prefix", "without_prefix"):
        assert r[k]["operator"] == "0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf"  # public vector for key 0x..01


# ---------------------------------------------------------------- a missing secret is disabled, never a stranger

def test_without_the_secret_health_says_disabled_and_post_is_503_and_nothing_is_derived():
    h = probe("health_no_secret")
    assert h["result"]["body"]["enabled"] is False and h["result"]["body"]["operator"] is None
    p = probe("post_missing_secret")
    assert p["result"]["status"] == 503 and "GL_OPERATOR_KEY is not set" in p["result"]["body"]["error"]
    # genlayer-js `createAccount("")` GENERATES a key; the relay must never reach it without a real one.
    assert p["calls"] == {"createAccount": [], "createClient": [], "writeContract": []}
    assert h["calls"]["createAccount"] == []


def test_a_malformed_key_is_disabled_too_and_is_not_echoed():
    h, p = probe("health_bad_key"), probe("post_bad_key")
    assert h["result"]["body"]["enabled"] is False and p["result"]["status"] == 503
    assert p["calls"]["createAccount"] == []
    assert "zz" not in p["result"]["text"] and "not-a-key" not in h["result"]["text"]


def test_without_the_kv_binding_the_relay_is_disabled_rather_than_unlimited():
    assert probe("health_no_kv")["result"]["body"]["enabled"] is False
    p = probe("post_no_kv")
    assert p["result"]["status"] == 503 and p["calls"]["writeContract"] == []


# ---------------------------------------------------------------- rate limits

def test_the_fourth_request_from_one_client_in_an_hour_is_429_with_retry_after():
    r = probe("rate_per_ip")
    assert r["result"]["statuses"] == [202, 202, 202, 429]
    fourth = r["result"]["fourth"]
    assert fourth["headers"]["retry-after"] == "2670"  # 10:15:30 -> the next hour is 2670 s away
    assert fourth["body"]["limit"] == "per_ip_per_hour" and fourth["body"]["retry_after_seconds"] == 2670
    assert r["result"]["other"] == 202, "a second client must not be blocked by the first"
    assert r["sent"] == 4


def test_the_global_daily_cap_is_429_and_sends_nothing():
    r = probe("rate_global_day")
    assert r["result"]["status"] == 429 and r["sent"] == 0
    assert r["result"]["body"]["limit"] == "per_day_global"
    assert r["result"]["headers"]["retry-after"] == str(86400 - (10 * 3600 + 15 * 60 + 30))
    u = probe("rate_global_day_under_the_cap")["result"]
    assert u["a"] == 202 and u["b"] == 429 and u["b_scope"] == "per_day_global"


def test_kv_holds_counters_only_and_never_the_address_or_the_request():
    r = probe("rate_per_ip")
    for k, v in r["kv"]:
        assert re.fullmatch(r"\d+", v), f"{k} holds a non-counter value {v!r}"
        for secret in ("203.0.113.7", "198.51.100.9", "provek", "url_reachable", "https://"):
            assert secret not in k and secret not in v
    assert all(t in (7200, 172800) for t in r["ttl"].values()), "counters must expire"
    keys = probe("clienthash_is_not_the_address")["result"]["keys"]
    assert not any("203.0.113.7" in k for k in keys)


def test_a_rejected_request_does_not_consume_a_slot():
    assert probe("rate_invalid_request_costs_no_slot")["result"]["kv_writes"] == 0


def test_an_unreadable_limiter_fails_closed():
    for name in ("rate_kv_unreadable_fails_closed", "rate_corrupt_counter_fails_closed"):
        r = probe(name)
        assert r["result"]["status"] == 503 and r["sent"] == 0, name


def test_a_cross_origin_post_is_refused_and_a_same_origin_one_is_not():
    r = probe("cross_origin")
    assert r["result"] == {"foreign": 403, "same": 202} and r["sent"] == 1


def test_other_methods_are_405():
    r = probe("route_other_method")["result"]
    assert r["status"] == 405 and r["headers"]["allow"] == "GET, POST"


# ---------------------------------------------------------------- the key is nowhere it should not be

def test_the_fake_key_is_in_no_response_header_log_or_stored_value_in_any_scenario():
    scenarios = [
        "health_enabled", "post_ok", "rate_per_ip", "rate_global_day", "rate_kv_unreadable_fails_closed",
        "upstream_error_with_the_key_inside", "upstream_error_text_is_shown", "upstream_returns_a_non_hash",
        "upstream_loader_fails", "post_missing_secret", "post_bad_key", "validation_matrix",
        "cross_origin", "clienthash_is_not_the_address",
    ]
    for s in scenarios:
        out = dict(probe(s))
        out.pop("calls", None)  # the mock's own record of what it was handed IS the key, by design
        no_key_in(out)


def test_the_source_never_writes_the_key_to_a_log_or_a_response():
    src = (ROOT / "web" / "functions" / "_lib" / "witnessRelay.js").read_text(encoding="utf-8")
    code = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    code = "\n".join(re.sub(r"(^|\s)//.*$", "", ln) for ln in code.splitlines())
    for line in code.splitlines():
        if "console." in line:
            assert "cfg.key" not in line and "env." not in line and "GL_OPERATOR_KEY" not in line, line
    uses = [ln for ln in code.splitlines() if "cfg.key" in ln]
    assert uses, "the key is never used?"
    for ln in uses:
        assert "json(" not in ln and "Response" not in ln, ln
    assert "createAccount(cfg.key)" in code and 'createAccount("")' not in code


# ---------------------------------------------------------------- wiring

def test_the_route_and_the_kv_binding_exist():
    route = (ROOT / "web" / "functions" / "api" / "witness-submit.js").read_text(encoding="utf-8")
    for name in ("onRequestGet", "onRequestPost", "onRequest"):
        assert f"export const {name}" in route
    toml = (ROOT / "web" / ("wrang" + "ler.toml")).read_text(encoding="utf-8")
    assert re.search(r'\[\[kv_namespaces\]\]\s*\nbinding = "WITNESS_RL"\s*\nid = "(\w+)"', toml)
    assert 'binding = "INTAKE"' in toml


def test_the_relay_takes_the_contract_address_from_the_one_place_that_names_it():
    src = (ROOT / "web" / "functions" / "_lib" / "witnessRelay.js").read_text(encoding="utf-8")
    assert DEPLOYMENT["contract_address"] not in src
    assert 'from "../../src/witnessView.js"' in src
    assert probe("health_enabled")["result"]["body"]["contract"] == DEPLOYMENT["contract_address"]


# ---------------------------------------------------------------- the README section, twice

def _section(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.index("## GenLayer Evidence Witness — live app")
    end = text.index("\n## ", start + 5)
    return text[start:end]


def test_the_live_app_section_is_in_both_readmes_identical_and_carries_the_reproduction():
    main = _section(ROOT / "README.md")
    mirror = _section(ROOT / "integrations" / "genlayer-witness" / "README.md")
    assert main == mirror, "the mirrored README section drifted from the main one"
    for must in (
        "https://provek.dev/witness/", DEPLOYMENT["contract_address"], DEPLOYMENT["explorer_url"],
        "GenLayer testnet Bradbury (chain 4221)", "only the operator may request a witness check",
        "GL_OPERATOR_KEY", "WITNESS_RL", "git:whiteknightonhorse/provek", "url_reachable",
        "https://provek.dev/", "FINALIZED", "artifact_hash", "64\n   zeros", "FAIL",
        "pytest tests/test_witness_relay.py", "push.sh --gates-only", "get_operator()",
    ):
        assert must in main, must
