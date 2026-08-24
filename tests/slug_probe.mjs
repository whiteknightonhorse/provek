/**
 * The instrument for `tests/test_passport_slug_is_judged_before_it_is_fetched.py`: it RUNS the
 * slug guard instead of reading it.
 *
 * WHY IT EXISTS AT ALL. A source scan can see that `^[A-Za-z0-9_-]+$` is written and can never see
 * what it returns. The two are not the same claim, and the gap between them is wide enough to ship
 * a hole through: the same pattern in Python's `re` accepts a trailing newline and in JavaScript
 * does not, so a gate that re-implemented the rule in the test's own language would have asserted
 * a property the browser does not have. This file imports `web/src/slug.js` - the exact module the
 * bundle ships, no compile step between them - and reports what it answers. L-25 is the standing
 * form of it; `tests/intake_probe.mjs` is the precedent.
 *
 * WHAT IT IS STILL NOT. This runs the GUARD. It does not run `App.tsx`, so it cannot say that the
 * guard is called before the fetch - that half is asserted against the source by the caller, which
 * says so in its own WHAT IS NOT ASSERTED paragraph rather than leaving the boundary implied.
 * `useEffect` does not fire under `preact-render-to-string`, so there is no server render that
 * would exercise the real path, and pretending otherwise would be a claim about an instrument that
 * cannot see the quantity (L-10).
 *
 * Reads a JSON array of slugs as argv[2]. Emits one JSON array on stdout, one object per slug,
 * carrying both the verdict AND the URL `App.tsx` would build from it - because the property the
 * caller cares about is where the request goes, and a boolean alone would let a refusal be
 * asserted while the path was still constructed. Every failure is loud: unreadable input exits 2.
 */

import { isSafeSlug } from "../web/src/slug.js";

let slugs;
try {
  slugs = JSON.parse(process.argv[2]);
  if (!Array.isArray(slugs)) throw new Error("argv[2] is not a JSON array");
} catch (e) {
  // Exit 2 rather than an empty array: a probe that cannot read its input must not be
  // indistinguishable from one that was asked about nothing (invariant 1).
  console.error(`slug_probe: ${e.message}`);
  process.exit(2);
}

// The interpolation is copied from `App.tsx` deliberately, so the recorded URL is the one the
// component would have requested. It is reported for EVERY slug including the refused ones, which
// is what lets the caller assert that a refused slug never leaves /data/passports/.
const url = (slug) => `/data/passports/${slug}.json`;

console.log(
  JSON.stringify(
    slugs.map((slug) => ({ slug, safe: isSafeSlug(slug), url: url(slug) })),
    null,
    1,
  ),
);
