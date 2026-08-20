# Keyword base — captured 2026-08-20

A dated capture of what people ask around this product's subject, taken from instruments that
answered. It exists so that a decision about which pages could exist is taken against a
measurement instead of an intuition.

**It authorises no page.** The ordinary use of a file like this is one page per query, assembled
because the query exists — which is this product's own defect wearing our colours: a claim
(*"here is the answer"*) stronger than the artefact behind it. Demand is evidence about readers,
not about us. A page built on a key still needs an address in SPEC.md, exactly like every other
sentence on the surface. Decision **D-17**.

## The files

| file | what it holds |
|---|---|
| `keywords.csv` | the base: one row per key, each naming the source that returned it and the address inside that source |
| `keywords_rejected.csv` | every string a source returned that did **not** get in, with the rule that dropped it |
| `sources.json` | the manifest: endpoint, parameters, budget, control and state for each source |

Columns in `keywords.csv`:

* `key` — the string **a source returned**. Nothing here was assembled by us; see "What a key is".
* `source_id`, `source_locator` — which instrument, and where inside it (which seed it came back
  for, or which line of the standard it was taken from).
* `corroborated_by` — other sources that returned the same string. 574 keys have at least one.
* `captured_at` — the date of the reading. Demand decays; a row is a statement about that day.
* `demand_state` — `measured`, `nothing_qualified`, `check_did_not_run` or `unreadable`. Never a
  bare number, never a bare blank.
* `impressions_exact`, `impressions_broad` — filled **only** when `demand_state` is `measured`,
  and then always greater than zero. An unmeasured quantity is absent, not `0`.
* `intent_shape` — `question` or `statement`, derived from the string itself (269 questions,
  1149 statements). Derived, not measured, and labelled as such.

## What a key is, and what a probe is

**A key is a string a source handed back.** A probe is a string we used to ask. Seeds, and the
seven question stems (`what is`, `how does`, `how to`, `why`, `who`, `can`, `is`), are probes.
A probe that comes back unchanged is dropped by rule `echo_of_probe` — 263 of them — rather than
counted as a discovery.

This is the whole guard against the failure this base was commissioned to avoid: multiplying our
own lists together produces something that has the shape of a base and the content of noise. Every
row here survived the round trip through an instrument.

Expansion was two rounds: 44 seeds (20 taken from SPEC.md with the line quoted in
`sources.json`, 24 from the text of ERC-8004), then 120 keys that round one **admitted**, re-asked.
The second round was capped at 120 of 438 candidates, ordered by measured demand; the 318 that
were not expanded are counted in the manifest rather than left to be inferred from a round number.

## Measured

<!-- MEASURED:BEGIN -->
```json
{
  "totals": {
    "keys": 1418,
    "sources_configured": 6,
    "sources_that_yielded_keys": 4,
    "keys_corroborated_by_a_second_source": 574,
    "rejected": 12653
  },
  "demand_states": {
    "measured": 257,
    "nothing_qualified": 733,
    "unreadable": 427,
    "check_did_not_run": 1
  },
  "rejected_by_rule": {
    "duplicate": 6031,
    "off_topic": 5629,
    "navigational": 477,
    "echo_of_probe": 263,
    "false_friend": 87,
    "too_long": 77,
    "non_ascii": 68,
    "too_short": 16,
    "generic_term": 4,
    "code_fragment": 1
  }
}
```
<!-- MEASURED:END -->

`tests/test_keyword_base.py` compares this block against `sources.json` and both against the CSV
files. A number that drifts out of the prose fails the build, because a document quoting a
measurement it no longer matches is the drift this project exists to catch. It has already fired
once, on this document, for exactly that reason.

## The sources, and what each one's silence means

| source | state | keys | probes | control |
|---|---|---|---|---|
| `bing_autosuggest` | ok | 1132 | 305 | `python` → 25 suggestions |
| `bing_related_keywords` | ok | 203 | 165 | `ai agents` → 66 related queries |
| `ddg_autocomplete` | ok | 63 | 165 | `python` → 8 suggestions |
| `erc8004_spec_text` | ok | 20 | 1 fetch | 24,458 bytes, 29 terms extracted |
| `bing_serp_related` | **unreadable** | 0 | 5 | `python`, `weather`, `how to boil an egg` → **0** related-search items each |
| `bing_get_keyword` | ok | 0 (prices keys, cannot discover them) | 1,279 | `ai agents` → 5,395 impressions |

**Every zero-capable source was asked a control question first**, because a zero is not a reading
until the instrument has been shown able to see a non-zero. That is L-10 in this repository's
`tasks/lessons.md`, and it earned its place here twice:

* **`bing_serp_related` is blind, so it says nothing.** The Bing result page is the only candidate
  source for "people also ask". It answers HTTP 200 and carries organic results — ten of them, with
  `python.org` among them — and yields **zero** related-question items to our reader. Three control
  queries, two of them (`weather`, `how to boil an egg`) chosen for being the least plausible things
  on the web to have no related searches: zero from all three, out of responses of 117 kB and 124 kB.
  The organic results were counted for the first control only; for the other two the reading is that
  a full-sized page carried no related searches, and the claim goes no further. An empty result from
  an instrument that cannot be shown able to see the quantity is a statement about the client, not
  about Bing. The source is recorded `unreadable` and contributes no keys **and no zeros**; a test
  refuses to let a blind source do either — and refuses, separately, to let any source with a
  zero-returning control be `ok`. Question-shaped keys in this base come from the two suggest
  endpoints and from Bing's related queries instead — 269 of them.
