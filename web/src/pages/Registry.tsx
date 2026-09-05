/** The listing. Dense, plain, and honest about its size (decision D-04).
 *
 * Eight rows exist. All are affiliated. We do not invent companies to fill the table: fabricated
 * entries in a trust registry would be precisely the thing this product exists to expose. So the
 * near-empty state is designed rather than apologised for. */

import { useMemo, useState } from "react";
import { Page, Strip } from "../components/Chrome";
import { AbsentMark } from "../components/Measured";
import { effectiveStatus, orderAbsentReason, orderLinkUrl, slug } from "../types";
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
        {/* "Every business that has been MEASURED" sat directly above four rows whose entire
            content is that measurement did not happen. The registry lists what was SUBMITTED to
            the method, and what the method could establish about each - which is a different and
            truer sentence. */}
        Every business submitted to the method, what could be established about each, and the
        evidence behind it &mdash; and, once verified, where you can order from them. Generated
        {" "}
        {reg.generated_at.slice(0, 19).replace("T", " ")} UTC.
      </p>

      {/* Corrections log (phase-2 plan): all errata live at /registry/corrections/, in full and
          unabridged - this is a POINTER, not a summary of what they said. Reproducing their text
          here as well would be the same rule written in two places (LAW #ONE-PLACE); the full,
          byte-for-byte originals live at the one address, held to that by
          `tests/test_registry_corrections.py`. */}
      <div className="mt-5">
        <Strip tone="warn">
          Three corrections are on record for this registry.{" "}
          <a href="/registry/corrections/" className="text-[var(--color-accent)] hover:underline">
            All corrections (3) →
          </a>
        </Strip>
      </div>

      {/* THE SUMMARY STRIP WAS REMOVED 2026-08-25 at the operator's instruction: it was a wall
          of prose above the table it described, and the reader came here for the table. Nothing
          it said is lost -- the affiliation of every row is a column, and an unmeasured row
          states its own reason where the number would be. A count of them belongs to whoever
          wants to count, not to everyone who opens the page. */}

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
              {/* T-76 ruling (Fable, 2026-09-05): `generated_at` above is ONE date for the whole
                  document; a row carried forward unread keeps an OLDER `issued_at` while every
                  other row's is fresh. Printing only `generated_at` would report a carried-forward
                  row as measured today - a third world beside "verified" and "not measured", and
                  the one this column exists to name honestly rather than silently. */}
              <th scope="col" className="px-4 py-2.5 font-semibold">Measured</th>
              <th scope="col" className="px-4 py-2.5 font-semibold">Valid until</th>
              {/* PHASE 2 SLOT (decision D-05), FILLED: the Provider Catalog's "Order" link
                  (specification 4.2-bis point 3). The predicate is `orderLinkUrl` - code, not this
                  page's own opinion - and a row that fails it shows WHY, never an empty cell. */}
              <th scope="col" className="px-4 py-2.5 font-semibold">
                Order{" "}
                <a
                  href="/method/#the-order-link"
                  className="font-normal text-xs text-[var(--color-accent)] hover:underline whitespace-nowrap"
                >
                  &mdash; how it is decided
                </a>
              </th>
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
                <td data-label="Status" className="px-4 py-2.5">
                  {(() => {
                    const eff = effectiveStatus(s.status, s.valid_until);
                    return eff === "stale" ? (
                      <span style={{ color: "var(--color-warn)" }} title="The evidence window has closed. The verdict was true when issued and has not been renewed.">
                        stale
                      </span>
                    ) : (
                      eff
                    );
                  })()}
                </td>
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
                <td data-label="Measured" className="px-4 py-2.5 tabular-nums">
                  {/* NOT AbsentMark - `issued_at` missing here means "published before this field
                      existed", not one of the named absence reasons that enum carries. NOT
                      staleness either - `valid_until` already says whether the verdict still
                      holds; this says only WHEN it was taken. */}
                  {s.issued_at ? s.issued_at.slice(0, 10) : (
                    <span className="text-[var(--color-ink-3)]">pre-dates this field</span>
                  )}
                </td>
                <td data-label="Valid until" className="px-4 py-2.5 tabular-nums">{s.valid_until.slice(0, 10)}</td>
                <td data-label="Order" className="px-4 py-2.5">
                  {(() => {
                    const url = orderLinkUrl(s.status, s.valid_until, s.service_url, s.service_reachable);
                    return url ? (
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer nofollow"
                        className="text-[var(--color-accent)] hover:underline whitespace-nowrap"
                      >
                        Order ↗
                      </a>
                    ) : (
                      <AbsentMark reason={orderAbsentReason(s.status, s.valid_until, s.service_url, s.service_reachable)} />
                    );
                  })()}
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-[var(--color-ink-3)]">
                  Nothing matches &ldquo;{q}&rdquo;. The registry holds {reg.count} records in total.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* THE ONLY FABRICATED CONTENT ON THIS PAGE, FENCED OFF ON PURPOSE (D-04's rule still
          applies to the real table above - nothing here is a row of it, nothing here is written
          to registry.json, and neither name belongs to a real subject). Its only job is showing
          what an earned Order link looks like before anyone has actually earned one; the "Order"
          mark below is a static span, not a link, so it cannot be crawled or clicked as if it
          led anywhere real. */}
      <div className="mt-6 max-w-[46rem] border border-dashed border-[var(--color-line-2)] bg-[var(--color-paper-2)] px-4 py-3">
        <p className="font-mono text-xs uppercase tracking-wide text-[var(--color-ink-3)]">
          What an earned listing looks like &mdash; sample, not a real subject
        </p>
        <div className="mt-2 flex items-baseline justify-between gap-4 text-sm">
          <span className="flex min-w-0 flex-col gap-0.5">
            <span className="text-[var(--color-accent)]">example-agent</span>
            <span className="font-mono text-xs text-[var(--color-ink-3)]">
              git:example-org/example-agent
            </span>
          </span>
          <span
            aria-hidden="true"
            className="shrink-0 border border-[var(--color-line-2)] px-2.5 py-1 text-xs text-[var(--color-accent)]"
          >
            Order &#8599;
          </span>
        </div>
      </div>

      <p className="mt-4 text-xs text-[var(--color-ink-3)] max-w-[46rem]">{reg.disclaimer}</p>
    </Page>
  );
}
