"""Shared fixtures for direct-mode tests of `ProvekEvidenceWitness`.

Fixtures `direct_vm`, `direct_deploy`, `direct_owner`, `direct_alice`, ... come from
`genlayer-test`'s own pytest plugin (registered via its `pytest11` entry point) — this file adds
only what this contract's own test suite needs on top of that.
"""
from pathlib import Path

import pytest

CONTRACT_PATH = Path(__file__).resolve().parent.parent.parent / "contracts" / "provek_evidence_witness.py"


@pytest.fixture
def deploy_witness_contract(direct_vm, direct_deploy):
    """Factory fixture: deploy a fresh `ProvekEvidenceWitness`, operated by a freshly-built
    `Address`, on demand. Most tests want the `witness_contract` convenience fixture below
    instead; use this factory directly when the deploy itself must happen at a specific point —
    e.g. AFTER `direct_vm.warp(...)`, since `gl.message_raw["datetime"]` is captured once, at
    deploy/import time, by this direct-mode harness (there is no per-call re-injection the way a
    real GenVM re-executes a transaction fresh each time) — warping after an existing instance was
    already deployed has no effect on that instance.

    Deliberately does NOT use the `direct_owner` fixture for the operator address:
    `direct_owner`/`direct_alice`/`direct_bob` are resolved by `create_address()` before any
    contract's SDK paths are on `sys.path`, so `from genlayer.py.types import Address` inside
    `create_address` fails and it falls back to plain `bytes` (see its own `except ImportError`
    branch). That is harmless when such a fixture is later assigned to `direct_vm.sender`/
    `.prank()` — `VMContext._refresh_gl_message` heals bytes into a real `Address` at that point,
    once `genlayer.gl` is loaded — but it is NOT harmless as a raw constructor argument, which
    goes through `calldata` encode/decode instead and has no such healing step: a plain `bytes`
    object encodes as `TYPE_BYTES`, not the special `Address` form, and the contract's
    `operator: Address` storage field then fails to store it. Calling `setup_sdk_paths` here first
    (the exact same call `direct_deploy` makes internally) makes `Address` importable before
    `create_address()` runs, so it returns the real thing.
    """
    from gltest.direct.sdk_loader import setup_sdk_paths
    from gltest.direct.loader import create_address

    def _deploy():
        setup_sdk_paths(CONTRACT_PATH)
        operator = create_address("default_sender")
        return direct_deploy(str(CONTRACT_PATH), operator)

    return _deploy


@pytest.fixture
def witness_contract(deploy_witness_contract):
    """Convenience: a `ProvekEvidenceWitness` deployed with the VM's default (real wall-clock)
    datetime — use `deploy_witness_contract` directly instead when the deploy must happen after a
    `direct_vm.warp(...)` call."""
    return deploy_witness_contract()


@pytest.fixture
def contract_module(witness_contract):
    """The already-imported contract module (registered by `direct_deploy` as
    `sys.modules["_contract_provek_evidence_witness"]`) — used by tests that check the module's
    own pure helper functions (`_judge`, `_url_reachable_digest`, ...) directly, without going
    through a contract method call. Depends on `witness_contract` only to guarantee the deploy
    (and therefore the module import) has already happened."""
    import sys
    return sys.modules[f"_contract_{CONTRACT_PATH.stem}"]
