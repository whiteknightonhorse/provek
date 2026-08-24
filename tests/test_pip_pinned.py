"""T-S1, second half - the pip pins hold their shape, and the check is watched to fire.

`tests/test_actions_pinned.py` holds this property for `uses:`. This file holds it for the three
`pip install` lines D-30 pinned, and exists for the reason that file states about itself: A ONE-TIME
EDIT DRIFTS BACK. The first draft of D-30 argued no gate was possible here, on the ground that "the
set was moved by somebody who read what changed" is a fact about an edit rather than about the
tree. That is true of the JUDGEMENT and false of the SHAPE, and it was smuggling the second past
L-8 under cover of the first: whether `--require-hashes` is still on the line is a fact about the
tree, it can be read offline, and it can go red. Refuted by Fable before the change was pushed.

EVERY ASSERTION BELOW IS DRIVEN BY A FIXTURE THAT MAKES IT FAIL, not by reading the live tree and
finding it clean. A test that only ever sees the good state cannot distinguish a working checker
from one that returns an empty list - invariant 5, and the reason `evidence/RED-027-*` keeps the
run where the reverted line was actually caught.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.verify_pip_pins import (  # noqa: E402
    check,
    line_problems,
    pins,
    pip_install_lines,
    run_command_lines,
    segments,
    strip_comment,
    unhashed,
)

GOOD = "pip install --quiet --require-hashes --only-binary=:all: -r requirements/ci-tests.txt"


# --- the tree itself ----------------------------------------------------------------------------

def test_the_workflows_in_this_tree_are_clean():
    """The property, on the real files, on every push."""
    assert check() == []


def test_every_pip_install_in_gates_names_a_committed_set():
    """The three lines the task was about, found rather than assumed to be there."""
    text = (ROOT / ".github" / "workflows" / "gates.yml").read_text(encoding="utf-8")
    lines = pip_install_lines(text)
    # THE COUNT IS ASSERTED because "all of them are pinned" is satisfied vacuously by finding none,
    # and a refactor that moved an install into a block scalar this reader missed would do exactly
    # that - report perfect compliance over an empty set.
    assert len(lines) == 3, f"expected three pip installs in gates.yml, read {len(lines)}: {lines}"
    for line in lines:
        assert line_problems(line) == []


# --- the ways the pin is lost -------------------------------------------------------------------

def test_a_line_reverted_to_bare_packages_is_caught():
    """The regression this file exists for: `--require-hashes` edited back out.

    This is the exact line that stood in `gates.yml` until D-30, and the exact edit no other gate in
    this repository can see - `tests/test_door_matches_ci.py` reads any line starting `pip install`
    as runner preparation and waves it through.
    """
    problems = line_problems("pip install --quiet pytest pytest-cov")
    assert any("--require-hashes" in p for p in problems)
    assert any("rather than a committed requirements file" in p for p in problems)


def test_dropping_only_the_hash_flag_is_caught():
    """A set still named, still committed, and no longer enforced by pip."""
    assert any("--require-hashes" in p
               for p in line_problems("pip install -r requirements/ci-tests.txt --only-binary=:all:"))


def test_dropping_the_source_distribution_ban_is_caught():
    assert any("--only-binary=:all:" in p
               for p in line_problems("pip install --require-hashes -r requirements/ci-tests.txt"))


def test_a_requirements_file_fetched_over_the_network_is_caught():
    """The hole `-r` opens that a flag check alone waves through.

    Every required flag is present and the contents come from somebody else's server. Named by
    Fable, which is why it is here rather than discovered later.
    """
    line = "pip install --require-hashes --only-binary=:all: -r https://example.invalid/reqs.txt"
    assert any("not a path in this tree" in p for p in line_problems(line))


def test_a_requirements_file_outside_the_tree_is_caught():
    for ref in ("/tmp/reqs.txt", "../../reqs.txt"):
        line = f"pip install --require-hashes --only-binary=:all: -r {ref}"
        assert line_problems(line), f"{ref} was accepted"


def test_the_control_for_the_controls():
    """A correct line yields nothing - or every assertion above is met by rejecting everything."""
    assert line_problems(GOOD) == []


# --- reading the workflow -----------------------------------------------------------------------

def test_an_install_hidden_in_a_block_scalar_is_still_read():
    """`run: |` is how a step grows a second line; a reader that knew only the inline form would
    let a pip install be hidden from this gate by reformatting the step around it."""
    wf = ("jobs:\n  j:\n    steps:\n"
          "      - name: setup\n"
          "        run: |\n"
          "          python -m pip install pytest\n"
          "          echo done\n")
    lines = pip_install_lines(wf)
    assert lines == ["python -m pip install pytest"], lines
    assert any("--require-hashes" in p for p in line_problems(lines[0]))


def test_the_block_scalar_ends_at_the_next_step():
    """Or the reader would swallow following steps as shell and invent commands nobody runs."""
    wf = ("jobs:\n  j:\n    steps:\n"
          "      - run: |\n"
          "          echo one\n"
          "      - name: a later step\n"
          "        run: echo two\n")
    assert run_command_lines(wf) == ["echo one", "echo two"]


# --- text that is not the command -----------------------------------------------------------------

def _problems(workflow: str) -> list[str]:
    """Every problem this gate finds in a one-step workflow, through the real reading path."""
    return [p for line in pip_install_lines(workflow) for p in line_problems(line)]


def test_a_trailing_comment_cannot_vouch_for_the_command_it_was_removed_from():
    """The bypass that defeated the whole guarantee, and the one a natural edit reaches.

    bash discards a `#` comment; the first draft of this reader kept it, and every check here looks
    for its flags as SUBSTRINGS. So the line below satisfied all three flags and an `-r` pointing
    inside the tree, reported nothing, and installed one unpinned package with no requirements file
    at all - holding the workflow token. A developer commenting out the tail of a command while
    debugging, and not putting it back, produces exactly this. Found by Fable.
    """
    wf = ("jobs:\n  j:\n    steps:\n      - run: pip install evilpkg  "
          "# --require-hashes --only-binary=:all: -r requirements/ci-tests.txt\n")
    problems = _problems(wf)
    assert any("--require-hashes" in p for p in problems), problems
    assert any("rather than a committed requirements file" in p for p in problems), problems


def test_a_later_command_on_the_line_cannot_vouch_for_the_install():
    """`... && echo "--require-hashes -r requirements/ci-tests.txt"` - the printed excuse that
    contains the string being matched, which is how a step gets disabled with prose beside it."""
    wf = ('jobs:\n  j:\n    steps:\n      - run: pip install evilpkg && echo '
          '"--require-hashes --only-binary=:all: -r requirements/ci-tests.txt"\n')
    assert any("--require-hashes" in p for p in _problems(wf))


def test_a_hash_inside_quotes_is_data_and_does_not_truncate_the_command():
    """Cutting at every `#` would invent a false red on a command that legitimately contains one."""
    line = 'pip install --require-hashes --only-binary=:all: -r requirements/ci-tests.txt  # note'
    assert strip_comment(line).endswith("ci-tests.txt")
    assert strip_comment('echo "a # b" && pip install x') == 'echo "a # b" && pip install x'


def test_a_quoted_flag_still_counts_because_pip_still_receives_it():
    """The reader keeps quoted text, unlike the door's: `"--require-hashes"` really is passed."""
    assert line_problems(
        'pip install "--require-hashes" --only-binary=:all: -r requirements/ci-tests.txt') == []


