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
 * AND THE OFFER IS THE SIZE OF WHAT ARRIVES AT THEIR SERVER, NOT THE SIZE OF OUR UNIT (T-A2-5).
 * "One operation" is true in the prober's own vocabulary and it was the whole of what this page
 * said, while `src/prober/prober.py` spends THREE requests on the subject's origin for one probe:
 * a positive control, a negative control and the attempt. Both counts are honest and they are not
 * interchangeable here, because the person reading this page is deciding what may touch their
 * system - and the number they are deciding about is the number of requests, not the number of
 * operations we have names for. The signed mandate names paths in the plural and a rate ceiling,
 * so the document was never the narrow claim; the offer that precedes it was, which is the worse
 * place for it. `tests/test_apply_names_the_probe_cost.py` holds this copy, the same offer in
 * `docs/WHY_GET_VERIFIED.md` and `CALLS_PER_PROBE` to one number, because a count stated in prose
 * beside a constant it must equal is a rule written in three places (L-2) - and what goes missing
 * is never the value, it is the comparison.
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

// THE SAME TWO CONSTANTS THE ENDPOINT HOLDS (functions/api/apply.js), and the endpoint is the one
// that decides: it stores ITS copy into the record, never the one a client submits. This copy
// exists to be READ BY A PERSON, because the words somebody agrees to have to be on the screen
// where they agree. Two copies of one sentence is a rule written twice, so
// tests/test_consent_text_is_one_sentence.py goes red the moment they drift.
const CONSENT_VERSION = "updates-1.1.0";
const CONSENT_TEXT =
  "Also send me product updates about Provek at this address: new features, and changes to how " +
  "verification works. Optional. Not shared with anyone else; you can ask us to stop at any time.";
import { Page, Strip } from "../components/Chrome";
import { FUNNEL_SENTENCE, INCUBATOR_SENTENCE } from "../copy";

