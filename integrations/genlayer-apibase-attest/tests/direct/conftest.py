"""Shared fixtures for direct-mode tests of `ApibaseReceiptAttest`.

Fixtures `direct_vm`, `direct_deploy`, `direct_alice`, ... come from `genlayer-test`'s own pytest
plugin; this file adds only what this contract's suite needs on top. The deploy has to build the
operator `Address` AFTER `setup_sdk_paths` has made it importable — the same reason, spelled out in
full, in `integrations/genlayer-witness/tests/direct/conftest.py`.
"""
from pathlib import Path

import pytest

CONTRACT_PATH = Path(__file__).resolve().parent.parent.parent / "contracts" / "apibase_receipt_attest.py"
RECEIPT_BASE_URL = "https://receipts.example/r/"
BASE_RPC_URL = "https://rpc.example/base"
BASE_USDC = "0x833589fCd6eDb6E08f4c7C32D4f71b54bdA02913"


@pytest.fixture
def deploy_attest_contract(direct_vm, direct_deploy):
    """Factory: deploy a fresh `ApibaseReceiptAttest` operated by the VM's default sender. Use it
    directly when the deploy must come after `direct_vm.warp(...)` (the direct harness captures
    `gl.message_raw` once, at deploy time)."""
    from gltest.direct.sdk_loader import setup_sdk_paths
    from gltest.direct.loader import create_address

    def _deploy():
        setup_sdk_paths(CONTRACT_PATH)
        operator = create_address("default_sender")
        return direct_deploy(str(CONTRACT_PATH), operator, RECEIPT_BASE_URL)

    return _deploy


@pytest.fixture
def bare_contract(deploy_attest_contract):
    """A deployed contract with NO chain configured."""
    return deploy_attest_contract()


@pytest.fixture
def attest_contract(bare_contract):
    """A deployed contract with Base (8453) configured, as the operator."""
    bare_contract.set_chain("8453", BASE_RPC_URL, BASE_USDC)
    return bare_contract


@pytest.fixture
def contract_module(bare_contract):
    """The already-imported contract module, for tests of its pure helpers."""
    import sys
    return sys.modules[f"_contract_{CONTRACT_PATH.stem}"]


# --- T-GD-01: the two dispute contracts (receipt claim, payment claim) ---------------------------
CONTRACTS_DIR = CONTRACT_PATH.parent
RECEIPT_DISPUTE_PATH = CONTRACTS_DIR / "apibase_receipt_dispute.py"
PAYMENT_DISPUTE_PATH = CONTRACTS_DIR / "apibase_payment_dispute.py"
PAYEE = "0x781dfd3f2687f8e5656313b2179fdefdf99d339d"  # recipient of the real Base USDC transfer fixture
POLICY_VERSION = "refund-policy-1"
POLICY_SHA256 = "ab" * 32


def _deploy_at(direct_deploy, path):
    from gltest.direct.sdk_loader import setup_sdk_paths
    from gltest.direct.loader import create_address

    setup_sdk_paths(path)
    return direct_deploy(str(path), create_address("default_sender"), RECEIPT_BASE_URL)


@pytest.fixture
def deploy_receipt_dispute_contract(direct_vm, direct_deploy):
    """Factory: a fresh `ApibaseReceiptDispute`, no policy set."""
    return lambda: _deploy_at(direct_deploy, RECEIPT_DISPUTE_PATH)


@pytest.fixture
def receipt_dispute_contract(deploy_receipt_dispute_contract):
    """A deployed `ApibaseReceiptDispute` with the refund policy set, as the operator."""
    contract = deploy_receipt_dispute_contract()
    contract.set_policy(POLICY_VERSION, POLICY_SHA256)
    return contract


@pytest.fixture
def deploy_payment_dispute_contract(direct_vm, direct_deploy):
    """Factory: a fresh `ApibasePaymentDispute`, no chain and no policy."""
    return lambda: _deploy_at(direct_deploy, PAYMENT_DISPUTE_PATH)


@pytest.fixture
def payment_dispute_contract(deploy_payment_dispute_contract):
    """A deployed `ApibasePaymentDispute` with Base (8453) + payee and the policy set."""
    contract = deploy_payment_dispute_contract()
    contract.set_chain("8453", BASE_RPC_URL, BASE_USDC, PAYEE)
    contract.set_policy(POLICY_VERSION, POLICY_SHA256)
    return contract


@pytest.fixture
def receipt_dispute_module(receipt_dispute_contract):
    import sys
    return sys.modules[f"_contract_{RECEIPT_DISPUTE_PATH.stem}"]


@pytest.fixture
def payment_dispute_module(payment_dispute_contract):
    import sys
    return sys.modules[f"_contract_{PAYMENT_DISPUTE_PATH.stem}"]
