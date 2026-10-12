/** Browser-side reads of the GenLayer Evidence Witness on Bradbury.
 *
 * `genlayer-js` is imported DYNAMICALLY, inside the first call, for two reasons: it brings viem
 * with it, which no other route should download, and the build-time renderer (`entry-server.tsx`)
 * must never execute it. The page therefore prerenders as plain HTML and the chain code loads only
 * once a reader looks something up.
 *
 * READS GO DIRECTLY TO THE BRADBURY RPC. `https://rpc-bradbury.genlayer.com` answers a browser
 * origin with `access-control-allow-origin: *` (measured, `evidence/MEASURED-015-*`), so no
 * forwarding function is needed and none exists. There is no account, key or secret here: every
 * call is a read. */
import { CONTRACT_ADDRESS } from "./witnessView.js";

type Client = {
  readContract: (a: { address: string; functionName: string; args: unknown[] }) => Promise<unknown>;
  getTransaction: (a: { hash: string }) => Promise<unknown>;
};

let client: Promise<Client> | null = null;

function getClient(): Promise<Client> {
  if (!client) {
    client = Promise.all([import("genlayer-js"), import("genlayer-js/chains")]).then(
      ([gl, chains]) => gl.createClient({ chain: chains.testnetBradbury }) as unknown as Client,
    );
    // A failed chunk load must not poison every later attempt.
    client.catch(() => { client = null; });
  }
  return client;
}

export async function readView(functionName: string, args: unknown[] = []): Promise<unknown> {
  const c = await getClient();
  return c.readContract({ address: CONTRACT_ADDRESS, functionName, args });
}

export async function readTransaction(hash: string): Promise<unknown> {
  const c = await getClient();
  return c.getTransaction({ hash });
}