* **427 rows are `unreadable` because the demand instrument ran out.** `GetKeyword` gave 812
  readings and then returned `{"ErrorCode":4,"Message":"ThrottleUser"}` — a quota on the account,
  not a fact about the keywords. A second pass at one call per second met the same refusal on all
  43 rows it reached before it was stopped. Those keys may well have demand; what is known is that
  the instrument would not say, and writing `0` there would destroy the only evidence that the
  reading is missing.

`nothing_qualified` (733 rows) is the different state: the instrument answered, and Bing has no
impressions for that exact query in the window. It is the expected reading for most of this
subject. **ERC-8004's own name returns nothing** — `GetRelatedKeywords("erc-8004")` came back with
an empty list, and `GetKeyword("erc-8004")` with `Query: null`. The standard this project validates
has, as measured, no search demand at all. That is worth knowing before anybody builds a page on
the assumption that it has.

The single `check_did_not_run` row is `endpoint domain verification`: normalisation stripped the
`(Optional)` qualifier off the standard's heading, and the demand figure the row was carrying had
been measured for the *unstripped* string. A reading belongs to the string it was taken for, so it
was discarded rather than carried across. `sources.json` records the rename.

## The rules that dropped 12,653 strings

Applied in this order, first match wins, all of them code:

| rule | dropped | what it is |
|---|---|---|
| `duplicate` | 6031 | already in the base. Where the second return came from a different source it was kept as `corroborated_by` rather than discarded |
| `off_topic` | 5629 | carries no domain anchor: needs `ai agent`/`agentic`/`erc-8004`, or an agent word **and** a domain word together |
| `navigational` | 477 | someone else's front door — `login`, `near me`, `customer service`, `salary` |
| `echo_of_probe` | 263 | the probe string handed back unchanged; a probe is not a discovery |
| `false_friend` | 87 | the other sense of "agent" or of "trust" |
| `too_long` | 77 | over 80 characters or 12 words |
| `non_ascii` | 68 | the repository surface is English-only. Kept in the reject file, escaped, so the record stays auditable without failing the language ratchet |
| `too_short` | 16 | under 3 characters |
| `generic_term` | 4 | a one-word heading of the standard with no domain anchor |
| `code_fragment` | 1 | a heading quoting an identifier |

Three of these were written **after** the capture, by reading it:

* **`false_friend` — 87 rows, and the list is explicit but NOT complete.**
  `GetRelatedKeywords("trustless agents")` answers with "insurance agents", and one round of
  expansion later the base held 70 rows about Geico and continuing education for brokers.
  `insurance` and `escrow` had been in the domain-anchor list — the first because the accountability
  block names insurance, the second because phase 2 names escrow only to forbid it (A-6). A token
  this project uses in one sense and the query stream uses overwhelmingly in another is a false
  friend, not an anchor.
  The first version of this section called the collision list explicit and stopped there. It was
  refuted with the obvious counter-example: **`trust`, this project's own core word, collides with
  estate law**, where an agent registers, manages and claims *a trust* — Bing had answered the probe
  `trustless agents` with the British Trust Registration Service, and 17 further rows were riding on
  it. Those collisions are now in the list too. What that episode establishes is not that the list
  is finished but that it is a **measured, extendable list**: the next unfamiliar sense of "agent"
  will be found the same way, by reading the base rather than by trusting this paragraph. The cost
  is named: a genuine query about an AI agent sold into insurance is dropped with them.
* **`generic_term`.** Terms taken from the text of ERC-8004 are exempt from `off_topic` — topicality
  there is a fact of provenance, since "validation registry" carries no anchor word and is
  nevertheless the vocabulary of the standard we validate. That exemption has a price, and the rule
  is where it falls due: Bing priced the heading word **"feedback"** at 14,514 impressions belonging
  to somebody else's subject, and sorting by demand put it second in the whole base. A term whose
  string and whose measured demand are about different things is not a keyword.
* **`code_fragment`.** One heading quoting an identifier.

A late rule is applied in exactly one honest way: as code, to every row, with the movements
counted. `sources.json` records that pass under `refilter_pass`: 72 rows left the base, 20 rows
that had been rejected as duplicates of those rows were re-judged by the same code and are now
`false_friend`, and one key was renamed. Re-running the pass moves nothing — the base is closed
under its own rules, which a hand-edited file could never claim.

## Scope, and what is simply not known

* **One market**: `country=us`, `language=en-US`. A second market is a second capture, never an
  extrapolation from this one.
* **One window**: impressions are for 2026-05-01 to 2026-08-01.
* **Google is not measured at all.** No instrument on this host reads it. Nothing here should be
  read as a statement about Google's demand, and Bing's shape is not assumed to carry over.
* **Impressions are Bing Webmaster's own figures for the window.** They are a measurement of that
  source, not a market size.

## Repeating the capture, and what a clone cannot check

`sources.json` carries every endpoint, every parameter and every budget, so the capture can be
re-taken without our code — which is the standard the registry holds itself to, applied here.

The collector is `~/orchestra/keyword_probe.py`, outside this repository and deliberately so: every
`*.py` under `scripts/` must be bound to an `ABI-*` requirement, the master specification contains
no requirement about search demand, and binding one anyway to get past `scripts/ratchet_scope.py`
is precisely the rubber-stamp that ratchet exists to catch. The same reasoning put `bing_probe.py`
in the same place.

**Two costs, named rather than hidden.** The capture cannot be re-run from a clone. And the raw
responses — the only artefact that proves the claim above, that every row survived the round trip
through an instrument — live outside the repository too. Their fingerprint is pinned in
[`../evidence/KEYWORD-CAPTURE-001.txt`](../evidence/KEYWORD-CAPTURE-001.txt), so a reader can at
least tell whether the file they are shown is the file that was used. A reader who is not on this
host verifies the base by re-taking it, not by trusting us.

The Bing Webmaster API key lives in `~/.env` and appears in no output file, no log and no row here.
