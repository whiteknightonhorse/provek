/**
 * T-2.16 - a Provek Auditor agent built on the Amadeus Protocol SDK, PACKAGING Provek's own
 * published self-audit (ABI-5-1, ABI-24-4 - the bindings in requirements/ABI_MAP.yaml, which an
 * earlier draft of this line contradicted by citing ABI-31-4; the self-application requirement
 * belongs to the runner and the passport, not to this file).
 *
 * "Packaging", not "running": no scoring happens here and nothing is written to the chain. The
 * agent reads a passport this repository already published, hashes it, anchors it at a height it
 * read through the SDK, and encodes the result with the SDK's codec. The README retracted the
 * word "runs" and this file kept it for a round, which is exactly how a corrected claim survives.
 *
 * This file is the SDK arm of the demo and it deliberately holds NO verdict: it gathers, and
 * `src/amadeus/demo_audit.py` decides. The split is invariant 2 -
 * PASS/FAIL is taken by deterministic code from a measured quantity - and it is also why the
 * shape of every reading is re-checked on the Python side rather than trusted from here.
 *
 * WHY THIS AGENT VALIDATES THE SHAPE OF WHAT IT READS, WHICH LOOKS LIKE PARANOIA AND IS NOT.
 *
 * On 2026-08-20 at ~23:07Z, three consecutive requests to `mainnet-rpc.ama.one` for
 * `/api/chain/tip`, `/api/chain/stats` and `/api/chain/kpi` returned HTTP 200 whose body was a
 * CKAN package_search response from `ckan.opendata.swiss` - the Swiss open government data
 * portal. The record of that reading is `evidence/AMADEUS-RPC-ANOMALY-001.txt`, and it is worth
 * opening before repeating any of this: the full bodies and the response headers were NOT
 * retained, and where on the path the substitution happened was NOT established. Nothing here
 * says it was Amadeus's edge.
 *
 * What IS established, by reading the SDK rather than by inference: `ChainAPI.getTip()` is
 * `return this.client.get('/api/chain/tip')`, and NO SCHEMA IS APPLIED TO A SUCCESS BODY. Be
 * precise about what the client does check, because it is not nothing and an imprecise version
 * of this sentence is one an Amadeus engineer can dismiss: `handleResponse()` inspects a 2xx
 * body for an application-level `error` envelope - throwing 404 on `error:"not_found"`, 400 on
 * any other non-`ok` value, stripping `error:"ok"` - and throws if the body will not parse as
 * JSON. The `validate()` calls in these files guard INPUT arguments. A document like the CKAN
 * one carries no `error` key at all, so it falls through to `return data` and reaches the caller
 * AS THE CHAIN TIP, where `entry.header.height` reads `undefined` - which, one arithmetic step
 * downstream, is the zero that invariant 1 exists to forbid. The control below reproduces this
 * on demand, offline, so the claim rests on an experiment rather than on a window nobody can
 * re-open.
 */
import { createServer } from 'node:http'
import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

import {
  AmadeusSDK,
  SDK_VERSION,
  NETWORK_URLS,
  encode,
  toBase58,
} from '@amadeus-protocol/sdk'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(HERE, '..', '..')
const SELF_PASSPORT = path.join(ROOT, 'public', 'passports', 'git_whiteknightonhorse_provek.json')
const TIMEOUT_MS = 20000

/** The readings taken, in order. `require` is the path Python re-checks the body against. */
const READINGS = [
  { endpoint: 'chain.getTip', call: (sdk) => sdk.chain.getTip() },
  { endpoint: 'chain.getStats', call: (sdk) => sdk.chain.getStats() },
  { endpoint: 'chain.getKpi', call: (sdk) => sdk.chain.getKpi() },
]

/**
 * One reading. Never throws: a failure is a RECORDED outcome, because an exception here would
 * end the run and the artefact would be missing rather than honest about what it could not get.
 *
 * `transport` separates "the request did not complete" from "the source answered and declined"
 * from "the source answered". It deliberately does NOT say whether the body is chain-shaped -
 * that judgement belongs to the classifier, and making it here would put the same rule in two
 * places (L-2).
 */
