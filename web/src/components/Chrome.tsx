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
          <a href="#/" className="flex items-baseline gap-2 min-h-11 py-2">
            <span className="text-lg font-semibold tracking-tight">Provek</span>
            <span className="text-xs text-[var(--color-ink-3)]">evidence, not claims</span>
          </a>
          <a href="#/apply" className="text-sm border border-[var(--color-line-2)] px-3.5 min-h-11 inline-flex items-center hover:bg-[var(--color-paper-2)]">
            Request verification
          </a>
        </div>
        <nav className="flex gap-1 border-t border-[var(--color-line)] pt-1" aria-label="Main">
          {link("#/registry", "Registry", route.startsWith("#/registry") || route.startsWith("#/p/"))}
          {link("#/method", "Method", route === "#/method")}
          {/* PHASE 2 SLOT - reserved, disabled, and NOT described as a coming feature. */}
          <span
            className="px-3 py-2.5 min-h-11 inline-flex items-center text-sm text-[var(--color-ink-disabled)] cursor-default select-none"
            aria-disabled="true"
            aria-label="Corpus, not available"
          >
            Corpus
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
