---
{
  "slug": "not-measured-is-not-zero",
  "title": "Four Ways a Measurement Can Be Absent - Provek",
  "h1": "Four states of absence, and the one that hides as a finding",
  "description": "Distinguishes nothing_qualified, check_did_not_run and unreadable, plus the state where a blind instrument's empty reading reads as a finding.",
  "keys": [],
  "addresses": [
    {
      "ref": "SPEC §3.1",
      "file": "SPEC.md",
      "anchor": "### 3.1 Passport",
      "url": "/method/"
    },
    {
      "ref": "D-03",
      "file": "DECISIONS.md",
      "anchor": "## D-03. `not_measured` is rendered as its own state, never as zero or blank"
    },
    {
      "ref": "D-13",
      "file": "DECISIONS.md",
      "anchor": "## D-13. Absence carries its reason everywhere, not only inside the score"
    },
    {
      "ref": "L-1",
      "file": "tasks/lessons.md",
      "anchor": "## L-1 A return value that means two states of the world"
    },
    {
      "ref": "L-10",
      "file": "tasks/lessons.md",
      "anchor": "## L-10 A wrong instrument reports absence, and absence reads as a finding"
    },
    {
      "ref": "L-11",
      "file": "tasks/lessons.md",
      "anchor": "## L-11 The origin answers a different question depending on who asks"
    },
    {
      "ref": "the registry",
      "file": "public/registry/registry.json",
      "anchor": "\"disclaimer\"",
      "url": "/registry/"
    },
    {
      "ref": "the keyword base",
      "file": "seo/KEYWORD_BASE.md",
      "anchor": "# Keyword base"
    }
  ],
  "figures": [
    {
      "id": "registry-coverage"
    },
    {
      "id": "keyword-demand-states"
    }
  ],
  "faq": [],
  "provenance": {
    "plan_model": "claude-sonnet-5",
    "prose_model": "claude-haiku-4-5",
    "generated_at": "2026-08-24",
    "topics_sha256": "92359f33c15c21e05fdc8ba6030b8b74f393b5eb25bc96a68e0f9f80521c3652",
    "generator_sha256": "bbea990ba7773340efd88c806a7fca00008e597099f09397289b814ed1a5c56c",
    "plan_sha256": "6f9a2f3990bdfc1f9fa8dcb101822586b6fbccd805bb6dad36484389e9456303"
  },
  "lifecycle": {
    "status": "current",
    "corrections": []
  },
  "keys_absent_reason": "nothing_on_topic_in_base",
  "keys_absent_detail": "The keyword base holds no row whose subject is the distinction between kinds of absence: zero question rows and no statement row about measurement discipline. The nearest cluster is audit ('ai agent audit process', 'what is an ai audit'), which is a different subject. Putting an audit key in this note's title would make a page whose string and whose measured demand are about different things - the defect the base's own generic_term rule was written to catch."
}
---

An unmeasured field is not a blank. A passport must name which of three reasons left an operation unmeasured: the check did not run, it ran but nothing qualified, or the source refused to answer. A fourth exists: an instrument that cannot see the quantity, producing an indistinguishable reading. Unless the instrument's reach is disclosed alongside the finding, absence remains indistinguishable from the three.

## Three states, not a blank

The passport distinguishes three states of absence: `nothing_qualified` when the check ran and found no match, `check_did_not_run` when the check never ran, and `unreadable` when the source declined to answer.

Each measurement carries exactly one of: a value, or the reason it is absent. A `Measurement` dataclass enforces this by rejecting any instance that is both empty and doubled. One return value meaning two states of the world caused seven defects in the operator's systems, including a twelve-week outage where "no news" and "the source is dead" returned identically, hiding the failure from monitoring.

As [the method](/method/) specifies, every operation must show either a level or `not_measured` with its reason. Two of three operations on every current subject read `not_measured`. The table looks sparse, and that sparseness is the truth staying visible. An interface rendering absence as zero would reintroduce the defect: "the source is dead" mistaken for "nothing matched".

An instrument that cannot see a quantity still answers HTTP 200 with an empty list, indistinguishable from a true zero at the point of reading. A conclusion drawn from such an instrument is not evidence, and it becomes more dangerous when it happens to be correct.

## The accountability block's separate discipline

The accountability block requires each field to be `{value, measured, reason}` with defaults `measured: false, reason: check_did_not_run`. All passports were re-emitted under schema 2.0.0 from 2026-08-20 onward.

Under 1.0.0, the block was `T | None` and emitters built from defaults without inspecting anything. Artefacts claimed "we checked and found none" while meaning "nobody looked". The specification enabled this defect: [the method](/method/) demanded a reason for every unmeasured operation in item 3, then granted an honest `none` to the accountability block in item 5 without requiring the same apparatus. Three emitters took that licence, and every passport under 1.0.0 falsely claimed a completed check.

Fable's ruling on 2026-08-20 named the schema as primary defect and the specification as complicit. The front door — which rendered nulls inconsistently in adjacent rows — was acquitted because that inconsistency is what revealed the defect. The specification's erratum in item 5 acknowledges it granted the conclusion without apparatus.

The wrapper is per-field rather than a coverage list because the distinction must survive quotation. This mirrors the logic that keeps `verified` and `self_reported` on separate branches: the structure must persist when extracted or cited, not collapse under selection. A JSON export carrying an addressee field must show whether that addressee was measured or defaulted.

