/**
 * Runs `web/functions/badge/[id].js` against a REAL passport file on disk, rather than a
 * synthetic fixture - the control `tests/test_badge_never_prints_a_bare_level.py` needs to prove
 * the "no bare level" guarantee against data this project actually published, not only against a
 * shape a fixture author chose to write.
 *
 * argv: <path to a passports/*.json file> <slug>
 */
import { readFileSync } from "node:fs";
import { onRequestGet } from "../web/functions/badge/[id].js";

const [, , fixturePath, slug] = process.argv;
const fixture = JSON.parse(readFileSync(fixturePath, "utf8"));
const env = { ASSETS: { fetch: async () => new Response(JSON.stringify(fixture)) } };
const request = new Request(`https://provek.dev/badge/${slug}.svg`);
const response = await onRequestGet({ request, params: { id: `${slug}.svg` }, env });
process.stdout.write(await response.text());
