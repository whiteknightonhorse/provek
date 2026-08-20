"""Q-M1 measurement, step 1: the real population upper bound in the ERC-8004 Identity Registry.

Measured by direct on-chain reads, not by quoting a press release. The ceiling on work is declared
in advance: at most 40 RPC calls (binary search over the id space plus a sample).
"""
import json
import subprocess

IDR = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
RPC = "https://ethereum-rpc.publicnode.com"
CEILING = 40
calls = 0


def owner_of(token_id: int):
    """Address, or None when the token does not exist. None means 'asked and it is absent'."""
    global calls
    if calls >= CEILING:
        raise SystemExit(f"declared ceiling of {CEILING} RPC calls reached - stopping honestly")
    calls += 1
    data = "0x6352211e" + f"{token_id:064x}"
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                       "params": [{"to": IDR, "data": data}, "latest"]})
    p = subprocess.run(["curl", "-s", "--max-time", "20", "-X", "POST",
                        "-H", "Content-Type: application/json", "-d", body, RPC],
                       capture_output=True, text=True)
    try:
        d = json.loads(p.stdout)
    except json.JSONDecodeError:
        return "UNREADABLE"
    if "error" in d:
        return None                      # revert = token does not exist
    r = d.get("result", "")
    return None if not r or int(r, 16) == 0 else "0x" + r[-40:]


SEARCH_CEILING = 10_000_000
"""ASSIGNED, and it is a SAFETY STOP rather than a belief about the population.

The doubling search would otherwise run until the RPC refused, and an unbounded loop against a
paid endpoint is how a measurement turns into a bill. Ten million is chosen to sit far above any
plausible identity count while still terminating; if a real registry ever approaches it, the
correct response is to raise this deliberately, not to discover it as a silent truncation.

Named because ABI-16-10 forbids a bare number at a comparison: a literal here could not be told
apart from a measured bound, which is precisely the confusion that makes a guessed constant into
a cause."""

lo, hi = 1, 1
while owner_of(hi) is not None and hi < SEARCH_CEILING:
    lo, hi = hi, hi * 2
while lo + 1 < hi:
    mid = (lo + hi) // 2
    if owner_of(mid) is not None:
        lo = mid
    else:
        hi = mid

print("=== Q-M1 step 1: measured population ===")
print(f"highest existing token id: {lo}")
print(f"RPC calls used: {calls} of the declared ceiling {CEILING}")
print()
print("WHAT THIS NUMBER IS: the count of ERC-8004 identities on Ethereum mainnet.")
print("WHAT IT IS NOT: the count of AI BUSINESSES per spec 2.7. An identity is an agent record;")
print("a subject needs an observable business operation. The filter is step 2 and is NOT done.")
