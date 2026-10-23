/**
 * `GET /api/apply/<id>` - the applicant reads the state of their own request (T-IN-03, D-69).
 *
 * WHY IT EXISTS. The form used to promise "within about fifteen minutes" and then said nothing
 * more. Measured 2026-10-23: a refused applicant learned nothing (no row, no mail, no reason), and
 * a deferred or stuck one learned nothing either. The id `POST /api/apply` returns is a random
 * UUID only the applicant holds, so it is the read capability: whoever holds it may read the state
 * of that one request, and nobody can enumerate the others.
 *
 * WHAT IS RETURNED, AND WHAT NEVER IS. An explicit allow-list is built field by field. The stored
 * record also holds `contact`, `user_agent`, `source_country` and the consent fields; none of them
 * is copied here, because a response assembled by spreading the record would leak whatever the
 * record grows next. tests/test_apply_status_names_its_states.py asserts the absence.
 *
 * `state` IS EXACTLY ONE OF FIVE, derived from the record and never defaulted (invariant 1):
 * received (nothing written by the intake run yet), deferred, refused, published, withdrawn.
 * Anything else is reported as `unknown_outcome:<value>`, so a state this file has not learned is
 * visible as such instead of being read as one it has.
 *
 * AND THE FAILURES ARE NOT "NO SUCH REQUEST". 404 means the id was malformed or unknown. A store
 * that cannot be read, or an index entry whose record is gone, says so in its own state, because
 * telling an applicant "no such request" about a request that exists is the defect this endpoint
 * was built to end.
 */

const ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const SLUG = /^[A-Za-z0-9_-]+$/;
const HEADERS = { "cache-control": "no-store" };

function answer(body, status) {
  return Response.json(body, { status, headers: HEADERS });
}

function text(v) {
  return typeof v === "string" && v !== "" ? v : null;
}

function stateOf(rec) {
  const outcome = rec.provek_outcome;
  if (outcome === "published") return "published";
  if (outcome === "refused") return "refused";
  if (outcome === "withdrawn_by_operator") return "withdrawn";
  if (outcome !== undefined && outcome !== null) return `unknown_outcome:${String(outcome)}`;
  if (rec.provek_deferred_until || rec.provek_defer_reason) return "deferred";
  // No outcome and no deferral: "received" is only true if the intake run has written NOTHING.
  // Any other provek_* field means a state this file does not know, and it is named as such.
  const touched = Object.keys(rec).filter((k) => k.startsWith("provek_"));
  return touched.length === 0 ? "received" : "unknown_outcome:none";
}

function registryUrl(state, repo, origin) {
  if (state !== "published") return `${origin}/registry/`;
  const m = /^https:\/\/github\.com\/([\w.-]+)\/([\w.-]+?)\/?$/.exec(repo || "");
  const slug = m ? `git_${m[1]}_${m[2]}` : "";
  return SLUG.test(slug) ? `${origin}/p/${slug}/` : `${origin}/registry/`;
}

export async function onRequestGet({ request, env, params }) {
  const id = String((params && params.id) || "");
  if (!ID.test(id)) return answer({ ok: false, state: "no_such_request" }, 404);
  if (!env.INTAKE) return answer({ ok: false, state: "status_unavailable" }, 503);

  let rec;
  try {
    const key = await env.INTAKE.get(`request-id:${id}`);
    if (!key) return answer({ ok: false, state: "no_such_request" }, 404);
    const raw = await env.INTAKE.get(key);
    if (!raw) return answer({ ok: false, state: "record_missing" }, 500);
    rec = JSON.parse(raw);
  } catch {
    return answer({ ok: false, state: "status_unavailable" }, 503);
  }
  if (!rec || typeof rec !== "object" || rec.id !== id)
    return answer({ ok: false, state: "record_missing" }, 500);

  const state = stateOf(rec);
  const origin = new URL(request.url).origin;
  const reason = state === "deferred" ? text(rec.provek_defer_reason) : text(rec.provek_reason);
  return answer({
    ok: true,
    id,
    received_at: text(rec.received_at),
    repo: text(rec.repo),
    state,
    reason,
    next_attempt_after: state === "deferred" ? text(rec.provek_deferred_until) : null,
    registry_url: registryUrl(state, rec.repo, origin),
  }, 200);
}
