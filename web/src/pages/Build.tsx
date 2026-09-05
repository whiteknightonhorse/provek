/** `/build/` - the AI agent template library index (ADR-0011, SPEC 3.7, D-57).
 *
 * Not an academy, not a course, not a marketplace: one screen before a grid of templates a
 * reader's own coding agent turns into a running business agent, one business operation at a
 * time. Section 5.1 of the ruling names the shape below fact for fact. */
import { useState } from "react";
import { Page, Strip } from "../components/Chrome";
import { CopyButton } from "../components/CopyButton";
import { FunnelStrip } from "../components/FunnelStrip";
import { FUNNEL_SENTENCE, INCUBATOR_SENTENCE } from "../copy";
import type { Template } from "../types";

const TOOLS = ["Claude Code", "Codex", "Cursor", "Other"] as const;
type Tool = (typeof TOOLS)[number];

const WHERE_TO_PASTE: Record<Tool, string> = {
  "Claude Code": "Paste it into a Claude Code conversation, or save it under a project's own skills folder and reference it by name.",
  Codex: "Paste it into a Codex conversation, or add it to your project's AGENTS.md so Codex reads it automatically.",
  Cursor: "Paste it into Cursor's chat, or save it as a rules file under .cursor/ and reference it.",
  Other: "Paste it into any coding agent that can create files and run shell commands - the instruction names what it needs from the agent, not which one.",
};

/** The tool selector. Copied text never changes with the tool - only where the reader is told to
 * paste it does. All four instructions are always in the DOM; before any click (and for a reader
 * with no JavaScript at all) every one of them is visible, never just the first. */
function ToolSelector() {
  const [active, setActive] = useState<Tool | null>(null);
  return (
    <div className="mt-4">
      <div role="tablist" aria-label="Coding agent" className="flex flex-wrap gap-2">
        {TOOLS.map((t) => (
          <button
            key={t}
            type="button"
            role="tab"
            aria-selected={active === t}
            onClick={() => setActive(t)}
            className={
              "text-xs border px-2.5 py-1.5 min-h-8 inline-flex items-center " +
              (active === t
                ? "border-[var(--color-ink)] bg-[var(--color-paper-2)]"
                : "border-[var(--color-line-2)] hover:bg-[var(--color-paper-2)]")
            }
          >
            {t}
          </button>
        ))}
      </div>
      <div className="mt-2">
        {TOOLS.map((t) => (
          <p
            key={t}
            className={
              (active !== null && active !== t ? "hidden " : "") +
              "text-sm text-[var(--color-ink-2)]"
            }
          >
            {WHERE_TO_PASTE[t]}
          </p>
        ))}
      </div>
      <p className="mt-2 text-xs text-[var(--color-ink-3)]">
        Your coding agent runs on your own subscription or API key. Provek runs nothing for you and
        sees nothing you build.
      </p>
    </div>
  );
}

function TemplateCard({ t }: { t: Template }) {
  return (
    <div className="border border-[var(--color-line)] bg-[var(--color-paper)] p-4">
      <a
        href={`/build/${t.slug}/`}
        className="text-base font-semibold tracking-tight text-[var(--color-accent)] hover:underline"
      >
        {t.title}
      </a>
      <p className="mt-1 text-sm text-[var(--color-ink-2)]">{t.businessOperation}</p>
      <dl className="mt-3 space-y-1 text-xs text-[var(--color-ink-3)]">
        <div>
          <dt className="inline font-medium text-[var(--color-ink-2)]">Human still does: </dt>
          <dd className="inline">{t.humanRemainsFor}</dd>
        </div>
        <div>
          <dt className="inline font-medium text-[var(--color-ink-2)]">Needs: </dt>
          <dd className="inline">{t.requires}</dd>
        </div>
        <div>
          <dt className="inline font-medium text-[var(--color-ink-2)]">{t.dryRun.line}</dt>
        </div>
      </dl>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <CopyButton getText={() => t.raw} idleLabel="Copy" />
        <a href={`/build/${t.slug}/`} className="text-xs text-[var(--color-accent)] hover:underline">
          Open &rarr;
        </a>
      </div>
    </div>
  );
}

export default function Build({ templates }: { templates: Template[] }) {
  return (
    <Page>
      <div className="max-w-[46rem]">
        <h1 className="text-2xl font-semibold tracking-tight">
          Build an AI agent that runs one operation of your business.
        </h1>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          Pick a template. Copy one instruction into Claude Code, Codex or Cursor. Your coding
          agent builds the agent in your own repository. Free, no account.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <a
            href="#templates"
            className="inline-flex items-center border border-[var(--color-ink)] bg-[var(--color-ink)] px-4 py-2 text-sm font-medium text-[var(--color-paper)] hover:opacity-90"
          >
            Choose a template
          </a>
          <a
            href="#how-it-works"
            className="inline-flex items-center border border-[var(--color-line-2)] px-4 py-2 text-sm font-medium hover:bg-[var(--color-paper-2)]"
          >
            How it works
          </a>
        </div>

        <h2 id="how-it-works" className="mt-10 text-lg font-semibold">
          How it works
        </h2>
        <ol className="mt-3 list-decimal space-y-1.5 pl-5 text-sm text-[var(--color-ink-2)]">
          <li>Choose a template below and read what a human still does and what it needs.</li>
          <li>Press Copy, and paste the instruction into your own coding agent.</li>
          <li>Your coding agent builds the agent, in your own repository, on your own credentials.</li>
        </ol>
        <ToolSelector />
      </div>

      <h2 id="templates" className="mt-10 text-lg font-semibold">
        Templates ({templates.length})
      </h2>
      {templates.length === 0 ? (
        <div className="mt-3">
          <Strip tone="info">No template has passed its witnessed dry run yet.</Strip>
        </div>
      ) : (
        <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {templates.map((t) => (
            <TemplateCard key={t.slug} t={t} />
          ))}
        </div>
      )}

      <div className="mt-10 max-w-[46rem]">
        <h2 className="text-lg font-semibold">What follows</h2>
        {/* T-78: the fixed funnel sentence, identical on all four surfaces, placed next to the
            four steps it summarises - and the one descriptive, lowercase use of "incubator" this
            page is allowed (Fable ruling). No new /apply/ link here: FunnelStrip below already
            carries the page's one permitted link to it (test_build_funnel_strip_once.py). */}
        <p className="mt-3 text-sm text-[var(--color-ink-2)]">
          {FUNNEL_SENTENCE} {INCUBATOR_SENTENCE}
        </p>
        <dl className="mt-3 space-y-3 text-sm text-[var(--color-ink-2)]">
          <div>
            <dt className="font-medium text-[var(--color-ink)]">01 &mdash; An agent, in your repository</dt>
            <dd>Built by your own coding agent, from the instruction you copied.</dd>
          </div>
          <div>
            <dt className="font-medium text-[var(--color-ink)]">02 &mdash; One business operation it runs without you</dt>
            <dd>Not a chat assistant: the operation the template names, with the human points it names too.</dd>
          </div>
          <div>
            <dt className="font-medium text-[var(--color-ink)]">03 &mdash; A passport, if you request one and the repository is public</dt>
            <dd>An independent measurement of how much runs without a human, including what could not be measured.</dd>
          </div>
          <div>
            <dt className="font-medium text-[var(--color-ink)]">04 &mdash; An Order link in the registry</dt>
            <dd>Once a passport for it declares where customers order from you.</dd>
          </div>
        </dl>
      </div>

      <div className="mt-8 max-w-[46rem]">
        <FunnelStrip />
      </div>
    </Page>
  );
}
