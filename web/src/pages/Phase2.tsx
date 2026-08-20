/** Phase two, announced as SPECIFIED and never as available.
 *
 * WHY THIS PAGE IS ALLOWED TO EXIST, AND WHAT IT MAY NOT BECOME. D-05 reserves space for phase 2
 * in the layout and forbids announcing a feature that does not exist. That boundary still holds
 * everywhere it was drawn: the registry's trailing column is still empty, the passport's task
 * history is still absent, the corpus nav slot is still disabled. What changed is narrower, and it
 * is recorded as D-16: the phase is DESCRIBED once, on a page of its own, because a specification
 * that constrains what we may build is a fact about the product today, whereas a "commission work"
 * control on a registry row would be an offer.
 *
 * The difference between a description and an offer has to survive a screenshot, because a
 * screenshot is how this page will be quoted. Hence the refusal at the top, the refusal at the
 * bottom, no control anywhere on the page that could be pressed, and no date anywhere in it.
 *
 * Every statement here is taken from SPEC.md section 4.1, "Phase 2 - what it is, and what it is
 * not", which in turn takes it from the project specification. Nothing is added. This is the one
 * page where an invented capability would be indistinguishable from the marketing this product
 * exists to detect, so the rule is stricter here than anywhere else: if a sentence cannot be traced
 * to a paragraph, it is not on the page. */

import { Facts, Page, Strip } from "../components/Chrome";

const SPEC = "https://github.com/whiteknightonhorse/provek/blob/main/SPEC.md";

/** From SPEC.md 4.1. `enforced` means the deployed contract carries the constraint out itself;
 * `evidenced` means it can be shown and argued and nothing more. Presenting the second as the first
 * is forbidden, and the specification puts that obligation on the interface, not only on the schema
 * - which is why the status is a column here rather than a sentence somewhere below.
 *
 * This comment said "makes it impossible" until Fable found it in the source AFTER the same phrase
 * had been corrected on the page. SPEC 4.1 now forbids that upgrade in normative terms, and a
 * comment contradicting the rule it explains is how the next editor learns which one to believe. */
const CONSTRAINTS: Array<[string, "enforced" | "evidenced"]> = [
  ["Ceiling on the amount", "enforced"],
  ["Permitted on-chain recipient", "enforced"],
  ["Release of a milestone against a machine-checkable criterion", "enforced"],
  ["Timeout, and return of whatever was not committed", "enforced"],
  ["“The money was spent on compute”", "evidenced"],
  ["“The work was done well”", "evidenced"],
  ["“The agent did not hand the task to a human”", "evidenced"],
];

/** `rejected` is on the diagram and not only in the sentence about terminal states below it. The
 * specification lists it as terminal while showing no arrow that reaches it, which is a small
 * version of the defect this whole surface exists to catch: a claim with nothing behind it in the
 * artefact. The transition is supplied by the policy gate, which refuses anything missing a
 * condition of creation.
 *
 * The seam that reconstruction leaves, named rather than smoothed over: the specification also says
 * such a task "is not created at all", which cannot both be true and leave it sitting in a terminal
 * state. The reading taken here - a DRAFT is refused at `policy_check` and never becomes a funded
 * task - satisfies both sentences, and it is recorded in SPEC.md 4.1 as a reconstruction rather
 * than presented as quotation. The durable fix belongs in the specification, not on this page. */
const LIFECYCLE = [
  "draft → policy_check → funded → executing",
  "policy_check → rejected                     (a condition of creation is missing)",
  "executing → milestone_released → executing  (partial release)",
  "executing → completed                       (every acceptance criterion met)",
  "executing → failed                          (a failure criterion fired)",
  "executing → timed_out                       (the timeout expired — by time, with no event)",
  "failed | timed_out → settled                (the uncommitted remainder returned by code)",
];

