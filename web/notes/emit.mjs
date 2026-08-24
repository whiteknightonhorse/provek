/**
 * Method notes: deterministic emit. NO MODEL IS CALLED HERE, and that is the design.
 *
 * WHY. A note's prose is captured once, by `~/orchestra/notes_gen.py`, and committed under `src/`.
 * `loadNotes()` returns whatever is in that directory, and an EMPTY one is a real state rather than
 * a failure: the corpus is capped at `NOTE_CEILING` (D-18, laddered by D-35) and is under no
 * obligation to be full.
 * No count is written here on purpose. This paragraph carried one - "that directory is EMPTY today
 * and `loadNotes()` therefore returns nothing" - which was true when it was written on 2026-08-20
 * and stopped being true at `0a874e4`, when the first capture landed a source. A build
 * that called a model would depend on a network and on a token this host happens to hold,
 * would not be reproducible by a third party, and would make `dateModified` a function of when
 * somebody last rebuilt rather than of whether anything changed. So generation is a capture - the
 * same shape as the keyword base (D-17) - and this file only renders what is already in the tree.
 *
 * WHAT THIS FILE REFUSES. It reads the note's declared keys, addresses and figures and stops the
 * build when one of them does not hold: a key the base never returned, a declared demand state the
 * base contradicts, an address that resolves to nothing, a slug the manifest does not pin.
 *
 * WHAT IT DOES NOT REFUSE, STATED BECAUSE THIS SENTENCE USED TO CLAIM OTHERWISE. It does NOT
 * compare the body against `body_sha256`. That comparison lives in `tests/test_notes_freshness.py`
 * and only there. The line above promised it for four days, and the promise is load-bearing in the
 * wrong direction: `~/orchestra/notes_gen.py` publishes a note's manifest line BEFORE its prose
 * precisely because `loadNotes()` tolerates a pin whose note has not landed yet, and a future
 * repair that made this file honour its own old comment would turn that ordering into a build that
 * fails on the instant a capture was interrupted (T-C7, `evidence/RED-024-*`). A comment that
 * over-states a gate is not harmless documentation drift; it is a claim stronger than the artefact,
 * which is the defect this project exists to find. Found by Fable.
 *
 * The refusals are duplicated as tests under `tests/test_notes*.py`, which judge the EMITTED site
 * rather than this code - a gate that only lives in the generator is a gate the generator can be
 * edited past.
 *
 * FIGURES ARE COMPUTED FROM THE ARTEFACTS, not checked against them. A figure drawn by hand and
 * verified by a test is a figure that happened to agree today; a figure read out of
 * `registry.json` at build time cannot drift from it at all.
 */
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join } from "node:path";

const REPO = new URL("../../", import.meta.url).pathname;
const SRC = join(REPO, "web/notes/src");
const MANIFEST = join(REPO, "web/notes/manifest.json");
const KEYWORDS = join(REPO, "seo/keywords.csv");
const REACH = join(REPO, "web/notes/reach.json");

// --- the ceiling, as a ladder -------------------------------------------------------------------

/** THE LADDER (D-35). Each step is bought by observing the NEXT link of one causal chain -
 *  publication -> crawl -> index -> impressions - and none of them is bought by a date.
 *
 *  THE NUMBERS 7 AND 15 ARE ASSIGNED, exactly as 3 was assigned on 2026-08-20, and there is no
 *  reading behind either of them. What is measured is which STEP is open; how far a step carries is
 *  a choice. This sentence is here for the same reason D-18 states its own bounds as assigned: a
 *  number that arrives with a gate looks measured, and the ladder is a stronger claim than the flat
 *  ceiling was, so its unmeasured half has to be louder.
 *
 *  WHY `opens_on` NAMES A COUNTER AND NOT A CONDITION. The step is decided by `ceilingFrom` below
 *  from the reading in `reach.json`, so the whole rule is these four lines plus that function. A
 *  ladder described in prose and enforced somewhere else is the promise D-18 refused to be.
 *
 *  THERE IS NO FOURTH STEP ON PURPOSE. Above fifteen is an operator's decision taken at live
 *  impressions, not an automatic consequence of one; a ladder that keeps climbing on its own is the
 *  printing press D-19 declined to build. */
