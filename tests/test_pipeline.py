"""End-to-end pipeline. We check PROPERTIES of the result, not that it exists."""
import subprocess
import tempfile
from pathlib import Path

import pytest

import src.pipeline as pipeline_module
from src.abs_profile.identity import Binding, BindingKind
from src.collector import declaration as decl
from src.collector.declaration import github_full_name
from src.collector.divergence import Divergence
from src.registry.public_registry import PublicRegistry
from src.transport.file_transport import FileTransport


@pytest.fixture(autouse=True)
def _no_network_declaration(monkeypatch):
    """`verify()` now also reads the subject's own `provek.json` (phase 2 accountability). Every
    test in this file exercises the rest of the pipeline against a LOCAL git repository with no
    real GitHub remote behind it, so `github_full_name` already returns `None` for all of them and
    no fetch is attempted - this stub is the second, belt-and-suspenders line of defence, for the
    tests further down that deliberately pass a GitHub-shaped remote."""
    monkeypatch.setattr(decl, "_fetch_raw", lambda full_name, ref: (404, "404: Not Found"))


def _repo(tmp: Path) -> Path:
    r = tmp / "r"
    r.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=r, check=True)
    subprocess.run(["git", "config", "user.email", "a@b.c"], cwd=r, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=r, check=True)
    (r / "m.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "-A"], cwd=r, check=True)
    subprocess.run(["git", "commit", "-qm", "c1"], cwd=r, check=True)
    return r


def test_end_to_end_produces_passport_and_publishes_it():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        res = pipeline_module.verify(
            str(_repo(p)), Binding(BindingKind.GIT, "a/b"),
            FileTransport(p / "out"), PublicRegistry(p / "reg"))
        assert Path(res.published_ref).exists()
        m = res.passport.to_machine()
        assert m["subject_id"] == "git:a/b"
        assert m["binding_strength"] == "weak"      # git is a weak binding, and that is visible


def test_unpresented_runtime_is_NOT_a_violation():
    """The core honesty: we do not accuse a subject of what we failed to measure."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        res = pipeline_module.verify(
            str(_repo(p)), Binding(BindingKind.GIT, "a/b"),
            FileTransport(p / "o"), PublicRegistry(p / "r"))
        assert res.divergence is Divergence.NOT_MEASURED
        assert any("not a violation" in f for f in res.findings)


def test_unmeasured_operations_are_reported_as_unmeasured_not_L0():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        res = pipeline_module.verify(
            str(_repo(p)), Binding(BindingKind.GIT, "a/b"),
            FileTransport(p / "o"), PublicRegistry(p / "r"))
        ops = {o["operation"]: o for o in res.passport.to_machine()["verified"]["operations"]}
        assert ops["treasury_control"]["measured"] is False
        assert ops["treasury_control"]["level"] != "L0"


def test_divergence_is_detected_when_deployed_differs():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        res = pipeline_module.verify(
            str(_repo(p)), Binding(BindingKind.GIT, "a/b"),
            FileTransport(p / "o"), PublicRegistry(p / "r"),
            deployed_digest="deadbeef")
        assert res.divergence is Divergence.DIVERGED
        assert any("DIVERGENCE" in f for f in res.findings)


def test_unreachable_subject_still_yields_an_honest_passport():
    """An unreachable subject neither crashes the pipeline nor turns into zeros."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        res = pipeline_module.verify(
            "/nope/x.git", Binding(BindingKind.DNS, "x.com"),
            FileTransport(p / "o"), PublicRegistry(p / "r"))
        m = res.passport.to_machine()
        assert m["verified"]["projection"] is None
        assert m["verified"]["projection_absent_reason"] is not None


def test_a_failed_clone_does_not_claim_github_was_inspected():
    """AUD-002 mutation control (part c of Fable's 2026-09-03 finding). Before this fix,
    `pipeline.verify` built coverage with `github_inspected=True` UNCONDITIONALLY - even when the
    clone above had just failed - so a subject whose repository could not be read at all still had
    its passport declare "Inspected: github" (the same B2 shape Fable already fixed in
    `scripts/cohort.py`, alive here as a second instance)."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        res = pipeline_module.verify(
            "/nope/x.git", Binding(BindingKind.DNS, "x.com"),
            FileTransport(p / "o"), PublicRegistry(p / "r"))
        coverage = res.passport.to_machine()["verified"]["coverage"]
        assert "github" not in coverage["inspected"]
        assert "github" in coverage["out_of_reach"]


def test_a_local_or_non_github_remote_skips_the_declaration_read_entirely():
    """A remote this collector cannot name a `provek.json` location for leaves accountability at
    its default - the check genuinely did not run, which is a different claim from `not_declared`
    (the channel WAS read and said nothing). Every test above already relies on this: `github_full_name`
    returns `None` for a local path, so none of them ever attempt the fetch this file stubs anyway."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        res = pipeline_module.verify(
            str(_repo(p)), Binding(BindingKind.GIT, "a/b"),
            FileTransport(p / "o"), PublicRegistry(p / "r"))
        acc = res.passport.to_machine()["accountability"]
        assert all(f["measured"] is False and f["reason"] == "check_did_not_run"
                  for f in acc.values())


