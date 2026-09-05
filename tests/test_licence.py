"""T-PROFILE-2 — the licence exists, is the one the specification names, and covers both halves.

Specification 4.4-bis, requirement ABI-20-5: the profile text is CC BY 4.0, the schemas and test
vectors are Apache-2.0, and **openness without a licence is legally undefined**. The project told
readers on every page that its methodology was "published in full" for a day and a half while
carrying no licence at all - publication in the legally undefined sense the specification
explicitly forbids.

This checks the files rather than the intention, because a licence named only in prose is the kind
that turns out to be missing when someone actually needs to rely on it.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROFILE = "CC-BY-4.0"
CODE = "Apache-2.0"


def test_the_licence_files_exist():
    for name in ("LICENSE", "LICENSE-CC-BY-4.0", "LICENSE-APACHE-2.0"):
        assert (ROOT / name).exists(), f"{name} is missing"


def test_both_spdx_identifiers_are_named_exactly():
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert f"SPDX-License-Identifier: {PROFILE}" in text
    assert f"SPDX-License-Identifier: {CODE}" in text


def test_the_full_texts_are_the_real_ones_not_a_summary():
    """A three-line paraphrase of a licence is not that licence."""
    cc = (ROOT / "LICENSE-CC-BY-4.0").read_text(encoding="utf-8")
    ap = (ROOT / "LICENSE-APACHE-2.0").read_text(encoding="utf-8")
    assert "Attribution 4.0 International" in cc and len(cc) > 10_000
    assert "Apache License" in ap and "Version 2.0" in ap and len(ap) > 8_000


def test_the_split_names_which_half_is_which():
    """A dual licence that does not say what each half covers is one unanswered question."""
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    for path in ("src/", "tests/", "web/", "templates/"):
        assert path in text, f"the code licence does not name {path}"
    for doc in ("SPEC.md", "DECISIONS.md", "docs/"):
        assert doc in text, f"the profile licence does not name {doc}"


def test_the_templates_directory_carries_its_own_licence():
    """ADR-0011: templates/ may be extracted into its own repository later and must carry its
    own terms when it travels, rather than relying on a reader having also fetched the root."""
    tpl = (ROOT / "templates" / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in tpl and "Version 2.0" in tpl and len(tpl) > 8_000


def test_the_unlicensed_part_is_stated_rather_than_left_ambiguous():
    """A-8: the evidence corpus and the issuer's reputation do not travel with the text."""
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "WHAT IS NOT LICENSED" in text
    assert "corpus of evidence" in text


def test_the_public_surface_states_the_licence():
    """A reader who never opens the repository must still be able to learn the terms."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert PROFILE in readme and CODE in readme, "README does not name both licences"
