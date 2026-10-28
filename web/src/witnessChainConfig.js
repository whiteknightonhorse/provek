/**
 * The one place the page and the relay get their Bradbury chain object from.
 *
 * WHY NOT THE SDK PRESET. genlayer-js 2.0.0-rc.2 ships `chains.testnetBradbury` with the http RPC
 * `https://rpc.testnet-chain.genlayer.com`. On Bradbury Phase 2 the read path that answers is
 * `https://rpc-bradbury.genlayer.com` (raw `gen_call`, measured in `evidence/MEASURED-017-*`), the
 * `rpc_url` of `integrations/genlayer-witness/deploy/deployment.json`. So the preset is used for
 * everything except its RPC url, which is replaced here, once. `tests/test_witness_page.py` compares
 * `RPC_URL` and the id of the resulting chain object with `deployment.json`.
 */
import { CHAIN_ID } from "./witnessView.js";

export const RPC_URL = "https://rpc-bradbury.genlayer.com";

/** `base` is `chains.testnetBradbury` of the installed genlayer-js. A preset for another chain id is
 *  refused rather than re-pointed at this RPC. */
export function bradburyChain(base) {
  if (!base || base.id !== CHAIN_ID) {
    throw new Error(`the genlayer-js preset is not chain ${CHAIN_ID}`);
  }
  return { ...base, rpcUrls: { ...base.rpcUrls, default: { ...(base.rpcUrls && base.rpcUrls.default), http: [RPC_URL] } } };
}
