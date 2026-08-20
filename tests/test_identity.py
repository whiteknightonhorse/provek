"""ABI-12-7 plus revision 1.2: binding strength is visible, continuity needs a cross-signature."""
from src.abs_profile.identity import EXPIRABLE, Binding, BindingKind, Strength, continuity_preserved


def test_bindings_are_NOT_equally_strong():
    """A domain expires and gets resold - equating it with token ownership is a lie."""
    assert Binding(BindingKind.ERC8004, "42").strength is Strength.STRONG
    assert Binding(BindingKind.DNS, "example.com").strength is Strength.WEAK
    assert Binding(BindingKind.GIT, "github.com/x/y").strength is Strength.WEAK


def test_weak_binding_declares_WHY_it_is_weak():
    assert EXPIRABLE in Binding(BindingKind.DNS, "example.com").flags


def test_subject_id_names_its_binding_kind():
    """A passport reader must see the basis, not just a string."""
    assert Binding(BindingKind.ERC8004, "42").as_subject_id() == "erc8004:42"


def test_reputation_does_not_survive_rebinding_without_cross_signature():
    """Otherwise rebinding becomes cheap reputation laundering (attack T10)."""
    a, b = Binding(BindingKind.DNS, "old.com"), Binding(BindingKind.ERC8004, "7")
    assert continuity_preserved(a, b, cross_signature=True) is True
    assert continuity_preserved(a, b, cross_signature=False) is False