def test_segments_splits_on_every_shell_separator():
    assert segments("a && b || c ; d | e") == ["a", "b", "c", "d", "e"]


def test_an_escaped_quote_does_not_invert_the_readers_idea_of_quoting():
    """The fifth bypass, and it defeated BOTH earlier repairs with one character.

    bash reads `\\"` inside double quotes as a literal quote and stays inside the string. The first
    repair's two quote-tracking loops read it as a close followed by an open, so from that point
    their quoting was inverted against bash's: the `;` never split, the `#` never cut, and every
    flag was "found" in a comment on a command bash never receives them on. Found by Fable, in the
    round that reviewed the previous round's repair.
    """
    wf = ('jobs:\n  j:\n    steps:\n      - run: echo "\\"" ; pip install evilpkg  '
          '# --require-hashes --only-binary=:all: -r requirements/ci-tests.txt\n')
    assert pip_install_lines(wf) == ["pip install evilpkg"], pip_install_lines(wf)
    assert any("--require-hashes" in p for p in _problems(wf))


def test_an_escaped_quote_does_not_redden_an_honest_line():
    """The same blindness in the other direction, and the more expensive one.

    `grep -r "\\"" logs && pip install --require-hashes ...` is correct. The inverted quoting
    swallowed the `&&`, so grep's `-r` was read as a second requirements reference pointing outside
    `requirements/` - a red on a line that does everything right. A gate that reddens correct work
    teaches people to route around it (L-5).
    """
    wf = ('jobs:\n  j:\n    steps:\n      - run: grep -r "\\"" logs && pip install '
          '--require-hashes --only-binary=:all: -r requirements/ci-tests.txt\n')
    assert _problems(wf) == [], _problems(wf)


