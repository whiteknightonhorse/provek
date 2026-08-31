---
{
  "slug": "autonomy-levels-l0-l5",
  "title": "AI Agent Autonomy Levels: The L0-L5 Ladder - Provek",
  "h1": "AI Agent Autonomy Levels: What Each Rung Requires as Evidence",
  "description": "This method note defines ai agent autonomy levels L0 through L5, what evidence each rung requires, and which thresholds are assigned rather than measured.",
  "keys": [
    {
      "key": "ai agent autonomy levels",
      "demand_state": "nothing_qualified",
      "source_id": "bing_autosuggest",
      "role": "primary"
    },
    {
      "key": "levels of autonomy for ai agents",
      "demand_state": "unreadable",
      "source_id": "bing_autosuggest",
      "role": "supporting"
    },
    {
      "key": "agent autonomy levels reference model",
      "demand_state": "nothing_qualified",
      "source_id": "bing_autosuggest",
      "role": "supporting"
    }
  ],
  "addresses": [
    {
      "ref": "SPEC §3.1",
      "file": "SPEC.md",
      "anchor": "### 3.1 Passport",
      "url": "/method/"
    },
    {
      "ref": "SPEC §7",
      "file": "SPEC.md",
      "anchor": "## 7. What we may honestly claim, and what would be a lie"
    },
    {
      "ref": "src/abs_profile/ladder.py",
      "file": "src/abs_profile/ladder.py",
      "anchor": "class L(IntEnum)"
    },
    {
      "ref": "D-11",
      "file": "DECISIONS.md",
      "anchor": "## D-11. Binding strength is shown, not implied"
    },
    {
      "ref": "the registry",
      "file": "public/registry/registry.json",
      "anchor": "\"disclaimer\"",
      "url": "/registry/"
    }
  ],
  "figures": [
    {
      "id": "registry-coverage"
    }
  ],
  "faq": [
    {
      "q": "what is an autonomous ai agent",
      "a": "In this instrument's terms, an autonomous AI agent operation sits higher on the L0-L5 ladder, with L5 meaning no human control path exists for that operation. The ladder assigns levels per operation, not to an agent or company as a whole—one agent may reach L5 in deployment and L0 in development. The ladder does not measure decision quality, profitability, reliability, or accountability."
    },
    {
      "q": "what is autonomy in ai",
      "a": "Define autonomy as what the L0-L5 scale measures: a monotonic six-rung progression from L0 (a human performs the operation, the agent drafts or advises) to L5 (no human control path exists), assigned per operation rather than per company, and explicitly not a measure of decision quality, profitability, desirability, reliability, or the presence of an accountable party."
    }
  ],
  "provenance": {
    "plan_model": "claude-sonnet-5",
    "prose_model": "claude-haiku-4-5",
    "generated_at": "2026-08-31",
    "topics_sha256": "f803a1050107c083e025e3fbbac7fd137b286b91b331cd74a3cba7f157ee3da1",
    "generator_sha256": "37774e8610230a5a987c6bd4066ad87ae5b1d571402001ee73140937ce84bce7",
    "plan_sha256": "f4d4d498d8f5d0db31ca59c07a0c84593e0e8ea846fec64cc5ffa415a7e05f1d"
  },
  "lifecycle": {
    "status": "current",
    "corrections": []
  }
}
---

Autonomy in software operations is measured by the ai agent autonomy levels ladder, which assigns a level (L0 through L5) to individual operations, never to entire organizations. A company may operate at different levels across its functions: deployment could reach L4 while pricing remains L0. Critically, the thresholds supporting these assignments are stated policy awaiting ratification rather than measured facts; no experiment validates the boundary conditions.

## Six rungs, one operation at a time

The ladder defines six rungs of operational autonomy. At L0, a human performs the operation and the agent drafts or advises. At L1, the agent performs it but a human approves each instance. At L2, the agent performs it but a human approves by exception.

At L3, the agent performs and decides, and a human may intervene but routinely does not. At L4, intervention requires a privileged path, and that path is recorded. At L5, no human control path exists for this operation.

The ladder is monotonic: L5 is the top, not a red flag (Operator ruling A-5). It measures autonomy, not desirability.

A level is assigned to an operation, never to a company as a whole (ABI-2-3). A single scalar for a company is a marketing number—the exact kind this product exists to replace. A company can be L4 in deployment and L0 in pricing. The [SPEC §3.1](/method/) passport captures each operation's level from the [registry](/registry/) separately, never as a company average.

## What the ladder does not price in

The ladder measures autonomy; it does not measure decision quality, profitability, the desirability of autonomy, reliability, or the presence of an accountable party. It captures whether an operation can proceed without human intervention, not whether that operation is wise or safe.

L0-L5 measures a subject's operational autonomy. The operator's agents carry permissions P0-P5: observe, recommend, prepare, execute low-risk, autonomous, and self-optimizing. Using one letter for two quantities is the same defect as a return value with two states of the world. The operator's "AI Agent Fleet" document defines its own L0-L5 differently. Permissions use the letter P to keep them distinct.

Some numbers are assigned rather than measured: the distinct author count (FEW_AUTHORS_FOR_L3 = 2), the signature share for L4 (SIGNED_SHARE_FOR_L4 = 0.9), and the sole author threshold (SOLE_AUTHOR = 1). These represent policy choices, not empirical findings, awaiting operator ratification.

