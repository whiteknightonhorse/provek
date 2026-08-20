"""T-2.15a - the ERC-8004 read adapter is honest about what it did not read."""
import pytest

from src.abs_profile.measured import NotMeasured
from src.transport.erc8004 import Erc8004Transport, RegistryConfig, read_identity


def test_unconfigured_registry_is_CHECK_DID_NOT_RUN_not_empty():
    """"We never asked" and "the registry is empty" are different states of the world."""
    r = read_identity(RegistryConfig(), 1)
    assert r.owner.is_measured is False
    assert r.owner.absent is NotMeasured.CHECK_DID_NOT_RUN
    assert r.notes and "never asked" in r.notes[0]


def test_configuration_is_a_state_not_a_default():
    assert RegistryConfig().is_configured is False
    assert RegistryConfig(rpc_url="http://x", identity_registry="0xabc").is_configured is True


def test_unreachable_rpc_yields_UNREADABLE_not_zero():
    """An unreachable node must never look like an identity with owner 0."""
    cfg = RegistryConfig(rpc_url="http://127.0.0.1:1", identity_registry="0xdead")
    r = read_identity(cfg, 7)
    assert r.owner.is_measured is False
    assert r.owner.absent is NotMeasured.UNREADABLE
    assert any("ownerOf" in n for n in r.notes)


def test_onchain_publication_REFUSES_loudly_rather_than_doing_nothing():
    """A transport that silently does nothing yields a passport nobody can find."""
    t = Erc8004Transport(RegistryConfig())
    with pytest.raises(NotImplementedError) as e:
        t.publish("erc8004:1", {}, 80)
    assert "T-2.15b" in str(e.value)


def test_selectors_are_declared_not_guessed():
    from src.transport import erc8004
    assert erc8004.SELECTOR_OWNER_OF == "0x6352211e"
    assert erc8004.SELECTOR_TOKEN_URI == "0xc87b56dd"
