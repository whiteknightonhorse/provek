/** Runs `web/src/deferral.js` (T-0584) for each reason and prints the text as JSON. argv[2] = reason ("" = null). */
import { deferralKind, deferralText } from "../web/src/deferral.js";
const reason = process.argv[2] === "" ? null : process.argv[2];
process.stdout.write(JSON.stringify({ kind: deferralKind(reason), ...deferralText(reason) }));
