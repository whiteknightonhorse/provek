/** Intake. What we may touch is stated on the form, not in terms of service - because it is the
 * thing that decides whether we may reach a live system at all.
 *
 * THE CHOICE IS BACK, AND IT IS NARROWER THAN THE ONE THAT WAS REMOVED (D-23). It was withdrawn on
 * 2026-08-20 (D-21) because no prober existed, and offering it would have asked a stranger to grant
 * access to a live system that nothing here could use. T-2.12 built the prober, and it does exactly
 * one thing: an unauthenticated access attempt against a path the subject says is closed. So the
 * option names that one thing rather than "active probing" in general - the artefact is one action
 * wide and the offer may not be wider.
 *
 * AND THE OPTION ASKS RATHER THAN GRANTS. `src/mandate/mandate.py` opens "a mandate is a legal
 * object, not a checkbox": it has to state permitted actions, their limits, what must not be
 * affected, liability, an abort condition and how it is revoked. A radio button collects none of
 * that, so what this control records is a REQUEST, and the endpoint stores it beside the policy
 * actually applied, which stays `passive` for every submission (`mandate_requested` /
 * `mandate_applied`). A form that appeared to grant a probing mandate would be the same claim
 * outrunning its artefact one floor down from the one D-21 removed.
 *
 * THIS FORM USED TO DO NOTHING. `onSubmit` was `preventDefault` and nothing else: zero requests,
 * no confirmation, no error. It is the only action the site asks for, reached from the primary
 * call to action and from a button in the masthead on every screen, and a visitor who filled it in
 * correctly received silence.
 *
 * What the confirmation may claim is a substantive question, not a wording one (Fable's ruling).
 * "Received" asserts that somebody has taken responsibility for reading it, and that is only true
 * because the submission is written durably AND announced in a channel the operator actually
 * watches. When the announcement fails, the record still exists and the page says so in different
 * words rather than claiming the stronger thing. And nothing here promises a clock: no side of
 * this has committed to one, so the page may not invent it. */

import { useState } from "react";
import { Page, Strip } from "../components/Chrome";

type Sent =
  | { state: "idle" }
  | { state: "sending" }
  // `asked` is carried into the confirmation because the two submissions are answered differently
  // and the difference is the applicant's to know: one waits for a verification, the other waits
  // for a document to sign. A single confirmation screen for both would let somebody who asked for
  // probing leave the page believing it had been authorised.
  | { state: "sent"; delivered: boolean; asked: Mandate }
  | { state: "failed"; why: string };

type Mandate = "passive" | "active";

const ISSUES = "https://github.com/whiteknightonhorse/provek/issues";
// The entry, not the file. A reader sent to the top of the decision log to hunt for the paragraph
// about the tracker on the page they are standing on has been answered in the shape of a refusal.
//
// (A dead number is kept here because what first replaced it was worse. The draft called this "a
// 964-line log"; the commit carrying that sentence also added lines to that file, so the count was
// false on arrival - hardcoded beside the document it counts, in the same file as this page's own
// rule that a stated count is the count in the artefact. The sentence then written to explain the
// mistake stated how many lines the commit added, and the commit grew again before it went out.
// A number is a claim with a maintenance cost, and neither of these was worth one.)
const DECISION_LOG =
  "https://github.com/whiteknightonhorse/provek/blob/main/DECISIONS.md" +
  "#d-14-measurement-on-the-public-surface-ga4-without-a-consent-banner";

