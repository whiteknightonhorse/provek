"""T-S1 - the workflows pin the code they run and bound the token they run it with.

Two properties, one cause. Code scanning reported 19 `PinnedDependenciesID` and 5
`actions/missing-workflow-permissions` against this repository's workflows: every third-party
action was named by a movable TAG, and no job said what its token was allowed to do. Those are the
two halves of one exposure - unreviewed code, executing with unbounded credentials, in a public
repository - and fixing either alone leaves the other standing.

WHAT IS CHECKED HERE AND WHAT IS NOT, because the distinction is the whole risk of this task.

  * SHAPE is checked from this tree, offline, and is what the assertions below hold on every push:
    every `uses:` is a 40-hex commit SHA, every SHA carries a `# tag` comment, and every workflow
    bounds its token.
  * TRUTH - that `# v4.4.0` beside a SHA is that tag's real commit - cannot be taken from this tree
    at all, and this is exactly where pinning can make things worse. A pin to somebody else's
    commit looks identical to a correct one and defeats review by appearing to have passed it. It
    is re-derived from each action's own repository by `scripts/verify_action_pins.py`, which needs
    a network; that script's pure core is driven HERE against a stubbed resolver, so its MISMATCH
    and NOT_MEASURED arms are seen to fire rather than merely being present (L-16).

The network half is deliberately not run inside pytest. A lookup that fails offline would either
make this suite red on a host with no route out, or - far worse - be softened into a skip, and a
skip is how "the instrument did not run" comes to be recorded as "the pin is fine" (invariant 1).
The verdict on shape is taken here on every push; the verdict on truth is taken by the script,
which reports a refused lookup as NOT_MEASURED and exits non-zero on it.

The pins in this tree were re-derived on 2026-08-24 by two independent instruments that agreed on
all five actions - `git ls-remote` over the git protocol and the REST API's tag endpoint. The
transcripts of both runs are kept in `evidence/GREEN-004-every-pin-re-derived-from-its-owner.txt`;
an earlier draft of this docstring cited "the commit that introduced them" instead, which was a
reference to an artefact that did not exist yet (L-30).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.verify_action_pins import (  # noqa: E402
    Pin,
    collect,
    resolve_tags,
    shape_problems,
    token_problems,
    verify,
)

WORKFLOWS = ROOT / ".github" / "workflows"


# --- the tree itself ---------------------------------------------------------------------------

def test_every_action_is_pinned_to_a_commit_with_a_readable_tag():
    """The property the 19 alerts were about, held on every workflow rather than on the one named.

    The task named `gates.yml`. `codeql.yml` and `scorecard.yml` run on push to `main` with tokens
    of their own - `security-events: write` and `id-token: write` between them, which are wider
    than anything `gates.yml` holds - so a checker that read only the file in the task description
    would report the tree clean while the more privileged workflows stayed unpinned. That is L-12:
    a checker inspecting one part of the tree and reporting on all of it.
    """
    pins, problems = collect()
    assert problems == [], problems
    assert pins, "no `uses:` found in any workflow - unreadable, not clean"
    assert shape_problems(pins) == []


def test_the_shape_check_is_able_to_fail():
    """L-16: present is not armed. Each control is a state that really existed in this tree."""
    tagged = Pin("w.yml", 1, "actions/checkout", "v4", "v4.4.0")
    assert any("MOVABLE ref" in p for p in shape_problems([tagged]))

    unlabelled = Pin("w.yml", 1, "actions/checkout", "a" * 40, None)
    assert any("no `# tag` comment" in p for p in shape_problems([unlabelled]))

    # The control for the control: a correct pin produces nothing, or the two assertions above
    # would be satisfied by a checker that simply rejects everything it is shown.
    good = Pin("w.yml", 1, "actions/checkout", "a" * 40, "v4.4.0")
    assert shape_problems([good]) == []


def test_a_branch_or_a_bare_action_is_not_read_as_pinned(tmp_path):
    """`@main` is a pin to a moving branch; a `uses:` with no ref at all is the default branch."""
    assert any("MOVABLE ref" in p
               for p in shape_problems([Pin("w.yml", 1, "some/action", "main", "main")]))
    (tmp_path / "w.yml").write_text("jobs:\n  j:\n    steps:\n      - uses: some/action\n")
    _pins, problems = collect(tmp_path)
    assert any("names no ref at all" in p for p in problems), problems


def test_a_uses_line_this_checker_cannot_parse_is_a_red_and_not_a_skip(tmp_path):
    """Fable's break of the first draft, and the most dangerous kind: it failed GREEN.

    `USES_RE` required the tag comment to be a single word, and a line that did not match was
    dropped silently. So `uses: github/codeql-action/init@main  # pinned upstream, see notes` was
    invisible: `shape_problems` had nothing to complain about, `verify()` never saw it, and the
    script's own summary counted 16 actions instead of 17 with nothing holding the total. A moving
    branch, running with our token, reported as a clean pinned tree - by a checker written to
    prevent exactly that.

    Both halves are asserted: the multi-word comment now PARSES (so the pin is really checked), and
    a line this parser genuinely cannot read is REPORTED (so the class of miss cannot recur).
    """
    sha = "a" * 40
    (tmp_path / "w.yml").write_text(
        f"jobs:\n  j:\n    steps:\n      - uses: a/b@{sha}  # v1.2.3 (pinned upstream, see notes)\n")
    pins, problems = collect(tmp_path)
    assert problems == [] and len(pins) == 1, "a multi-word comment must not hide the line"
    assert pins[0].tag == "v1.2.3" and shape_problems(pins) == []

    # The property is that no `uses:` line ESCAPES, by either route: read it and judge the ref, or
    # report it unreadable. Which of the two applies is an implementation detail and is deliberately
    # not asserted - `uses : a/b@main` is now parsed and caught as a movable ref, while a flow
    # mapping is reported unparseable. Silence is the only forbidden answer.
    for hidden in ("      - uses : a/b@main\n", "      - { uses: a/b@main }\n",
                   "      - uses: a/b@main  # dropped the pin while debugging\n"):
        (tmp_path / "w.yml").write_text(f"jobs:\n  j:\n    steps:\n{hidden}")
        pins, problems = collect(tmp_path)
        assert problems + shape_problems(pins) != [], f"{hidden!r} was skipped in silence"


def test_the_real_workflows_hold_no_uses_line_the_checker_skipped(tmp_path):
    """The count is pinned, because a silent skip subtracts from a total nobody watches.

    17 `uses:` lines across the three workflows, counted independently of the parser that reads
    them: a grep for the key, compared against what `collect()` returned.
    """
    grepped = sum(
        1 for f in sorted(WORKFLOWS.glob("*.yml"))
        for ln in f.read_text(encoding="utf-8").splitlines()
        if not ln.lstrip().startswith("#") and re.search(r"(?:^|[-{,\s])uses\s*:", ln))
    pins, problems = collect()
    assert problems == []
    assert len(pins) == grepped, (
        f"{grepped} lines name `uses:` but the checker produced {len(pins)} pins - the difference "
        "is lines it walked past")


def test_an_unreadable_workflow_directory_is_not_reported_as_clean(tmp_path):
    """Invariant 1 turned on this file's own instrument."""
    _pins, problems = collect(tmp_path / "does-not-exist")
    assert any("UNREADABLE" in p for p in problems)
    _pins, problems = collect(tmp_path)          # exists, holds nothing
    assert any("unreadable or empty" in p for p in problems)


