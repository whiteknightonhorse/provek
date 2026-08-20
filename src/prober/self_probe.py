"""T-2.12 - the prober, LOADED. The incubator's own mandate and the one claim it tests
(ABI-6-4, ABI-16-5, ABI-5-1).

WHY THIS FILE EXISTS AND NOT ONLY `prober.py`. `src/liveness/obligations.py` sat in the tree for a
week with seven passing tests and two laws, and nothing had ever declared an obligation into it:
every registry in the repository was built by a test and filled by the same test three lines later
(L-18). A prober whose only mandate and only claim are constructed inside `tests/` would repeat that
exactly - the fail-closed behaviour would be correct and the component would never have run. So the
mandate below is declared here, in module scope, outside any test, and `scripts/probe_self.py` is
the production caller that spends it.

WHY THE SUBJECT IS OURSELVES. The same reason the cohort is: this project verifies the operator's
own systems first and marks every row `same_owner`, because a method rehearsed on a stranger is a
method rehearsed at a stranger's expense (ADR-0004, ADR-0006). An unauthenticated access attempt is
the first thing built here that can cost a subject anything at all, and it is pointed at the one
subject whose permission the operator can actually give.

THE MANDATE IS A NEW ONE AND THAT IS DELIBERATE. Eight published passports reference
`self-mandate-0001`, and they were issued for read-only verification under ADR-0006. Widening that
reference to cover active probing would change, retroactively, what eight artefacts already in
public say they were produced under. The active mandate is therefore `self-mandate-0002` and it
grants exactly one action against exactly one origin.

ADJACENT, AND RECORDED RATHER THAN QUIETLY FIXED: `self-mandate-0001` has no document anywhere in
this repository. It is a bare string in `scripts/cohort.py` that eight published passports point at,
which is a reference with no referent - this project's own subject defect, in the field that says by
what authority a subject was touched. Closing it means writing the read mandate down and is a task
of its own; naming it here is what stops it being lost (D-23).
"""
from __future__ import annotations

from datetime import datetime, timezone

from src.mandate.mandate import Mandate
from src.prober.prober import ACTION, ControlClaim

SUBJECT_ID = "git:whiteknightonhorse/provek"
ORIGIN = "https://provek.dev"

SELF_MANDATE = Mandate(
    ref="self-mandate-0002",
    subject_id=SUBJECT_ID,
    permitted_actions=frozenset({ACTION}),
    # Twelve an hour, against a site with no customers. The number is small because the ceiling is
    # the subject's protection and this subject's operator is the person choosing it - a generous
    # self-grant is the one place a mandate costs nothing to write and proves nothing.
    max_calls_per_hour=12,
    blast_radius=(
        "read-only HTTP requests to https://provek.dev only. No POST to /api/apply: that endpoint "
        "writes a durable KV record and sends the operator a notification, so a probe of it would "
        "manufacture an intake submission nobody made and put it in front of a human as though "
        "somebody had. Nothing else on the origin is touched, and no request carries a credential."
    ),
    liability=(
        "the operator, who owns both the verifier and the subject. Stated rather than omitted "
        "because a self-mandate is where a liability clause is easiest to leave blank and hardest "
        "to notice missing - the first mandate signed by somebody else is the one that has to have "
        "this field, and a template with a hole in it is what it would be copied from."
    ),
    abort_condition=(
        "any 5xx from the origin, or a control request that stops answering 2xx: both mean the "
        "site is not serving normally, and continuing would add our requests to whatever is "
        "already wrong. The prober reaches this by refusing to produce a reading rather than by "
        "retrying (src/prober/prober.py, ORIGIN_UNREADABLE)."
    ),
    valid_from=datetime(2026, 8, 20, tzinfo=timezone.utc),
    # NINETY DAYS, AND THE EXPIRY IS THE FEATURE. A mandate without an end is a permission that
    # outlives the reason it was given, and this one is checked against the real clock by
    # `tests/test_prober.py`, which goes red when it lapses. That red is correct: renewing a
    # standing permission to touch a live system is an act somebody should have to perform.
    valid_until=datetime(2026, 11, 18, tzinfo=timezone.utc),
    notes=[
        "Granted by the operator under ADR-0006's identity predicate: the subject is the owner of "
        "the verifier, so this is not a third party's production system.",
        "Superset of nothing: exactly one action, one origin, one protected path.",
    ],
)

SOURCE_EXPOSURE_CLAIM = ControlClaim(
    subject_id=SUBJECT_ID,
    origin=ORIGIN,
    # The landing page. `~/orchestra/deploy.sh` refuses to call a deploy confirmed unless this
    # answers 200, so it is the origin's own declaration that this path is public - which is what
    # an instrument control has to be, rather than a path we picked because it usually works.
    control_path="/",
    # The negative control. A path this site does not serve and no plausible future version will:
    # the comparison it exists for only works if its absence is certain, so it is not a plausible
    # typo of a real route.
    absent_path="/.provek-negative-control-no-such-path",
    protected_path="/.git/config",
    method="GET",
    expected_refusal=frozenset({404}),
    claimed_by=(
        'web/wrangler.toml, `pages_build_output_dir = "dist"` - the published artefact is the '
        "build output, which contains no repository metadata and no unbuilt source"
    ),
)
"""THE ONE CLAIM, AND THE FIRST VERSION OF IT WAS THE DEFECT THIS PROJECT EXISTS TO CATCH.

That version probed `GET /api/apply` expecting 405. Fable refuted it, and the refutation is the
reason this docstring is long. `/api/apply` is a PUBLIC intake endpoint: it accepts anonymous
submissions, that is its purpose, and a 405 on GET is a method restriction rather than an access
control. The subject had not declared that path closed - it had declared it wrong-method. So the
action was named `unauthenticated_access_attempt` while the instance actually wired up was an
ordinary public GET that needs no mandate at all, which is L-13 exactly: the measurement fitted to
the acceptance criterion, and invisible afterwards because the surrounding code looks principled.
The tell was sitting in `prober.py` the whole time - `DECLINES_TO_SAY` excludes 401 as the clearest
evidence a path is protected, the whole design reasons about 401 and 403, and the shipped claim
named 405, which is neither.

WHAT THIS ONE IS INSTEAD. Requesting another party's `.git/config` is the canonical opening move of
an intruder, it appears in the subject's logs as exactly that, and no reading of a published page
resembles it. That is what makes it an act needing written authorisation even though it fails - and
it is why the mandate below is not decoration.

WHAT IT MEASURES, AND IT CAN FAIL. A static host that uploads its working directory rather than its
build output serves `.git/config` with HTTP 200, which hands a reader the repository's remotes and
often more. The claim is addressed to `web/wrangler.toml`, where the subject declares that what
gets published is `dist` - so 200 here would be the deployment contradicting the subject's own
configuration, measured at the origin rather than inferred from the file.

WHAT IT CANNOT ESTABLISH ON THIS SUBJECT, WHICH IS THE SECOND THING FABLE REFUTED. This origin
answers 404 to everything unknown, so `/.git/config` returning 404 reads exactly as
`/.provek-negative-control-no-such-path` returning 404. That is enough to say the file is NOT
SERVED and not enough to say a control refused it - and the difference is the whole subject of this
component. The negative control makes the probe report `INDISTINGUISHABLE_FROM_ABSENT` here rather
than the flattering `ENFORCED` it returned before the third call existed. A PASS on this subject
would need a path whose refusal differs from the catch-all, and this site has none; that is a fact
about a static site with no authenticated surface, and it is left as the measurement rather than
worked around.
"""
