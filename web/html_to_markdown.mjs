/**
 * HTML → markdown for THIS SITE'S OWN pages, and deliberately not a general converter.
 *
 * WHY IT EXISTS. `_middleware.js` already negotiates markdown for any page route by shape, needing
 * no route list; what it could not do is answer for a page nobody wrote a builder for. Eleven of
 * nineteen routes had a sibling and the other eight fell through to HTML — including `/`, which is
 * the first address any scanner tries, which is why a site that DOES support markdown measured as
 * one that does not.
 *
 * A PER-PAGE BUILDER DOES NOT SCALE AND IS NOT WHAT WAS ASKED. `buildRegistryMarkdown` and
 * `buildPassportMarkdown` stay: they render from DATA and say things a conversion cannot, like the
 * reason behind each absence. This is the DEFAULT for every other route — derived from the rendered
 * page, so a route added tomorrow gets its markdown without anyone remembering to write one, and
 * the two renderings cannot drift because one is computed from the other.
 *
 * WHY NOT A DEPENDENCY. Turndown and friends convert arbitrary web HTML — a hard problem this
 * project does not have. The markup here is our own, emitted by our own prerenderer, and a
 * converter that meets exactly it is smaller than the configuration a general one would need. It
 * handles what our pages contain and REFUSES to guess at what they do not: an unknown block is kept
 * as its text rather than dropped, because losing a sentence silently is the failure that matters.
 */


/** Entities our own pages actually emit. Not a full table: an unknown entity stays as written,
 *  which is visibly wrong to a reader rather than silently dropped. */
const ENTITIES = {
  amp: "&", lt: "<", gt: ">", quot: '"', "#39": "'", apos: "'", nbsp: " ",
  mdash: "\u2014", ndash: "\u2013", hellip: "\u2026", rsquo: "\u2019", lsquo: "\u2018",
  ldquo: "\u201c", rdquo: "\u201d", middot: "\u00b7", times: "\u00d7", divide: "\u00f7",
  thinsp: "\u2009", check: "\u2713",
};

/** DECODING MAY NOT MANUFACTURE A TAG.
 *
 *  Stripping runs on the page's markup; decoding runs after it. So an angle bracket that arrives
 *  ESCAPED is never seen by the strip and becomes a live bracket in the published document. That
 *  is not hypothetical here: since 2026-08-31 the accountability block renders four fields read
 *  from a SUBJECT'S OWN `provek.json`. React escapes them into the page correctly - and this
 *  converter used to hand them straight back. Measured before the fix: a declaration field holding
 *  `<script>alert(1)</script>` produced exactly that, live, in `/p/<subject>/index.md`.
 *
 *  So `<` and `>` stay escaped, whichever spelling asked for them - named (`&lt;`), decimal
 *  (`&#60;`) or hex (`&#x3c;`). A markdown reader still SEES the bracket; no reader can be made to
 *  execute it. Nothing else changes: every other entity decodes as before.
 *
 *  Measured 2026-09-01: zero passports currently carry a declaration, so this closes the path
 *  before it ever carried a stranger's text rather than after.
 */
const NEVER_UNESCAPED = new Set(["<", ">"]);

function decode(s) {
  return s.replace(/&(#x?[0-9a-fA-F]+|[a-zA-Z]+);/g, (m, e) => {
    if (e[0] === "#") {
      const n = e[1] === "x" || e[1] === "X" ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10);
      if (!Number.isFinite(n)) return m;
      const ch = String.fromCodePoint(n);
      return NEVER_UNESCAPED.has(ch) ? m : ch;
    }
    if (!Object.prototype.hasOwnProperty.call(ENTITIES, e)) return m;
    return NEVER_UNESCAPED.has(ENTITIES[e]) ? m : ENTITIES[e];
  });
}

/** Repeat a rewrite until it stops changing the string.
 *
 *  A SINGLE pass is not removal. Deleting `<script>` from `<scr<script>ipt>` leaves `<script>`:
 *  the pass RECONSTRUCTS the very tag it just took out. That is what CodeQL means by "incomplete
 *  multi-character sanitization", and it stopped being theoretical here on 2026-08-31, when the
 *  accountability block began rendering fields read from a SUBJECT'S OWN `provek.json`. This
 *  converter's input is no longer only our own prerendered markup.
 *
 *  The iteration is bounded. An unbounded loop over hostile input is the other half of the same
 *  class of bug - this repository has already shipped one measured ReDoS - and 20 passes is far
 *  past anything nesting in real markup produces.
 */