# --- the truth of a pin, driven without a network ----------------------------------------------

def test_verify_separates_a_match_from_a_lie_from_a_refusal():
    """The four states the network half must keep apart.

    MISMATCH is the state this whole task can create: pinning to a plausible SHA with a correct
    tag beside it. NOT_MEASURED is the state that would otherwise be reported as MATCH the first
    time the audit host has no route out - a gate green precisely when it is blind.
    """
    real = "1" * 40
    pin = Pin("w.yml", 1, "actions/checkout", real, "v4.4.0")

    def agrees(_repo):
        return {"v4.4.0": real}

    def disagrees(_repo):
        return {"v4.4.0": "2" * 40}

    def has_no_such_tag(_repo):
        return {"v9.9.9": real}

    def refuses(_repo):
        return None

    assert [s for _p, s, _d in verify([pin], agrees)] == ["MATCH"]
    assert [s for _p, s, _d in verify([pin], disagrees)] == ["MISMATCH"]
    assert [s for _p, s, _d in verify([pin], has_no_such_tag)] == ["TAG_ABSENT"]
    assert [s for _p, s, _d in verify([pin], refuses)] == ["NOT_MEASURED"]


def test_a_refusal_never_becomes_a_match_however_many_pins_share_the_repository():
    """The resolver is cached per repository; the cache must carry the refusal, not drop it."""
    pins = [Pin("w.yml", i, "actions/checkout", "1" * 40, "v4.4.0") for i in (1, 2, 3)]
    calls = []

    def refuses(repo):
        calls.append(repo)
        return None

    assert {s for _p, s, _d in verify(pins, refuses)} == {"NOT_MEASURED"}
    assert calls == ["actions/checkout"], "the lookup should be cached, and its refusal cached too"