export const NOTE_LADDER = [
  { ceiling: 3, opens_on: null, link: "publication, which is our own act and buys nothing" },
  { ceiling: 7, opens_on: "crawl_stats", link: "a crawl of this site" },
  { ceiling: 15, opens_on: "query_stats", link: "a search impression of this site" },
];

/** The subject the reading has to be ABOUT. A control-paired reading of somebody else's property
 *  proves nothing about ours, and `reach.json` is a copied file - the one thing a copy can get
 *  wrong without any of its numbers being wrong is which site it is a copy about. */
const REACH_SUBJECT = "https://provek.dev/";

/** WHY `query_stats` AND NOT `rank_and_traffic` FOR THE SECOND STEP. Both read the impressions link
 *  of the chain, at different grains, and the control proves that they disagree while both work:
 *  402 impressions through `GetQueryStats` against 985 through `GetRankAndTrafficStats` in the same
 *  minute (D-34). A step that opened on whichever of two readings of one link answers first is a
 *  step calibrated to the more generous instrument. `query_stats` is the counter D-24 named when it
 *  stated the release condition, so it is the one the condition keeps. */

/** Read the ladder's reading. THE FILE'S ABSENCE IS A STATE, not a zero and not a default: a clone
 *  with no `reach.json` has not measured a closed step, it has not measured anything. Both answers
 *  hold the ceiling at the floor, and they are still different facts - the second one means nobody
 *  ran the probe, and a reader of a red build needs to be told which. */
export function readReach(path = REACH) {
  if (!existsSync(path)) return { state: "check_did_not_run", why: `no reading at ${path}`, chain: {} };
  let doc;
  try {
    doc = JSON.parse(readFileSync(path, "utf8"));
  } catch (e) {
    return { state: "unreadable", why: `reading did not parse: ${e.message}`, chain: {} };
  }
  if (doc.subject !== REACH_SUBJECT)
    return { state: "unreadable", why: `reading is about ${doc.subject}, not ${REACH_SUBJECT}`, chain: {} };
  if (typeof doc.chain !== "object" || doc.chain === null)
    return { state: "unreadable", why: "reading carries no chain object", chain: {} };
  return { state: "measured", why: null, chain: doc.chain, captured_at: doc.captured_at ?? null };
}

/** Is one step open? Returns the STATE, never a bare boolean, because four different things hold a
 *  step shut and only one of them is "we looked and there was nothing".
 *
 *  THE CONTROL PAIR IS REQUIRED IN BOTH DIRECTIONS, and one of those directions is deliberately
 *  stricter than it has to be. A subject that returned rows has itself demonstrated the call can
 *  see the quantity, so `control_proven_capable` is redundant in that case - and it is still
 *  demanded, because the pair is what makes the reading auditable by somebody who was not here when
 *  it was taken, and because being over-strict here errs toward a LOWER ceiling. The other
 *  direction is not a preference at all: a zero whose control also read zero establishes nothing
 *  (D-34), and letting it open a step would rebuild the defect T-B10 removed from the probe. */
export function stepState(chain, counter) {
  const c = chain[counter];
  if (c === undefined) return { open: false, state: "check_did_not_run", detail: `${counter} is not in the reading` };
  if (c.control_proven_capable !== true)
    return { open: false, state: "capability_unproven", detail: `${counter}: the control did not prove this call can see the quantity` };
  if (typeof c.count !== "number")
    return { open: false, state: "unreadable", detail: `${counter}: count is ${JSON.stringify(c.count)}, not a number` };
  if (c.count === 0)
    return { open: false, state: "nothing_qualified", detail: `${counter}: the call sees, and no row qualified for this site` };
  return { open: true, state: "measured", detail: `${counter}: ${c.count} rows for this site against ${c.control_count} at the control` };
}

/** The ceiling, and the reason it is that number. A step is climbed only when every step below it
 *  is open - a ladder rather than a menu, so an impressions row cannot arrive without a crawl row
 *  and skip a rung on the way. */
