/** Shell: masthead, nav, footer. Phase-2 slots are reserved here and rendered as disabled, never
 * announced as features that exist (decision D-05). */

export function Masthead({ route }: { route: string }) {
  const link = (href: string, label: string, active: boolean) => (
    <a
      key={href}
      href={href}
      aria-current={active ? "page" : undefined}
      className={
        "px-3 py-2.5 min-h-11 inline-flex items-center text-sm border-b-2 -mb-px " +
        (active
          ? "border-[var(--color-ink)] text-[var(--color-ink)]"
          : "border-transparent text-[var(--color-ink-2)] hover:text-[var(--color-ink)]")
      }
    >
      {label}
    </a>
  );
  return (
    <header className="bg-[var(--color-paper)] border-b border-[var(--color-line)]">
      <div className="mx-auto max-w-[1180px] px-5">
        <div className="flex items-center justify-between py-3">
          <a href="/" className="flex items-baseline gap-2 min-h-11 py-2">
            <span className="text-lg font-semibold tracking-tight">Provek</span>
            <span className="text-xs text-[var(--color-ink-3)]">evidence, not claims</span>
          </a>
          <a href="/apply/" className="text-sm border border-[var(--color-line-2)] px-3.5 min-h-11 inline-flex items-center hover:bg-[var(--color-paper-2)]">
            Request verification
          </a>
        </div>
        <nav className="flex gap-1 border-t border-[var(--color-line)] pt-1" aria-label="Main">
          {link("/registry/", "Registry", route.startsWith("/registry") || route.startsWith("/p/"))}
          {link("/method/", "Method", route === "/method/")}
          {link("/build/", "Build", route.startsWith("/build/"))}
          {/* PHASE 2 SLOT - reserved, disabled, and NOT described as a coming feature.

              THE UNAVAILABILITY IS TEXT, NOT AN ARIA ATTRIBUTE, and that is a correction rather
              than a style. This carried `aria-label="Corpus, not available"` with `aria-disabled`
              on a bare <span>. A <span> with no role is `generic`, and `aria-label` on a generic
              element is invalid HTML - the W3C Nu validator returns it as the one error on every
              emitted page (measured 2026-08-21 on the live /method/) - AND is discarded by
              assistive technology. So the greyed word said "not available" to sighted readers
              through its colour and said nothing at all to a screen reader, which is the accessible
              name silently reading `Corpus`. An attribute that fails validation and is ignored is
              not a smaller version of the information; it is its absence, dressed as care.

              `sr-only` puts the fact in the document as text, where nothing has to honour an ARIA
              contract for it to arrive - the same construction `Measured.tsx` already uses for
              `not measured`, which is this project's own rule about an absence being a state
              applied to the one reader who cannot see the colour.

              `aria-disabled` STAYS, and dropping it was a separate change riding on the first
              one's reasoning. The paragraph above indicts `aria-label`, and only `aria-label`:
              re-measured 2026-08-24 against the Nu validator on the live /method/, the page
              returns exactly one error, it names `aria-label`, and `aria-disabled="true"` sits
              inside that same error's extract unflagged. It is the attribute D-05 is enforced
              through - tests/test_phase_two_promises_nothing.py reads it - so removing it
              repealed the invariant in order to fix something it was not accused of. The
              accessible name and the disabled state are two facts, and this slot owes both. */}
          <span
            className="px-3 py-2.5 min-h-11 inline-flex items-center text-sm text-[var(--color-ink-disabled)] cursor-default select-none"
            aria-disabled="true"
          >
            Corpus<span className="sr-only">, not available</span>
          </span>
        </nav>
      </div>
    </header>
  );
}

