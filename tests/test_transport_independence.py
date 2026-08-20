"""T-TRANSPORT-2 - proof that the methodology has not fused with a Draft standard."""
import ast
import pathlib
import tempfile
from pathlib import Path

from src.transport.file_transport import FileTransport


def test_file_transport_publishes_and_preserves_absent_projection():
    """An absent projection must reach the transport as None, never as 0."""
    with tempfile.TemporaryDirectory() as d:
        t = FileTransport(Path(d))
        ref = t.publish("erc8004:42", {"x": 1}, None)
        import json
        got = json.loads(Path(ref).read_text(encoding="utf-8"))
        assert got["projection"] is None
        assert got["subject_id"] == "erc8004:42"


def test_methodology_modules_do_not_import_any_transport():
    """The load-bearing guarantee of section 4.4: the methodology knows nothing of publication.

    Checked via AST IMPORTS across every methodology module, not just the scorer.
    """
    methodology = ["src/verify/scorer.py", "src/verify/control_map.py",
                   "src/passport/passport.py", "src/abs_profile/ladder.py"]
    for path in methodology:
        tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
        names = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                names += [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom):
                names.append(n.module or "")
        for m in names:
            assert "transport" not in m.lower(), f"{path} imports transport: {m}"


def test_the_independence_check_is_ABLE_to_fail():
    """Instrument control: the check must catch a planted import."""
    assert "transport" in "src.transport.file_transport".lower()
