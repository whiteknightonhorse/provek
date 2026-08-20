"""GitHub API collector: secret redaction and honesty when the source is unreachable.

NOTE ON THE FIXTURES. The fake secrets below are ASSEMBLED AT RUNTIME from fragments, so no
secret-shaped literal ever exists in this file. The alternative - exempting `tests/` from the
secret scan - would open a door for a real secret to hide behind, and a gate with a hole in it is
not a gate. The scan stays strict; the fixture bends.
"""
from src.abs_profile.measured import Measurement, NotMeasured
from src.collector.github import GitHubEvidence, redact

_GH = "gh" + "p_" + "abcdefghijklmnopqrstuvwxyz0123"
_ANT = "sk-" + "ant-" + "oat01-" + "x" * 40
_PEM = "-----BEGIN " + "RSA PRIVATE KEY" + "-----"
_HEX = "0x" + "a" * 64


def test_secrets_are_redacted_BEFORE_becoming_an_artefact():
    """An artefact from which a secret is removed later has already sat in a log."""
    s = redact(f"token {_GH} and key {_ANT}")
    assert "gh" + "p_abcdef" not in s
    assert "oat01" not in s
    assert "<REDACTED>" in s


def test_redaction_covers_private_keys_and_hex_secrets():
    assert "<REDACTED>" in redact(_PEM)
    assert "<REDACTED>" in redact(_HEX)


def test_redaction_leaves_ordinary_text_alone():
    """A redactor that erases everything destroys evidence along with secrets."""
    t = "an ordinary commit about github actions and sk-something-short"
    assert redact(t) == t


def test_unreadable_repo_yields_NotMeasured_not_zeros():
    ev = GitHubEvidence("x/y", False, None,
                        Measurement(absent=NotMeasured.UNREADABLE),
                        Measurement(absent=NotMeasured.UNREADABLE),
                        Measurement(absent=NotMeasured.UNREADABLE),
                        Measurement(absent=NotMeasured.UNREADABLE))
    assert ev.signed_commit_share.is_measured is False
    assert ev.has_runtime_trace is False   # no data != no trace, but L3+ is forbidden either way


def test_runtime_trace_requires_actual_runs_not_just_readability():
    """Zero runs is a MEASURED zero: the trace is absent, which differs from "we could not read"."""
    def m(v):
        return Measurement(value=v)

    ev = GitHubEvidence("x/y", True, "s", m(1.0), m(1), m(0.0), m(0))
    assert ev.workflow_runs.is_measured is True
    assert ev.has_runtime_trace is False
    ev2 = GitHubEvidence("x/y", True, "s", m(1.0), m(1), m(0.0), m(42))
    assert ev2.has_runtime_trace is True