export default function Phase2() {
  return (
    <Page>
      <div className="max-w-[46rem]">
        <h1 className="text-2xl font-semibold tracking-tight">Phase two: funding tasks</h1>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          Specified. Not built. Not open. Everything below describes what the specification requires
          of phase 2 &mdash; it is not a description of anything that runs.
        </p>

        <div className="mt-5 space-y-3">
          <Strip tone="warn">
            <strong>Nothing on this page is in service.</strong> No funding task can be created, no
            work can be commissioned through us, and no application for one is being taken. Phase 2
            is deferred by decision A-10 &mdash; projects first &mdash; because a registry is useful
            without the second side, and the second side is not useful without a registry. Deferred
            is not cancelled: the specification defines phase 2 so that it will not have to be
            designed twice.
          </Strip>
          <Strip tone="info">
            <strong>There is no date here, and there will not be one.</strong> Nothing and nobody has
            committed to a date, so this page may not invent one. A promised date would be exactly
            the thing this product exists to detect: a claim stronger than the artefact behind it.
          </Strip>
        </div>

        <h2 className="mt-9 text-lg font-semibold">Where this sits</h2>
        <ol className="mt-3 space-y-3 text-sm text-[var(--color-ink-2)]">
          <li className="border-l border-[var(--color-line-2)] pl-3.5">
            <strong className="text-[var(--color-ink)]">You ask to be verified.</strong> Nobody is
            assessed who did not ask, and without a mandate nothing in your production is touched.
            This part is open today.
          </li>
          <li className="border-l border-[var(--color-line-2)] pl-3.5">
            <strong className="text-[var(--color-ink)]">A passport is issued.</strong>{" "}
            Machine-readable first: a level for each business operation, the evidence behind each
            level, and the reason for every operation that could not be measured. This part is open
            today.
          </li>
          <li className="border-l border-[var(--color-line-2)] pl-3.5">
            <strong className="text-[var(--color-ink)]">
              In phase 2, a funding task can be addressed to a subject.
            </strong>{" "}
            A customer commissions work, the agent performs it, and the incubator witnesses the fact
            of performance. <strong className="text-[var(--color-ink)]">This part does not exist.</strong>
          </li>
        </ol>
        <p className="mt-3 text-sm text-[var(--color-ink-2)]">
          The order is a dependency, not a sales funnel. Phase 2 stands on the registry, which is
          what decision A-10 means when it says the registry is useful without the second side while
          the reverse is false.
        </p>

        <h2 className="mt-9 text-lg font-semibold">What a funding task is, in the specification</h2>
        <div className="mt-3 bg-[var(--color-paper)] border border-[var(--color-line)] px-5 py-1">
          <Facts
            rows={[
              ["it is", "a contract for services — procurement"],
              [
                "it is not",
                "a grant, a donation, a pre-payment for a share, or an investment contract",
              ],
              ["the funder", "is a customer, and takes delivery of the result"],
              ["a share of revenue", "excluded permanently — not deferred, excluded"],
              // The scope qualifier is load-bearing and was missing here in the first draft. The
              // row above it is permanent (A-3); this one is normative for phase 2.0 only, and the
              // specification marks the difference deliberately. A table that flattens the two
              // would make this page retroactively false the day 2.1 relaxes the norm.
              ["one task, in phase 2.0", "has exactly one principal"],
            ]}
          />
        </div>
        <p className="mt-3 text-sm text-[var(--color-ink-2)]">
          The words <span className="font-mono text-xs">investment</span>,{" "}
          <span className="font-mono text-xs">investor</span>,{" "}
          <span className="font-mono text-xs">equity</span> and{" "}
          <span className="font-mono text-xs">secondary market</span> are forbidden in the product.
          The specification records in the same breath that the prohibition is not itself a legal
          argument: classification follows substance, not vocabulary.
        </p>

        <h2 className="mt-9 text-lg font-semibold">Money never passes through us</h2>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          Decision A-6, and it is permanent rather than deferred &mdash; which is why there is no
          payment step anywhere on this site, not in this phase and not in a later one. We hold and
          route no funds: no escrow, no treasury, no keys. In phase 2 a customer pays the agent
          directly. A commission on transfers is excluded forever.
        </p>
        <p className="mt-3 text-sm text-[var(--color-ink-2)]">
          The milestone contract is deployed by the parties themselves. Our part is to publish the
          template and to hold no key to it. If we deployed that contract and kept an administrative
          key, the custodial risk decision A-6 removed would return through the back door, and
          &ldquo;we are only infrastructure&rdquo; would stop being true.
        </p>
        <p className="mt-3 text-sm text-[var(--color-ink-2)]">
          What we would be paid for, when it exists, is a fixed fee for the witnessing itself
          &mdash; never a share of what passes between the parties.
        </p>

        {/* Fable, on the brief that preceded this page: an unqualified heading over a present-tense
            table reads as documentation of a running machine once a screenshot separates it from
            the refusals at the top and the foot. The qualifier costs three words and travels with
            the fragment. Same for the lifecycle below. */}
        <h2 className="mt-9 text-lg font-semibold">Enforced, or only evidenced &mdash; as specified</h2>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          This is the line where products of this kind most often lie, so the specification requires
          the interface to publish the status of every constraint rather than the constraints alone.{" "}
          <span className="font-mono text-xs">enforced</span> means the deployed contract carries the
          constraint out itself. <span className="font-mono text-xs">evidenced</span> means it can be
          shown and argued, and nothing more. Neither word promises a contract free of defects: the
          template has not been through the review named at the foot of this page.
        </p>
        <ul className="mt-3 divide-y divide-[var(--color-line)] border-y border-[var(--color-line)]">
          {CONSTRAINTS.map(([what, status]) => (
            <li
              key={what}
              className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 py-2.5"
            >
              <span className="text-sm">{what}</span>
              {/* The word carries the fact; the colour only repeats it. DESIGN rule 1. */}
              <span
                className="shrink-0 font-mono text-xs"
                style={{
                  color: status === "enforced" ? "var(--color-pass)" : "var(--color-warn)",
                }}
              >
                {status === "enforced" ? "enforced" : "evidenced only"}
              </span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-sm text-[var(--color-ink-2)]">
          <span className="font-mono text-xs">enforced</span> means enforced by the contract the
          parties deploy between themselves. Not by us: we are not a party to it.
        </p>

        <h2 className="mt-9 text-lg font-semibold">The lifecycle, as specified</h2>
        <div className="mt-3 overflow-x-auto bg-[var(--color-paper)] border border-[var(--color-line)] p-4">
          <pre className="font-mono text-xs leading-relaxed whitespace-pre">
            {LIFECYCLE.join("\n")}
          </pre>
        </div>
        <p className="mt-3 text-sm text-[var(--color-ink-2)]">
          Terminal states are <span className="font-mono text-xs">completed</span>,{" "}
          <span className="font-mono text-xs">settled</span> and{" "}
          <span className="font-mono text-xs">rejected</span>. A funder cannot cancel. The only ways
          out of <span className="font-mono text-xs">executing</span> are completion, failure and
          timeout, and all three are performed by the contract rather than decided by a person. An
          undefined transition is impossible, not undocumented.
        </p>
        <p className="mt-3 text-sm text-[var(--color-ink-2)]">
          A draft that does not carry acceptance criteria, failure criteria, a timeout, milestones
          and a ceiling never becomes a task &mdash; the policy gate refuses it, and{" "}
          <span className="font-mono text-xs">rejected</span> is where the refusal lands. That is a
          condition of creation, not a recommendation. In phase 2.0, financing a task out of the
          pooled funds of an agent acting for several principals is forbidden, and the check follows
          the chain from the funder through the delegation to the principal rather than stopping at
          the funder.
        </p>

        <h2 className="mt-9 text-lg font-semibold">What is unresolved</h2>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          These are on the page because they are unresolved, not in spite of it.
        </p>
        <ul className="mt-3 space-y-3 text-sm text-[var(--color-ink-2)]">
          <li className="border-l border-[var(--color-line-2)] pl-3.5">
            <strong className="text-[var(--color-ink)]">
              Only machine-checkable acceptance criteria are admitted.
            </strong>{" "}
            A task whose acceptance is a matter of opinion is never created, which is also the reason
            we can never be asked to arbitrate one. We would be a witness recording a fact, and an
            observer holding no money cannot be an arbiter.
          </li>
          <li className="border-l border-[var(--color-line-2)] pl-3.5">
            <strong className="text-[var(--color-ink)]">Witnessing creates exposure.</strong> A party
            relies on our statement at the moment money moves. The specification marks this, and the
            milestone-contract template, as requiring a lawyer&rsquo;s review before phase 2 &mdash;
            marked, and not yet resolved.
          </li>
          <li className="border-l border-[var(--color-line-2)] pl-3.5">
            <strong className="text-[var(--color-ink)]">
              &ldquo;The agent did not hand this task to a human&rdquo; is not verifiable at
              reasonable cost.
            </strong>{" "}
            It may be published as a probabilistic signal and never as a verdict. That rule is not
            waiting for phase 2; it binds every signal we publish now.
          </li>
        </ul>

        <div className="mt-9">
          <Strip tone="info">
            <strong>Nothing on this page is an offer.</strong> The only thing open today is
            verification, and it is a different thing:{" "}
            <a href="/apply/" className="text-[var(--color-accent)] hover:underline">
              request verification
            </a>
            . To check this page against its source rather than taking it from us, the phase-2
            section is in{" "}
            <a href={SPEC} className="text-[var(--color-accent)] hover:underline">
              SPEC.md
            </a>{" "}
            in the repository.
          </Strip>
        </div>
      </div>
    </Page>
  );
}