def test_a_subpath_action_is_resolved_against_its_repository():
    """`github/codeql-action/init` lives in `github/codeql-action`; asking for the subpath 404s."""
    assert Pin("w.yml", 1, "github/codeql-action/init", "1" * 40, "v3").repo == "github/codeql-action"
    assert Pin("w.yml", 1, "actions/checkout", "1" * 40, "v4").repo == "actions/checkout"


def test_the_network_resolver_reports_a_failure_as_none_rather_than_as_empty(tmp_path):
    """An unreachable remote must not return `{}`, which would read as TAG_ABSENT on every pin.

    TAG_ABSENT accuses the action's owner of deleting a tag; NOT_MEASURED accuses nothing and names
    our own blindness. Collapsing the second into the first sends the next reader to investigate
    somebody else's repository over a broken route out of this one.

    Driven against a local path that is not a repository rather than against GitHub: this suite
    runs at the door and in CI, and a test that needs a route out would go red on a host that has
    none - or, far worse, be softened into a skip, which is the same defect this assertion exists
    to prevent, one level up.
    """
    assert resolve_tags("nothing-here", base=f"{tmp_path}/") is None


# --- the token each workflow hands to that code -------------------------------------------------

def test_every_workflow_bounds_the_token_it_hands_out():
    """The property the 5 `actions/missing-workflow-permissions` alerts were about."""
    files = sorted(p for p in WORKFLOWS.iterdir() if p.suffix in (".yml", ".yaml"))
    assert files, "no workflows found - unreadable, not clean"
    for f in files:
        assert token_problems(f.read_text(encoding="utf-8"), f.name) == []


def test_the_permissions_check_is_able_to_fail():
    """Including the case this commit chose: one declaration at workflow level covering five jobs."""
    none_at_all = "on:\n  push:\n\njobs:\n  a:\n    steps: []\n  b:\n    steps: []\n"
    assert len(token_problems(none_at_all)) == 2

    at_workflow_level = "on:\n\npermissions:\n  contents: read\n\njobs:\n  a:\n    steps: []\n"
    assert token_problems(at_workflow_level) == []

    per_job = ("on:\n  push:\n\njobs:\n  a:\n    permissions:\n      contents: read\n"
               "    steps: []\n  b:\n    steps: []\n")
    problems = token_problems(per_job)
    assert len(problems) == 1 and "`b`" in problems[0], (
        "a bounded neighbour must not vouch for an unbounded job")


def test_an_annotated_jobs_key_does_not_render_the_workflow_as_bounded():
    """Fable's break of the first draft: `partition("\\njobs:\\n")` on an ordinary YAML comment.

    The partition found nothing, the job list came back empty, and a workflow with NO permissions
    anywhere was reported clean. "I could not find the jobs" rendered as "every job is bounded" is
    invariant 1 turned on this checker - the same defect `collect()` already reports honestly for an
    unreadable directory, one level down.
    """
    annotated = "on:\n  push:\n\njobs:  # five of them\n  a:\n    steps: []\n"
    assert token_problems(annotated) != [], "an annotated `jobs:` key hid an unbounded job"

    missing = "on:\n  push:\n\nsteps: []\n"
    assert any("UNREADABLE" in p for p in token_problems(missing))


def test_a_blanket_write_grant_is_not_accepted_as_a_bound():
    """Checking that the key is PRESENT lets the fix be undone by editing its value (L-16)."""
    assert token_problems("permissions: write-all\n\njobs:\n  a:\n    steps: []\n") != []
    assert token_problems("permissions: read-all\n\njobs:\n  a:\n    steps: []\n") == []
