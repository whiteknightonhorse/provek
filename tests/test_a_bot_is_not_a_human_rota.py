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
    humans, bots = authors_and_bot_commits(
        [_c("claude", "User"), _c("dependabot[bot]", "Bot"), _c("dependabot[bot]", "Bot")])
    assert humans == {"claude"}, f"the bot was counted as a person: {humans}"
    assert bots == 2, "bot commits stopped being counted at all; the share would go silent"


def test_a_sole_human_stays_sole_when_a_bot_arrives():
    """The case that started this: adding Dependabot must not cost a level."""
    before, _ = authors_and_bot_commits([_c("claude", "User")] * 5)
    after, _ = authors_and_bot_commits([_c("claude", "User")] * 5 + [_c("dependabot[bot]", "Bot")])
    assert len(before) == len(after) == 1


def test_a_user_named_like_a_bot_is_still_a_person():
    """The loophole this rule must not open: renaming an account to buy back a level."""
    humans, bots = authors_and_bot_commits([_c("sneaky-bot", "User"), _c("real-person", "User")])
    assert humans == {"sneaky-bot", "real-person"}, (
        "an account was excluded on the strength of its NAME; the platform types it User, and "
        "keying on the name lets anyone rename their way to a higher level")
    assert bots == 0


def test_the_platform_type_decides_even_without_the_suffix():
    humans, bots = authors_and_bot_commits([_c("some-app", "Bot"), _c("person", "User")])
    assert humans == {"person"}
    assert bots == 1


def test_an_unlinked_commit_still_counts_by_its_email():
    """No login is not no author - it is an author we can only name by address."""
    humans, _ = authors_and_bot_commits([_c(email="a@example.com"), _c(email="b@example.com")])
    assert humans == {"a@example.com", "b@example.com"}
