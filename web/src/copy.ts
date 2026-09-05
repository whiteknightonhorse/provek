/** T-78 (Fable ruling, 78-texts-for-the-incubator-funnel.ruling-1.md): a fixed lexicon for the
 * four funnel surfaces (landing, /apply/, /build/, /registry/) and one funnel sentence, identical
 * word for word on all four, so "no agent yet" reads the same wherever it appears rather than
 * being retyped once per page and drifting.
 *
 * FUNNEL_SENTENCE never links anywhere - each page already carries its own real link for each
 * step (the masthead's "Request verification", `/build/`'s own template grid, the registry
 * table), and `tests/test_build_funnel_strip_once.py` counts `/apply/` links per page under
 * `dist/build/**` at exactly one; a second link inside this sentence on that surface would fail
 * it for a reason that has nothing to do with what broke.
 *
 * INCUBATOR_SENTENCE is the one place "incubator" is allowed to describe the product on these four
 * surfaces (ruling: lowercase, descriptive, never a title/H1/nav label/meta, one sentence per
 * surface) - it sits beside the funnel sentence rather than at the top of a page or in a heading,
 * and it names the two things a reader is likeliest to assume wrongly from the word alone: that
 * money moves through us, and that there is a cohort or admission date to apply for. Neither
 * exists (D-05, D-16, ADR-0011's own rejection of "Incubator tiers"), so the sentence says so
 * instead of leaving the word to imply it.
 *
 * NEITHER SENTENCE MAY CONTAIN A BARE NUMBER WORD. `tests/test_apply_names_the_probe_cost.py`
 * treats every numeral on the whole of `/apply/` - including "one" used as a pronoun, not a count
 * - as a stray quantity unless it is the prober's own declared number of requests. This sentence
 * renders on that page too, so "if you don't have one" (an earlier draft) read as an undeclared
 * second count of something reaching a stranger's server, and failed that gate for a reason that
 * had nothing to do with what it actually guards. */
export const FUNNEL_SENTENCE =
  "Build an agent from a template if you have none yet, request verification for a free " +
  "passport, and take orders once the registry lists you.";

export const INCUBATOR_SENTENCE =
  "That whole path — build, verify, list — is what we mean by an AI agent incubator: it " +
  "holds no funds, and there is no cohort to join.";
