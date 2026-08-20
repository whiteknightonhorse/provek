# Project rules

## Load-bearing invariants (a violation is a red build, not a remark)

1. **`not_measured` is a state of its own.** Not a zero, not a default, not a missing field.
   Any counter that can read zero distinguishes `nothing_qualified` / `check_did_not_run` /
   `unreadable`. This is the most frequent defect in the operator's systems - seven instances.
2. **The verdict is computed by DETERMINISTIC code.** An LLM may gather and reason, but PASS/FAIL
   is taken by code from a measured quantity. A failed LLM is a red result, never a skip.
3. **`scorer` does not import transport.** Transport independence is a machine guarantee, proven
   by an AST test, not by convention.
4. **Every module is bound to an `ABI-*` requirement.** An unbound module fails the build.
5. **A test MUST BE ABLE TO FAIL.** "The section exists" is not a test; the red run is kept as an
   artefact under `evidence/`.
6. **L0-L5 is the subject's autonomy ladder. P0-P5 are our agents' permissions.** Using "L" for
   permissions is a defect.
7. **The entire GitHub surface is ENGLISH ONLY** - code, comments, documents, commit messages.
   Working documents on the operator's laptop stay in Russian; the repository is what others read.
8. Never `--no-verify`, never `push --force` to main. The only door outward is `scripts/push.sh`.

## Resource budget (measured 2026-08-19; ten projects share this host)
disk 10 GB - memory 1.5 GB - CPU <= 1 core - **concurrency = 1 process**
Clones are `--depth 1` and the working copy is deleted after the audit.
On contention THIS project yields; deferral is a named finding, not silence.
