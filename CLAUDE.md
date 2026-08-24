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

## Rollback procedure (the return point is a commit; the damage need not be tracked)

`git reset --hard` restores TRACKED files and does not touch untracked ones, so a rollback can
leave exactly half of a broken state standing. On 2026-08-24 at 06:34 that happened in this tree:
the reset returned the note manifest lines and left behind the two note sources they belonged to,
the orphaned sources crashed `loadNotes()`, the gates read RED **after** the rollback, and the
orchestra halted - correctly, over damage the rollback itself had created.

Before `git reset --hard`, `git checkout -- .` or `git stash` here:

1. **Inventory first**, because after the fact your own wreckage is indistinguishable from work
   that was already lying here:
   `git status --porcelain -z -uall | tr '\0' '\n' | grep '^?? ' | cut -c4- | sort`.
   `-z` is not a preference: without it git QUOTES non-ASCII names, and a quoted name is not a
   path any later command can resolve - measured, `~/orchestra/evidence/RED-H7-*`.
2. **Roll back.**
3. **Inventory again and take the difference.** A missing before-inventory is `not_measured`,
   never "nothing appeared" - invariant 1, applied to the repair rather than to the product.
4. **Park what appeared - MOVE it, never delete it.** Wreckage of a failed task goes to
   `~/orchestra/quarantine/<UTC>-<task>/`, work deliberately set aside to
   `~/orchestra/parked/<task>-<date>/`, in both cases with a file beside it saying why. `git clean`
   is forbidden in this project without exception: it is one keystroke from erasing the evidence
   corpus, the only asset here that cannot be rebuilt.
5. **Re-run `./scripts/push.sh --gates-only`.** Green only after the park means the damage was in
   the untracked half, and that is a finding to report by name, not a footnote.

No gate in this repository enforces those five steps, and D-29 records why one cannot exist:
a check whose trigger is the action it polices measures the person, not the tree (L-19). The
machine half lives where a program does the rollback - `~/orchestra/orch.sh`.
