"""End-to-end pipeline. We check PROPERTIES of the result, not that it exists."""
import subprocess
import tempfile
from pathlib import Path

from src.abs_profile.identity import Binding, BindingKind
from src.collector.divergence import Divergence
from src.pipeline import verify
from src.registry.public_registry import PublicRegistry
from src.transport.file_transport import FileTransport


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