export default function Apply() {
  const [sent, setSent] = useState<Sent>({ state: "idle" });

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    // The radio always has a checked member, so this falls back to the SAFER of the two rather
    // than to the one that asks for more access - a default reached only when something has
    // already gone wrong should not be the permissive one.
    const asked: Mandate = form.get("mandate") === "active" ? "active" : "passive";
    setSent({ state: "sending" });
    try {
      const r = await fetch("/api/apply", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          repo: form.get("repo"),
          contact: form.get("contact"),
          mandate: asked,
          website: form.get("website"),
        }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok || !d.ok) {
        setSent({ state: "failed", why: d.error || `HTTP ${r.status}` });
        return;
      }
      setSent({ state: "sent", delivered: Boolean(d.delivered), asked });
    } catch (err) {
      setSent({ state: "failed", why: (err as Error).message });
    }
  }

  if (sent.state === "sent") {
    return (
      <Page>
        <div className="max-w-[40rem]">
          <h1 className="text-2xl font-semibold tracking-tight">Request recorded</h1>
          <div className="mt-4">
            <Strip tone="pass">
              {/* WHAT `delivered` ACTUALLY MEASURES. It is `r.ok` from Telegram's sendMessage -
                  proof that the message was ACCEPTED BY TELEGRAM, not that a person has seen it.
                  This line said "has reached the operator", which is the stronger of the two and
                  the one the visitor would act on by not following up. This file's own docstring
                  sets the standard it fell short of: "received" asserts that someone has taken
                  responsibility for reading it. The success branch now claims delivery of the
                  notification, which is exactly what was measured. */}
              {sent.delivered ? (
                <>
                  <strong>Your request is recorded and the notification to the operator went
                  out.</strong> Nothing further is required from you.
                </>
              ) : (
                <>
                  <strong>Your request is recorded.</strong> The notification to the operator did
                  not go through, so it may be read later than usual. The record itself is safe -
                  we are telling you this rather than claiming otherwise.
                </>
              )}
            </Strip>
          </div>
          <p className="mt-5 text-sm text-[var(--color-ink-2)]">
            Verification runs are performed by hand at this stage. If yours runs, the passport
            appears in the registry and you are contacted at the address you gave. There is no
            queue position and no promised date, because nothing here has promised one.
          </p>
          {/* SAID ONLY TO THE PERSON WHO ASKED, and said plainly. Recording a request is not
              granting it, and the gap between the two is where somebody would otherwise assume
              their production system is now in scope. */}
          {sent.asked === "active" && (
            <p className="mt-4 text-sm text-[var(--color-ink-2)]">
              <strong>You asked about an active-probing mandate.</strong> Nothing is authorised by
              this form and nothing will be sent at your systems. What happens next is that the
              operator writes to you with a document to agree: it names the one action, the paths,
              a ceiling on how often, what must not be affected, who answers for damage, what
              stops the run, and how you revoke it. No request runs before you have signed it.
            </p>
          )}
          <p className="mt-4 text-sm">
            <a href="/registry/" className="text-[var(--color-accent)] hover:underline">
              See the registry
            </a>{" "}
            <span className="text-[var(--color-ink-3)]">
              &mdash; every record it holds, and what each one could not measure.
            </span>
          </p>
        </div>
      </Page>
    );
  }

  return (
    <Page>
      <div className="max-w-[40rem]">
        <h1 className="text-2xl font-semibold tracking-tight">Request verification</h1>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          Free at this stage. We verify only what you ask us to verify, and only what you give us
          access to.
        </p>

        {sent.state === "failed" && (
          <div className="mt-4">
            <Strip tone="warn">
              <strong>Not recorded.</strong> {sent.why}. Nothing was saved, so please try again -
              and if it keeps failing, the one channel that certainly works is{" "}
              <a href={ISSUES} className="text-[var(--color-accent)] hover:underline">
                an issue on the repository
              </a>
              .
            </Strip>
          </div>
        )}

        <form className="mt-7 space-y-5" onSubmit={submit}>
          {/* A field no human sees and no human fills. */}
          <div className="sr-only" aria-hidden="true">
            <label htmlFor="website">Leave this empty</label>
            <input id="website" name="website" type="text" tabIndex={-1} autoComplete="off" />
          </div>

          <div>
            <label htmlFor="repo" className="block text-sm font-medium">Repository URL</label>
            <p className="mt-0.5 text-xs text-[var(--color-ink-3)]">
              Public repositories only at this stage. That restriction exists so we never hold your
              secrets &mdash; and so that anyone can recompute the verdict from the same source.
            </p>
            <input
              id="repo" name="repo" type="url" required
              placeholder="https://github.com/org/repo"
              className="mt-2 w-full border border-[var(--color-line-2)] bg-[var(--color-paper)] px-3 py-2 text-base"
            />
          </div>

          <div>
            <label htmlFor="contact" className="block text-sm font-medium">Contact</label>
            <input
              id="contact" name="contact" type="email" required
              placeholder="you@example.com"
              className="mt-2 w-full border border-[var(--color-line-2)] bg-[var(--color-paper)] px-3 py-2 text-base"
            />
          </div>

          {/* THE OPTION RETURNS WITH THE PROBER AND IS THE SIZE OF THE PROBER (D-23). It was
              removed on 2026-08-20 because it promised "we will send it before anything runs" and
              nobody would have sent it - a false claim about US on the one page where a stranger
              commits to something.

              Two things keep the copy below level with the artefact. It names the ONE action the
              prober implements rather than "active probing", because that is all there is. And it
              asks rather than grants: the endpoint records `mandate_requested` beside a
              `mandate_applied` that is `passive` on every submission, so no HTTP request - from
              this form or from a hand-built client - can authorise anything. That was the hole
              D-21 actually closed, and it stays closed. */}
          <fieldset className="border border-[var(--color-line-2)] bg-[var(--color-paper)] p-3">
            <legend className="px-1 text-sm font-medium">What we may touch</legend>
            {/* THE SENTENCE THE MANDATE EXISTS TO CARRY, required on the form and not in terms of
                service by SPEC §3.4. It survived the option's removal in D-21 and it survives the
                option's return: it is the rule, and the radio below only asks which side of it a
                given applicant wants to stand on. */}
            <p className="text-xs text-[var(--color-ink-3)]">
              <strong className="text-[var(--color-ink-2)]">Without a mandate we do not touch
              production.</strong>{" "}
              Whichever you choose, this form authorises nothing on its own.
            </p>

            <label className="mt-3 flex gap-2.5">
              <input type="radio" name="mandate" value="passive" defaultChecked className="mt-1" />
              <span className="text-sm">
                <strong>Read-only verification.</strong>
                <span className="block text-xs text-[var(--color-ink-3)]">
                  We read what is already public and touch nothing you run. Fewer operations can be
                  measured that way, and the passport says which ones and why.
                </span>
              </span>
            </label>

            <label className="mt-3 flex gap-2.5">
              <input type="radio" name="mandate" value="active" className="mt-1" />
              <span className="text-sm">
                <strong>Ask about an active-probing mandate as well.</strong>
                <span className="block text-xs text-[var(--color-ink-3)]">
                  One operation exists today: we attempt to use a path you tell us is closed, and
                  report whether your running system actually refuses it &mdash; which your
                  repository cannot show. Ticking this records the question. It is answered with a
                  document naming the action, the paths, a ceiling on how often, what must not be
                  affected, who answers for damage, what stops the run and how you revoke it, and
                  nothing is sent at your systems before you sign it.
                </span>
              </span>
            </label>
          </fieldset>

          <button
            type="submit"
            disabled={sent.state === "sending"}
            className="border border-[var(--color-ink)] bg-[var(--color-ink)] text-[var(--color-paper)] px-4 py-2 text-sm disabled:opacity-60"
          >
            {sent.state === "sending" ? "Sending…" : "Submit request"}
          </button>
          <p className="text-xs text-[var(--color-ink-3)]">
            Nothing is charged. There is no payment step anywhere on this site, in this phase or any
            later one &mdash; money does not pass through us by design.
          </p>

          {/* An operator who ruled that cookieless analytics needs care about consent will be asked
              why intake data has no notice. It takes a paragraph, and a verification product that
              is vague about what it does with your address has picked a strange thing to be vague
              about. */}
          <div className="border-t border-[var(--color-line)] pt-4">
            <h2 className="text-sm font-medium">What happens to what you type here</h2>
            <ul className="mt-2 space-y-1 text-xs text-[var(--color-ink-3)]">
              {/* THE HOUSEKEEPING FIELDS ARE NAMED because "nothing else" was not true when they
                  were not. `functions/api/apply.js` wrote seven keys and this list declared four;
                  it now writes eight, because the single `mandate` field became the pair
                  `mandate_requested` / `mandate_applied` (D-23). A list that was corrected once
                  and then left behind by the next change would be the same false sentence again,
                  on the page of a site whose product is catching those - so the count is stated
                  and it is the count in the endpoint. */}
              <li>
                <strong className="text-[var(--color-ink-2)]">Stored:</strong> the repository URL,
                your address, the time, and the two-letter country your request arrived from —
                plus four fields about the record rather than about you: a random identifier, which
                mandate you asked for, which one we applied (always the read-only one), and whether
                our notification to the operator went through. Nothing further, and this form sets
                no cookie of its own.
              </li>
              <li>
                <strong className="text-[var(--color-ink-2)]">Where:</strong> Cloudflare key-value
                storage, plus — when that notification succeeds — a copy carried by Telegram to the
                operator&rsquo;s private channel so a human sees it. Telegram is named because a
                message channel that reaches a person passes through somebody; the stored record is
                read by the operator alone.
              </li>
              <li>
                <strong className="text-[var(--color-ink-2)]">Used for:</strong> deciding whether to
                run a verification and contacting you about it. Never for anything else, never sold,
                never passed on.
              </li>
              <li>
                {/* THE PROMISE HAD TO GROW WITH THE LIST ABOVE IT. Once the Telegram copy was
                    named as a second place the data sits, "deleted whenever you ask" covered two
                    stores while describing one - and `apply.js` has no deletion path at all, so
                    both are the operator's hands. Naming a store and leaving the promise where it
                    was is how a privacy statement quietly becomes partly false. */}
                <strong className="text-[var(--color-ink-2)]">Deleted:</strong> whenever you ask, by
                opening an issue or replying to any message from us &mdash; the stored record and
                the message-channel copy together, both by hand, since nothing here deletes on a
                timer. There is nothing to unsubscribe from &mdash; we do not send anything you did
                not ask for.
              </li>
              <li>
                {/* This paragraph claimed "no identifier is created for you" while Google
                    Analytics sets one on this very page. The first half of that sentence was
                    scoped to the form and true; the second was unscoped and false - a false
                    sentence in the one paragraph a stranger reads before handing over an address.
                    The measurement decision is the operator's (D-14). A surface that contradicts
                    it is a separate matter, and this is the correction.

                    AND "IT IS WRITTEN DOWN" IS NOW REACHABLE FROM THE PAGE THAT SAYS IT. This is
                    the one place a stranger is told they are being counted, and the clause that
                    softens it - that the argument against it is on the record - was the only claim
                    in this list they could not check without being told where to look. A site whose
                    product is evidence over claims may not ask to be taken at its word about the
                    entry that argues against its own tracker. */}
                <strong className="text-[var(--color-ink-2)]">Separately, about this whole site:</strong>{" "}
                Google Analytics runs on every page here, without a consent banner. It sets a cookie
                and creates an identifier for your browser, and what it records goes to Google. That
                is the operator&rsquo;s decision and it is written down, with the argument against
                it, in the{" "}
                <a href={DECISION_LOG} className="text-[var(--color-accent)] hover:underline">
                  project&rsquo;s decision log
                </a>
                . Advertising and personalisation signals are switched off, which is the most that
                can be said for it.
              </li>
            </ul>
          </div>
        </form>
      </div>
    </Page>
  );
}
