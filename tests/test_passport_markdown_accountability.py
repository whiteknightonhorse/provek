"""D-43. `web/markdown.mjs` is the OTHER assembler that writes a published artefact directly from
passport data - `/p/<slug>/index.md` - and it never passes through `web/html_to_markdown.mjs`:
no `stripTags`, no `NEVER_UNESCAPED`, no `decode`. It does not read `passport.accountability` at
all today, so every assertion below is currently vacuously true - the hostile value cannot reach
the output because nothing in `buildPassportMarkdown` looks at it.

That is the point, not a gap in this test. Fable's ruling asked for the tripwire to exist BEFORE
the feature does: the day someone adds `${p.accountability.claims_addressee.value}` to the
template in `web/markdown.mjs`, `tests/passport_accountability_probe.mjs` starts feeding that
interpolation a real payload, and this file's assertions - unchanged - start failing in the gate
that runs on every push instead of in production on provek.dev. See
`tests/passport_accountability_probe.mjs` for the synthetic passport and the two payloads.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

PROBE = Path(__file__).parent / "passport_accountability_probe.mjs"


@pytest.fixture(scope="module")
def out():
    if shutil.which("node") is None:
        pytest.skip("node is not on PATH")
    r = subprocess.run(["node", str(PROBE)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_a_live_script_tag_never_reaches_the_passport_markdown(out):
    md = out["script"]
    assert "<script" not in md.lower(), md
    assert "alert(1)" not in md, md


def test_a_markdown_link_payload_never_reaches_the_passport_markdown(out):
    """`[urgent: verify here](https://evil.example)` needs no angle bracket at all - it is
    markdown's OWN syntax, the gap `NEVER_UNESCAPED` does not cover and `src/collector/
    declaration.py`'s `FORBIDDEN_CHARS` exists to refuse before it ever reaches an assembler."""
    md = out["link"]
    assert "evil.example" not in md, md
    assert "verify here" not in md, md


def test_the_probe_still_names_the_gap_it_tests(out):
    """THE CONTROL. If `buildPassportMarkdown` started reading `passport.accountability` without
    ANY escaping, `out["script"]` would contain the raw payload and the first test above would
    fail - proving these assertions test something real rather than two strings that can never
    appear for unrelated reasons. Recorded here as the argument, not re-run: `git grep
    accountability web/markdown.mjs` finding nothing is what makes today's pass vacuous, and this
    test is the reminder that the day it stops being vacuous is the day it must still be green."""
    assert "accountability" not in Path("web/markdown.mjs").read_text(encoding="utf-8")
