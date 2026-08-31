/** Rendering of a measured value versus an absent one.
 *
 * DECISION D-03, and it is the single most load-bearing rule in this interface: an unmeasured
 * quantity renders as its own state with its own glyph and its own neutral colour. It never
 * renders as 0, never as an empty cell, never as a dash that could be mistaken for either.
 *
 * The pattern is borrowed from OpenSSF Scorecard, where an unevaluable check shows "?" in grey
 * while a genuinely failing check shows a measured 0 in red. Two different states of the world,
 * two different appearances - proven in a product people already trust. */

export const REASON_TEXT: Record<string, string> = {
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

/** The 0..100 projection, or its absence with the reason.
 *
 * `arithmetic`, added 2026-08-31: the exact expression `src/verify/scorer.py::projection()` used
 * to reach `value` - `round(sum(level for measured) / (5 * len(measured)) * 100)` - spelled out
 * in the reader's units so "60" reads as "one operation, at L3, out of a possible L5" rather than
 * as a raw score out of 100. Built by the caller from the real operations, never hand-typed here:
 * a mismatch between this line and the number above it would be worse than the plain number was. */
export function Projection({
  value,
  absentReason,
  arithmetic,
}: {
  value: number | null;
  absentReason: string | null;
  arithmetic?: string | null;
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
    <div>
      <div className="flex items-baseline gap-2">
        <span className="text-5xl font-semibold tabular-nums leading-none">{value}</span>
        <span className="text-sm text-[var(--color-ink-3)]">/ 100</span>
      </div>
      {arithmetic && (
        <p className="mt-1 font-mono text-[11.5px] text-[var(--color-ink-3)]">{arithmetic}</p>
      )}
    </div>
  );
}

/** Level rail: the number, plus a six-notch scale (L0..L5) underneath filled to the level.
 *
 * ACCEPTED LAYOUT, 2026-08-31, AND THE ONE THING THE MOCKUP GOT WRONG.
 *
 * The approved mockup filled the notches in `--color-pass`. That is exactly the shape Fable's
 * I3 was written against: "this rail used to paint L4-L5 in the pass colour and L0-L1 in the
 * fail colour, while the Method page said in words that the ladder does not measure whether
 * autonomy is desirable." A green scale says HIGHER IS BETTER two lines under a sentence that
 * says the opposite - Measures autonomy. Not reliability, not decision quality.
 *
 * The conflict was carried to the operator rather than resolved by either side of it, and the
 * ruling on 2026-08-31 was NEUTRAL INK: the notches fill in `--color-ink-2`, so the rail reads
 * as a POSITION on a scale (three of six) and never as a grade. The layout the mockup was
 * approved for survives intact; only the judgement the colour smuggled in is gone.
 *
 * L5 means "no human control path exists for this operation" - a fact, not an achievement.
 * Nothing on this rail may imply otherwise. */
export function LevelRail({ level, measured }: { level: string; measured: boolean }) {
  const n = measured ? Number(level.replace("L", "")) : null;
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
      {measured && (
        <div className="mt-1">
          <div className="flex gap-0.5" aria-hidden="true">
            {Array.from({ length: 6 }, (_, i) => (
              <div
                key={i}
                className="h-1 flex-1"
                style={{ background: i < (n ?? 0) ? "var(--color-ink-2)" : "var(--color-line)" }}
              />
            ))}
          </div>
          <div className="mt-0.5 font-mono text-[10.5px] text-[var(--color-ink-3)]">L0 … L5</div>
        </div>
      )}
    </div>
  );
}
