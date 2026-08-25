/** The load-bearing screen (decision D-01).
 *
 * A consumer of evidence arrives here by a link from an email or a due-diligence memo and has
 * never seen the landing page. So this page must stand alone, and it must still be readable a
 * year from now - which is why provenance and protocol version are ON the page rather than in
 * metadata. */

import { Facts, Page, Strip } from "../components/Chrome";
import { AbsentMark, LevelRail, Projection } from "../components/Measured";
import { daysUntil, effectiveStatus } from "../types";
import type { Fact, Passport as P } from "../types";

const OBS_LABEL: Record<string, string> = {
  signed_commit_share: "Share of commits with a verified signature",
  distinct_authors: "Distinct commit authors",
  bot_author_share: "Share of commits from bot or app accounts",
  workflow_runs: "Automated CI runs observed",
  head_sha: "Commit the reading was taken at",
};

const OP_LABEL: Record<string, string> = {
  development_initiation: "Development initiation",
  deployment: "Deployment",
  treasury_control: "Treasury control",
};

/** Every limiter the scorer can apply, in the reader's language.
 *
 * SPEC 3.1 item 3 requires "which limiters were applied". A code alone is a citation to a document
 * the reader does not have; an unrecognised code still prints raw rather than being swallowed. */
const LIMITER_TEXT: Record<string, string> = {
  "O1:mixed_classes->inferred":
    "evidence of mixed forgery cost, so this level is inferred rather than measured",
  "O2:no_runtime_trace->capped_L2":
    "no runtime trace, so the level is capped at L2 whatever the repository suggests",
  "O3:contradicts_claim->claim_rejected":
    "the subject claimed a higher level than the evidence supports; the claim was rejected",
  control_map_cap:
    "a human control path exists, so the level cannot exceed what the map allows",
};

const OP_DESC: Record<string, string> = {
  development_initiation:
    "Who starts and lands changes to the running system, and whether that requires a human.",
  deployment: "Who ships a change to production, and whether a human approves each one.",
  treasury_control: "Who can move funds, change destinations, or alter spending rules.",
};

/** One accountability field.
 *
 * Three renderings for three states, because there are three. A measured absence says who looked;
 * an unmeasured field says nobody did and why. Under schema 1.0.0 this component had to guess,
 * and guessed differently in adjacent rows - which is what exposed the schema defect. */
function AccFact({ f, yes, no }: { f: Fact; yes?: string; no?: string }) {
  if (!f.measured) return <AbsentMark reason={f.reason} />;
  // The register travels with the value (V4). These fields are self-declared by construction, so
  // `assumed` is the usual answer and saying so is the difference between "the subject states" and
  // "we checked" - which the previous copy, "established, not assumed", got exactly backwards.
  const register =
    f.confidence === "assumed" ? (
      <span className="evidence-class ml-2" title="Taken from the subject's own declaration; not independently verified.">
        self-declared
      </span>
    ) : f.confidence ? (
      <span className="evidence-class ml-2">{f.confidence}</span>
    ) : null;
  if (f.value === null)
    return (
      <span className="text-[var(--color-ink-2)]">
        {no ?? "none"} &mdash; stated, not omitted{register}
      </span>
    );
  return (
    <span>
      {f.value === true ? (yes ?? "present") : String(f.value)}
      {register}
    </span>
  );
}

