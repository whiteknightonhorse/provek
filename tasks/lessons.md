# Project laws

Grows as work proceeds. Every law MUST have an anchor in `enforced_by.yaml`.
A law with no armed gate is a defect, not a note.

## L-1 A return value that means two states of the world
"No data" and "the source is dead" must never read identically. Seven instances in the operator's
systems; a twelve-week source outage hid in exactly this shape.
Anchor: LAW-NOT-MEASURED.

## L-2 A rule written in more than one place survives its own repeal
Before declaring a rule repealed, find ALL of its copies.
Anchor: LAW-DECISION-RATCHET.

## L-3 Measure the shipped artefact
A file in the repository, a registry row and an exit code are not what the consumer receives.
Anchor: LAW-MEASURE-SHIPPED.

## L-4 A gate that does not stop is not a gate
The first push succeeded while the ratchet was red, because the checks ran without `set -e`.
Anchor: LAW-GATE-MUST-BLOCK.

## L-5 A pipeline's exit status belongs to its LAST command
The secret scan ended in `| head -5` and therefore always reported success, blocking a clean tree.
A false red teaches bypassing the gate exactly as a false green does.
Anchor: LAW-GATE-MUST-BLOCK.

## L-6 A checker that inspects one shape reports success on every other
The scope ratchet looked only at `*.py`; shell scripts were outside supervision entirely.
Anchor: LAW-SCOPE-RATCHET.

## L-7 A rule that lives only in a comment is not enforced
The weak-signal limiters were a docstring note until they became code.
Anchor: LAW-WEAK-SIGNAL-LIMITERS.

## L-8 On a shared host, a file you cannot write may still be one you read

`git commit -F /tmp/m.txt` picked up ANOTHER project's commit message. The host has ten project
users; `/tmp/m.txt` already existed and belonged to one of them. The write failed with permission
denied - which is visible - but the read succeeded silently, and the commit landed carrying a
message about a completely different codebase.

Two things made it survivable: the commit had not been pushed, and the language gate would have
caught it at the door anyway. Neither is a reason to rely on luck.

Rule: scratch files go to the project's own directory, never to a shared `/tmp`. The same host
already carries a related trap - a stray `/tmp/re.py` shadows the standard library for any script
run from there.

Anchor: no code gate. This is a working habit, and it is recorded as such rather than pretended to
be enforced - a law with a fake anchor is worse than an honest note.
