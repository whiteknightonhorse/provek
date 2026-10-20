"""Named fixtures for the live `ApibaseReceiptAttest` tests (see `gltest.helpers.load_fixture`).

Unlike the witness suite, nothing is deployed here: the contract under test is the one already
deployed by T-GA-02, named by the `ATTEST_CONTRACT` variable, and the receipt it is asked about is
named by `APIBASE_RECEIPT_ID`. Either one unset means the live test is skipped — the door and CI
only ever *collect* this directory.
"""
import os

from gltest import get_contract_factory


def live_settings():
    """`(contract_address, receipt_id)` from the process variables, or `None` if either is unset."""
    address = os.getenv("ATTEST_CONTRACT", "")
    receipt_id = os.getenv("APIBASE_RECEIPT_ID", "")
    if not address or not receipt_id:
        return None
    return address, receipt_id


def attach_apibase_receipt_attest(address: str):
    """A handle on the already-deployed contract. `get_contract_factory` resolves by CLASS NAME
    (`ApibaseReceiptAttest`), not by file stem."""
    return get_contract_factory("ApibaseReceiptAttest").build_contract(address)