export default function Passport({ p }: { p: P }) {
  const v = p.verified;
  const affiliated = p.verifier_affiliation === "same_owner";
  const unmeasured = v.operations.filter((o) => !o.measured).length;

  return (
    <Page>
      <nav className="text-xs text-[var(--color-ink-3)] mb-3">
        <a href="/registry/" className="text-[var(--color-accent)] hover:underline">Registry</a>
        <span className="mx-1.5">›</span>
        <span>{p.subject_id}</span>
      </nav>

      <h1 className="text-2xl font-semibold tracking-tight break-all">{p.subject_id}</h1>

      {/* Provenance is the second thing on the page, as in SSL Labs and Scorecard. */}
      <p className="mt-1.5 text-xs text-[var(--color-ink-3)]">
        Issued {p.issued_at.slice(0, 19).replace("T", " ")} UTC &nbsp;|&nbsp; valid until{" "}
        {p.valid_until.slice(0, 10)}
        {daysUntil(p.valid_until) > 0 && (
          <span className="text-[var(--color-ink-3)]"> ({daysUntil(p.valid_until)} days)</span>
        )} &nbsp;|&nbsp; protocol {p.provenance.protocol_version}{" "}
        &nbsp;|&nbsp; profile {p.provenance.profile_version} &nbsp;|&nbsp; evidence window{" "}
        {p.provenance.evidence_window_days} days
      </p>

      {/* THE SHARED THESIS, M's reading of it: coverage as a sentence, not a chart. A bar that
          restates a number beside it is decoration; a count of what was measured is the fact. */}
      {/* BINDING STRENGTH SITS WITH THE VERDICT (A3, spec 2.8: "the buyer sees the strength of the
          foundation TOGETHER WITH the verdict"). It used to appear six blocks down, after
          accountability - by which point a reader has already formed a view of the number without
          knowing that the identity under it is revocable. Fable upgraded this from taste to
          requirement, and he is right: a weak binding changes how everything below it reads. */}
      <p className="mt-3 text-sm">
        <span
          className="evidence-class"
          title={
            p.binding_strength === "strong"
              ? "The identity is bound by something that cannot be quietly reassigned."
              : "A domain expires and can be resold; a signing key rotates."
          }
        >
          {p.binding_strength} identity binding
        </span>
        <span className="mx-2 text-[var(--color-line-2)]">·</span>
        {/* THE DOCUMENT'S OWN STATUS, which this page never stated (Fable). A reader who clicked
            "unverified" in the registry arrived at a page showing a binding, a validity date and a
            control map, with no word about what the document itself is - and "valid until, 30 days"
            on an unverified record invites the question: valid as what? */}
        <span className="evidence-class">{effectiveStatus(p.status, p.valid_until)}</span>
        <span className="mx-2 text-[var(--color-line-2)]">·</span>
        <strong className="font-medium">
          {v.operations.length - unmeasured} of {v.operations.length} operations measured.
        </strong>{" "}
        <span className="text-[var(--color-ink-2)]">
          {unmeasured === 0
            ? "Every operation on this subject carries evidence."
            : "The rest are stated as unmeasured, with the reason, rather than scored as zero."}
        </span>
      </p>

      {/* A2. A verdict lapses by time with no event, and until now the surface never said so. */}
      {effectiveStatus(p.status, p.valid_until) === "stale" && (
        <div className="mt-3">
          <Strip tone="warn">
            <strong>This passport has lapsed.</strong> Its evidence window closed on{" "}
            {p.valid_until.slice(0, 10)} and it has not been renewed. Nothing below is retracted —
            it was true when measured — but a verdict has a shelf life, and a reader deciding today
            should know they are reading a record rather than a current statement.
          </Strip>
        </div>
      )}

      {/* THE RULE, stated where a visitor meets its consequence. It lived in a code comment and in
          a hover title - invisible on a phone - so four rows read as four failures instead of as
          the method working. */}
      {v.projection === null && v.projection_absent_reason === "unreadable" && (
        <div className="mt-3">
          <Strip tone="info">
            <strong>This subject has not presented itself publicly.</strong> The repository does not
            answer a reader holding no credential, so nothing here could be measured. We hold a
            credential that would read it &mdash; and deliberately did not use one, because evidence
            only we can reach is not evidence anyone else can recompute, and a verdict nobody can
            check is worth nothing. This record stays as it is until the subject opens the source or
            offers a channel that anyone could use.
          </Strip>
        </div>
      )}

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
                      {/* SPEC 3.1 item 3 requires confidence and the limiters applied. They were
                          computed and then dropped at the emission boundary, so every level in the
                          registry - all of them O1-limited - rendered exactly like a measured one
                          (Fable, R3). A published number stronger than the measured one is the
                          overstatement this product exists to prevent. */}
                      {o.measured && o.confidence === "inferred" && (
                        <span className="evidence-class" title="">inferred</span>
                      )}
                      {!o.measured && <AbsentMark reason={o.level} />}
                    </div>
                    <p className="mt-0.5 text-sm text-[var(--color-ink-2)]">
                      {OP_DESC[o.operation] ?? ""}
                    </p>
                    {o.limiters_applied.length > 0 && (
                      <ul className="mt-1.5 space-y-0.5">
                        {o.limiters_applied.map((lim) => (
                          <li key={lim} className="text-xs text-[var(--color-ink-3)]">
                            <span className="font-mono">{lim.split(":")[0]}</span>{" "}
                            {LIMITER_TEXT[lim] ?? lim}
                          </li>
                        ))}
                      </ul>
                    )}
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
          nothing about who answers when something goes wrong, so an empty control map can yield
          maximum autonomy and no addressee at once &mdash; both truths side by side.
          {Object.values(p.accountability).every((f) => !f.measured) && (
            <>
              {" "}
              <em>
                Nothing here has been inspected yet. That is why every row reads not measured rather
                than none: a field nobody looked at is not a business without an answer.
              </em>
            </>
          )}
        </p>
        <div className="mt-3 bg-[var(--color-paper)] border border-[var(--color-line)] px-5 py-1">
          <Facts
            rows={[
              ["Emergency stop", <AccFact f={p.accountability.emergency_stop} yes="present" no="none" />],
              ["Claims addressee", <AccFact f={p.accountability.claims_addressee} />],
              ["Insurance", <AccFact f={p.accountability.insurance} />],
              ["Dispute path", <AccFact f={p.accountability.dispute_path} />],
            ]}
          />
        </div>
      </section>

      {/* THE OBSERVATIONS. The site claims it publishes the evidence behind every number, and until
          now it published the conclusion and its caveats but never the inputs. These are the raw
          measured quantities the level was built from, each keeping its own absence state. */}
      {Object.keys(v.observations || {}).length > 0 && (
        <section className="mt-6">
          <h2 className="text-sm font-semibold">What was actually observed</h2>
          <p className="mt-1 text-xs text-[var(--color-ink-3)] max-w-[46rem]">
            The quantities the level above was computed from. They are published so the verdict can
            be recomputed rather than believed &mdash; and so a reader who disagrees with the
            reasoning can say where.
          </p>
          <div className="mt-3 bg-[var(--color-paper)] border border-[var(--color-line)] px-5 py-1">
            <Facts
              rows={Object.entries(v.observations).map(([key, o]) => [
                OBS_LABEL[key] ?? key,
                typeof o === "string" || o === null ? (
                  <span className="font-mono text-xs">{o ?? "—"}</span>
                ) : o.measured ? (
                  <span className="tabular-nums">{o.value}</span>
                ) : (
                  <AbsentMark reason={o.absent_reason} />
                ),
              ])}
            />
          </div>
        </section>
      )}

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
              /* THIS ROW READ `L5` AND THAT WAS A CLAIM THE MAP CANNOT MAKE. `implied_level_cap`
                 returns 5 for "no limiting path was found", and the row printed it as a settled
                 ceiling three paragraphs under the map's own sentence that it "can never prove
                 that no undiscovered path exists". On the page for a subject whose coverage
                 lists three of four surfaces as out of reach, a bare L5 reads as "maximum
                 autonomy permitted" when what happened is that nobody could look.
                 The value is unchanged; what it says about itself is not. A ceiling of 5 over
                 partial coverage is stated as no ceiling FROM WHAT WAS INSPECTED, which is the
                 whole of what was measured. */
              ["Level ceiling implied by the map",
                v.control_map_cap === null
                  ? <AbsentMark reason={null} />
                  : v.control_map_cap === 5 && Object.keys(v.coverage.out_of_reach ?? {}).length > 0
                    ? <span>none &mdash; no limiting path was found <em>among the surfaces that
                        were inspected</em>. Surfaces out of reach cannot raise this ceiling and
                        cannot confirm it.</span>
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
      {/* PHASE 2 (task history) has no reserved element here on purpose. A `{false && ...}`
          placeholder used to sit in this spot with a comment claiming the section was "hidden
          while empty" - it was absent from the layout entirely, so the comment described
          something that did not exist (Fable, I5). Reserving vertical space for a feature that
          may never ship would also push the control map further from the score that constrains
          it. When task history ships it takes its place in the block order, which is a decision
          to be recorded then. */}
    </Page>
  );
}
