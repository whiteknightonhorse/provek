/** `/build/<slug>/` - one AI agent template, in progressive disclosure (ADR-0011 section 5.2). */
import { useState } from "react";
import { Page } from "../components/Chrome";
import { CopyButton } from "../components/CopyButton";
import { FunnelStrip } from "../components/FunnelStrip";
import type { Template } from "../types";

const TOOLS = ["Claude Code", "Codex", "Cursor", "Other"] as const;
type Tool = (typeof TOOLS)[number];

const WHERE_TO_PASTE: Record<Tool, string> = {
  "Claude Code": "Paste it into a Claude Code conversation, or save it under a project's own skills folder and reference it by name.",
  Codex: "Paste it into a Codex conversation, or add it to your project's AGENTS.md so Codex reads it automatically.",
  Cursor: "Paste it into Cursor's chat, or save it as a rules file under .cursor/ and reference it.",
  Other: "Paste it into any coding agent that can create files and run shell commands - the instruction names what it needs from the agent, not which one.",
};

function ToolSelector() {
  const [active, setActive] = useState<Tool | null>(null);
  return (
    <div className="mt-3">
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
            className={(active !== null && active !== t ? "hidden " : "") + "text-sm text-[var(--color-ink-2)]"}
          >
            {WHERE_TO_PASTE[t]}
          </p>
        ))}
      </div>
    </div>
  );
}

const SOURCE_ID = (slug: string) => `skill-source-${slug}`;

/** The copy payload is read from the page's own `<pre>` node at click time, never from a second
 * string carried in the bundle (SPEC 3.7 item 7, `LAW-COPY-IS-THE-ARTEFACT`) - the same node
 * `tests/test_template_copy_is_the_artefact.py` compares against the source file and the raw
 * sibling. Both the layer-1 button and the layer-4 button read the identical node. */
function fromSourceNode(slug: string): string {
  return document.getElementById(SOURCE_ID(slug))?.textContent ?? "";
}

function issueUrl(t: Template): string {
  const title = encodeURIComponent(`Template: ${t.title}`);
  const body = encodeURIComponent(
    `Template: ${t.slug}\nSKILL.md sha256: ${t.bodySha256}\n\nWhat's wrong:\n`,
  );
  return `https://github.com/whiteknightonhorse/provek/issues/new?title=${title}&labels=template&body=${body}`;
}

export default function BuildTemplate({ t }: { t: Template }) {
  return (
    <Page>
      <nav className="text-xs text-[var(--color-ink-3)] mb-3">
        <a href="/build/" className="text-[var(--color-accent)] hover:underline">Build</a>
        <span className="mx-1.5">&rsaquo;</span>
        <span>{t.title}</span>
      </nav>

      <div className="max-w-[46rem]">
        <h1 className="text-2xl font-semibold tracking-tight">{t.title}</h1>
        <p className="mt-1.5 text-sm text-[var(--color-ink-2)]">{t.businessOperation}</p>
        <p className="mt-1 text-xs text-[var(--color-ink-3)]">For {t.forWhom}</p>

        <dl className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 text-sm">
          <div className="border border-[var(--color-line)] bg-[var(--color-paper)] px-3 py-2.5">
            <dt className="text-xs text-[var(--color-ink-2)]">Human still does</dt>
            <dd className="mt-1">{t.humanRemainsFor}</dd>
          </div>
          <div className="border border-[var(--color-line)] bg-[var(--color-paper)] px-3 py-2.5">
            <dt className="text-xs text-[var(--color-ink-2)]">Needs</dt>
            <dd className="mt-1">{t.requires}</dd>
          </div>
        </dl>

        <p className="mt-3 text-xs text-[var(--color-ink-3)]">{t.dryRun.line}</p>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <CopyButton
            getText={() => fromSourceNode(t.slug)}
            idleLabel="Copy"
            className="inline-flex items-center border border-[var(--color-ink)] bg-[var(--color-ink)] px-4 py-2 text-sm font-medium text-[var(--color-paper)] hover:opacity-90"
          />
        </div>
        <ToolSelector />

        <h2 className="mt-8 text-lg font-semibold">What it does</h2>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">{t.description}</p>

        <h2 className="mt-6 text-lg font-semibold">What you get</h2>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          A codebase your coding agent builds and tests in your own repository, that runs{" "}
          {t.businessOperation}, with {t.humanRemainsFor.toLowerCase()} staying with a human.
        </p>

        <h2 className="mt-8 text-lg font-semibold">The full instruction, section by section</h2>
        <div className="mt-3 divide-y divide-[var(--color-line)] border-y border-[var(--color-line)]">
          {t.sections.map((s) => (
            <details key={s.heading} className="py-3">
              <summary className="cursor-pointer text-sm font-medium">{s.heading}</summary>
              <div
                className="mt-1 max-w-none"
                dangerouslySetInnerHTML={{ __html: s.html }}
              />
            </details>
          ))}
        </div>

        <details className="mt-6">
          <summary className="cursor-pointer text-sm font-medium">Show the whole instruction</summary>
          <pre
            id={SOURCE_ID(t.slug)}
            className="mt-3 overflow-x-auto border border-[var(--color-line)] bg-[var(--color-paper-2)] p-4 text-xs font-mono whitespace-pre-wrap"
          >
            {t.raw}
          </pre>
        </details>

        <h2 className="mt-8 text-lg font-semibold">Questions</h2>
        <dl className="mt-3 space-y-4 text-sm">
          {t.faq.map((f) => (
            <div key={f.q}>
              <dt className="font-medium">{f.q}</dt>
              <dd className="mt-1 text-[var(--color-ink-2)]">{f.a}</dd>
            </div>
          ))}
        </dl>

        <p className="mt-6 text-sm">
          <a href={issueUrl(t)} className="text-[var(--color-accent)] hover:underline">
            Something wrong with this template? Open an issue
          </a>
        </p>

        <div className="mt-4">
          <FunnelStrip />
        </div>

        <p className="mt-6 text-sm">
          <a href="/build/" className="text-[var(--color-accent)] hover:underline">
            Back to all templates
          </a>
        </p>
      </div>
    </Page>
  );
}
