# ADR-0002. Transport independence is machine-checked, not agreed

**Date:** 2026-08-19. **Status:** accepted. **Refines:** ADR-0001.

## Decision
`scorer` imports nothing transport-related, and a test proves it by parsing the AST.

## Why AST and not grep
The first version of the test grepped the file text and FAILED on its own name, quoted in the
module docstring. A test that fails on documentation of a constraint pushes people to stop
documenting the constraint. What must be checked is the DEPENDENCY, not the mention.

## Instrument control
Next to it sits `test_the_transport_check_is_ABLE_to_fail` - the check must catch a planted
import, otherwise it is decoration. The instrument is adjudicated before it is believed.
