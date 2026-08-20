/** Intake. The mandate choice is on the form, not in terms of service - because it is the thing
 * that decides whether we may touch a live system at all.
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
  | { state: "sent"; delivered: boolean }
  | { state: "failed"; why: string };

const ISSUES = "https://github.com/whiteknightonhorse/provek/issues";

export default function Apply() {
  const [sent, setSent] = useState<Sent>({ state: "idle" });

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setSent({ state: "sending" });
    try {
      const r = await fetch("/api/apply", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          repo: form.get("repo"),
          contact: form.get("contact"),
          mandate: "passive",
          website: form.get("website"),
        }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok || !d.ok) {
        setSent({ state: "failed", why: d.error || `HTTP ${r.status}` });
        return;
      }
      setSent({ state: "sent", delivered: Boolean(d.delivered) });
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

          {/* THE ACTIVE-MANDATE OPTION IS REMOVED, not hidden (Fable's ruling). It promised
              "we will send it before anything runs" - and nobody would send it, because no prober
              exists to honour it if it were signed. That is a false claim about US, which is the
              least excusable kind, and it sat on the one page where a stranger commits to
              something. It returns with T-2.12 and not before. The endpoint already coerces
              anything that is not "active" to "passive", so nothing behind this changed. */}
          <div className="border border-[var(--color-line-2)] bg-[var(--color-paper)] p-3">
            <p className="text-sm">
              <strong>Every verification at this stage is read-only.</strong> We read what is already
              public and touch nothing. Fewer operations can be measured that way, and the passport
              says which ones and why.
            </p>
            <p className="mt-1.5 text-xs text-[var(--color-ink-3)]">
              A probing mandate &mdash; where you name what we may touch, how often, what must not be
              affected and how you revoke it &mdash; becomes available when the prober exists. It
              will require a signed document before anything runs. It is not offered here yet
              because offering it would be a promise nobody could keep today.
            </p>
          </div>

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
              {/* THE THREE HOUSEKEEPING FIELDS ARE NAMED because "nothing else" was not true.
                  `functions/api/apply.js` writes seven keys, and this list declared four: it also
                  stores a random record id, the mandate the form sent (always "passive" - the
                  active one is not offered), and whether our own notification to the operator got
                  through. None of the three says anything further about the visitor, which is
                  exactly why nobody noticed - and "nothing else" was still a false statement about
                  a stored record, on the page of a site whose product is catching those. */}
              <li>
                <strong className="text-[var(--color-ink-2)]">Stored:</strong> the repository URL,
                your address, the time, and the two-letter country your request arrived from —
                plus three fields about the record rather than about you: a random identifier, the
                mandate this form sends (always the passive one), and whether our notification to
                the operator went through. Nothing further, and this form sets no cookie of its own.
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
                    it is a separate matter, and this is the correction. */}
                <strong className="text-[var(--color-ink-2)]">Separately, about this whole site:</strong>{" "}
                Google Analytics runs on every page here, without a consent banner. It sets a cookie
                and creates an identifier for your browser, and what it records goes to Google. That
                is the operator&rsquo;s decision and it is written down, with the argument against
                it, in the project&rsquo;s decision log. Advertising and personalisation signals are
                switched off, which is the most that can be said for it.
              </li>
            </ul>
          </div>
        </form>
      </div>
    </Page>
  );
}
