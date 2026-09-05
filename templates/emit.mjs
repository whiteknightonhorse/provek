/**
 * AI agent templates: deterministic emit. NO MODEL IS CALLED HERE, and no network is reached -
 * the same discipline `web/notes/emit.mjs` holds itself to, for the same reason: a build that
 * depends on a network and a token this host happens to hold is not reproducible from a clone
 * (D-18's own reasoning, restated for this generator).
 *
 * WHAT THIS FILE DOES. Reads every `templates/<slug>/SKILL.md`, validates its frontmatter and its
 * fixed body-section order against `templates/SCHEMA.md`'s normative contract, refuses to publish
 * a template with a missing or mismatched witnessed-dry-run record (`LAW-TEMPLATE-WAS-RUN`,
 * `evidence/TEMPLATE-RUN-<slug>.json`), and hands back one plain object per template: its parsed
 * frontmatter fields, its body sections rendered to small HTML fragments (for the page's
 * progressive-disclosure `<details>` blocks), the raw file bytes verbatim (for the `<pre>` and
 * for the machine-readable sibling served at `/build/<slug>/SKILL.md`), and the one computed
 * figure this surface is allowed to show: `Dry run · <date> · <tool> · <outcome>`. Also attaches
 * `faq`: three {q, a} pairs read from `templates/faq.json`, the fixed questions matched against
 * `FAQ_QUESTIONS` by position - site content about a template, kept OUTSIDE `SKILL.md` on purpose,
 * so editing an answer never touches a body a witnessed dry run is keyed to.
 *
 * WHAT THIS FILE REFUSES. A template whose `name` does not equal its own directory; a body whose
 * `##` headings are not exactly the thirteen sections in the fixed order `SCHEMA.md` requires, in
 * that order; a template with no `evidence/TEMPLATE-RUN-<slug>.json`, or one whose `body_sha256`
 * no longer matches the current file (LAW-TEMPLATE-WAS-RUN's "missing" and "hash mismatch"
 * states) - both refuse the build here, named separately in the thrown message rather than
 * collapsed into one generic failure, even though neither is currently reachable in a build that
 * publishes. Also a template with no `templates/faq.json` entry, or with the wrong number of
 * answers.
 *
 * THIS FILE DOES NOT CHECK LAW-TEMPLATE-NAMES-NO-INSTRUMENT. That gate is
 * `tests/test_templates_never_name_the_instrument.py`, over the same real tree, and duplicating it
 * here would be the same rule bound in two places (L-2, CLAUDE.md). A vocabulary violation is a
 * red test suite, not a build refusal at this layer.
 */
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join } from "node:path";
import { createHash } from "node:crypto";

const REPO = new URL("../", import.meta.url).pathname;
export const TEMPLATES_ROOT = join(REPO, "templates");
export const EVIDENCE_ROOT = join(REPO, "evidence");
export const MANIFEST_PATH = join(REPO, "templates", "manifest.json");
export const FAQ_PATH = join(REPO, "templates", "faq.json");

/** The three fixed questions every template's FAQPage answers, in this order (SPEC 3.7, ruling
 * section 6.3) - only the answers vary, in that template's own words. Fixed here and in
 * `templates/faq.json` itself; `loadFaq` cross-checks the two never drift apart. */
export const FAQ_QUESTIONS = [
  "What does a human still do?",
  "What do I need before I start?",
  "What happens after it runs?",
];

/** ADR-0011 section 4.2's own order. A slug not in this list (a backlog entry that should not be
 *  on the surface at all, or a mistake) sorts after every known one, alphabetically among itself -
 *  never silently first, which would misorder the grid for a reason nobody chose. */
const CANONICAL_ORDER = [
  "customer-support-agent",
  "lead-generation-agent",
  "ecommerce-operations-agent",
  "market-research-agent",
  "content-production-agent",
  "finance-operations-agent",
];

export const REQUIRED_SECTIONS = [
  "What to build",
  "Architecture",
  "Workflow",
  "Tools and APIs",
  "Credentials",
  "Memory",
  "Decision points",
  "Where a human stays in the loop",
  "Security",
  "Tests",
  "Deployment",
  "Commercial use",
  "Attribution",
];

const SLUG_RE = /^[a-z0-9]+(-[a-z0-9]+)*$/;

