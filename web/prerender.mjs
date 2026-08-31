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
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { loadNotes, noteArticle, notesIndexArticle, noteLd } from "./notes/emit.mjs";

const DIST = "dist";
const SITE = "https://provek.dev";
const shellRaw = readFileSync(join(DIST, "index.html"), "utf8");

/** THE FONTS ARE PRELOADED BECAUSE THE FIRST LONG PAGE ON THIS SITE MEASURED THE COST OF NOT
 *  DOING IT. `@fontsource` ships `font-display: swap`, and the faces are referenced from inside the
 *  stylesheet, so a browser cannot discover them until the CSS has been fetched and parsed. Text
 *  therefore paints in the fallback and reflows when the real face arrives.
 *
 *  On the short pages that was invisible in use and nearly invisible in measurement - the landing
 *  reads CLS 0.0608. The first method note is a 5404px column of prose, where the same swap moved
 *  the whole of `<main>` and measured CLS 0.2524, which is what took Lighthouse Performance to 83
 *  against the landing's 95 on the same host in the same minute. The defect scales with how much
 *  text a page has, so it arrived with the first page that had a lot.
 *
 *  Preloading is chosen over `font-display: optional`, which also removes the shift: optional buys
 *  it by dropping the typography for the whole of a first visit, and the reader is the one who pays.
 *  A preload starts the fetch beside the stylesheet instead of after it, so the face is usually
 *  there for the first paint and there is nothing to swap.
 *
 *  Only the three faces the measurement named are preloaded. Preloading all five would spend
 *  bandwidth ahead of first paint on faces that no page uses above the fold, which is the same
 *  mistake in the other direction. `crossorigin` is not optional: a font preload without it is
 *  fetched in a different mode from the CSS request and the file is downloaded TWICE. */
