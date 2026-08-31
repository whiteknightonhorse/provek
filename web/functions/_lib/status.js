/**
 * `effectiveStatus`, a third time.
 *
 * The rule is ABI-15-5: a `verified` record lapses to `stale` on its own, with no event, once
 * `now >= valid_until`. It already exists twice - `Passport.effective_status` in Python (the
 * definition) and `effectiveStatus` in `web/src/types.ts` (recomputed at hydration, in a real
 * visitor's browser). Neither reaches a Cloudflare Pages Function: Python is not available at the
 * edge, and the TypeScript copy lives inside the Vite/Preact bundle a Function does not build or
 * import. `web/functions/badge/[id].js` renders an `<img>`, which runs no JavaScript at all, and
 * `web/functions/p/[id]/brief.js` answers a raw HTTP GET before any deploy could rebake it - both
 * exist specifically to say the CURRENT word without waiting for the next scheduled rebuild, so
 * neither can be satisfied by a value baked into a JSON file at the last `npm run build`.
 *
 * This is the one place those two Functions share the computation, so it drifts from the other
 * two copies at most twice rather than four times. `tests/effective_status_probe.mjs` runs this
 * file directly, the same way `tests/slug_probe.mjs` runs `web/src/slug.js`.
 */
export function effectiveStatus(status, validUntil, now = new Date()) {
  if (status !== "verified") return status;
  return now >= new Date(validUntil) ? "stale" : "verified";
}
