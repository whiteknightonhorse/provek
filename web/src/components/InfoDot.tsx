import type { ReactNode } from "react";

/** Passport clarity (phase-2 plan): the accessible replacement for a bare `title=` attribute.
 *
 * `title` is a mouse-only affordance - nothing focuses it (a keyboard user tabbing through the
 * page never sees it) and nothing hovers it on a phone (a touch user gets no affordance at all),
 * which is exactly why this schema's self-declared/assumed badges were unreadable off a desktop -
 * the main clarity defect this task exists to close.
 *
 * `<details>` is native, needs no JS, and both problems disappear for free: the `<summary>` is a
 * real focusable element (Tab reaches it, Enter/Space toggles it, per the HTML spec's own
 * disclosure-widget behaviour) and a tap opens it exactly the way a tap opens anything else on the
 * page.
 *
 * INTENTIONALLY NOT A FLOATING POPOVER. The content unfolds inline, below the dot, so it can
 * never be clipped by a scrolling or `overflow:hidden` ancestor and never has to compute a
 * position - the same reason `Landing.tsx`'s video transcript already uses a plain `<details>`
 * rather than a tooltip library. A dot inside a narrow table cell or a four-across tile still
 * reads correctly: it just pushes the row taller while open, which every layout on this page
 * already tolerates for its own `<AbsentMark>`/`Strip` blocks.
 */
export function InfoDot({ children, label = "More info" }: { children: ReactNode; label?: string }) {
  return (
    <details className="inline-block align-baseline ml-1 normal-case tracking-normal font-normal">
      <summary
        aria-label={label}
        className="inline-flex h-4 w-4 cursor-pointer select-none items-center justify-center rounded-full border border-[var(--color-line-2)] text-[10px] leading-none text-[var(--color-ink-3)] [&::-webkit-details-marker]:hidden"
      >
        i
      </summary>
      <div className="mt-1 max-w-[22rem] text-xs font-normal normal-case tracking-normal text-[var(--color-ink-2)]">
        {children}
      </div>
    </details>
  );
}
