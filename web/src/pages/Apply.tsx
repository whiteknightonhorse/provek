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
  const [mandate, setMandate] = useState<"passive" | "active">("passive");
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
          mandate: form.get("mandate"),
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
              {sent.delivered ? (
                <>
                  <strong>Your request is recorded and has reached the operator.</strong> Nothing
                  further is required from you.
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

          <fieldset>
            <legend className="text-sm font-medium">What we may do</legend>
            <div className="mt-2 space-y-2">
              <label className="flex gap-3 border border-[var(--color-line-2)] bg-[var(--color-paper)] p-3 cursor-pointer">
                <input
                  type="radio" name="mandate" value="passive" className="mt-1"
                  checked={mandate === "passive"} onChange={() => setMandate("passive")}
                />
                <span className="text-sm">
                  <strong>Read only.</strong> We read what is already public and touch nothing.
                  <span className="block text-xs text-[var(--color-ink-3)] mt-0.5">
                    Fewer operations can be measured; the passport will say which.
                  </span>
                </span>
              </label>
              <label className="flex gap-3 border border-[var(--color-line-2)] bg-[var(--color-paper)] p-3 cursor-pointer">
                <input
                  type="radio" name="mandate" value="active" className="mt-1"
                  checked={mandate === "active"} onChange={() => setMandate("active")}
                />
                <span className="text-sm">
                  <strong>Read, plus an explicit mandate to probe.</strong> You name what we may
                  touch, how often, what must not be affected, and how you revoke it.
                  <span className="block text-xs text-[var(--color-ink-3)] mt-0.5">
                    Stronger evidence. Requires a signed mandate before anything runs.
                  </span>
                </span>
              </label>
            </div>
          </fieldset>

          {mandate === "active" && (
            <Strip tone="warn">
              A mandate is a document, not a checkbox: it names permitted actions, their limits,
              liability for collateral damage, abort conditions and revocation. We will send it
              before anything runs.
            </Strip>
          )}

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
              <li>
                <strong className="text-[var(--color-ink-2)]">Stored:</strong> the repository URL,
                your address, the mandate you chose, the time, and the two-letter country your
                request arrived from. Nothing else &mdash; no cookie is set by this form and no
                identifier is created for you.
              </li>
              <li>
                <strong className="text-[var(--color-ink-2)]">Where:</strong> Cloudflare key-value
                storage, plus a copy in the operator&rsquo;s private message channel so a human sees
                it. Both are read by the operator alone.
              </li>
              <li>
                <strong className="text-[var(--color-ink-2)]">Used for:</strong> deciding whether to
                run a verification and contacting you about it. Never for anything else, never sold,
                never passed on.
              </li>
              <li>
                <strong className="text-[var(--color-ink-2)]">Deleted:</strong> whenever you ask, by
                opening an issue or replying to any message from us. There is nothing to unsubscribe
                from &mdash; we do not send anything you did not ask for.
              </li>
            </ul>
          </div>
        </form>
      </div>
    </Page>
  );
}
