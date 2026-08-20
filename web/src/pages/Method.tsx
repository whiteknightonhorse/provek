/** The methodology is published in full - it is an asset, not a vulnerability (decision A-8).
 * Publishing it invites optimisation against it, which is the price of being reproducible. */

import { Facts, Page } from "../components/Chrome";

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

        {/* THE ONLY REFERENCE to the provenance corpus, and it is deliberately one sentence of
            prose rather than a nav entry (Fable's architecture ruling, ADR-0009). The
            specification anticipated the conflict: a party that teaches people to pass its own
            verification grades work it set itself, and its mitigation is that teaching and
            verification stay separated as components. A nav item would make the corpus a component
            OF this surface - integration, not separation - and DESIGN.md rule 4 forbids the
            retrofit independently. A test over the emitted site asserts this stays the only
            occurrence. */}
        <h2 className="mt-8 text-lg font-semibold">Published in full, including our own workings</h2>
        <p className="mt-1 text-sm text-[var(--color-ink-2)]">
          The methodology, the scorer, every gate and every decision are open at{" "}
          <a
            href="https://github.com/whiteknightonhorse/provek"
            className="text-[var(--color-accent)] hover:underline"
          >
            github.com/whiteknightonhorse/provek
          </a>
          , licensed for reuse, so a verdict can be recomputed by anyone from the same inputs. The
          operating documents that produced this instrument are recorded separately at{" "}
          <a
            href="https://github.com/whiteknightonhorse/provek-method"
            className="text-[var(--color-accent)] hover:underline"
          >
            provek-method
          </a>{" "}
          &mdash; provenance, not instruction. Following them has no effect on any verdict: the
          score is computed from measured operations, and the use of a method is not one of them.
        </p>
      </div>
    </Page>
  );
}
