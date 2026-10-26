/**
 * The one generator for the "detection maps" a crawler or agent reads before it reads the site:
 * /.well-known/api-catalog (RFC 9727, application/linkset+json), /llms.txt, /llms-full.txt, and
 * /.well-known/ai-catalog.json (ARD - Agentic Resource Discovery manifest).
 *
 * WHY ONE FILE. Three copies of the same map inevitably drift - the operator's own words for this
 * task. `buildApiCatalog`, `buildLlmsTxt`, `buildLlmsFullTxt`, and `buildAiCatalog` are pure
 * functions of exactly one input, `ids`: the set of passport identifiers. Nothing about any of the
 * four resources is typed twice, so there is nothing for a second copy to disagree with.
 *
 * WHAT IS LISTED. Only what exists and answers today: the registry, every passport actually
 * present, the intake endpoint (`/api/apply` - GET 405, empty POST 400) and its one read (`GET /api/apply/<id>`), and
 * the sitemap. Nothing here describes a capability this project does not have (no OAuth
 * discovery, no MCP server, no A2A; the skills index lists only the SKILL.md files prerender.mjs
 * already serves at /build/<slug>/SKILL.md) - a verdict this project cannot itself reproduce is exactly
 * what it marks other subjects down for claiming. The ARD manifest holds the same three kinds of
 * resource and nothing more: every entry carries `url`, never `data` - inlining a copy of a
 * document already served at a URL would itself be the second copy LAW #ONE-PLACE forbids.
 *
 * STANDALONE ON PURPOSE. `node discovery.mjs [dataDir] [site]` reads a `data/` directory shaped
 * like `web/public/data/` (a `registry.json` and a `passports/` folder) and prints one JSON object
 * with all four generated documents plus the id sets each is built from - so a test can check for
 * drift without paying for the site's full vite/tsc/ssr build.
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { loadTemplates } from "../templates/emit.mjs";

export const SITE = "https://provek.dev";

/** AI agent templates (ADR-0011, D-57) - always the real, committed `templates/` tree, never the
 * `dataDir` override this module's own CLI accepts for registry/passport drift testing: a
 * template is not a fixture that varies per test, it is the one thing this generator reads from a
 * fixed place regardless of what `dataDir` names. `{slug, title, businessOperation}` is all the
 * llms.txt Templates section needs; loading the full parsed template (sections, raw body) here
 * would be the second copy LAW #ONE-PLACE forbids of what `templates/emit.mjs` already computes
 * for the page itself. */
export function templateEntries() {
  return loadTemplates().map((t) => ({
    slug: t.slug, title: t.title, businessOperation: t.businessOperation,
    description: t.description, bodySha256: t.bodySha256,
  }));
}

/** Agent Skills Discovery index (RFC v0.2.0, /.well-known/agent-skills/index.json): one entry per
 *  SKILL.md this site serves at /build/<slug>/SKILL.md. `digest` is the SHA-256 of that file's raw
 *  bytes (`bodySha256` from emit.mjs, the same hash templates/manifest.json records), so it is
 *  read from the one place it is computed, never typed. */
export function buildAgentSkillsIndex(templates, site = SITE) {
  return {
    $schema: "https://schemas.agentskills.io/discovery/0.2.0/schema.json",
    skills: templates.map((t) => ({
      name: t.slug,
      type: "skill-md",
      description: t.description,
      url: `${site}/build/${t.slug}/SKILL.md`,
      digest: `sha256:${t.bodySha256}`,
    })),
  };
}

/** Passport ids, from the one place they are ever listed: the directory the site itself serves. */
export function passportIdsFromDir(passportsDir) {
  return readdirSync(passportsDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(/\.json$/, ""))
    .sort();
}

/** The one collapse of a `subject_id` into a filesystem-safe slug - shared by every generator
 *  that needs it (`prerender.mjs`, `markdown.mjs`), so there is exactly one place that knows how a
 *  slug is built rather than three copies of one regular expression drifting apart (LAW #ONE-PLACE).
 *  Not invertible in general, which is why `passportEntries` below joins it against the registry
 *  instead of guessing `subject_id` back out of a slug found on disk. */
export const slugOf = (id) => id.replace(/[:/]/g, "_");

/** Slugs of the subjects withdrawn in data/subjects.json (T-IN-07, D-72). The cohort run already
 *  drops the row and deletes the passport, so this is the second lock: a stale file that survives
 *  a hand-edit still gets no `/p/<slug>/` page and no sitemap entry. */