async function takeReading(sdk, { endpoint, call }) {
  try {
    const body = await call(sdk)
    return {
      endpoint,
      transport: 'answered',
      // NOT 200. The SDK does not expose the status of a successful call, and any 2xx arrives
      // here identically. Writing `200` was inventing a number nobody read - in the artefact
      // whose banner is "a 200 is not a measurement". Found by Fable.
      http_status: null,
      http_status_absent_reason: 'the SDK does not expose the status of a successful call',
      error: null,
      body,
    }
  } catch (err) {
    // `AmadeusSDKError.status` is 0 for a transport failure, 408 for a timeout, and otherwise a
    // code - but NOT always the source's: `handleResponse` mints 404/400 itself for a 2xx that
    // carries an `error` envelope, and mints the response's own status when a 2xx body will not
    // parse. So `source_declined` here means "the SDK reports the request as refused", which is
    // a statement about the SDK's reading and not always about the origin. The classifier maps
    // every branch of this to UNREADABLE, so the distinction costs no correctness downstream.
    const status = typeof err?.status === 'number' ? err.status : null
    const transport = status && status > 0 && status !== 408 ? 'source_declined' : 'no_answer'
    return {
      endpoint,
      transport,
      http_status: status,
      http_status_absent_reason: status === null ? 'the error carried no status' : null,
      error: `${err?.name ?? 'Error'}: ${err?.message ?? String(err)}`,
      body: null,
    }
  }
}

/**
 * THE INSTRUMENT CONTROL, and the reason it serves a payload from a local socket rather than
 * waiting for the outage to happen again: a finding that can only be reproduced by luck is a
 * story. A local server answers 200 with a body that is unmistakably not chain state, the SDK
 * is pointed at it, and whether the SDK notices is recorded as a fact.
 *
 * The body is a reduced CKAN `package_search` envelope of the shape that was actually observed.
 * It is a stand-in, not the captured bytes - the full response was not retained, and inventing
 * a "verbatim capture" would be exactly the claim-stronger-than-the-artefact this project
 * exists to find. What the control proves is the SDK's behaviour, which does not depend on
 * which foreign document arrives.
 *
 * This control is ABLE TO FAIL, in the direction that matters: if a future SDK validates its
 * responses, `sdk_threw` becomes true, the classifier reports the finding as retired, and the
 * paragraph at the top of this file stops being true of the current version.
 */
const FOREIGN_BODY = {
  help: 'https://ckan.opendata.swiss/api/3/action/help_show?name=package_search',
  success: true,
  result: { count: 188, facets: {}, results: [{ name: 'not-a-chain-entry' }] },
}

async function foreignPayloadControl() {
  let server
  try {
    server = createServer((_req, res) => {
      res.writeHead(200, { 'content-type': 'application/json' })
      res.end(JSON.stringify(FOREIGN_BODY))
    })
    await new Promise((resolve, reject) => {
      server.once('error', reject)
      server.listen(0, '127.0.0.1', resolve)
    })
    const { port } = server.address()
    const sdk = new AmadeusSDK({ baseUrl: `http://127.0.0.1:${port}/api`, timeout: TIMEOUT_MS })
    try {
      const body = await sdk.chain.getTip()
      const height = body?.entry?.header?.height
      return {
        performed: true,
        served: FOREIGN_BODY,
        sdk_threw: false,
        returned: body,
        // Recorded explicitly because this is the number a careless caller would go on to use.
        // A bare `null` here would mean three different things - the SDK read `undefined`, the
        // SDK threw so nothing was read, or the control never ran - so each carries its reason.
        height_seen: height ?? null,
        height_seen_absent_reason: height === undefined
          ? 'the SDK returned the foreign body and entry.header.height was undefined'
          : null,
        error: null,
      }
    } catch (err) {
      return {
        performed: true,
        served: FOREIGN_BODY,
        sdk_threw: true,
        returned: null,
        height_seen: null,
        height_seen_absent_reason: 'the SDK rejected the body, so no height was read',
        error: `${err?.name ?? 'Error'}: ${err?.message ?? String(err)}`,
      }
    }
  } catch (err) {
    // The control itself could not be set up. That is `check_did_not_run`, and it must not be
    // confused with "the SDK rejected the payload" - opposite meanings, and one of them is good
    // news about the SDK.
    return {
      performed: false,
      served: null,
      sdk_threw: null,
      returned: null,
      height_seen: null,
      height_seen_absent_reason: 'the control never ran, so nothing was read',
      error: `control could not be set up: ${err?.message ?? String(err)}`,
    }
  } finally {
    if (server) await new Promise((resolve) => server.close(resolve))
  }
}