LAW-NOT-MEASURED lived in the `Measurement` class, not enforced at the boundary. Exemption from the score silently became exemption from measurement discipline — fields bypassing that class never had to declare absence. Schema 2.0.0 gates at the boundary itself: `tests/test_no_bare_nulls.py` rejects any document containing a null without the reason wrapper. Now the invariant has machinery behind it.

## When the instrument cannot see the quantity

The three named states - nothing_qualified, check_did_not_run, unreadable - occupy distinct places in the grammar of absence. A fourth sits at the boundary: an endpoint that cannot see a quantity returns HTTP 200 with an empty list, indistinguishable from zero at the point of capture. Two GitHub endpoints show the risk. The `/commits/{sha}/status` endpoint reported zero integrations for every commit; the reading was correct. The `/commits/{sha}/check-runs` endpoint returned four runs on the same commits. The legacy API cannot carry what the modern one does.

A conclusion drawn from an instrument that cannot see the quantity is not evidence. It is more dangerous when correct, because it will be repeated elsewhere. The wrong-source state is the fourth member in the operation-level absence grammar of [the method](/method/): beside nothing_qualified and unreadable sits the case where an endpoint was asked, answered 200 with no data, and vanished into zero.

Fable found this while refuting a brief that used an empty measurement as proof. The reading was correct - no deploy integrations existed - but the proof was invalid, because it came from an instrument blind to deploy integrations. This form of failure is most dangerous when correct: the conclusion will be trusted and the pattern will be repeated without record of its source.

No general code gate exists for this failure, because a checker cannot know an endpoint is blind. One instance is armed as a model: every passport in [the registry](/registry/) carries the `access_channel` field, declaring which instrument supplied the evidence. This allows verdicts to carry both reading and instrument, governed by LAW-GRANTED-CHANNEL-ONLY. The test `tests/test_granted_channel_only.py` rejects any passport missing or mismatching the channel.

## Where this showed up in the keyword base

The bing_serp_related source is the only candidate for "people also ask" items. It answered HTTP 200, carried organic results including python.org, but yielded zero related-question items - recorded as `unreadable` in [the method](/method/), contributing no keys and no zeros. An instrument that cannot be shown to see a quantity cannot yield a reading about the measured property.

Three control queries were run before trusting this zero: "weather" and "how to boil an egg" were chosen as implausible to have no related searches. All three returned zero despite 117 kB and 124 kB response bodies. L-10 requires measuring a source's ability to see non-zero before trusting its zero as a reading.

**Erratum, 2026-08-24 — T-B10, D-34:** all three controls returned zero, so the ability to see quantity was argued from plausibility rather than measured. Zero controls establish nothing in either direction. The honest state is `capability_unproven` - a statement about nobody, not the client. The source contributes no keys and no zeros. This defect appears in the repository's own explanation at source material lines 100-135.

Demand data retrieval faced different constraints. `GetKeyword` returned 812 readings then `{"ErrorCode":4,"Message":"ThrottleUser"}` - a quota on the account, not a fact about keywords. Those 427 rows sit in `unreadable` state. A second pass at one call per second met the same refusal on 43 more rows. The state records what is known: the instrument would not answer.

`nothing_qualified` names a different absence: 733 rows where the instrument answered and Bing carries no demand data for those terms. The check ran and nothing matched. Unlike `unreadable`, the instrument can see the quantity; it simply found none.

{{figure:keyword-demand-states}}

## What a passport's per-operation table renders

A passport's per-operation table embodies decision D-03: every unmeasured operation shows the word `not_measured` and its reason, never blank or zero. Each row names an operation, assigns a level from L0 to L5, carries confidence (`measured` or `inferred`), and lists the limiters applied. When an operation remains unmeasured, the reason is one of three forms: `nothing_qualified` when the check ran but matched nothing, `check_did_not_run` when the check never executed, or `unreadable` when the source refused to answer.

L-10 names a fourth absence: the wrong source was asked. An endpoint answers HTTP 200 with an empty list, indistinguishable from true zero at the point of reading. A conclusion drawn from an instrument that cannot see the quantity is not evidence. Before recording absence, the instrument must be shown able to see presence. This extends the project's foundational rule from L-1: "no news" and "the source is dead" must never read the same.

The table stays sparse by design. Two of three operations on current subjects read `not_measured`, and that sparsity is the truth the artifact must keep visible. This rendering prevents the collapse that caused seven production defects across the operator's systems.

Beside the per-operation table sits the control map, detailing what was inspected, what lay out of reach and why, and what an undiscovered path would look like. Coverage statements anchor measurement in reality rather than assumption.

The projection 0-100 appears adjacent to a disclaimer clarifying that the score measures autonomy and explicitly not reliability, decision quality, profitability, or the presence of an accountable party. This disclaimer is never in a footnote, and the placement matters: the score and its constraint must be read together.

Gate logic processes these states according to [the specification](/method/), implementing ABI-33-4: when `Measurement.gate_verdict()` returns PASS, FAIL, or NOT_MEASURED, an absent measurement is never treated as failure. "The subject failed" and "we could not measure the subject" are distinct statements requiring different responses. Missing measurement is not a violation.

The [registry](/registry/) publishes the `access_channel` through which each measurement arrived, pairing the instrument with the reading. This prevents the instrument's blindness from dissolving into an empty result.

{{figure:registry-coverage}}
