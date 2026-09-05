/** The one copy mechanism on the site (SPEC 3.7 item 7). Extracted from the passport page's
 * `ShareActions`, which duplicated this exact logic once per button; the passport now imports
 * this component too, so a template page and a passport page share one implementation rather
 * than two that could drift.
 *
 * `navigator.clipboard.writeText` is the only path attempted - no `execCommand` fallback. It
 * needs a secure context, which this site always is, and every browser this site otherwise
 * supports ships it. A failed write says so rather than pretending: a silent failure here is a
 * visitor who pastes nothing and assumes the button is broken. */
import { useState } from "react";

type State = "idle" | "copied" | "error";

export function CopyButton({
  getText,
  idleLabel = "Copy",
  className,
  announce = "Copied to clipboard.",
}: {
  /** Called at click time, not render time - for a template page the payload is read straight
   *  off the page's own `<pre>` DOM node, never from a second string carried in the bundle
   *  (SPEC 3.7 item 7's other requirement, `LAW-COPY-IS-THE-ARTEFACT`). */
  getText: () => string;
  idleLabel?: string;
  className?: string;
  announce?: string;
}) {
  const [state, setState] = useState<State>("idle");

  const copy = () => {
    navigator.clipboard?.writeText(getText()).then(
      () => setState("copied"),
      () => setState("error"),
    );
  };

  const label =
    state === "copied" ? "Copied" : state === "error" ? "Copy failed - select and copy manually" : idleLabel;

  return (
    <span className="inline-flex items-center gap-2">
      <button
        type="button"
        onClick={copy}
        className={
          className ??
          "text-xs border border-[var(--color-line-2)] px-2.5 py-1.5 min-h-8 inline-flex items-center hover:bg-[var(--color-paper-2)]"
        }
      >
        {label}
      </button>
      {/* A visible label change is a sighted-only confirmation; a screen reader needs its own,
          the same sr-only aria-live device Chrome.tsx's masthead and this button's predecessor
          both already use. */}
      <span aria-live="polite" className="sr-only">
        {state === "copied" && announce}
        {state === "error" && "Copy failed. Select the text and copy it manually."}
      </span>
    </span>
  );
}