/** The published self-audit this demo packages: Provek's own passport, as already published.
 * Nothing is "under test" here - it is read and hashed, not recomputed. */
function loadSelfAudit() {
  try {
    const raw = readFileSync(SELF_PASSPORT, 'utf-8')
    return {
      loaded: true,
      path: path.relative(ROOT, SELF_PASSPORT),
      sha256: createHash('sha256').update(raw, 'utf-8').digest('hex'),
      document: JSON.parse(raw),
      error: null,
    }
  } catch (err) {
    return {
      loaded: false,
      path: path.relative(ROOT, SELF_PASSPORT),
      sha256: null,
      document: null,
      error: `${err?.name ?? 'Error'}: ${err?.message ?? String(err)}`,
    }
  }
}

/**
 * The anchor: which point in Amadeus time this audit was taken at. Built ONLY from a tip whose
 * shape is right; otherwise it is an absence with a reason, never a zero height. Python
 * re-derives this from the same reading and disagreement is a red - that cross-check is what
 * stops this function from being able to invent an anchor.
 */
function buildAnchor(tipReading) {
  const header = tipReading?.body?.entry?.header
  if (tipReading?.transport !== 'answered') {
    return { present: false, absent_reason: `tip reading ${tipReading?.transport ?? 'missing'}` }
  }
  if (!Number.isInteger(header?.height)) {
    return { present: false, absent_reason: 'tip answered but carries no integer height' }
  }
  // `slot` is optional and documented as such: null here means the header carried none. The
  // load-bearing field is `height`, which is never null in a present anchor - the guard above
  // returns an absence with a reason rather than letting it through.
  return { present: true, network: 'mainnet', height: header.height, slot: header.slot ?? null }
}

/**
 * The validation payload, serialised with the SDK's OWN codec. That is the part of the demo
 * addressed to Amadeus: the ABS validation record is transportable on their rails as bytes they
 * already know how to read, without the methodology knowing anything about those rails
 * (spec 4.4).
 *
 * BE EXACT ABOUT WHICH TRANSPORTS THIS RECORD HAS ACTUALLY TRAVELLED OVER. A draft of this
 * comment, and of the README, said the record "already travels over `file-transport` and the
 * ERC-8004 adapter". Only the first is true: `src/transport/erc8004.py::publish` raises
 * `NotImplementedError` and says why - on-chain publication is T-2.15b and needs a deployed
 * validator contract and gas. Citing a refusing adapter as evidence of transport independence
 * was a claim stronger than its artefact, in the file arguing against exactly that.
 */
