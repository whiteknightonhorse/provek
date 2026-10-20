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