export function ceilingFrom(reach) {
  const steps = [];
  let ceiling = NOTE_LADDER[0].ceiling;
  let climbing = reach.state === "measured";
  for (const rung of NOTE_LADDER.slice(1)) {
    if (!climbing) {
      steps.push({ ceiling: rung.ceiling, open: false, state: reach.state === "measured" ? "blocked_below" : reach.state,
                   detail: reach.why ?? "the step below this one is closed" });
      continue;
    }
    const s = stepState(reach.chain, rung.opens_on);
    steps.push({ ceiling: rung.ceiling, ...s });
    if (s.open) ceiling = rung.ceiling;
    else climbing = false;
  }
  return { ceiling, reading: reach.state, steps };
}

export const NOTE_REACH = readReach();
export const NOTE_STEP = ceilingFrom(NOTE_REACH);

/** The number the build enforces. It is DERIVED - the ladder above and the reading beside it are
 *  the source, and `tests/test_notes_ceiling.py` recomputes both rather than trusting this. */
export const NOTE_CEILING = NOTE_STEP.ceiling;

const esc = (s) =>
  String(s).replace(/[<>&"]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;" })[c]);

// --- sources ------------------------------------------------------------------------------------

function keywordRows() {
  const [head, ...lines] = readFileSync(KEYWORDS, "utf8").trim().split("\n");
  const cols = head.split(",");
  const out = new Map();
  for (const line of lines) {
    // The base is written by us and holds no quoted commas; a key with one would be `too_long`
    // anyway. Parsing narrowly and loudly beats parsing broadly and silently.
    const cells = line.split(",");
    const row = Object.fromEntries(cols.map((c, i) => [c, cells[i]]));
    out.set(row.key, row);
  }
  return out;
}

export function loadNotes() {
  if (!existsSync(SRC)) return [];
  const manifest = JSON.parse(readFileSync(MANIFEST, "utf8")).notes;
  const base = keywordRows();
  const files = readdirSync(SRC).filter((f) => f.endsWith(".md")).sort();

  if (files.length > NOTE_CEILING) {
    // The refusal names the CLOSED STEP, not just the number. "ceiling is 3" invites an edit to a
    // 3; "the crawl step is shut because no row qualified" names the reading that would open it,
    // and says which of four silences that reading was.
    const shut = NOTE_STEP.steps.find((s) => !s.open);
    throw new Error(
      `notes: ${files.length} sources, ceiling is ${NOTE_CEILING} (LAW-NOTES-CEILING). ` +
      `The step to ${shut?.ceiling} is closed: ${shut?.state} - ${shut?.detail}. ` +
      `It opens on a reading in web/notes/reach.json, not on an edit to this file (D-35).`);
  }

  return files.map((f) => {
    const raw = readFileSync(join(SRC, f), "utf8");
    const m = raw.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
    if (!m) throw new Error(`notes: ${f} has no front matter`);
    const front = JSON.parse(m[1]);
    const body = m[2].trim();

    const entry = manifest[front.slug];
    if (!entry) throw new Error(`notes: ${front.slug} is not in the manifest`);

    for (const k of front.keys ?? []) {
      const row = base.get(k.key);
      if (!row) throw new Error(`notes: ${front.slug} names a key the base never returned: ${k.key}`);
      if (row.demand_state !== k.demand_state)
        throw new Error(
          `notes: ${front.slug} key ${k.key} carries demand_state ${k.demand_state}, base says ${row.demand_state}`);
      // An unmeasured demand has no number. Writing a zero here would destroy the only evidence
      // that the reading is missing - the founding defect of this project, in a front matter.
      if (row.demand_state !== "measured" && "impressions_exact" in k)
        throw new Error(`notes: ${front.slug} key ${k.key} carries impressions while ${row.demand_state}`);
    }
    for (const a of front.addresses ?? []) {
      const p = join(REPO, a.file);
      if (!existsSync(p)) throw new Error(`notes: ${front.slug} address ${a.ref} -> missing ${a.file}`);
      if (!readFileSync(p, "utf8").includes(a.anchor))
        throw new Error(`notes: ${front.slug} address ${a.ref} -> anchor absent in ${a.file}`);
    }
    return { front, body, ...entry };
  });
}

