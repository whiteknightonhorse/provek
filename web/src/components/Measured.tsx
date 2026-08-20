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
      {/* The reason is the substance of this state, not a hint about it. `title` alone reaches a
          mouse and nothing else, which would leave a keyboard or screen-reader user with the bare
          word "unmeasured" and no way to learn why - the precise omission this mark exists to
          prevent. */}
      <span className="sr-only">
        {reason ? `not measured: ${REASON_TEXT[reason] ?? reason}` : "not measured, reason not stated"}
      </span>
      {/* THE DEVICE. Not a question mark and not a dash - a BLANK that has kept its place, ruled
          on the line the value would have occupied. A dash says "nothing here"; a slot says
          "something belongs here and nobody has filled it in", which is the true statement. */}
      <span className="slot" aria-hidden="true" />
      <span className="slot--label" aria-hidden="true">not measured</span>
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
  // NO GOOD/BAD MAPPING (Fable, I3). This rail used to paint L4-L5 in the pass colour and
  // L0-L1 in the fail colour, while the Method page said in words that the ladder does not
  // measure whether autonomy is desirable. L0 - "a human performs the operation" - is a state,
  // and a company at L0 on treasury control may well be the prudent one. The bar now shows
  // POSITION on the ladder in one neutral ink; the number carries the fact.
  return (
    <div className="w-14 shrink-0 text-center">
      <div
        className="font-mono text-lg leading-tight"
        style={{ color: measured ? "var(--color-ink)" : "var(--color-unknown)" }}
      >
        {measured
          ? level
          : <><span className="slot" aria-hidden="true" /><span className="sr-only">not measured</span></>}
      </div>
      {/* The bar restates the level it sits under; it carries no fact of its own, so it is
          decorative rather than a second, colour-only channel. */}
      {measured && (
        <div className="mt-1 h-[3px] w-full rounded-sm bg-[var(--color-line)]" aria-hidden="true">
          <div
            className="h-full rounded-sm bg-[var(--color-ink-2)]"
            style={{ width: `${((n ?? 0) / 5) * 100}%` }}
          />
        </div>
      )}
    </div>
  );
}
