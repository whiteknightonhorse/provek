"""T-2.16 - the deterministic half of the Amadeus demo.

The SDK arm lives in `demo/amadeus/auditor.mjs` and gathers; everything that decides is here,
because invariant 2 puts PASS/FAIL in code taken from a measured quantity, and because a rule
that lived in the JavaScript would be a rule the Python gates cannot test.
"""
