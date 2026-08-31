"""Every button says what it is under the cursor - checked in the BUILT css, not the source.

WHY THIS EXISTS. Browsers give `<button>` `cursor: default`, and Tailwind's preflight does not
override it. All three buttons this site has hovered as if they were text: the passport's two
copy buttons (reported by the operator) and - worse - the intake form's Submit, the one control a
stranger uses to send their request.

WHY IT IS A RULE AND NOT A CLASS. A `cursor-pointer` class on each button fixes the three that
exist and misses the fourth somebody adds. The rule lives where every button already passes.

WHY `:disabled` IS ASSERTED TOO, and it is not tidiness. /apply/ keeps Submit disabled until the
updates box is ticked. A pointer cursor there would tell the visitor "clickable" about a control
that refuses - the silent-refusal shape that gate exists to prevent, arriving through the cursor
instead of through the handler. `not-allowed` agrees with the sentence printed under the button.

WHY THE BUILT CSS. A rule in `src/index.css` that Tailwind drops, reorders or overrides is a rule
that is not in force. Reading `web/dist` measures what the browser receives - the lesson
`prerender.mjs` taught this project when it overwrote a corrected robots.txt after the build.

HOW TO MAKE IT FAIL: delete either rule from src/index.css and rebuild.
"""

from __future__ import annotations

import re
from pathlib import Path

DIST = Path(__file__).resolve().parents[1] / "web" / "dist" / "assets"

ENABLED = re.compile(r"button:not\(:disabled\)\s*\{[^}]*cursor:\s*pointer")
DISABLED = re.compile(r"button:disabled\s*\{[^}]*cursor:\s*not-allowed")


def _built_css() -> str:
    assert DIST.is_dir(), (
        f"{DIST} is absent, so this gate measured nothing. Run `npm run build` in web/ - "
        "scripts/push.sh does exactly that before the suite. A skip here would be a gate "
        "present but not armed."
    )
    sheets = sorted(DIST.glob("*.css"))
    assert sheets, f"no stylesheet under {DIST}: the build emitted no css to check"
    return "\n".join(p.read_text(encoding="utf-8") for p in sheets)


def test_an_enabled_button_shows_the_pointer_cursor() -> None:
    assert ENABLED.search(_built_css()), (
        "the built css carries no `button:not(:disabled) { cursor: pointer }`, so every button on "
        "the site hovers like plain text - including Submit on /apply/."
    )


def test_a_disabled_button_says_it_refuses() -> None:
    assert DISABLED.search(_built_css()), (
        "the built css carries no `button:disabled { cursor: not-allowed }`. /apply/ disables "
        "Submit until consent is ticked; without this the cursor claims the control is clickable "
        "while it refuses - a refusal the visitor can only discover by clicking."
    )
