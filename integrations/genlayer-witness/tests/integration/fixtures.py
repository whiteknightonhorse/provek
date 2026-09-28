"""Named, reusable fixtures for integration tests — see `gltest.helpers.load_fixture`.

`load_fixture` snapshots and restores state only against a LOCAL node; against a hosted network
(Studionet, Testnet Bradbury) it simply calls the fixture function fresh each time
(`gltest_cli`'s own `check_local_rpc()`), which is what every test in this suite relies on: each
test gets its OWN freshly deployed contract, so `witness()`'s duplicate-id and operator-only
checks never collide across tests in the same run.
"""
from gltest import get_contract_factory, get_default_account


def deploy_provek_evidence_witness():
    """Deploy a fresh `ProvekEvidenceWitness` with the default account as its `operator`."""
    account = get_default_account()
    factory = get_contract_factory("provek_evidence_witness")
    return factory.deploy(args=[account.address])
