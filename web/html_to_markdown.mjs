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
  mdash: "—", ndash: "–", hellip: "…", rsquo: "’", lsquo: "‘",
  ldquo: "“", rdquo: "”", middot: "·", times: "×", divide: "÷",
  thinsp: " ", check: "✓",
};

/** DECISIONS.md D-43. This converter's input became PARTLY UNTRUSTED on 2026-08-31, when the
 *  accountability block began rendering fields read from a SUBJECT'S OWN `provek.json`. Two rules
 *  hold the boundary; both live here in code, not only in D-43's prose, because a rule that lives
 *  only in a decision record is not armed by anything that runs.
 *
 *  DECODING MAY NOT MANUFACTURE A TAG. Stripping runs on the page's markup; decoding runs after it
 *  (ratified in D-43; reversing the order is forbidden - decoding first would let an honestly
 *  ESCAPED sequence like `&amp;lt;div&amp;gt;` be turned into a live tag by decoding and then eaten
 *  by the strip that follows, a silent loss of text nobody attacked). An angle bracket that arrives
 *  escaped is therefore never seen by `stripTags`/`strip`, and `<`/`>` stay escaped here regardless
 *  of which spelling asked for them - named (`&lt;`), decimal (`&#60;`) or hex (`&#x3c;`). A
 *  markdown reader still SEES the bracket; no reader can be made to execute it.
 *
 *  WHAT WAS ACTUALLY MEASURED, stated at the strength the artefact supports (D-43 corrects an
 *  earlier overclaim here: this file's own docstring once named `/p/<subject>/index.md` as the
 *  artefact affected, but that file is built by `web/markdown.mjs`, which does not read a
 *  declaration at all - the claim named the wrong assembler). What was actually run is
 *  `tests/sanitisation_probe.mjs` against THIS converter directly: before this constant existed, a
 *  declaration field holding `<script>alert(1)</script>`, fed through `htmlToMarkdown` the way a
 *  future accountability-rendering page would present it, decoded back into a live tag in the
 *  function's own return value. `web/markdown.mjs` interpolates passport fields with no escaping
 *  step of its own and is a SEPARATE open gap (D-43), guarded by `src/collector/declaration.py`
 *  refusing `[`, `]` and a backtick in any declared string - markdown's link/code-span syntax,
 *  which no angle-bracket rule touches. */
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

/** Remove every HTML tag, to a fixed point. D-43. A SINGLE pass is not removal: deleting
 *  `<script>` from `<scr<script>ipt>` leaves `<script>` exposed - the pass RECONSTRUCTS the very
 *  tag it just took out, which is the whole of CodeQL's "incomplete multi-character sanitization".
 *
 *  WRITTEN AS A LITERAL do/while ON PURPOSE, not behind a generic higher-order helper. An earlier
 *  version wrapped every loop in `untilStable(text, rewrite, limit)`, and CodeQL's static analysis
 *  did not credit it: `js/incomplete-multi-character-sanitization` still fired seven times against
 *  the individual `.replace()` calls inside that wrapper, on the very commit that introduced it,
 *  because the analyzer has no way to see through a rewrite function passed as a parameter to know
 *  the loop around it reaches a fixed point. The rule's own documentation recommends exactly this
 *  shape - a `do {...} while (input !== previous)` around ONE `.replace()` - so the fix is the
 *  literal form the tool already asks for, not a cleverer abstraction of it.
 *
 *  ONE-PLACE, closing a gap the wrapper had opened rather than closed: `y.replace(/<[^>]+>/g, "")`
 *  used to appear five times across `inline()` below - the href-text extractor, strong, em, code,
 *  and the final catch-all - each wrapped in its own separate `untilStable` call. One rule, five
 *  copies, found in the same review that asked for the literal loop.
 *
 *  Bounded at 20 iterations: an unbounded loop over hostile input is the other half of the same bug
 *  class - this repository has already shipped one measured ReDoS - and 20 passes is far past
 *  anything nesting in real markup produces. */
function stripTags(s) {
  let prev;
  let i = 0;
  do {
    prev = s;
    s = s.replace(/<[^>]+>/g, "");
    i += 1;
  } while (s !== prev && i < 20);
  return s;
}

/** Everything a reader never sees is removed BEFORE any text is taken: scripts, styles, and the
 *  `sr-only` spans that exist so a screen reader hears what the eye reads. Keeping the latter would
 *  print every reason twice — the exact doubling the visible/announced pair is designed to avoid.
 *
 *  ITS OWN LITERAL LOOP - the second and last manual fixed-point in this file (D-43); `stripTags`
 *  above is the first. Kept separate rather than merged into one bigger loop because the two strip
 *  DIFFERENT things for different reasons: this one removes whole elements a reader must never see
 *  any part of, `stripTags` removes bare markup around text a reader DOES see. */
function strip(html) {
  let prev;
  let i = 0;
  do {
    prev = html;
    html = html
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
      .replace(/<span[^>]*\bclass="[^"]*\bsr-only\b[^"]*"[^>]*>[\s\S]*?<\/span>/gi, "");
    i += 1;
  } while (html !== prev && i < 20);
  return html;
}

function inline(html) {
  // ADJACENT ELEMENTS ARE ADJACENT WORDS, NOT ONE WORD. `<span>…recipient</span><span>enforced…`
  // has no whitespace between the two texts, so stripping the tags glued them into
  // "recipientenforced" — measured on `/phase-2/`, where a word-level fidelity check then reported
  // "recipient" as LOST when in truth it was merged. The text was never dropped; it stopped being
  // readable, which for a document meant for machines is the same defect wearing a better mask.
  //
  // MARKDOWN-FORMING REPLACEMENTS RUN ONCE, IN ONE PASS. None of the six below can reconstruct a
  // match of its own pattern the way a bare tag-strip can - each consumes a specific, named element
  // and emits markdown syntax, never HTML - so this half of `inline()` carries no loop. Whatever
  // markup they leave behind (their own children's tags, and anything unrecognised) is bare `<...>`
  // markup with nothing left to reconstruct it, which is exactly what `stripTags` removes below.
  html = html
    .replace(/<\/(span|a|strong|em|b|i|code)>\s*<(span|a|strong|em|b|i|code)\b/gi, "</$1> <$2")
    .replace(/<a\b[^>]*\bhref="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi,
      (m, href, text) => {
        const t = decode(stripTags(text)).trim();
        return t ? `[${t}](${href})` : "";
      })
    .replace(/<(strong|b)\b[^>]*>([\s\S]*?)<\/\1>/gi, (m, _t, x) => `**${stripTags(x).trim()}**`)
    .replace(/<(em|i)\b[^>]*>([\s\S]*?)<\/\1>/gi, (m, _t, x) => `*${stripTags(x).trim()}*`)
    .replace(/<code\b[^>]*>([\s\S]*?)<\/code>/gi, (m, x) => "`" + stripTags(x).trim() + "`")
    .replace(/<br\s*\/?>/gi, "\n");

  // Whatever tags remain are inline or unknown; `stripTags` drops the markup WITHOUT dropping the
  // text it wrapped, then `decode` resolves entities last (D-43: never before the strip above).
  return decode(stripTags(html))
    .replace(/[ \t ]+/g, " ")
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

  const lines = s.split("\n").map((l) => l.replace(/[ \t ]+/g, " ").replace(/ · $/, "").trim());
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