// --- frontmatter: a small, controlled subset of YAML, not a general parser ---------------------
//
// Sufficient for exactly the shape `SCHEMA.md` specifies: flat `key: value` lines, one nested
// `metadata:` block of flat `key: value` lines, values optionally double-quoted. A general YAML
// parser is not pulled in as a dependency for thirteen lines of controlled frontmatter.

function unquote(raw) {
  const t = raw.trim();
  if (t.length >= 2 && t.startsWith('"') && t.endsWith('"')) {
    return t.slice(1, -1).replace(/\\"/g, '"');
  }
  return t;
}

export function parseFrontmatter(fileText, slug) {
  const m = fileText.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!m) throw new Error(`templates/${slug}/SKILL.md: no YAML frontmatter fence found`);
  const [, fm, body] = m;
  const lines = fm.split("\n");
  const top = {};
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.trim() === "") { i++; continue; }
    const top_m = line.match(/^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$/);
    if (!top_m) throw new Error(`templates/${slug}/SKILL.md: unparseable frontmatter line: ${JSON.stringify(line)}`);
    const [, key, rest] = top_m;
    if (key === "metadata") {
      if (rest.trim() !== "") throw new Error(`templates/${slug}/SKILL.md: metadata: must open a nested block, not carry a value on the same line`);
      const meta = {};
      i++;
      while (i < lines.length && /^\s+\S/.test(lines[i])) {
        const meta_m = lines[i].match(/^\s+([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$/);
        if (!meta_m) throw new Error(`templates/${slug}/SKILL.md: unparseable metadata line: ${JSON.stringify(lines[i])}`);
        meta[meta_m[1]] = unquote(meta_m[2]);
        i++;
      }
      top.metadata = meta;
      continue;
    }
    top[key] = unquote(rest);
    i++;
  }
  return { frontmatter: top, body };
}

/** SCHEMA.md's normative contract, checked. Throws with every problem named at once, rather than
 * stopping at the first, so a fix does not have to be rediscovered one field at a time. */
export function validateFrontmatter(fm, slug) {
  const problems = [];
  if (fm.name !== slug) problems.push(`name (${JSON.stringify(fm.name)}) must equal the directory name (${slug})`);
  if (!SLUG_RE.test(slug) || slug.length > 64) problems.push(`slug ${slug} is not kebab-case of at most 64 characters`);
  if (!fm.description || fm.description.length === 0) problems.push("description is required");
  if (fm.description && fm.description.length > 1024) problems.push(`description is ${fm.description.length} chars, over the 1024 limit`);
  if (!fm.license) problems.push("license is required");
  if (!fm.compatibility) problems.push("compatibility is required");
  const meta = fm.metadata || {};
  for (const k of ["business_operation", "for", "human_remains_for", "requires"]) {
    if (!meta[k]) problems.push(`metadata.${k} is required`);
  }
  if (problems.length) {
    throw new Error(`templates/${slug}/SKILL.md fails SCHEMA.md:\n  - ${problems.join("\n  - ")}`);
  }
}

// --- body: fixed section order, `##` headings ---------------------------------------------------

