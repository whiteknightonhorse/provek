/** Who a deferred request is waiting on (T-0584). Plain JavaScript so the gate runs the same bytes
 *  the bundle ships (the pattern of `slug.js`).
 *
 * The reason values are the ones T-0566-a emits (docs/INTAKE_OPERATIONS.md § Why a request is
 * deferred): `github_*` (GitHub's budget or availability), `verifier_red_<step>` (our run went
 * red), `live_registry_unreadable` (the live registry could not be read after a deploy). A reason
 * outside those families gets no claim about who is at fault: a cause invented for a reason we
 * have not read would be the page's founding defect. */

export function deferralKind(reason) {
  if (typeof reason !== "string") return "unknown";
  if (reason.startsWith("github_")) return "github";
  if (reason.startsWith("verifier_red_")) return "ours";
  if (reason.startsWith("live_registry_")) return "registry";
  return "unknown";
}

/** `{ head, body }`: the bold lead and the sentence that follows it. `body` ends before the retry time. */
export function deferralText(reason) {
  switch (deferralKind(reason)) {
    case "github":
      return { head: "Waiting for GitHub.", body: "is queued; GitHub’s public interface is busy or unreachable." };
    case "ours":
      return { head: "Waiting on our own check.", body: "is queued; our check of the run is not green yet. The request is kept and retried." };
    case "registry":
      return { head: "Waiting on the live registry check.", body: "is queued; the live registry check after publishing is pending. The request is kept and retried." };
    default:
      return { head: "Queued.", body: "is queued and will be retried." };
  }
}
