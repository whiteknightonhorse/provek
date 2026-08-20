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

## L-9 Trace the path to the acceptance criterion BEFORE taking the step

A task whose gate is a live URL begins by establishing how a commit becomes that URL. This one did
not: the page was built, reviewed, corrected and pushed before anyone asked what publishes it, and
the answer turned out to be a manual `wrangler pages deploy` needing a credential this host does not
hold. A push to `main` publishes nothing here.

The path was readable in advance - `web/wrangler.toml`, a `.wrangler/cache` in the tree, and an
`AUDIT.md` that names the Pages project while saying nothing about the mechanism. Cost was small
(the push was needed anyway) and the damage was to the ORDER in which facts were discovered, which
is exactly the damage that is invisible until it is large.

Anchor: no code gate. A checker cannot know which of a task's criteria is the load-bearing one. It
is recorded as a habit, in L-8's form, rather than dressed as an enforced rule.

## L-10 A wrong instrument reports absence, and absence reads as a finding

`/commits/{sha}/status` returned zero statuses for every commit in this repository, and that was
read as "no deploy integration". The reading happened to be right; the measurement was empty.
`/commits/{sha}/check-runs` returns four successful runs on the same commits - the legacy endpoint
simply does not carry what the modern one does. A conclusion drawn from an instrument that cannot
see the quantity is not evidence, and it is more dangerous when correct, because it will be repeated.

This extends L-1 and specification 2.9 by a third sibling. Beside `nothing_qualified` and
`unreadable` sits **the wrong source was asked** - a state that answers HTTP 200 with an empty list
and is therefore indistinguishable from a true zero at the point of reading.

Found by Fable while refuting a brief in which the empty measurement was offered as proof.

Anchor: no code gate for the general rule - a checker cannot know that an endpoint is blind. One
instance of it IS armed, and it is the model to copy: every passport publishes the `access_channel`
its evidence arrived through, so a verdict carries the instrument beside the reading
(LAW-GRANTED-CHANNEL-ONLY, `tests/test_granted_channel_only.py`).

## L-11 The origin answers a different question depending on who asks

The Bing probe read `https://provek.dev/BingSiteAuth.xml` with Python's default user agent and got
`403` - as it did for the homepage, which a browser agent gets `200` for. Cloudflare was refusing
the CLIENT, and the probe was one line from writing that refusal into the log as
`carries_expected_code: false`, i.e. as a finding about whether the site publishes the file.

What makes it worth a law of its own beside L-10 is WHEN it happened. The probe was written that
same hour, deliberately, to honour L-10 - it already ran a control site beside every zero-capable
API call. The lesson did not transfer, because it had been learned in the shape "ask the endpoint
that carries the quantity" and this failure has a different mechanism: the right endpoint, asked
correctly, returning a status that encodes the asker's identity rather than the resource's state.

Rule: a status code is not a measurement until the client has been ruled out as its cause. `404` is
absence. `403`, `429` and `5xx` are the server declining to say, and must land in a state named for
not knowing - never in the same field as a measured `false`. The general form: **before recording
absence, establish that the instrument would have been able to see presence.**

Anchor: no code gate here - this repository does not own the probe, which lives at
`~/orchestra/bing_probe.py` (a Bing client is bound to no `ABI-*` requirement, so `scripts/` would
have to be rubber-stamped to hold it). Recorded in L-8's and L-9's form as a habit, not dressed as
an enforced rule.
