/** Where one request stands (T-IN-03, D-69). `/apply/status/?id=<id>`.
 *
 * The id the intake endpoint returned is a random UUID only the applicant holds, so it is the read
 * capability: this page asks `GET /api/apply/<id>` and says what comes back in plain words. It
 * promises no time. A refused applicant used to learn nothing at all (no row, no mail, no reason)
 * and a deferred one learned nothing either; the two states a clock cannot describe are the ones
 * this page exists for.
 *
 * The id is read in an effect, not during render: the static HTML is prerendered with no query
 * string, and a page that read `window` while rendering would differ between the server and the
 * browser. Prerendered, it says that it is looking. */

import { useEffect, useState } from "react";
import { Page, Strip } from "../components/Chrome";
import { deferralText } from "../deferral.js";

type Status = {
  state: string;
  reason: string | null;
  next_attempt_after: string | null;
  registry_url: string | null;
  received_at: string | null;
  repo: string | null;
};

type View =
  | { kind: "reading" }
  | { kind: "no_id" }
  | { kind: "none" }
  | { kind: "error"; why: string }
  | { kind: "status"; s: Status };

// One sentence per refusal code the intake run (T-IN-01) names. A code NOT in this list prints the
// code itself: a sentence invented for a reason we have not read would be this site's founding
// defect, a guess standing where a measurement should be.
const REFUSAL: Record<string, string> = {
  repository_unavailable_for_legal_reasons_http_451:
    "GitHub reports the repository is unavailable for legal reasons, so there is nothing we may read.",
  repository_blocked_http_403:
    "GitHub refused anonymous access to the repository, so it is not publicly readable.",
  repository_not_readable_for_24h:
    "GitHub could not be read for this repository for a full day, so the request was closed. Submit it again when it can be.",
};

export function refusalSentence(code: string): string {
  if (REFUSAL[code]) return REFUSAL[code];
  const m = /^repository_did_not_answer_http_(\d{3})$/.exec(code);
  if (m)
    return `GitHub answered ${m[1]} for this repository, so it does not exist publicly at that address.`;
  return code;
}

export default function ApplyStatus() {
  const [view, setView] = useState<View>({ kind: "reading" });

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("id");
    if (!id) {
      setView({ kind: "no_id" });
      return;
    }
    let live = true;
    fetch(`/api/apply/${encodeURIComponent(id)}`, { cache: "no-store" })
      .then(async (r) => {
        const d = await r.json().catch(() => ({}));
        if (!live) return;
        if (r.status === 404) setView({ kind: "none" });
        else if (!r.ok || !d.ok) setView({ kind: "error", why: d.state || `HTTP ${r.status}` });
        else setView({ kind: "status", s: d as Status });
      })
      .catch((e: Error) => live && setView({ kind: "error", why: e.message }));
    return () => {
      live = false;
    };
  }, []);

  return (
    <Page>
      <div className="max-w-[40rem]">
        <h1 className="text-2xl font-semibold tracking-tight">Where your request stands</h1>
        <div className="mt-4">{body(view)}</div>
        <p className="mt-6 text-sm text-[var(--color-ink-3)]">
          This page shows the state of one request, read from the same record the intake run
          updates. It does not show the address you gave.{" "}
          <a href="/registry/" className="underline underline-offset-2">Registry</a>
        </p>
      </div>
    </Page>
  );
}

function body(view: View) {
  if (view.kind === "reading") return <Strip tone="info">Looking up your request&hellip;</Strip>;
  if (view.kind === "no_id")
    return (
      <Strip tone="warn">
        This address carries no request id. Use the <strong>Check this request</strong> link from
        the confirmation you received after submitting.
      </Strip>
    );
  if (view.kind === "none")
    return (
      <Strip tone="warn">
        No request is recorded under this id. That is a statement about the id, not about your
        repository: check the link was copied whole.
      </Strip>
    );
  if (view.kind === "error")
    return (
      <Strip tone="warn">
        The state could not be read ({view.why}). That is our failure to answer, and it says
        nothing about your request.
      </Strip>
    );
  const s = view.s;
  const repo = s.repo ? <code className="font-mono text-xs">{s.repo}</code> : "your repository";
  if (s.state === "received")
    return <Strip tone="info"><strong>Received.</strong> {repo} is recorded and has not been picked up by the run yet.</Strip>;
  if (s.state === "deferred") {
    const d = deferralText(s.reason);
    return (
      <Strip tone="info">
        <strong>{d.head}</strong> {repo} {d.body}{" "}
        {s.next_attempt_after ? <>We retry after <code className="font-mono text-xs">{s.next_attempt_after}</code>.</> : null}
        {s.reason ? <> <span className="text-[var(--color-ink-3)]">({s.reason})</span></> : null}
      </Strip>
    );
  }
  if (s.state === "refused")
    return (
      <Strip tone="warn">
        <strong>Refused.</strong> {s.reason ? refusalSentence(s.reason) : "No reason was recorded."}
      </Strip>
    );
  if (s.state === "withdrawn")
    return <Strip tone="warn"><strong>Withdrawn.</strong> The operator withdrew this request.{s.reason ? <> {s.reason}</> : null}</Strip>;
  if (s.state === "published")
    return (
      <Strip tone="pass">
        <strong>Published.</strong>{" "}
        <a href={s.registry_url || "/registry/"} className="underline underline-offset-2">
          See the entry for {repo}
        </a>
        .
      </Strip>
    );
  return <Strip tone="warn">The state of this request is <code className="font-mono text-xs">{s.state}</code>, which this page does not know how to describe.</Strip>;
}
