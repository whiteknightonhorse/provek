/**
 * Design tokens, copied out of `web/src/index.css`'s two `:root` blocks.
 *
 * A Cloudflare Pages Function returns raw bytes over HTTP - it never loads the site's stylesheet,
 * so it cannot reach a CSS custom property the way a component under `web/src` does. The badge is
 * worse off still: it is an `<img>` embedded on SOMEBODY ELSE'S page, which never defines
 * `--c-pass` at all, so inheriting rather than copying would render every token as the browser's
 * default black the instant it left provek.dev.
 *
 * `tests/test_badge_palette_matches_index_css.py` reads both this file and `index.css` and fails
 * the moment a value here stops matching the one a human sees on the real site - the usual answer
 * in this project to a rule that has to live in two places at once.
 */
export const LIGHT = {
  ink: "#16171c",
  ink2: "#464b57",
  ink3: "#666c78",
  line: "#e4e2dd",
  line2: "#cbc8c1",
  paper: "#fffefb",
  paper2: "#f5f3ee",
  pass: "#2c6b3c",
  warn: "#8a5b12",
  fail: "#9b2b2b",
  unknown: "#666c78",
  slot: "#8d8677",
};

export const DARK = {
  ink: "#e8e6e1",
  ink2: "#b2b0aa",
  ink3: "#8f8d88",
  line: "#2c2f36",
  line2: "#414650",
  paper: "#191b20",
  paper2: "#121317",
  pass: "#6fb37c",
  warn: "#d9a85c",
  fail: "#e08a8a",
  unknown: "#8f8d88",
  slot: "#6a707a",
};

/** A validity STATE, never an autonomy level - see the header of `badge/[id].js` for why that
 *  distinction is load-bearing here in particular. `suspended`, `failed` and `withdrawn` share the
 *  fail colour because all three are negative public verdicts (`NEGATIVE_PUBLIC_VERDICTS`,
 *  `src/registry/lifecycle.py`); `unverified` and `in_progress` share the neutral colour used
 *  everywhere else in this codebase for "nobody has looked yet". */
function statusColors(p) {
  return {
    verified: p.pass,
    stale: p.warn,
    suspended: p.fail,
    failed: p.fail,
    withdrawn: p.fail,
    unverified: p.unknown,
    in_progress: p.unknown,
  };
}

export const STATUS_COLOR_LIGHT = statusColors(LIGHT);
export const STATUS_COLOR_DARK = statusColors(DARK);