export function withdrawnSlugs(subjectsDoc) {
  return new Set((subjectsDoc.withdrawn ?? []).map((w) => slugOf(`git:${w.repo}`)));
}

/** The registry rows that get a `/p/<slug>/` page: a passport exists and the subject is not
 *  withdrawn. The one route-list builder for passport pages, so a test can hold it. */
export function passportRows(registry, passports, withdrawn) {
  return registry.subjects.filter((row) => {
    const s = slugOf(row.subject_id);
    return passports[s] && !withdrawn.has(s);
  });
}

/** `{slug, subjectId}` pairs, slug-sorted - the one place a filesystem slug and the registry's own
 *  `subject_id` are joined. Guessing `subject_id` back out of the slug (undoing the `slugOf`
 *  collapse) is not attempted: it is not invertible in general, and a passport title is exactly
 *  the kind of thing this project's own doctrine says must come from a measurement, not a guess. */
export function passportEntries(registry, passportsDir) {
  const bySlug = new Map(registry.subjects.map((s) => [slugOf(s.subject_id), s.subject_id]));
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
      title: "Submit a subject for verification. GET answers 405, an empty POST answers 400. The one read beside it is GET /api/apply/{id}, which returns the state of one request by its id.",
    },
    {
      href: `${site}/sitemap.xml`,
      type: "application/xml",
      title: "Sitemap.",
    },
  ];
  return { linkset: [{ anchor: `${site}/`, item }] };
}

/** llms.txt (llmstxt.org convention): a short map for models, over the same entries as the catalog,
 *  plus a Templates section (ADR-0011) built from the emitted set, never typed by hand. */
export function buildLlmsTxt(entries, site = SITE, templates = []) {
  const passportLines = entries
    .map(({ slug, subjectId }) => `- [${subjectId}](${site}/data/passports/${slug}.json): autonomy passport, JSON`)
    .join("\n");
  // The brief pages and badge SVGs are served per passport; a sitemap lists pages only, so the
  // SVGs are named here and nowhere else.
  const briefLines = entries
    .map(({ slug, subjectId }) => `- [${subjectId} brief](${site}/p/${slug}/brief): one-page brief`)
    .join("\n");
  const badgeLines = entries
    .map(({ slug, subjectId }) => `- [${subjectId} badge](${site}/badge/${slug}.svg): badge, SVG`)
    .join("\n");
  const templateSection = templates.length
    ? `\n## Templates\n\n${templates
        .map((t) => `- [${t.title}](${site}/build/${t.slug}/): ${t.businessOperation}. Raw: ${site}/build/${t.slug}/SKILL.md`)
        .join("\n")}\n- Skills index (Agent Skills Discovery 0.2.0): ${site}/.well-known/agent-skills/index.json\n`
    : "";
  return `# Provek

> Verification of how much of a business runs without a human in the loop, established from
> evidence rather than from a claim. The registry and every passport are meant to be found and
> quoted. Nothing here is meant to be trained on: see Content-Signal in /robots.txt - a verdict
> baked into model weights has no field it can go stale in, and every passport here does.

## Pages

- [Registry](${site}/registry/): every subject submitted, what could be established about each, and why not where it could not.
- [Method](${site}/method/): how a level is assigned to an operation, how evidence is classed, and what the score does not measure.
- [Build](${site}/build/): AI agent templates - copy one instruction into your own coding agent, get an agent that runs one business operation. Free, no account.
- [Apply](${site}/apply/): request verification. Free at this stage. Public repositories only (the operator's private ones are listed as unreadable).
- [Phase 2](${site}/phase-2/): live: the Provider Catalog (a verified subject may publish an Order link).
- [Phase 3](${site}/phase-2/#phase-3): specified, not in service - no application taken, no date given.
- [Corrections](${site}/registry/corrections/): every erratum the project has published, in full.
- [Challenge](${site}/challenge/): the open verification challenge - free, public, open to any business whose operations run through agents.
- [Witness](${site}/witness/): the GenLayer Evidence Witness - validators independently check an evidence URL and must agree before a record is written. Contract explorer: https://scan.bradbury.genlayer.com/address/0x499eD0E23CbCdC8Fc7735709dca32bCb01638fd6 (pre-reset network; redeploy pending).
- [Autonomy levels L0-L5](${site}/method/notes/autonomy-levels-l0-l5/): what each rung requires as evidence, and which thresholds are assigned rather than measured.
- [Six states of absence](${site}/method/notes/not-measured-is-not-zero/): why a measurement that is absent is not a zero.
- [ERC-8004](${site}/method/notes/what-erc-8004-provides-and-what-it-does-not/): what ERC-8004 standardizes, and what it leaves to a validator.

## Data (JSON)

- [Registry](${site}/data/registry.json)
${passportLines}
- [Templates](${site}/data/templates.json)

## Briefs and badges

${briefLines}
${badgeLines}
${templateSection}
## API

- [API catalog](${site}/.well-known/api-catalog): RFC 9727 linkset of every resource above and the one endpoint below.
- [/api/apply](${site}/api/apply): submit a subject for verification. GET -> 405. Empty POST -> 400. Non-JSON -> 415.
- POST /api/apply is limited per IP at the edge (5 per 10 s): over the limit the edge answers 429 with an HTML body, not JSON; wait ten seconds and retry.
- \`GET /api/apply/<id>\` -> state of one request, by its id (the id POST /api/apply returned; never the contact).
`;
}

