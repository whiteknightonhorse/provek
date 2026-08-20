/** Intake. The mandate choice is on the form, not in terms of service - because it is the thing
 * that decides whether we may touch a live system at all. */

import { useState } from "react";
import { Page, Strip } from "../components/Chrome";

export default function Apply() {
  const [mandate, setMandate] = useState<"passive" | "active">("passive");
  return (
    <Page>
      <div className="max-w-[40rem]">
        <h1 className="text-2xl font-semibold tracking-tight">Request verification</h1>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          Free at this stage. We verify only what you ask us to verify, and only what you give us
          access to.
        </p>

        <form className="mt-7 space-y-5" onSubmit={(e) => e.preventDefault()}>
          <div>
            <label htmlFor="repo" className="block text-sm font-medium">Repository URL</label>
            <p className="mt-0.5 text-xs text-[var(--color-ink-3)]">
              Public repositories only at this stage. That restriction exists so we never hold your
              secrets.
            </p>
            <input
              id="repo" name="repo" type="url" required
              placeholder="https://github.com/org/repo"
              className="mt-2 w-full border border-[var(--color-line-2)] bg-[var(--color-paper)] px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label htmlFor="contact" className="block text-sm font-medium">Contact</label>
            <input
              id="contact" name="contact" type="email" required
              placeholder="you@example.com"
              className="mt-2 w-full border border-[var(--color-line-2)] bg-[var(--color-paper)] px-3 py-2 text-sm"
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
            className="border border-[var(--color-ink)] bg-[var(--color-ink)] text-[var(--color-paper)] px-4 py-2 text-sm"
          >
            Submit request
          </button>
          <p className="text-xs text-[var(--color-ink-3)]">
            Nothing is charged. There is no payment step anywhere on this site, in this phase or any
            later one &mdash; money does not pass through us by design.
          </p>
        </form>
      </div>
    </Page>
  );
}
