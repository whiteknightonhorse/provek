"""The apply form tells assistive technology which fields are required, offers the browser the right
autocomplete hints, labels the mandate group, and the endpoint answers OPTIONS and GET with `Allow`.

Source assertions: each is able to fail by deleting the attribute it names (evidence/RED-076).
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
APPLY = (ROOT / "web" / "src" / "pages" / "Apply.tsx").read_text(encoding="utf-8")
ENDPOINT = (ROOT / "web" / "functions" / "api" / "apply.js").read_text(encoding="utf-8")
CHROME = (ROOT / "web" / "src" / "components" / "Chrome.tsx").read_text(encoding="utf-8")


def _input(field_id: str) -> str:
    m = re.search(r"<input\s[^>]*?id=\"%s\"[^>]*?/?>" % field_id, APPLY, re.S)
    assert m, f"no <input id={field_id!r}> in Apply.tsx"
    return m.group(0)


def test_repo_and_contact_are_aria_required_and_autocomplete():
    repo, contact = _input("repo"), _input("contact")
    assert 'aria-required="true"' in repo and 'aria-required="true"' in contact
    assert 'autoComplete="url"' in repo
    assert 'autoComplete="email"' in contact


def test_labels_carry_a_visible_required_marker_and_the_form_explains_it():
    for label in ("Repository URL", "Contact"):
        assert re.search(label + r' <span aria-hidden="true">\*</span></label>', APPLY), label
    assert re.search(r'<span aria-hidden="true">\*</span> required', APPLY)


def test_mandate_fieldset_has_a_visible_legend():
    fieldset = APPLY[APPLY.index("<fieldset"):APPLY.index("</fieldset>")]
    assert re.search(r"<legend[^>]*>What you are asking for</legend>", fieldset)


def test_endpoint_answers_options_and_names_its_method_on_405():
    assert "export async function onRequestOptions" in ENDPOINT
    assert 'Allow: "POST, OPTIONS"' in ENDPOINT
    assert '"Access-Control-Allow-Methods": "POST"' in ENDPOINT
    assert "status: 204" in ENDPOINT
    assert 'res.headers.set("Allow", "POST")' in ENDPOINT


def test_the_dead_corpus_nav_item_is_gone():
    assert "Corpus" not in CHROME
    assert "aria-disabled" not in CHROME