@pytest.mark.parametrize("remote,expected", [
    ("https://github.com/whiteknightonhorse/apibase", "whiteknightonhorse/apibase"),
    ("https://github.com/whiteknightonhorse/apibase.git", "whiteknightonhorse/apibase"),
    ("git@github.com:whiteknightonhorse/apibase.git", "whiteknightonhorse/apibase"),
    ("/nope/x.git", None),
    ("https://gitlab.com/owner/repo", None),
])
def test_github_full_name_parses_only_github_remotes(remote, expected):
    assert github_full_name(remote) == expected


def test_a_github_remote_DOES_reach_the_declaration_mapper(monkeypatch):
    """The wiring test `github_full_name` alone cannot give: a GitHub-shaped `remote` must reach
    `apply_declaration`, pinned to the head_sha the base collector measured. Both `collect()` (the
    local clone, for `tree_digest`/divergence) and `collect_github()` (the API read AUD-002 added
    for scoring a GitHub remote) are stubbed so this stays offline - only the declaration fetch
    (already stubbed by the autouse fixture above) is what this test inspects."""
    from src.abs_profile.measured import Measurement
    from src.collector.github import GitHubEvidence
    from src.collector.repo import RepoEvidence

    fake_ev = RepoEvidence("https://github.com/whiteknightonhorse/apibase", "cafebabe",
                          Measurement(value=1.0), Measurement(value=1), "digest")
    monkeypatch.setattr(pipeline_module, "collect", lambda remote, **kw: fake_ev)
    fake_gh = GitHubEvidence("whiteknightonhorse/apibase", private=False, head_sha="cafebabe",
                             signed_commit_share=Measurement(value=1.0),
                             distinct_authors=Measurement(value=1),
                             bot_author_share=Measurement(value=0.0),
                             workflow_runs=Measurement(value=0),
                             identity_window_closed=Measurement(value=True))
    monkeypatch.setattr(pipeline_module, "collect_github", lambda full_name, *a, **kw: fake_gh)

    seen = {}

    def _spy(full_name, ref):
        seen["full_name"], seen["ref"] = full_name, ref
        return 404, "404: Not Found"
    monkeypatch.setattr(decl, "_fetch_raw", _spy)

    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        pipeline_module.verify(
            "https://github.com/whiteknightonhorse/apibase",
            Binding(BindingKind.GIT, "whiteknightonhorse/apibase"),
            FileTransport(p / "o"), PublicRegistry(p / "r"))

    assert seen == {"full_name": "whiteknightonhorse/apibase", "ref": "cafebabe"}


def test_a_github_remote_is_scored_through_platform_closure_not_just_the_local_clone(monkeypatch):
    """AUD-002 mutation control (part b). Before this fix, `pipeline.verify` scored EVERY remote -
    including a real github.com one - from `collect()`'s bare `git log`, which cannot see GitHub's
    bot flag or attribute an unsigned commit to a platform login. It therefore had no platform
    closure gate at all: a sole author with a high signed share reached L4 (`_observed_level` only
    checked `signed_commit_share`/`distinct_authors`) even when nothing vouched for the identity
    behind the unsigned commits - the ratified rule (Fable, 2026-08-25) that an OPEN identity window
    is a LOWER BOUND, not a count, and floors the level at L2.

    `runtime_trace` is forced true here (via `workflow_runs`) so the O2 weak-signal limiter cannot
    also produce L2 and mask whether the closure gate itself ran - this test isolates that one gate.
    """
    from src.abs_profile.measured import Measurement
    from src.collector.github import GitHubEvidence
    from src.collector.repo import RepoEvidence

    fake_ev = RepoEvidence("https://github.com/whiteknightonhorse/apibase", "cafebabe",
                          Measurement(value=1.0), Measurement(value=1), "digest")
    monkeypatch.setattr(pipeline_module, "collect", lambda remote, **kw: fake_ev)

    # SOLE_AUTHOR + a high signed share WOULD reach L4 under the old, closure-blind rule - see
    # `_observed_level`. The open window here must floor it at L2 regardless.
    fake_gh = GitHubEvidence("whiteknightonhorse/apibase", private=False, head_sha="cafebabe",
                             signed_commit_share=Measurement(value=1.0),
                             distinct_authors=Measurement(value=1),
                             bot_author_share=Measurement(value=0.0),
                             workflow_runs=Measurement(value=1),
                             identity_window_closed=Measurement(value=False))
    monkeypatch.setattr(pipeline_module, "collect_github", lambda full_name, *a, **kw: fake_gh)

    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        res = pipeline_module.verify(
            "https://github.com/whiteknightonhorse/apibase",
            Binding(BindingKind.GIT, "whiteknightonhorse/apibase"),
            FileTransport(p / "o"), PublicRegistry(p / "r"))

    ops = {o["operation"]: o for o in res.passport.to_machine()["verified"]["operations"]}
    assert ops["development_initiation"]["level"] == "L2"
