/**
 * Copy shared with `web/src/pages/Passport.tsx` and `web/src/components/Measured.tsx`, for the
 * two Functions that render passport text outside the React bundle: `web/functions/p/[id]/brief.js`
 * and, for the absence reasons only, `web/functions/badge/[id].js`.
 *
 * Every string below is a VERBATIM copy, not a paraphrase - `tests/test_brief_copy_matches_passport_page.py`
 * asserts each one is still a substring of the file it was copied from, so a wording change on the
 * full passport page that is not carried here fails a test instead of quietly producing two
 * summaries of one subject that disagree.
 */
export const OP_LABEL = {
  development_initiation: "Development initiation",
  deployment: "Deployment",
  treasury_control: "Treasury control",
};

export const OP_DESC = {
  development_initiation:
    "Who starts and lands changes to the running system, and whether that requires a human.",
  deployment: "Who ships a change to production, and whether a human approves each one.",
  treasury_control: "Who can move funds, change destinations, or alter spending rules.",
};

export const REASON_TEXT = {
  nothing_qualified: "the check ran and nothing qualified",
  check_did_not_run: "the check did not run",
  unreadable: "the source could not be read",
};
