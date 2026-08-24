---
{
  "slug": "not-measured-is-not-zero",
  "title": "The vocabulary of absence in a measurement - Provek",
  "h1": "Three absences, and the fourth an instrument invents",
  "description": "States what nothing_qualified, check_did_not_run, and unreadable each mean, and the fourth absence: an instrument blind to a quantity reporting it as a finding.",
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
    "topics_sha256": "44957c1f90a68e7b14bd005585339d07bcd2c5ba30028263475145cd919da03b",
    "generator_sha256": "219c38db5b7498a6f8cd93face8c8e182f114895bf0fce77395e37241e0b7a07",
    "plan_sha256": "1820173eaaec1ae512d8fdb4687babee329b91a6197d62f3f57e76d85c4a48dc"
  },
  "lifecycle": {
    "status": "current",
    "corrections": []
  },
  "keys_absent_reason": "nothing_on_topic_in_base",
  "keys_absent_detail": "The keyword base holds no row whose subject is the distinction between kinds of absence: zero question rows and no statement row about measurement discipline. The nearest cluster is audit ('ai agent audit process', 'what is an ai audit'), which is a different subject. Putting an audit key in this note's title would make a page whose string and whose measured demand are about different things - the defect the base's own generic_term rule was written to catch."
}
---

A passport renders absence in three distinct named states rather than a zero: nothing_qualified when the check ran but matched nothing, check_did_not_run when the check never ran, unreadable when the source refused to answer. Beside these sits a fourth absence that lies outside the taxonomy - an instrument that cannot see the quantity it was asked about, which returns success and empty data, indistinguishable from a true zero at the point of reading.

## Three states a measurement can carry instead of a number

The [SPEC §3.1](/method/) requirement is that each operation carries either a measurement level or, when absent, its reason. Three absence states exist: `nothing_qualified` when the check ran but found nothing, `check_did_not_run` when it never ran, and `unreadable` when the source refused to answer. These are members of the `NotMeasured` enumeration in `src/abs_profile/measured.py`.

A `Measurement` object enforces a strict rule: it holds either a value or an absence reason, never both and never neither. This guards against the defect that haunted seven production systems, where "no data" and "the source is dead" became indistinguishable. Decision D-03 requires that absence appear always as text and reason, never as zero or blank.

The `gate_verdict` method returns PASS, FAIL, or NOT_MEASURED. Absent measurements are never treated as failures (ABI-33-4). Absence and violation are separate facts requiring separate operator responses.

## The defect this taxonomy was built to stop

One twelve-week source outage went undetected because its signature-no return values-matched the signature of a system with no findings. This pattern repeated across seven instances in the operator's production systems, in each case preventing detection of the actual failure state.

Fixing it required accepting visible consequences: Decision D-03 mandates that absence appear textually with its reason, and as a result, two of every three operations on each current subject read `not_measured` in the [registry](/registry/). The resulting tables look sparse-and that sparseness is the truth of the measurement landscape, kept visible rather than hidden under zeros.

## A fourth absence: an instrument blind to the quantity

The first three absence states describe checks that ran or did not. A fourth emerges from checking against the wrong instrument. When `/commits/{sha}/status` returned zero statuses, that was correctly read as "no deploy integration" - the reading was sound, the measurement empty.

Against the same commits, `/commits/{sha}/check-runs` returns four successful runs - the legacy endpoint does not. A conclusion from an incapable instrument is not evidence, more dangerous when correct because it repeats.

This extends the three siblings by a third: beside `nothing_qualified` and `unreadable` sits "the wrong source was asked". HTTP 200 with an empty list is indistinguishable from true zero. A check against the legacy endpoint looks identical to a system genuinely publishing nothing.

Fable discovered this while refuting a brief offering the empty measurement as proof. The armed instance: every passport publishes the `access_channel` its evidence arrived through - LAW-GRANTED-CHANNEL-ONLY, `tests/test_granted_channel_only.py`.

## The same failure wearing a different mechanism

