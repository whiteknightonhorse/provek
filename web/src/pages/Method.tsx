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

        <h2 className="mt-8 text-lg font-semibold">What it does not measure</h2>
        <ul className="mt-2 text-sm text-[var(--color-ink-2)] list-disc pl-5 space-y-1">
          <li>decision quality</li>
          <li>profitability</li>
          <li>whether the autonomy is desirable</li>
          <li>reliability, and whether anyone is accountable</li>
        </ul>

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

      </div>
    </Page>
  );
}
