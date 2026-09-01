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
from src.pipeline import verify
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
        res = verify(str(_repo(p)), Binding(BindingKind.GIT, "a/b"),
                     FileTransport(p / "out"), PublicRegistry(p / "reg"))
        assert Path(res.published_ref).exists()
        m = res.passport.to_machine()
        assert m["subject_id"] == "git:a/b"
        assert m["binding_strength"] == "weak"      # git is a weak binding, and that is visible


def test_unpresented_runtime_is_NOT_a_violation():
    """The core honesty: we do not accuse a subject of what we failed to measure."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        res = verify(str(_repo(p)), Binding(BindingKind.GIT, "a/b"),
                     FileTransport(p / "o"), PublicRegistry(p / "r"))
        assert res.divergence is Divergence.NOT_MEASURED
        assert any("not a violation" in f for f in res.findings)


def test_unmeasured_operations_are_reported_as_unmeasured_not_L0():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        res = verify(str(_repo(p)), Binding(BindingKind.GIT, "a/b"),
                     FileTransport(p / "o"), PublicRegistry(p / "r"))
        ops = {o["operation"]: o for o in res.passport.to_machine()["verified"]["operations"]}
        assert ops["treasury_control"]["measured"] is False
        assert ops["treasury_control"]["level"] != "L0"


def test_divergence_is_detected_when_deployed_differs():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        res = verify(str(_repo(p)), Binding(BindingKind.GIT, "a/b"),
                     FileTransport(p / "o"), PublicRegistry(p / "r"),
                     deployed_digest="deadbeef")
        assert res.divergence is Divergence.DIVERGED
        assert any("DIVERGENCE" in f for f in res.findings)


def test_unreachable_subject_still_yields_an_honest_passport():
    """An unreachable subject neither crashes the pipeline nor turns into zeros."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        res = verify("/nope/x.git", Binding(BindingKind.DNS, "x.com"),
                     FileTransport(p / "o"), PublicRegistry(p / "r"))
        m = res.passport.to_machine()
        assert m["verified"]["projection"] is None
        assert m["verified"]["projection_absent_reason"] is not None


def test_a_local_or_non_github_remote_skips_the_declaration_read_entirely():
    """A remote this collector cannot name a `provek.json` location for leaves accountability at
    its default - the check genuinely did not run, which is a different claim from `not_declared`
    (the channel WAS read and said nothing). Every test above already relies on this: `github_full_name`
    returns `None` for a local path, so none of them ever attempt the fetch this file stubs anyway."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        res = verify(str(_repo(p)), Binding(BindingKind.GIT, "a/b"),
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
    `apply_declaration`, pinned to the head_sha the base collector measured. `collect()` itself is
    stubbed so this stays offline - only the declaration fetch (already stubbed by the autouse
    fixture above) is what this test inspects."""
    from src.abs_profile.measured import Measurement
    from src.collector.repo import RepoEvidence

    fake_ev = RepoEvidence("https://github.com/whiteknightonhorse/apibase", "cafebabe",
                          Measurement(value=1.0), Measurement(value=1), "digest")
    monkeypatch.setattr(pipeline_module, "collect", lambda remote: fake_ev)

    seen = {}

    def _spy(full_name, ref):
        seen["full_name"], seen["ref"] = full_name, ref
        return 404, "404: Not Found"
    monkeypatch.setattr(decl, "_fetch_raw", _spy)

    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        verify("https://github.com/whiteknightonhorse/apibase",
              Binding(BindingKind.GIT, "whiteknightonhorse/apibase"),
              FileTransport(p / "o"), PublicRegistry(p / "r"))

    assert seen == {"full_name": "whiteknightonhorse/apibase", "ref": "cafebabe"}
