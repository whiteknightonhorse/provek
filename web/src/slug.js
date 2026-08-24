/**
 * The one place a `/p/<slug>` path segment is judged before it is interpolated into a URL.
 *
 * WHY IT IS PLAIN JAVASCRIPT AND NOT `.ts`. The gate over this rule
 * (`tests/test_passport_slug_is_judged_before_it_is_fetched.py`) RUNS it under Node against
 * adversarial slugs rather than matching patterns against the source, by the precedent
 * `tests/intake_probe.mjs` set for the intake endpoint. Node on this host is v20 and cannot strip
 * types, so a `.ts` module would have to be compiled before it could be executed - and the thing
 * the test would then be running is the compiler's output, not the file the browser gets. Keeping
 * it as `.js` with a `.d.ts` beside it means the bundle and the gate load the SAME BYTES. L-25 is
 * the standing form: a test can only be about what it can read, and a source scan can say the
 * regular expression is written and can never say what it returns.
 *
 * WHAT THE RULE IS. `App.tsx` derives the slug from `location.pathname` and interpolates it into
 * `/data/passports/<slug>.json`. `route.slice(3).replace(/\/$/, "")` strips only a TRAILING
 * slash, so an inner `/` survives into the path - the finding the 2026-08-24 triage raised against
 * itself while dismissing CodeQL #6 and #7 on the frozen `web-1.0/` copy, where the same fetch was
 * built through a `.replace(/[:/]/g, "_")` that removes the separator. The live tree carried the
 * superset and no alert, and absence of an alert is `not_measured`, not `clean`.
 *
 * WHY THIS SHAPE AND NOT A GUARD ON `known`. Guarding the fetch on a matched registry subject was
 * the other disposition the triage offered, and it fails invariant 1 in the state that matters: an
 * unmatched slug would never be fetched, never resolve, and sit under a skeleton for ever - so
 * "the registry has not loaded yet" and "no such subject" would render identically, which is the
 * defect this component's own four-state loader exists to refuse.
 *
 * `^[A-Za-z0-9_-]+$` is not a guess about what a slug looks like. It was measured against every
 * subject the registry carries and every passport file on disk (8 and 8 on 2026-08-24), each of
 * which is `subject_id.replace(/[:/]/g, "_")` over `git:owner/repo` - so the character set is the
 * one the emitter can actually produce, and a slug outside it cannot be any subject's sanitised
 * form. The empty string is refused by `+`, which matters because `/p//` would otherwise fetch the
 * directory.
 *
 * The anchors were measured too, and JavaScript is not Python here: without the `m` flag `$`
 * matches only at the end of input, so `"abc\n"` is REFUSED. The same pattern in Python's `re`
 * accepts it, and this rule would have shipped one re-implementation away from a trailing-newline
 * hole if the gate had asserted against a Python copy of the regular expression instead of running
 * this file.
 */
const SLUG = /^[A-Za-z0-9_-]+$/;

/**
 * True only for a slug safe to interpolate into a passport path.
 *
 * The `typeof` is not decoration: this is called with a value derived from `location.pathname`,
 * and a non-string reaching `RegExp.test` would be coerced to one - so `null` would be tested as
 * the string `"null"`, which passes the character class.
 */
export function isSafeSlug(slug) {
  return typeof slug === "string" && SLUG.test(slug);
}
