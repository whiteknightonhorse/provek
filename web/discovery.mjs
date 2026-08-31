/**
 * The one generator for the "detection maps" a crawler or agent reads before it reads the site:
 * /.well-known/api-catalog (RFC 9727, application/linkset+json) and /llms.txt.
 *
 * WHY ONE FILE. Three copies of the same map inevitably drift - the operator's own words for this
 * task. `buildApiCatalog` and `buildLlmsTxt` are pure functions of exactly one input, `ids`: the
 * set of passport identifiers. Nothing about either resource is typed twice, so there is nothing
 * for a second copy to disagree with.
 *
 * WHAT IS LISTED. Only what exists and answers today: the registry, every passport actually
 * present, the single real endpoint (`/api/apply` - GET 405, empty POST 400, nothing else), and
 * the sitemap. Nothing here describes a capability this project does not have (no OAuth
 * discovery, no MCP server, no skills) - a verdict this project cannot itself reproduce is exactly
 * what it marks other subjects down for claiming.
 *
 * STANDALONE ON PURPOSE. `node discovery.mjs [dataDir] [site]` reads a `data/` directory shaped
 * like `web/public/data/` (a `registry.json` and a `passports/` folder) and prints one JSON object
 * with both generated documents plus the id sets each is built from - so a test can check for
 * drift without paying for the site's full vite/tsc/ssr build.
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

export const SITE = "https://provek.dev";

/** Passport ids, from the one place they are ever listed: the directory the site itself serves. */
export function passportIdsFromDir(passportsDir) {
  return readdirSync(passportsDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(/\.json$/, ""))
    .sort();
}

/** `{slug, subjectId}` pairs, slug-sorted - the one place a filesystem slug and the registry's own
 *  `subject_id` are joined. Guessing `subject_id` back out of the slug (undoing the `:`/`/` -> `_`
 *  collapse `prerender.mjs` applies) is not attempted: it is not invertible in general, and a
 *  passport title is exactly the kind of thing this project's own doctrine says must come from a
 *  measurement, not a guess. */
export function passportEntries(registry, passportsDir) {
  const bySlug = new Map(
    registry.subjects.map((s) => [s.subject_id.replace(/[:/]/g, "_"), s.subject_id]));
  return passportIdsFromDir(passportsDir).map((slug) => ({
    slug,
    subjectId: bySlug.get(slug) ?? slug,   // falls back to the slug itself rather than throw: a
    // passport on disk with no registry row is a real drift this generator must still be able to
    // describe, not a crash that hides which resource is unaccounted for.
  }));
}

/** RFC 9727 API catalog: a linkset (RFC 9264) anchored at the site, listing every JSON resource
 *  and the one real endpoint. `item` is used throughout - not `service-desc` - because that
 *  relation names formal API description documents (OpenAPI, AsyncAPI) and this project has none;
 *  claiming one would be the same overclaim the project refuses to let other subjects make. */
export function buildApiCatalog(entries, site = SITE) {
  const item = [
    {
      href: `${site}/data/registry.json`,
      type: "application/json",
      title: "Provek registry: every subject submitted, what could be established, and the evidence behind it.",
    },
    ...entries.map(({ slug, subjectId }) => ({
      href: `${site}/data/passports/${slug}.json`,
      type: "application/json",
      title: `Autonomy passport: ${subjectId}`,
    })),
    {
      href: `${site}/api/apply`,
      type: "text/plain",
      title: "Submit a subject for verification. This is the only endpoint: GET answers 405, an empty POST answers 400, no other method or path exists.",
    },
    {
      href: `${site}/sitemap.xml`,
      type: "application/xml",
      title: "Sitemap.",
    },
  ];
  return { linkset: [{ anchor: `${site}/`, item }] };
}

/** llms.txt (llmstxt.org convention): a short map for models, over the same entries as the catalog. */
export function buildLlmsTxt(entries, site = SITE) {
  const passportLines = entries
    .map(({ slug, subjectId }) => `- [${subjectId}](${site}/data/passports/${slug}.json): autonomy passport, JSON`)
    .join("\n");
  return `# Provek

> Verification of how much of a business runs without a human in the loop, established from
> evidence rather than from a claim. The registry and every passport are meant to be found and
> quoted. Nothing here is meant to be trained on: see Content-Signal in /robots.txt - a verdict
> baked into model weights has no field it can go stale in, and every passport here does.

## Pages

- [Registry](${site}/registry/): every subject submitted, what could be established about each, and why not where it could not.
- [Method](${site}/method/): how a level is assigned to an operation, how evidence is classed, and what the score does not measure.
- [Apply](${site}/apply/): request verification. Free at this stage. Public repositories only.
- [Phase 2](${site}/phase-2/): specified and not in service - no application taken, no date given.

## Data (JSON)

- [Registry](${site}/data/registry.json)
${passportLines}

## API

- [API catalog](${site}/.well-known/api-catalog): RFC 9727 linkset of every resource above and the one endpoint below.
- [/api/apply](${site}/api/apply): the only endpoint on this site. GET -> 405. Empty POST -> 400.
`;
}

const isMain = process.argv[1] && process.argv[1].endsWith("discovery.mjs");
if (isMain) {
  const dataDir = process.argv[2] ?? "public/data";
  const site = process.argv[3] ?? SITE;
  const registry = JSON.parse(readFileSync(join(dataDir, "registry.json"), "utf8"));
  const registrySubjectIds = registry.subjects
    .map((s) => s.subject_id.replace(/[:/]/g, "_"))
    .sort();
  const entries = passportEntries(registry, join(dataDir, "passports"));
  process.stdout.write(JSON.stringify({
    registrySubjectIds,
    passportIds: entries.map((e) => e.slug),
    apiCatalog: buildApiCatalog(entries, site),
    llmsTxt: buildLlmsTxt(entries, site),
  }));
}
