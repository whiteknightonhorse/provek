/**
 * `/api/witness-submit` - the operator-signed relay for the GenLayer Evidence Witness (T-PW-02).
 * Everything that decides anything lives in `../_lib/witnessRelay.js`, where a test can reach it with
 * a mocked client; this file only names the HTTP methods Pages routes to it.
 *
 *   GET   -> { enabled, operator, contract, limits }   (enabled:false when the secret is missing)
 *   POST  -> 202 { tx_hash, explorer_url, track_url }  |  400 | 403 | 429 | 502 | 503
 */
import { handleGet, handlePost, methodNotAllowed } from "../_lib/witnessRelay.js";

export const onRequestGet = (ctx) => handleGet(ctx);
export const onRequestPost = (ctx) => handlePost(ctx);
export const onRequest = () => methodNotAllowed();