function buildPayload(selfAudit, anchor) {
  if (!selfAudit.loaded) {
    return { built: false, absent_reason: 'self-audit passport could not be read', record: null }
  }
  const doc = selfAudit.document
  const record = {
    profile: 'ABS',
    profile_version: doc?.passport?.provenance?.profile_version ?? null,
    subject_id: doc?.subject_id ?? null,
    // Passed through, NOT recomputed. The scorer is Python and authoritative; a second
    // implementation of the score in JavaScript would be a second methodology.
    projection: doc?.projection ?? null,
    projection_absent_reason: doc?.passport?.verified?.projection_absent_reason ?? null,
    passport_sha256: selfAudit.sha256,
    issued_at: doc?.passport?.issued_at ?? null,
    valid_until: doc?.passport?.valid_until ?? null,
    verifier_affiliation: doc?.passport?.verifier_affiliation ?? null,
    access_channel: doc?.passport?.access_channel ?? null,
    anchored_at: anchor.present
      ? { network: anchor.network, height: anchor.height, slot: anchor.slot }
      : null,
    anchor_absent_reason: anchor.present ? null : anchor.absent_reason,
  }
  // EVERY `?? null` ABOVE IS AN ABSENCE WITH NO REASON ATTACHED, so the ones that are not
  // supposed to happen are named here instead of being left to look like data. In a well-formed
  // passport none of these is missing; if one is, the passport is malformed and the record must
  // say so rather than ship a null that reads as "the field is legitimately empty". `projection`
  // is NOT in this list - it has a reason field of its own, because an absent score is a normal
  // outcome of the methodology rather than a broken input. Fable raised the collapse; this is the
  // half of it that was still open after `height_seen` was fixed.
  const REQUIRED = ['profile_version', 'subject_id', 'passport_sha256', 'issued_at',
    'valid_until', 'verifier_affiliation', 'access_channel']
  record.missing_fields = REQUIRED.filter((k) => record[k] === null || record[k] === undefined)
  // AND SAY SO IN THE RECORD ITSELF. Two fields here carry an explicit `*_absent_reason` and the
  // rest do not, and a reader of the artefact cannot tell whether those two are the only fields
  // that can be absent or merely the only ones anybody explained. One line removes the ambiguity
  // for all of them; six more reason fields would say no more. Fable's judgement was that leaving
  // it undocumented is not defensible, and that this is.
  record.null_means = 'a null field was absent from the source passport; an explicit '
    + '*_absent_reason is added only where an absence is an expected outcome rather than a defect '
    + '(see missing_fields for absences that are defects)'
  try {
    const bytes = encode(record)
    return {
      built: true,
      absent_reason: null,
      record,
      encoding: 'amadeus-sdk encode() -> base58',
      byte_length: bytes.length,
      base58: toBase58(bytes),
      sha256: createHash('sha256').update(bytes).digest('hex'),
    }
  } catch (err) {
    return {
      built: false,
      absent_reason: `SDK encode() refused the record: ${err?.message ?? String(err)}`,
      record,
    }
  }
}

/**
 * The write is NOT attempted, and this block is why that is a recorded state rather than a gap.
 *
 * Two independent blockers, both named. This is the same shape as T-2.15b, whose on-chain write
 * is blocked for the same class of reason. A blocked step that leaves no sentinel is how
 * "cannot" becomes "forgot".
 *
 * THE BLOCKERS ARE STATED, NOT CITED. An earlier draft hung them on `NEW-13` and `A-7`, which
 * appear nowhere in SPEC.md or DECISIONS.md - they live in the operator's specification, which
 * is not published. An identifier a reader cannot resolve is not an authority, it is a footnote
 * pointing at a locked door, and on the GitHub surface that is indistinguishable from invention.
 * Found by Fable.
 */
function onchainWrite() {
  return {
    attempted: false,
    state: 'check_did_not_run',
    blockers: [
      'no signing key is present: by operator decision this agent is never given one, so it '
        + 'cannot sign - only a public address would ever reach a file',
      'a write costs AMA and the project holds none: the MVP runs on a budget of approximately '
        + 'zero, and paid dependencies are outside it',
    ],
    would_use: 'sdk.transaction.submit(txPacked) after TransactionBuilder + signing',
  }
}

async function main() {
  const rpcUrl = `${NETWORK_URLS.mainnet}/api`
  const sdk = new AmadeusSDK({ baseUrl: rpcUrl, timeout: TIMEOUT_MS })

  const readings = []
  for (const spec of READINGS) {
    readings.push(await takeReading(sdk, spec))
  }

  const control = await foreignPayloadControl()
  const selfAudit = loadSelfAudit()
  const anchor = buildAnchor(readings.find((r) => r.endpoint === 'chain.getTip'))
  const payload = buildPayload(selfAudit, anchor)

  const artefact = {
    generated_by: 'demo/amadeus/auditor.mjs',
    task: 'T-2.16',
    // No timestamp is minted here. The runner stamps the artefact once, on the Python side, so
    // there is one clock in the record rather than two that can disagree.
    sdk: {
      package: '@amadeus-protocol/sdk',
      pinned_version: '1.2.0',
      reported_version: SDK_VERSION,
    },
    network: { name: 'mainnet', rpc_url: rpcUrl },
    readings,
    foreign_payload_control: control,
    self_audit: {
      loaded: selfAudit.loaded,
      path: selfAudit.path,
      sha256: selfAudit.sha256,
      error: selfAudit.error,
      subject_id: selfAudit.document?.subject_id ?? null,
      projection: selfAudit.document?.projection ?? null,
    },
    anchor,
    payload,
    onchain_write: onchainWrite(),
  }

  process.stdout.write(`${JSON.stringify(artefact, null, 2)}\n`)
}

await main()