// --- figures, computed from the artefacts --------------------------------------------------------

/** Every colour is a design token or `currentColor`. A hex literal here would route around
 *  DESIGN.md's palette through the one element nobody thinks to look at.
 *
 *  THE IDS ARE NAMESPACED PER FIGURE, and they were not until the first note carried two of them.
 *  These `<defs>` were a module constant, so every figure emitted the same `pv-hatch` and
 *  `pv-cross`; one figure to a page hid it, and the first page to place two shipped duplicate IDs.
 *  The Nu validator names it, and the browser consequence is worse than the validation error: both
 *  `<pattern>` elements answer to one name, so `url(#pv-hatch)` in the second figure resolves to
 *  the first figure's definition. The hatch that distinguishes an instrument's refusal from a small
 *  measurement is exactly the paint that would have gone wrong. Measured on the live page, not in
 *  the tree - see `evidence/MEASURED-001-the-first-note-pages-as-served.txt`. */
const hatchDefs = (ns) => `<defs>
  <pattern id="${ns}-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="6" stroke="var(--color-unknown)" stroke-width="2"/>
  </pattern>
  <pattern id="${ns}-cross" width="6" height="6" patternUnits="userSpaceOnUse">
    <path d="M0 0 L6 6 M6 0 L0 6" stroke="var(--color-unknown)" stroke-width="1.2" fill="none"/>
  </pattern>
</defs>`;

