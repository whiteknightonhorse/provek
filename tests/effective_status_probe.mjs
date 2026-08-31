/**
 * Runs `web/functions/_lib/status.js` directly, the way `tests/slug_probe.mjs` runs
 * `web/src/slug.js`: a source scan can prove the code is written and never that it returns the
 * right thing. One scenario per argv[2]; prints the result as JSON.
 */
import { effectiveStatus } from "../web/functions/_lib/status.js";

const CASES = {
  verified_before_expiry: () =>
    effectiveStatus("verified", "2099-01-01T00:00:00Z", new Date("2026-01-01T00:00:00Z")),
  verified_lapsed: () =>
    effectiveStatus("verified", "2020-01-01T00:00:00Z", new Date("2026-01-01T00:00:00Z")),
  verified_exactly_at_boundary: () =>
    effectiveStatus("verified", "2026-01-01T00:00:00Z", new Date("2026-01-01T00:00:00Z")),
  unverified_untouched_by_the_date: () =>
    effectiveStatus("unverified", "2020-01-01T00:00:00Z", new Date("2026-01-01T00:00:00Z")),
  suspended_untouched_by_the_date: () =>
    effectiveStatus("suspended", "2020-01-01T00:00:00Z", new Date("2026-01-01T00:00:00Z")),
};

const name = process.argv[2];
if (!Object.prototype.hasOwnProperty.call(CASES, name)) {
  process.stderr.write(`unknown scenario ${JSON.stringify(name)}\n`);
  process.exit(2);
}
process.stdout.write(JSON.stringify({ scenario: name, result: CASES[name]() }));
