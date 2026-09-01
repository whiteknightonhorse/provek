/** Recompute one derived sibling from its own rendered page, exactly as `prerender.mjs` does, and
 *  print it. The gate compares this to the file on disk; any divergence means the sibling was
 *  hand-edited or produced by something other than the converter. Kept beside the tests rather than
 *  inside them so the recomputation runs the REAL module, not a python paraphrase of it. */
import { readFileSync } from "node:fs";
import { join, basename } from "node:path";
import { pageMarkdown } from "../web/html_to_markdown.mjs";
import { SITE } from "../web/discovery.mjs";

const dir = process.argv[2];
const html = readFileSync(join(dir, "index.html"), "utf8");
const distIdx = dir.indexOf("dist");
const rel = dir.slice(distIdx + 5);
const route = "/" + (rel ? `${rel}/` : "");
const title = (html.match(/<title>([\s\S]*?)<\/title>/i) || [, route])[1]
  .replace(/\s*[-–—]\s*Provek\s*$/, "").trim();
const description = (html.match(/<meta name="description" content="([^"]*)"/i) || [, ""])[1];
process.stdout.write(pageMarkdown(html, { title, description, site: SITE, route }));
