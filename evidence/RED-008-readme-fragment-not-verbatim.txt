# RED-008 - the README verdict fragment stops being a quotation
#
# Produced deliberately on 2026-08-20 to establish that
# tests/test_readme_fragment_is_verbatim.py CAN fail (invariant 5). The 'treasury_control'
# operation was deleted from the JSON block in README.md - exactly the abridgement the
# original spliced fragment made silently - and the suite was run. README was restored
# immediately afterwards. Everything below this line is verbatim tool output.
#
# $ python3 -m pytest tests/test_readme_fragment_is_verbatim.py -q
..F.                                                                     [100%]
=================================== FAILURES ===================================
____ test_fragment_is_the_operations_array_of_the_passport_the_readme_names ____

    def test_fragment_is_the_operations_array_of_the_passport_the_readme_names() -> None:
        """The content is THAT passport's operations array, entire and in order."""
        parsed = json.loads(_fragment())
        source = _linked_passport()
        doc = json.loads(source.read_text(encoding="utf-8"))
        ops = doc.get("passport", {}).get("verified", {}).get("operations")
        assert isinstance(ops, list), (
            f"{source.name} carries no passport.verified.operations array, so the README's quotation "
            "has no source to be checked against."
        )
        if ops == parsed:
            return
>       pytest.fail(
            "the README fragment under 'What a verdict looks like' is not the "
            f"passport.verified.operations of {source.name}, which is the file the README links to.\n"
            f"  README shows {len(parsed)}: {_summarise(parsed)}\n"
            f"  {source.name} has {len(ops)}: {_summarise(ops)}\n"
            "Re-copy the block from that passport, or repoint the link at the passport it really came "
            "from. Editing this test to match the README instead would be the rubber stamp the "
            "ratchets exist to refuse."
        )
E       Failed: the README fragment under 'What a verdict looks like' is not the passport.verified.operations of git_whiteknightonhorse_APIbase.json, which is the file the README links to.
E         README shows 2: development_initiation=L4, deployment=check_did_not_run
E         git_whiteknightonhorse_APIbase.json has 3: development_initiation=L4, deployment=check_did_not_run, treasury_control=check_did_not_run
E       Re-copy the block from that passport, or repoint the link at the passport it really came from. Editing this test to match the README instead would be the rubber stamp the ratchets exist to refuse.

tests/test_readme_fragment_is_verbatim.py:162: Failed
=========================== short test summary info ============================
FAILED tests/test_readme_fragment_is_verbatim.py::test_fragment_is_the_operations_array_of_the_passport_the_readme_names
1 failed, 3 passed in 0.03s