function untilStable(text, rewrite, limit = 20) {
  for (let i = 0; i < limit; i += 1) {
    const next = rewrite(text);
    if (next === text) return text;
    text = next;
  }
  return text;
}

/** Everything a reader never sees is removed BEFORE any text is taken: scripts, styles, and the
 *  `sr-only` spans that exist so a screen reader hears what the eye reads. Keeping the latter would
 *  print every reason twice — the exact doubling the visible/announced pair is designed to avoid. */
function strip(html) {
  return untilStable(html, (t) => t
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/<(script|style|template)\b[^>]*>[\s\S]*?<\/\1>/gi, "")
    // DECLARED LOSS: inline SVG. Two method notes draw charts whose axis labels are `<text>` nodes
    // — subject names and level codes. Read in document order they are a word salad, not prose:
    // "cryptocardhub-defycard 257 L2 gov-auction-report" says nothing a reader can use, and a
    // markdown document that prints it would be claiming to convey a figure it cannot. Measured
    // 2026-09-01: 26 words across the two notes, all of them chart labels. The loss is named here
    // and excluded on BOTH sides of the fidelity gate, so the gate measures what this converter
    // actually promises rather than being quietly widened until it passes.
    .replace(/<svg\b[^>]*>[\s\S]*?<\/svg>/gi, "")
    .replace(/<span[^>]*\bclass="[^"]*\bsr-only\b[^"]*"[^>]*>[\s\S]*?<\/span>/gi, ""));
}

function inline(html) {
  // ADJACENT ELEMENTS ARE ADJACENT WORDS, NOT ONE WORD. `<span>…recipient</span><span>enforced…`
  // has no whitespace between the two texts, so stripping the tags glued them into
  // "recipientenforced" — measured on `/phase-2/`, where a word-level fidelity check then reported
  // "recipient" as LOST when in truth it was merged. The text was never dropped; it stopped being
  // readable, which for a document meant for machines is the same defect wearing a better mask.
  return decode(untilStable(html
    .replace(/<\/(span|a|strong|em|b|i|code)>\s*<(span|a|strong|em|b|i|code)\b/gi, "</$1> <$2")
    .replace(/<a\b[^>]*\bhref="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi,
      (m, href, text) => {
        const t = decode(untilStable(text, (x) => x.replace(/<[^>]+>/g, ""))).trim();
        return t ? `[${t}](${href})` : "";
      })
    .replace(/<(strong|b)\b[^>]*>([\s\S]*?)<\/\1>/gi, (m, _t, x) => `**${untilStable(x, (y) => y.replace(/<[^>]+>/g, "")).trim()}**`)
    .replace(/<(em|i)\b[^>]*>([\s\S]*?)<\/\1>/gi, (m, _t, x) => `*${untilStable(x, (y) => y.replace(/<[^>]+>/g, "")).trim()}*`)
    .replace(/<code\b[^>]*>([\s\S]*?)<\/code>/gi, (m, x) => "`" + untilStable(x, (y) => y.replace(/<[^>]+>/g, "")).trim() + "`")
    .replace(/<br\s*\/?>/gi, "\n"), (t) => t.replace(/<[^>]+>/g, "")))
    .replace(/[ \t\u00a0]+/g, " ")
    .trim();
}

/** The document's `<main>` when it has one — the chrome (masthead, nav, footer) repeats on every
 *  page and would drown the page's own content in a format meant to be read whole. Falls back to
 *  `<body>` rather than returning nothing: an unexpected shape must still produce the page. */
function contentOf(html) {
  const main = html.match(/<main\b[^>]*>([\s\S]*?)<\/main>/i);
  if (main) return main[1];
  const body = html.match(/<body\b[^>]*>([\s\S]*?)<\/body>/i);
  return body ? body[1] : html;
}

