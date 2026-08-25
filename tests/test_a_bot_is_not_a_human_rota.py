"""Accounts the platform classifies as bots do not count toward `distinct_authors`.

Ratified by the operator 2026-08-25. `SOLE_AUTHOR` claims to detect a HUMAN rota, and a dependency
bot's commit is not evidence of one; counting it cost a subject a level for adding automation,
which is an inverted incentive in an instrument that measures autonomy.

The rule keys on the PLATFORM's classification. These tests keep it there: the moment it keys on
the name instead, anyone renames an account and buys back a level.
"""
from src.collector.github import authors_and_bot_commits


def _c(login=None, typ=None, email=None):
    return {"author": ({"login": login, "type": typ} if login or typ else None),
            "commit": {"author": {"email": email or "nobody@example.com"}}}


def test_a_bot_commit_does_not_add_an_author():
    humans, bots, _keys, _un = authors_and_bot_commits(
        [_c("claude", "User"), _c("dependabot[bot]", "Bot"), _c("dependabot[bot]", "Bot")])
    assert humans == {"claude"}, f"the bot was counted as a person: {humans}"
    assert bots == 2, "bot commits stopped being counted at all; the share would go silent"


def test_a_sole_human_stays_sole_when_a_bot_arrives():
    """The case that started this: adding Dependabot must not cost a level."""
    before, *_ = authors_and_bot_commits([_c("claude", "User")] * 5)
    after, *_ = authors_and_bot_commits([_c("claude", "User")] * 5 + [_c("dependabot[bot]", "Bot")])
    assert len(before) == len(after) == 1


def test_a_user_named_like_a_bot_is_still_a_person():
    """The loophole this rule must not open: renaming an account to buy back a level."""
    humans, bots, _keys, _un = authors_and_bot_commits([_c("sneaky-bot", "User"), _c("real-person", "User")])
    assert humans == {"sneaky-bot", "real-person"}, (
        "an account was excluded on the strength of its NAME; the platform types it User, and "
        "keying on the name lets anyone rename their way to a higher level")
    assert bots == 0


def test_the_platform_type_decides_even_without_the_suffix():
    humans, bots, _keys, _un = authors_and_bot_commits([_c("some-app", "Bot"), _c("person", "User")])
    assert humans == {"person"}
    assert bots == 1


def test_an_unlinked_commit_is_not_an_author_and_opens_the_window(tmp_path=None):
    """A commit nothing vouches for is not a person we can count. It is the absence of a count.

    This test asserted the opposite until 2026-08-25 -- that an unlinked commit "still counts by
    its email" -- and that was the defect, not the intent. The e-mail in a commit is written by
    the side being measured, in their own `git config`. Counting it as an identity lets the
    subject author the key that identifies them; merging two such keys, or splitting one, both
    encode a guess. They are collected apart, and what they produce is a lower bound.
    """
    humans, bots, keys, unlinked = authors_and_bot_commits(
        [_c("claude", "User"), _c(email="a@example.com"), _c(email="b@example.com")])
    assert humans == {"claude"}, f"an unattributed commit was counted as an author: {humans}"
    assert keys == {"a@example.com", "b@example.com"}, "the unattributed keys were not collected"
    assert unlinked == 2, "the count of unattributed commits is what opens the window"
    assert bots == 0
