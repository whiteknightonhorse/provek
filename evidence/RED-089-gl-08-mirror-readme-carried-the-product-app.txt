RED-089 - the mirror README carried the product app (T-GL-08)
tree: cb0eb1bd0a0e089290fb84df318376e64096ccc6 (dirty)
base: origin/main cb0eb1b
Mon Nov  9 08:25:56 AM UTC 2026

## RED: pre-edit integrations/genlayer-witness/README.md (origin/main cb0eb1b) with the new test
$ python3 -m pytest tests/test_witness_relay.py -q -k live_app_section
E           assert '## GenLayer...s — live app' not in '# Provek Ev..." section.\n'
E             
E             '## GenLayer Evidence Witness — live app' is contained here:
E               de here.
E               
E               ## GenLayer Evidence Witness — live app
E               
E               **What it does.** A web page, [https://provek.dev/witness/](https://provek.dev/witness/), for the...
E             
E             ...Full output truncated (499 lines hidden), use '-vv' to show

tests/test_witness_relay.py:385: AssertionError
=========================== short test summary info ============================
FAILED tests/test_witness_relay.py::test_the_live_app_section_is_in_the_product_readme_only
1 failed, 32 deselected in 0.11s

## GREEN: new README
.                                                                        [100%]
1 passed, 32 deselected in 0.03s