def test_a_backslash_inside_single_quotes_is_literal():
    """bash escapes nothing inside `'...'`, so the quote closes where it looks like it closes."""
    assert segments(r"echo 'a\' ; pip install x") == [r"echo 'a\'", "pip install x"]


def test_a_line_with_an_unclosed_quote_is_refused_rather_than_guessed_at():
    """Past a stray quote every separator is data, so any verdict would be about a string this
    reader cannot segment. It is reported as unreadable instead of parsed on."""
    problems = line_problems('pip install x "unclosed')
    assert len(problems) == 1 and "unclosed" in problems[0], problems


def test_a_command_substitution_is_judged_as_the_command_it_is():
    """The eighth bypass: `$( )` holds no `&&`, `;` or `|`, so the whole line arrived as one
    segment carrying every required flag - reported clean, while bash runs the install inside the
    substitution and the flags decorate the `echo` around it. Found by Fable."""
    for opener, closer in (("$(", ")"), ("`", "`")):
        wf = (f"jobs:\n  j:\n    steps:\n      - run: echo {opener}pip install evilpkg{closer} "
              "--require-hashes --only-binary=:all: -r requirements/ci-tests.txt\n")
        assert pip_install_lines(wf) == ["pip install evilpkg"], pip_install_lines(wf)
        assert any("--require-hashes" in p for p in _problems(wf))


def test_a_substitution_inside_double_quotes_is_still_a_command():
    """bash expands `$(...)` inside double quotes, so quoting it hides nothing - and the reader's
    `is_syntax` flag alone would have said otherwise. That is why `substitutable` is separate."""
    wf = ('jobs:\n  j:\n    steps:\n      - run: echo "$(pip install evilpkg)" '
          '--require-hashes --only-binary=:all: -r requirements/ci-tests.txt\n')
    assert any("--require-hashes" in p for p in _problems(wf))


def test_single_quotes_do_suppress_a_substitution():
    """The control in the other direction: bash does NOT expand inside `'...'`, so splitting there
    would invent commands that never run."""
    assert segments("echo '$(pip install evilpkg)'") == ["echo '$(pip install evilpkg)'"]


def test_a_command_split_over_two_lines_with_a_backslash_is_not_reddened():
    """An honest install wrapped for readability. Read as two physical lines, the first carries
    both flags and no `-r` and was reported as installing packages named on the command line -
    a red on correct work, and these three lines are exactly the candidates for being wrapped
    this way one day (L-5). Found by Fable."""
    wf = ("jobs:\n  j:\n    steps:\n      - run: |\n"
          "          pip install --require-hashes --only-binary=:all: \\\n"
          "            -r requirements/ci-tests.txt\n")
    assert _problems(wf) == [], _problems(wf)


# --- block scalars the reader must not go silent on -----------------------------------------------

def test_an_install_behind_an_indentation_indicator_is_still_read():
    """`run: |2` is valid YAML the first draft did not recognise - and an unrecognised header meant
    the body was skipped in SILENCE, with the three real installs keeping the vacuity guard quiet.
    A control that valid YAML blinds without a signal is a defect, not a limit. Found by Fable."""
    for header in ("|2", "|-", ">-2", "|+", "&anchor |", "| # collect coverage", "|2 # note"):
        wf = (f"jobs:\n  j:\n    steps:\n      - run: {header}\n"
              "          pip install evilpkg\n")
        lines = pip_install_lines(wf)
        assert lines == ["pip install evilpkg"], f"{header}: {lines}"


