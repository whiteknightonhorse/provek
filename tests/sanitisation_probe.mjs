// A hostile-input probe for the derived-markdown converter. Not a build tool: a test fixture.
import { htmlToMarkdown } from "../web/html_to_markdown.mjs";

const CASES = {
  // Removing `<script>` in ONE pass rebuilds it out of the halves that remain.
  reconstructed: `<main><p>before<scr<script>ipt>alert(1)</script>after</p></main>`,
  comment: `<main><p>a<!<!-- -->-- x --># b</p></main>`,
  nested_svg: `<main><p>x<svg><svg></svg></svg>y</p></main>`,
  // THE REAL PATH. A subject writes this into their own `provek.json`; React escapes it into the
  // page as entities, which is what this converter actually reads.
  escaped_from_a_declaration: `<main><p>contact: &lt;script&gt;alert(1)&lt;/script&gt;</p></main>`,
  escaped_img: `<main><p>x &lt;img src=q onerror=alert(1)&gt; y</p></main>`,
  // D-43, the dismiss argument's mutation-sensitive attack for code-scanning alerts #76/#77.
  // `strip()` chains FOUR different regexes (comment, script/style/template, svg, sr-only) inside
  // ONE literal loop rather than four separate ones, because the four interact: removing the
  // `<script>` tag below turns `<!` + `--z-->` into a freshly reconstructed `<!--z-->` comment that
  // the comment regex, having already run earlier in THIS pass, will not see again until the loop
  // repeats. A SINGLE pass through the chain leaves `<!--z-->` behind - verified by hand against a
  // copy of `strip()`'s chain with the surrounding `do {...} while` deleted, which returns
  // `"<!--z-->w"` for this exact input where the shipped, looped `strip()` returns `"w"`.
  cross_category_reconstruction: `<main><p>x<!<script>y</script>--z-->w</p></main>`,
};
const out = {};
for (const [k, html] of Object.entries(CASES)) out[k] = htmlToMarkdown(html);
process.stdout.write(JSON.stringify(out, null, 1));
