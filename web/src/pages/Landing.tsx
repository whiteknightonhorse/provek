/** The only screen allowed air. Content follows docs/WHY_GET_VERIFIED.md, including its limits -
 * those are part of the pitch, not a caveat to bury. */

import { useEffect, useRef } from "react";
import { Page, Strip } from "../components/Chrome";
import { AbsentMark } from "../components/Measured";
import type { Registry as R } from "../types";

/** `reg` is null while the registry is still loading. Rendering a 0 or an invented row there
 * would state a measured fact we do not have yet - a fabrication in the one place this product
 * promises never to fabricate. */
export default function Landing({ reg }: { reg: R | null }) {
  const count = reg?.count ?? null;

  // Arms the one authored moment. Nothing here runs unless motion is welcome, and the offset is
  // added by this effect rather than by the stylesheet, so a reader whose script never runs sees
  // the list where it belongs instead of eight pixels low and stuck there.
  const paced = useRef<HTMLUListElement>(null);
  useEffect(() => {
    const el = paced.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const items = Array.from(el.children) as HTMLElement[];
    const release = (node: HTMLElement) => {
      node.dataset.seen = "";
    };
    el.classList.add("paced--armed");

    // Anything already on screen is released synchronously. An observer's first delivery is
    // asynchronous and, in a hidden document, may never arrive at all.
    for (const item of items) {
      const r = item.getBoundingClientRect();
      if (r.top < window.innerHeight && r.bottom > 0) release(item);
    }

    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (!e.isIntersecting) continue;
          release(e.target as HTMLElement);
          io.unobserve(e.target);
        }
      },
      { rootMargin: "0px 0px -12% 0px" },
    );
    for (const item of items) if (!item.dataset.seen) io.observe(item);

    // The release valve. Chrome suspends observer delivery while a document is hidden, and a page
    // opened in a background tab would otherwise sit permanently offset. Two seconds is longer
    // than any real reveal and shorter than anyone's patience.
    const valve = window.setTimeout(() => items.forEach(release), 2000);

    return () => {
      io.disconnect();
      window.clearTimeout(valve);
    };
  }, []);
  const preview = reg?.subjects.slice(0, 4) ?? [];
  return (
    <Page>
      <div className="grid gap-10 lg:grid-cols-[minmax(0,42rem)_minmax(0,1fr)] lg:gap-14">
      <section className="pt-6">
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
            See the registry{count === null ? "" : ` (${count})`}
          </a>
        </div>
      </section>

      {/* The right column is the argument's own evidence. The page claims a standard exists; the
          registry is the only thing that can show it does. These are the real rows, in the real
          order, with the affiliation on the face of each - a marketing wall of logos would be the
          exact substitution this product exists to detect. It also fills a half-width that read as
          unfinished on a desktop monitor, which is why it is here and not in a later phase. */}
      <aside className="lg:pt-8">
        <h2 className="text-xs uppercase tracking-wide text-[var(--color-ink-3)]">
          The registry, right now
        </h2>
        {reg === null ? (
          <div className="mt-4 space-y-3" aria-hidden="true">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="skeleton-bar h-10 bg-[var(--color-line)] rounded-sm" />
            ))}
          </div>
        ) : (
          <>
            <ul className="mt-4 divide-y divide-[var(--color-line)] border-y border-[var(--color-line)]">
              {preview.map((s2) => (
                <li key={s2.subject_id} className="flex items-baseline justify-between gap-4 py-2.5">
                  <a
                    href={`#/p/${encodeURIComponent(s2.subject_id)}`}
                    className="text-sm text-[var(--color-accent)] hover:underline truncate"
                  >
                    {s2.subject_id.split("/").pop()}
                  </a>
                  <span className="shrink-0 text-sm tabular-nums">
                    {s2.projection === null ? (
                      <AbsentMark reason={s2.projection_absent_reason} />
                    ) : (
                      <>
                        {s2.projection}
                        <span className="text-[var(--color-ink-3)]"> / 100</span>
                      </>
                    )}
                  </span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-[var(--color-ink-3)]">
              {/* Derived from the rows. The sentence used to assert that every subject was the
                  operator's own; it would have gone on asserting it after the first independent
                  one arrived (Fable, R4). */}
              {count} records
              {reg.subjects.every((x) => x.verifier_affiliation === "same_owner")
                ? ", every one of them the operator\u2019s own and marked "
                : ", of which " +
                  reg.subjects.filter((x) => x.verifier_affiliation === "same_owner").length +
                  " are the operator\u2019s own and marked "}
              <span style={{ color: "var(--color-warn)" }}>affiliated</span>. Saying so is the point.{" "}
              <a href="#/registry" className="text-[var(--color-accent)] hover:underline">
                See all
              </a>
              .
            </p>
          </>
        )}
      </aside>
      </div>

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
        <ul ref={paced} className="paced mt-4 space-y-3 text-sm text-[var(--color-ink-2)]">
          <li className="border-l border-[var(--color-line-2)] pl-3.5">
            <strong className="text-[var(--color-ink)]">We measure autonomy, not quality.</strong> The
            passport says nothing about whether your decisions are good, whether you are profitable,
            or whether you are safe to rely on.
          </li>
          <li className="border-l border-[var(--color-line-2)] pl-3.5">
            <strong className="text-[var(--color-ink)]">Some claims are not verifiable at reasonable cost.</strong>{" "}
            &ldquo;No human wrote this commit&rdquo; is one of them. Where a signal is probabilistic
            we publish it as probabilistic, and it never becomes a verdict.
          </li>
          <li className="border-l border-[var(--color-line-2)] pl-3.5">
            <strong className="text-[var(--color-ink)]">A control map proves a path exists; it can never prove none was missed.</strong>{" "}
            Every map publishes its own coverage.
          </li>
          <li className="border-l border-[var(--color-line-2)] pl-3.5">
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
