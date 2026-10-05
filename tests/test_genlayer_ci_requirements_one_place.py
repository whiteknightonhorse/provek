"""T-GL-07a - the mirror's copy of the GenLayer pin set cannot drift from the root's (D-64).

WHY A COPY EXISTS AT ALL. `integrations/genlayer-witness/` is published on its own as a
`git subtree split` mirror (D-64). In the mirror that directory is the repository root, so its CI
(`.github/workflows/contract-tests.yml`) asks for `requirements/ci-genlayer.txt` relative to it.
This repository's own gate asks for the root `requirements/ci-genlayer.txt`. Two files, one
meaning - a rule written in more than one place (L-2) - so the second is admitted only under this
law: the two are byte-identical, and a commit that changes one without the other is red.

UNREADABLE IS NOT EQUAL (invariant 1). Two files that both failed to read are not "equal"; a
missing or empty file is a red of its own, named, rather than a vacuous byte-comparison pass.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROOT_COPY = ROOT / "requirements" / "ci-genlayer.txt"
MIRROR_COPY = ROOT / "integrations" / "genlayer-witness" / "requirements" / "ci-genlayer.txt"


def _read(path: pathlib.Path) -> bytes:
    assert path.is_file(), f"{path.relative_to(ROOT)} does not exist"
    data = path.read_bytes()
    assert data, f"{path.relative_to(ROOT)} is empty - an empty pin set is not a pin set"
    return data


def test_the_two_copies_of_the_genlayer_pin_set_are_byte_identical():
    assert _read(ROOT_COPY) == _read(MIRROR_COPY), (
        "requirements/ci-genlayer.txt and "
        "integrations/genlayer-witness/requirements/ci-genlayer.txt differ - copy the root file "
        "over the mirror one (D-64)"
    )
