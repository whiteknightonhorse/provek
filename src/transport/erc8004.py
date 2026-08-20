"""T-2.15a - ERC-8004 read adapter. The ONLY module allowed to know the standard exists.

WHY IT IS LATE AND THIN. ERC-8004 is in **Draft**. If the methodology fused with it, a change to
the standard would become a rewrite of the product. So: this adapter is the entire blast radius of
that risk. `scorer`, `control_map`, `passport` and `ladder` import nothing from here - proven by
an AST test, not by convention.

HONESTY ABOUT WHAT IS NOT DEPLOYED. The registries may not exist on a given chain yet. An
unconfigured or unreachable registry yields `not_measured` with a REASON - never a zero, never a
silent empty result. "The registry is empty" and "we never asked it" are different states of the
world, and this project has paid seven times for collapsing that distinction.

READ ONLY. Writing a validation response on-chain is T-2.15b: it needs a deployed validator
contract and gas, which is a different cost and a different risk, and it is deliberately not here.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.abs_profile.measured import Measurement, NotMeasured
from src.transport.erc8004_deployment import (
    RECORD,
    SOURCE_REPO,
    RecordState,
    read_record,
)

ROOT = Path(__file__).resolve().parents[2]

# Function selectors are declared, not guessed. An unknown selector is an error, not a skip.
SELECTOR_OWNER_OF = "0x6352211e"      # ownerOf(uint256)
SELECTOR_TOKEN_URI = "0xc87b56dd"     # tokenURI(uint256)


@dataclass(frozen=True)
class RegistryConfig:
    """Where the registries live. Absent configuration is a STATE, not a default."""
    rpc_url: str | None = None
    identity_registry: str | None = None
    reputation_registry: str | None = None
    validation_registry: str | None = None

    @classmethod
    def from_env(cls) -> "RegistryConfig":
        return cls(rpc_url=os.environ.get("ERC8004_RPC_URL") or None,
                   identity_registry=os.environ.get("ERC8004_IDENTITY") or None,
                   reputation_registry=os.environ.get("ERC8004_REPUTATION") or None,
                   validation_registry=os.environ.get("ERC8004_VALIDATION") or None)

    @property
    def is_configured(self) -> bool:
        return bool(self.rpc_url and self.identity_registry)


@dataclass(frozen=True)
class IdentityRecord:
    token_id: str
    owner: Measurement          # an address, or the reason it is unknown
    token_uri: Measurement
    notes: tuple[str, ...] = ()


def _eth_call(cfg: RegistryConfig, to: str, data: str) -> tuple[bool, str]:
    """One JSON-RPC eth_call. Returns (ok, payload-or-reason). Never raises outward."""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                       "params": [{"to": to, "data": data}, "latest"]})
    try:
        p = subprocess.run(["curl", "-s", "--max-time", "20", "-X", "POST",
                            "-H", "Content-Type: application/json", "-d", body, cfg.rpc_url],
                           capture_output=True, text=True, timeout=30)
    except (subprocess.SubprocessError, OSError) as e:
        return False, f"rpc transport failure: {type(e).__name__}"
    if p.returncode != 0:
        return False, f"rpc call failed with code {p.returncode}"
    try:
        got = json.loads(p.stdout or "{}")
    except json.JSONDecodeError:
        return False, "rpc returned a non-JSON body"
    if "error" in got:
        return False, f"rpc error: {str(got['error'])[:120]}"
    result = got.get("result")
    if not result or result == "0x":
        return False, "empty result - the token may not exist"
    return True, result


def read_identity(cfg: RegistryConfig, token_id: int) -> IdentityRecord:
    """Read one identity. Unconfigured or unreachable yields NotMeasured WITH ITS REASON."""
    def unknown() -> Measurement:
        return Measurement(absent=NotMeasured.CHECK_DID_NOT_RUN)

    if not cfg.is_configured:
        return IdentityRecord(str(token_id), unknown(), unknown(),
                              ("registry not configured: ERC8004_RPC_URL / ERC8004_IDENTITY are "
                               "unset. This is 'we never asked', not 'the registry is empty'",))

    arg = f"{token_id:064x}"
    ok, owner = _eth_call(cfg, cfg.identity_registry, SELECTOR_OWNER_OF + arg)
    owner_m = (Measurement(value=int(owner, 16)) if ok
               else Measurement(absent=NotMeasured.UNREADABLE))
    notes = () if ok else (f"ownerOf: {owner}",)

    ok2, uri = _eth_call(cfg, cfg.identity_registry, SELECTOR_TOKEN_URI + arg)
    uri_m = (Measurement(value=len(uri)) if ok2
             else Measurement(absent=NotMeasured.UNREADABLE))
    if not ok2:
        notes = notes + (f"tokenURI: {uri}",)

    return IdentityRecord(str(token_id), owner_m, uri_m, notes)


def _last_target_reading() -> str:
    """The refusal's evidence: what the deployment list said, and when we last looked.

    WHY THE REFUSAL CITES A FILE. It used to say the registry "requires a deployed validator
    contract" in the present tense, permanently, with nothing behind it - true on the day it was
    written and unfalsifiable afterwards, which is the shape of claim this project exists to
    catch. `scripts/watch_validation_registry.py` measures it on an interval (T-F7), and this is
    where the measurement is read (ABI-16-3: a result nobody reads is the fifth sleeping state).

    IT NEVER RAISES AND NEVER GUESSES. If the record cannot be read, the message says so - a
    refusal that invented a reason would be worse than the standing claim it replaced.
    """
    r = read_record(ROOT / RECORD)
    if r.state is not RecordState.READ or r.target is None:
        return (f"the last reading of the deployment list could not be taken from "
                f"{RECORD.as_posix()} ({r.state.value}), so this refusal cites no measurement")
    listed = ", ".join(r.validation_addresses)
    where = f" listing {listed}" if listed else ""
    return (f"the deployment list at {SOURCE_REPO} read `{r.target.value}`{where} when it was "
            f"last checked ({r.checked_at_raw})")


class Erc8004Transport:
    """Publishes a projection into the Validation Registry.

    In the MVP this is a READ adapter, so publication is refused explicitly rather than silently
    doing nothing. A transport that pretends to publish is worse than one that says it cannot:
    the first produces a passport nobody can find.
    """

    def __init__(self, cfg: RegistryConfig) -> None:
        self.cfg = cfg

    def publish(self, subject_id: str, passport: dict, projection: int | None) -> str:
        raise NotImplementedError(
            "on-chain publication is T-2.15b: it requires a deployed validator contract and gas - "
            f"and {_last_target_reading()}. Until then use FileTransport, and note that the "
            "refusal is explicit, because a transport that silently does nothing yields a passport "
            "nobody can find")