function fontPreloads(shellHtml) {
  const hrefs = [];
  for (const m of shellHtml.matchAll(/href="(\/assets\/[^"]+\.css)"/g)) {
    const css = readFileSync(join(DIST, m[1]), "utf8");
    for (const f of css.matchAll(/url\((\/assets\/[^)"']+\.woff2)\)/g)) hrefs.push(f[1]);
  }
  const wanted = hrefs.filter((h) =>
    /ibm-plex-sans-latin-400/.test(h) || /ibm-plex-sans-latin-600/.test(h)
    || /ibm-plex-mono-latin-400/.test(h));
  // A BUILD THAT FINDS NO FONTS MUST NOT EMIT A PAGE THAT SILENTLY SHIFTS AGAIN. The filenames are
  // content-hashed and the package could rename a face, so this is exactly the shape that would
  // otherwise degrade to "no preloads, everything still builds, the score quietly returns to 83".
  if (wanted.length !== 3)
    throw new Error(
      `prerender: expected 3 above-the-fold woff2 faces to preload, found ${wanted.length} `
      + `(${wanted.join(", ") || "none"}). The stylesheet's font URLs changed shape.`);
  return wanted.map((h) =>
    `<link rel="preload" as="font" type="font/woff2" href="${h}" crossorigin>`).join("\n    ");
}

const shell = shellRaw.replace("</head>", `  ${fontPreloads(shellRaw)}\n  </head>`);
const { renderRoute, renderStatic, TITLES, PRERENDER_ROUTE } = await import("./dist-ssr/entry-server.js");

/** The same shell with the application's module script removed.
 *
 * A method note is prose. Hydrating it would download the router, the registry loader and the
 * passport loader to take over a document that is already finished, and would then have to be
 * taught every note route to avoid painting "No such page" over one. Stripping the entry here is
 * what keeps the open item in DESIGN.md ("222 KB of JavaScript for five static routes") from
 * growing with every note. The stylesheet stays - the design tokens are not optional - and so does
 * the measurement snippet ratified in D-14, because switching it off on some pages and not others
 * would make the reading say something nobody decided.
 */
const staticShell = shell
  .replace(/<script type="module"[^>]*><\/script>\s*/g, "")
  .replace(/<link rel="modulepreload"[^>]*>\s*/g, "");

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

/** The registry's own sentence, in the words the visible page uses.
 *
 * It read "every business that has been measured" while four of eight rows carry no measurement at
 * all - their sources answer no reader without a credential. The visible page had already been
 * corrected; the description, the og tags and this Dataset block had not, so the machine channel
 * went on reporting `unreadable` as `measured` to every crawler that asked. That is invariant 1
 * inverted in the one copy nobody re-reads, and L-2's shape exactly: a rule repealed in one place
 * survives in another. Both channels are now computed here, from the same field the table renders
 * (`projection_absent_reason === "unreadable"`), so the count cannot drift from the rows again.
 *
 * A THIRD COPY OF THE OLD SENTENCE SURVIVES, DELIBERATELY, at `web-1.0/src/pages/Registry.tsx:28`.
 * That tree is the frozen phase-2 rollback point and its own `FROZEN.md` says not to edit it; a
 * baseline that gets corrected is no longer a baseline. It is named here instead, because L-2 is
 * about knowing where every copy is, not about there being one: anybody rolling back to `web-1.0`
 * restores this defect along with the layout, and now finds that out from the file they are
 * rolling forward to.
 */
const unreadable = registry.subjects.filter(
  (s) => s.projection_absent_reason === "unreadable").length;
const REGISTRY_SENTENCE =
  "Every business submitted to the method, what could be established about each, and the evidence "
  + `behind it. ${registry.count} records, of which ${unreadable} could not be measured at all.`;

function ldRegistry() {
  return {
    "@context": "https://schema.org", "@type": "Dataset",
    name: "Provek registry",
    description: REGISTRY_SENTENCE,
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

/** Every per-page field in the head, rewritten in ONE place.
 *
 * There were two copies of this list - one in `page()`, one in `staticPage()` - and the head has
 * three channels saying the same thing to three different readers: `description` for search,
 * `og:*` for link previews, `twitter:*` for cards. Keeping them in step by hand is how the registry
 * page came to tell crawlers "every business that has been measured" for as long as it did: the
 * visible prose was corrected, `og:description` was missed, and nothing connected them.
 *
 * `twitter:title` and `twitter:description` were not rewritten AT ALL until now - every one of the
 * fourteen emitted documents carried the landing page's card, so sharing a passport advertised the
 * front page. It was not a false statement, only a wrong one, which is why it survived a review
 * that was hunting for false ones.
 *
 * One list, one loop. A channel added to `index.html` and not to this array is now the only way to
 * get an unrewritten head, instead of one of three ways.
 */
function head(shellHtml, route, title, description) {
  const t = esc(title), d = esc(description), url = SITE + route;
  return [
    [/<title>[^<]*<\/title>/, `<title>${t}</title>`],
    [/(<meta name="description" content=")[^"]*(")/, `$1${d}$2`],
    [/(<link rel="canonical" href=")[^"]*(")/, `$1${url}$2`],
    [/(<meta property="og:url" content=")[^"]*(")/, `$1${url}$2`],
    [/(<meta property="og:title" content=")[^"]*(")/, `$1${t}$2`],
    [/(<meta property="og:description" content=")[^"]*(")/, `$1${d}$2`],
    [/(<meta name="twitter:title" content=")[^"]*(")/, `$1${t}$2`],
    [/(<meta name="twitter:description" content=")[^"]*(")/, `$1${d}$2`],
  ].reduce((acc, [re, to]) => acc.replace(re, to), shellHtml);
}

function page(route, title, description, ld, data) {
  const html = renderRoute(route, registry, data?.passport ?? null);
  let out = head(shell, route, title, description);

  const blocks = [
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

  out = out.replace("</head>", `    ${blocks}\n  </head>`);
  out = out.replace('<div id="root"></div>', `<div id="root">${html}</div>\n    ${inline}`);
  return out;
}

/** A page with no application behind it: one document, many JSON-LD blocks, no bootstrap data. */
function staticPage(route, title, description, ld, html) {
  let out = head(staticShell, route, title, description);
  const blocks = (Array.isArray(ld) ? ld : [ld])
    .map((x) => `<script type="application/ld+json">${JSON.stringify(x)}</script>`).join("\n    ");
  out = out.replace("</head>", `    ${blocks}\n  </head>`);
  return out.replace('<div id="root"></div>', `<div id="root">${renderStatic(route, html)}</div>`);
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
  REGISTRY_SENTENCE,
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

// METHOD NOTES. Descriptive notes on the published methodology (SPEC 3.6, D-18) - never teaching,
// which ADR-0009 rules off this surface. `loadNotes()` throws rather than emitting a note whose key
// the keyword base never returned, whose address resolves to nothing, or that is missing from the
// freshness manifest; a build that cannot prove a note's provenance does not produce the note.
const notes = loadNotes();
const noteLastmod = new Map();
if (notes.length) {
  const indexRoute = "/method/notes/";
  written.push(write(indexRoute, staticPage(indexRoute, "Notes on the method - Provek",
    "Descriptive notes on the published methodology: what each term measures, which absences are distinguished, and what the standard underneath does not settle.",
    { "@context": "https://schema.org", "@type": "CollectionPage", url: SITE + indexRoute,
      name: "Notes on the method", inLanguage: "en",
      isPartOf: { "@type": "WebPage", url: SITE + "/method/" },
      publisher: { "@type": "Organization", name: "Provek" } },
    notesIndexArticle(notes))));
  noteLastmod.set(indexRoute,
    notes.map((n) => n.date_modified).sort().at(-1));

  for (const n of notes) {
    const route = `/method/notes/${n.front.slug}/`;
    written.push(write(route, staticPage(route, n.front.title, n.front.description,
      noteLd(n, SITE), noteArticle(n))));
    // lastmod comes from the manifest, which moves only when the body hash moves. Taking it from
    // the build clock would tell every crawler that all three notes changed whenever any file in
    // the repository did - a freshness claim with nothing behind it.
    noteLastmod.set(route, n.date_modified);
  }
}

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
// AND IT DECLARES NO ADDRESS OF ITS OWN. `page()` writes a canonical link and an og:url from the
// route it is given, which for this document is the placeholder `/__not_found__/` - a URL that does
// not exist and that no reader asked for. A 404 that names a canonical is telling every crawler
// that the thing it failed to find lives somewhere specific; the honest header for a document that
// stands in for any missing address is no address at all. Stripped rather than parameterised,
// because this is the only page in the site with no URL of its own.
const notFound = page(PRERENDER_ROUTE, "No such page - Provek",
  "Nothing is served at this address.", ldOrganization())
  .replace(/\s*<link rel="canonical"[^>]*>/, "")
  .replace(/\s*<meta property="og:url"[^>]*>/, "");
writeFileSync(join(DIST, "404.html"), notFound);

// LASTMOD IS EMITTED ONLY WHERE A DATE WAS ACTUALLY MEASURED. AN UNMEASURED ONE IS OMITTED.
//
// Every route used to take `registry.generated_at` as its fallback, so regenerating `registry.json`
// told every crawler that `/method/`, `/apply/` and `/phase-2/` had changed - pages whose prose the
// build had not touched. That is "a rebuild manufactures freshness", which is the exact thing
// LAW-NOTES-FRESHNESS forbids, running on all thirteen shipped routes while the law itself governed
// zero notes. A law that binds only where there is nothing to check is L-6 one level up.
//
// Three routes have a real date and keep it; the rest have none and say nothing, because `<lastmod>`
// is optional in the sitemap protocol and an absent field is honest where an invented one is not.
// This is invariant 1 in a machine channel: not_measured is a state of its own, and the way to
// write it here is to leave it out rather than to default it to the build clock.
const lastmodFor = (route) => {
  const note = noteLastmod.get(route);
  if (note) return note;                                   // manifest: moves with the body hash
  if (route.startsWith("/p/")) {                           // the passport was issued on a date
    return passports[route.slice(3, -1)]?.issued_at?.slice(0, 10) ?? null;
  }
  // The landing and the registry ARE renderings of `registry.json` - their content moves when it
  // does, so its generation stamp is a measurement of them and not a guess.
  if (route === "/" || route === "/registry/") return registry.generated_at.slice(0, 10);
  return null;                                             // prose we did not date: say nothing
};

const urls = written.map((route) => {
  const lastmod = lastmodFor(route);
  const stamp = lastmod ? `\n    <lastmod>${lastmod}</lastmod>` : "";
  return `  <url>\n    <loc>${SITE}${route}</loc>${stamp}\n  </url>`;
}).join("\n");
writeFileSync(join(DIST, "sitemap.xml"),
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`);

// ROBOTS.TXT IS `public/robots.txt` PLUS THE SITEMAP LINE, and it used to be neither.
//
// This call rewrote the file with a hardcoded copy of its own, running AFTER `vite build` had
// already copied `public/robots.txt` into DIST. So the file in the repository was not the file the
// site served, and editing the source changed nothing a reader receives - measured 2026-08-31,
// when a `Content-Signal` directive added to `public/robots.txt` was silently overwritten here.
// Two spellings of one file with no gate between them: the source lost, quietly, every build.
//
// The Sitemap line stays generated because it is the only part that depends on SITE, which the
// build knows and a static file cannot. Everything else now has exactly one home. If the source
// file is missing this THROWS rather than falling back to a copy: a fallback would restore the
// very defect - a second spelling that wins whenever the first is unavailable.
const robotsSource = readFileSync("public/robots.txt", "utf8").trimEnd();  // same relative form as registry.json above
writeFileSync(join(DIST, "robots.txt"), `${robotsSource}\n\nSitemap: ${SITE}/sitemap.xml\n`);

console.log(`prerendered ${written.length} routes + 404 + sitemap`);
for (const r of written) console.log("   ", r);
