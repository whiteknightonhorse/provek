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

# Documentation law (FLEET-DOCS-LAW-1026, operator ruling 2026-10-24)
Observable change = anything a user, agent, integrator or self-hoster can see: behaviour, routes and response fields, MCP tools and prompts, error codes and messages, limits, prices and fees, headers, env/config defaults, CLI flags, served files, page text.
1. Same card. A card with an observable change updates this project's public documentation on the SITE and on GITHUB in the same card. The card header carries `DOCS: <repo path>[, <repo path>...]` naming every documentation surface it edits, and the body has a `## Docs` section (per surface: live URL, GitHub-main URL, the sentence that changes, the grep that proves it live). A card with no observable change carries `DOCS: none - <class>: <reason>`, class in {refactor, tests, infra, internal, journal, fix-to-spec, revert, measure}. An observable change is never exempt; `fix-to-spec` cites the doc line that already states the behaviour; a `revert` of a change that had docs reverts the docs too (then it is not exempt). `MODEL: haiku` cards (read-only, no commit) need no DOCS line.
2. Read before write. Before editing a surface: fetch the CURRENT live page (`curl -sS -D - <url>`, and again with `Accept: text/markdown` where a twin exists), fetch the CURRENT file on GitHub main (`git fetch origin main`; the raw main URL for a repo this tree does not own), and `grep -rn` the fact's key phrase over every surface in section 4. Paste that evidence in the task log BEFORE the edit. Then edit the existing sentence in place. One canonical statement per fact; every other surface links to it (or carries one line plus the link). Never add a paragraph that restates one that exists; never leave an older sentence that now contradicts the new one (grep of the superseded wording = 0 at the end). Append-only files (decision logs, release notes, dated snapshots) are not rewritten: the new entry names what it supersedes and the old entry gets a one-line "superseded by ..." marker or an "as of <date>" label. Counts and generated files are never typed by hand: use the generator or the sync token.
3. Proof. The reviewer rejects: a DOCS surface untouched without a quoted already-correct line; a fact stated twice; a surviving old wording; `DOCS: none` on a diff with an observable change ("docs exemption false"). The reviewer cannot wait for a deploy: the live site and github.com main are checked by the dispatcher after merge from the card's "## After merge (dispatcher)" section (one `curl ... | grep -c` per live URL, one per raw main file; results pasted under the card's knowledge note). A new fact also gets the permanent check named in section 4 where this project has one.
4. Surfaces of this project.
Provek (whiteknightonhorse/provek; tenant tree /home/incubator/incubator):
SITE (provek.dev): web/public/** and the web/src pages (/, /registry/, /method/ and notes, /build/*, /apply/, /phase-2/, /witness/, /challenge/), web/public/llms.txt, web/public/.well-known/agent-registration.json; /data/registry.json, passports, briefs and badges only through scripts/cohort.py.
GITHUB (main): README.md, SPEC.md, DECISIONS.md (append-only: a new D-entry names the superseded one and the old entry gets "superseded by D-nn"), docs/** (WHY_GET_VERIFIED, INTAKE_OPERATIONS, LIVENESS_OPERATIONS, ALERT_TRIAGE, MEASUREMENT_*, adr/), PRODUCT.md, DESIGN.md, SECURITY.md, provek.json, integrations/*/README.md (the mirrors provek-genlayer-witness and apibase-genlayer-attest are re-split by the dispatcher after merge, never edited directly).
PERMANENT CHECK: test_readme_fragment_is_verbatim, test_brief_copy_matches_passport_page, test_apply_*, scripts/dated_promises.py for dated sentences, enforced_by.yaml for a new law; a new user-visible fact with no test gets one in the same card.
NOT documentation: PROGRESS.md, tasks/, CLAUDE.md.
Enforcement of the law above: sections 1-3 by the task engine's DOCS: pre-flight and reviewer clause (~/taskloop/lib/docs-law.sh, outside this tree, as the rollback procedure's machine half lives outside it); section 4 by LAW-DOCS-LAW-STANDS-AND-ITS-SURFACES-EXIST in enforced_by.yaml.

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
