/** The corrections log, in full. All six corrections this project has ever published, byte-for-byte.
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
 *
 * THE 2026-09-03 ERRATUM (AUD-001, Fable's cross-repository sweep) is published rather than
 * quietly folded into the intake fix it describes - D-28's rule again, this time for a stored fact
 * about a row rather than a stale sentence about a process. See D-54 in DECISIONS.md for the full
 * incident.
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
          Every erratum this project has published, in full and unabridged. Six exist today.
        </p>

        {/* THE MOVE, NAMED. A reader who bookmarked or quoted the original location on `/registry/`
            should find the same words here, not a summary standing in for them. */}
        <p className="mt-3 text-xs text-[var(--color-ink-3)]">
          The first two corrections below were originally published directly on the registry page.
          They were moved to this page on 2026-09-02, unabridged, when the registry itself was given
          a single compact line pointing here instead of carrying the full text of every correction
          it has ever needed. The third was published directly here, the address this page has
          carried since that move. The fourth was added on 2026-10-23, for a change made on 2026-09-01
          that had no notice of its own. The fifth was added on 2026-10-26, for a subject withdrawn
          from the registry because its project was retired. The sixth was added on 2026-10-26, for a
          method note that stated two live author counts the registry did not show.
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

          <div>
            <Strip tone="warn">
              <strong>Erratum, 2026-09-03.</strong> A defect in the corpus, not the rule that reads
              it: cryptocardhub-public, a repository the operator owns, was admitted to the registry
              on 2026-08-25 marked independent, and no gate ever compared that stored value to the
              owner the repository's own name states. The row read as an independent verification of
              the operator's own project for the length of that error. It now reads same_owner, the
              passport has been re-issued, and a gate added the same day refuses to publish the
              registry if any subject the operator owns carries anything else.
            </Strip>
          </div>

          <div>
            <Strip tone="warn">
              <strong>Correction, 2026-09-01.</strong> APIbase&rsquo;s autonomy projection moved from 60
              to 40 and its development-initiation level from L3 to L2 when it was re-measured that
              day. No defect in the rule or in the earlier data was found: between the two
              measurements the repository&rsquo;s head moved, and the 30-day window then held a commit
              whose author the platform did not attribute to an account (unlinked commit share 0.0 to
              0.009; one unlinked key). Under platform closure &mdash; an author count is a count only
              when every non-bot commit in the window is attributed &mdash; an open identity window
              floors the level at L2. The earlier figure was a true reading of the window it was
              taken from, and is superseded.
            </Strip>
          </div>

          <div>
            <Strip tone="warn">
              <strong>Correction, 2026-10-26.</strong> Subject withdrawn: project retired 2026-10. The
              subject audiobook-shorts-series was removed from the registry, and its passport and
              badge with it, because the project it described no longer exists. Its row read
              unverified with the reason unreadable and carried no verdict, so no verdict changed.
              Git history and copies kept by third parties still hold what was published (D-72).
            </Strip>
          </div>

          <div>
            <Strip tone="warn">
              <strong>Correction, 2026-10-26.</strong> The method note on the autonomy levels said
              that &ldquo;provek stays L3 because a second identity remains&rdquo; and that APIbase
              had a &ldquo;single author&rdquo; and was L3 because its signed share was 0.0. The
              registry showed neither: on 2026-10-23 and again on 2026-10-26, provek had one
              attributed author (signed share 0.302, then 0.283) and APIbase had two (signed share
              0.013, then 0.022). The note has been rewritten with each live number dated, and now
              says what platform attribution does and does not prove: an author address is written
              by the committer, so the count is a lower bound only for a subject that does not forge
              it. No score, threshold or rule changed. Interested party: the operator&rsquo;s own
              subjects; found by an external audit (Opus, 2026-10-24).
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
