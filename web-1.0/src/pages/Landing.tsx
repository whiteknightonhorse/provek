/** The only screen allowed air. Content follows docs/WHY_GET_VERIFIED.md, including its limits -
 * those are part of the pitch, not a caveat to bury. */

import { Page, Strip } from "../components/Chrome";

export default function Landing({ count }: { count: number }) {
  return (
    <Page>
      <section className="max-w-[42rem] pt-6">
        <h1 className="text-[2.1rem] leading-[1.15] font-semibold tracking-tight">
          Your customers cannot tell you apart from a company that wrote
          &ldquo;AI-powered&rdquo; on a landing page.
        </h1>
        <p className="mt-5 text-[1.05rem] leading-relaxed text-[var(--color-ink-2)]">
          That is not a marketing problem, and marketing cannot fix it: any claim you make, a
          competitor can make more loudly. It is a verification problem.
        </p>
        <p className="mt-4 text-[1.05rem] leading-relaxed text-[var(--color-ink-2)]">
          Provek measures, per business operation, how much of your company runs without a human in
          the loop &mdash; and publishes the evidence behind every number, including what could not
          be measured.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <a href="#/apply" className="border border-[var(--color-ink)] bg-[var(--color-ink)] text-[var(--color-paper)] px-4 py-2 text-sm">
            Request verification
          </a>
          <a href="#/registry" className="border border-[var(--color-line-2)] px-4 py-2 text-sm hover:bg-[var(--color-paper)]">
            See the registry ({count})
          </a>
        </div>
      </section>

      <section className="mt-14 max-w-[46rem]">
        <h2 className="text-lg font-semibold">Why this is worth your time today</h2>
        <div className="mt-4 space-y-3">
          <Strip tone="pass">
            <strong>It is an artefact for your customers, not for ours.</strong> Your buyers already
            ask how much of your product is really automated. A verified passport is the one answer a
            competitor running an AI theatre cannot copy &mdash; copying it requires actually being
            autonomous.
          </Strip>
          <Strip tone="pass">
            <strong>A regulatory dossier you will need anyway.</strong> At some point your counsel
            has to argue about who controls what. A control map is evidence input for that argument,
            built beforehand, by a third party, with a timestamp.
          </Strip>
          <Strip tone="info">
            <strong>It costs nothing right now.</strong> Early passports are free. That is not a
            favour: a registry with no entries is worth nothing, and we need the first ones as much
            as you do. Saying so is cheaper than pretending otherwise.
          </Strip>
        </div>
      </section>

      <section className="mt-12 max-w-[46rem]">
        <h2 className="text-lg font-semibold">The limits, up front</h2>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          We would rather lose you as a subject than have you discover these later.
        </p>
        <ul className="mt-4 space-y-3 text-sm text-[var(--color-ink-2)]">
          <li className="border-l-2 border-[var(--color-line-2)] pl-3">
            <strong className="text-[var(--color-ink)]">We measure autonomy, not quality.</strong> The
            passport says nothing about whether your decisions are good, whether you are profitable,
            or whether you are safe to rely on.
          </li>
          <li className="border-l-2 border-[var(--color-line-2)] pl-3">
            <strong className="text-[var(--color-ink)]">Some claims are not verifiable at reasonable cost.</strong>{" "}
            &ldquo;No human wrote this commit&rdquo; is one of them. Where a signal is probabilistic
            we publish it as probabilistic, and it never becomes a verdict.
          </li>
          <li className="border-l-2 border-[var(--color-line-2)] pl-3">
            <strong className="text-[var(--color-ink)]">A control map proves a path exists; it can never prove none was missed.</strong>{" "}
            Every map publishes its own coverage.
          </li>
          <li className="border-l-2 border-[var(--color-line-2)] pl-3">
            <strong className="text-[var(--color-ink)]">Without a mandate we do not touch your production.</strong>{" "}
            Probing a live system without one is an incident, not a verification.
          </li>
        </ul>
      </section>

      <section className="mt-12 max-w-[46rem]">
        <h2 className="text-lg font-semibold">What we never do</h2>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          We never hold your funds. We never take custody of your keys. We never store your secrets
          &mdash; they are redacted before they become an artefact. We never verify anyone who did
          not ask.
        </p>
      </section>
    </Page>
  );
}
