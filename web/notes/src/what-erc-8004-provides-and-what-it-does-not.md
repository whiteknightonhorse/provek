---
{
  "slug": "what-erc-8004-provides-and-what-it-does-not",
  "title": "ERC-8004: what it standardizes, what it leaves open - Provek",
  "h1": "What ERC-8004 standardizes, and what it leaves to a validator",
  "description": "This note describes what ERC-8004 fixes on-chain across its identity, reputation and validation registries, and what it leaves to a validator's method.",
  "keys": [
    {
      "key": "erc 8004",
      "demand_state": "nothing_qualified",
      "source_id": "bing_autosuggest",
      "role": "primary"
    },
    {
      "key": "trustless agents",
      "demand_state": "unreadable",
      "source_id": "erc8004_spec_text",
      "role": "supporting"
    }
  ],
  "addresses": [
    {
      "ref": "SPEC §1",
      "file": "SPEC.md",
      "anchor": "## 1. What this is"
    },
    {
      "ref": "ADR-0001",
      "file": "docs/adr/ADR-0001-validator-not-registry.md",
      "anchor": "#"
    },
    {
      "ref": "src/transport/erc8004.py",
      "file": "src/transport/erc8004.py",
      "anchor": "def "
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
  "figures": [],
  "faq": [],
  "provenance": {
    "plan_model": "claude-sonnet-5",
    "prose_model": "claude-haiku-4-5",
    "generated_at": "2026-08-24",
    "topics_sha256": "44957c1f90a68e7b14bd005585339d07bcd2c5ba30028263475145cd919da03b",
    "generator_sha256": "e6020320cd1a68c66414f9f4ce2b5149ad6c144be036f257d52998754944664f",
    "plan_sha256": "06a6f8d5668c6b6a055dcbe20301e438b8ad4078814211e855a2d3558abc9174"
  },
  "lifecycle": {
    "status": "current",
    "corrections": []
  },
  "figures_absent_reason": "nothing_to_measure",
  "figures_absent_detail": "This note is about what a standard says and does not say. There is no quantity here that we have measured, and a figure drawn to fill the slot would be decoration - forbidden by D-07."
}
---

erc 8004 is a draft standard that defines three on-chain registries—identity, reputation, and validation—to enable agents to be discovered and trusted without prior relationships. This note examines the boundary the standard establishes: what it fixes in concrete form (the registry interfaces, response shape, and on-chain state) and what it deliberately leaves to a validator—the methodology by which a claim is judged.

## What ERC-8004 standardizes

Model Context Protocol (MCP) allows servers to list and offer capabilities (prompts, resources, tools, and completions), while Agent2Agent (A2A) handles agent authentication, skills advertisement via AgentCards, direct messaging, and task-lifecycle orchestration. These agent communication protocols don't inherently cover agent discovery and trust.

The standard addresses this through three lightweight [registries](/registry/) deployable on any L2 or on Mainnet as per-chain singletons: the Identity Registry providing portable identifiers, the Reputation Registry establishing a standard interface for feedback signals, and the Validation Registry supporting independent validation.

Trust models are pluggable and tiered, with security proportional to value at risk, from low-stake tasks like ordering pizza to high-stake ones like medical diagnosis. Developers choose from reputation systems using client feedback, validation via stake-secured re-execution, zero-knowledge machine learning (zkML) proofs, or trusted execution environment (TEE) oracles. This enables agents to discover, choose, and interact across organizational boundaries without pre-existing trust, thereby enabling open-ended agent economies.

## The identity registry: a pointer, not a verdict

The Identity Registry uses ERC-721 with the URIStorage extension, making agents immediately browsable and transferable with NFTs-compliant apps. Each agent is uniquely identified by `agentRegistry` (format `{namespace}:{chainId}:{identityRegistry}`, e.g. `eip155:1:0x742...`), `agentId` (the ERC-721 tokenId), and `agentURI` (the ERC-721 tokenURI). The token owner can transfer ownership or delegate management (such as updating the registration file) to operators.

`agentURI` MUST resolve to the registration file, using `ipfs://`, `https://`, or base64-encoded `data:` URIs. The registration file MUST include `type`, `name`, and `description` fields; the description MAY include what the agent does, how it works, pricing, and interaction methods.

This structure - the on-chain token, the linked file, the ownership model - specifies only where an agent is found and who controls it. It makes no judgment about competence, reliability, or truthfulness. The Identity Registry is a pointer and an address, not a verdict. That judgment - whether an agent will deliver as described - belongs to validators, which is why verification requires a distinct layer.

## The validation registry: a fixed shape, an open method

The validation [registry](/registry/) enables agents to request verification and validators to record responses on-chain. Like the Identity Registry, it standardises only the mechanics, not the validator's method.

Agents call `validationRequest(validatorAddress, agentId, requestURI, requestHash)`. This MUST be called by the owner or operator of the agent. The `requestURI` points to off-chain data (inputs, outputs, execution traces), and `requestHash` is a keccak256 commitment to that data.

The specified validator responds with `validationResponse(requestHash, response, responseURI, responseHash, tag)`. This call MUST come from the validatorAddress named in the request. The `response` is a uint8 between 0 and 100, usable as binary (0 failed, 100 passed) or with intermediate values for outcomes across a spectrum. Optional fields allow validators to attach evidence and labels.

Calling `validationResponse()` multiple times for the same request enables progressive states like soft finality then hard finality, each tagged differently. Read functions include `getValidationStatus` (a single response), `getSummary` (aggregated statistics, with optional validator and tag filters), `getAgentValidations`, and `getValidatorRequests`.

What is not standardised: how validators reach their verdict. Stake-secured re-execution, zkML verifiers, TEE oracles, and trusted judges each have different methods. Incentives and slashing related to validation are managed by the validation protocol itself, outside the registry's scope. The standard fixes the shape—the commitment, the range, the repeatability—and leaves method to the validator.

## Reputation, and the aggregation the standard declines to fix

The Reputation [registry](/registry/) is a standard interface for posting and fetching feedback signals. Like validation, it standardises format while leaving aggregation mechanisms open. Scoring and aggregation occur both on-chain (for composability) and off-chain (for sophisticated algorithms), enabling an ecosystem of specialized services for agent scoring, auditor networks, and insurance pools.

This split reflects a deliberate constraint: the standard defines what a reputation signal must look like—a posted and fetchable piece of feedback—while leaving how those signals are combined entirely open. On-chain aggregation serves systems that require composability; off-chain aggregation serves systems that require sophisticated analysis.

Payments are orthogonal to this protocol and not covered here. Examples are provided showing how x402 payments can enrich feedback signals, but the standard does not mandate or prefer any payment mechanism. The reputation system functions without them.

ADR-0001 reads this design choice as fixing the shape of a validator's answer (0-100) while explicitly moving complex reputation aggregation off-chain, leaving the validator's mechanisms to the validator. The standard is transport; the methodology is what remains unoccupied.

## On-chain existence is not evidence a reader can use

On-chain existence is not evidence a human reader can verify. The ERC-8004 standard defines what registries record on-chain: identity, reputation signals, validation results. The sentence the product must earn: An outside party can determine, from evidence rather than claims, how much of a business is actually run by machines. Today the [registry](/registry/) is a JSON file—a machine reads it, a founder cannot.

Two audiences drive the design. The Subject, a team running an agent business, wants to be verified and to have something to show their own customers, and lands at an apply page. The Consumer of evidence—a counterparty, a buyer, a lawyer—wants to check whether a specific business is what it claims. They arrive by a link from elsewhere: an email, a footer badge, a due-diligence memo. That makes the passport page, not the landing page, the load-bearing screen.

This standard fixes the shape of what gets recorded: validation results scored 0 to 100, reputation signals posted and fetched. It does not prescribe how a validator judges a claim, nor mandate on-chain aggregation to render conclusions humans can reason about. That interpretive work falls to the validator's methodology and to platforms that present evidence.

## Provek's position on the ladder ERC-8004 leaves open

Provek occupies the validator's side of ERC-8004. The standard specifies what gets recorded: identity binding, reputation signals, validation results scored 0-100. The methodology—L0-L5 ladder, proof-of-active-business, the control map, mandated active probing—sits in what the standard leaves open. ERC-8004 is transport. Provek's product lives in what it does not prescribe.

The architecture is defined by what Provek does not build. An identity registry comes from ERC-8004. Provek builds a status [registry](/registry/)—required by ABI-19-2—holding evidence of whether a business runs on machines. That registry can publish through the validation layer, gaining distribution without depending on the standard's finalization.

Isolation from the Draft status risk follows three machine-level guarantees. The scorer does not import the transport layer; this is not convention but structural. The adapter is thin. A second transport exists, proving independence. If the standard fails to finalize, distribution falls. The product—methodology, evidence, validation—remains intact.

This protection costs. The standard lowers the barrier for competing validators. The moat sits in execution: the methodology, the issuer's reputation, and accumulated evidence.
