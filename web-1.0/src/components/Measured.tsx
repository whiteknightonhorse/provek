/** Rendering of a measured value versus an absent one.
 *
 * DECISION D-03, and it is the single most load-bearing rule in this interface: an unmeasured
 * quantity renders as its own state with its own glyph and its own neutral colour. It never
 * renders as 0, never as an empty cell, never as a dash that could be mistaken for either.
 *
 * The pattern is borrowed from OpenSSF Scorecard, where an unevaluable check shows "?" in grey
 * while a genuinely failing check shows a measured 0 in red. Two different states of the world,
 * two different appearances - proven in a product people already trust. */

const REASON_TEXT: Record<string, string> = {
  nothing_qualified: "the check ran and nothing qualified",
  check_did_not_run: "the check did not run",
  unreadable: "the source could not be read",
};

export function AbsentMark({ reason }: { reason: string | null }) {
  return (
    <span
      className="inline-flex items-baseline gap-1.5"
      title={reason ? REASON_TEXT[reason] ?? reason : "not measured"}
    >
      <span className="text-[var(--color-unknown)] font-mono text-base leading-none" aria-hidden="true">
        ?
      </span>
      <span className="text-[var(--color-unknown)] text-xs uppercase tracking-wide">
        not measured
      </span>
    </span>
  );
}

/** The 0..100 projection, or its absence with the reason. */
export function Projection({
  value,
  absentReason,
}: {
  value: number | null;
  absentReason: string | null;
}) {
  if (value === null) {
    return (
      <div>
        <AbsentMark reason={absentReason} />
        <p className="mt-1 text-xs text-[var(--color-ink-3)] max-w-[22rem]">
          A zero here would mean &ldquo;measured, and fully non-autonomous&rdquo; &mdash; an
          entirely different claim about the world.
        </p>
      </div>
    );
  }
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-5xl font-semibold tabular-nums leading-none">{value}</span>
      <span className="text-sm text-[var(--color-ink-3)]">/ 100</span>
    </div>
  );
}

/** Level rail: the number or "?" plus a colour bar underneath. Anatomy from OpenSSF Scorecard. */
export function LevelRail({ level, measured }: { level: string; measured: boolean }) {
  const n = measured ? Number(level.replace("L", "")) : null;
  const colour =
    n === null
      ? "var(--color-unknown)"
      : n >= 4
        ? "var(--color-pass)"
        : n >= 2
          ? "var(--color-warn)"
          : "var(--color-fail)";
  return (
    <div className="w-14 shrink-0 text-center">
      <div
        className="font-mono text-lg leading-tight"
        style={{ color: measured ? "var(--color-ink)" : "var(--color-unknown)" }}
      >
        {measured ? level : "?"}
      </div>
      <div className="mt-1 h-[3px] w-full rounded-sm" style={{ background: colour }} />
    </div>
  );
}
