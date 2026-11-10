"""T-AEO-01 / D-82: the agent list verify_live.sh reads and the policy robots.txt publishes cannot drift.

Every entry of AGENT_UAS, taken out of the script, must be allowed `/` by web/public/robots.txt for
its product token. If robots.txt ever disallows one, the live check would insist the edge serve a
crawler the site asks not to be crawled - so the test fails naming it.
"""
from __future__ import annotations

import pathlib
import re
import urllib.robotparser

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_live.sh"
ROBOTS = ROOT / "web" / "public" / "robots.txt"


def _agent_uas() -> list[str]:
    m = re.search(r"^AGENT_UAS=\((.*?)\)\s*$", SCRIPT.read_text(encoding="utf-8"), re.S | re.M)
    assert m, "no AGENT_UAS=( ... ) in verify_live.sh"
    uas = re.findall(r'"([^"]+)"', m.group(1))
    assert uas, "AGENT_UAS parsed to zero entries - a vacuous check"
    return uas


def check_robots_allows_every_agent(robots_path: pathlib.Path) -> None:
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(robots_path.read_text(encoding="utf-8").splitlines())
    for ua in _agent_uas():
        token = ua.split("/")[0]
        assert rp.can_fetch(token, "/"), f"robots.txt does not allow / for {token} ({ua})"


def test_every_agent_ua_is_allowed_by_the_published_robots_txt():
    check_robots_allows_every_agent(ROBOTS)


def test_mutation_a_disallow_for_gptbot_fails_naming_gptbot(tmp_path):
    mutated = tmp_path / "robots.txt"
    mutated.write_text(ROBOTS.read_text(encoding="utf-8") + "\nUser-agent: GPTBot\nDisallow: /\n", encoding="utf-8")
    try:
        check_robots_allows_every_agent(mutated)
    except AssertionError as e:
        assert "GPTBot" in str(e)
    else:
        raise AssertionError("a robots.txt disallowing GPTBot passed the drift check")
