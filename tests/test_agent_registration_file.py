"""T-0577 - the ERC-8004 registration file is one shape (`services` + `registrations`), carries the
real on-chain agentId, and describes only what runs.

`supportedTrust` is absent on purpose: T-GLR-02 left no ERC-8004 validation hook in the witness
relay or contract (nothing calls the Validation Registry), so advertising "validation" would claim
a thing that does not run. Add the key in the card that adds the hook.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "web/public/.well-known/agent-registration.json"
DEPLOYMENT = ROOT / "integrations/genlayer-witness/deploy/deployment.json"


def reg():
    return json.loads(FILE.read_text())


def test_the_keys_are_exactly_the_current_shape():
    assert set(reg()) == {"type", "name", "description", "image", "services", "registrations",
                          "active", "x402Support"}
    assert "endpoints" not in reg() and "supportedTrust" not in reg()


def test_the_registration_names_the_real_on_chain_agent():
    r = reg()["registrations"]
    assert r == [{"agentId": 399051,
                  "agentRegistry": "eip155:8453:0x8004a169fb4a3325136eb29fa0ceb6d2e539a432"}]
    assert reg()["active"] is True and reg()["x402Support"] is False


def test_the_contract_service_is_the_deployment_explorer_url():
    explorer = json.loads(DEPLOYMENT.read_text())["explorer_url"]
    svc = {s["name"]: s["endpoint"] for s in reg()["services"]}
    assert svc == {"web": "https://provek.dev", "GenLayer contract": explorer}


def test_the_description_claims_nothing_that_does_not_run():
    d = reg()["description"].lower()
    for banned in ("cannot fake", "accepted", "guarantee"):
        assert banned not in d, banned
    for stated in ("only the operator can request a record", "test network", "not a provek score"):
        assert stated in d, stated