type Sent =
  | { state: "idle" }
  | { state: "sending" }
  // `asked` is carried into the confirmation because the two submissions are answered differently
  // and the difference is the applicant's to know: one waits for a verification, the other waits
  // for a document to sign. A single confirmation screen for both would let somebody who asked for
  // probing leave the page believing it had been authorised.
  | { state: "sent"; delivered: boolean; asked: Mandate; id: string }
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
  "#d-78-measurement-on-the-public-surface-cloudflare-web-analytics-cookieless-no-banner";

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
          // The version, not the wording: the endpoint quotes its own text into the record, so
          // this says only WHICH wording was on screen - and it refuses if that is not today's.
          // The box's own answer, `false` when unticked (D-71): the request does not depend on it.
          consent: form.get("updates") === "on",
          consent_version: CONSENT_VERSION,
          // T-SG-14: "a page and an application flag" - read off the URL at submit time, not off
          // a route param, because this page carries no route state of its own (App.tsx strips the
          // query string before `route` is ever compared). Named `origin`, not `source`, so it is
          // never mistaken for `source_country` in the stored record. Never asserts anything about
          // the applicant or their evidence - `functions/api/apply.js` stores it verbatim beside
          // the record for later attribution, and it does not reach `src/verify` or the mandate
          // fields above, which are computed exactly as they are for every other submission.
          origin: new URLSearchParams(window.location.search).get("via") === "challenge" ? "challenge" : null,
        }),
      });
      // T-IN-08: a Cloudflare rate-limiting rule on POST /api/apply (5 per 10 s per IP, block 10 s,
      // on since 2026-10-23) answers 429 with an HTML page, so say what to do instead of "HTTP 429".
      if (r.status === 429) {
        setSent({
          state: "failed",
          why: "Too many requests from your network in a few seconds. Wait ten seconds and send once more; nothing was saved.",
        });
        return;
      }
      const d = await r.json().catch(() => ({}));
      if (!r.ok || !d.ok) {
        setSent({ state: "failed", why: d.error || `HTTP ${r.status}` });
        return;
      }
      setSent({ state: "sent", delivered: Boolean(d.delivered), asked, id: String(d.id || "") });
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
          {/* THIS PARAGRAPH PROMISED A CLOCK, AND NOTHING KEPT IT (T-IN-03, D-69). It said the
              entry appears within a quarter of an hour. Measured 2026-10-23: GitHub's public
              interface is shared and sometimes busy, a request that meets it is deferred and
              retried, and a refused applicant saw nothing at all. The page now says what is true
              - the run is automatic and usually publishes within the hour, and can take longer -
              and gives the applicant the one thing that does not depend on a clock: a page that
              reads the state of THEIR request by its id. */}
          <p className="mt-5 text-sm text-[var(--color-ink-2)]">
            The run is automatic and usually publishes within the hour. GitHub&rsquo;s public
            interface is shared and sometimes busy, so it can take longer. Your entry appears in
            the <a href="/registry/" className="underline underline-offset-2">registry</a>, and we
            do not send mail, so there is nothing to wait for in an inbox.
          </p>
          {sent.id && (
            <p className="mt-3 text-sm">
              <a href={`/apply/status/?id=${encodeURIComponent(sent.id)}`}
                 className="text-[var(--color-accent)] hover:underline">
                Check this request
              </a>{" "}
              <span className="text-[var(--color-ink-3)]">
                &mdash; where it stands, and the reason if it was refused or is waiting. Keep the
                link: the id in it is the only key to this request.
              </span>
            </p>
          )}
          <p className="mt-3 text-sm text-[var(--color-ink-2)]">
            Appearing is not the same as scoring well. If your repository cannot be read by a
            visitor holding no credentials, your row will say <em>not measured</em> and give the
            reason, because a source we could not read is a state and not a zero. A verdict is
            computed from what is publicly observable and from nothing else, which is what lets
            anyone recompute it.
          </p>
          {/* SAID ONLY TO THE PERSON WHO ASKED, and said plainly. Recording a request is not
              granting it, and the gap between the two is where somebody would otherwise assume
              their production system is now in scope. */}
          {sent.asked === "active" && (
            <p className="mt-4 text-sm text-[var(--color-ink-2)]">
              <strong>You asked about an active-probing mandate.</strong> Nothing is authorised by
              this form and nothing will be sent at your systems. What happens next is that the
              operator writes to you with a document to agree: it names the one action and the
              three requests it spends on your origin, the paths, a ceiling on how often, what
              must not be affected, who answers for damage, what stops the run, and how you revoke
              it. No request runs before you have signed it.
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
        {/* ONE LINE, per the operator's brief - the benefit is real and specific (a verified
            passport is what the Order link's own predicate checks first, specification 4.2-bis
            point 3), not a sales pitch dressed as a fact. */}
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          A current <code>verified</code> passport is what lets you declare your own order-intake
          channel and show an &ldquo;Order&rdquo; link in the registry &mdash; see{" "}
          <a href="/method/#the-order-link" className="text-[var(--color-accent)] hover:underline">
            how that link is decided
          </a>
          .
        </p>

        {/* T-78: why this form exists at all, in the funnel's own terms - the brief asked this
            page to say what verifying is FOR rather than just how to submit. No project yet is
            answered by naming the door rather than leaving a reader with nothing to build with. */}
        <p className="mt-4 text-sm text-[var(--color-ink-2)]">
          {FUNNEL_SENTENCE} {INCUBATOR_SENTENCE}{" "}
          No project of your own yet?{" "}
          <a href="/build/" className="text-[var(--color-accent)] hover:underline">
            Build an agent from a template first &rarr;
          </a>
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
          <p className="text-xs text-[var(--color-ink-3)]"><span aria-hidden="true">*</span> required</p>
          {/* A field no human sees and no human fills. */}
          <div className="sr-only" aria-hidden="true">
            <label htmlFor="website">Leave this empty</label>
            <input id="website" name="website" type="text" tabIndex={-1} autoComplete="off" />
          </div>

          <div>
            <label htmlFor="repo" className="block text-sm font-medium">Repository URL <span aria-hidden="true">*</span></label>
            <p className="mt-0.5 text-xs text-[var(--color-ink-3)]">
              Public repositories only. That restriction exists so we never hold your secrets
              &mdash; and so that anyone can recompute the verdict from the same source. The
              registry also lists private repositories the operator entered as his own before this
              form existed; they are measured as unreadable, which is the method&rsquo;s answer to
              evidence only one party can see. That path is not open to applicants.
            </p>
            <input
              id="repo" name="repo" type="url" required aria-required="true" autoComplete="url"
              placeholder="https://github.com/org/repo"
              className="mt-2 w-full border border-[var(--color-line-2)] bg-[var(--color-paper)] px-3 py-2 text-base"
            />
          </div>

          <div>
            <label htmlFor="contact" className="block text-sm font-medium">Contact <span aria-hidden="true">*</span></label>
            <input
              id="contact" name="contact" type="email" required aria-required="true" autoComplete="email"
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
            <legend className="px-1 text-sm font-medium">What you are asking for</legend>
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
                  repository cannot show. That one operation costs your origin three requests. We
                  ask a path you publish as public, to establish that your server answers us at
                  all; a path that cannot exist, to learn what your server says about a path that
                  is simply not there; and then the closed path itself. Without those two controls
                  a refusal is not a measurement, so they are part of the operation and not extras.
                  Ticking this records the question. It is answered with a document naming the
                  action, the paths, a ceiling on how often &mdash; which all three requests count
                  against &mdash; what must not be affected, who answers for damage, what stops the
                  run and how you revoke it, and nothing is sent at your systems before you sign
                  it.
                </span>
              </span>
            </label>
          </fieldset>

          {/* THE TICK DOES NOT GATE THE BUTTON (D-71). An address is needed to answer a request;
              product updates are a separate, optional, unticked question. Browser validation is
              the only thing between the visitor and the button. */}
          <div className="border-t border-[var(--color-line)] pt-4">
            <label htmlFor="updates" className="flex gap-2.5 items-start cursor-pointer">
              <input
                id="updates" name="updates" type="checkbox"
                className="mt-0.5 h-4 w-4 shrink-0 accent-[var(--color-ink)]"
              />
              <span className="text-sm text-[var(--color-ink-2)]">{CONSENT_TEXT}</span>
            </label>
          </div>

          <button
            type="submit"
            disabled={sent.state === "sending"}
            className="border border-[var(--color-ink)] bg-[var(--color-ink)] text-[var(--color-paper)] px-4 py-2 text-sm disabled:opacity-60"
          >
            {sent.state === "sending" ? "Sending…" : "Submit request"}
          </button>
          <p className="text-xs text-[var(--color-ink-3)]">
            Nothing is charged today and Provek never holds or routes your funds. Verification may
            become paid later; the registry will say so before it does.
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
                and the browser string your request arrived with (both for abuse triage; they travel with the
                record and expire with it) &mdash; plus four fields about the
                record rather than about you: a random identifier, which mandate you asked for,
                which one we applied (always the read-only one), and whether our notification to
                the operator went through. Nothing further, and this form sets no cookie of its own.
              </li>
              <li>
                {/* THE COUNT ABOVE WENT FROM EIGHT TO THIRTEEN, so this entry exists rather than a
                    quiet edit of a number. The comment opening this list has already been earned
                    once: a list corrected and then left behind by the next change is the same
                    false sentence again, on the site whose product is catching those. */}
                <strong className="text-[var(--color-ink-2)]">Your consent, as evidence:</strong>{" "}
                only if you tick the optional updates box do we store the tick, the moment you
                ticked it, the version of the wording, and the wording itself, word for word. An
                unticked box is recorded as <code>false</code>, with those three left empty, and
                your request is processed all the same. The words are stored because
                a consent record is worth what it can later prove, and &ldquo;they agreed&rdquo;
                proves nothing without what they agreed to. Nothing is being sent yet: there is no
                mail sender in this project, so today these records only wait for the day a sender exists.
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
                <strong className="text-[var(--color-ink-2)]">Kept for:</strong> a refused or withdrawn
                request is deleted from storage 30 days after its outcome; a published request is
                kept while its row is listed, because the request is the provenance of the verdict,
                and deleted 30 days after the row is withdrawn. The operator&rsquo;s intake log keeps
                the request id and repository, not your address. The Telegram copy is deleted by hand
                on request.
              </li>
              <li>
                <strong className="text-[var(--color-ink-2)]">Deleted sooner:</strong> whenever you
                ask, through partners@provek.dev (private; a public issue would publish that you
                asked). There is nothing to reply to: we send no mail.
              </li>
              <li>
                <strong className="text-[var(--color-ink-2)]">Who holds it:</strong> Cloudflare (the
                storage and the edge that serves this form, which also keeps standard request logs
                with your IP address for its own retention period, and counts requests per address to
                limit abuse), Telegram (the one-line notification), and this server&rsquo;s intake log
                as above.
              </li>
              <li>
                <strong className="text-[var(--color-ink-2)]">Removal:</strong> a published row and
                passport are withdrawn on request by the repository&rsquo;s owner &mdash; open an
                issue on github.com/whiteknightonhorse/provek from an account that can act for the
                repository, or write through the private channel named under Deleted sooner. The next run removes the page, the
                badge and the summary. Git history and third-party caches keep what was
                published; we cannot recall those, and we say so rather than promise otherwise.
              </li>
              <li>
                {/* This paragraph described GA4 from 2026-08-20 to this change.
                    It is the one place a stranger is told how they are counted, so it changes in
                    the same commit as the counter (D-78). */}
                <strong className="text-[var(--color-ink-2)]">Separately, about this whole site:</strong>{" "}
                visits are counted by Cloudflare Web Analytics. It sets no cookie and creates no
                identifier for your browser; what it records is a count of page loads, by page, and
                it is held by Cloudflare, not by us. That decision, and the one it replaced, are
                written down in the{" "}
                <a href={DECISION_LOG} className="text-[var(--color-accent)] hover:underline">
                  project&rsquo;s decision log
                </a>
                .
              </li>
              <li>
                <strong className="text-[var(--color-ink-2)]">Not legal advice:</strong> this is a
                plain description of what the system does, written by the people who built it and
                checked against the code; it has not been reviewed by a lawyer.
              </li>
            </ul>
          </div>
        </form>
      </div>
    </Page>
  );
}