/** llms-full.txt: a second RENDER of the same `entries` input llms.txt is built from, not a
 *  second copy of the map (Fable's ruling on this file). The laziest admissible version is a
 *  concatenation of outputs this generator already produces - llms.txt itself, plus the same
 *  RFC 9727 linkset `buildApiCatalog` already builds, serialized - rather than hand-written
 *  "expanded content" no checker has asked for yet. */
export function buildLlmsFullTxt(entries, site = SITE, templates = []) {
  const catalog = buildApiCatalog(entries, site);
  return `${buildLlmsTxt(entries, site, templates)}
## Full API catalog (RFC 9727 linkset, machine-readable)

\`\`\`json
${JSON.stringify(catalog, null, 2)}
\`\`\`
`;
}

/** ARD (Agentic Resource Discovery) manifest served at /.well-known/ai-catalog.json. A third
 *  render of the same `entries` input, not a third copy: every entry's `url` points at a document
 *  this generator (or the site's one real endpoint) already serves, and no entry ever carries
 *  `data` - inlining a copy here would be exactly the second copy LAW #ONE-PLACE forbids.
 *
 *  representativeQueries are phrased about OPERATIONS, never about a company's own autonomy level
 *  (ABI-2-3): the level this project assigns belongs to one operation, not to the business that
 *  runs it, and a query implying otherwise would make the catalog itself the kind of overclaim
 *  this project marks other subjects down for. */
export function buildAiCatalog(entries, site = SITE) {
  const host = { displayName: "Provek", url: site };

  const registryEntry = {
    identifier: "urn:air:provek.dev:registry:subjects",
    displayName: "Provek registry",
    type: "application/json",
    url: `${site}/data/registry.json`,
    representativeQueries: [
      "Which AI-run businesses are in the Provek registry?",
      "What evidence backs subject X's verification?",
      "Which subjects applied to Provek and what was established?",
    ],
  };

  const passportItems = entries.map(({ slug, subjectId }) => ({
    identifier: `urn:air:provek.dev:passport:${slug}`,
    displayName: `Autonomy passport: ${subjectId}`,
    type: "application/json",
    url: `${site}/data/passports/${slug}.json`,
    representativeQueries: [
      `Which operations of ${subjectId} are verified autonomous, and at what level?`,
      `What is the autonomy passport of ${subjectId}?`,
      `What evidence supports each operation score for ${subjectId}?`,
    ],
  }));

  const applyEntry = {
    identifier: "urn:air:provek.dev:intake:apply",
    displayName: "Apply for verification",
    type: "text/plain",
    url: `${site}/api/apply`,
    representativeQueries: [
      "How does an AI-run business apply for Provek verification?",
      "Where does an agent submit a subject to Provek?",
    ],
  };

  return {
    specVersion: "1.0",
    host,
    entries: [registryEntry, ...passportItems, applyEntry],
  };
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
  const templates = templateEntries();
  process.stdout.write(JSON.stringify({
    registrySubjectIds,
    passportIds: entries.map((e) => e.slug),
    templateSlugs: templates.map((t) => t.slug),
    apiCatalog: buildApiCatalog(entries, site),
    llmsTxt: buildLlmsTxt(entries, site, templates),
    llmsFullTxt: buildLlmsFullTxt(entries, site, templates),
    aiCatalog: buildAiCatalog(entries, site),
    agentSkillsIndex: buildAgentSkillsIndex(templates, site),
  }));
}
