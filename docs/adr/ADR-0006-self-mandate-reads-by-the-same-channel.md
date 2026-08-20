# ADR-0006. A self-mandate reads private code BY THE SAME CHANNEL an external subject would use

**Date:** 2026-08-19. **Status:** accepted. **Basis:** Fable ruling.

## Decision
The narrowing "public repositories only" applies to THIRD PARTIES. The operator's own systems are
not third parties - the exception rests on an IDENTITY PREDICATE (subject == owner of the
verifier), not on discretion.

## What is FORBIDDEN
Reading a subject through host privileges (sudo). A methodology that works only where we are root
is not reproducible by a third party and violates ABI-5-3. Access goes through a scoped read-only
token - the same channel an external subject would grant. Home directories at 0750 stay untouched.

## Mandatory disclosure
`verifier_affiliation: same_owner` in the passport. Without it the first registry entries would
read as independent verifications - a quiet conflict of interest on the shop window.