export function parseSections(body, slug) {
  const lines = body.split("\n");
  const sections = [];
  let current = null;
  for (const line of lines) {
    const h = line.match(/^## (.+)$/);
    if (h) {
      current = { heading: h[1].trim(), lines: [] };
      sections.push(current);
    } else if (current) {
      current.lines.push(line);
    }
  }
  const headings = sections.map((s) => s.heading);
  const want = REQUIRED_SECTIONS.join(" > ");
  const got = headings.join(" > ");
  if (got !== want) {
    throw new Error(
      `templates/${slug}/SKILL.md: body sections do not match the fixed order SCHEMA.md requires.\n` +
      `  got:  ${got}\n  want: ${want}`
    );
  }
  return sections.map((s) => ({ heading: s.heading, text: s.lines.join("\n").trim() }));
}

// --- a small, controlled markdown-to-HTML renderer for one section's text ----------------------
//
// Supports exactly what a template body uses: paragraphs, bullet and numbered lists (continuation
// lines folded into the item they wrap, not a new item each), fenced code blocks, inline code and
// bold. Not a general markdown renderer - `web/notes/emit.mjs`'s renderBody() is not reused here
// because it also carries the notes corpus's own figure/table machinery, which a template body
// has no use for and which would be a second thing to keep working for no benefit (L-2 the other
// way: importing capability nothing here calls is its own kind of drift risk).

const escHtml = (s) => String(s).replace(/[<>&]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;" })[c]);

function inlineMd(s) {
  return escHtml(s)
    .replace(/`([^`]+)`/g, '<code class="font-mono text-[0.85em]">$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}

function joinItems(block, markerRe) {
  const items = [];
  for (const raw of block.split("\n")) {
    if (markerRe.test(raw)) {
      items.push(raw.replace(markerRe, "").trim());
    } else if (items.length && raw.trim() !== "") {
      items[items.length - 1] += " " + raw.trim();
    }
  }
  return items;
}

export function sectionHtml(text) {
  const out = [];
  for (const raw of text.split(/\n{2,}/)) {
    const b = raw.trim();
    if (!b) continue;
    if (b.startsWith("```")) {
      const inner = b.replace(/^```[a-zA-Z0-9]*\n?/, "").replace(/\n?```$/, "");
      out.push(`<pre class="mt-3 overflow-x-auto border border-[var(--color-line)] bg-[var(--color-paper-2)] p-3 text-xs font-mono">${escHtml(inner)}</pre>`);
    } else if (/^[-*]\s/.test(b)) {
      const items = joinItems(b, /^[-*]\s+/).map((it) => `<li>${inlineMd(it)}</li>`).join("");
      out.push(`<ul class="mt-3 list-disc pl-5 space-y-1 text-sm text-[var(--color-ink-2)]">${items}</ul>`);
    } else if (/^\d+\.\s/.test(b)) {
      const items = joinItems(b, /^\d+\.\s+/).map((it) => `<li>${inlineMd(it)}</li>`).join("");
      out.push(`<ol class="mt-3 list-decimal pl-5 space-y-1 text-sm text-[var(--color-ink-2)]">${items}</ol>`);
    } else {
      const para = b.split("\n").map((l) => l.trim()).join(" ");
      out.push(`<p class="mt-3 text-sm text-[var(--color-ink-2)]">${inlineMd(para)}</p>`);
    }
  }
  return out.join("\n");
}

// --- the witnessed dry run, LAW-TEMPLATE-WAS-RUN ------------------------------------------------

export function bodySha256(fileBytes) {
  return createHash("sha256").update(fileBytes).digest("hex");
}

function loadRunRecord(slug, fileBytes, evidenceRoot) {
  const recordPath = join(evidenceRoot, `TEMPLATE-RUN-${slug}.json`);
  if (!existsSync(recordPath)) {
    throw new Error(
      `templates/${slug}: no witnessed dry run at evidence/TEMPLATE-RUN-${slug}.json ` +
      `(LAW-TEMPLATE-WAS-RUN, state: missing_record) - not publishable`
    );
  }
  const record = JSON.parse(readFileSync(recordPath, "utf8"));
  const currentHash = bodySha256(fileBytes);
  if (record.body_sha256 !== currentHash) {
    throw new Error(
      `templates/${slug}: evidence/TEMPLATE-RUN-${slug}.json's body_sha256 (${record.body_sha256}) ` +
      `does not match the current SKILL.md (${currentHash}) (LAW-TEMPLATE-WAS-RUN, state: ` +
      `hash_mismatch) - the dry run predates the current revision and is not publishable as fresh`
    );
  }
  return record;
}

const titleCase = (slug) => slug.split("-").map((w) => w[0].toUpperCase() + w.slice(1)).join(" ");

/** `lastmod`/`dateModified` are pinned to this manifest, never to the build clock (the same
 * discipline `web/notes/manifest.json` holds itself to) - a rebuild that touches nothing must not
 * tell every crawler that every template changed today. A slug missing from the manifest, or
 * whose recorded `body_sha256` no longer matches the file, fails the build rather than silently
 * falling back to "today": a stale pin is a worse lie than no page at all. */
function loadManifest(manifestPath) {
  if (!existsSync(manifestPath)) throw new Error(`templates/manifest.json is missing`);
  return JSON.parse(readFileSync(manifestPath, "utf8")).templates ?? {};
}

