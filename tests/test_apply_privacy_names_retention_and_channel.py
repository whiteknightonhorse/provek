"""T-0573 - the privacy list on /apply/ states a retention rule, every holder and a private channel.

THE DEFECT THIS HOLDS SHUT. The list said "nothing here deletes on a timer" and "reply to any
message from us", and the project sends no mail: the only deletion channel it offered did not
exist, the alternative (a public issue) published the fact of the request, Cloudflare was not named
as a holder, and nothing said how long a refused applicant's address stayed. These are source
assertions on `web/src/pages/Apply.tsx`; the TTL itself is proved in ~/orchestra by
`tests/test_intake_cron.py` (a refusal is written with expiration_ttl 2592000, a publication with none).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "web/src/pages/Apply.tsx").read_text(encoding="utf-8")
DOC = (ROOT / "docs/INTAKE_OPERATIONS.md").read_text(encoding="utf-8")


def _list_text():
    """The privacy list as a reader sees it: JSX comments and tags gone, whitespace folded."""
    start = PAGE.index("What happens to what you type here")
    body = re.sub(r"\{/\*.*?\*/\}", " ", PAGE[start:], flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body).replace("&rsquo;", "'").replace("&mdash;", "-")
    return re.sub(r"\s+", " ", body)


def test_the_retention_rule_is_stated_with_its_period():
    text = _list_text()
    assert "30 days after its outcome" in text
    assert "30 days after the row is withdrawn" in text
    assert "nothing here deletes on a timer" not in text


def test_every_holder_is_named():
    text = _list_text()
    for holder in ("Cloudflare", "Telegram", "intake log"):
        assert holder in text
    assert "IP address" in text


def test_the_private_channel_exists_and_the_mail_that_does_not_is_gone():
    text = _list_text()
    assert "reply to any message from us" not in text.lower()
    assert "replying to any message from us" not in text.lower()
    assert "Deleted sooner" in text and "private" in text
    assert re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text), "the channel must be a stated address"


def test_the_page_says_it_is_not_legal_advice_and_is_last():
    text = _list_text()
    assert "not legal advice" in text.lower()
    assert text.lower().rindex("not legal advice") > text.rindex("Separately, about this whole site")


def test_the_operations_doc_carries_the_retention_table():
    assert "## Retention (T-0573)" in DOC
    assert "2592000" in DOC and "expiration_ttl" in DOC
