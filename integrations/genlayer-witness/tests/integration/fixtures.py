"""Named, reusable fixtures for integration tests — see `gltest.helpers.load_fixture`.

`load_fixture` snapshots and restores state only against a LOCAL node; against a hosted network
(Studionet, Testnet Bradbury) it simply calls the fixture function fresh each time
(`gltest_cli`'s own `check_local_rpc()`), which is what every test in this suite relies on: each
test gets its OWN freshly deployed contract, so `witness()`'s duplicate-id and operator-only
checks never collide across tests in the same run.
"""
from gltest import get_contract_factory, get_default_account
from gltest.types import CalldataAddress


def deploy_provek_evidence_witness():
    """Deploy a fresh `ProvekEvidenceWitness` with the default account as its `operator`.

    `get_contract_factory` resolves by CLASS NAME (`ast.ClassDef.name`, see
    `gltest.artifacts.contract.search_path_by_class_name`), not by file stem — the file is
    `provek_evidence_witness.py` but the class is `ProvekEvidenceWitness`.

    `operator: Address` on the contract side means the constructor arg must cross the calldata
    boundary as an address value, not a plain string: `CalldataAddress` is the one
    `CalldataEncodable` the calldata encoder emits as `SPECIAL_ADDR` (`str` encodes as
    `TYPE_STR` instead, which `Address(...)` storage cannot accept — the same TYPE_STR/TYPE_BYTES
    failure class `tests/direct/conftest.py`'s `deploy_witness_contract` docstring names for the
    direct-mode harness).
    """
    account = get_default_account()
    factory = get_contract_factory("ProvekEvidenceWitness")
    return factory.deploy(args=[CalldataAddress(account.address)])
