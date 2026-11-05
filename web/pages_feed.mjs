/**
 * /feed/pages.json and the article-only markdown copy of the method notes and the build guides
 * (T-WB-06, CCH-MEDIUM-01). The sales press lane reads the feed to decide which pages it may offer
 * as Medium mirrors, and reads `<page url>` with `Accept: text/markdown` for the body to mirror.
 *
 * ONE INPUT, THREE OUTPUTS. Each article is one `{ markdown, html }` pair derived from the same
 * source (a note's `web/notes/src/*.md` body, a template's `SKILL.md` sections): the markdown is
 * the copy a mirror publishes, the html is what `scripts/style-lint.py` reads, and the feed row
 * carries the lint verdict. Nothing is typed by hand, so the copy, the verdict and the word count
 * cannot describe different texts.
 *
 * WHAT THE COPY CONTAINS: the title as `# `, then the body headings and paragraphs. NOT the
 * breadcrumb, the FAQ, the "where each statement comes from" list, the provenance line, the
 * dry-run line or the copy buttons: those are page chrome, and a mirror that carried them would
 * publish our navigation under somebody else's byline. Figures are drawn SVG and have no markdown
 * form, so they are dropped, never replaced by a guess.
 *
 * `medium_eligible` IS THE STYLE-LINT VERDICT AND NOTHING ELSE. If the linter cannot run (no
 * python3, a crash, unparseable output) the build FAILS: an eligibility that defaulted to false
 * would read as "measured, and not eligible", which is the invariant-1 defect (`not_measured` is
 * not a zero), and one that defaulted to true would publish unlinted prose.
 *
 * STANDALONE: `node pages_feed.mjs` prints `{ feed, markdown }` as JSON (no site build needed), so
 * a test can check the rendering without paying for vite/tsc/ssr.
 */
import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadNotes, renderBody } from "./notes/emit.mjs";
import { loadTemplates } from "../templates/emit.mjs";

export const SITE = "https://provek.dev";
export const FEED_MAX = 200;
export const STYLE_LINT = new URL("../scripts/style-lint.py", import.meta.url).pathname;

const esc = (s) => String(s).replace(/[<>&]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;" })[c]);

/** Relative links in a body become absolute: the copy is read on another site. */
function absolutise(md, site) {
  return md.replace(/\]\((\/[^)\s]*)\)/g, (_, path) => `](${site}${path})`);
}

/** A note body without its `{{figure:...}}` blocks (drawn SVG, no markdown form). */
function noteMarkdownBody(body) {
  return body.split(/\n{2,}/)
    .filter((b) => !/^\{\{figure:[a-z0-9-]+\}\}$/.test(b.trim()))
    .join("\n\n").trim();
}

export function wordCount(md) {
  return md.split(/\s+/).filter(Boolean).length;
}

/** Notes and build guides as `{ route, title, type, date_published, date_modified, markdown, html }`. */
export function collectArticles({ notes = loadNotes(), templates = loadTemplates(), site = SITE } = {}) {
  const out = [];
  for (const n of notes) {
    const md = absolutise(noteMarkdownBody(n.body), site);
    out.push({
      route: `/method/notes/${n.front.slug}/`,
      title: n.front.h1,
      type: "learn",
      date_published: n.date_published,
      date_modified: n.date_modified,
      markdown: `# ${n.front.h1}\n\n${md}\n`,
      html: `<h1>${esc(n.front.h1)}</h1>\n${renderBody(noteMarkdownBody(n.body))}`,
    });
  }
  for (const t of templates) {
    const md = t.sections.map((s) => `## ${s.heading}\n\n${s.text}`).join("\n\n");
    out.push({
      route: `/build/${t.slug}/`,
      title: t.title,
      type: "how-to",
      date_published: t.datePublished,
      date_modified: t.dateModified,
      markdown: `# ${t.title}\n\n${absolutise(md, site)}\n`,
      html: `<h1>${esc(t.title)}</h1>\n`
        + t.sections.map((s) => `<h2>${esc(s.heading)}</h2>\n${s.html}`).join("\n"),
    });
  }
  return out;
}

/** The verdict of `scripts/style-lint.py` on each html body: `Map<index, boolean>`. Throws when the
 *  linter did not give an answer - see the header. */
export function styleVerdicts(htmls, lintPath = STYLE_LINT) {
  const dir = mkdtempSync(join(tmpdir(), "pages-feed-"));
  try {
    const files = htmls.map((h, i) => {
      const f = join(dir, `${i}.html`);
      writeFileSync(f, h, "utf8");
      return f;
    });
    const r = spawnSync("python3", ["-I", lintPath, "--json", ...files], { encoding: "utf8", timeout: 60000 });
    // Exit 0 = every page GREEN, 1 = at least one RED; anything else is the linter not answering.
    if (r.error || (r.status !== 0 && r.status !== 1))
      throw new Error(`style-lint did not run: status ${r.status} ${r.error ?? ""} ${r.stderr ?? ""}`);
    let report;
    try { report = JSON.parse(r.stdout); } catch (e) {
      throw new Error(`style-lint output did not parse: ${e.message}`);
    }
    return files.map((f) => {
      const res = report[f];
      if (!res || typeof res.green !== "boolean")
        throw new Error(`style-lint reported nothing for ${f}`);
      return res.green;
    });
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

/** The feed rows, newest `date_published` first, at most FEED_MAX. `verdicts[i]` is for
 *  `articles[i]`. */
export function buildFeed(articles, verdicts, site = SITE) {
  const rows = articles.map((a, i) => ({
    url: `${site}${a.route}`,
    title: a.title,
    type: a.type,
    date_published: a.date_published,
    date_modified: a.date_modified,
    words: wordCount(a.markdown),
    medium_eligible: verdicts[i],
  }));
  rows.sort((x, y) =>
    y.date_published.localeCompare(x.date_published)
    || y.date_modified.localeCompare(x.date_modified)
    || x.url.localeCompare(y.url));
  return rows.slice(0, FEED_MAX);
}

/** Everything the build needs: the feed and `route -> markdown` for each article page. */
export function buildPagesArtefacts(opts = {}) {
  const articles = collectArticles(opts);
  const verdicts = articles.length ? styleVerdicts(articles.map((a) => a.html)) : [];
  return {
    feed: buildFeed(articles, verdicts, opts.site ?? SITE),
    markdown: Object.fromEntries(articles.map((a) => [a.route, a.markdown])),
  };
}

const isMain = process.argv[1] && process.argv[1].endsWith("pages_feed.mjs");
if (isMain) process.stdout.write(JSON.stringify(buildPagesArtefacts()));
