// Prints the `/p/<slug>/` routes web/prerender.mjs would build for the JSON on stdin:
// {registry, passports: [slug...], subjects_doc}. Used by tests/test_withdrawn_subjects_are_not_carried.py.
import { readFileSync } from "node:fs";
import { passportRows, withdrawnSlugs, slugOf } from "../web/discovery.mjs";

const { registry, passports, subjects_doc } = JSON.parse(readFileSync(0, "utf8"));
const have = Object.fromEntries(passports.map((s) => [s, {}]));
const rows = passportRows(registry, have, withdrawnSlugs(subjects_doc));
console.log(JSON.stringify(rows.map((r) => `/p/${slugOf(r.subject_id)}/`)));