/** `templates/faq.json`'s per-slug entries, validated against `FAQ_QUESTIONS` - three answers,
 * matched to the fixed questions by position, never a template supplying its own question text
 * (the three questions are the site's own, not the artefact's - SPEC 3.7). A slug with no entry,
 * or with a wrong count, fails the build the same way a missing dry-run record does: a page
 * silently missing its FAQPage block is exactly the kind of drift this project's own doctrine
 * refuses to let stand unnoticed. */
function loadFaq(faqPath) {
  if (!existsSync(faqPath)) throw new Error(`templates/faq.json is missing`);
  const doc = JSON.parse(readFileSync(faqPath, "utf8"));
  return doc.templates ?? {};
}

function faqFor(slug, faqData) {
  const answers = faqData[slug];
  if (!answers) throw new Error(`templates/faq.json carries no FAQ entry for ${slug}`);
  if (answers.length !== FAQ_QUESTIONS.length) {
    throw new Error(
      `templates/faq.json's entry for ${slug} has ${answers.length} answers, ` +
      `expected ${FAQ_QUESTIONS.length} (one per fixed question)`
    );
  }
  return FAQ_QUESTIONS.map((q, i) => ({ q, a: answers[i] }));
}

/** One template, fully loaded and validated, or a thrown Error naming exactly what failed. */
function loadOne(slug, templatesRoot, evidenceRoot, manifest, faqData) {
  const dir = join(templatesRoot, slug);
  const skillPath = join(dir, "SKILL.md");
  const fileBytes = readFileSync(skillPath);
  const fileText = fileBytes.toString("utf8");

  const { frontmatter, body } = parseFrontmatter(fileText, slug);
  validateFrontmatter(frontmatter, slug);
  const sections = parseSections(body, slug).map((s) => ({ ...s, html: sectionHtml(s.text) }));
  const record = loadRunRecord(slug, fileBytes, evidenceRoot);

  const hash = bodySha256(fileBytes);
  const entry = manifest[slug];
  if (!entry) throw new Error(`templates/manifest.json carries no entry for ${slug}`);
  if (entry.body_sha256 !== hash) {
    throw new Error(
      `templates/manifest.json's body_sha256 for ${slug} (${entry.body_sha256}) does not match ` +
      `the current SKILL.md (${hash}) - bump date_modified and the recorded hash together`
    );
  }

  return {
    slug,
    title: titleCase(slug),
    description: frontmatter.description,
    license: frontmatter.license,
    compatibility: frontmatter.compatibility,
    businessOperation: frontmatter.metadata.business_operation,
    forWhom: frontmatter.metadata.for,
    humanRemainsFor: frontmatter.metadata.human_remains_for,
    requires: frontmatter.metadata.requires,
    derivedFrom: frontmatter.metadata.derived_from ?? null,
    sections,
    raw: fileText,
    bodySha256: hash,
    datePublished: entry.date_published,
    dateModified: entry.date_modified,
    faq: faqFor(slug, faqData),
    dryRun: {
      date: record.run_at.slice(0, 10),
      tool: record.tool,
      outcome: record.outcome,
      line: `Dry run · ${record.run_at.slice(0, 10)} · ${record.tool} · ${record.outcome}`,
    },
  };
}

/** Every admitted template, in ADR-0011's canonical order. Throws (refuses the build) rather than
 * skipping a template that fails validation or carries no witnessed dry run - a page silently
 * missing one template is a drift nobody would notice; a red build is not. */
export function loadTemplates(templatesRoot = TEMPLATES_ROOT, evidenceRoot = EVIDENCE_ROOT, manifestPath = MANIFEST_PATH, faqPath = FAQ_PATH) {
  if (!existsSync(templatesRoot)) return [];
  const slugs = readdirSync(templatesRoot, { withFileTypes: true })
    .filter((e) => e.isDirectory() && existsSync(join(templatesRoot, e.name, "SKILL.md")))
    .map((e) => e.name)
    .sort((a, b) => {
      const ia = CANONICAL_ORDER.indexOf(a), ib = CANONICAL_ORDER.indexOf(b);
      if (ia !== -1 && ib !== -1) return ia - ib;
      if (ia !== -1) return -1;
      if (ib !== -1) return 1;
      return a.localeCompare(b);
    });
  if (slugs.length === 0) return [];
  const manifest = loadManifest(manifestPath);
  const faqData = loadFaq(faqPath);
  return slugs.map((slug) => loadOne(slug, templatesRoot, evidenceRoot, manifest, faqData));
}