A Bing probe read `https://provek.dev/BingSiteAuth.xml` with Python's default user agent and got `403` - as it did for the homepage, which a browser agent gets `200` for. Cloudflare refused the client, not the resource; it was one line from being logged as `carries_expected_code: false`.

Written that same hour to honour L-10, the probe already ran a control site beside every zero-capable call. The lesson did not transfer because it arrived as "ask the right endpoint" and this failure has a different mechanism: the right endpoint, correctly asked, returning status that encodes the asker rather than the resource.

Before recording absence, establish that the instrument would have seen presence. [The specification](/method/) §3.1 demands this discipline. `404` is absence. `403`, `429`, `5xx` are the server declining to say; they land in `not_measured`, never in the same field as a measured `false`. The probe honoured this rule for one blindness - asking the wrong endpoint. Here, with the right endpoint and right call, the mechanism differed, and without code enforcing it, the lesson did not persist.

## Absence as measured in this project's own keyword capture

The `bing_serp_related` source answered with HTTP 200, carrying ten organic results including python.org, yet yielded zero related-question items across responses of 117 kB and 124 kB. Whether an empty result reflects true absence or blindness in the client cannot be determined from the signal alone.

Three control queries supplied the ground truth: `weather` and `how to boil an egg`, chosen as the least plausible things on the web to have no related searches, both returned zero. The third control's full response page also yielded nothing. An empty result from an instrument that cannot be shown able to see the quantity is a statement about the client, not about Bing.

This source is recorded `unreadable` and contributes no keys to the [registry](/registry/) and no zeros to any field; a test refuses to let a blind source do either, and refuses, separately, to let any source with a zero-returning control be `ok`.

GetKeyword gave 812 readings and then returned `{"ErrorCode":4,"Message":"ThrottleUser"}` — a quota on the Bing account, not a property of the keywords. A second attempt at one call per second met the same refusal on all 43 rows it reached before stopping. These 427 rows remain `unreadable`; writing zero there would destroy the only evidence that the reading never arrived.

Nothing_qualified is the state where the instrument answered completely. Bing has no impressions for that exact query in the measurement window, the expected reading for most keywords. ERC-8004's own name returns nothing — `GetRelatedKeywords("erc-8004")` came back with an empty list, and `GetKeyword("erc-8004")` with `Query: null`. This standard, as measured, has no search demand at all. 733 rows carry this state.

The single `check_did_not_run` row is endpoint domain verification. Normalisation stripped the `(Optional)` qualifier from the standard's heading; the demand figure belonged to the unstripped string. A reading belongs to the string it was taken for, so it was discarded. The [specification](/method/) §3.1 demands this discipline — before recording absence, establish that the instrument would have seen presence.

{{figure:keyword-demand-states}}

## Where the reason travels inside the passport

A per-operation table at [SPEC](/method/) §3.1 shows level L0-L5 or, if `not_measured`, its reason, confidence, and applicable limiters. Accountability fields mirror this structure: each carries its value or the reason for none, recorded as {value, measured, reason} in D-13, default `measured: false, reason: check_did_not_run`. Schema 2.0.0; every passport re-emitted.

Until 2026-08-20 the specification broke this symmetry. Item 5 granted "claims addressee (which may honestly be none)" — no reason required — while item 3, two lines above, demanded a reason for every unmeasured operation. Three emitters took the licence and built accountability blocks from defaults without inspecting them. Every passport under schema 1.0.0 claimed a completed check that never ran.

Fable's ruling held the schema the primary defect, the specification complicit. The front door, which rendered the same null two ways in adjacent rows, was acquitted: that inconsistency detected the defect. Schema 1.0.0 let a field carry absence without its reason, making the unchecked field indistinguishable from a measured answer. The accountable statement and the non-inspected field look identical at the point of reading.

The reason must travel with the field into a [registry](/registry/) entry, quotation, or report. The wrapper sits on every field rather than on a coverage list elsewhere because the distinction survives citation only when it travels in the data itself. That structural requirement is what the three absences — `nothing_qualified`, `check_did_not_run`, `unreadable` — exist to enforce.

{{figure:registry-coverage}}
