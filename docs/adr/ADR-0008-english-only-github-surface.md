# ADR-0008. The GitHub surface is English-only

**Date:** 2026-08-19. **Status:** accepted. **Basis:** operator ruling.

## Decision
Everything that reaches GitHub is in English: code, comments, docstrings, documents, YAML, and
commit messages. Working documents that live on the operator's laptop stay in Russian - the
repository is what other people read.

## Enforced, not requested
`scripts/ratchet_language.py` fails the build on Cyrillic in tracked files, and `scripts/push.sh`
runs it as step 4 of 5. A rule with no armed gate rots into a comment; this project has already
paid for that twice.

## Two named exemptions, neither of them silent
* `evidence/` - archived run output. Historical artefacts are never rewritten.
* Commits at or before `987d209` - authored before this ruling and already pushed. Rewriting
  published history is worse than the defect it would fix, and the project's own doctrine is
  supersede-never-erase: a record that disappears reads as closure to anything that reads absence
  as resolution.

A checker that silently skips what it cannot fix reports success on it. Both exemptions are
printed by the gate itself, together with their reasons.

## Scale
47 files carried Russian at the moment of the ruling. All were translated, and the substance of
the reasoning was preserved rather than summarised - in this project the docstrings carry the
arguments, not decoration.
