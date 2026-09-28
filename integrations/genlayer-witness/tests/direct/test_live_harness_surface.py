"""Offline surface tests for the call FORM `tests/integration/`'s live-network tests must use —
no network, no `gltest --network studionet` run. See `GL-05-call-signature.ruling-1.md`.

`gltest.contracts.contract.contract_function_factory` builds bound methods of the shape
`lambda self, args=None: ...` (`gltest/contracts/contract.py` — there is no `kwargs=` parameter at
all). `tests/direct/`'s own tests call contract methods positionally
(`witness_contract.witness("a", "b", ...)`), but that goes through a DIFFERENT wrapper —
`gltest.direct.loader._make_contract_proxy` — not `gltest.contracts.Contract`. The live tests in
`tests/integration/` go through `gltest.contracts.Contract` (`load_fixture` / `get_contract_factory`
return one), so copying the direct-mode call form there raises `TypeError` against a real network —
exactly what the dispatcher's Studionet run reproduced.

Building a `Contract` and a `ContractFunction` never touches the network by itself: the closures
`read_contract_wrapper`/`write_contract_wrapper` only call `get_gl_client()` from INSIDE
`call_method`/`transact_method`, which run when `.call()`/`.transact()` is invoked — never here.
"""
import ast
import inspect
from pathlib import Path

import pytest

from gltest.contracts import Contract
from gltest.contracts.contract_functions import ContractFunction
from gltest.direct.loader import _find_contract_class

INTEGRATION_DIR = Path(__file__).resolve().parent.parent / "integration"


def _schema_for(contract_module):
    """Derive the real ABI schema from the already-deployed contract class instead of hand-typing
    method names — `get_schema` is the exact function GenVM itself uses to build a contract's
    schema, so this cannot go stale silently if a method is renamed, added, or removed."""
    from genlayer.py.get_schema import get_schema

    contract_cls = _find_contract_class(contract_module)
    assert contract_cls is not None, "no contract class found in the deployed module"
    return get_schema(contract_cls)


@pytest.fixture
def live_contract(contract_module):
    """A real `gltest.contracts.Contract` — the class the live tests call through — built from the
    real schema, with a placeholder address/account since nothing here transacts or calls."""
    schema = _schema_for(contract_module)
    return Contract.new(address="0x" + "00" * 20, schema=schema, account=None)


def test_positional_call_raises_type_error(live_contract):
    with pytest.raises(TypeError):
        live_contract.witness("a", "b", "c", "d")


def test_args_kwarg_call_returns_a_contract_function(live_contract):
    result = live_contract.witness(args=["a", "b", "c", "d"])
    assert isinstance(result, ContractFunction)


def _integration_files():
    files = sorted(p for p in INTEGRATION_DIR.glob("*.py"))
    assert files, f"no .py files found under {INTEGRATION_DIR}"
    return files


def _iter_transact_or_call_sites(tree):
    """Yield every `ast.Call` node of the form `<expr>(...).transact(...)` / `<expr>(...).call(...)`
    — the `<expr>(...)` inner call is the contract-method call whose FORM this task fixes."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in ("transact", "call"):
            continue
        inner = node.func.value
        if not isinstance(inner, ast.Call):
            continue
        yield node, inner


def test_integration_call_sites_use_args_kwarg_only():
    """AST check over `tests/integration/*.py`: every contract-method call chained into
    `.transact()`/`.call()` passes zero positional arguments and only `args=`/`kwargs=` keywords —
    the one form `contract_function_factory`'s bound methods actually accept."""
    checked_any = False
    for path in _integration_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for _outer, inner in _iter_transact_or_call_sites(tree):
            checked_any = True
            assert not inner.args, (
                f"{path.name}:{inner.lineno}: positional argument(s) passed to a contract "
                f"method ({ast.dump(inner)})"
            )
            bad_keys = [kw.arg for kw in inner.keywords if kw.arg not in ("args", "kwargs")]
            assert not bad_keys, f"{path.name}:{inner.lineno}: unexpected keyword(s) {bad_keys}"
    assert checked_any, "no chained contract call found under tests/integration/ — check is vacuous"


def test_wait_kwargs_used_by_the_live_tests_are_real_transact_call_parameters():
    """Every kwarg a live test passes to `.transact()`/`.call()` (`wait_transaction_status`,
    `wait_retries`, `wait_interval`, ...) must be a real parameter of the PINNED gltest's
    `ContractFunction.transact`/`.call` — read via `inspect.signature`, not assumed."""
    transact_params = set(inspect.signature(ContractFunction.transact).parameters) - {"self"}
    call_params = set(inspect.signature(ContractFunction.call).parameters) - {"self"}
    checked_any = False
    for path in _integration_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for outer, _inner in _iter_transact_or_call_sites(tree):
            checked_any = True
            allowed = transact_params if outer.func.attr == "transact" else call_params
            used = {kw.arg for kw in outer.keywords if kw.arg is not None}
            unknown = used - allowed
            assert not unknown, (
                f"{path.name}:{outer.lineno}: .{outer.func.attr}() kwarg(s) {sorted(unknown)} "
                f"are not in the pinned gltest signature {sorted(allowed)}"
            )
    assert checked_any, "no chained contract call found under tests/integration/ — check is vacuous"