## Thresholds assigned, not measured

Each threshold is a policy choice. SOLE_AUTHOR = 1 asserts that one distinct author is the strongest signal no human rota operates behind the commits. It is not proof - which is why a level built on it is capped and marked inferred. SIGNED_SHARE_FOR_L4 = 0.9 sets the signature threshold for sole-author repositories reaching L4. FEW_AUTHORS_FOR_L3 = 2 defines L3 qualification.

These values were bare numbers in comparison logic until 2026-08-20, when task T-THRESHOLD-1 surfaced them. A magic number at the point of comparison cannot be ratified, cannot be found when it needs changing, and cannot be told apart from a measurement. This project paid that cost before, when a cap invented for a cost that did not exist became an outage.

The codebase labels these **assigned, not measured**. They are a stated reading of what commit evidence can support, awaiting operator ratification. Stating that here is the difference between policy and leftover.

## Who counts as an author

Accounts the platform classifies as bots are excluded from the author count, ratified by the operator on 2026-08-25. The rule follows from what `SOLE_AUTHOR` in [the methodology](/method/) claims to detect: one distinct author is the strongest signal of a human rota behind the commits. A dependency bot's commit is not evidence of a human rota. Counting it would assign people to code no person wrote and penalize adding automation - an inverted incentive in an instrument measuring autonomy.

This rule was ratified on evidence it does not serve the operator's interests. Applying it changes neither of the operator's scores. provek stays L3 because a second identity remains after the bot is removed. A rule that raised the operator's levels would deserve suspicion; unchanged scores do not.

APIbase is L3 for a different reason, corrected here 2026-08-31 after Fable found the original one false. Within its 30-day evidence window APIbase has a single author, so there is no second account for this rule to exclude at all. It is L3 because `signed_commit_share` is 0.0, below the 0.9 `SIGNED_SHARE_FOR_L4` threshold a sole author must clear to reach L4 - the same rule that keeps `pipeline.verify` from granting it L4.

Automation running on ordinary user accounts such as `apibase-dispatch` and `provek-dispatch` still counts as a human author. This error points downward - it understates autonomy rather than overstating it, which is the correct direction for a gate to fail in.

Identity resolution is separately broken and deliberately left open. The collector reads `login` and falls back to commit e-mail, so distinct names sharing an address collapse into one author while one person with linked and unlinked accounts splits into two. [The registry](/registry/) measured this on provek on 2026-08-25. Fixing it could raise the operator's scores, requiring its own control, not a quiet edit by the interested party. Hiding a second human behind a self-installed GitHub App requires repository-admin rights, already acknowledged as the unmeasurable attack T1.

## Evidence classes and what a passport must show

The passport displayed at [the methodology](/method/) section 3.1 shows subject identity and binding strength: erc8004 binds strongly because control of the identity cannot be transferred; git or dns bind weakly because domains expire and get resold. Beside the projection 0-100 stands a disclaimer that the score measures autonomy, not reliability, decision quality, profitability, or the presence of an accountable party.

A per-operation table forms the core: each row lists the operation, its level L0 through L5 or `not_measured` with a reason, whether the level came from measurement or inference, and which limiters were applied. A control map discloses what was inspected, what lay beyond reach and why, and what an undiscovered path would look like.

The accountability block sits adjacent to but apart from the score. Each field - emergency stop, claims addressee, insurance, dispute path - either holds a value or states why none was found, drawing from three categories: the check ran and qualified nothing, the check did not run, or the source was unreadable. These match the categories that qualify an operation as unmeasured, so a measured absence differs from an unchecked field and the artefact must state which.

Provenance lists protocol version, profile version, evidence window span, and valid_until. An affiliation disclosure marks where verifier_affiliation is same_owner. Evidence falls into four classes by the cost to forge. Self-reported comes from the subject freely but never scores. Platform-observed comes from the subject at the cost of sustained theatre - behaviour the ecosystem captures, performed knowing it may be inspected. Third-party-attested requires collusion with a third party. Cryptographically-bound requires compromising a key and is costliest to fabricate.

{{figure:registry-coverage}}

## Not measured is not zero

The specification's [section 3.1](/method/) identifies three absence states in operation-level measurements. A check ran and nothing qualified means the evidence exists but no operation reached the threshold. A check did not run means no evidence was gathered. A source could not be read means the evidence was unreachable. Missing measurements are not violations; an instrument that suspended a subject for its own blindness would be wrong.

Subject git:whiteknightonhorse/AIpush demonstrates these states. Its development_initiation operation shows nothing_qualified - the check ran. Both deployment and treasury_control show check_did_not_run - no evidence was gathered for either. Its three key observations (signed_commit_share, distinct_authors, bot_author_share) are all null and measured is false.

In this example, binding_strength is weak with the flag revocable, and status is unverified. Until 2026-08-20 the specification granted an honest-none conclusion without field inspection, and three emitters relied on that licence to claim a completed check that never ran under schema 1.0.0.

## The workings are published, not just the verdict

The [methodology](/method/) is published in full, licensed for reuse. The scorer, every gate and every decision live at github.com/whiteknightonhorse/provek, so any verdict can be recomputed from the same inputs.

Operating documents that produced the instrument are recorded separately at provek-method as provenance, not instruction. Following the methodology has no effect on any verdict, since the score is computed from measured operations alone and the use of a method is not one of them. Every verdict in the [registry](/registry/) remains recomputable.
