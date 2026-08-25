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
  return (
    <footer className="mt-16 border-t border-[var(--color-line)] bg-[var(--color-paper)]">
      <div className="mx-auto max-w-[1180px] px-5 py-8 text-xs text-[var(--color-ink-3)] space-y-2">
        <p>
          The score measures <strong className="text-[var(--color-ink-2)]">autonomy</strong>. It does
          not measure reliability, decision quality, profitability, or the presence of an accountable
          party.
        </p>
        <p>
          Methodology is published in full. A verdict is reproducible by a third party from the same
          inputs &mdash; if it were not, this would be a brand rather than a standard.
        </p>
        {/* The notes were live at /method/notes/ and reachable from nowhere: nothing on the site
            linked to them, so a reader arrived only by typing the address and a crawler only by
            the sitemap. A footer link appears on every page, which is what gives the section any
            standing at all. The anchor text is the target page's own heading rather than "here":
            the words in the link are what describe the destination to both readers and crawlers. */}
        <p>
          <a
            href="/method/notes/"
            className="underline underline-offset-2 hover:text-[var(--color-ink)]"
          >
            Notes on the method
          </a>{" "}
          &mdash; the method, one topic at a time.
        </p>
        <p>provek.dev</p>
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
export function Facts({ rows }: { rows: Array<[string, React.ReactNode]> }) {
  return (
    <dl className="divide-y divide-[var(--color-line)] border-y border-[var(--color-line)]">
      {rows.map(([k, v]) => (
        <div key={k} className="grid grid-cols-1 gap-1 py-2 sm:grid-cols-[minmax(9rem,14rem)_1fr] sm:gap-4">
          <dt className="text-sm text-[var(--color-ink-2)]">{k}</dt>
          <dd className="text-sm">{v}</dd>
        </div>
      ))}
    </dl>
  );
}
