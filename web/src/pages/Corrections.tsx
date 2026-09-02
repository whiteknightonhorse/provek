/** The corrections log, in full. Both errata this project has ever published, byte-for-byte.
 *
 * WHY THIS PAGE EXISTS (the corrections-log step of the phase-2 plan). `/registry/` used to carry both errata in full,
 * as two `<Strip>` blocks above the table - honest, and increasingly not what a reader who has
 * already seen them wants above the table every time. Moving the text here is not editing it: a
 * corrections log that silently reworded what it corrects would be the exact defect this project
 * exists to catch, one level up. So the two erratum bodies below are the ORIGINAL text, unchanged,
 * and `tests/test_registry_corrections.py` holds them to that byte-for-byte, against a fixture
 * captured from the commit that moved them here.
 *
 * THE 2026-08-25 ERRATUM CARRIES A RESOLUTION, ADDED BESIDE IT, NEVER INSIDE IT (D-28's own rule,
 * applied here). Its original text says the registry "is being re-measured" and that corrected
 * verdicts "will be re-issued" - true in the present tense on 2026-08-25, false by the time this
 * page was written: the re-measure completed, every live passport has carried profile 1.1.0 (the
 * time-windowed reading) since, and the corrected verdicts ARE the ones on `/registry/` today.
 * Editing the original sentence to the past tense would erase the fact that a promise was made in
 * public before it was kept; appending a dated resolution beside it keeps both facts on the page.
 */

import { Page, Strip } from "../components/Chrome";

export default function Corrections() {
  return (
    <Page>
      <div className="max-w-[46rem]">
        <nav className="text-xs text-[var(--color-ink-3)] mb-3">
          <a href="/registry/" className="text-[var(--color-accent)] hover:underline">Registry</a>
          <span className="mx-1.5">›</span>
          <span>Corrections</span>
        </nav>

        <h1 className="text-2xl font-semibold tracking-tight">All corrections</h1>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          Every erratum this project has published, in full and unabridged. Two exist today.
        </p>

        {/* THE MOVE, NAMED. A reader who bookmarked or quoted the original location on `/registry/`
            should find the same words here, not a summary standing in for them. */}
        <p className="mt-3 text-xs text-[var(--color-ink-3)]">
          Both corrections below were originally published directly on the registry page. They were
          moved to this page on 2026-09-02, unabridged, when the registry itself was given a single
          compact line pointing here instead of carrying the full text of every correction it has
          ever needed.
        </p>

        <div className="mt-6 space-y-4">
          <div>
            <Strip tone="warn">
              <strong>Erratum, 2026-08-25.</strong> Every passport issued under profile 1.0.0 states an
              evidence window of 30 days. The collector read the last 50 commits by count instead, and
              never looked at a date. The whole registry is being re-measured against the window that
              was published; corrected verdicts will be re-issued together, in whichever direction each
              one moves, and the superseded documents will stay readable rather than disappear.
            </Strip>
            {/* THE RESOLUTION - beside the erratum, never inside it (D-28). */}
            <div className="mt-2 pl-4 border-l-2 border-[var(--color-line-2)]">
              <p className="text-xs text-[var(--color-ink-3)]">
                <strong className="text-[var(--color-ink-2)]">Resolved, 2026-08-25 into 2026-09-02.</strong>{" "}
                The re-measure above completed the same day it was announced. Every passport on the
                registry has carried profile 1.1.0 - the time-windowed reading this erratum promised -
                since; the phrase &ldquo;is being re-measured&rdquo; in the paragraph above described a
                state that no longer holds by the time a reader sees it, and is left as it was written
                rather than quietly edited to agree with what happened afterward.
              </p>
            </div>
          </div>

          <div>
            <Strip tone="warn">
              <strong>Erratum, 2026-08-31.</strong> A defect in the rule, not the data: the cohort
              granted L4 to a sole author without checking the signature share the published
              methodology requires for that rung. The rule now matches what is published; APIbase, the
              one passport the defect affected, moved from L4 to L3 (projection 80 to 60). Nothing here
              disappears &mdash; this notice stays up next to the one it follows.
            </Strip>
          </div>
        </div>

        <p className="mt-6 text-xs text-[var(--color-ink-3)]">
          Nothing here disappears when a correction is superseded or resolved. A registry whose past
          statements can quietly vanish is not one whose present statements can be trusted.
        </p>
      </div>
    </Page>
  );
}
