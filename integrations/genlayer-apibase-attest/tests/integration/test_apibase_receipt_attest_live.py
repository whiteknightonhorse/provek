"""Live tests for `ApibaseReceiptAttest` against a real GenLayer network — NOT run at the door or in CI.

Skipped unless BOTH `ATTEST_CONTRACT` (address of the deployed contract) and `APIBASE_RECEIPT_ID`
(a real, billed, x402-base APIbase receipt id) are set. Run explicitly:

    cd integrations/genlayer-apibase-attest
    ATTEST_CONTRACT=0x... APIBASE_RECEIPT_ID=... gltest --network studionet tests/integration -v -s

As in the witness suite, a view call here returns values that crossed the calldata boundary:
`Attestation` comes back as a plain `dict`, not a dataclass instance.
"""
import json

import pytest
from gltest.assertions import tx_execution_succeeded

from .fixtures import attach_apibase_receipt_attest, live_settings

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(live_settings() is None, reason="ATTEST_CONTRACT and APIBASE_RECEIPT_ID are not both set"),
]


def test_a_real_receipt_is_attested_and_readable_back():
    address, receipt_id = live_settings()
    contract = attach_apibase_receipt_attest(address)

    receipt = contract.attest(args=[receipt_id]).transact()
    assert tx_execution_succeeded(receipt)

    attest_ids = json.loads(contract.list_by_receipt(args=[receipt_id]).call())
    assert len(attest_ids) >= 1
    record = contract.get_attestation(args=[attest_ids[-1]]).call()
    assert record["receipt_id"] == receipt_id
    assert record["result"] in ("PASS", "FAIL", "NOT_FOUND")
