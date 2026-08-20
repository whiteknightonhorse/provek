# CI gates

Four jobs, mirroring `scripts/push.sh` so that the checks stop depending on who pushes:

| job | what fails the build |
|---|---|
| `ratchets` | a module with no ABI requirement; a law with no armed gate; Cyrillic on the GitHub surface |
| `tests` | any test failing, or coverage under 70% |
| `lint` | ruff findings |
| `secrets` | a secret-shaped string anywhere in the tree |

## Why the ratchets are the important part

The other three jobs are standard hygiene. The ratchets are what make this project's own laws
falsifiable: scope sprawl, dangling rules and language drift all become red builds rather than
things somebody notices later.

## Known dated condition

Actions minutes on this account are exhausted until **2026-09-01**. Until then these workflows do
not run, and `scripts/push.sh` remains the enforcing path. This is a billing state with a date on
it, not a broken pipeline - and when the repository goes public, Actions become free and the
condition disappears for good.

`mypy` is currently advisory (`|| true`): the codebase has no type-checking baseline yet, and a
gate that fails on day one gets disabled by whoever meets it. It becomes blocking once a clean
baseline exists - and that promise is recorded here rather than left as an intention.