export function Footer() {
  /* TWO KINDS OF THING, TWO PLACES. This was four paragraphs at one weight in one column, so a
     limit the product states about itself and a link to another page looked like the same kind of
     thing, and the bare domain hung off the GitHub link by an em dash saying what neither was.
     The limits keep full reading size on the left - they are the product's honesty, not fine print
     - and each is labelled by its own subject, words taken from the sentence itself so the label
     asserts nothing the copy did not. The domain sits on the identity rule at the bottom, where a
     domain belongs. The GitHub link still carries no description: the notes link earned one, that
     one never had one, and writing it here would be copy rather than structure. */
  return (
    <footer className="mt-16 border-t border-[var(--color-line)] bg-[var(--color-paper)]">
      <div className="mx-auto max-w-[1180px] px-5 py-8">
        <div className="grid gap-10 md:grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)] md:gap-16">
          <div className="grid gap-8 sm:grid-cols-2">
            <div>
              <h2 className="border-b border-[var(--color-line)] pb-1.5 text-xs uppercase tracking-wide text-[var(--color-ink-3)]">
                The score
              </h2>
              <p className="mt-2.5 text-xs leading-relaxed text-[var(--color-ink-3)]">
                The score measures{" "}
                <strong className="font-semibold text-[var(--color-ink)]">autonomy</strong>. It does
                not measure reliability, decision quality, profitability, or the presence of an
                accountable party.
              </p>
            </div>
            <div>
              <h2 className="border-b border-[var(--color-line)] pb-1.5 text-xs uppercase tracking-wide text-[var(--color-ink-3)]">
                The method
              </h2>
              <p className="mt-2.5 text-xs leading-relaxed text-[var(--color-ink-3)]">
                Methodology is published in full. A verdict is reproducible by a third party from the
                same inputs &mdash; if it were not, this would be a brand rather than a standard.
              </p>
            </div>
          </div>
          <div>
            <h2 className="border-b border-[var(--color-line)] pb-1.5 text-xs uppercase tracking-wide text-[var(--color-ink-3)]">
              Read further
            </h2>
            <div className="mt-2.5 flex flex-col gap-3">
              {/* The notes were live at /method/notes/ and reachable from nowhere. A footer link
                  appears on every page, which is what gives the section any standing at all. The
                  anchor text is the target page's own heading rather than "here". */}
              <div>
                <a
                  href="/method/notes/"
                  className="text-sm text-[var(--color-accent)] underline underline-offset-2 hover:text-[var(--color-ink)]"
                >
                  Notes on the method
                </a>
                <div className="mt-0.5 text-xs text-[var(--color-ink-3)]">
                  the method, one topic at a time
                </div>
              </div>
              <div>
                <a
                  href="https://github.com/whiteknightonhorse/provek"
                  aria-label="GitHub: provek repository"
                  className="inline-flex items-center gap-1.5 text-sm text-[var(--color-accent)] underline underline-offset-2 hover:text-[var(--color-ink)] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[var(--color-accent)]"
                >
                  <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                    <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
                  </svg>
                  GitHub
                </a>
              </div>
            </div>
          </div>
        </div>
        <div className="mt-7 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 border-t border-[var(--color-line)] pt-3.5 text-xs text-[var(--color-ink-3)]">
          <span>Provek &mdash; evidence, not claims</span>
          <span className="font-mono">provek.dev</span>
        </div>
      </div>
    </footer>
  );
}

export function Page({ children }: { children: React.ReactNode }) {
  return <main className="mx-auto max-w-[1180px] px-5 py-8">{children}</main>;
}

/** A finding strip. Positive and negative share one rhythm - borrowed from SSL Labs, where
 * "does not support PQC" sits in the same stack as the passing lines rather than hiding. */
export function Strip({
  tone,
  children,
}: {
  tone: "pass" | "warn" | "info";
  children: React.ReactNode;
}) {
  // A wash and a 1px rule. A thick coloured bar down the side is the category's default for
  // "callout" and carries nothing the tint does not already carry.
  const wash =
    tone === "pass"
      ? "var(--c-wash-pass)"
      : tone === "warn"
        ? "var(--c-wash-warn)"
        : "var(--c-wash-info)";
  return (
    <div
      className="border border-[var(--color-line)] px-4 py-3 text-sm"
      style={{ background: wash }}
    >
      {children}
    </div>
  );
}

/** Dense two-column label/value table. Sub-detail goes inside the cell, never in a nested card. */
export function Facts({ rows }: { rows: Array<[React.ReactNode, React.ReactNode]> }) {
  // KEYED BY POSITION, NOT BY THE LABEL (Passport clarity task). The label widened from `string`
  // to `React.ReactNode` so a raw machine key can carry an `InfoDot` beside it - a plain string is
  // no longer guaranteed, so a stable React key has to come from somewhere else. Every caller
  // passes a fixed-length, fixed-order array built fresh per render, never reordered by the user,
  // so the index is exactly as stable as the label string it replaces.
  return (
    <dl className="divide-y divide-[var(--color-line)] border-y border-[var(--color-line)]">
      {rows.map(([k, v], i) => (
        <div key={i} className="grid grid-cols-1 gap-1 py-2 sm:grid-cols-[minmax(9rem,14rem)_1fr] sm:gap-4">
          <dt className="text-sm text-[var(--color-ink-2)]">{k}</dt>
          <dd className="text-sm">{v}</dd>
        </div>
      ))}
    </dl>
  );
}
