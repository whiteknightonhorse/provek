# ADR-0003. The STATUS registry is ours; the IDENTITY registry is not

**Date:** 2026-08-19. **Status:** accepted. **Corrects:** an omission in plan v1.0.

## Decision
`src/registry/public_registry.py` is our public registry of verification statuses. Identities come
from ERC-8004 (ADR-0001) and are not duplicated by a registry of our own.

## Why this was nearly lost
The slogan "the standard will eat a proprietary registry" is true ONLY of an identity registry.
A status registry is the subject of the product and a direct requirement (ABI-19-2). The first
draft of the plan had no ticket for it at all: passports were produced and nobody published them.
Found by Fable while reviewing the plan. The error class: an over-broad slogan swallowed whole.

## Consequence
The pitch to an external subject ("a passport as an artefact for THEIR customers") now has
something to point at: a public, machine-readable artefact with the caveat next to the score.