export function htmlToMarkdown(html) {
  const src = strip(contentOf(html));

  // LINEAR REWRITE, NOT AN ALLOWLIST SELECTION. The first version matched `h*|p|li|summary|td|th`
  // and took only what matched — while this file's own header promised "an unknown block is kept as
  // its text rather than dropped". The header was the rule; the code did the opposite, and the gap
  // was silent, which is the shape LAW #ALLOWLIST-WHAT-YOU-INSPECT names: a checker that skips what
  // it does not recognise reports success on what it cannot handle. Measured on the served pages
  // before this rewrite: `/apply` lost ~76 visible words — the `<label>`, `<span>` and `<button>`
  // text that says HOW to apply, which is the whole of that page for an agent — `/method` ~56,
  // `/phase-2` ~55.
  //
  // So known blocks are given their markdown shape IN PLACE and everything else keeps its text.
  // Nothing is selected; nothing is dropped. The fidelity gate in tests/test_markdown_negotiation.py
  // holds this to it by counting words, because a promise in a comment is not a mechanism.
  let s = src
    .replace(/<\/(p|div|section|article|header|footer|main|nav|ul|ol|table|tbody|thead|tr|details|figure|blockquote|form|fieldset)\s*>/gi, "\n\n")
    .replace(/<(h[1-6])\b[^>]*>([\s\S]*?)<\/\1>/gi, (m, tag, x) => `\n\n${"#".repeat(Number(tag[1]))} ${inline(x)}\n\n`)
    .replace(/<li\b[^>]*>([\s\S]*?)<\/li>/gi, (m, x) => `\n- ${inline(x)}`)
    .replace(/<summary\b[^>]*>([\s\S]*?)<\/summary>/gi, (m, x) => `\n\n**${inline(x)}**\n\n`)
    .replace(/<(td|th)\b[^>]*>([\s\S]*?)<\/\1>/gi, (m, tag, x) => `${inline(x)} · `)
    .replace(/<label\b[^>]*>([\s\S]*?)<\/label>/gi, (m, x) => `\n\n${inline(x)}`)
    .replace(/<button\b[^>]*>([\s\S]*?)<\/button>/gi, (m, x) => `\n\n[${inline(x)}]`)
    .replace(/<option\b[^>]*>([\s\S]*?)<\/option>/gi, (m, x) => `\n- ${inline(x)}`)
    // Definition lists carry the method's own vocabulary — `third_party_attested`, `a share of
    // revenue` — as `<dt>`/`<dd>` pairs. Without a shape of their own they merged into the
    // surrounding run and the dedup line below then ate them as repeats: measured 5 lost words on
    // `/method/` and 3 on `/phase-2/` after the allowlist was already gone.
    .replace(/<dt\b[^>]*>([\s\S]*?)<\/dt>/gi, (m, x) => `\n\n**${inline(x)}**`)
    .replace(/<dd\b[^>]*>([\s\S]*?)<\/dd>/gi, (m, x) => `\n${inline(x)}\n`)
    .replace(/<\/(dl|dt|dd)\s*>/gi, "\n");

  // Whatever tags are left are inline or unknown; `inline` turns links, emphasis and code into
  // markdown and drops the remaining markup WITHOUT dropping the text it wrapped.
  s = inline(s);

  const lines = s.split("\n").map((l) => l.replace(/[ \t ]+/g, " ").replace(/ · $/, "").trim());
  const out = [];
  for (const l of lines) {
    if (!l) { if (out.length && out[out.length - 1] !== "") out.push(""); continue; }
    if (l === out[out.length - 1]) continue;      // the same label rendered at two breakpoints
    out.push(l);
  }
  return out.join("\n").replace(/\n{3,}/g, "\n\n").trim() + "\n";
}

export function pageMarkdown(html, { title, description, site, route }) {
  const body = htmlToMarkdown(html);
  const blocks = body.split("\n\n");
  // ONE TITLE PER DOCUMENT, and it is the page's own. Emitting the shell's `<title>` above an `h1`
  // printed two headings that were not even the same words — measured on `/phase-2/`, where the
  // title reads "Phase two: funding tasks, not in service" and the heading "Phase two: funding
  // tasks". Matching them exactly was the wrong test: the question is not whether they agree, it is
  // whether the page already has a heading. When it does, the description slots UNDER it, which is
  // also where a reader expects a standfirst; when it does not, the shell supplies the title.
  const first = (blocks[0] || "").trim();
  const opensWithHeading = /^#\s+\S/.test(first);
  const head = opensWithHeading
    ? [first, "", description, ""].join("\n")
    : [`# ${title}`, "", description, ""].join("\n");
  const rest = opensWithHeading ? blocks.slice(1).join("\n\n") : body;
  const foot = `\n\n---\n\nSource: ${site}${route} — this markdown is derived from the page it `
    + `serves, so the two cannot disagree.\n`;
  return head + rest + foot;
}
