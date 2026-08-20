/**
 * Static emit. Writes one real HTML file per route, plus 404.html, sitemap.xml and robots.txt.
 *
 * WHY THIS EXISTS. Before 2026-08-20 the whole site was one URL: routing was by hash, so a crawler
 * saw nothing after the `#`, and the raw HTML body contained zero characters of text. The registry
 * and all eight passports had no address anyone could index, cite, or archive. D-01 requires a
 * passport to stand alone and be readable a year later; a fragment behind an empty body cannot be
 * linked from a due-diligence memo. Answer engines make it sharper still - most fetch HTML and run
 * no JavaScript, so the site was invisible to them however good the content was.
 *
 * Structured data is deliberately conservative. A passport is a `Report` - a document stating
 * findings - never a `Review` or anything carrying `ratingValue`, because rating semantics are
 * endorsement and would encode into metadata the exact misreading D-02 exists to prevent. An
 * unmeasured operation is emitted as a named PropertyValue with the string `not_measured` and its
 * reason: no schema has a slot for absence, and inventing a zero would be the founding defect.
 */
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";

const DIST = "dist";
const SITE = "https://provek.dev";
const shell = readFileSync(join(DIST, "index.html"), "utf8");
const { renderRoute, TITLES } = await import("./dist-ssr/entry-server.js");

const registry = JSON.parse(readFileSync("public/data/registry.json", "utf8"));
const passports = Object.fromEntries(
  readdirSync("public/data/passports")
    .filter((f) => f.endsWith(".json"))
    .map((f) => {
      const d = JSON.parse(readFileSync(join("public/data/passports", f), "utf8"));
      return [f.replace(/\.json$/, ""), d.passport];
    }),
);

const slug = (id) => id.replace(/[:/]/g, "_");
const esc = (s) => String(s).replace(/[<>&"]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;" })[c]);

function ldOrganization() {
  return {
    "@context": "https://schema.org", "@type": "Organization",
    name: "Provek", url: SITE + "/",
    description: "Verification of how much of a business runs without a human in the loop, from evidence.",
  };
}

function ldRegistry() {
  return {
    "@context": "https://schema.org", "@type": "Dataset",
    name: "Provek registry",
    description: "Every business that has been measured, with the evidence behind each verdict.",
    url: SITE + "/registry/",
    dateModified: registry.generated_at,
    creator: { "@type": "Organization", name: "Provek" },
    distribution: [{ "@type": "DataDownload", encodingFormat: "application/json",
                     contentUrl: SITE + "/data/registry.json" }],
  };
}

function ldPassport(p) {
  const ops = p.verified.operations.map((o) => ({
    "@type": "PropertyValue",
    name: o.operation,
    value: o.measured ? o.level : "not_measured",
    description: o.measured
      ? `confidence: ${o.confidence}${o.limiters_applied.length ? "; limiters: " + o.limiters_applied.join(", ") : ""}`
      : `${o.level}: no level was established for this operation`,
  }));
  const projection = {
    "@type": "PropertyValue",
    name: "autonomy_projection",
    value: p.verified.projection === null ? "not_measured" : p.verified.projection,
    description: p.verified.projection === null
      ? `${p.verified.projection_absent_reason}: no projection was established`
      : "Measures autonomy only. Not reliability, decision quality, profitability, or the presence of an accountable party.",
  };
  return {
    "@context": "https://schema.org", "@type": "Report",
    name: `Autonomy passport: ${p.subject_id}`,
    url: `${SITE}/p/${slug(p.subject_id)}/`,
    datePublished: p.issued_at,
    expires: p.valid_until,
    inLanguage: "en",
    publisher: { "@type": "Organization", name: "Provek" },
    author: { "@type": "Organization", name: "Provek" },
    about: { "@type": "SoftwareSourceCode", name: p.subject_id },
    isBasedOn: `${SITE}/data/passports/${slug(p.subject_id)}.json`,
    description:
      `${p.verifier_affiliation === "same_owner"
        ? "AFFILIATED VERIFICATION: the subject and the verifier's owner are the same party. "
        : ""}` +
      `Status ${p.status}. Evidence read through the ${p.access_channel} channel. ` +
      "The score measures autonomy only.",
    additionalProperty: [projection, ...ops],
  };
}