def test_a_workflow_saved_as_yaml_is_measured_too(tmp_path):
    """GitHub reads both extensions; a checker that knew one would be silent about the other."""
    wf = tmp_path / "wf"
    wf.mkdir()
    (wf / "gates.yaml").write_text(
        "jobs:\n  j:\n    steps:\n      - run: pip install evilpkg\n", encoding="utf-8")
    problems = check(workflows=wf, root=tmp_path)
    assert any("--require-hashes" in p for p in problems), problems


# --- reading the compiled sets ------------------------------------------------------------------

def test_a_pin_with_no_hash_is_caught():
    body = ("coverage==7.15.4 \\\n"
            "    --hash=sha256:aaaa\n"
            "pytest==9.1.1\n")
    assert unhashed(body) == ["pytest"]


def test_a_fully_hashed_set_reports_nothing():
    body = ("coverage==7.15.4 \\\n"
            "    --hash=sha256:aaaa \\\n"
            "    --hash=sha256:bbbb\n"
            "pytest==9.1.1 \\\n"
            "    --hash=sha256:cccc\n")
    assert unhashed(body) == []
    assert pins(body) == {"coverage": "7.15.4", "pytest": "9.1.1"}


def test_the_real_sets_are_fully_hashed():
    for name in ("ci-tests", "ci-shipped", "ci-lint"):
        body = (ROOT / "requirements" / f"{name}.txt").read_text(encoding="utf-8")
        assert unhashed(body) == [], name
        assert pins(body), f"{name} pins nothing"


# --- the cost of three files --------------------------------------------------------------------

def _tree(tmp_path: Path, tests_pytest: str, shipped_pytest: str) -> tuple[Path, Path]:
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    reqs = tmp_path / "requirements"
    reqs.mkdir()
    steps = "jobs:\n  j:\n    steps:\n"
    for name in ("ci-tests", "ci-shipped"):
        steps += (f"      - run: pip install --require-hashes --only-binary=:all: "
                  f"-r requirements/{name}.txt\n")
    (wf / "gates.yml").write_text(steps, encoding="utf-8")
    (reqs / "ci-tests.txt").write_text(f"pytest=={tests_pytest} \\\n    --hash=sha256:aaaa\n",
                                       encoding="utf-8")
    (reqs / "ci-shipped.txt").write_text(f"pytest=={shipped_pytest} \\\n    --hash=sha256:bbbb\n",
                                         encoding="utf-8")
    return wf, tmp_path


def test_two_jobs_pinned_to_different_versions_of_one_package_is_caught(tmp_path):
    """The price of separate sets per job: a bump applied to one file and not its sibling leaves
    both jobs green and only one of them current. Named by Fable as the cost D-30 recorded without."""
    wf, root = _tree(tmp_path, "9.1.1", "8.0.0")
    problems = check(workflows=wf, root=root)
    assert any("DIFFERENT versions" in p for p in problems), problems


def test_matching_versions_across_the_sets_are_accepted(tmp_path):
    wf, root = _tree(tmp_path, "9.1.1", "9.1.1")
    assert check(workflows=wf, root=root) == []


# --- the third state ----------------------------------------------------------------------------

def test_a_named_set_that_does_not_exist_is_a_violation(tmp_path):
    wf = tmp_path / "wf"
    wf.mkdir()
    (wf / "gates.yml").write_text(
        "jobs:\n  j:\n    steps:\n      - run: pip install --require-hashes --only-binary=:all: "
        "-r requirements/absent.txt\n", encoding="utf-8")
    problems = check(workflows=wf, root=tmp_path)
    assert any("does not exist or cannot be read" in p for p in problems), problems


def test_a_workflow_directory_with_no_pip_install_reports_unknown_not_clean(tmp_path):
    """Invariant 1 inside the instrument. If the workflows stop installing packages, this gate has
    become vacuous - and a vacuous gate that prints `clean` is how a control is lost silently."""
    wf = tmp_path / "wf"
    wf.mkdir()
    (wf / "gates.yml").write_text("jobs:\n  j:\n    steps:\n      - run: echo hello\n",
                                  encoding="utf-8")
    problems = check(workflows=wf, root=tmp_path)
    assert any("measured NOTHING" in p for p in problems), problems


def test_absent_workflows_are_not_reported_as_clean(tmp_path):
    problems = check(workflows=tmp_path / "nope", root=tmp_path)
    assert any("ABSENT" in p for p in problems), problems
