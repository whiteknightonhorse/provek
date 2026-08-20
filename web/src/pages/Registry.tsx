/** The listing. Dense, plain, and honest about its size (decision D-04).
 *
 * Eight rows exist. All are affiliated. We do not invent companies to fill the table: fabricated
 * entries in a trust registry would be precisely the thing this product exists to expose. So the
 * near-empty state is designed rather than apologised for. */

import { useMemo, useState } from "react";
import { Page, Strip } from "../components/Chrome";
import { AbsentMark } from "../components/Measured";
import { slug } from "../types";
import type { Registry as R } from "../types";

function shortId(id: string) {
  const i = id.indexOf("/");
  return i === -1 ? id : id.slice(i + 1);
}

export default function Registry({ reg }: { reg: R }) {
  const [q, setQ] = useState("");
  const rows = useMemo(
    () => reg.subjects.filter((s) => s.subject_id.toLowerCase().includes(q.toLowerCase())),
    [reg.subjects, q],
  );

  return (
    <Page>
      <h1 className="text-2xl font-semibold tracking-tight">Registry</h1>
      <p className="mt-1 text-sm text-[var(--color-ink-2)] max-w-[46rem]">
        Every business that has been measured, with the evidence behind each verdict. Generated{" "}
        {reg.generated_at.slice(0, 19).replace("T", " ")} UTC.
      </p>

      {/* The honest state, stated as method rather than apology. */}
      <div className="mt-5 space-y-2">
        <Strip tone="info">
          <strong>{reg.count} records.</strong> All of them are the operator&rsquo;s own systems,
          marked as affiliated. A registry of trust that padded itself with invented entries would be
          doing the exact thing it exists to detect, so it stays this size until real subjects grant
          a mandate.
        </Strip>
      </div>

      <div className="mt-6 flex flex-wrap items-baseline justify-between gap-3">
        <label className="flex items-center gap-2 text-sm">
          <span className="text-[var(--color-ink-2)]">Filter</span>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="subject"
            className="border border-[var(--color-line-2)] bg-[var(--color-paper)] px-2.5 py-1.5 text-sm w-56"
          />
        </label>
        {/* Filtering changes the table silently for anyone not watching it. The count is the only
            thing that says how much of the registry is now hidden, so it has to be announced. */}
        <p aria-live="polite" className="text-sm text-[var(--color-ink-3)] tabular-nums">
          {rows.length === reg.count ? `${reg.count} of ${reg.count}` : `${rows.length} of ${reg.count}`}
        </p>
      </div>

      <div className="mt-3 overflow-x-auto bg-[var(--color-paper)] border border-[var(--color-line)]">
        <table className="stack-table w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--color-line-2)] text-left">
              <th scope="col" className="px-4 py-2.5 font-semibold">Subject</th>
              <th scope="col" className="px-4 py-2.5 font-semibold">Status</th>
              <th scope="col" className="px-4 py-2.5 font-semibold">Autonomy</th>
              <th scope="col" className="px-4 py-2.5 font-semibold">Verifier</th>
              <th scope="col" className="px-4 py-2.5 font-semibold">Valid until</th>
              {/* PHASE 2 SLOT (decision D-05): reserved, empty, unannounced. Retrofitting a column
                  into a finished table changes widths, breakpoints and scan patterns - that is a
                  redesign, not an addition. */}
              <th scope="col" className="px-4 py-2.5" aria-hidden="true" />
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--color-line)]">
            {rows.map((s) => (
              <tr key={s.subject_id} className="hover:bg-[var(--color-paper-2)]">
                <td className="px-4 py-2.5">
                  <a
                    href={`/p/${slug(s.subject_id)}/`}
                    className="text-[var(--color-accent)] hover:underline"
                  >
                    {shortId(s.subject_id)}
                  </a>
                  <div className="text-xs text-[var(--color-ink-3)] font-mono">{s.subject_id}</div>
                </td>
                <td data-label="Status" className="px-4 py-2.5">{s.status}</td>
                <td data-label="Autonomy" className="px-4 py-2.5 tabular-nums">
                  {s.projection === null ? (
                    <AbsentMark reason={s.projection_absent_reason} />
                  ) : (
                    <span>{s.projection} <span className="text-[var(--color-ink-3)]">/ 100</span></span>
                  )}
                </td>
                <td data-label="Verifier" className="px-4 py-2.5">
                  {/* From the row, not from this template (Fable, R4). The literal used to be
                      printed into every line, which is true while every subject is the operator's
                      own and becomes a false accusation the moment one is not. */}
                  {s.verifier_affiliation === "same_owner" ? (
                    <span style={{ color: "var(--color-warn)" }}>affiliated</span>
                  ) : (
                    <span className="text-[var(--color-ink-2)]">independent</span>
                  )}
                </td>
                <td data-label="Valid until" className="px-4 py-2.5 tabular-nums">{s.valid_until.slice(0, 10)}</td>
                <td className="px-4 py-2.5" />
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-[var(--color-ink-3)]">
                  Nothing matches &ldquo;{q}&rdquo;. The registry holds {reg.count} records in total.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p className="mt-4 text-xs text-[var(--color-ink-3)] max-w-[46rem]">{reg.disclaimer}</p>
    </Page>
  );
}