function registryCoverage(ns) {
  // The SERVED copy, `web/public/data/`, not the emitted-artefact copy under `public/`. They are
  // byte-identical today and a test holds them so; the figure reads the one a visitor fetches
  // because that is the artefact a claim on this page is about (L-3).
  const DATA = join(REPO, "web/public/data");
  const reg = JSON.parse(readFileSync(join(DATA, "registry.json"), "utf8"));
  const passports = Object.fromEntries(
    readdirSync(join(DATA, "passports"))
      .filter((f) => f.endsWith(".json"))
      .map((f) => {
        const p = JSON.parse(readFileSync(join(DATA, "passports", f), "utf8")).passport;
        return [p.subject_id, p];
      }));

  const ops = ["development_initiation", "deployment", "treasury_control"];
  const rows = reg.subjects.map((s) => {
    const p = passports[s.subject_id];
    return {
      name: s.subject_id.replace(/^git:[^/]+\//, ""),
      cells: ops.map((op) => {
        const o = p?.verified.operations.find((x) => x.operation === op);
        if (!o) return { state: "check_did_not_run", label: "" };
        return { state: o.measured ? "measured" : o.level, label: o.measured ? o.level : "" };
      }),
    };
  });

  const W = 640, LEFT = 210, CELL = 128, ROW = 26, TOP = 46;
  const H = TOP + rows.length * ROW + 34;
  const head = ops.map((op, i) =>
    `<text x="${LEFT + i * CELL + CELL / 2}" y="30" text-anchor="middle" font-size="10.5"
       fill="var(--color-ink-3)" font-family="var(--font-mono)">${esc(op.replace(/_/g, " "))}</text>`).join("");

  const body = rows.map((r, ri) => {
    const y = TOP + ri * ROW;
    const cells = r.cells.map((c, ci) => {
      const x = LEFT + ci * CELL + 6;
      const fill = c.state === "measured" ? "var(--color-pass)"
        : c.state === "unreadable" ? `url(#${ns}-cross)` : `url(#${ns}-hatch)`;
      const label = c.label
        ? `<text x="${x + 56}" y="${y + 13}" text-anchor="middle" font-size="10.5"
             fill="var(--color-paper)" font-family="var(--font-mono)">${esc(c.label)}</text>` : "";
      return `<rect x="${x}" y="${y + 2}" width="112" height="16" fill="${fill}"
                stroke="var(--color-line-2)" stroke-width="0.75"/>${label}`;
    }).join("");
    return `<text x="0" y="${y + 14}" font-size="11" fill="var(--color-ink-2)"
              font-family="var(--font-mono)">${esc(r.name.slice(0, 30))}</text>${cells}`;
  }).join("");

  const legend = [
    ["var(--color-pass)", "measured"],
    [`url(#${ns}-hatch)`, "check_did_not_run"],
    [`url(#${ns}-cross)`, "unreadable"],
  ].map(([fill, label], i) =>
    `<rect x="${i * 190}" y="${H - 22}" width="14" height="11" fill="${fill}"
       stroke="var(--color-line-2)" stroke-width="0.75"/>
     <text x="${i * 190 + 20}" y="${H - 12}" font-size="10.5" fill="var(--color-ink-3)"
       font-family="var(--font-mono)">${label}</text>`).join("");

  // The alternative text is COUNTED, like the bars it describes. A sentence typed out by hand
  // beside a computed figure is the one part of the drawing that can quietly go on saying "four
  // are measured" after the registry stops agreeing - and it is the part only a screen reader
  // hears, so nobody would see it drift.
  const cells = rows.length * ops.length;
  const measured = rows.flatMap((r) => r.cells).filter((c) => c.state === "measured").length;
  return {
    svg: `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" xmlns="http://www.w3.org/2000/svg"
      aria-label="${cells} operations across ${rows.length} subjects. ${measured} are measured; the rest carry a named absence.">
      ${hatchDefs(ns)}${head}${body}${legend}</svg>`,
    caption: `Every operation on every subject in the registry, as at ${reg.generated_at.slice(0, 10)}. `
      + `No total is drawn: a single coverage number would turn a named shortfall into a score. `
      + `Read from <code>public/registry/registry.json</code> and the eight passports beside it.`,
  };
}

function keywordDemandStates(ns) {
  const src = JSON.parse(readFileSync(join(REPO, "seo/sources.json"), "utf8"));
  const d = src.demand_states;
  const order = ["measured", "nothing_qualified", "unreadable", "check_did_not_run"];
  const max = Math.max(...order.map((k) => d[k]));
  const W = 640, LEFT = 168, ROW = 34, TOP = 8, BARW = W - LEFT - 56;
  const H = TOP + order.length * ROW + 8;

  const bars = order.map((k, i) => {
    const y = TOP + i * ROW;
    const w = Math.max(2, Math.round((d[k] / max) * BARW));
    // An instrument's refusal is not a quantity of demand. It gets the same hatch the passport
    // gives an absent level, so the eye cannot read it as a smaller measurement.
    const fill = k === "measured" ? "var(--color-accent)"
      : k === "nothing_qualified" ? "var(--color-line-2)" : `url(#${ns}-hatch)`;
    return `<text x="0" y="${y + 15}" font-size="11" fill="var(--color-ink-2)"
              font-family="var(--font-mono)">${k}</text>
            <rect x="${LEFT}" y="${y + 3}" width="${w}" height="16" fill="${fill}"
              stroke="var(--color-line-2)" stroke-width="0.75"/>
            <text x="${LEFT + w + 8}" y="${y + 16}" font-size="11" fill="var(--color-ink-3)"
              font-family="var(--font-mono)">${d[k]}</text>`;
  }).join("");

  // Read out of the same object the bars are drawn from, for the reason given on the figure above:
  // a hand-written count beside a computed one is a claim with a separate lifetime.
  const spoken = `Of ${src.totals.keys} captured keys, ${d.measured} have a measured demand, `
    + `${d.nothing_qualified} returned nothing, ${d.unreadable} could not be read, and `
    + `${d.check_did_not_run} did not reach the instrument.`;
  return {
    svg: `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" xmlns="http://www.w3.org/2000/svg"
      aria-label="${esc(spoken)}">
      ${hatchDefs(ns)}${bars}</svg>`,
    caption: `The demand states of all ${src.totals.keys} keys captured on ${src.captured_at}. `
      + `The two hatched rows are not small numbers - they are rows where the instrument did not `
      + `answer. Read from <code>seo/sources.json</code>.`,
  };
}

const FIGURES = {
  "registry-coverage": registryCoverage,
  "keyword-demand-states": keywordDemandStates,
};

// --- markdown, narrowly ---------------------------------------------------------------------------

function inline(s) {
  return esc(s)
    .replace(/`([^`]+)`/g, '<code class="font-mono text-[0.8em]">$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g,
      '<a href="$2" class="text-[var(--color-accent)] hover:underline">$1</a>');
}

const slugify = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

export function renderBody(body) {
  const out = [];
  // The namespace is the figure's POSITION on the page, not its name. Either would have fixed the
  // collision that shipped, and a counter also holds if the same figure is ever placed twice - a
  // case the declared/placed check permits, because it compares sets.
  let figureSeq = 0;
  for (const block of body.split(/\n{2,}/)) {
    const b = block.trim();
    if (!b) continue;
    let m;
    if ((m = b.match(/^\{\{figure:([a-z0-9-]+)\}\}$/))) {
      const build = FIGURES[m[1]];
      if (!build) throw new Error(`notes: unknown figure ${m[1]}`);
      const { svg, caption } = build(`pv-f${figureSeq++}`);
      out.push(
        `<figure class="my-7 border border-[var(--color-line)] bg-[var(--color-paper)] p-4">` +
        `${svg}<figcaption class="mt-3 text-xs text-[var(--color-ink-3)]">${inline(caption)}</figcaption></figure>`);
    } else if ((m = b.match(/^## (.+)$/))) {
      out.push(`<h2 id="${slugify(m[1])}" class="mt-9 text-lg font-semibold">${inline(m[1])}</h2>`);
    } else if ((m = b.match(/^### (.+)$/))) {
      out.push(`<h3 class="mt-6 text-base font-semibold">${inline(m[1])}</h3>`);
    } else if (b.startsWith("- ")) {
      const items = b.split("\n").map((l) => `<li>${inline(l.replace(/^- /, ""))}</li>`).join("");
      out.push(`<ul class="mt-3 list-disc pl-5 space-y-1 text-sm text-[var(--color-ink-2)]">${items}</ul>`);
    } else if (b.startsWith("|")) {
      const rows = b.split("\n").filter((l) => !/^\|[\s:|-]+\|$/.test(l));
      const cells = (l, tag) => l.split("|").slice(1, -1)
        .map((c) => `<${tag} class="py-2 pr-5 align-top">${inline(c.trim())}</${tag}>`).join("");
      out.push(`<table class="mt-4 w-full text-sm border-y border-[var(--color-line)]">` +
        `<thead><tr class="text-[var(--color-ink-3)]">${cells(rows[0], "th")}</tr></thead><tbody>` +
        rows.slice(1).map((r) => `<tr class="border-t border-[var(--color-line)]">${cells(r, "td")}</tr>`).join("") +
        `</tbody></table>`);
    } else {
      out.push(`<p class="mt-4 text-sm text-[var(--color-ink-2)]">${inline(b)}</p>`);
    }
  }
  return out.join("\n");
}

// --- the page -------------------------------------------------------------------------------------

/** The provenance line, on the face of every note.
 *
 * We measure how much of somebody else's business runs without a human. Publishing prose drafted
 * by two models without saying so would be the same omission we exist to find, committed by the
 * party that named it. The models draft; the verdict on every structural claim is taken by
 * `tests/test_notes*.py` from a measured quantity, and that half is said here too because a
 * disclosure that only admits the machine is only half the fact. */
function provenanceLine(front) {
  const p = front.provenance;
  return `<p class="mt-6 text-xs text-[var(--color-ink-3)] border-t border-[var(--color-line)] pt-3">` +
    `Drafted by <code class="font-mono">${esc(p.plan_model)}</code> (structure) and ` +
    `<code class="font-mono">${esc(p.prose_model)}</code> (prose) on ${esc(p.generated_at)}; ` +
    `every claim on this page resolves to an artefact in ` +
    `<a href="https://github.com/whiteknightonhorse/provek" class="text-[var(--color-accent)] hover:underline">the repository</a>, ` +
    `and the structural rules are held by deterministic tests rather than by review.</p>`;
}

function addressList(front) {
  const rows = front.addresses.map((a) =>
    `<li><code class="font-mono text-xs">${esc(a.ref)}</code> &mdash; ${esc(a.file)}</li>`).join("");
  return `<h2 id="addresses" class="mt-9 text-lg font-semibold">Where each statement comes from</h2>
    <p class="mt-4 text-sm text-[var(--color-ink-2)]">Nothing on this page is asserted on its own
    authority. These are the places in the repository where each claim above is written down, and a
    note whose address does not resolve fails the build rather than being published with a gap.</p>
    <ul class="mt-3 list-disc pl-5 space-y-1 text-sm text-[var(--color-ink-2)]">${rows}</ul>`;
}

function faqBlock(front) {
  if (!front.faq?.length) return "";
  // Every question and answer in the JSON-LD exists here, visibly and verbatim. Schema carrying
  // text the page does not show is what earns a manual action.
  const items = front.faq.map((f) =>
    `<div class="border-t border-[var(--color-line)] py-4">
       <h3 class="text-base font-semibold">${esc(f.q)}</h3>
       <p class="mt-2 text-sm text-[var(--color-ink-2)]">${esc(f.a)}</p></div>`).join("");
  return `<h2 id="questions" class="mt-9 text-lg font-semibold">Questions</h2>
    <div class="mt-3">${items}</div>`;
}

export function noteArticle(note) {
  const { front, body, date_published, date_modified } = note;
  const corrections = front.lifecycle.corrections.length
    ? `<div class="mt-4 border border-[var(--color-line)] px-4 py-3 text-sm"
         style="background: var(--c-wash-warn)"><strong>Corrected.</strong> ` +
      front.lifecycle.corrections.map((c) => `${esc(c.on)}: ${esc(c.what)}`).join(" ") + `</div>`
    : "";
  const superseded = front.lifecycle.status === "superseded"
    ? `<div class="mt-4 border border-[var(--color-line)] px-4 py-3 text-sm"
         style="background: var(--c-wash-warn)"><strong>Superseded.</strong> ${esc(front.lifecycle.superseded_note ?? "")}</div>`
    : "";
  return `<article class="max-w-[46rem]">
  <nav aria-label="Breadcrumb" class="text-xs text-[var(--color-ink-3)]">
    <a href="/method/" class="hover:underline">Method</a> /
    <a href="/method/notes/" class="hover:underline">Notes</a>
  </nav>
  <h1 class="mt-2 text-2xl font-semibold tracking-tight">${esc(front.h1)}</h1>
  <p class="mt-2 text-xs text-[var(--color-ink-3)]">
    Published <time datetime="${date_published}">${date_published}</time>${
      date_modified !== date_published
        ? `, revised <time datetime="${date_modified}">${date_modified}</time>` : ""}.
  </p>
  ${superseded}${corrections}
  ${renderBody(body)}
  ${faqBlock(front)}
  ${addressList(front)}
  ${provenanceLine(front)}
</article>`;
}

/** The sentence under the index that says why the number is the number. EVERY FIGURE IN IT IS READ
 *  OUT OF THE LADDER AND THE READING, for the reason the figures above are computed: a hand-written
 *  count beside a computed one is a claim with its own lifetime, and this one is on the page a
 *  reader is most likely to quote. The sentence it replaced said the instrument "does not answer
 *  yet"; the instrument answers, and it answers zero, and those are different facts (D-34). */
function ladderSentence() {
  const shut = NOTE_STEP.steps.find((s) => !s.open);
  if (!shut)
    return `Every step of the ladder that this site's own measurements can open is open; going `
      + `further is a decision rather than a reading, and none has been taken.`;
  if (NOTE_STEP.reading !== "measured")
    return `No reading of how far these pages have travelled is present in this checkout, so the `
      + `ceiling sits at its floor. That is <code>${NOTE_STEP.reading}</code> - nobody measured - `
      + `and it is not the same state as having measured and found nothing.`;
  const rung = NOTE_LADDER.find((r) => r.ceiling === shut.ceiling);
  const c = NOTE_REACH.chain[rung.opens_on];
  const read = NOTE_REACH.captured_at ? ` Read on ${NOTE_REACH.captured_at.slice(0, 10)}:` : " Read:";
  const body = shut.state === "nothing_qualified"
    ? `${read} the call answers for both sites, it returned ${c.control_count} rows for the control `
      + `property and ${c.count} for this one.`
    : `${read} the step is held shut by <code>${esc(shut.state)}</code>, which is a named absence `
      + `rather than a measurement of nobody reading.`;
  return `It rises to ${shut.ceiling} when Bing Webmaster reports ${esc(rung.link)} `
    + `&mdash; <code>${esc(rung.opens_on)}</code> &mdash; alongside a control property that proves `
    + `the same call is able to report it at all.${body} Nothing here is published at a rate: the `
    + `number is the last reading of whether these pages reached anyone, not a schedule.`;
}

