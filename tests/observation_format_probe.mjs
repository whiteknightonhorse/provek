/**
 * Runs `web/src/formatObservation.js` directly, the way `tests/slug_probe.mjs` runs
 * `web/src/slug.js`: a source scan can prove the function is written and never that it returns
 * the right thing for a boolean, a share, or a count. One scenario per argv[2]; prints the
 * result as JSON so the caller can tell a returned STRING "false" apart from a returned
 * BOOLEAN false - which is exactly the distinction the defect this guards turned on.
 */
import { formatObservationValue, SHARE_OBSERVATION_KEYS } from "../web/src/formatObservation.js";

const CASES = {
  identity_window_closed_true: () => formatObservationValue("identity_window_closed", true),
  identity_window_closed_false: () => formatObservationValue("identity_window_closed", false),
  signed_commit_share_zero: () => formatObservationValue("signed_commit_share", 0.0),
  signed_commit_share_five_percent: () => formatObservationValue("signed_commit_share", 0.05),
  bot_author_share_third: () => formatObservationValue("bot_author_share", 1 / 3),
  distinct_authors_count: () => formatObservationValue("distinct_authors", 2),
  workflow_runs_count: () => formatObservationValue("workflow_runs", 318),
  unlinked_key_count_count: () => formatObservationValue("unlinked_key_count", 0),
  share_keys_list: () => SHARE_OBSERVATION_KEYS,
};

const name = process.argv[2];
if (!Object.prototype.hasOwnProperty.call(CASES, name)) {
  process.stderr.write(`unknown scenario ${JSON.stringify(name)}\n`);
  process.exit(2);
}
process.stdout.write(JSON.stringify({ scenario: name, result: CASES[name]() }));
