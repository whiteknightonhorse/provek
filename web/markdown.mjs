/**
 * Markdown renderings of the registry and every passport - the OTHER half of "Content follows
 * evidence": `web/discovery.mjs` tells a crawler where the JSON lives, this file is what a request
 * that actually asks for prose (`Accept: text/markdown`) gets back at the SAME address a browser
 * reads as HTML. `web/functions/_middleware.js` is the only thing that chooses between the two;
 * this file has no opinion about HTTP at all.
 *
 * WHY THIS MUST NOT BE HAND-WRITTEN (the ruling this file exists to satisfy). A markdown page typed
 * by hand describes the registry as it was on the day someone typed it, and the registry changes
 * every re-measure (`Daily re-measure`, `f00cfe5`). Two renderings of one fact set - `web/prerender.mjs`
 * for HTML, this file for markdown - are pure functions of the SAME two inputs, `registry.json` and
 * `public/data/passports/*.json`, so there is nothing for a hand-maintained copy to drift from
 * silently: a build that regenerates one regenerates the other from the artefact that is actually
 * true today.
 *
 * WHAT IT DOES NOT DO. Render the hand-authored prose pages (`/`, `/method/`, `/apply/`,
 * `/phase-2/`, the method notes) - their content lives in TSX and markdown source respectively, not
 * in registry+passport data, and reproducing THAT by scraping would be the second copy this file
 * exists to avoid rather than a fix for the one Fable named. Only the two pages whose content IS a
 * rendering of the registry get a markdown sibling: `/registry/` and every `/p/<slug>/`.
 *
 * STANDALONE, same shape as `discovery.mjs`: `node markdown.mjs [dataDir] [site]` reads a `data/`
 * directory shaped like `web/public/data/` and prints `{registryMd, passportMd}` on stdout, so a
 * test can check the rendering without paying for the site's full vite/tsc/ssr build.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { SITE, passportEntries, slugOf } from "./discovery.mjs";

/** The registry's own summary sentence - the one `web/prerender.mjs` puts in `<meta
 *  description>` and the Dataset JSON-LD, and the one this file opens the markdown rendering with.
 *  Computed here once so neither copy can say a different count (LAW #ONE-PLACE): before this
 *  export existed, `web/prerender.mjs` held the only computation of it. */
export function registrySentence(registry) {
  const unreadable = registry.subjects.filter(
    (s) => s.projection_absent_reason === "unreadable").length;
  return "Every business submitted to the method, what could be established about each, and the "
    + `evidence behind it. ${registry.count} records, of which ${unreadable} could not be measured `
    + "at all.";
}

/** `/registry/` as markdown: the same rows the HTML table renders, over the same field names the
 *  JSON carries - `not measured (<reason>)` rather than a blank cell, because an absence with no
 *  reason attached is the founding defect this whole project measures other subjects for. */
export function buildRegistryMarkdown(registry, site = SITE) {
  const rows = registry.subjects.map((s) => {
    const slug = slugOf(s.subject_id);
    const projection = s.projection === null
      ? `not measured (${s.projection_absent_reason})`
      : `${s.projection}/100`;
    return `| [${s.subject_id}](${site}/p/${slug}/) | ${s.status} | ${projection} `
      + `| [passport.json](${site}/data/passports/${slug}.json) |`;
  }).join("\n");

  return `# Provek registry

${registrySentence(registry)}

${registry.disclaimer}

Generated ${registry.generated_at}. Machine-readable form: `
    + `[registry.json](${site}/data/registry.json).

| Subject | Status | Projection | Evidence |
| --- | --- | --- | --- |
${rows}
`;
}

/** One passport as markdown. Every field printed here is read straight off the passport object -
 *  the same one `web/prerender.mjs:ldPassport` turns into JSON-LD and `web/functions/badge/[id].js`
 *  reads for the badge - so there is one place that knows what a passport contains, not three that
 *  each format it their own way.
 *
 *  THE PROJECTION IS NEVER PRINTED BARE, for the reason `badge/[id].js`'s own header states: a
 *  number with no name travelling alone is the overclaim this project exists to catch other
 *  subjects making. It always carries the word "projection" and, when absent, the reason. */
export function buildPassportMarkdown(passport, site = SITE) {
  const p = passport;
  const slug = slugOf(p.subject_id);
  const projection = p.verified.projection === null
    ? `not measured (${p.verified.projection_absent_reason})`
    : `${p.verified.projection}/100`;
  const affiliationNote = p.verifier_affiliation === "same_owner"
    ? "\n**Affiliated verification**: the subject and the verifier's owner are the same party.\n"
    : "";
  const opRows = p.verified.operations.map((o) =>
    `| ${o.operation} | ${o.level} | ${o.measured ? o.confidence : "-"} `
    + `| ${o.limiters_applied.length ? o.limiters_applied.join(", ") : "-"} |`).join("\n");

  return `# Autonomy passport: ${p.subject_id}

Status: **${p.status}**. Issued ${p.issued_at.slice(0, 10)}, valid until `
    + `${p.valid_until.slice(0, 10)}. Evidence read through the ${p.access_channel} channel.
${affiliationNote}
Projection: **${projection}**

## Operations

| Operation | Level | Confidence | Limiters |
| --- | --- | --- | --- |
${opRows}

${p.disclaimer}

Machine-readable form: [passport.json](${site}/data/passports/${slug}.json). `
    + `Badge: [badge.svg](${site}/badge/${slug}.svg). `
    + `Brief: [${site}/p/${slug}/brief](${site}/p/${slug}/brief).
`;
}

const isMain = process.argv[1] && process.argv[1].endsWith("markdown.mjs");
if (isMain) {
  const dataDir = process.argv[2] ?? "public/data";
  const site = process.argv[3] ?? SITE;
  const registry = JSON.parse(readFileSync(join(dataDir, "registry.json"), "utf8"));
  const entries = passportEntries(registry, join(dataDir, "passports"));
  const passportMd = {};
  for (const { slug } of entries) {
    const doc = JSON.parse(readFileSync(join(dataDir, "passports", `${slug}.json`), "utf8"));
    passportMd[slug] = buildPassportMarkdown(doc.passport, site);
  }
  process.stdout.write(JSON.stringify({
    registryMd: buildRegistryMarkdown(registry, site),
    passportMd,
  }));
}