export function notesIndexArticle(notes) {
  const rows = notes.map((n) =>
    `<li class="border-t border-[var(--color-line)] py-4">
       <a href="/method/notes/${n.front.slug}/" class="text-[var(--color-accent)] hover:underline font-medium">${esc(n.front.h1)}</a>
       <p class="mt-1 text-sm text-[var(--color-ink-2)]">${esc(n.front.description)}</p>
       <p class="mt-1 text-xs text-[var(--color-ink-3)]">${n.date_modified}</p></li>`).join("");
  return `<article class="max-w-[46rem]">
  <nav aria-label="Breadcrumb" class="text-xs text-[var(--color-ink-3)]">
    <a href="/method/" class="hover:underline">Method</a>
  </nav>
  <h1 class="mt-2 text-2xl font-semibold tracking-tight">Notes on the method</h1>
  <p class="mt-2 text-sm text-[var(--color-ink-2)] max-w-[46rem]">Each note describes one part of
  this instrument: a term it uses, a state it distinguishes, or a thing the standard underneath it
  does not settle. They document what is measured and what cannot be, and none of them advises
  anybody on what to do about it.</p>
  <p class="mt-4 text-sm text-[var(--color-ink-2)]">There are ${notes.length}, and at most
  ${NOTE_CEILING} may stand. ${ladderSentence()}</p>
  <ul class="mt-6">${rows}</ul>
</article>`;
}

