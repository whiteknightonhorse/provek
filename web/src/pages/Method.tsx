/** The methodology is published in full - it is an asset, not a vulnerability (decision A-8).
 * Publishing it invites optimisation against it, which is the price of being reproducible. */

import { Facts, Page, Strip } from "../components/Chrome";

const LADDER: Array<[string, string]> = [
  ["L0", "A human performs the operation; the agent drafts or advises."],
  ["L1", "The agent performs it; a human approves each instance."],
  ["L2", "The agent performs it; a human approves by exception."],
  ["L3", "The agent performs and decides; a human may intervene but routinely does not."],
  ["L4", "Intervention requires a privileged path, and that path is recorded."],
  ["L5", "No human control path exists for this operation."],
];

export default function Method() {
  return (
    <Page>
      <div className="max-w-[46rem]">
        <h1 className="text-2xl font-semibold tracking-tight">Method</h1>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          Published in full. A verdict that only we can reproduce would be a brand, not a standard.
        </p>

        {/* THE ONLY REFERENCE to the provenance corpus, and it sits here rather than at the foot of
            the page because the claim it backs is made in the sentence directly above it. A page
            that asserts "published in full" and puts the link four screens below has made the
            reader hunt for the evidence - which is the shape this product exists to reject.

            Still one sentence of prose and still no nav entry (ADR-0009): a nav item would make the
            corpus a component OF this surface, which is integration rather than separation, and
            DESIGN.md rule 4 forbids the retrofit independently. A test over the emitted site
            asserts this stays the only occurrence. */}
        <div className="mt-5">
          <Strip tone="info">
            <strong>Everything here is open, including our own workings.</strong> The methodology,
            the scorer, every gate and every decision live at{" "}
            <a
              href="https://github.com/whiteknightonhorse/provek"
              className="text-[var(--color-accent)] hover:underline"
            >
              github.com/whiteknightonhorse/provek
            </a>
            , licensed for reuse, so any verdict can be recomputed from the same inputs. The
            operating documents that produced this instrument are recorded separately at{" "}
            <a
              href="https://github.com/whiteknightonhorse/provek-method"
              className="text-[var(--color-accent)] hover:underline"
            >
              provek-method
            </a>{" "}
            &mdash; provenance, not instruction. Following them has no effect on any verdict: the
            score is computed from measured operations, and the use of a method is not one of them.
          </Strip>
        </div>

        <h2 className="mt-8 text-lg font-semibold">The ladder</h2>
        <p className="mt-1 text-sm text-[var(--color-ink-2)]">
          Assigned per operation, never to a company as a whole. A company can be L4 in deployment
          and L0 in pricing.
        </p>
        <div className="mt-3 bg-[var(--color-paper)] border border-[var(--color-line)] px-5 py-1">
          <Facts rows={LADDER} />
        </div>

        {/* THE WINDOW WAS A NUMBER IN `provenance` BEFORE IT WAS A RULE ANYONE COULD READ (Fable,
            2026-08-31). Every passport already states `evidence_window_days`, but nowhere on this
            page did the number decide anything in the reader's eyes - it looked like a footnote
            about how the evidence was gathered, not like the input that the author-count rungs are
            computed against. It is EVIDENCE_WINDOW_DAYS in src/collector/github.py, and it decides
            how many distinct authors a subject shows before the ladder ever looks at signatures. */}
        <h2 className="mt-8 text-lg font-semibold">The evidence window</h2>
        <p className="mt-1 text-sm text-[var(--color-ink-2)]">
          Author counts are read over a rolling 30-day window, not over the repository's whole
          history. A subject with one author in the last 30 days and twelve before that is read as
          one author &mdash; the window is what "distinct authors" means throughout this
          methodology, and every passport states the exact window it used.
        </p>

        <h2 className="mt-8 text-lg font-semibold">What it does not measure</h2>
        <ul className="mt-2 text-sm text-[var(--color-ink-2)] list-disc pl-5 space-y-1">
          <li>decision quality</li>
          <li>profitability</li>
          <li>whether the autonomy is desirable</li>
          <li>reliability, and whether anyone is accountable</li>
        </ul>

        {/* THE DENOMINATOR IS THE PART THAT WAS MISSING (Fable, 2026-08-31). A visitor who sees
            "60" or "80" on the registry with no formula in reach reads it against an unstated
            denominator of 100, the way a school mark or a credit score would be read. The true
            denominator is 5 points per MEASURED operation - unmeasured operations drop out of the
            sum on both sides rather than counting as zero, which is the same "absence is not a
            zero" rule this page states elsewhere applied to the one number visitors are most
            likely to skim past. */}
        <h2 className="mt-8 text-lg font-semibold">The projection</h2>
        <p className="mt-1 text-sm text-[var(--color-ink-2)]">
          The 0-100 number on the registry is: sum the ladder value of every MEASURED operation,
          divide by 5 times the count of operations that were measured, multiply by 100. Operations
          with no measurement do not enter the sum or the count &mdash; they are absent, not zero.
          A subject with exactly one measured operation, scored L3, projects to 60: 3 &divide; (5
          &times; 1) &times; 100. A second measured operation would change the denominator, and
          therefore the number, even if its own level changed nothing else.
        </p>

        <h2 className="mt-8 text-lg font-semibold">Evidence classes</h2>
        <p className="mt-1 text-sm text-[var(--color-ink-2)]">
          Every piece of evidence carries the cost of forging it. Mixing classes inside one number
          without disclosing the mix is forbidden &mdash; otherwise a score would say the same thing
          about a self-report as about a cryptographic signature.
        </p>
        <div className="mt-3 bg-[var(--color-paper)] border border-[var(--color-line)] px-5 py-1">
          <Facts
            rows={[
              ["self_reported", "the subject, for free — never enters the score"],
              ["platform_observed", "the subject, at the cost of sustained theatre"],
              ["third_party_attested", "requires collusion with a third party"],
              ["cryptographically_bound", "requires compromising a key"],
            ]}
          />
        </div>

        <h2 className="mt-8 text-lg font-semibold">Not measured is a state, not a zero</h2>
        <p className="mt-1 text-sm text-[var(--color-ink-2)]">
          Three absences are distinguished and never collapsed: the check ran and nothing qualified;
          the check did not run; the source could not be read. A missing measurement is not a
          violation, and a verifier that suspended a subject for its own blindness would be
          punishing someone for its own failure.
        </p>

        {/* THE ENTRANCE RETURNED WITH THE FIRST NOTE, which is the condition the comment that
            stood here set for it. A capture survived `notes_gen.py`'s own `measure()` on
            2026-08-24, so `prerender.mjs` emits the route and this sentence no longer points at a
            404 - the state `tests/test_notes_entrance.py` holds in both directions.

            THE WORDING STATES NO COUNT, and that is the whole care taken here. The sentence this
            replaces claimed in the present tense that a body of writing existed while zero notes
            were captured, which is L-16 and the defect this product sells the detection of. The
            obvious repair - "one note is published so far" - swaps one unbacked claim for another
            that nothing measures: it goes stale the moment a second note lands and no gate would
            go red over it (L-7, L-13). So the prose points at the index and lets the index do the
            counting, which is the only copy of that number that cannot drift from the artefact. */}

        {/* THE GAP THIS CLOSES (Fable, 2026-08-31). `github` is listed as `inspected` on every
            passport that could read it, and GitHub separately exposes a Deployments API - over a
            hundred records, readable anonymously - that this project has never queried. Leaving
            that unsaid let `inspected: [github]` imply more than it meant: the channel was
            inspected for commits and authorship, not for deployment history. The honest fix costs
            nothing to build: the `deployment` operation is declared in `coverage.out_of_reach`
            with the reason "collector not implemented", the same place `server`, `treasury` and
            `database` already say why they are unreached. */}
        <h2 className="mt-8 text-lg font-semibold">What "deployment" means on a passport today</h2>
        <p className="mt-1 text-sm text-[var(--color-ink-2)]">
          The `github` channel is inspected for commits and authorship only. No collector queries
          deployment history &mdash; not even GitHub's own Deployments records, which are public.
          Every passport now states this plainly, in `coverage.out_of_reach`, with the reason
          "collector not implemented" &mdash; a declared absence of collection, never a probe that
          ran and found nothing.
        </p>

        <h2 className="mt-8 text-lg font-semibold">Notes on the method</h2>
        <p className="mt-1 text-sm text-[var(--color-ink-2)]">
          Parts of the methodology carry more argument than this page has room for, and those are
          written up separately, one note to a topic. The index lists what has been captured and
          nothing else, so it is also the record of how much of the method has been written down:{" "}
          <a href="/method/notes/" className="text-[var(--color-accent)] hover:underline">
            notes on the method
          </a>
          .
        </p>

        {/* The only route to the phase-2 page, and it is here rather than on the landing on
            purpose. The landing's argument is built to hold at zero funders - that is the whole
            point of it - so dangling a future second side there as a reason to apply would
            reintroduce the dependency the specification deliberately removed. On the methodology
            page the same page reads as what it is: a part of the specification that is written
            down and not built. */}
        <h2 className="mt-8 text-lg font-semibold">What is specified and not built</h2>
        <p className="mt-1 text-sm text-[var(--color-ink-2)]">
          The specification also defines a second phase, in which a customer commissions work from a
          verified agent and we witness the fact of performance. None of it is in service and no
          application for it is being taken. It is written down here anyway, because what a
          specification forbids us to build is a fact about the product today:{" "}
          <a href="/phase-2/" className="text-[var(--color-accent)] hover:underline">
            phase two, and why it is not running
          </a>
          .
        </p>


        {/* WHY THIS LIST EXISTS AT ALL (Fable, 2026-08-31). "Declared holds the door, undeclared
            does not" - the L4 defect this page's other additions respond to was exactly an
            undeclared rule change nobody could have caught by reading this page, because the page
            said nothing for the change to contradict. Naming what is NOT yet published here is
            cheaper than the alternative, which is a reader discovering the gap by finding a
            surprising verdict, the way this one was found. */}
        <h2 className="mt-8 text-lg font-semibold">Open items</h2>
        <p className="mt-1 text-sm text-[var(--color-ink-2)]">
          Measured or coded today, and not yet published here as a rule of the method:
        </p>
        <ul className="mt-2 text-sm text-[var(--color-ink-2)] list-disc pl-5 space-y-1">
          <li>the rules for L0, L1, L2 and L5 &mdash; only L3 and L4's thresholds are stated above</li>
          <li>the denominator `signed_commit_share` is a share OF &mdash; which commits are counted
            in it</li>
          <li>the comparison operators used at each threshold (&ge;, &le;, or ==)</li>
          <li>whether any level above L4 is reachable at all under `SOLE_AUTHOR`</li>
          <li>the full list of limiters O1-O3 and what each one does to a verdict</li>
          <li>the inputs `identity_window_closed`, `has_runtime_trace`, the `unlinked_*` measures,
            and `control_map_cap`</li>
        </ul>

      </div>
    </Page>
  );
}
