"""LAW-DEPLOY-LABEL-TRUE - the name a deployment carries must describe what was published.

THE TEST THIS FILE REFUSES TO BE. "`scripts/deploy_label.py` exists" and "it prints something on
this repository" are both satisfied by a script whose body is `print(sha)` - which is the exact
defect being fixed. So every case below puts a tree into a known state and asserts what the label
must and must NOT be, and the two load-bearing cases are the ones where the answer is a refusal and
where the answer must not contain the short sha at all.

WHY REAL `git init` REPOSITORIES AND NOT A STUBBED `git status`. The subject is a decision taken
FROM git's own output, and a stub would encode my belief about that output and then confirm it
(L-18: a test that builds its own subject cannot find the subject missing). These cost about a
tenth of a second each.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "deploy_label.py"

sys.path.insert(0, str(ROOT / "scripts"))
import deploy_label as dl  # noqa: E402


def _repo(tmp_path: pathlib.Path) -> pathlib.Path:
    """A git repository with one commit, so that `clean` is a state it can actually be in."""
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    (tmp_path / "README.md").write_text("seed\n", encoding="utf-8")
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "page.tsx").write_text("<p/>\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-qm", "seed"],
        cwd=tmp_path, check=True,
    )
    return tmp_path


def _head(repo: pathlib.Path) -> str:
    out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True,
                         check=True)
    return out.stdout.strip()


def test_a_clean_tree_is_labelled_with_the_commit_it_equals(tmp_path):
    repo = _repo(tmp_path)
    code, fields, dirty = dl.decide(repo, allow_dirty=False)
    assert code == dl.LABELLED
    assert dirty == []
    assert fields["LABEL"] == _head(repo)[:7]
    assert fields["COMMIT_HASH"] == _head(repo)
    assert fields["COMMIT_DIRTY"] == "false"


def test_a_dirty_tree_is_refused_by_default_and_the_paths_are_named(tmp_path):
    """THE CASE THIS GATE WAS WRITTEN FOR: a build from work no gate judged, under a commit's name.

    `dirty` is asserted by content rather than by length. A refusal that cannot say what it is
    refusing sends the operator to `git status` to find out, and this project has already paid for
    a report that named a count and not the thing counted (L-23).
    """
    repo = _repo(tmp_path)
    (repo / "web" / "page.tsx").write_text("<p>parked rewrite</p>\n", encoding="utf-8")
    code, fields, dirty = dl.decide(repo, allow_dirty=False)
    assert code == dl.DIRTY_REFUSED
    assert dirty == ["web/page.tsx"]
    assert fields == {}


def test_an_untracked_file_is_dirty_too(tmp_path):
    """Untracked and modified are different porcelain shapes, and `wrangler` uploads both."""
    repo = _repo(tmp_path)
    (repo / "web" / "extra.tsx").write_text("never committed\n", encoding="utf-8")
    code, _, dirty = dl.decide(repo, allow_dirty=False)
    assert code == dl.DIRTY_REFUSED
    assert dirty == ["web/extra.tsx"]


def test_the_operators_flag_publishes_but_the_label_stops_being_a_sha(tmp_path):
    """The half of the ruling that the permission alone would have thrown away.

    Asserting the short sha is ABSENT from every field the deployment carries is the whole point:
    a `--allow-dirty` that let `LABEL` keep saying `0538a90` would be the original defect with a
    flag in front of it.
    """
    repo = _repo(tmp_path)
    (repo / "web" / "page.tsx").write_text("<p>parked rewrite</p>\n", encoding="utf-8")
    code, fields, dirty = dl.decide(repo, allow_dirty=True)
    assert code == dl.LABELLED
    assert dirty == ["web/page.tsx"]
    assert fields["LABEL"].startswith(dl.DIRTY_PREFIX)
    assert fields["LABEL"] != _head(repo)[:7]
    assert _head(repo)[:7] not in fields["LABEL"]
    assert fields["COMMIT_DIRTY"] == "true"
    # The base commit may be NAMED in the message - it is a fact - but the message must say what
    # the sha does not describe, or the record is a sha with decoration.
    assert "does NOT describe what was published" in fields["COMMIT_MESSAGE"]
    assert fields["LABEL"] in fields["COMMIT_MESSAGE"]


def test_the_flag_does_not_relabel_a_clean_tree(tmp_path):
    """`--allow-dirty` is a permission, not a rename. A clean tree is still the commit it equals."""
    repo = _repo(tmp_path)
    code, fields, _ = dl.decide(repo, allow_dirty=True)
    assert code == dl.LABELLED
    assert fields["LABEL"] == _head(repo)[:7]
    assert fields["COMMIT_DIRTY"] == "false"


def test_the_digest_follows_the_content_and_nothing_else(tmp_path):
    """A label that did not move with the bytes would be a constant wearing a hash's clothes.

    Two directions, because only one of them is enough to pass by accident: the same content in a
    different repository must digest alike (the digest is over content, not over git's history),
    and one changed byte must move it.
    """
    a = _repo(tmp_path / "a")
    b = _repo(tmp_path / "b")
    assert dl.content_digest(a) == dl.content_digest(b)
    before = dl.content_digest(a)
    (a / "web" / "page.tsx").write_text("<p>one byte more</p>\n", encoding="utf-8")
    assert dl.content_digest(a) != before


def test_a_deleted_file_moves_the_digest_rather_than_failing_the_reading(tmp_path):
    """A deletion is a state of the CONTENT; an unreadable file is a failed instrument.

    Folding the first into the second would make every ordinary `git rm` in the tree look like a
    broken disk, and the operator would be sent to the wrong place.
    """
    repo = _repo(tmp_path)
    before = dl.content_digest(repo)
    (repo / "web" / "page.tsx").unlink()
    after = dl.content_digest(repo)
    assert after is not None
    assert after != before


def test_a_directory_that_is_not_a_repository_is_not_labelled_at_all(tmp_path):
    """Invariant 1 on the outward name: `unreadable` is neither a clean sha nor a refusal.

    WHAT THIS CASE DOES AND DOES NOT PROVE, because the first draft of it claimed the second.
    Outside a repository BOTH readings fail - `git status` and `git rev-parse HEAD` - so this
    passes against code that checks only the second, and the docstring here originally said it
    proved "no paths is not clean". It does not; the case below does. Left in place because a
    caller does point this script at a non-repository by mistake, and the answer must still be a
    named third state rather than a traceback.
    """
    not_a_repo = tmp_path / "elsewhere"
    not_a_repo.mkdir()
    code, fields, _ = dl.decide(not_a_repo, allow_dirty=False)
    assert code == dl.UNREADABLE
    assert code not in (dl.LABELLED, dl.DIRTY_REFUSED)
    assert fields == {}


def test_a_status_that_could_not_be_read_is_not_a_clean_tree(tmp_path, monkeypatch):
    """THE CASE THAT DECIDES WHETHER THE MODULE IS HONEST, and it is here because it was missing.

    `_porcelain` returns None for "we could not ask", and code that treated that as an empty dirty
    list would hand out a commit's short sha over content it never read - a name earned by a check
    that did not run. That mutation was applied to `decide` and the whole suite stayed GREEN,
    because every other unreadable case above is ALSO an unreadable HEAD and was caught by the
    second half of the same condition. The red run is kept in `evidence/RED-023-*`.

    The instrument is stubbed and the SUBJECT is not: what is under test is the branch `decide`
    takes when a reading fails, not git's output format, which the cases above exercise for real.
    A repository that git can read but cannot `status` is not constructible on this host - the one
    candidate, an unreadable subdirectory, makes git warn and exit 0 (see the module docstring's
    named limit) - so refusing to test the branch would mean leaving the module's load-bearing
    state to a mutation nobody ran.
    """
    repo = _repo(tmp_path)
    monkeypatch.setattr(dl, "_porcelain", lambda root: None)
    for flag in (False, True):
        code, fields, dirty = dl.decide(repo, allow_dirty=flag)
        assert code == dl.UNREADABLE, f"allow_dirty={flag}"
        assert fields == {}
        assert dirty == []


def test_the_flag_cannot_turn_an_unreadable_tree_into_a_publishable_one(tmp_path):
    """The permission is over uncommitted work, not over the absence of a measurement."""
    not_a_repo = tmp_path / "elsewhere"
    not_a_repo.mkdir()
    code, fields, _ = dl.decide(not_a_repo, allow_dirty=True)
    assert code == dl.UNREADABLE
    assert fields == {}


@pytest.mark.parametrize(
    ("state", "flag", "expected"),
    [
        ("clean", [], dl.LABELLED),
        ("dirty", [], dl.DIRTY_REFUSED),
        ("dirty", ["--allow-dirty"], dl.LABELLED),
        ("unreadable", [], dl.UNREADABLE),
        ("unreadable", ["--allow-dirty"], dl.UNREADABLE),
    ],
)
def test_the_exit_code_and_the_fields_reach_the_caller(tmp_path, state, flag, expected):
    """`deploy.sh` branches on the PROCESS exit code and reads the PROCESS stdout.

    Those are the artefacts the shell sees, and a `main()` that returned the right tuple while
    printing nothing - or printing on a refusal - would satisfy every test above and still hand
    `deploy.sh` an empty label to publish under.

    The repository is a SIBLING of `elsewhere`, not its parent: a directory created inside a git
    repository is readable by git, so nesting it would silently measure a clean tree instead of an
    unreadable one. That mistake cost a red run in `evidence/RED-022-*` on the neighbouring gate.
    """
    repo = _repo(tmp_path / "repo")
    if state == "dirty":
        (repo / "README.md").write_text("parked\n", encoding="utf-8")
    target = repo if state != "unreadable" else tmp_path / "elsewhere"
    if state == "unreadable":
        target.mkdir()

    done = subprocess.run([sys.executable, str(GATE), "--root", str(target), *flag],
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == expected, done.stderr

    if expected != dl.LABELLED:
        assert done.stdout == "", "a refusal that prints a label is a label the shell will use"
        return
    printed = dict(line.split("=", 1) for line in done.stdout.splitlines())
    assert set(printed) == {"LABEL", "COMMIT_HASH", "COMMIT_DIRTY", "COMMIT_MESSAGE"}
    assert printed["LABEL"]
    if state == "dirty":
        assert printed["LABEL"].startswith(dl.DIRTY_PREFIX)
        assert printed["COMMIT_DIRTY"] == "true"
    else:
        assert printed["LABEL"] == _head(repo)[:7]
        assert printed["COMMIT_DIRTY"] == "false"


# A `chmod 000` means nothing to root, so the two cases below cannot express their own subject
# there. This is the one skip in this file and it is conditional on a MEASURED property of the
# runtime rather than on whether a fixture happened to build - the shape L-16 warns about is a
# check that quietly does nothing on the host where it matters, and this one is armed on this host
# and on the CI runner, both of which are unprivileged.
_needs_permissions = pytest.mark.skipif(
    os.geteuid() == 0, reason="root ignores the permission bits these two cases are made of")


@_needs_permissions
def test_a_tracked_file_under_an_unenterable_directory_is_unreadable_not_clean(tmp_path):
    """THE STATE THE CLEAN PATH'S DIGEST EXISTS FOR, and it is not the one that was predicted.

    `git status` does not fail on a directory it cannot enter - it warns and exits 0 with the
    subtree simply missing from its output - so the tree LOOKS clean and would be signed with a
    commit's short sha over content nothing read. The digest's reading is the only thing between
    those two facts, and this case is what proves it is doing the work: delete the call and the
    tree below is labelled `<short sha>`, clean, confidently.
    """
    repo = _repo(tmp_path)
    locked = repo / "locked"
    locked.mkdir()
    (locked / "inside.txt").write_text("tracked, and about to become unreachable\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t",
                    "commit", "-qm", "second"], cwd=repo, check=True)
    locked.chmod(0o000)
    try:
        # The fixture asserts its own premise: if git could see in there, this case would be
        # measuring an ordinary clean tree and passing for the wrong reason.
        assert dl._porcelain(repo) == [], "git reported the locked subtree; the fixture is not the state it claims"
        code, fields, _ = dl.decide(repo, allow_dirty=False)
        assert code == dl.UNREADABLE
        assert fields == {}
    finally:
        locked.chmod(0o755)


@_needs_permissions
def test_an_unreadable_file_is_refused_as_dirty_which_is_honest_and_misleading(tmp_path):
    """The other half, pinned because it is the confusing one and it should not change silently.

    git cannot compare an unreadable file to the index, so it reports it MODIFIED and the tree is
    refused as dirty before the digest ever runs. The refusal is correct - the tree cannot be shown
    equal to HEAD - but the wording sends the operator to look for uncommitted work. Asserted here
    so that the day someone improves it, this test is what tells them the old behaviour was known
    rather than accidental.
    """
    repo = _repo(tmp_path)
    target = repo / "README.md"
    target.chmod(0o000)
    try:
        code, _, dirty = dl.decide(repo, allow_dirty=False)
        assert code == dl.DIRTY_REFUSED
        assert dirty == ["README.md"]
    finally:
        target.chmod(0o644)
