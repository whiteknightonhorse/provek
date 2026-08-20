/** The load-bearing screen (decision D-01).
 *
 * A consumer of evidence arrives here by a link from an email or a due-diligence memo and has
 * never seen the landing page. So this page must stand alone, and it must still be readable a
 * year from now - which is why provenance and protocol version are ON the page rather than in
 * metadata. */

import { Facts, Page, Strip } from "../components/Chrome";
import { AbsentMark, LevelRail, Projection } from "../components/Measured";
import type { Passport as P } from "../types";

const OP_LABEL: Record<string, string> = {
  development_initiation: "Development initiation",
  deployment: "Deployment",
  treasury_control: "Treasury control",
};

const OP_DESC: Record<string, string> = {
  development_initiation:
    "Who starts and lands changes to the running system, and whether that requires a human.",
  deployment: "Who ships a change to production, and whether a human approves each one.",
  treasury_control: "Who can move funds, change destinations, or alter spending rules.",
};

export default function Passport({ p }: { p: P }) {
  const v = p.verified;
  const affiliated = p.verifier_affiliation === "same_owner";
  const unmeasured = v.operations.filter((o) => !o.measured).length;

  return (
    <Page>
      <nav className="text-xs text-[var(--color-ink-3)] mb-3">
        <a href="#/registry" className="text-[var(--color-accent)] hover:underline">Registry</a>
        <span className="mx-1.5">›</span>
        <span>{p.subject_id}</span>
      </nav>

      <h1 className="text-2xl font-semibold tracking-tight break-all">{p.subject_id}</h1>

      {/* Provenance is the second thing on the page, as in SSL Labs and Scorecard. */}
      <p className="mt-1.5 text-xs text-[var(--color-ink-3)]">
        Issued {p.issued_at.slice(0, 19).replace("T", " ")} UTC &nbsp;|&nbsp; valid until{" "}
        {p.valid_until.slice(0, 10)} &nbsp;|&nbsp; protocol {p.provenance.protocol_version}{" "}
        &nbsp;|&nbsp; profile {p.provenance.profile_version} &nbsp;|&nbsp; evidence window{" "}
        {p.provenance.evidence_window_days} days
      </p>

      {affiliated && (
        <div className="mt-3">
          <Strip tone="warn">
            <strong>Affiliated verification.</strong> The subject and the verifier&rsquo;s owner are
            the same party. This record is a rehearsal of the protocol, not an independent
            verification, and it is marked so rather than left to be assumed.
          </Strip>
        </div>
      )}

      {/* Verdict block: number plus the dimensions it is made of. */}
      <section className="mt-6 bg-[var(--color-paper)] border border-[var(--color-line)]">
        <div className="grid gap-6 p-5 md:grid-cols-[minmax(14rem,18rem)_1fr]">
          <div>
            <h2 className="text-xs uppercase tracking-wide text-[var(--color-ink-2)]">
              Autonomy projection
            </h2>
            <div className="mt-2">
              <Projection value={v.projection} absentReason={v.projection_absent_reason} />
            </div>
            {/* D-02: the caveat sits beside the number, not in a footnote. A caveat that must be
                hunted for is a caveat that was not given - and a screenshot is how this page gets
                quoted. */}
            <p className="mt-3 text-xs leading-relaxed text-[var(--color-ink-2)] border-l-2 border-[var(--color-line-2)] pl-3">
              Measures <strong>autonomy</strong>. Not reliability, not decision quality, not
              profitability, and not the presence of an accountable party.
            </p>
          </div>

          <div>
            <h2 className="text-xs uppercase tracking-wide text-[var(--color-ink-2)]">
              Per operation
            </h2>
            <p className="mt-1 text-xs text-[var(--color-ink-3)]">
              A level is assigned to an operation, never to a company. A single number for a whole
              company is a marketing number.
            </p>
            <ul className="mt-3 divide-y divide-[var(--color-line)] border-t border-[var(--color-line)]">
              {v.operations.map((o) => (
                <li key={o.operation} className="flex gap-4 py-3">
                  <LevelRail level={o.level} measured={o.measured} />
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-baseline gap-2">
                      <span className="font-medium">{OP_LABEL[o.operation] ?? o.operation}</span>
                      {!o.measured && <AbsentMark reason={o.level} />}
                    </div>
                    <p className="mt-0.5 text-sm text-[var(--color-ink-2)]">
                      {OP_DESC[o.operation] ?? ""}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
            {unmeasured > 0 && (
              <p className="mt-3 text-xs text-[var(--color-ink-3)]">
                {unmeasured} of {v.operations.length} operations are not measured. Runtime evidence
                is not collected at this stage, and the passport says so rather than scoring them
                zero.
              </p>
            )}
          </div>
        </div>
      </section>

      {/* Accountability - adjacent to the score, visibly NOT part of it (decision D-03 sibling). */}
      <section className="mt-6">
        <h2 className="text-sm font-semibold">Accountability</h2>
        <p className="mt-1 text-xs text-[var(--color-ink-3)] max-w-[46rem]">
          Deliberately outside the score. The ladder measures how little a human is required; it says
          nothing about who answers when something goes wrong. An empty control map yields maximum
          autonomy <em>and</em> an honest &ldquo;no addressee&rdquo; &mdash; both truths side by side.
        </p>
        <div className="mt-3 bg-[var(--color-paper)] border border-[var(--color-line)] px-5 py-1">
          <Facts
            rows={[
              ["Emergency stop", p.accountability.emergency_stop === null
                ? <AbsentMark reason={null} />
                : p.accountability.emergency_stop ? "present" : "none"],
              ["Claims addressee", p.accountability.claims_addressee ?? (
                <span className="text-[var(--color-ink-2)]">none &mdash; stated, not hidden</span>
              )],
              ["Insurance", p.accountability.insurance ?? <span className="text-[var(--color-ink-2)]">none</span>],
              ["Dispute path", p.accountability.dispute_path ?? <span className="text-[var(--color-ink-2)]">none</span>],
            ]}
          />
        </div>
      </section>

      {/* Identity binding strength - D-11. */}
      <section className="mt-6">
        <h2 className="text-sm font-semibold">Identity binding</h2>
        <div className="mt-3 bg-[var(--color-paper)] border border-[var(--color-line)] px-5 py-1">
          <Facts
            rows={[
              ["Binding", <code className="font-mono text-xs">{p.subject_id}</code>],
              ["Strength", p.binding_strength === "strong"
                ? <span style={{ color: "var(--color-pass)" }}>strong</span>
                : <span style={{ color: "var(--color-warn)" }}>weak</span>],
              ["Properties", p.binding_flags.join(", ") || "—"],
              ["Why it matters", <span className="text-[var(--color-ink-2)]">
                A domain expires and can be resold; a signing key rotates. Equating either with
                ownership of a token would overstate what the binding guarantees.
              </span>],
            ]}
          />
        </div>
      </section>

      {/* Control map coverage - the map proves a path exists, never that none was missed. */}
      <section className="mt-6">
        <h2 className="text-sm font-semibold">Human control map &mdash; coverage</h2>
        <p className="mt-1 text-xs text-[var(--color-ink-3)] max-w-[46rem]">
          This map can prove that a control path <em>exists</em>. It can never prove that no
          undiscovered path exists &mdash; that is impossible in principle, so the map publishes what
          it inspected and what it could not reach.
        </p>
        <div className="mt-3 bg-[var(--color-paper)] border border-[var(--color-line)] px-5 py-1">
          <Facts
            rows={[
              ["Inspected", v.coverage.inspected.join(", ") || "—"],
              ["Out of reach", Object.entries(v.coverage.out_of_reach).length === 0 ? "—" : (
                <ul className="space-y-0.5">
                  {Object.entries(v.coverage.out_of_reach).map(([k, why]) => (
                    <li key={k}>
                      <span className="font-mono text-xs">{k}</span>
                      <span className="text-[var(--color-ink-3)]"> &mdash; {why}</span>
                    </li>
                  ))}
                </ul>
              )],
              ["An undiscovered path would look like", <span className="text-[var(--color-ink-2)]">{v.coverage.unknown_shape}</span>],
              ["Level ceiling implied by the map", v.control_map_cap === null
                ? <AbsentMark reason={null} />
                : `L${v.control_map_cap}`],
            ]}
          />
        </div>
      </section>

      {/* Self-reported lives in its own branch, visually and structurally (D-02 sibling, ABI-14-2). */}
      <section className="mt-6">
        <h2 className="text-sm font-semibold">
          Self-reported <span className="font-normal text-[var(--color-ink-3)]">&mdash; claimed by the subject, not verified by us</span>
        </h2>
        <div className="mt-3 border border-dashed border-[var(--color-line-2)] bg-[var(--color-paper-2)] px-5 py-1">
          <Facts
            rows={Object.entries(p.self_reported).map(([k, val]) => [k, String(val)])}
          />
        </div>
      </section>

      {/* PHASE 2 SLOT: task history. Hidden while empty rather than absent from the layout. */}
      {false && <section className="mt-6" aria-hidden="true" />}
    </Page>
  );
}
