/** T-SG-14 (`~/taskloop/briefs/SG-00-ruling-1.md` §SG-14; incubator's own decision, `DECISIONS.md`
 * D-61). The operator's growth brief called this "open verification challenge" and the ruling
 * accepted it "as a page and an application flag" - both built here and in `Apply.tsx`
 * respectively, never in `src/verify` or `src/collector/github.py` (D-10's conflict-of-interest
 * rule: sales and growth work never reaches the scorer).
 *
 * WHY THIS IS ITS OWN PAGE AND NOT A SECTION OF `Apply.tsx`. The two pages answer different
 * questions. `/apply/` is for somebody who already decided to be verified and needs the form;
 * `/challenge/` is for somebody who has not decided yet and needs the one fact that makes deciding
 * possible - that "verified" is not a favour handed to companies who ask nicely, it is the SAME
 * pipeline, run the same way, on request, for anyone. Folding that fact into the form page would
 * bury it under the fields; a stranger arriving from a cold outreach email or a partner mention
 * needs it to be the whole page.
 *
 * NOT A CONTEST. SPEC.md §9's anti-example names Product Hunt and kin - "big logos, vote counts,
 * gradients... they sell attention; we sell evidence" - and a page called a "challenge" is the one
 * surface on this site most at risk of drifting toward that register. So this page makes no
 * promise about the OUTCOME (a low score, or `not_measured`, is named as the ordinary result, not
 * hedged around), offers no leaderboard or count of participants (that is I11's rejected idea,
 * `~/taskloop/briefs/SG-00-ruling-1.md` §2), and its one link goes to the same `/apply/` form
 * everyone else uses, carrying only a query flag for `functions/api/apply.js` to record where the
 * request came from - never a different queue, priority, or reviewer.
 *
 * "incubator" DOES NOT APPEAR ON THIS PAGE. `tests/test_incubator_word_is_descriptive_only.py`
 * binds the word's one sanctioned descriptive use to exactly three funnel surfaces
 * (`/apply/`, `/build/`, `/registry/`) via `INCUBATOR_SENTENCE`; this is a fourth, unnamed by that
 * ruling, and reusing the sentence here would put a fifth surface silently inside a rule written
 * to hold at three (or reintroduce the word outside the rule's placement requirement, which the
 * ruling never considered for this page at all). Simpler to just not use the word. */

import { Page, Strip } from "../components/Chrome";

export default function Challenge() {
  return (
    <Page>
      <div className="max-w-[40rem]">
        <h1 className="text-2xl font-semibold tracking-tight">Open verification challenge</h1>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          Free, public, and open to any business whose operations run through agents &mdash; whether
          or not we have ever heard of it.
        </p>

        <p className="mt-4 text-sm text-[var(--color-ink-2)]">
          If you operate &mdash; or believe you operate &mdash; a business where agents run real
          operations with little or no human in the loop, we will look at the public evidence and
          say what it shows. This is not a different offer from the one everyone else gets: it is
          the same request, on the same form, scored by the same public method, whether you found
          us or we found you.
        </p>

        <div className="mt-5">
          <Strip tone="info">
            <strong>This is not a separate pipeline.</strong> A request made from this page joins
            the same queue, is read against the same public methodology, and can come back{" "}
            <code className="font-mono text-xs">not_measured</code> on some or all operations, or
            at a lower level than you expected &mdash; exactly as it can for any other subject. We
            record that a request came from this page so we can tell later whether naming the
            challenge brought in subjects the ordinary form did not; nothing about how it is
            scored changes because of it.
          </Strip>
        </div>

        <p className="mt-5 text-sm">
          <a
            href="/apply/?via=challenge"
            className="inline-block border border-[var(--color-ink)] bg-[var(--color-ink)] text-[var(--color-paper)] px-4 py-2 text-sm font-medium"
          >
            Request verification &rarr;
          </a>
        </p>

        <h2 className="mt-8 text-sm font-medium">What "open" means here</h2>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          Anyone may ask, not only businesses we contact first. We do not keep a leaderboard, a
          participant count, or a queue you can jump by asking louder &mdash; the registry itself,
          not a tally of who entered, is the record of who has been looked at and what was found.
        </p>

        <h2 className="mt-6 text-sm font-medium">What we check, and where to see it first</h2>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          The method is published in full at{" "}
          <a href="/method/" className="text-[var(--color-accent)] hover:underline">/method/</a>,
          including what each level of the ladder requires and what evidence class each finding
          rests on. Every past result &mdash; the ones that scored well and the ones that came back
          mostly <code className="font-mono text-xs">not_measured</code> &mdash; stands in the{" "}
          <a href="/registry/" className="text-[var(--color-accent)] hover:underline">registry</a>,
          unedited, so you can read what a real result looks like before asking for your own.
        </p>
      </div>
    </Page>
  );
}
