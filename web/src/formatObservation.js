/**
 * Pure formatting for one MEASURED observation value on the passport page (`Passport.tsx`,
 * "What was actually observed"). Plain JavaScript, not `.ts`, by the precedent `slug.js` set:
 * the gate that guards this (`tests/test_observation_labels_and_values.py`, via
 * `tests/observation_format_probe.mjs`) runs it directly under Node, and Node on this host is
 * v20 and cannot strip types - a `.ts` module would have to be compiled first, and the gate
 * would then be testing the compiler's output rather than the bytes the bundle ships.
 *
 * THE DEFECT THIS CLOSES. React renders a bare boolean child as nothing:
 * `<span>{true}</span>` prints an empty tag, `<span>{false}</span>` prints an empty tag too.
 * `identity_window_closed` is `true`/`false` by construction (`src/collector/github.py`) and
 * IS the verdict for that row, not decoration around it - schema 2.0.0 says a value is never a
 * bare null, and a rendering that turns a real value into a bare NOTHING is the same defect one
 * layer up. Every measured observation now goes through this function instead of `{o.value}`.
 */

/** Keys whose measured value is a share of commits (0..1), not a count. Read from
 *  `scripts/cohort.py`'s `observations()`: these three alone are `round(n / len(commits), 3)`.
 *  `distinct_authors`, `workflow_runs` and `unlinked_key_count` are plain counts and must not be
 *  multiplied by 100 - a count rendered as a percentage would misstate what it measures. */
export const SHARE_OBSERVATION_KEYS = [
  "signed_commit_share",
  "bot_author_share",
  "unlinked_commit_share",
];

/**
 * `value` -> the string to render. Called only for a MEASURED observation (`o.measured` true);
 * an unmeasured field renders through `AbsentMark` instead and never reaches this function.
 *
 * A boolean formats to the word itself ("true"/"false") so the verdict a reader must see is
 * actually on the page. A share formats as a percentage, rounded to one decimal place with no
 * trailing ".0" - `0` still prints as `0%`, distinct from "not measured" (that state never
 * reaches this function at all, so the two can never collide). Anything else (a plain count)
 * prints as its own number, unchanged.
 */
export function formatObservationValue(key, value) {
  if (typeof value === "boolean") return String(value);
  if (SHARE_OBSERVATION_KEYS.includes(key)) {
    const pct = Math.round(value * 1000) / 10;
    return `${pct}%`;
  }
  return String(value);
}
