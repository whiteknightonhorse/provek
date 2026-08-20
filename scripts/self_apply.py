"""Self-application (ABI-31-4): the incubator runs its own procedure on itself.

"A verifier that exempts itself has published an opinion, not a standard."
"""
import sys
from pathlib import Path

sys.path.insert(0, "/home/incubator/incubator")

from src.abs_profile.identity import Binding, BindingKind
from src.pipeline import verify
from src.registry.public_registry import PublicRegistry
from src.transport.file_transport import FileTransport

out = Path("/home/incubator/incubator/public")
res = verify("/home/incubator/incubator",
             Binding(BindingKind.GIT, "incubator/incubator"),
             FileTransport(out / "passports"),
             PublicRegistry(out / "registry"),
             claims={"self_description": "Proof of Autonomy - an ERC-8004 validator"},
             mandate_ref="self-mandate-0001",
             verifier_affiliation="same_owner")

m = res.passport.to_machine()
print("=== PASSPORT OF THE INCUBATOR ITSELF ===")
print("subject:", m["subject_id"])
print("binding:", m["binding_strength"], m["binding_flags"])
print("status:", m["status"])
print("projection:", m["verified"]["projection"],
      "| absent reason:", m["verified"]["projection_absent_reason"])
print("control map ceiling:", m["verified"]["control_map_cap"])
print("operations:")
for o in m["verified"]["operations"]:
    print("   %-24s %-20s measured=%s" % (o["operation"], o["level"], o["measured"]))
print("inspected:", m["verified"]["coverage"]["inspected"])
print("out of reach:", list(m["verified"]["coverage"]["out_of_reach"].keys()))
print("affiliation:", m["verifier_affiliation"])
print("findings:")
for f in res.findings:
    print("   -", f)
print("published:", res.published_ref)