function page(route, title, description, ld, data) {
  const html = renderRoute(route, registry, data?.passport ?? null);
  let out = shell
    .replace(/<title>[^<]*<\/title>/, `<title>${esc(title)}</title>`)
    .replace(/(<meta name="description" content=")[^"]*(")/, `$1${esc(description)}$2`)
    .replace(/(<link rel="canonical" href=")[^"]*(")/, `$1${SITE}${route}$2`)
    .replace(/(<meta property="og:url" content=")[^"]*(")/, `$1${SITE}${route}$2`)
    .replace(/(<meta property="og:title" content=")[^"]*(")/, `$1${esc(title)}$2`)
    .replace(/(<meta property="og:description" content=")[^"]*(")/, `$1${esc(description)}$2`);

  const head = [
    `<script type="application/ld+json">${JSON.stringify(ld)}</script>`,
    data?.passport
      ? `<link rel="alternate" type="application/json" href="/data/passports/${slug(data.passport.subject_id)}.json">`
      : route === "/registry/"
        ? `<link rel="alternate" type="application/json" href="/data/registry.json">`
        : "",
  ].join("\n    ");

  const inline = `<script>window.__PROVEK__=${JSON.stringify({
    registry,
    ...(data?.passport ? { passport: data.passport } : {}),
  }).replace(/</g, "\\u003c")}</script>`;

  out = out.replace("</head>", `    ${head}\n  </head>`);
  out = out.replace('<div id="root"></div>', `<div id="root">${html}</div>\n    ${inline}`);
  return out;
}

function write(route, html) {
  const file = join(DIST, route === "/" ? "index.html" : join(route, "index.html"));
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, html);
  return route;
}

const written = [];
written.push(write("/", page("/", TITLES["/"],
  "Per business operation, how much of a company runs without a human in the loop - with the evidence behind every number, including what could not be measured.",
  ldOrganization())));
written.push(write("/registry/", page("/registry/", TITLES["/registry/"],
  `Every business that has been measured, with the evidence behind each verdict. ${registry.count} records.`,
  ldRegistry())));
written.push(write("/method/", page("/method/", TITLES["/method/"],
  "How a level is assigned to an operation, how evidence is classed by forgery cost, and what the score does not measure.",
  ldOrganization())));
written.push(write("/apply/", page("/apply/", TITLES["/apply/"],
  "Request verification. Free at this stage. Public repositories only.",
  ldOrganization())));
// The description is the page's refusal, not its subject. A summary reading "commission work from a
// verified agent" would travel into search results and social cards with the capability intact and
// the refusal left behind on the page - and the summary is what most readers will ever see.
written.push(write("/phase-2/", page("/phase-2/", TITLES["/phase-2/"],
  "Funding tasks are specified and NOT in service: none can be created, none commissioned, no application taken, and no date is given. What the specification requires of phase 2.",
  ldOrganization())));

for (const row of registry.subjects) {
  const s = slug(row.subject_id);
  const p = passports[s];
  if (!p) continue;
  const verdict = p.verified.projection === null
    ? `not measured (${p.verified.projection_absent_reason})`
    : `${p.verified.projection} of 100`;
  written.push(write(`/p/${s}/`, page(`/p/${s}/`,
    `${p.subject_id} - Provek`,
    `Autonomy passport for ${p.subject_id}. Projection ${verdict}. Issued ${p.issued_at.slice(0, 10)}, valid until ${p.valid_until.slice(0, 10)}.`,
    ldPassport(p), { passport: p })));
}

// A REAL 404. Its presence switches off Cloudflare Pages' SPA fallback, which until now answered
// 200 with the app shell for every nonexistent path - including /sitemap.xml. A positive answer
// where the truthful answer is absence is this product's own thesis inverted.
writeFileSync(join(DIST, "404.html"), page("/__not_found__/", "No such page - Provek",
  "Nothing is served at this address.", ldOrganization()));

const urls = written.map((route) => {
  const p = route.startsWith("/p/") ? passports[route.slice(3, -1)] : null;
  const lastmod = (p ? p.issued_at : registry.generated_at).slice(0, 10);
  return `  <url>\n    <loc>${SITE}${route}</loc>\n    <lastmod>${lastmod}</lastmod>\n  </url>`;
}).join("\n");
writeFileSync(join(DIST, "sitemap.xml"),
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`);

writeFileSync(join(DIST, "robots.txt"),
  "# The registry and every passport are meant to be found and quoted.\n" +
  "User-agent: *\nAllow: /\n\n" +
  `Sitemap: ${SITE}/sitemap.xml\n`);

console.log(`prerendered ${written.length} routes + 404 + sitemap`);
for (const r of written) console.log("   ", r);