// --- structured data --------------------------------------------------------------------------------

export function noteLd(note, SITE) {
  const { front, date_published, date_modified } = note;
  const url = `${SITE}/method/notes/${front.slug}/`;
  const out = [{
    "@context": "https://schema.org",
    "@type": "Article",
    headline: front.h1,
    description: front.description,
    url,
    datePublished: date_published,
    dateModified: date_modified,
    inLanguage: "en",
    isAccessibleForFree: true,
    // Organization, never a person and never a model name. The signature belongs to the party a
    // claim can be brought against, and a model is not one. What drafted the prose is disclosed on
    // the face of the page instead, where a reader sees it.
    author: { "@type": "Organization", name: "Provek", url: SITE + "/" },
    publisher: { "@type": "Organization", name: "Provek", url: SITE + "/" },
    isPartOf: { "@type": "WebPage", url: `${SITE}/method/` },
    // No `image`. The figures are SVG computed at build time; consumers of Article expect a raster,
    // and drawing a PNG purely so the markup can carry one would be a claim made for a validator
    // rather than for a reader.
  }, {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Provek", item: SITE + "/" },
      { "@type": "ListItem", position: 2, name: "Method", item: SITE + "/method/" },
      { "@type": "ListItem", position: 3, name: "Notes", item: SITE + "/method/notes/" },
      { "@type": "ListItem", position: 4, name: front.h1, item: url },
    ],
  }];
  if (front.faq?.length) {
    out.push({
      "@context": "https://schema.org",
      "@type": "FAQPage",
      mainEntity: front.faq.map((f) => ({
        "@type": "Question",
        name: f.q,
        acceptedAnswer: { "@type": "Answer", text: f.a },
      })),
    });
  }
  return out;
}
